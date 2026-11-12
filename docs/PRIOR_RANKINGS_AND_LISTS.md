# AI4S / AutoResearch · 排行榜与资源目录专项调研

> 核查日期：2026-11-12。重点：计算机科学、AI/ML 研究、科研 Agent、实验自动化、AI Systems。
> 说明：官方榜单、GitHub Stars、社区精选目录具有不同的证据等级；榜单排名受模型、Harness、工具、预算和评测版本影响。

记录数：**43**（包括项目目录、榜单、官方说明和数据集）。

## 优先研究的五条资源链

1. **CS论文研究/文献证据**：THU-KEG 目录 → AstaBench ScholarQA-CS2 → Asta Skills / OpenScholar。
2. **机器学习自动实验**：AI4Scientist awesome-autoresearch → MLE-bench → Meta AIRS-Bench → autoresearch / RD-Agent / AIDE。
3. **AI Systems/GPU研究**：KernelBench → RE-Bench 中 Kernel/LLM优化任务 → 可重放的实验Harness。
4. **开放科学问题**：Into the Unknown → AI Scientist / ResearchStudio / Agent Laboratory → 论文证据审计。
5. **Harness/Skill生态**：Awesome Research Agents → AI-Research-SKILLs → 选用LangGraph、OpenHands、Codex等。

## 原始来源列表

### GitHub 机构、研究者、社区整理的索引

|优先级|名称|类别|作用与备注|
|---|---|---|---|
| P0 | [THU-KEG / Awesome AI for Research](https://github.com/THU-KEG/Awesome-AI-for-Research) | github_list | AI科研全生命周期；Benchmark专项 |
| P0 | [Tsinghua FIB Lab / Awesome AI Scientists](https://github.com/tsinghua-fib-lab/Awesome-AI-Scientists) | github_list | 基于综述的Deep Research、Idea、Experiment、Review分类 |
| P0 | [Awesome Research Agents](https://github.com/chrisliu298/awesome-research-agents) | github_list | 专注Codex/Claude Code科研Harness/Skills/实验 |
| P0 | [Awesome AutoResearch](https://github.com/AI4Scientist/awesome-autoresearch) | github_list | 自动科研框架与模块索引 |
| P1 | [Awesome Automated AI](https://github.com/jbogocz/awesome-automated-ai) | github_list | 自动化ML项目排名和Stars/近期活跃度快照 |
| P1 | [Awesome Autonomous Research Agent](https://github.com/LTzycLT/Awesome-Autonomous-Research-Agent) | github_list | 核心AutoResearch系统，发布时间与Star快照 |
| P1 | [Awesome Auto Research Landscape](https://github.com/yuanzhang7/awesome-auto-research-landscape) | github_list | 中英双语自动科研版图 |
| P1 | [Awesome AI Scientist Papers](https://github.com/openags/Awesome-AI-Scientist-Papers) | github_list | 论文、调研和科学自动化方法 |
| P0 | [Awesome Scientific LLM Benchmarks](https://github.com/subinium/Awesome-Scientific-LLM-Benchmarks) | github_list | Agentic Science与科学能力评测清单 |
| P0 | [Awesome Agentic Benchmarks](https://github.com/gray311/awesome-agentic-benchmarks) | github_list | 区别官方成绩、论文自报、厂商自报结果 |
| P1 | [Awesome AI for Science](https://github.com/ai4s-research/awesome-ai-for-science) | github_list | 跨科学领域，选择自动研究/算法优化板块 |
| P1 | [Awesome AI for Research](https://github.com/ShinyDataTech/awesome-ai-for-research) | github_list | Skills/文献/图表/投稿/引用 |
| P1 | [Awesome AI Scientist / Omni Scientist](https://github.com/Omni-Scientist/Awesome-AI-Scientist) | github_list | AI Scientist论文、工具与评测 |
| P0 | [AI Research Skills / Orchestra Research](https://github.com/Orchestra-Research/AI-Research-SKILLs) | github_list | AI/ML研究Skills合集；需安全审计 |
| P1 | [FAROS / OpenNSWM Lab](https://github.com/OpenNSWM-Lab/FAROS) | github_list | 科研蓝图驱动的Agent科研工作流 |
| P0 | [GitHub Topic: ai-scientist](https://github.com/topics/ai-scientist?o=desc&s=stars) | github_topic | 按Stars检索自称AI Scientist的仓库 |
| P1 | [GitHub Topic: ai4science](https://github.com/topics/ai4science) | github_topic | AI4S跨学科项目，有较多非CS内容 |
| P0 | [GitHub Topic: auto-research](https://github.com/topics/auto-research) | github_topic | 自动科研主题最新仓库 |
| P0 | [GitHub Topic: research-agent](https://github.com/topics/research-agent) | github_topic | 研究Agent和Deep Research工具 |

### Hugging Face Collections 与发现入口

|优先级|名称|类别|作用与备注|
|---|---|---|---|
| P0 | [InternScience / SGI-Bench](https://huggingface.co/collections/InternScience/sgi-bench) | huggingface_collection | 研究能力榜单、数据、论文、评测工具 |
| P0 | [InternScience / ResearchClawBench](https://huggingface.co/collections/InternScience/researchclawbench) | huggingface_collection | 40任务Benchmark、ResearchHarness及提交工具 |
| P1 | [InternScience / InternAgent](https://huggingface.co/collections/InternScience/internagent) | huggingface_collection | InternAgent相关模型/数据/论文 |
| P1 | [inkoziev / AutoResearch](https://huggingface.co/collections/inkoziev/autoresearch) | huggingface_collection | Harness优化、Idea证据与长期AutoResearch论文 |
| P1 | [ShiyuHuang / auto-research](https://huggingface.co/collections/ShiyuHuang/auto-research) | huggingface_collection | SIA、EurekAgent、ResearchStudio研究 |
| P1 | [zhaviraax / Agentic AI for science](https://huggingface.co/collections/zhaviraax/agentic-ai-for-science) | huggingface_collection | AI Scientist/Agent Laboratory/ScienceAgentBench论文 |
| P2 | [alexngai / Automated Research](https://huggingface.co/collections/alexngai/automated-research) | huggingface_collection | 早期代表论文的小型合集 |
| P2 | [JBHF / AI FOR RESEARCH](https://huggingface.co/collections/JBHF/ai-for-research) | huggingface_collection | 综合AutoResearch模型论文Space |
| P0 | [Hugging Face Trending Papers](https://huggingface.co/papers/trending) | discovery_feed | 日报/周报/月榜，按社区关注 |

### 原始排行榜 / Benchmark / 官方说明

|优先级|名称|类别|作用与备注|
|---|---|---|---|
| P0 | [AstaBench](https://huggingface.co/spaces/allenai/asta-bench-leaderboard) | leaderboard | Ai2；ScholarQA-CS2、Coding、E2E多子榜 |
| P0 | [MLE-bench](https://github.com/openai/mle-bench) | leaderboard | OpenAI；75个Kaggle任务；目前暂停新提交 |
| P0 | [AIRS-Bench](https://github.com/facebookresearch/airs-bench) | leaderboard | Meta；20个论文衍生ML研究任务 |
| P0 | [Into the Unknown](https://prometheus-eval.github.io/into-the-unknown/) | leaderboard | 15个开放研究问题；公开轨迹与论文 |
| P1 | [ResearchClawBench](https://internscience.github.io/ResearchClawBench-Home/) | leaderboard | 40任务，跨学科端到端研究 |
| P1 | [SGI-Bench](https://internscience.github.io/SGI-Page/) | leaderboard | 实验/文献/idea等科研活动多维评测 |
| P1 | [AutoResearchExam](https://benchmarks.bespokelabs.ai/autoresearchexam/) | leaderboard | 自动ML优化与hidden-test泛化 |
| P0 | [PaperBench](https://github.com/openai/frontier-evals/tree/main/project/paperbench) | benchmark_repo | OpenAI；论文从头复现 |
| P0 | [KernelBench](https://github.com/ScalingIntelligence/KernelBench) | benchmark_repo | GPU Kernel正确性与效率 |
| P1 | [RE-Bench (archived)](https://github.com/METR/RE-Bench) | benchmark_repo | ML研究工程环境，2026年10月已归档 |
| P0 | [Hugging Face Leaderboards docs](https://huggingface.co/docs/leaderboards/index) | official_guide | 解释社区榜/官方Eval Results等差异 |
| P0 | [Meta AIRS-Bench task dataset](https://huggingface.co/datasets/facebook/airs-bench) | official_dataset | 20任务元数据；CC BY-NC 4.0 |
| P1 | [InternScience ResearchClawBench dataset](https://huggingface.co/datasets/InternScience/ResearchClawBench) | official_dataset | 可下载任务和harness说明 |
| P0 | [Ai2 AstaBench guide](https://allenai.org/asta/bench) | official_guide | 各子Benchmark的任务定义 |
| P0 | [Into the Unknown code & trajectories](https://github.com/prometheus-eval/into-the-unknown) | benchmark_repo | 包含实验对象、评测脚本、轨迹链接 |

## 如何判断一个榜单是否可信

1. 同一 Benchmark 只能比较同一任务版本、同一评分规则下的结果。
2. 要同时记录模型版本、Harness/Agent版本、工具权限、训练数据泄漏风险、资源预算、运行时长、seed数与置信区间。
3. 官方榜单优先于项目 README 自报成绩；其中未公开源码或日志的成绩要标记 `not-reproducible-yet`。
4. GitHub Stars 和 Hugging Face Upvotes 只能衡量社区关注度，不是科研能力；作者声称的 #1 不等于独立核验。
5. 记录 `last_checked`、`last_commit`、`license`、`maintenance_status`、`code_available` 和 `benchmark_method`。
6. 避免在有泄漏风险的公开 Benchmark 上重复训练后再次当作独立测试；要使用独立隐藏测试集或严谨 holdout。

## 供 Codex 使用的资源注册表字段

`id`, `source_type`, `source_url`, `project_url`, `paper_url`, `origin`, `first_seen`, `last_checked`, `release_or_commit`, `domains`, `capability_tags`, `license`, `dependencies`, `api_credentials`, `hardware`, `execution_risk`, `evaluation_protocol`, `reproducibility`, `priority`, `integration_status`, `confidence`, `notes`

建议把仓库中的 `resource catalog`、`benchmark registry`、`skill registry`、`tool registry` 分开存储；不同领域资源可入库，但只在合适工作流中启用。

## 特别注意

- OpenAI 的 MLE-bench 官方榜单于 2026-04-24 宣布暂停接收新提交；不能把任何项目主页的历史“第一”直接当成最新官方结果。
- METR 的 RE-Bench 仓库于 2026-10-20 归档，作为历史评测样例可用，但不是当前维护中的榜单。
- Meta AIRS-Bench 的 HF 任务数据标注 `CC BY-NC 4.0`，必须审查许可证和使用范围。
- 大多数 Hugging Face Collections 属个人整理，不代表 Hugging Face 对所选项目的质量背书。
