# Phase 1 report — 2026-11-12

**Acceptance status: Phase 1.1 (literature tools and persistent graph slice) implemented and exercised. Phase 1 as a whole is not accepted.** The user selected no model integration for this acceptance.

## 1. Implemented

- `ai4s/literature/crossref.py`: read-only Crossref title search and exact DOI-filter lookup, query/DOI approval scopes, selected-field allowlist, response size/timeout/rate bounds. Abstract is excluded from requests.
- `ai4s/skills/registry.py` and `skills/literature-evidence-review/SKILL.md`: Agent Skills-compatible manifest, `yaml.safe_load`, file and symlink limits, tool/permission/rule allowlists, bundle SHA-256, one-use approval for activation. Skill scripts are not executed.
- `ai4s/agents/literature_graph.py`: LangGraph checkpoint plus MCP SDK in-process Client/Server. Fixed search/resolve/report nodes; no model calls. Business approvals/events and graph checkpoints use separate SQLite stores. A failed node is attempted once; retry resumes a successful prior node from the same thread checkpoint.
- `ai4s/cli.py`: `approve-crossref`, `approve-doi`, `approve-skill`, and `run-literature-agent`. Approvals bind to a normalized query hash/result cap or exact DOI and the Skill content hash. Completed runs return their saved report idempotently.
- `ai4s/core.py`: atomic one-use approval consumption and literature run/tool-call/raw-snapshot/evidence/event tables.
- `requirements-agents.lock`, `registries/runtime_dependency_audit.json`, and live smoke evidence under `examples/literature/phase1-smoke/`.

## 2. Reused

| Component | Reused interface | Status |
|---|---|---|
| LangGraph 1.2.21 / MIT | `StateGraph`, thread IDs, graph checkpoint state | Installed, tested |
| langgraph-checkpoint-sqlite 3.1.3 / MIT | Official SQLite saver; JsonPlus msgpack allowed modules set empty | Persistence and resume tests |
| MCP Python SDK 2.3.0 / MIT | `MCPServer.tool` and `Client.call_tool` | Actual in-process SDK calls tested; no external MCP server |
| PyYAML 6.0.3 / MIT | `yaml.safe_load` for Skill frontmatter | Unsafe tag and unknown tool tests |
| Crossref REST API | `/works` title query; `/works?filter=doi:…&select=…` exact DOI lookup | Approved live HTTP smoke; abstracts excluded |

The title-search smoke surfaced three same-title posted-content records unrelated to the expected paper. Search results remain untrusted discovery data. A first DOI lookup implementation used `/works/{doi}?select=…`, which Crossref rejects with HTTP 400; the original search response and error were retained, and the adapter was corrected to use the official DOI filter on `/works` with `select`. A subsequent exact DOI smoke succeeded. Crossref documents its filter endpoint and selected-field parameter separately ([REST API filters](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/), [REST API tips](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)). This checks metadata identity only, not scientific claim support.

## 3. Tests run

- `.venv\Scripts\python.exe -m pytest -q`: **19 passed**.
- `.venv\Scripts\ruff.exe check ai4s tests`: passed.
- `.venv\Scripts\ruff.exe format --check ai4s tests`: **20 files already formatted**.
- `.venv\Scripts\python.exe -m mypy ai4s`: **Success: no issues found in 17 source files**.
- `.venv\Scripts\python.exe -m pip check`: **No broken requirements found**.
- The offline suite covers query/result limits, malformed DOI/oversized/invalid JSON responses, unsafe YAML and unknown tools, no-egress without exact approval, real SDK dispatch, artifact hashes, checkpoint persistence, resume without repeating the completed search node, approval consumption, and idempotent repeat.
- Evidence manifest validation: **2 raw response snapshots verified across 3 recorded live runs**.

## 4. Real integration smoke

- Successful bounded request: DOI `10.18653/v1/N19-1423`; Crossref returned the BERT paper (2019), ACL publisher/proceedings, authors, title, and pages. A one-use exact DOI approval and Skill activation approval were recorded before egress.
- The smoke used no API key, mailto identifier, model, GPU, external write, full text, or abstract.
- Raw JSON bytes, SHA-256, request metadata, failure records, and reports are retained in `examples/literature/phase1-smoke/`. The manifest rechecks byte hashes.
- The title search's suspicious same-title results and the initial HTTP 400 are recorded as failures/negative evidence, not as passing lookup results.
- This is a metadata API smoke, not a benchmark, paper-claim verification, or novelty evaluation.

## 5. Security and provenance

- Network is not triggered by default. One-use approvals are atomically consumed before the call and bind either an exact query hash plus result cap or a DOI hash. Skill approval binds to Skill bundle SHA.
- Query is capped at 256 characters; results at five; timeout is 8 seconds; response size at 1 MB; request start spacing is at least 1.05 seconds and persisted in the shared SQLite DB across CLI processes using that DB; automatic tool retries are disabled.
- DOI syntax is validated; only selected fields are requested; response bytes, SHA, URL, time, tool call, and SQLite event are stored.
- Checkpoints use `JsonPlusSerializer(allowed_msgpack_modules=())`. `LANGSMITH_TRACING` is disabled. No shell tool or arbitrary code execution is available.
- External metadata is treated as untrusted data. DOI/title identity does not establish truth or support for a scientific claim.

## 6. Not implemented

Semantic Scholar and OpenAlex; arXiv graph/MCP integration and live provider smoke; remote MCP servers/transports; model provider gateway; model-generated literature synthesis/hypotheses/idea selection; full-text passage evidence; graph-node pause/cancel; OpenHands or another code sandbox; literature-to-approved-experiment-to-CPU-run handoff; and UI. Full Phase 1 acceptance remains open.

## 7. Next actions

1. Add multi-candidate DOI/author reconciliation to reduce same-title metadata poisoning.
2. Add evidence intake → human-reviewed hypothesis → approved experiment contract → existing P0 CPU runner, without enabling a model.
3. Integrate one more official paper API only after an independent source/license/permission/contract/smoke audit.
4. Add graph-level pause/cancel after defining interruption and approval semantics.

---

# Phase 1.2 report — local MLflow + arXiv tool slice (2026-11-12)

**Acceptance: MLflow local Tracking adapter accepted by offline CPU contract and CLI run. arXiv adapter/CLI has offline contract coverage but no live provider smoke; arXiv is not yet accepted as a live provider integration. Phase 1 overall remains open.** Models remain disabled.

## 1. Implemented

- `ai4s/tracking/mlflow_local.py`: optional MLflow client adapter; persistent SQLite URI only, completed reports only, workflow-id idempotency, run parameters, seed metrics, JSON artifact checksum/readback, mismatch refusal. MLflow import is lazy and tracking is opt-in via `--mlflow`.
- `ai4s/literature/arxiv_adapter.py`: pinned `arxiv.py` Client/Search interface; one bounded metadata query (1–5 results), one captured raw Atom response, normalized bibliographic fields, no PDF/source download, mandatory exact-scope approval consumer, and 8-second request timeout. CLI holds a shared SQLite write lock throughout each request and spaces starts by 3.1 seconds, preventing concurrent API connections across processes that share the research DB.
- `ai4s/cli.py`: `approve-arxiv` and `search-arxiv`; query hash/result cap approval is consumed once before egress. Raw Atom bytes are saved as a content-addressed artifact plus a JSON metadata receipt.
- `pyproject.toml`, `requirements-research.lock`: optional and separately pinned integrations, not added to the API/runtime base image.
- `registries/runtime_dependency_audit.json`: actual status and runtime risks recorded. arXiv is explicitly marked `offline-contract-tested-live-smoke-not-run`.

## 2. Reused

| Project/API | Interface | Verified status |
|---|---|---|
| MLflow `mlflow-skinny==3.18.0`, Apache-2.0 | `mlflow.tracking.MlflowClient`; local SQLite tracking store and artifact API | Real fixture workflow logged and read back; idempotent second call verified. No tracking server or remote URI. |
| `arxiv==4.0.2`, upstream MIT | `arxiv.Client.results(arxiv.Search(...))`; requests response hook captures original Atom bytes | Installed pinned SDK and introspected actual client/session/Search signatures; offline contract with a raw Atom fixture passes. No live API request made. |
| SQLite, already part of AI4S | Reused `network_rate_limits` table through `SQLiteRateLimiter` | CLI uses the `arxiv` bucket, a held cross-process lock during the request, and 3.1-second start spacing. Contract test verifies another DB connection cannot acquire a write slot until the request releases it. |

Sources reviewed: [arxiv.py PyPI release](https://pypi.org/project/arxiv/4.0.2/), [arxiv.py upstream releases](https://github.com/lukasschwab/arxiv.py/releases), [arXiv API terms and rate limit](https://info.arxiv.org/help/api/tou.html), [MLflow Tracking](https://mlflow.org/docs/latest/tracking/), [MLflow Tracking API](https://mlflow.org/docs/latest/tracking/tracking-api/), [mlflow-skinny PyPI](https://pypi.org/project/mlflow-skinny/3.18.0/). arXiv terms require one connection and no more than one API request every three seconds across systems under the operator's control. The API feed can include abstract text supplied by arXiv; the adapter does not download PDFs, source files, or full text.

## 3. Tests and real commands

- Focused contract: `.venv\Scripts\python.exe -m pytest tests/test_mlflow_tracking.py tests/test_arxiv_adapter.py -q` — **9 passed**.
- Full offline suite after integration: `.venv\Scripts\python.exe -m pytest -q` — **28 passed** (one upstream SQLAlchemy deprecation warning from MLflow 3.18.0).
- Ruff check: `.venv\Scripts\ruff.exe check ai4s tests` — passed.
- Ruff format check: `.venv\Scripts\ruff.exe format --check ai4s tests` — passed after formatting.
- Dependency health: `.venv\Scripts\python.exe -m pip check` — no broken requirements.
- Pinned arXiv interface inspection verified actual `Client._session` response hooks, `Client.results(search, offset=0)`, and the `Search` signature. This is interface evidence, not an API smoke.
- Actual local end-to-end command: explicit `approve-local`, then `run-offline --run-key phase1-2-mlflow --mlflow --mlflow-db .ai4s/phase1.2/mlflow.db`. MLflow SQLite row status was `FINISHED`; report artifact SHA matched the local MLflow artifact.

## 4. CPU experiment artifact

- Question: does an x1-only threshold improve over majority baseline on the checked-in synthetic held-out fixture?
- Seeds: 11, 23, 37; 5 held-out examples per seed.
- Baseline accuracy: 0.2, 0.6, 0.4. Candidate: 0.4, 0.6, 0.8. Per-seed deltas: +0.2, 0.0, +0.4; mean delta +0.2. This small synthetic fixture supports only an exploratory signal, not a generalization or benchmark claim.
- Code SHA-256 (recursive `ai4s/**/*.py`): `b6877f0fd25f50c7cf963ab4aff8ad72f2eeba873d005a219b53b803b8025f87`; dataset SHA-256: `4d18f52435537c0c830f5867ffda4af31c4e7f62ebe9fb41d4fa4ac9d412f85f`; contract/config SHA-256: `9df9f56a5a84bf0374bb2da6ac8fa151f3c8eabdbd86edc0208b943b668715fe`.
- Ignored local report: `.ai4s/phase1.2/runs-final-lock/research_report.json`; raw results artifact SHA-256 `ffa8f2346f7990705a938980999c1b2b2561e5b79768f8d155677b0de8fa3a60`.
- MLflow run `523623540d024ff8bbeef0e837ff191b`, status `FINISHED`; report artifact SHA-256 `155485cabaf055d05d10d3d0f67906702c74f4d55ee6d0405f6c0b7467c90007`; CLI receipt artifact SHA-256 `25669d0be8a4b1180c7bf85b87da4fa135c5674d08fa30c04656528864a821a1`. A repeat CLI execution returned the same MLflow run id and artifact SHA with `reused: true`.

## 5. Security and provenance

- arXiv CLI does not request until the exact normalized query and result cap have an unused persisted approval; missing approval is rejected before network access and failures are recorded. The query is capped at 256 characters, results at five, SDK retries disabled, request timeout is 8 seconds, and the shared SQLite bucket enforces both single-connection serialization and 3.1-second request spacing. Raw response bytes are SHA-256-addressed.
- The adapter currently accesses the pinned SDK's private `_session` to install a raw-response hook. Version pin and offline contract protect this assumption; an upstream SDK change fails closed.
- MLflow remote tracking URIs, unfinished workflows, and same-workflow runs with missing/conflicting report artifacts are rejected. No autologging, remote server, model calls, or paid service.
- The live arXiv provider was not called. No arXiv record, paper citation, or successful network integration is claimed.

## 6. Not implemented / remaining acceptance gates

- arXiv is an approved direct CLI tool, not yet routed through the LangGraph/MCP literature workflow or stored as a literature-graph source/evidence edge.
- No arXiv live smoke because no exact human approval for a bounded live query was supplied in this work. No live rate-limit test was performed.
- OpenAlex/Semantic Scholar, full-text evidence passages, model providers, human-reviewed hypothesis → approved contract → CPU experiment handoff, and graph pause/cancel remain open.
- MLflow emits one upstream `SADeprecationWarning` inside its SQLAlchemy store. It does not fail tests but needs upstream resolution/version monitoring.

## 7. Next actions

1. After an exact arXiv query approval, run one metadata-only request and preserve raw feed/approval/artifact checksums as live smoke evidence.
2. Route arXiv through the existing MCP/LangGraph tool contract and source/evidence storage; record preprint status explicitly.
3. Add human-reviewed hypothesis and experiment-contract handoff while keeping model generation disabled unless separately selected.
