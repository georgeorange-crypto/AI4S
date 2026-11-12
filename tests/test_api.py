from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from ai4s.api import app
from ai4s.database import get_session
from ai4s.orm import Base, CapabilityEntry, Resource

ROOT = Path(__file__).resolve().parents[1]


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            f"sqlite:///{Path(self.temp.name) / 'api.sqlite'}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

        def override_session():
            session = self.sessions()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_session] = override_session
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.temp.cleanup()

    def test_api_project_question_workflow_controls_and_event_audit(self) -> None:
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})
        created = self.client.post(
            "/api/v1/projects", json={"project_id": "p1", "name": "CPU research", "domain": "ml"}
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(
            self.client.post("/api/v1/projects", json={"project_id": "p1", "name": "duplicate"}).status_code, 409
        )
        question = self.client.post(
            "/api/v1/projects/p1/questions",
            json={"question_id": "q1", "question": "Can a small candidate improve held-out accuracy?"},
        )
        self.assertEqual(question.status_code, 201)
        wf = self.client.post("/api/v1/workflows", json={"workflow_id": "w1", "run_key": "rk1", "project_id": "p1"})
        self.assertEqual(wf.status_code, 201)
        paused = self.client.post("/api/v1/workflows/w1/control", json={"action": "pause", "reason": "human review"})
        self.assertEqual(paused.json()["state"], "paused")
        resumed = self.client.post(
            "/api/v1/workflows/w1/control", json={"action": "resume", "reason": "review complete"}
        )
        self.assertEqual(resumed.json()["state"], "running")
        events = self.client.get("/api/v1/workflows/w1/events").json()
        self.assertEqual([e["sequence"] for e in events], [1, 2, 3])
        self.assertEqual(
            self.client.post(
                "/api/v1/workflows/w1/control", json={"action": "resume", "reason": "invalid"}
            ).status_code,
            409,
        )

    def test_api_validates_input_and_lists_reviewed_registry_states(self) -> None:
        response = self.client.post("/api/v1/projects", json={"project_id": "p1", "name": "x", "extra": "rejected"})
        self.assertEqual(response.status_code, 422)
        with self.sessions.begin() as session:
            session.add(
                Resource(
                    resource_id="r1",
                    canonical_url="https://example.org",
                    kind="test",
                    name="candidate",
                    maintainer=None,
                    license_status="unknown",
                    version_or_commit=None,
                    integration_status="discovered",
                    execution_risk="unreviewed",
                    notes="",
                    source_payload={},
                )
            )
        result = self.client.get("/api/v1/resources?status=discovered").json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["integration_status"], "discovered")
        self.assertEqual(self.client.get("/api/v1/resources?limit=501").status_code, 422)
        with self.sessions.begin() as session:
            session.add(
                CapabilityEntry(
                    capability_id="fastapi",
                    version="pinned",
                    source="https://example.org",
                    license="MIT",
                    integration_status="tested",
                    execution_risk="loopback API",
                    permissions=["listen on loopback"],
                    secrets=[],
                    evidence=["contract test"],
                )
            )
        capabilities = self.client.get("/api/v1/capabilities").json()
        self.assertEqual(capabilities[0]["capability_id"], "fastapi")
        self.assertEqual(capabilities[0]["integration_status"], "tested")


class MigrationTests(unittest.TestCase):
    def test_alembic_migrates_sqlite_and_schema_contains_core_entities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "migrated.sqlite"
            env = os.environ.copy()
            env["AI4S_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, env=env, text=True, capture_output=True
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            migrated_engine = create_engine(env["AI4S_DATABASE_URL"])
            tables = set(inspect(migrated_engine).get_table_names())
            migrated_engine.dispose()
            expected = {
                "projects",
                "research_questions",
                "sources",
                "paper_snapshots",
                "claims",
                "evidence_edges",
                "hypotheses",
                "experiment_contracts",
                "experiment_runs_api",
                "artifacts",
                "budgets",
                "approvals",
                "workflow_runs",
                "workflow_events",
                "resource_registry",
                "resource_observations",
                "discovery_indexes",
                "capability_registry",
                "alembic_version",
            }
            self.assertTrue(expected.issubset(tables))


if __name__ == "__main__":
    unittest.main()
