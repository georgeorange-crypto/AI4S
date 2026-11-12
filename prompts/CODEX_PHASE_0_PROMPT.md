# Codex Phase 0 Prompt — Minimal Real Research Loop

优先阅读 `AGENTS.md` 与 `prompts/CODEX_MASTER_PROMPT.md`。

本次只做 Phase 0：一个真正可运行的 `AI4S Research OS` 内核，而不是展示 Dashboard 的空壳。用 Postgres 存状态（测试可使用 SQLite 作为显式测试适配器，但正式环境需 Postgres），FastAPI 暴露状态与审批、持久任务执行器、资源导入、离线论文 fixture、基本证据图、冻结合约、多 seed CPU 实验和 MLflow/工件记录。

实现最少 5 组测试：
1. 资源去重且保留所有发现来源（100+43 原始记录不能消失）；
2. 证据来源不存在时不允许声称 `verified`；
3. 未冻结/未授权/超预算实验禁止提交；
4. worker 重启后继续/恢复，外部实验不重复；
5. 离线端到端科研任务产生真实指标、日志、源码/数据 checksum 与报告。

优先 Command Line Interface + REST API，UI 做到能显示真实数据即可；所有生成结果必须有可查询的持久 ID 与实际产物。维护源码版本、迁移、配置文档、错误记录。禁止提前宣布完成。完成 Phase 0 后给出清晰验收摘要。
