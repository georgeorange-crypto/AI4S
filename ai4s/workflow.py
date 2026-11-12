"""Deterministic, offline CPU research loop with durable seed-level records."""

from __future__ import annotations

import csv
import json
import platform
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .core import Budget, ExperimentContract, ResearchStore, digest, now


def load_fixture(path: str | Path) -> tuple[list[tuple[float, float]], str]:
    raw = Path(path).read_bytes()
    rows = list(csv.DictReader(raw.decode().splitlines()))
    return [(float(r["x1"]), float(r["x2"])) for r in rows], digest(raw)


def _label(x: tuple[float, float]) -> int:
    return int(x[0] + x[1] > 0)


def evaluate(points: list[tuple[float, float]], seed: int, method: str) -> dict[str, float]:
    # Frozen 25% holdout, deterministic per seed; model fit uses only remaining rows.
    order = list(range(len(points)))
    random.Random(seed).shuffle(order)
    split = max(1, len(order) // 4)
    test_idx, train_idx = order[:split], order[split:]
    if method == "majority_baseline":
        pred = int(sum(_label(points[i]) for i in train_idx) / len(train_idx) >= 0.5)
        predictions = [pred] * len(test_idx)
    else:
        # Candidate: fit a 1-D threshold on x1 alone, deliberately omitting x2.
        vals = sorted((points[i][0], _label(points[i])) for i in train_idx)
        threshold = sum(v for v, _ in vals) / len(vals)
        predictions = [int(points[i][0] > threshold) for i in test_idx]
    accuracy = sum(predictions[j] == _label(points[i]) for j, i in enumerate(test_idx)) / len(test_idx)
    return {"heldout_accuracy": accuracy, "test_examples": float(len(test_idx))}


def run_research(
    store: ResearchStore,
    fixture_path: str | Path,
    output_dir: str | Path,
    *,
    approval_id: str,
    seeds: tuple[int, ...] = (11, 23, 37),
    budget: Budget | None = None,
    run_key: str = "offline-fixture-v1",
    pause_after_seed: int | None = None,
    fail_seed: int | None = None,
) -> dict[str, Any]:
    if len(seeds) > 3 or (budget is not None and len(seeds) > budget.max_runs):
        raise ValueError("run exceeds configured max_runs budget (3)")
    points, data_sha = load_fixture(fixture_path)
    budget = budget or Budget(wall_seconds=30, max_runs=len(seeds))
    contract = ExperimentContract(
        "offline-trend-v1",
        "Does x1-only classification match a simple majority baseline on held-out synthetic labels?",
        "A one-feature threshold may improve held-out accuracy over the majority baseline, though labels depend on both features.",
        "synthetic-linear-fixture-v1",
        data_sha,
        seeds,
        budget,
        approval_id,
    )
    if not store.has_approval(contract.approval_id, "local_cpu_experiment"):
        raise PermissionError("local experiment requires an approval record")
    package_root = Path(__file__).parent
    code_material = b"".join(
        path.name.encode() + b"\0" + path.read_bytes() for path in sorted(package_root.glob("*.py"))
    )
    code_sha = digest(code_material)
    workflow_key = f"{run_key}:{contract.sha256()}:{code_sha}"
    wid, created = store.create_workflow(workflow_key, budget)
    if not created and store.state(wid) == "completed":
        return summarize(store, wid, contract, reused=True)
    if store.state(wid) in {"queued", "paused", "failed"}:
        store.transition(wid, "running", {"contract_sha256": contract.sha256(), "code_sha256": code_sha})
    started = time.monotonic()
    started_at = now()
    config_sha = contract.sha256()
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    for seed in seeds:
        state = store.state(wid)
        if state == "paused":
            return summarize(store, wid, contract, paused=True)
        if state == "cancelled":
            return summarize(store, wid, contract, cancelled=True)
        key = f"{contract.sha256()}:{code_sha}:{seed}:local-cpu"
        prior = store.db.execute("SELECT status FROM experiment_runs WHERE idempotency_key=?", (key,)).fetchone()
        if prior and prior[0] == "completed":
            continue
        if fail_seed == seed:
            store.db.execute(
                "INSERT OR REPLACE INTO experiment_runs(id,workflow_id,seed,status,metrics_json,idempotency_key,elapsed_seconds,error,started_at,ended_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    key,
                    wid,
                    seed,
                    "failed",
                    "{}",
                    key,
                    0.0,
                    "injected failure for failure-path validation",
                    now(),
                    now(),
                ),
            )
            store.db.commit()
            store.event(
                wid, "experiment_failed", {"seed": seed, "error": "injected failure for failure-path validation"}
            )
            store.transition(wid, "failed", {"seed": seed}, error="seed execution failed")
            return summarize(store, wid, contract, failed=True)
        seed_start = time.monotonic()
        baseline = evaluate(points, seed, "majority_baseline")
        candidate = evaluate(points, seed, "x1_threshold")
        result = {
            "seed": seed,
            "baseline": baseline,
            "candidate": candidate,
            "difference": candidate["heldout_accuracy"] - baseline["heldout_accuracy"],
        }
        elapsed = time.monotonic() - seed_start
        store.db.execute(
            "INSERT OR REPLACE INTO experiment_runs(id,workflow_id,seed,status,metrics_json,idempotency_key,elapsed_seconds,error,started_at,ended_at) VALUES(?,?,?,?,?,?,?,NULL,?,?)",
            (key, wid, seed, "completed", json.dumps(result, sort_keys=True), key, elapsed, now(), now()),
        )
        store.db.commit()
        store.event(wid, "seed_completed", result)
        if time.monotonic() - started >= budget.wall_seconds:
            store.transition(wid, "failed", {"reason": "wall-time budget exceeded"}, error="wall-time budget exceeded")
            return summarize(store, wid, contract, failed=True)
        if pause_after_seed == seed:
            store.transition(wid, "paused", {"checkpoint_seed": seed})
            return summarize(store, wid, contract, paused=True)
    report = summarize(store, wid, contract)
    report.update(
        {
            "code_sha256": code_sha,
            "config_sha256": config_sha,
            "experiment_started_at": started_at,
            "experiment_ended_at": now(),
            "runtime": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "hardware": {
                    "accelerator": None,
                    "cpu_model": platform.processor() or platform.machine(),
                    "architecture": platform.machine(),
                },
                "dependency_lock_sha256": digest(
                    (Path(__file__).resolve().parent.parent / "requirements.lock").read_bytes()
                ),
            },
            "model": None,
            "tool_versions": {"ai4s_research_os": "0.1.0", "python": sys.version.split()[0]},
        }
    )
    if report["status"] == "running":
        report["status"] = "completed"
        raw = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True).encode()
        artifact = store.store_artifact(wid, "raw_results.json", raw, out_root / "artifacts", "application/json")
        report["artifact"] = artifact
        store.transition(wid, "completed", {"artifact_sha256": artifact["sha256"]})
        report_bytes = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True).encode()
        report_artifact = store.store_artifact(
            wid, "research_report.json", report_bytes, out_root / "artifacts", "application/json"
        )
        report["report_artifact"] = report_artifact
        (out_root / "research_report.json").write_bytes(report_bytes)
    return report


def summarize(store: ResearchStore, wid: str, contract: ExperimentContract, **flags: bool) -> dict[str, Any]:
    rows = store.db.execute("SELECT * FROM experiment_runs WHERE workflow_id=? ORDER BY seed", (wid,)).fetchall()
    completed = [json.loads(r["metrics_json"]) for r in rows if r["status"] == "completed"]
    diffs = [x["difference"] for x in completed]
    mean_diff = sum(diffs) / len(diffs) if diffs else None
    status = store.state(wid)
    approval = store.db.execute(
        "SELECT id,action,decision,actor,scope,created_at FROM approvals WHERE id=?", (contract.approval_id,)
    ).fetchone()
    interpretation = "inconclusive" if mean_diff is None or mean_diff <= 0 else "exploratory_signal"
    claims = [
        {
            "id": "claim-supported",
            "status": "supported",
            "content": "Fixture labels are generated from x1 + x2 > 0.",
            "source": "offline_fixture.csv",
        },
        {
            "id": "claim-conflicting",
            "status": "disputed",
            "content": "The candidate uses both x1 and x2.",
            "source": "fixture_notes_untrusted.txt",
            "excluded_from_conclusion": True,
        },
    ]
    return {
        "workflow_id": wid,
        "status": status,
        "question": contract.question,
        "hypothesis": contract.hypothesis,
        "intent": contract.intent,
        "approval": dict(approval) if approval else None,
        "contract_sha256": contract.sha256(),
        "dataset_id": contract.dataset_id,
        "dataset_sha256": contract.dataset_sha256,
        "seeds": list(contract.seeds),
        "runs": [
            {
                "seed": r["seed"],
                "status": r["status"],
                "metrics": json.loads(r["metrics_json"]),
                "elapsed_seconds": r["elapsed_seconds"],
                "started_at": r["started_at"],
                "ended_at": r["ended_at"],
                "error": r["error"],
            }
            for r in rows
        ],
        "mean_candidate_minus_baseline_accuracy": mean_diff,
        "interpretation": interpretation,
        "claims": claims,
        "budget": asdict(contract.budget),
        **flags,
    }
