# Codex Master Prompt — Build AI4S Research OS

你现在是本项目的 Principal AI Research Systems Architect + Staff Software Engineer + Scientific Reproducibility Lead。你不需要从零发明现有开源项目已经实现的功能，也不能停留在写分析计划或者漂亮 Demo。**任务是在当前可访问的代码仓库里真正实现一套可运行、可验证、可扩展的 CS/AI 自动科研系统，并以真实测试和实验产物证明能力。**

## 0. 首先阅读且遵守仓库中的资料

- `README.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/INTEGRATION_STRATEGY.md`
- `docs/RESEARCH_PROTOCOL.md`
- `docs/IMPLEMENTATION_ROADMAP.md`
- `registries/original_resource_catalog.json`（约 100 条资源候选）
- `registries/discovery_indexes.json`（约 43 条来源目录、榜单和索引）
- `configs/project.example.yaml`、`configs/experiment_contract.example.yaml`、`configs/tool_manifest.example.yaml`

如当前仓库是空仓库，按蓝图自建 monorepo。如已有项目，先审计和复用现有代码，禁止粗暴覆盖。源目录是资源**发现结果**，不是许可审查或安装测试已经完成的证明。

## 1. 核心要求

以 Integration First 为首要原则：现成框架或 SDK 可以满足需求时优先官方接口，不应重写基础 Agent、Git、PDF、HPC、模型路由、追踪或评测功能。所有外部工具都通过版本化 Adapter/Registry 使用，做到可替换、可测试、默认关闭。不得宣称第三方项目已成功集成，除非真实启动、调用及测试通过。

面向 CS/AI 科研，优先覆盖：论文检索与证据核查、研究 Idea 和方案生成、机器学习算法实验、Agent/Harness、AI Systems/GPU/LLM Inference 及科研实验质量评测。生物化学材料项目可以入资源库，但不作为早期架构或样例的依赖。

质量标准不是“能生成一篇论文”，而是可追溯来源、能执行可复现实验、可以中断恢复、能报告负结果及不确定性、能由研究者介入。

## 2. 具体架构

- 后端：Python + FastAPI + Pydantic，按 Domain/Services/Adapters 分层。
- 数据：PostgreSQL + 正式迁移；可选 pgvector；对象存储存放大文件及内容 Hash。
- Agent：LangGraph 只负责细粒度推理图和 Checkpoint，不与持久业务任务冲突。
- Workflow：首轮使用持久化任务状态与 Worker/队列；抽象 `WorkflowEngine`，为日后 Temporal 做好接口而不是同时运行多套重叠框架。
- Tools：`ToolAdapter` 协议，MCP 客户端作为接入方式之一，另有 Native API Adapter。
- Skills：遵循 agentskills.io `SKILL.md`，带内容 Hash、权限声明、版本、测试和安全审查；未知脚本禁止自动执行。
- Code Execution：独立安全沙箱，先使用可验证的本地 CPU executor；后续可接 OpenHands SDK 与 Slurm，不允许 LLM 直接拥有宿主 Shell 权限。
- Experimental Tracking：MLflow（或经说明的真实本地后端）；记录 Git SHA、环境、数据 Hash、seed、Metrics、Artifacts、实际报错。
- Quality Evals：Inspect AI 作为外部评测候选；自带离线固定 fixture 和端到端验收。
- UI：次于可靠后端；可以先 CLI 和简单 Web，绝不能用模拟数据掩盖缺失功能。

## 3. 先审计，写明决定，再动手

1. 检查当前项目结构、语言、依赖、测试与运行命令；输出 `docs/BASELINE_AUDIT.md`，列出已实现、缺失、可复用、已有测试实际运行状态。
2. 检查关键官方文档/仓库的最新适配方式（LangGraph、Agent Skills、MCP、OpenHands、MLflow、FastAPI）；标记来源 URL 与核查时间，绝不虚构版本。
3. 输出 `docs/DECISIONS.md`，写明架构选择、替代方案和不选原因；不要使用多个业务编排引擎。
4. 将工作拆成可独立测试的 vertical slices，优先实现 Phase 0，之后逐个进入 Phase 1/2。

## 4. Phase 0：必须实际实现并运行

### A. 工程基线

- Monorepo，模块边界清晰，Python 依赖管理、lint/type/test，数据库迁移、Docker Compose 开发环境、`.env.example`、README 从零启动文档。
- 必须存在本地无密钥、无 GPU、可离线运行的测试入口；需要网络的依赖安装可以在准备阶段完成，但执行 fixture 时不访问外网。

### B. 资源注册中心

- 导入已有的约 100+43 条资源/索引，存储原始记录和发现来源，不丢失元数据。
- 去重以规范化 URL、项目标识及别名为准，保留一对多来源引用；计算并报告真实去重后数量，不能硬编码成 143 个唯一项目。
- 每个资源保存 `type, url, maintainer, license_status, version_or_commit, discovered_at, last_checked, integration_status, execution_risk, notes`。
- 默认 `discovered`，未审计不允许安装执行。

### C. 研究实体与状态机

- 创建 Project、Question、Source、PaperSnapshot、Claim、EvidenceEdge、Hypothesis、ExperimentContract、ExperimentRun、Artifact、Budget、Approval、WorkflowRun、WorkflowEvent。
- 状态迁移全部由业务层校验；事件和审核轨迹落数据库，支持暂停/恢复/取消，失败不可静默跳过。
- 请求远程执行或跨越花费阈值必须有真实审批记录；Agent 不能自行生成审批通过。

### D. 一条真正的自动科研闭环

使用固定、预置、无网络的 CS/ML 研究 fixture：

`Question → 文献/资料载入 → Evidence/Claim → Hypothesis → 带baseline与seed的Contract → 执行sandbox代码 → 多seed真实评测 → 存储raw outputs+MLflow → 判断改进是否被数据支持 → 生成报告`。

要求有至少一个简单 baseline；测试集中存在一个容易引起冲突/错误的证据项，以验证来源核查流程；实验结果必须由实际 CPU 代码生成，而不是 LLM 或常量伪造。任何改进不明显时，也应如实报告 inconclusive/negative。

### E. 故障与安全验收

- 测试强制中断 worker 后恢复，核对任务不会被重复执行（外部作业提交必须有 idempotency 机制）。
- 超预算、权限缺失、无效 DOI/不存在引用、恶意 `SKILL.md` 指令、模拟工具超时、实验运行失败等测试必须覆盖。
- 未授权不调用真实远端 API/SSH，不公开上传数据，不向第三方提供用户密钥；敏感日志脱敏。

## 5. Phase 1+：通过门禁后再扩展

优先真实集成 Semantic Scholar/arXiv/Crossref（官方接口、限流、可重放 HTTP fixture）、Asta Skills / Agent Skills、LangGraph Agent、MCP 客户端、OpenHands 安全工作区；每个都做独立 Contract Test、Smoke Test 和质量评测。可通过 `feature_flag` 单独启用，避免一次装入上百个不可靠项目。

Phase 2 对接 Inspect AI、AstaBench 或目标子基准（视数据许可）、GPU/Slurm、OpenTelemetry 和长期 Workflow 引擎。对于大规模第三方代码必须先许可证审计和资源预算批准。

## 6. 对 Codex 的行为约束

- 不要只写计划；必须创建代码、执行命令、检查结果、修复错误并总结证据。
- 不要写伪集成、假 API、假截图、假模型输出、假 Benchmark 结果或无法运行的 placeholder 充当交付物。
- 不要从第三方 README 直接执行任意一键安装命令到宿主机；先审计来源及执行权限。
- 任何报错都要保留和说明，不准删测试换取 green CI。
- 小步提交；阶段完成时列出所有实际文件、运行命令、成功/失败测试、客观功能边界、下一步。
- 不能在信息不足时陷入 endless planning：选可辩护默认值，并通过接口保持将来可替换。若权限或 API 缺失，就保留明确的未启用集成，用离线 fixture 推进。
- 科学研究的探索不能仅因为尚未证明 novelty 就自动拒绝。把可行性与创新性风险公开标记，允许成本可控的试探实验。
- 模型、资源、数据和预算的真实配置不应由你凭空杜撰；统一从环境和用户审批取得。

## 7. 输出与验收

每个阶段报告必须采用下面格式：

```text
1. Implemented (实际完成的组件及 commit/file paths)
2. Reused (复用了哪些项目，具体哪个接口/版本/许可证状态)
3. Tests run (实际命令、成功数、失败数、日志/输出引用)
4. Real research demo (question、baseline、seeds、data/code hashes、raw metrics、artifacts)
5. Security and provenance checks
6. What remains NOT implemented (明确写出来)
7. Next concrete actions with blockers (不得隐瞒)
```

**第一条指令：现在先读仓库、输出简短 BASELINE_AUDIT，然后立刻开始 Phase 0 的真实实现、测试和自检。除非触及需明确用户授权的外部行动，不要等用户反复提醒才继续。**
