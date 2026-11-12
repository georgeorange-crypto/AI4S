"""Persistent domain and control-plane primitives for offline research runs."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Budget:
    wall_seconds: float
    max_runs: int
    spend_usd: float = 0.0


@dataclass(frozen=True)
class ExperimentContract:
    contract_id: str
    question: str
    hypothesis: str
    dataset_id: str
    dataset_sha256: str
    seeds: tuple[int, ...]
    budget: Budget
    approval_id: str
    intent: str = "exploratory"

    def sha256(self) -> str:
        payload = asdict(self)
        payload.pop("approval_id", None)  # authorization record is audit metadata, not experiment identity
        return digest(json.dumps(payload, sort_keys=True).encode())


class ResearchStore:
    """SQLite-backed append-only workflow journal and research object store."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY, canonical_url TEXT, kind TEXT, name TEXT, status TEXT, license_status TEXT, execution_risk TEXT, raw_json TEXT NOT NULL, maintainer TEXT, version_or_commit TEXT, discovered_at TEXT, last_checked TEXT, integration_status TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS resource_observations(resource_id TEXT, source_record_id TEXT, source_file TEXT, raw_json TEXT NOT NULL, PRIMARY KEY(resource_id,source_record_id,source_file));
        CREATE TABLE IF NOT EXISTS discoveries(id TEXT PRIMARY KEY, canonical_url TEXT, raw_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS approvals(id TEXT PRIMARY KEY, action TEXT, decision TEXT, actor TEXT, scope TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY, run_key TEXT UNIQUE, state TEXT, checkpoint TEXT, budget_json TEXT, started_at TEXT, ended_at TEXT, error TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT, seq INTEGER, event_type TEXT, payload TEXT, created_at TEXT, UNIQUE(workflow_id, seq));
        CREATE TABLE IF NOT EXISTS experiment_runs(id TEXT PRIMARY KEY, workflow_id TEXT, seed INTEGER, status TEXT, metrics_json TEXT, idempotency_key TEXT UNIQUE, elapsed_seconds REAL, error TEXT);
        CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY, workflow_id TEXT, name TEXT, sha256 TEXT, path TEXT, media_type TEXT);
        CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, content TEXT, source_id TEXT, status TEXT, rationale TEXT);
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(experiment_runs)")}
        for name in ("started_at", "ended_at"):
            if name not in columns:
                self.db.execute(f"ALTER TABLE experiment_runs ADD COLUMN {name} TEXT")
        resource_columns = {row[1] for row in self.db.execute("PRAGMA table_info(resources)")}
        resource_migrations = {
            "maintainer": "TEXT",
            "version_or_commit": "TEXT",
            "discovered_at": "TEXT",
            "last_checked": "TEXT",
            "integration_status": "TEXT",
            "notes": "TEXT",
        }
        for name, sql_type in resource_migrations.items():
            if name not in resource_columns:
                self.db.execute(f"ALTER TABLE resources ADD COLUMN {name} {sql_type}")
        self.db.commit()
        self.db.commit()

    def event(self, workflow_id: str, event_type: str, payload: dict[str, Any] | None = None) -> None:
        seq = self.db.execute(
            "SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE workflow_id=?", (workflow_id,)
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO events(workflow_id,seq,event_type,payload,created_at) VALUES(?,?,?,?,?)",
            (workflow_id, seq, event_type, json.dumps(payload or {}, sort_keys=True), now()),
        )
        self.db.commit()

    def approve(self, action: str, actor: str, scope: str) -> str:
        approval_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO approvals VALUES(?,?,?,?,?,?)", (approval_id, action, "approved", actor, scope, now())
        )
        self.db.commit()
        return approval_id

    def has_approval(self, approval_id: str, action: str) -> bool:
        return (
            self.db.execute(
                "SELECT 1 FROM approvals WHERE id=? AND action=? AND decision='approved'", (approval_id, action)
            ).fetchone()
            is not None
        )

    def create_workflow(self, run_key: str, budget: Budget) -> tuple[str, bool]:
        existing = self.db.execute("SELECT id FROM workflows WHERE run_key=?", (run_key,)).fetchone()
        if existing:
            return existing[0], False
        wid = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO workflows VALUES(?,?, 'queued', '{}', ?, ?, NULL, NULL)",
            (wid, run_key, json.dumps(asdict(budget)), now()),
        )
        self.db.commit()
        self.event(wid, "workflow_created", {"run_key": run_key})
        return wid, True

    def state(self, workflow_id: str) -> str:
        row = self.db.execute("SELECT state FROM workflows WHERE id=?", (workflow_id,)).fetchone()
        if not row:
            raise KeyError(workflow_id)
        return row[0]

    def transition(
        self, workflow_id: str, state: str, payload: dict[str, Any] | None = None, error: str | None = None
    ) -> None:
        allowed = {
            "queued": {"running", "cancelled"},
            "running": {"paused", "cancelled", "completed", "failed"},
            "paused": {"running", "cancelled"},
            "failed": {"running", "cancelled"},
        }
        current = self.state(workflow_id)
        if state not in allowed.get(current, set()):
            raise ValueError(f"invalid workflow transition: {current} -> {state}")
        self.db.execute(
            "UPDATE workflows SET state=?, ended_at=?, error=? WHERE id=?",
            (state, now() if state in {"completed", "cancelled", "failed"} else None, error, workflow_id),
        )
        self.db.commit()
        self.event(workflow_id, "state_changed", {"from": current, "to": state, **(payload or {})})

    def request_control(self, workflow_id: str, action: str, actor: str) -> None:
        if action not in {"pause", "cancel"}:
            raise ValueError(f"unsupported control action: {action}")
        target = "paused" if action == "pause" else "cancelled"
        self.transition(workflow_id, target, {"actor": actor, "requested_action": action})

    def authorize(self, action: str, approval_id: str | None = None) -> None:
        if action in {"remote_execution", "external_publication", "network_tool"}:
            if approval_id is None or not self.has_approval(approval_id, action):
                raise PermissionError(f"{action} requires a persisted approval")
        elif action not in {"local_cpu_experiment"}:
            raise PermissionError(f"unknown action denied: {action}")

    def import_registries(self, resources_path: str | Path, discoveries_path: str | Path) -> dict[str, int]:
        resources = json.loads(Path(resources_path).read_text(encoding="utf-8"))
        discoveries = json.loads(Path(discoveries_path).read_text(encoding="utf-8"))
        for item in resources:
            url = canonical_url(item.get("url", ""))
            rid = digest(url.encode())[:24]
            source_record = json.dumps(item, ensure_ascii=False, sort_keys=True)
            source_id = digest(source_record.encode())
            self.db.execute(
                "INSERT OR IGNORE INTO resources(id,canonical_url,kind,name,status,license_status,execution_risk,raw_json,maintainer,version_or_commit,discovered_at,last_checked,integration_status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    rid,
                    url,
                    item.get("category", "unknown"),
                    item.get("name", ""),
                    "discovered",
                    "unknown",
                    "unreviewed",
                    source_record,
                    item.get("organization"),
                    None,
                    now(),
                    None,
                    "discovered",
                    item.get("notes", ""),
                ),
            )
            self.db.execute(
                "INSERT OR IGNORE INTO resource_observations VALUES(?,?,?,?)",
                (rid, source_id, "original_resource_catalog.json", source_record),
            )
        for item in discoveries:
            url = canonical_url(item.get("url", ""))
            did = digest((url + item.get("name", "")).encode())[:24]
            self.db.execute(
                "INSERT OR IGNORE INTO discoveries VALUES(?,?,?)",
                (did, url, json.dumps(item, ensure_ascii=False, sort_keys=True)),
            )
        self.db.commit()
        combined_urls = {
            row[0]
            for row in self.db.execute(
                "SELECT canonical_url FROM resources UNION SELECT canonical_url FROM discoveries"
            )
            if row[0]
        }
        return {
            "resource_records": len(resources),
            "resource_unique_urls": self.db.execute("SELECT COUNT(DISTINCT canonical_url) FROM resources").fetchone()[
                0
            ],
            "resource_entities": self.db.execute("SELECT COUNT(*) FROM resources").fetchone()[0],
            "discovery_records": len(discoveries),
            "discovery_entities": self.db.execute("SELECT COUNT(*) FROM discoveries").fetchone()[0],
            "combined_records": len(resources) + len(discoveries),
            "combined_unique_urls": len(combined_urls),
        }

    def store_artifact(
        self, workflow_id: str, name: str, content: bytes, root: str | Path, media_type: str
    ) -> dict[str, str]:
        sha = digest(content)
        path = Path(root) / sha[:2] / sha
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
        aid = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO artifacts VALUES(?,?,?,?,?,?)", (aid, workflow_id, name, sha, str(path), media_type)
        )
        self.db.commit()
        return {"id": aid, "name": name, "sha256": sha, "path": str(path)}

    def get_artifact(self, artifact_id: str) -> bytes:
        row = self.db.execute("SELECT path,sha256 FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        if not row:
            raise KeyError(artifact_id)
        content = Path(row["path"]).read_bytes()
        if digest(content) != row["sha256"]:
            raise ValueError(f"artifact checksum mismatch: {artifact_id}")
        return content

    def close(self) -> None:
        self.db.close()


def canonical_url(url: str) -> str:
    from urllib.parse import urlsplit, urlunsplit

    if not url:
        return ""
    p = urlsplit(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/")
    return urlunsplit((p.scheme.lower() or "https", host, path, "", ""))
