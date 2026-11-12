# Phase 1 acceptance ledger

- **Phase 1.1: Crossref + Agent Skill + model-free MCP/LangGraph workflow** — implementation and bounded real smoke done; see [`PHASE_1_REPORT.md`](PHASE_1_REPORT.md) and [`evidence_manifest.json`](../examples/literature/phase1-smoke/evidence_manifest.json).
- **Phase 1.2: MLflow local tracking + arXiv client adapter** — MLflow SQLite logging and arXiv offline response/approval contracts implemented and tested. arXiv live smoke remains not run; it is not counted as a live provider integration yet. See [`PHASE_1_REPORT.md`](PHASE_1_REPORT.md).
- **Phase 1 overall** — open. Literature-driven hypothesis/idea selection and approved experiment handoff to the CPU runner are not implemented. Crossref and arXiv are read-only, explicitly approved tools; model providers remain disabled.
- User preference: keep model integrations disabled while tools and graph workflows are accepted.
