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

Semantic Scholar, arXiv, OpenAlex; remote MCP servers/transports; model provider gateway; model-generated literature synthesis/hypotheses/idea selection; full-text passage evidence; graph-node pause/cancel; OpenHands or another code sandbox; literature-to-approved-experiment-to-CPU-run handoff; and UI. Full Phase 1 acceptance remains open.

## 7. Next actions

1. Add multi-candidate DOI/author reconciliation to reduce same-title metadata poisoning.
2. Add evidence intake → human-reviewed hypothesis → approved experiment contract → existing P0 CPU runner, without enabling a model.
3. Integrate one more official paper API only after an independent source/license/permission/contract/smoke audit.
4. Add graph-level pause/cancel after defining interruption and approval semantics.
