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

The offline CLI requires a persisted local approval. Remote execution, external publication, network tools and unknown actions require a matching approval and are not implemented as active adapters. Compose binds API/database ports to loopback; API has no authentication and must not be exposed publicly.

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
