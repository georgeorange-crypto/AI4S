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
