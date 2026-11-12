# Architecture decisions

## ADR-001 — Two explicit persistence profiles in Phase 0

**Decision:** keep the offline executor on SQLite (`ResearchStore`) so fixture runs require no service, secret, or network; use PostgreSQL through SQLAlchemy/Alembic for the API/control-plane profile. Both represent the same domain concepts, but writes are not mirrored and the CLI executor is not PostgreSQL worker-dispatched.

**Reason:** satisfies offline reproducibility while providing a real PostgreSQL API environment in the user's existing WSL Docker. The limitation is explicit and a Phase 1 task. Do not imply PostgreSQL is the store behind the current CLI run.

## ADR-002 — One business workflow state machine per profile

Workflow state/events are authoritative in one configured store for each profile. Agent reasoning checkpoints, if added, will not own business workflow state. No second business orchestrator is installed; Temporal remains a future option after measured need.

## ADR-003 — Discovery and audited capabilities are separate registries

The 100 resource records and 43 discovery indexes preserve source payload and source observations. Canonical URL deduplication is calculated (139 unique URLs across 143 records). All discovery candidates default to `discovered`, license `unknown`, and risk `unreviewed`. The smaller runtime dependency registry lists only packages/images actually used, their licenses, permissions, risk and test evidence.

## ADR-004 — Deterministic offline research before agents

The first CPU experiment is repository-owned deterministic code against a checked-in fixture. It records a simple baseline, candidate, three seeds, hashes and raw metrics. A conflicting fixture note remains disputed. This validates provenance and recovery mechanics; it is not a scientific benchmark.

## ADR-005 — Fail closed on privileged actions

The offline CLI requires a persisted local approval. Remote execution and external publication require explicit matching approvals and remain unimplemented. Unknown actions are denied. As of Phase 1.1, the only active network adapter is the read-only Crossref metadata adapter; it requires one-use persisted approval bound to an exact query scope or DOI and does not fetch abstracts. Compose binds API/database ports to loopback; API has no authentication and must not be exposed publicly.

## ADR-006 — WSL Docker is the selected local container environment

The user confirmed the workstation has Docker in WSL. Compose targets the existing WSL engine and makes no Docker Desktop, WSL service, or daemon configuration changes. PostgreSQL/API ports have overridable defaults in `.env`; credentials remain local and ignored by Git. This development environment was smoke-tested with the WSL Compose CLI and PostgreSQL.

## Official integration entry points checked — 2026-11-12

These official sources informed adapter boundaries; they do **not** imply installation or integration:

- LangGraph persistence/checkpointer: https://docs.langchain.com/oss/python/langgraph/persistence
- Agent Skills format: https://agentskills.io/specification
- MCP security guidance: https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices
- MCP Python SDK: https://py.sdk.modelcontextprotocol.io/
- OpenHands SDK source: https://github.com/OpenHands/software-agent-sdk
- FastAPI tutorial/release notes: https://fastapi.tiangolo.com/tutorial/ and https://fastapi.tiangolo.com/release-notes/
- MLflow Tracking: https://mlflow.org/docs/latest/tracking/

Direct dependencies/images actually used, exact versions, license, source, maintenance evidence, scope, risk and smoke evidence are listed in `registries/runtime_dependency_audit.json`. No candidate from the broad discovery catalog is activated automatically.

## ADR-007 — Model-free Phase 1 literature/tool graph slice

**Decision:** add one bounded Crossref adapter, a reviewed Agent Skills-compatible metadata-only skill, the official MCP Python SDK in-process server/client, and LangGraph with its official SQLite checkpointer. Keep the business run and approvals in `ResearchStore`; graph checkpoints only resume node state. Every network query or exact DOI lookup and skill activation requires a persisted one-use approval before egress. The optional integration is not imported by the offline core workflow.

**Reason:** the user requested tool and graph-workflow acceptance before enabling any model. A deterministic metadata-only graph can validate permissions, tool contracts, provenance, checkpoint recovery and raw artifacts without model keys, GPU, or fabricated research reasoning. Crossref abstracts are excluded at the API request level. The search smoke surfaced title-matched but unrelated posted-content records, so search ranking is treated as untrusted discovery and not citation verification; an exact DOI filter is supported separately. No claim-support inference or automatic idea selection is made.

**Limitations:** only Crossref is wired into this graph. arXiv has a separate approved direct CLI adapter with offline contract coverage, but it is not wired into the LangGraph/MCP source/evidence flow and has no live provider smoke yet. Semantic Scholar/OpenAlex and external Skills/MCP servers are not enabled. MCP is in-process and local to this adapter, not a general remote MCP connector. No model gateway, idea generation, pause/cancel control for graph nodes, sandboxed code agent, or hypothesis/experiment release workflow has been added. See `docs/PHASE_1_REPORT.md` and `examples/literature/phase1-smoke/evidence_manifest.json`.

## ADR-008 — Optional local MLflow plus bounded arXiv client (2026-11-12)

- **MLflow:** choose `mlflow-skinny==3.18.0` behind an optional `research` extra and a local-only `MlflowClient` adapter. Use SQLite because the reproducible fixture is local/CPU and SQLAlchemy is already part of the base stack. Do not enable a tracking server, remote URI, autologging, or model provider for this slice. Acceptance evidence is `tests/test_mlflow_tracking.py` plus a real CLI fixture run.
- **Literature provider:** choose the maintained `arxiv.py==4.0.2` API client rather than maintaining Atom parsing and pagination in-house. Keep it separate from the Crossref adapter; require exact query/result-cap approval, cap each call at five records, use a shared persistent 3.1-second SQLite limiter in the CLI, disable SDK retries, and preserve original response bytes. The SDK does not expose a public raw-response hook, so the pinned adapter uses its private requests session hook and fails closed if the expected hook interface changes.
- **Acceptance boundary:** arXiv's offline response/approval contract is tested, but no live arXiv request has been made. It is not yet connected to the LangGraph/MCP literature workflow. This decision does not mark arXiv as a fully accepted provider integration.
- **License/operations:** MLflow is Apache-2.0; arxiv.py upstream is MIT. arXiv API usage terms require a single connection and at least three seconds between requests across operator-controlled systems. The optional dependency lock is separate so the API image and default install do not acquire either integration.
