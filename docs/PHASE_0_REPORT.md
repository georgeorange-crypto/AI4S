# AI4S Research OS — Phase 0 Acceptance Report

Date: 2026-11-12
Status: **Phase 0 implementation complete with the explicitly listed limitations below.**

## 1. Implemented

- Six replaceable layers: CLI workspace (`ai4s/cli.py`); typed FastAPI control plane and SQLite workflow journal (`ai4s/api.py`, `ai4s/core.py`); deterministic research workflow (`ai4s/workflow.py`); candidate and runtime capability registries (`ai4s/registry.py`, `ai4s/orm.py`); checked-in CPU fixture execution; SQLAlchemy domain persistence with Alembic migrations; content-addressed local JSON artifacts. Domain contracts are in `ai4s/domain.py`; vendor-neutral ports in `ai4s/ports.py`.
- Research entities include project, question, source, paper snapshot, claim/evidence edge, hypothesis, experiment contract/run, artifact, budget, approval, workflow/event, resource, source observation, discovery index, and capability entry.
- SQLite is the fully offline execution profile. PostgreSQL is the API/control-plane profile. They share domain concepts, but the offline experiment CLI is not yet wired to PostgreSQL worker dispatch; neither profile silently mirrors writes into the other.
- Registry ingestion preserves 100 resource records and 43 discovery-index records with raw payloads and per-source observations. Normalized URL calculation produced **139 unique URLs across 143 records**. SQLAlchemy/PostgreSQL catalog entities are URL-deduplicated; source observations preserve original resource rows. Discovered projects remain disabled.
- A project-local runtime capability registry reports exact dependency versions, source, license, risk, permissions, secret needs, and smoke evidence. `GET /api/v1/capabilities` lists those reviewed runtime capabilities; `GET /api/v1/resources` keeps discovery candidates separate.
- Workflow controls, legal transitions, event audit, human approval records, idempotency keys, pause/resume/cancel, run-count and elapsed-time budget enforcement, and persisted failure messages. Crash/reopen test exits the child process after a persisted seed checkpoint and verifies resume does not duplicate that seed.
- WSL Docker Compose setup uses the existing WSL Docker engine, PostgreSQL 16, a loopback-only API, pinned image digests, non-root API container, read-only root, dropped Linux capabilities, no-new-privileges, CPU/memory limits, named DB volume, and `.env` credentials. Project ports are configurable in `.env` and no WSL daemon/service configuration is changed by the repository.

## 2. Reused

Direct software used by the implementation is inventoried with source/license/maintenance/risk/permissions/secrets/evidence in `registries/runtime_dependency_audit.json`; transitive Python package versions are pinned in `requirements.lock` and `requirements-dev.lock`.

| Component | Version / license | Actual use and verification |
|---|---|---|
| FastAPI | 0.162.4 / MIT | API routes; API contract tests and live WSL PostgreSQL smoke |
| Pydantic | 2.14.3 / MIT | request/response validation; rejection contract test |
| SQLAlchemy | 2.1.8 / MIT | typed persistence models; SQLite migrations and live PostgreSQL operations |
| Alembic | 1.20.1 / MIT | revisions 0001 and 0002; SQLite and WSL PostgreSQL upgrade |
| Psycopg | 3.3.9 / LGPL-3.0-only | PostgreSQL driver; migration, CRUD, catalog import smoke |
| Uvicorn | 0.54.0 / BSD-3-Clause | serves API container; live `/healthz` |
| Docker Compose | existing WSL CLI 5.1.0 / Apache-2.0 | built and ran this repository's API and PostgreSQL services |
| Official Postgres image | 16-alpine, pinned digest | live ready check, migrations, API and registry smoke |
| Official Python image | 3.12-slim, pinned digest | API image build and live service |
| pytest / Ruff / mypy | 9.0.3 / MIT; 0.14.5 / MIT; 1.19.0 / MIT | offline tests, lint/format and static checks |
| httpx2 / setuptools | 2.16.0 / BSD-3-Clause; 84.2.1 / MIT | ASGI tests and pinned editable package build |

Official LangGraph, Agent Skills, MCP, OpenHands and MLflow entry points were checked for future adapter boundaries and recorded in `docs/DECISIONS.md`. They are **not integrated**. The 143-row discovery inventory is not evidence of source/license/runtime verification for those candidates.

## 3. Tests run

Final local commands (Python 3.12.7, `.venv`):

- `.venv\Scripts\python.exe -m pytest -q` — **10 passed, 0 failed**. Covers fixed fixture, approval denial, pause/cancel, max-run and elapsed-time budget limits, persisted errors, idempotent resume after child-process hard exit, API validation/control/events/registry, and SQLite Alembic schema.
- `.venv\Scripts\ruff.exe check ai4s tests migrations scripts` — **All checks passed**.
- `.venv\Scripts\ruff.exe format --check ai4s tests migrations scripts` — **17 files already formatted**.
- `.venv\Scripts\mypy.exe ai4s` — **Success: no issues found in 10 source files**.
- `.venv\Scripts\python.exe -m ai4s.cli import-registry --db .ai4s/registry-final.sqlite` — 100 resource records/entities, 43 discovery records/entities, 143 total source records, **139 unique normalized URLs**; SQLite `integrity_check=ok`.
- WSL Compose: `docker-compose config -q`; build/start PostgreSQL and API; `pg_isready` reported accepting connections; `alembic current` reported `0002_capability_registry (head)`. Live HTTP smoke created a project/question/workflow, paused then resumed it, and read the 3 persisted events. API returned 100 discovered resources and 14 runtime capabilities (all 14 have smoke evidence in the audit registry).
- Offline artifact verification recomputed fixture SHA-256 `4d18f52435537c0c830f5867ffda4af31c4e7f62ebe9fb41d4fa4ac9d412f85f`, matched raw artifact SHA-256 `d227e045b574e26f7e405e7113a09ba482309fbf85ac1b10c813b64fbfed2bd2`, and report SHA-256 `8c68c7e7c8d3bc7e8d1c26023295bb8ffd92499ae85b60c1553cf7fc0e829275`. The report artifact record in SQLite matches the latter report digest.

Observed issues and dispositions: the first zero-second wall-time budget test exposed a comparison-boundary bug; it was fixed (`>=`) and the retained test then passed. Renaming the budget from CPU seconds to wall seconds initially left one stale attribute reference; mypy and four tests caught it, it was fixed, and final checks passed. `ruff format --check` initially found the newly added test needed formatting; formatter ran and final checks passed. WSL's buildx plugin failed with a local input/output error, so Compose was built successfully with the existing WSL classic builder (`DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0`). The host kernel warned that swap limits are unavailable; memory limits still apply without swap accounting. The first registry-import shell invocation omitted the port because the local `.env` only had the database URL; it was rerun using that URL, and explicit default ports were added to `.env`. Import/API checks passed. A first inline artifact-hash command had PowerShell quoting issues; the same assertions were rerun as a multiline Python check and passed. The project does not alter the WSL daemon or service setup.

## 4. Real research demo

- **Question:** Does a threshold using only `x1` match or improve a majority-class baseline on held-out synthetic labels defined by `x1 + x2 > 0`?
- **Evidence:** checked-in `offline_fixture.csv`, plus `fixture_notes_untrusted.txt`; the conflicting note is labeled disputed and excluded. No external citation or DOI is claimed.
- **Hypothesis:** the one-feature threshold may improve held-out accuracy, but omits a feature used to generate labels. Intent is exploratory.
- **Contract:** majority baseline vs. x1-only threshold, fixed 25% split per seed, seeds 11/23/37, max 30 seconds and 3 runs, no network/GPU/spend, explicit persisted local approval.
- **Hashes:** code `8ff01e4b500675c84b6745e6c1aba94532266e5448c7c0894b380b3d0b14d2e4`; config/contract `9df9f56a5a84bf0374bb2da6ac8fa151f3c8eabdbd86edc0208b943b668715fe`; data `4d18f52435537c0c830f5867ffda4af31c4e7f62ebe9fb41d4fa4ac9d412f85f`; dependency lock `5ccf9f8d8d0a2536ebce1da738563f909b7560e77377a630ea90667989df1559`.
- **Approval:** the report records persisted approval `896b6835-27d9-4717-b1e7-fcd9756ee67a`, action `local_cpu_experiment`, decision `approved`, actor `codex-user-instruction`, scope `offline fixture; zero spend; no network`.
- **Runtime:** Python 3.12.7, Windows 11, AMD64 CPU (`AuthenticAMD`, Family 25 Model 97 Stepping 2), no accelerator.
- **Artifacts:** committed `examples/offline_research/results/research_report.json` (SHA-256 `e2a4c92aaf5b5cf3f056a4dcb45a832cf30fae69832b610b7abada9fcc4be74d`) and content-addressed raw JSON artifact (SHA-256 `b460c1f7aef5969698a00017b8ae9c0347211a4a7ca2411b2404e23e9dae2f2f`). Both digests were recomputed from disk. The SQLite artifact record also stores the report digest; the JSON report does not self-reference its own hash.
- This is a tiny synthetic software-validation fixture. It is neither an established benchmark nor evidence of scientific generalization or novelty.

## 5. Security and provenance checks

- Resource and discovery input is parsed as data only; no discovered package or skill is installed or executed.
- Unapproved remote execution, publication, network tools, and unknown actions are denied in the offline policy. Local experiment requires a stored approval record. API is loopback-bound by Compose and has **no user authentication**, so it must remain local/trusted.
- No agent is given a host shell, Docker socket, SSH keys, home directory, or secrets. The fixture executor only runs checked-in deterministic Python logic; it does not execute arbitrary user/agent code.
- Each run report records code/config/data SHA-256, Python/platform, CPU-only declaration, timestamps, seeds, raw per-seed metrics, budget, exceptions and artifact hashes. No model was used.
- The user’s WSL daemon was not reconfigured. Verification used the WSL Docker CLI; when no default socket/service was available, an isolated temporary daemon and temporary project volume were used and are removed after checks.

## 6. Not implemented / limitations

- No web UI, model gateway, agent harness, LangGraph, Skills execution, MCP client, OpenHands sandbox adapter, literature API/DOI verification, external citation retrieval, MLflow, Inspect AI, GPU/Slurm, object store, telemetry, or production authentication/authorization.
- PostgreSQL API records and offline SQLite executor records are separate persistence profiles; there is no PostgreSQL-backed research worker or API endpoint that launches the offline run.
- There is no arbitrary-code executor. This is deliberate: Phase 0 executes repository-owned fixture code only, not paper/skill/prompt-supplied instructions.
- Python 3.12 is the verified full stack environment. The pure research core is Python 3.10+; older global host Python had a `.pth` startup encoding error, so the repository documents a project virtual environment.
- WSL Docker user preference is honored by Compose and README. Ports 54329/8000 are defaults, not assumed free; users can select alternatives in their ignored `.env` before startup.

## 7. Next concrete actions

Phase 0 is frozen after this acceptance commit. Phase 1 should first make PostgreSQL the durable worker store or formally retain and test SQLite as an independent local profile, then integrate one real literature metadata adapter with source/license/maintenance review, HTTP fixtures, rate limits, and contract tests. Add authentication before exposing the API beyond loopback. Do not enable model, MCP, Skill, benchmark, GPU, or remote execution integrations without their own gates.
