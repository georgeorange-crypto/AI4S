# AI4S Research OS — Scientific Protocol, Safety Gates and Example Flows

## 1. Principle: Research is more than an autonomous loop

The system should produce *scientific progress with attributable evidence*, not automatically declare successful papers. It must preserve genuine exploration. A plausible but unproven idea may receive a small bounded exploratory experiment without already proving top-conference novelty. If evidence is weak, label exploratory rather than burying it.

## 2. Four research quality gates

**Gate A — Literature**: source existence (DOI/arXiv/URL), date/version, critical claims grounded in passage, conflicts highlighted, missing relevant work acknowledged. Draft idea may proceed with gaps openly marked; no hallucinated citations.

**Gate B — Pre-experiment contract**: research question, hypothesis, problem definition, data provenance, target metric and polarity, baselines (including simplest/identity where relevant), train-dev-test boundaries, seeds, target hardware, statistical comparison, resource/time ceilings, stopping rule and failure criteria frozen before formal experiments. Exploratory tests may be separately labeled and run within small budgets.

**Gate C — Execution**: code revision + environment lock + dataset version, checksums, logs, raw outputs, tests, hardware/driver specifics where appropriate. Any timeout/OOM/invalid scores remain recorded, not erased.

**Gate D — Validation and interpretation**: paired comparisons where relevant, confidence intervals, replicate variation, independent reviewer/validator role, post-hoc selection and cherry-picking warnings; conclusions bounded by actual evidence. No automatic conference submission.

## 3. Experiment Contract schema (conceptual)

```yaml
id: exp-001
project_id: demo-ml-algorithms
hypothesis_id: hypothesis-001
intent: exploratory     # exploratory | confirmatory
question: "Does candidate improve held-out accuracy vs frozen baseline?"
data:
  id: offline-synthetic-fixture-v1
  sha256: "<filled by executor>"
  split_policy: train-dev-frozen-test
baselines:
  - id: baseline-1
    implementation_ref: refs/baseline.py
candidate:
  source_ref: refs/candidate.py
metrics:
  - name: accuracy
    direction: maximize
  - name: runtime_seconds
    direction: minimize
seeds: [11, 23, 37]
resources:
  executor: local-sandbox
  cpu_cores: 2
  memory_gb: 4
  walltime_minutes: 10
  estimated_spend_cap_usd: 0
stop_conditions:
  - budget_exhausted
  - invariant_violation
  - explicit_cancel
approvals:
  external_data_transfer: false
  remote_gpu_execution: false
  public_post: false
```

Treat `intent: exploratory` distinctly; claim-making only after confirmatory validation. Frozen contract hashes must be signed/stored before execution; any changed metric/test population requires new contract revision.

## 4. Bounded self-improvement loop

```text
1. Read approved Experiment Contract, prior best result and remaining budget.
2. Choose ONE controlled modification and describe testable mechanism.
3. Implement in isolated worktree, execute static tests and local smoke test.
4. Run baseline and candidate under matched conditions.
5. Save run artifacts and compare raw metrics, with uncertainty.
6. If valid improvement: retain new branch, not overwrite frozen baseline.
7. If invalid, lower, inconclusive, or crash: record negative result and reason.
8. Choose next bounded hypothesis only if budget remains; otherwise stop/report.
```

Practical inspiration: Karpathy autoresearch https://github.com/karpathy/autoresearch; do not claim its setup generalizes to all domains.

## 5. Specialized AI Systems task example

**Goal:** Benchmark a compression/restore optimization for KV cache or inference subsystem.

- Inputs: repo commit; runtime stack including model, model dtype, GPUs and device allocation; workload traces and context distribution; code and optional codec implementation.
- Baselines: uncompressed, no-cache and standard codec as appropriate.
- Validity: output fidelity/correctness, compression-loss effects on downstream generation quality, no cross-run warmup contamination.
- Metrics: TTFT P50/P95, throughput, bytes transferred, decode host/GPU time, hit/miss rates, GPU memory and runtime errors. Record precise metric definitions, sampling policy and workload version.
- Controls: same workload and machine, warmup, concurrency, seeds; monitor GPU contention, cache state, timeouts and memory fragmentation.
- Result: summary table directly generated from stored raw run records; disputed inference marked for investigation.
- Remote HPC access only via approved Slurm executor; no direct unbounded SSH agent.

## 6. Research Radar program

A `RadarSpec` includes topics (e.g. GPU systems, LLM context compression, Agent benchmark, world model, RL), discovery sources, exclusion tags, desired summary cadence, maximum requests/day and duplicate horizon. Each poll creates an auditable ingestion event; date of each finding and freshness matter. AI only suggests new tasks until project policy approves autonomous experiments.

## 7. Benchmark evaluation protocol

- Task ID/version, dataset hash, permitted external tools, model API revision, system prompt, agent framework revision, budgets, evaluator code revision, run seed and machine resources are part of an EvalConfiguration.
- Evaluate paper QA (evidence retrieval) separately from research code generation, autonomous experiments, and end-to-end real discovery.
- Keep public dev data separate from final holdout; detect accidental leakage and contamination.
- External LLM-judge scores are diagnostics; use deterministic metrics and human auditing where appropriate.
- Evaluate both **quality** and **engineering**: accuracy, reproducibility, completion rate, invalid tool calls, duplicate compute submissions, recoverability, cost, permission violations, time to useful evidence.

## 8. Failure protocol

Any failure creates `FailureRecord`: step, time, error class, related artifact and trace, retryability, suspected cause, and suggested next step. System must stop after max retries/timeout/budget. Invalid tests or zero evidence cannot become positive results.

Do not turn every uncertain paper/idea into NO-GO prematurely: classify `promising-exploratory`, `needs-data`, `needs-baseline`, `blocked`, `validated-negative`, `ready-for-confirmatory`; define the cheapest decisive experiment before discarding.

## 9. Human decision gates (not human micromanagement)

Requires consent: installing untrusted code or scripts, allowing new network egress, accessing private papers/accounts, exceeding compute or spend caps, deleting data, pushing to external repos, sending emails, publishing results, and final claims of readiness to submit. Routine approved read/search/cost-bounded local CPU work can be automated.

Approval records are explicit, scoped and time-limited; no approval by mere system prompt or model claim.

## 10. Offline scientific quality acceptance

Use a fixed toy ML problem with known ground truth and controlled split and seeds. The system must:

- import 3 fixture citations, annotate at least one conflicting piece of evidence, and not invent DOI;
- propose one hypothesis and explicit simple baseline;
- build and freeze a valid experiment contract;
- request approval for execution when needed;
- execute a **real CPU process** (not a fake metric) inside a controlled workspace;
- log at least 3 seeds and raw metrics to disk / MLflow;
- recover from a simulated interruption without duplicate logical experiment;
- produce a report with reproducible command, code/data hashes, all metrics, negative results if any, and unverified claims flagged;
- cancel on exhausted budget and prohibit unauthorized network/host commands.

Any unmet check fails the phase rather than being hidden by a polished UI.

## Phase 0 acceptance status (2026-11-12)

Implemented and exercised: offline fixed-fixture research with an explicit local approval, baseline/candidate comparison across three seeds, disputed evidence handling, persisted metrics/events, SHA-256 data/config/code/artifacts, pause/resume/cancel, hard worker-process exit and idempotent recovery, over-budget and permission-denial checks, resource/capability registry, API contracts, and SQLite/PostgreSQL migrations. The sample report and raw content-addressed output are committed under `examples/offline_research/results/`.

The CPU runner executes repository-owned code only. It is not a sandbox for untrusted code. PostgreSQL API and SQLite offline runner are separately persistent profiles, not yet one worker system. Refer to `PHASE_0_REPORT.md` for exact final outputs and unimplemented scope.
