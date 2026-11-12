import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai4s.core import Budget, ResearchStore, canonical_url
from ai4s.registry import SQLiteResourceRegistry
from ai4s.workflow import run_research

ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = ResearchStore(self.root / "db.sqlite")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_registry_ingestion_preserves_records_and_deduplicates_url(self):
        registry = SQLiteResourceRegistry(self.store)
        result = registry.ingest(
            ROOT / "registries/original_resource_catalog.json", ROOT / "registries/discovery_indexes.json"
        )
        self.assertEqual(result["resource_records"], 100)
        self.assertEqual(result["discovery_records"], 43)
        self.assertEqual(result["combined_records"], 143)
        self.assertLessEqual(result["resource_unique_urls"], 100)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM discoveries").fetchone()[0], 43)
        self.assertEqual(
            self.store.db.execute(
                "SELECT COUNT(*) FROM resources WHERE status='discovered' AND license_status='unknown'"
            ).fetchone()[0],
            result["resource_entities"],
        )
        self.assertEqual(
            self.store.db.execute(
                "SELECT COUNT(*) FROM resource_observations WHERE source_file='original_resource_catalog.json'"
            ).fetchone()[0],
            100,
        )
        self.assertEqual(
            self.store.db.execute(
                "SELECT COUNT(*) FROM resources WHERE integration_status='discovered' AND execution_risk='unreviewed'"
            ).fetchone()[0],
            100,
        )
        self.assertEqual(len(registry.list(status="discovered")), 100)

    def test_workflow_generates_seed_records_and_real_artifacts(self):
        with self.assertRaises(PermissionError):
            run_research(
                self.store,
                ROOT / "examples/offline_research/offline_fixture.csv",
                self.root / "out",
                approval_id="missing",
            )
        approval = self.store.approve("local_cpu_experiment", "test-human", "test-only offline fixture")
        result = run_research(
            self.store, ROOT / "examples/offline_research/offline_fixture.csv", self.root / "out", approval_id=approval
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual([r["seed"] for r in result["runs"]], [11, 23, 37])
        self.assertTrue(result["dataset_sha256"])
        self.assertTrue(Path(result["artifact"]["path"]).exists())
        self.assertTrue(Path(result["report_artifact"]["path"]).exists())
        self.assertEqual(result["claims"][1]["status"], "disputed")
        self.assertEqual(result["approval"]["decision"], "approved")
        self.assertEqual(result["approval"]["actor"], "test-human")
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM experiment_runs").fetchone()[0], 3)

    def test_killed_worker_resumes_from_sqlite_checkpoint_without_duplicate_seed(self):
        approval = self.store.approve("local_cpu_experiment", "test-human", "test-only offline fixture")
        self.store.close()
        run_key = "process-restart"
        worker = """
import os, sys
from ai4s.core import ResearchStore
from ai4s.workflow import run_research
store = ResearchStore(sys.argv[1])
result = run_research(store, sys.argv[2], sys.argv[4], approval_id=sys.argv[3], run_key=sys.argv[5], pause_after_seed=11)
os._exit(71 if result["status"] == "paused" else 72)
"""
        crashed = subprocess.run(
            [
                sys.executable,
                "-c",
                worker,
                str(self.root / "db.sqlite"),
                str(ROOT / "examples/offline_research/offline_fixture.csv"),
                approval,
                str(self.root / "out"),
                run_key,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(crashed.returncode, 71, crashed.stdout + crashed.stderr)
        self.store = ResearchStore(self.root / "db.sqlite")
        checkpoint = self.store.db.execute(
            "SELECT id,state FROM workflows WHERE run_key LIKE ?", (run_key + ":%",)
        ).fetchone()
        self.assertEqual(checkpoint["state"], "paused")
        wid = checkpoint["id"]
        resumed = run_research(
            self.store,
            ROOT / "examples/offline_research/offline_fixture.csv",
            self.root / "out",
            approval_id=approval,
            run_key=run_key,
        )
        self.assertEqual(resumed["status"], "completed")
        self.assertEqual(
            self.store.db.execute("SELECT COUNT(*) FROM experiment_runs WHERE workflow_id=?", (wid,)).fetchone()[0], 3
        )
        self.assertEqual(
            self.store.db.execute(
                "SELECT COUNT(DISTINCT idempotency_key) FROM experiment_runs WHERE workflow_id=?", (wid,)
            ).fetchone()[0],
            3,
        )
        with self.assertRaises(ValueError):
            self.store.transition(wid, "running")
        self.store.authorize("local_cpu_experiment")
        with self.assertRaises(PermissionError):
            self.store.authorize("unknown_action")

    def test_failure_is_persisted_and_remote_permission_is_not_implied(self):
        approval = self.store.approve("local_cpu_experiment", "test-human", "test-only offline fixture")
        result = run_research(
            self.store,
            ROOT / "examples/offline_research/offline_fixture.csv",
            self.root / "out",
            approval_id=approval,
            fail_seed=23,
            run_key="failure",
        )
        self.assertEqual(result["status"], "failed")
        self.assertTrue(
            self.store.db.execute("SELECT error FROM workflows WHERE id=?", (result["workflow_id"],)).fetchone()[0]
        )
        with self.assertRaises(PermissionError):
            self.store.authorize("remote_execution")
        approval = self.store.approve("remote_execution", "human-reviewer", "one named job")
        self.store.authorize("remote_execution", approval)

    def test_over_budget_and_cancel(self):
        approval = self.store.approve("local_cpu_experiment", "test-human", "test-only offline fixture")
        with self.assertRaises(ValueError):
            run_research(
                self.store,
                ROOT / "examples/offline_research/offline_fixture.csv",
                self.root / "out",
                approval_id=approval,
                seeds=(1, 2, 3, 4),
            )
        wid, _ = self.store.create_workflow("cancel-test", Budget(10, 1))
        self.store.transition(wid, "running")
        self.store.request_control(wid, "cancel", "local-user")
        self.assertEqual(self.store.state(wid), "cancelled")

    def test_cpu_time_budget_exhaustion_is_persisted(self):
        approval = self.store.approve("local_cpu_experiment", "test-human", "test-only offline fixture")
        result = run_research(
            self.store,
            ROOT / "examples/offline_research/offline_fixture.csv",
            self.root / "out",
            approval_id=approval,
            run_key="zero-time-budget",
            budget=Budget(0, 3),
        )
        self.assertEqual(result["status"], "failed")
        row = self.store.db.execute("SELECT state,error FROM workflows WHERE id=?", (result["workflow_id"],)).fetchone()
        self.assertEqual(row["state"], "failed")
        self.assertEqual(row["error"], "wall-time budget exceeded")
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM experiment_runs").fetchone()[0], 1)

    def test_url_normalization_and_budget_value(self):
        self.assertEqual(canonical_url("HTTPS://WWW.Example.COM/path/?track=1#part"), "https://example.com/path")
        self.assertEqual(Budget(1, 2).max_runs, 2)


if __name__ == "__main__":
    unittest.main()
