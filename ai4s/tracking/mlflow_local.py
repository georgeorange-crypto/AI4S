"""Explicit local-only MLflow Tracking adapter for reproducible CPU experiments."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from sqlalchemy.engine import make_url


class MlflowLocalTracker:
    """Record a completed AI4S workflow in a local SQLite-backed MLflow store."""

    def __init__(
        self, tracking_uri: str = "sqlite:///.ai4s/mlflow.db", artifact_root: str | Path = ".ai4s/mlflow-artifacts"
    ):
        url = make_url(tracking_uri)
        if url.drivername != "sqlite" or url.host or url.query or not url.database or url.database == ":memory:":
            raise ValueError("MLflow tracking must use a persistent local SQLite URI")
        self.tracking_uri = tracking_uri
        self.artifact_root = Path(artifact_root).resolve()

    def log_workflow(self, report: dict[str, Any]) -> dict[str, Any]:
        if report.get("status") != "completed":
            raise ValueError("only completed research workflows can be logged to MLflow")
        workflow_id = str(report.get("workflow_id", ""))
        if not workflow_id:
            raise ValueError("workflow_id is required for idempotent MLflow tracking")

        # Import the optional package only when an operator explicitly enables tracking.
        os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
        from mlflow.tracking import MlflowClient

        stable_report = {
            key: value for key, value in report.items() if key not in {"reused", "report_artifact", "mlflow"}
        }
        serialized = json.dumps(stable_report, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        artifact_sha = hashlib.sha256(serialized).hexdigest()

        self.artifact_root.mkdir(parents=True, exist_ok=True)
        client = MlflowClient(tracking_uri=self.tracking_uri)
        experiment_name = "AI4S Offline Research"
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = client.create_experiment(experiment_name, artifact_location=self.artifact_root.as_uri())
        else:
            experiment_id = experiment.experiment_id

        existing = client.search_runs(
            [experiment_id],
            filter_string=f"tags.ai4s_workflow_id = '{workflow_id}'",
            max_results=1,
            order_by=["attributes.start_time DESC"],
        )
        if existing and existing[0].info.status == "FINISHED":
            run = existing[0]
            recorded_sha = self._artifact_sha(client, run.info.run_id)
            if recorded_sha != artifact_sha:
                self._dispose_client(client)
                raise ValueError("MLflow run already exists with a different or missing report artifact")
            receipt = {
                "provider": "mlflow",
                "run_id": run.info.run_id,
                "experiment_id": experiment_id,
                "artifact_sha256": artifact_sha,
                "reused": True,
            }
            self._dispose_client(client)
            return receipt

        if existing:
            run_id = existing[0].info.run_id
            if existing[0].info.status != "RUNNING":
                client.update_run(run_id, status="RUNNING")
        else:
            created = client.create_run(experiment_id, tags={"ai4s_workflow_id": workflow_id})
            run_id = created.info.run_id

        params = {
            "workflow_id": workflow_id,
            "contract_sha256": report.get("contract_sha256", "unknown"),
            "config_sha256": report.get("config_sha256", report.get("contract_sha256", "unknown")),
            "code_sha256": report.get("code_sha256", "unknown"),
            "dataset_sha256": report.get("dataset_sha256", "unknown"),
            "seed_count": str(len(report.get("seeds", []))),
            "python": str(report.get("runtime", {}).get("python", "unknown")),
        }
        for key, value in params.items():
            if value != "unknown":
                client.log_param(run_id, key, str(value))
        tags = {
            "ai4s.workflow_id": workflow_id,
            "ai4s.intent": str(report.get("intent", "exploratory")),
            "ai4s.model": "none",
            "ai4s.tracking_scope": "local-only",
        }
        for key, value in tags.items():
            client.set_tag(run_id, key, value)

        metrics: dict[str, float] = {}
        for item in report.get("runs", []):
            if item.get("status") != "completed":
                continue
            seed = int(item["seed"])
            values = item["metrics"]
            metrics[f"baseline_accuracy_seed_{seed}"] = float(values["baseline"]["heldout_accuracy"])
            metrics[f"candidate_accuracy_seed_{seed}"] = float(values["candidate"]["heldout_accuracy"])
            metrics[f"candidate_minus_baseline_seed_{seed}"] = float(values["difference"])
        for key, value in metrics.items():
            history = client.get_metric_history(run_id, key)
            if history and any(point.value != value for point in history):
                raise ValueError(f"MLflow metric conflict for {key}; refusing to overwrite prior evidence")
            if not history:
                client.log_metric(run_id, key, value)

        with tempfile.TemporaryDirectory(prefix="ai4s-mlflow-") as temp_dir:
            report_path = Path(temp_dir) / "research_report.json"
            report_path.write_bytes(serialized)
            existing_artifacts = {entry.path for entry in client.list_artifacts(run_id)}
            if "research_report.json" not in existing_artifacts:
                client.log_artifact(run_id, str(report_path))
        client.set_terminated(run_id, status="FINISHED")
        receipt = {
            "provider": "mlflow",
            "run_id": run_id,
            "experiment_id": experiment_id,
            "artifact_sha256": artifact_sha,
            "reused": False,
        }
        self._dispose_client(client)
        return receipt

    @staticmethod
    def _dispose_client(client: Any) -> None:
        # MlflowClient has no public close method; dispose only its local SQLite engine.
        tracking_client = getattr(client, "_tracking_client", None)
        store = getattr(tracking_client, "store", None)
        engine = getattr(store, "engine", None)
        if engine is not None:
            engine.dispose()

    @staticmethod
    def _artifact_sha(client: Any, run_id: str) -> str | None:
        with tempfile.TemporaryDirectory(prefix="ai4s-mlflow-read-") as temp_dir:
            try:
                local = Path(client.download_artifacts(run_id, "research_report.json", temp_dir))
            except Exception:
                return None
            return hashlib.sha256(local.read_bytes()).hexdigest() if local.is_file() else None
