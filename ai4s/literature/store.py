"""Durable SQLite provenance for literature graph executions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..core import ResearchStore, now
from .crossref import normalize_title


class LiteratureStore:
    def __init__(self, store: ResearchStore, output_root: str | Path):
        self.store = store
        self.output_root = Path(output_root)

    def prepare_run(
        self,
        run_key: str,
        thread_id: str,
        query: str,
        approval_id: str,
        skill_name: str,
        skill_sha256: str,
    ) -> tuple[str, dict[str, Any] | None]:
        existing = self.store.db.execute(
            "SELECT status,report_json FROM literature_runs WHERE run_key=?", (run_key,)
        ).fetchone()
        if existing and existing["status"] == "completed" and existing["report_json"]:
            return thread_id, json.loads(existing["report_json"])
        if existing:
            self.store.db.execute(
                "UPDATE literature_runs SET status='running',error=NULL,started_at=?,ended_at=NULL WHERE run_key=?",
                (now(), run_key),
            )
        else:
            self.store.db.execute(
                "INSERT INTO literature_runs(run_key,thread_id,query,status,approval_id,skill_name,skill_sha256,started_at) VALUES(?,?,?,'running',?,?,?,?)",
                (run_key, thread_id, query, approval_id, skill_name, skill_sha256, now()),
            )
        self.event(run_key, "literature_run_started", {"thread_id": thread_id, "skill": skill_name})
        return thread_id, None

    def record_tool_call(
        self, run_key: str, sequence: int, tool_name: str, request: dict[str, Any], envelope: dict[str, Any]
    ) -> dict[str, Any]:
        raw_text = envelope["raw_response_text"]
        raw = raw_text.encode("utf-8")
        response_sha = hashlib.sha256(raw).hexdigest()
        if response_sha != envelope["response_sha256"]:
            raise ValueError("Crossref raw response checksum did not match provider envelope")
        request_json = json.dumps(request, ensure_ascii=False, sort_keys=True)
        call_id = hashlib.sha256(f"{run_key}:{sequence}:{tool_name}".encode()).hexdigest()[:32]
        snapshot = self.store.store_artifact(
            run_key, f"{tool_name}_response.json", raw, self.output_root / run_key / "snapshots", "application/json"
        )
        self.store.db.execute(
            "INSERT OR REPLACE INTO literature_tool_calls(call_id,run_key,sequence,tool_name,request_json,response_json,response_sha256,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (call_id, run_key, sequence, tool_name, request_json, raw_text, response_sha, envelope["retrieved_at"]),
        )
        self.store.db.execute(
            "INSERT OR REPLACE INTO literature_snapshots(snapshot_id,source_id,request_url,response_sha256,response_json,status_code,retrieved_at) VALUES(?,?,?,?,?,?,?)",
            (
                call_id,
                "crossref",
                envelope["request_url"],
                response_sha,
                raw_text,
                envelope["status_code"],
                envelope["retrieved_at"],
            ),
        )
        self.event(
            run_key,
            "literature_tool_succeeded",
            {"sequence": sequence, "tool": tool_name, "response_sha256": response_sha},
        )
        self.store.db.commit()
        return {"call_id": call_id, "response_sha256": response_sha, "artifact": snapshot}

    def record_evidence(self, run_key: str, source_record: dict[str, Any], status: str) -> dict[str, Any]:
        doi = source_record["doi"]
        source_id = hashlib.sha256(f"crossref:{doi}".encode()).hexdigest()[:32]
        url = f"https://doi.org/{doi}"
        metadata = json.dumps(source_record, ensure_ascii=False, sort_keys=True)
        self.store.db.execute(
            "INSERT OR IGNORE INTO literature_sources(source_id,provider,doi,url,title,metadata_json,license_status,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (
                source_id,
                "crossref",
                doi,
                url,
                source_record.get("title") or "",
                metadata,
                "metadata_facts; abstract_excluded",
                now(),
            ),
        )
        claim_text = f"Crossref returned metadata for DOI {doi} with title {source_record.get('title')!r}."
        evidence_id = hashlib.sha256(f"{run_key}:{source_id}:{status}".encode()).hexdigest()[:32]
        self.store.db.execute(
            "INSERT OR REPLACE INTO literature_evidence(evidence_id,run_key,source_id,claim_text,status,location,created_at) VALUES(?,?,?,?,?,?,?)",
            (evidence_id, run_key, source_id, claim_text, status, "Crossref metadata fields: DOI and title", now()),
        )
        self.event(
            run_key,
            "citation_identity_checked",
            {
                "source_id": source_id,
                "doi": doi,
                "status": status,
                "title_match": normalize_title(source_record.get("title")),
            },
        )
        self.store.db.commit()
        return {"source_id": source_id, "doi": doi, "url": url, "evidence_id": evidence_id, "status": status}

    def event(self, run_key: str, event_type: str, payload: dict[str, Any]) -> None:
        self.store.db.execute(
            "INSERT INTO literature_events(run_key,event_type,payload,created_at) VALUES(?,?,?,?)",
            (run_key, event_type, json.dumps(payload, ensure_ascii=False, sort_keys=True), now()),
        )
        self.store.db.commit()

    def finish(self, run_key: str, status: str, report: dict[str, Any], error: str | None = None) -> None:
        report_text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        self.store.db.execute(
            "UPDATE literature_runs SET status=?,ended_at=?,error=?,report_json=? WHERE run_key=?",
            (status, now(), error, report_text, run_key),
        )
        self.event(run_key, f"literature_run_{status}", {"error": error} if error else {})
        self.store.db.commit()

    def get_tool_call_count(self, run_key: str) -> int:
        return int(
            self.store.db.execute("SELECT COUNT(*) FROM literature_tool_calls WHERE run_key=?", (run_key,)).fetchone()[
                0
            ]
        )
