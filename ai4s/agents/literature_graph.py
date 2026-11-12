"""A model-free LangGraph + in-process MCP literature identity workflow."""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, TypedDict

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy
from mcp import Client
from mcp.server import MCPServer

from ..core import ResearchStore
from ..literature.crossref import (
    CrossrefAdapter,
    SQLiteRateLimiter,
    approval_scope,
    doi_approval_scope,
    normalize_doi,
    normalize_title,
)
from ..literature.store import LiteratureStore
from ..skills.registry import SkillRegistry, skill_approval_scope


class LiteratureState(TypedDict, total=False):
    run_key: str
    query: str
    max_results: int
    direct_doi: str | None
    search: dict[str, Any]
    resolve: dict[str, Any]
    report: dict[str, Any]


def _make_mcp_server(adapter: CrossrefAdapter) -> MCPServer:
    server = MCPServer(name="ai4s-crossref", version="1.0.0")

    @server.tool(name="crossref_search", structured_output=True)
    async def crossref_search(query: str, max_results: int = 3) -> dict[str, Any]:
        """Search Crossref for bounded bibliographic metadata; abstracts are excluded."""
        return adapter.search(query, max_results)

    @server.tool(name="crossref_resolve", structured_output=True)
    async def crossref_resolve(doi: str) -> dict[str, Any]:
        """Resolve a DOI to Crossref bibliographic metadata; abstracts are excluded."""
        return adapter.resolve(doi)

    return server


async def _call_mcp(server: MCPServer, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async with Client(server) as client:
        result = await client.call_tool(name, arguments)
    if result.is_error:
        raise RuntimeError(f"MCP tool {name} returned an error")
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    # SDKs may encode structured output as a JSON text block. Parse only JSON data.
    for content in result.content:
        text = getattr(content, "text", None)
        if isinstance(text, str):
            import json

            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
    raise RuntimeError(f"MCP tool {name} did not return a structured object")


def run_literature_graph(
    store: ResearchStore,
    *,
    query: str,
    max_results: int,
    run_key: str,
    output_root: str | Path,
    checkpoints_path: str | Path,
    crossref_approval_id: str,
    skill_approval_id: str,
    skill_root: str | Path,
    adapter: CrossrefAdapter | None = None,
    direct_doi: str | None = None,
) -> dict[str, Any]:
    """Run a bounded tool-only graph. Model calls and telemetry are intentionally disabled."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_key):
        raise ValueError("run_key must be 1-80 safe filename characters")
    skill = SkillRegistry(skill_root).load("literature-evidence-review")
    normalized_doi = normalize_doi(direct_doi) if direct_doi else None
    if normalized_doi:
        query = f"doi:{normalized_doi}"
    if not {"crossref_search", "crossref_resolve"}.issubset(skill.allowed_tools):
        raise PermissionError("skill is missing required MCP tool permissions")
    if set(skill.permissions) != {"crossref.search", "crossref.resolve"}:
        raise PermissionError("skill permissions do not match this workflow")
    thread_id = hashlib.sha256(f"ai4s-literature:{run_key}".encode()).hexdigest()
    literature = LiteratureStore(store, output_root)
    existing = store.db.execute(
        "SELECT status,report_json,query,approval_id,skill_name,skill_sha256 FROM literature_runs WHERE run_key=?",
        (run_key,),
    ).fetchone()
    if existing and existing["query"] != query:
        raise ValueError("run_key is already bound to a different query")
    if existing and existing["status"] == "completed" and existing["report_json"]:
        import json

        return json.loads(existing["report_json"])

    if not existing:
        store.consume_approvals(
            [
                (
                    crossref_approval_id,
                    "network_tool",
                    doi_approval_scope(normalized_doi) if normalized_doi else approval_scope(query, max_results),
                ),
                (skill_approval_id, "skill_activation", skill_approval_scope(skill)),
            ]
        )
        literature.prepare_run(
            run_key,
            thread_id,
            query,
            crossref_approval_id,
            skill.name,
            skill.content_sha256,
        )
    else:
        if existing["approval_id"] != crossref_approval_id or existing["skill_sha256"] != skill.content_sha256:
            raise PermissionError("resume requires the original approved Crossref and skill identities")
        # A persisted in-progress run may resume from its SQLite graph checkpoint. Its approvals
        # were consumed before the first external call; no new permission is created here.

    os.environ["LANGSMITH_TRACING"] = "false"
    mcp_server = _make_mcp_server(adapter or CrossrefAdapter(limiter=SQLiteRateLimiter(store.db)))

    def search_node(state: LiteratureState) -> dict[str, Any]:
        if state.get("direct_doi"):
            return {"search": {"records": [], "snapshot": None}}
        data = asyncio.run(
            _call_mcp(mcp_server, "crossref_search", {"query": state["query"], "max_results": state["max_results"]})
        )
        artifact = literature.record_tool_call(run_key, 1, "crossref_search", data["request"], data)
        return {"search": {"records": data["records"], "snapshot": artifact}}

    def resolve_node(state: LiteratureState) -> dict[str, Any]:
        records = state["search"]["records"]
        candidate: dict[str, Any] | None
        if state.get("direct_doi"):
            candidate = {"doi": state["direct_doi"], "title": None}
        else:
            candidate = next((record for record in records if record.get("doi") and record.get("title")), None)
        if not candidate:
            return {"resolve": {"status": "no_resolvable_result", "candidate": None}}
        data = asyncio.run(_call_mcp(mcp_server, "crossref_resolve", {"doi": candidate["doi"]}))
        artifact = literature.record_tool_call(run_key, 2, "crossref_resolve", data["request"], data)
        resolved = data["record"]
        if not resolved:
            return {
                "resolve": {
                    "status": "doi_not_found",
                    "candidate": candidate,
                    "record": None,
                    "snapshot": artifact,
                }
            }
        if candidate["title"] is None:
            status = "doi_resolved_title_uncompared"
        else:
            status = (
                "identity_match"
                if normalize_title(candidate["title"]) == normalize_title(resolved.get("title"))
                else "title_mismatch"
            )
        evidence = literature.record_evidence(run_key, resolved, status)
        return {
            "resolve": {
                "status": status,
                "candidate": candidate,
                "record": resolved,
                "evidence": evidence,
                "snapshot": artifact,
            }
        }

    def report_node(state: LiteratureState) -> dict[str, Any]:
        resolved = state["resolve"]
        report = {
            "workflow": "crossref-metadata-identity-check",
            "run_key": run_key,
            "thread_id": thread_id,
            "status": resolved["status"],
            "query": state["query"],
            "direct_doi": state.get("direct_doi"),
            "max_results": state["max_results"],
            "model_used": None,
            "skill": {"name": skill.name, "version": skill.version, "sha256": skill.content_sha256},
            "tools": (["crossref_resolve"] if state.get("direct_doi") else ["crossref_search"])
            + (["crossref_resolve"] if resolved.get("record") and not state.get("direct_doi") else []),
            "search_results": state["search"]["records"],
            "resolution": resolved,
            "interpretation_limit": "Confirms only that Crossref returned metadata and whether the title strings match; it does not establish scientific claim support or correctness.",
            "approvals": {"crossref": crossref_approval_id, "skill_activation": skill_approval_id},
        }
        literature.finish(run_key, "completed", report)
        return {"report": report}

    graph = StateGraph(LiteratureState)
    graph.add_node("search", search_node, retry_policy=RetryPolicy(max_attempts=1))
    graph.add_node("resolve", resolve_node, retry_policy=RetryPolicy(max_attempts=1))
    graph.add_node("report", report_node)
    graph.add_edge(START, "search")
    graph.add_edge("search", "resolve")
    graph.add_edge("resolve", "report")
    graph.add_edge("report", END)

    checkpoint_path = Path(checkpoints_path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(checkpoint_path), check_same_thread=False)
    saver = SqliteSaver(connection, serde=JsonPlusSerializer(allowed_msgpack_modules=()))
    saver.setup()
    compiled: Any = graph.compile(checkpointer=saver)
    try:
        graph_config = {"configurable": {"thread_id": thread_id}}
        checkpoint = compiled.get_state(graph_config) if existing else None
        graph_input = (
            None
            if checkpoint and checkpoint.values
            else {
                "run_key": run_key,
                "query": query,
                "max_results": max_results,
                "direct_doi": normalized_doi,
            }
        )
        result = compiled.invoke(
            graph_input,
            graph_config,
        )
        return result["report"]
    except Exception as exc:
        literature.finish(run_key, "failed", {"run_key": run_key, "model_used": None}, f"{type(exc).__name__}: {exc}")
        raise
    finally:
        connection.close()
