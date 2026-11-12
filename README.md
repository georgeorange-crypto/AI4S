# AI4S Research OS — Architecture & Codex Development Blueprint

**状态：Phase 0 离线内核已实现；Phase 1.1 文献工具/图工作流已实测；完整 Phase 1 尚未验收**
**日期：2026-11-12**
**方向：Computer Science / Artificial Intelligence / Machine Learning / AI Systems / Agents / GPU Systems**

## 使命

用成熟的研究工具、Agent Harness、Skills、MCP、实验运行时与研究方法组织出可审计、可恢复、可复现的 AI 自动科研系统；不是从零重写整个 AI Agent 生态，不以论文生成量代替科研质量。

## 从这里开始

### 当前可运行的离线研究闭环

离线研究核心需要 Python 3.10+；安装依赖后，fixture 执行不需要密钥、网络或 GPU。API/迁移开发环境要求 Python 3.12+。从 Windows 仓库目录初始化：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check ai4s tests migrations scripts
.\.venv\Scripts\mypy.exe ai4s
.\.venv\Scripts\python.exe -m ai4s.cli import-registry --db .ai4s/research.sqlite
.\.venv\Scripts\python.exe -m ai4s.cli approve-local --db .ai4s/research.sqlite --actor <your-name>
.\.venv\Scripts\python.exe -m ai4s.cli run-offline --db .ai4s/research.sqlite --out examples/offline_research/results --approval-id <approval-id-from-previous-command>
```

CLI 会运行固定 CSV fixture 上的多数类 baseline 与 x1 阈值候选算法，执行 seeds 11/23/37，保存 SQLite 事件/指标和按 SHA-256 寻址的 JSON 工件。演示数据是合成数据，不是外部论文或 benchmark。详情见 [BASELINE_AUDIT](docs/BASELINE_AUDIT.md)、[DECISIONS](docs/DECISIONS.md) 与 `docs/PHASE_0_REPORT.md`。

可使用 `run-offline --pause-after-seed 11` 暂停，再使用 `resume --approval-id <approval-id>` 恢复；`--run-key` 可指定 workflow 的幂等键。必须先由显式 `approve-local` 命令写入本地 approval 记录；失败记录和被争议证据会保留。此批准仅表示本地用户允许该零花费 fixture 实验，不构成远程/发布权限。

资源导入保留 100 项资源记录、43 项发现索引记录和原始字段；按规范 URL 计算实际去重。第三方资源仍为 `discovered`，未知许可证和未审查执行风险默认禁止启用。

### Phase 1.1：模型关闭的文献工具与图工作流

此 slice 使用官方 MCP Python SDK、LangGraph SQLite checkpointer、Crossref REST API 和仓库内 Agent Skill；**不调用任何模型**。离线测试使用 fake HTTP transport，不联网。真实 Crossref smoke 的批准、报告和原始响应 SHA-256 见 `docs/PHASE_1_REPORT.md` 与 `examples/literature/phase1-smoke/evidence_manifest.json`。执行入口示例：

```powershell
.\.venv\Scripts\python.exe -m ai4s.cli approve-doi --db .ai4s/research.sqlite --doi 10.18653/v1/N19-1423 --actor <your-name>
.\.venv\Scripts\python.exe -m ai4s.cli approve-skill --db .ai4s/research.sqlite --actor <your-name>
.\.venv\Scripts\python.exe -m ai4s.cli run-literature-agent --db .ai4s/research.sqlite --out .ai4s/literature --checkpoints .ai4s/agent-checkpoints.sqlite --doi 10.18653/v1/N19-1423 --run-key bert-doi-lookup --crossref-approval-id <approval-id> --skill-approval-id <approval-id>
```

搜索模式使用 `approve-crossref --query ... --max-results 3`，批准范围绑定规范化查询哈希与结果数。注意：检索仅是发现，标题/DOI 元数据相符不能证明论文结论；当前 slice 不选 Idea、不生成假设、不执行代码。详见 [`docs/PHASE_1_REPORT.md`](docs/PHASE_1_REPORT.md)。

### WSL Docker 环境（API + PostgreSQL）

项目使用现有 WSL Docker 引擎，不安装或配置 Docker Desktop。先复制 `.env.example` 为 `.env`，换成仅本地使用的随机 PostgreSQL 密码；确认 `AI4S_POSTGRES_PORT`、`AI4S_API_PORT` 未与已有服务冲突。Compose 将数据库/API 端口绑定到 loopback，数据库使用 Docker named volume。

```powershell
Copy-Item .env.example .env
# 编辑 .env 中的密码和可选端口
wsl -d Ubuntu-24.04 -- sh -lc 'cd /mnt/d/OPPitems/HOMEWORK/Liberty/AI4S && docker-compose up -d --build'
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

API 容器启动时运行 Alembic migration。API 文档位于 `http://127.0.0.1:8000/docs`。停止服务使用 `docker-compose down`，它会保留数据库卷；仅在明确要删除本地数据库时使用 `docker-compose down -v`。若当前 WSL Docker daemon 未运行，请按该 WSL 环境的既有启动流程处理；仓库不修改发行版服务或 Docker daemon 设置。

1. 阅读 `docs/ARCHITECTURE.md`（系统架构与组件协议）。
2. 阅读 `docs/RESEARCH_PROTOCOL.md`（科研约束、工作流、验收与控制）。
3. 阅读 `docs/INTEGRATION_STRATEGY.md`（复用现有项目、评测、集成决策）。
4. 阅读 `docs/IMPLEMENTATION_ROADMAP.md`（分期可交付目标和验收）。
5. 对编码 Agent 提交 `prompts/CODEX_MASTER_PROMPT.md`，并让其严格遵循 `AGENTS.md`。
6. `registries/` 包含前两轮研究的 100 条资源记录和 43 条来源索引，不能将其当作已完成的源码、许可证或实际运行审计。

## MVP 目标

**目标研究闭环（Phase 0 使用固定离线 evidence fixture，尚不接论文 API）：**

`Research Question → Search/Import Papers → Evidence → Hypothesis → Approved Experiment Contract → CPU Sandbox Run → MLflow Artifact → Result Validation → Research Report → Resume`。

外部 API 和 GPU/HPC 是按需连接的进阶能力；没有密钥不应阻止本地离线验收。不得以 UI 截图、假数据或生成的报告伪装任务已经运行成功。

## 目标结构（蓝图；当前实现边界见 `docs/PHASE_0_REPORT.md`）

```text
apps/web/               Research UI, approval and run dashboards
services/api/           FastAPI HTTP/WebSocket APIs
services/worker/        durable tasks and schedulers
packages/domain/        core entities, validators, events and policies
packages/research/      workflows and specialized research skills
packages/agents/        LangGraph agent processes, memory and model policy
packages/integrations/  paper APIs, MCP, skill/tool registries, vendors
packages/execution/     sandbox, OpenHands integration, HPC executor
packages/evaluation/    Inspect tasks, gates and comparisons
packages/observability/ traces and budgets
skills/                 Agent Skills compliant SKILL.md bundles
registries/             resource, tool, skill, model, benchmark registries
configs/                examples and schemas
infra/                  docker compose, db migrations, minio, local dev
examples/               offline e2e research task and expected results
tests/                  unit, contracts, integration, e2e, security
```

## 不可变原则

- Sources are evidence; model generations are hypotheses, not facts.
- Experiments are controlled, reproducible, budgeted, and provenance-rich.
- Research autonomy is bounded by permissions and explicit human gates.
- Every tool/skill must have a versioned manifest and evaluation evidence.
- Build adapters around existing ecosystems; never fork a third-party project merely for superficial integration.

## 重要参考（已查阅官方文档）

- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- Temporal workflows: https://docs.temporal.io/develop/python
- OpenHands SDK: https://github.com/OpenHands/software-agent-sdk
- Agent Skills: https://agentskills.io/specification
- MCP security: https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices
- Ai2 Asta resources: https://allenai.org/asta/resources
- Inspect AI: https://inspect.aisi.org.uk/
- MLflow Tracking: https://mlflow.org/docs/latest/tracking/

**版权与许可：** 本蓝图并不授予对第三方代码、全文论文、数据集的再分发权；真实集成前必须核验各项目许可证、服务条款与 API 配额。
