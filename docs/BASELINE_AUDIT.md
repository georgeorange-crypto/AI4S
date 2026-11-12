# Baseline audit — 2026-11-12

## Scope and method

Read `README.md`, `AGENTS.md`, all files in `docs/`, `configs/`, and the two discovery registries before implementation. Enumerated the workspace with `rg --files`; inspected the top-level source records and counted the JSON arrays with PowerShell `ConvertFrom-Json`. Git root is this workspace; baseline commit is `ef6db8e` (`chore: initialize AI4S project`). At audit start, `README.md` was already modified and the supplied `AGENTS.md`, `configs/`, `docs/`, `prompts/`, and `registries/` were untracked inputs. Those pre-existing changes were preserved.

## Existing implementation and actual checks

- Existing runtime source, package metadata, dependency lock, migration, API, CLI, worker, UI, sandbox, fixture, and test files: **none**. The repository starts as a documentation and resource-catalog blueprint.
- Existing tests: **none found**. There is no pre-existing test command to run.
- Python available during audit: **3.10.11**. Docker, package installation, and external service availability were not established by this audit.
- The documentation describes the intended six-layer architecture and workflows; these are design statements, not implemented behavior.

## Discovery inputs

- `registries/original_resource_catalog.json`: **100** source records. Fields: category, name, organization, url, role, integration_mode, priority, adoption_risk, notes.
- `registries/discovery_indexes.json`: **43** source records. Fields: type, name, url, authority, priority, description_zh, project_use, date_checked, verified, notes.
- These counts are record counts, not unique project counts. Resource records and discovery indexes have distinct semantics and will be preserved separately; URL normalization/deduplication is computed by the importer and does not imply license, maintenance, installation, or runtime verification.
- Actual normalized URL count across both inputs: **139 unique URLs among 143 records**. The 100 resource records map to 100 normalized URLs; all 43 discovery source records are retained separately even when their URL overlaps a candidate.
- The catalog documents no per-candidate completed source/license/maintenance/smoke-test audit. Therefore none of the third-party candidates is asserted as integrated by this baseline.

## Reusable designs and decisions to implement

- Six logical layers: Workspace; Control Plane; Agent Intelligence; Capability Registry; Execution Plane; Data/Knowledge, with policy/provenance cross-cutting.
- Typed domain ports, one authoritative workflow state machine, append-only events, offline fixtures, bounded CPU execution, checksummed artifacts, and human approval for privileged actions.
- Reuse targets from the design: FastAPI/Pydantic, LangGraph, MCP, Agent Skills, OpenHands, MLflow, Inspect AI, Temporal, Slurm/Apptainer. They remain candidates until source/license/maintenance/risk review and a real smoke/contract test establish whether to adopt them. For the first offline slice, Python standard library + SQLite avoids adding an unverified dependency and provides an actual local tracking backend.

## Phase 0 baseline outcome

No runnable research workflow existed. Phase 0 therefore begins with a small Python package, SQLite-backed domain/event store, deterministic local fixture experiment, content-addressed artifacts, resource registry ingestion, CLI, and tests. This is an initial offline core, not completion of the blueprint's Postgres/FastAPI/UI or third-party integrations.

## Phase 0 implementation disposition (2026-11-12)

The repository now contains a working offline SQLite research loop plus a separately persistent FastAPI/PostgreSQL control-plane profile. It includes runtime capability discovery, Alembic schema, WSL Compose, crash/resume and API tests, and an actual fixture report. See `PHASE_0_REPORT.md` for exact final commands and limitations. The two persistence profiles are not yet joined by a PostgreSQL-backed worker; no model, paper API, MCP, Skills, MLflow, arbitrary-code sandbox, UI, or GPU integration is claimed.
