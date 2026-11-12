# AI4S Research OS — Delivery Roadmap, Backlog and Verification

## Phase semantics

P0 is the minimum usable research backbone; P1 is real integration and autonomous experiment loop; P2 expands to long-running productivity and HPC. Each phase is independently verifiable. The coding agent should *implement code, run test, and report output* at each phase, not simply deliver plans.

## Phase 0 — Reproducible Research Core

**Deliverables:**

1. Monorepo with FastAPI, Python packaging, lint/test/type checks, Postgres migrations, Docker Compose and optional slim Next.js UI; working CLI. All core services boot with documented commands.
2. Import existing `registries/` seed resources (100 + 43 entries), preserve original discovery records and deduplicate by normalized canonical links. Counts of unique entities are calculated, not guessed.
3. Typed models for Project, ResearchQuestion, Source, ClaimEvidence, Hypothesis, ExperimentContract, ExperimentRun, Approval, Artifact, Budget, WorkflowEvent.
4. Research workflow state machine, append-only events, approval policy, offline fixture paper source and CPU-only experiment executor.
5. MLflow tracking or documented local tracking backend with actual experiment artifacts and checksums; no reliance on paid APIs.
6. README, AGENTS.md, architecture ADRs, tests and actual generated sample report.

**Acceptance:**

- `docker compose up -d` plus documented initial setup works in a clean development environment (if Docker available).
- `pytest` and package lint/type checks pass; statuses are backed by state.
- offline end-to-end command creates a stored research run and real CPU experiment artifacts.
- restart/kill test preserves workflow state and avoids duplicate execution.
- exhausted budget and unauthorized tool attempts are stopped and audited.
- sample report references actual artifacts and test outputs, includes any missing validations.

## Phase 1 — Research Sources, Skills, Agents

### Status update — 2026-11-12

Phase 1.1 delivered a model-free Crossref + Agent Skills + in-process MCP + LangGraph SQLite checkpoint slice. See `PHASE_1_REPORT.md`. The complete Phase 1 acceptance remains open: semantic/arXiv sources, literature-driven idea/hypothesis selection, and an approved experiment handoff are not implemented.

**Deliverables:**

1. Official adapters for Semantic Scholar and arXiv, Crossref DOI verification, optional OpenAlex; recorded HTTP fixtures and rate limiting. Missing credentials gracefully degrade.
2. Claim/evidence linking to source identifier and location; citation verifier and contradiction display.
3. LangGraph workflow with checkpoint persistence and 3–5 specialized role configurations; model gateway behind provider interface; no provider assumed.
4. Agent Skills-compatible registry, skill installer with explicit review, capability tags and permission constraints; run skill regression tests.
5. MCP client with allowlist and audited registration; document model/skill/tool selection reasons.
6. OpenHands or other mature Code Agent adapter in a sandbox, prove execution and cancellation; no arbitrary host execution.
7. Minimal UI showing task/approval/metrics/provenance/trace events.

**Acceptance:** end-to-end paper search + evidence verification + idea selection + sandbox code experiment, with one actual tool invocation, tool failures correctly surfaced, costs and credentials bounded, no fake citations.

## Phase 2 — Quality Gates and HPC-Aware Autonomous Research

**Deliverables:**

1. Inspect AI evaluation adapter with a reproducible small task suite; optional AstaBench, PaperBench, MLE-bench and KernelBench profiles only when permissions/data permit.
2. Scientific experiment optimizer: baseline, candidate, seeds, statistical report, negative results, budget and stopping criteria.
3. GPU/HPC executor (Slurm/Apptainer as applicable) with authorized job templates, timeouts, polling, cancel, idempotency, no login-node heavy compute.
4. Trace backend (Phoenix OR Langfuse), OpenTelemetry, model and compute cost accounts.
5. Automated Research Radar with schedules and digests, Zotero sync optional.
6. Evaluate transition to Temporal if multi-day durability/retry/approval requirements warrant it; migration test preserves task IDs and event history.

**Acceptance:** one real GPU or HPC run on authorized infrastructure, recorded device/runtime/config version and full metrics; benchmark comparison only matched protocol; failure-resume after worker restart and failed external request.

## Phase 3 — Specialization and Scientific Publication Support

1. AI Systems profile: GPU kernel profiling, TTFT/throughput/memory and regression guardrails.
2. ML/AI profile: RD-Agent/AIDE/autoresearch comparisons or wrappers under fixed benchmarks.
3. Agent/Harness profile: context compression/retention, tool-feedback accuracy, multi-turn long-run evals.
4. Draft/figure/rebuttal assistance grounded in verified results; conference PolicyRegistry and human approval for submissions.
5. Multi-project scheduling, versioned capability selection and automated resource discovery refresh.

**Acceptance:** per-domain experimental results, no hidden benchmark contamination, honest limitations; well-documented user control and provenance.

## Mandatory engineering practices for every phase

- Create small issues/PRs or commits; no giant opaque rewrite.
- Use official references and source pinning; never assume online blog code is still current.
- Implement full vertical slices over empty placeholder interfaces.
- Update `docs/DECISIONS.md` with trade-offs and discarded frameworks.
- Record exact setup/test commands and their output; independent reproducibility is more important than screenshot quality.
- Never remove a hard test merely to get green CI.
- Keep feature flags around integrations until they have passed a real smoke test.
- Avoid installing remote plugins or network dependencies merely because they appear in discovery lists.
- Retain source date and licensing status for each new resource.

## Realistic boundary of this blueprint

All documents are design artifacts. They are not proof that an AI4S platform already exists, that third-party services are connected, or that paid APIs or GPU environments are authorized. Codex should create implementation, show actual tests and log limitations truthfully.

## Phase 0 acceptance record (2026-11-12)

Phase 0 code, offline report, migrations, registry, tests, WSL Compose smoke evidence and limitations are recorded in `PHASE_0_REPORT.md`. The Compose stack was built and tested with the existing WSL Docker environment; the repository does not reconfigure Docker or WSL. Runtime ports are configurable through local ignored `.env`. API has no authentication and remains loopback-only. The API/PostgreSQL profile and offline SQLite CLI are not yet wired together through a worker. Phase 1 must address that boundary and add one audited literature adapter before enabling agents or remote tools.
