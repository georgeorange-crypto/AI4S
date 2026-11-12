import json
import tempfile
import unittest
from pathlib import Path

try:
    from mlflow.tracking import MlflowClient
except ImportError:
    MlflowClient = None

from ai4s.core import ResearchStore
from ai4s.tracking.mlflow_local import MlflowLocalTracker
from ai4s.workflow import run_research

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(MlflowClient is None, "install requirements-research.lock for MLflow integration tests")
class MlflowTrackingTests(unittest.TestCase):
    def test_completed_cpu_workflow_is_logged_locally_and_idempotently(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = ResearchStore(root / "research.sqlite")
            try:
                approval = store.approve("local_cpu_experiment", "test-human", "test-only offline run")
                report = run_research(
                    store,
                    ROOT / "examples/offline_research/offline_fixture.csv",
                    root / "outputs",
                    approval_id=approval,
                    run_key="mlflow-test",
                )
                uri = f"sqlite:///{(root / 'mlflow.db').as_posix()}"
                tracker = MlflowLocalTracker(uri, root / "mlflow-artifacts")
                first = tracker.log_workflow(report)
                second = tracker.log_workflow(report)
                replayed_report = run_research(
                    store,
                    ROOT / "examples/offline_research/offline_fixture.csv",
                    root / "outputs",
                    approval_id=approval,
                    run_key="mlflow-test",
                )
                replayed = tracker.log_workflow(replayed_report)
                self.assertEqual(first["run_id"], second["run_id"])
                self.assertEqual(first["run_id"], replayed["run_id"])
                self.assertFalse(first["reused"])
                self.assertTrue(second["reused"])
                self.assertEqual(first["artifact_sha256"], second["artifact_sha256"])
                self.assertEqual(first["artifact_sha256"], replayed["artifact_sha256"])
                self.assertEqual(report["code_sha256"], replayed_report["code_sha256"])

                client = MlflowClient(tracking_uri=uri)
                try:
                    logged = client.get_run(first["run_id"])
                    self.assertEqual(logged.data.tags["ai4s.model"], "none")
                    self.assertEqual(logged.data.params["dataset_sha256"], report["dataset_sha256"])
                    for seed in report["seeds"]:
                        self.assertIn(f"candidate_accuracy_seed_{seed}", logged.data.metrics)
                    artifact = Path(
                        client.download_artifacts(first["run_id"], "research_report.json", root / "readback")
                    )
                    saved_report = json.loads(artifact.read_text(encoding="utf-8"))
                    self.assertEqual(saved_report["workflow_id"], report["workflow_id"])
                finally:
                    MlflowLocalTracker._dispose_client(client)
            finally:
                store.close()

    def test_tracker_rejects_remote_uri_and_noncompleted_workflow(self):
        with self.assertRaises(ValueError):
            MlflowLocalTracker("https://tracking.example/api")
        tracker = MlflowLocalTracker("sqlite:///./.ai4s/reject-test.db")
        with self.assertRaises(ValueError):
            tracker.log_workflow({"status": "running", "workflow_id": "not-completed"})


if __name__ == "__main__":
    unittest.main()
