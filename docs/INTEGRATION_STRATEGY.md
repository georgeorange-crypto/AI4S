# AI4S Research OS — Integration Strategy and Tool Matrix

## 1. Integration philosophy

Index broadly, deploy deliberately. A project found in a GitHub Awesome List is an **index candidate**, not an audited dependency. A benchmark entry is **evidence under its protocol**, not general proof of research ability.

### Lifecycle

`DISCOVERED → SOURCE_VERIFIED → LICENSE_REVIEWED → RISK_REVIEWED → SMOKE_TESTED → ADAPTER_READY → EVALUATED → ENABLED → MONITORED`.

Also allow: `API_ONLY`, `REFERENCE_ONLY`, `REJECTED`, `ARCHIVED`, `BROKEN`, `PAUSED`. Block enabling if license/security requirements incomplete. Record when and how verified, not only boolean.

Each stage stores inputs and evidence: original link, creator, source snapshots, commit/release, SPDX if verified, tool outputs, tests, logs, cost estimate, benchmark comparability, and integration notes.

## 2. Concrete initial matrix (prioritized for CS/AI)

| Capability | Preferred initial candidate | Fallback/alternate | Integration mode | Target phase |
|---|---|---|---|---|
| Academic paper search | Semantic Scholar, OpenAlex | arXiv, Crossref | API source adapters | P0/P1 |
| Paper evidence QA | Asta plugins, PaperQA | OpenScholar | skill/adapter after trial | P1 |
| Structured survey | STORM | GPT Researcher | subworkflow adapter | P2 |
| Research topic tracking | Awesome lists, HF Collections, arXiv RSS | GitHub topics, OpenReview | resource crawler w/rate limits | P1 |
| Idea search/critique | AI Scientist v2 / Google Co-Scientist mechanisms | Agent Laboratory, ResearchAgent | implementation *pattern*, optional licensed wrapper | P2 |
| Autonomous ML iterations | autoresearch | AIDE, RD-Agent | isolated experiment-runner wrapper | P1/P2 |
| Code Agent | OpenHands SDK | Codex, other coding agent | external runtime adapter | P1 |
| Agent graph | LangGraph | OpenAI Agents SDK, Google ADK | one runtime initially | P0 |
| Long task workflow | simple durable worker → Temporal | other workflow engines if justified | workflow-service interface | P2 |
| Cross-vendor models | LiteLLM | direct official SDKs | unified model policy | P1 |
| Skills | agentskills.io, Asta Skills | Orchestra Research, Anthropic Skills | manifest + sandbox & eval | P1 |
| MCP tools | official MCP client and registry | native adapter for non-MCP sources | transport only | P1 |
| ML experiment tracking | MLflow | W&B | official SDK | P0 |
| Dataset lineage | content checksums + DVC optional | object store metadata | official SDK/CLI | P1 |
| Agent evaluation | Inspect AI | AstaBench tasks | official testing integration | P1 |
| ML research evaluation | MLE-bench, AIRS-Bench | AutoResearchExam | test suite, not runtime dependency | P2 |
| GPU/AI systems eval | KernelBench, RE-Bench historical tasks | hand-verified domain tests | test suite / research fixture | P2 |
| Agent traces | OpenTelemetry + Phoenix OR Langfuse | framework built-in trace | trace backend adapter | P1 |
| Compute scheduling | local Docker sandbox | Slurm / Apptainer | executor adapter | P1/P2 |
| Scientific archive | Git+object store | Zotero, Zenodo, OSF | opt-in and human-approved | P2 |

## 3. Per-candidate integration audit (required output)

```text
id / name / source URL / author or maintainer
source type (repo, paper, hosted product, list, benchmark, data, skill)
version tag / pinned commit / last commit / scan date
license type + scanned LICENSE URL + allowed distribution
actual entrypoint, installation steps, Python/node/CUDA/runtime requirements
API & MCP availability; auth and network requirements
sub-capabilities and overlap with already selected tools
run sandbox needs and permission scope
actual smoke-test command, output and log artifact IDs
known failures/limitations and compatibility
measurable effect versus baseline in an appropriate task
selected action: integrate SDK / call API / wrap CLI / adopt skill / method only / defer
owner, review date, next action
```

Maintain provenance to lists/collections separately, since the same item may be listed in dozens of sources. Deduplicate by canonical project URL and alternate repository identifiers while retaining each discovery edge. Do not drop license or versions when merging.

## 4. Ranking and selection methodology

There are no universal single-number scores for scientific tools. Use evidence dimensions rather than fabricated aggregate scores:

- Fitness: Does the candidate fulfill a specific capability of the research workflow?
- Reliability: Does it pass repeatable contract/smoke tests in our environment?
- Research quality: Does it outperform baseline on same version/method of matched benchmark?
- Reproducibility: Inputs, environment, run artifacts, seeds and failure logs available?
- Cost/latency: Approximate or measured in the same environment, budgeted?
- Maturity: releases, API stability, maintainers, security fixes?
- Rights/privacy: license, data handling and sensitive research restrictions?

GitHub Stars, social votes and HF Collection appearances are discovery signals only. Avoid automatic enabling via popularity thresholds.

## 5. Comparison rules

- Only compare results in the same benchmark family/version, same allowed tools, same budget/hardware policy and evaluation metric. Record score origin and author claim vs independent rerun.
- A reported leaderboard top result without runnable source is evaluation evidence, not an integration component.
- Reject using a benchmark's public answer or traces as training/optimization data while claiming it as hidden validation.
- AI-Scientist-v2 and Google Co-Scientist are not interchangeable: one publishes a repo, the other may describe an architecture/product; each license/deployment claim must be rechecked.

## 6. Reference sources

### Institutional and community catalogs

- https://github.com/THU-KEG/Awesome-AI-for-Research
- https://github.com/tsinghua-fib-lab/Awesome-AI-Scientists
- https://github.com/chrisliu298/awesome-research-agents
- https://github.com/AI4Scientist/awesome-autoresearch
- https://github.com/Orchestra-Research/AI-Research-SKILLs
- https://huggingface.co/papers/trending
- https://huggingface.co/collections/InternScience/researchclawbench

### Official agent and testing tools

- https://allenai.org/asta/resources
- https://github.com/allenai/asta-plugins
- https://github.com/allenai/asta-bench
- https://inspect.aisi.org.uk/
- https://github.com/openai/mle-bench
- https://github.com/facebookresearch/airs-bench
- https://github.com/ScalingIntelligence/KernelBench
- https://github.com/prometheus-eval/into-the-unknown

### Code and workflow systems

- https://github.com/karpathy/autoresearch
- https://github.com/AIcrowd/aicrowd-aide
- https://github.com/microsoft/RD-Agent
- https://github.com/OpenHands/software-agent-sdk
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.temporal.io/develop/python
- https://agentskills.io/specification
- https://modelcontextprotocol.io/

For the full dataset of 100 + 43 entries see `registries/` and the two prior survey documents in `docs/`.

## 7. Integration roll-out gates

1. **Source verification**: exact URL opens; repo is not fake, renamed, archived or unrelated; record snapshot.
2. **License review**: code/data/weights/Skill files separately; don't invent implicit permissions.
3. **Security review**: no credentials to untrusted code, command execution/egress checked.
4. **Runtime test**: fresh isolated environment with pinned commit; run smallest real sample.
5. **Contract tests**: same typed inputs/outputs, errors, timeouts, cancellation, retries.
6. **Scientific evaluation**: known fixed task, baseline, raw logs and honest limits.
7. **Enable/monitor**: default off until approved; periodically reverify version, vulnerability, maintenance and feature compatibility.

## Phase 0 current status

The FastAPI, Pydantic, SQLAlchemy, Alembic, Psycopg, Uvicorn, official PostgreSQL/Python images, pytest, Ruff, mypy, test transport and WSL Compose runtime actually used are enumerated in `registries/runtime_dependency_audit.json` with source, license, risk, scope and smoke evidence. `GET /api/v1/capabilities` exposes this audited runtime set. The broad 100+43 candidate inventory remains discovery-only. LangGraph, Skills execution, MCP, OpenHands, paper APIs, MLflow and Inspect AI have not been integrated. See `PHASE_0_REPORT.md`.
