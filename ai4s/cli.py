"""Command line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import ResearchStore
from .registry import SQLiteResourceRegistry
from .workflow import run_research


def main() -> None:
    parser = argparse.ArgumentParser(prog="ai4s")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run-offline", help="run the checked-in CPU research fixture")
    run.add_argument("--db", default=".ai4s/research.sqlite")
    run.add_argument("--out", default=".ai4s/runs")
    run.add_argument("--approval-id", required=True)
    run.add_argument("--run-key", default="offline-fixture-v1")
    run.add_argument("--pause-after-seed", type=int)
    resume = sub.add_parser("resume", help="resume a paused offline workflow")
    resume.add_argument("--db", default=".ai4s/research.sqlite")
    resume.add_argument("--out", default=".ai4s/runs")
    resume.add_argument("--run-key", default="offline-fixture-v1")
    resume.add_argument("--approval-id", required=True)
    approve = sub.add_parser("approve-local", help="record explicit human approval for the offline fixture only")
    approve.add_argument("--db", default=".ai4s/research.sqlite")
    approve.add_argument("--actor", required=True)
    registry = sub.add_parser("import-registry", help="ingest discovery records without enabling tools")
    registry.add_argument("--db", default=".ai4s/research.sqlite")
    crossref_approval = sub.add_parser("approve-crossref", help="approve one bounded Crossref metadata query")
    crossref_approval.add_argument("--db", default=".ai4s/research.sqlite")
    crossref_approval.add_argument("--query", required=True)
    crossref_approval.add_argument("--max-results", type=int, default=3)
    crossref_approval.add_argument("--actor", required=True)
    doi_approval = sub.add_parser("approve-doi", help="approve one Crossref DOI metadata lookup")
    doi_approval.add_argument("--db", default=".ai4s/research.sqlite")
    doi_approval.add_argument("--doi", required=True)
    doi_approval.add_argument("--actor", required=True)
    skill_approval = sub.add_parser("approve-skill", help="approve activation of a reviewed skill hash")
    skill_approval.add_argument("--db", default=".ai4s/research.sqlite")
    skill_approval.add_argument("--actor", required=True)
    literature = sub.add_parser("run-literature-agent", help="run model-free Crossref MCP/LangGraph workflow")
    literature.add_argument("--db", default=".ai4s/research.sqlite")
    literature.add_argument("--out", default=".ai4s/literature")
    literature.add_argument("--checkpoints", default=".ai4s/agent-checkpoints.sqlite")
    literature.add_argument("--query", default="")
    literature.add_argument("--doi")
    literature.add_argument("--max-results", type=int, default=3)
    literature.add_argument("--run-key", required=True)
    literature.add_argument("--crossref-approval-id", required=True)
    literature.add_argument("--skill-approval-id", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    store = ResearchStore(args.db)
    try:
        result: dict[str, Any]
        if args.command == "import-registry":
            result = SQLiteResourceRegistry(store).ingest(
                root / "registries/original_resource_catalog.json", root / "registries/discovery_indexes.json"
            )
        elif args.command == "approve-local":
            approval_id = store.approve("local_cpu_experiment", args.actor, "offline fixture; zero spend; no network")
            result = {
                "approval_id": approval_id,
                "action": "local_cpu_experiment",
                "actor": args.actor,
                "scope": "offline fixture; zero spend; no network",
            }
        elif args.command == "approve-crossref":
            from .literature.crossref import approval_scope

            scope = approval_scope(args.query, args.max_results)
            approval_id = store.approve("network_tool", args.actor, scope)
            result = {"approval_id": approval_id, "action": "network_tool", "actor": args.actor, "scope": scope}
        elif args.command == "approve-doi":
            from .literature.crossref import doi_approval_scope

            scope = doi_approval_scope(args.doi)
            approval_id = store.approve("network_tool", args.actor, scope)
            result = {"approval_id": approval_id, "action": "network_tool", "actor": args.actor, "scope": scope}
        elif args.command == "approve-skill":
            from .skills.registry import SkillRegistry, skill_approval_scope

            skill = SkillRegistry(root / "skills").load("literature-evidence-review")
            scope = skill_approval_scope(skill)
            approval_id = store.approve("skill_activation", args.actor, scope)
            result = {"approval_id": approval_id, "action": "skill_activation", "actor": args.actor, "scope": scope}
        elif args.command == "run-literature-agent":
            from .agents.literature_graph import run_literature_graph

            result = run_literature_graph(
                store,
                query=args.query,
                max_results=args.max_results,
                run_key=args.run_key,
                output_root=args.out,
                checkpoints_path=args.checkpoints,
                crossref_approval_id=args.crossref_approval_id,
                skill_approval_id=args.skill_approval_id,
                skill_root=root / "skills",
                direct_doi=args.doi,
            )
        else:
            result = run_research(
                store,
                root / "examples/offline_research/offline_fixture.csv",
                args.out,
                approval_id=args.approval_id,
                run_key=args.run_key,
                pause_after_seed=getattr(args, "pause_after_seed", None),
            )
    finally:
        store.close()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
