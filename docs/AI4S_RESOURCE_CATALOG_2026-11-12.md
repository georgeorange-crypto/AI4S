# AI4S / AI Auto Research · 资源目录（首轮调研）

> 版本日期：2026-11-12。研究入口目录，不表示所有项目已经完整试运行或完成许可证审计。
> 目标：先收集原始来源，按工具、方法、规范分类；第二阶段做源码级审计、功能验收、适配器实现。

共收录 **100** 项资源；按优先级分为 P0（先验证）、P1（候选）、P2（观察）。

## 集成判断与协议

- **代码**：仓库或SDK，可在许可和安全核查后接入。
- **API/MCP**：优先通过标准适配器使用，不复制服务端。
- **方法/论文**：学习思想，不等于可下载代码。
- **规范**：用于工作流守则和目标Venue校验，不当作可运行工具。
- **P0 并不表示已实测或全部开源**，只是建议优先调研。

## 推荐的第一条研究闭环

`Paper Sources → Metadata Normalization → Verified Evidence → Gap/Idea → Experiment Contract → Sandbox Code → Compute Scheduler → Run/Artifacts → Statistical Check → Research Memory → Human Decision`

## 必须强制执行的设计约束

1. 引文必须核对 DOI/arXiv ID、原文与论断证据位置；不能把Agent引用当作事实。
2. 区分公开论文、预印本、演讲、论坛传闻以及智能体自己的推断。
3. 研究方案执行前先冻结评价协议与基线；记录每次运行的代码版本、依赖、数据版本、seed、设备、预算、输出与失败。
4. LLM写的代码只可在隔离环境运行；最小权限，密钥分级，出站访问和外部发布需要授权。
5. 实验结论由可复验脚本和原始数据支持；拒绝根据单次LLM判词直接确认创新。
6. 自动科研应有明确停机与资源预算，不采用无限循环无成本上限。
7. 合规规则按目标期刊/会议/学校/资助方逐项校验，不能直接把其他机构的政策视作自己的规则。
8. 自动决策须保留行动和研究日志，以便人类随时接管、复盘并纠正过度保守或过度乐观。

## 资源清单

### 01 端到端科研（17）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P1 | [The AI Scientist v1](https://github.com/SakanaAI/AI-Scientist) · Sakana AI | 完整科研流水线模板 | 架构借鉴 | 特殊 Source Code License；AI 使用披露；运行模型生成的代码需隔离 |
| P0 | [The AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) · Sakana AI | 探索性研究、树搜索、实验管理 | 架构借鉴 / 许可审查后试验 | 特殊 Source Code License；沙箱；论文质量不可默认保证 |
| P0 | [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) · Samuel Schmidgall | 文献、实验、写作、人类反馈 | 源码试运行 | 检查仓库当前许可证与模型依赖 |
| P0 | [autoresearch](https://github.com/karpathy/autoresearch) · Andrej Karpathy | 指标驱动实验循环与自动代码迭代 | 原样跑通后改造 | 单GPU/单指标/固定时间的适用边界 |
| P0 | [AIDE ML](https://github.com/AIcrowd/aicrowd-aide) · AIcrowd | 代码搜索、实验评测、ML工程优化 | 实验优化适配器 | 要防止评价指标过拟合 |
| P1 | [Robin](https://github.com/Future-House/robin) · FutureHouse | 科研多智能体工作流 | 参考 / 局部适配 | 分析部分依赖 Edison API 和费用 |
| P0 | [Google AI Co-Scientist](https://docs.cloud.google.com/gemini/enterprise/docs/co-scientist-and-alphaevolve) · Google | Idea生成、反思、排序、演化、综述 | 架构设计参考 | 非全部开源；避免宣称可复现其内部实现 |
| P0 | [AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) · Google DeepMind | 代码进化搜索+自动评价 | 方法借鉴 | 公开的是介绍，非可直接复制内部产品 |
| P1 | [ResearchAgent](https://aclanthology.org/2025.naacl-long.342/) · Microsoft Research / academia | 论文图谱+Idea生成+Reviewer反馈 | 论文方法借鉴 | 须单独找代码许可和数据入口 |
| P2 | [AgentRxiv](https://arxiv.org/abs/2503.18102) · Schmidgall / collaborators | Agent间科研成果共享与复用 | 研究组织机制参考 | 不能把智能体生成内容当可靠科研结论 |
| P1 | [GPT Researcher](https://github.com/assafelovic/gpt-researcher) · Open-source community | 并行深度搜索与引用报告 | 直接试运行 | Web资料质量与引文复核 |
| P1 | [Open Deep Research](https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research) · Hugging Face | 开源深度研究工具链样例 | 直接试运行 | 复现实验条件与检索服务可变 |
| P0 | [STORM / Co-STORM](https://github.com/stanford-oval/storm) · Stanford OVAL | 多视角提问与文献综述 | 复用文献综合模块 | 不应默认生成稿达到可发表水平 |
| P1 | [Awesome Research Agents](https://github.com/chrisliu298/awesome-research-agents) · Community / Chris Liu | 自动科研系统与论文索引 | 二级资源索引 | 聚合索引需要逐项核验 |
| P0 | [AI for Auto-Research: A Survey](https://worldbench.github.io/assets_common/papers/survey-ai-auto-research.pdf) · Research community | 自动科研现有机制与评测综述 | 文献地图 | 综述观点须回查一手论文 |
| P0 | [Stanford Biomni](https://github.com/snap-stanford/Biomni) · Stanford SNAP | 科学领域工具环境+生物医学AI Agent | 领域插件生态参考 | 默认LLM代码可有完整系统权限，必须沙箱；集成数据库单独审许可 |
| P1 | [ARIS Adversarial Multi-Agent Research](https://arxiv.org/abs/2605.03042) · Research community | 对抗多Agent研究、主张审计与修订 | 论文机制参考 | 论文方法不代表已完成可运行源码核验 |

### 02 文献检索与知识库（14）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P0 | [Asta Tools / Plugins](https://github.com/allenai/asta-plugins) · Ai2 | 科研检索/文献库/数据分析Skills | 优先集成Skills | 检查API额度、许可证与鉴权 |
| P0 | [Asta Resources](https://allenai.org/asta/resources) · Ai2 | 科研工具、Agent模板、科学语料接口 | API / MCP | 规模与访问策略随服务更新 |
| P0 | [PaperQA](https://github.com/Future-House/paper-qa) · FutureHouse | 来源溯源的论文问答 | 源码复用 | 全文获取与版权、引用真实性 |
| P0 | [OpenScholar](https://github.com/AkariAsai/OpenScholar) · Ai2 / UW | 检索增强科研文献综合 | 源码与方法复用 | 模型/索引获取成本、许可 |
| P1 | [ScholarQABench](https://github.com/AkariAsai/ScholarQABench) · OpenScholar team | 检验科研问答与引用质量 | 评测集成 | 检查评测数据泄漏 |
| P0 | [Semantic Scholar Academic Graph API](https://api.semanticscholar.org/api-docs) · Ai2 | 论文/作者/引用图谱 | API适配器 | 限流/缺失字段/全文授权 |
| P1 | [Semantic Scholar Recommendations API](https://api.semanticscholar.org/api-docs/recommendations) · Ai2 | 相关论文推荐 | API适配器 | 推荐偏差和相关性核查 |
| P0 | [OpenAlex API](https://help.openalex.org/api/) · OurResearch | 论文、机构、作者和主题图谱 | API适配器 | 接口限制/免费额度政策动态 |
| P0 | [Crossref REST API](https://www.production.crossref.org/documentation/retrieve-metadata/rest-api/) · Crossref | DOI校验、出版信息、撤稿/更新 | API适配器 | 不同出版社元数据质量不一致 |
| P0 | [arXiv](https://info.arxiv.org/help/api/index.html) · Cornell / arXiv | 预印本检索与更新 | API / RSS | 预印本非同行评审，不等于最终版本 |
| P1 | [OpenReview](https://docs.openreview.net/) · OpenReview | 同行评审、投稿版本、评分与讨论 | API适配器 | 会议数据访问范围/隐私 |
| P0 | [Zotero Web API v3](https://www.zotero.org/support/dev/web_api/v3/start) · Zotero | 个人文献库与引用元数据 | API适配器 | 私有库授权/OAuth |
| P1 | [Hugging Face Papers CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) · Hugging Face | 每日/趋势论文发现 | CLI适配器 | 热度不等于学术质量 |
| P1 | [MinerU](https://github.com/opendatalab/MinerU) · OpenDataLab | PDF科学文档结构化解析 | 容器化适配 | PDF解析误差、排版与授权 |

### 03 Harness / Skills / MCP（16）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P0 | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) · OpenAI | 模型无关Agent、工具、Guardrails与Tracing | 框架候选 | 需要自行管理任务状态、资源与sandbox |
| P1 | [OpenAI Agents API](https://developers.openai.com/api/docs/guides/agents-api/overview) · OpenAI | 托管Codex harness及持久Session | 托管服务候选 | 价格、云端数据范围与厂商锁定 |
| P0 | [Google ADK](https://github.com/google/adk-python) · Google | 图式工作流、多Agent委派、HITL | 框架候选 | 版本快、锁定版本测试 |
| P0 | [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) · LangChain | 持久执行、Checkpoints、状态与恢复 | 框架候选 | Agent抽象和运行状态复杂度 |
| P1 | [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) · Microsoft | 工作流、Agent、Harness、可观测性 | 框架候选 | 框架成熟度/迁移风险 |
| P0 | [OpenHands](https://github.com/OpenHands/OpenHands) · OpenHands | 代码Agent与自动化控制台 | 研发执行层候选 | 沙箱安全、远程环境权限 |
| P1 | [smolagents](https://github.com/huggingface/smolagents) · Hugging Face | 轻量代码执行Agent | 轻量候选 | 执行隔离和模型兼容性 |
| P0 | [Agent Skills specification](https://agentskills.io/) · Agent Skills | 跨Agent技能标准 | 规范借鉴 | 执行宿主存在差异 |
| P0 | [OpenAI Plugins examples](https://github.com/openai/plugins) · OpenAI | 最新插件和Skill示例 | 复用模板 | 逐项核对技能许可证 |
| P0 | [Anthropic Skills](https://github.com/anthropics/skills) · Anthropic | Skill实践样例 | 复用模板 | 不同技能使用条款不同 |
| P0 | [Model Context Protocol](https://modelcontextprotocol.io/) · MCP Contributors | Agent工具/资源/提示词标准互联 | 标准接口 | 授权/数据隔离/Prompt Injection |
| P0 | [MCP Registry](https://registry.modelcontextprotocol.io/) · MCP Contributors | 查找MCP工具服务器 | 插件索引 | 第三方服务可信度 |
| P1 | [MCP Reference Servers](https://github.com/modelcontextprotocol/servers) · MCP Contributors | 参考服务器实现 | 参考代码 | 官方声明非生产就绪 |
| P0 | [LiteLLM](https://github.com/BerriAI/litellm) · BerriAI | 统一多模型API网关 | 模型接入层 | 计费/日志保密/版本兼容 |
| P1 | [Awesome Code-as-Agent Harness Papers](https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers) · Community | Harness相关论文和代码集 | 二级资源索引 | 非官方完整性保证 |
| P0 | [Orchestra AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) · Orchestra Research | 98研究Skills：autoresearch、ideation、ML训练、GPU系统、论文、评测 | 优先挑选接入（不要自动全安装） | 大量第三方脚本和依赖必须逐项审查；Skill内容要实测 |

### 04 评测与可观测性（9）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P0 | [AstaBench](https://github.com/allenai/asta-bench) · Ai2 | 科研Agent任务综合评测 | 核心基准 | 数据污染、评分主观性 |
| P0 | [Inspect AI](https://inspect.aisi.org.uk/) · UK AI Security Institute | 开放Agent/LLM评测框架 | 核心评测框架 | 环境隔离与评分器校准 |
| P0 | [PaperBench](https://github.com/openai/frontier-evals/tree/main/project/paperbench) · OpenAI | 复制AI科研论文能力 | 专项基准 | GPU成本、评分标准 |
| P0 | [MLE-bench](https://github.com/openai/mle-bench) · OpenAI | 机器学习工程任务能力 | 专项基准 | 实验成本/种子/数据访问 |
| P1 | [ScienceAgentBench](https://hal.cs.princeton.edu/scienceagentbench) · Princeton and collaborators | 科学数据分析任务 | 专项基准 | 公开任务变更 |
| P0 | [Arize Phoenix](https://github.com/Arize-ai/phoenix) · Arize AI | Agent调用Trace、评测、Prompt管理 | 观测候选 | 日志可能含私人和未公开研究数据 |
| P0 | [Langfuse](https://github.com/langfuse/langfuse) · Langfuse | Trace、成本、质量评估、管理 | 观测候选 | 敏感prompt/数据去标识化 |
| P1 | [OpenAI Agent Evals](https://developers.openai.com/api/docs/guides/agent-evals) · OpenAI | Trace grading、datasets、graders | 工程最佳实践 | 对外部平台的依赖 |
| P0 | [Skill Evals Guide](https://developers.openai.com/blog/eval-skills) · OpenAI | 技能回归与效果评测 | 开发规范 | 评价器与人工质量一致性 |

### 05 科研计算与复现（14）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P0 | [MLflow Tracking](https://mlflow.org/docs/latest/tracking/) · MLflow | 记录模型参数、指标、工件和版本 | 直接集成 | 日志与存储治理 |
| P0 | [DVC](https://doc.dvc.org/user-guide) · Iterative | 数据版本和实验管线 | 直接集成 | 远程存储权限与成本 |
| P1 | [Weights & Biases](https://docs.wandb.ai/) · W&B | 运行追踪、Artifacts、Sweeps | 可替代MLflow | 云服务定价与数据治理 |
| P1 | [Hydra](https://hydra.cc/) · Meta / community | 结构化配置与多实验运行 | 集成 | 配置复杂性 |
| P1 | [Ray Tune](https://docs.ray.io/en/latest/tune/index.html) · Anyscale / community | 分布式搜索与优化 | 计算调度层候选 | 集群环境与依赖 |
| P0 | [Slurm](https://slurm.schedmd.com/documentation.html) · SchedMD | HPC作业调度与GPU管理 | 适配现有集群 | 集群管理者授权/队列规则 |
| P0 | [Docker](https://docs.docker.com/) · Docker | 容器化实验与Agent沙箱 | 运行隔离 | 默认容器不是完整安全边界 |
| P1 | [Apptainer](https://apptainer.org/docs/user/main/) · Apptainer | 适配HPC容器环境 | 计算集群候选 | 集群软件与管理员设置 |
| P1 | [Zenodo](https://zenodo.org/) · CERN / OpenAIRE | 科研工件持久归档与DOI | 可选归档 | 公开前人工批准 |
| P1 | [CodeOcean / FAIR Principles](https://www.go-fair.org/fair-principles/) · GO FAIR | 可发现可访问可互操作可复用 | 数据规范 | 指导性质而非库 |
| P0 | [Snakemake](https://snakemake.readthedocs.io/en/stable/) · Scientific workflow community | 确定性可复验DAG分析流水线 | 工作流后端候选 | 业务规则需适配，可能与其他workflow引擎重叠 |
| P1 | [Parsl](https://github.com/Parsl/parsl) · University of Chicago / Argonne / UIUC | HPC/云端Python并行作业 | 计算后端候选 | 调度环境支持和共享集群权限核查 |
| P1 | [Open Science Framework API](https://developer.osf.io/) · Center for Open Science | 开放科学项目、文件、预注册与元数据管理 | 成果归档适配器 | 上传公开前人工审查 |
| P0 | [Harvard Kempner HPC Agentic Recipes](https://github.com/KempnerInstitute/hpc-agentic-recipes) · Harvard Kempner Institute | HPC本地模型+SLURM+研究Agent实践 | 集群部署参考 | 具体环境与学校规定不可直接移植 |

### 06 机构科研规范（15）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P0 | [MIT The Use of AI in Research and Scholarship](https://research.mit.edu/security-integrity-and-compliance/research-integrity/mits-guidelines-ethical-authorship-and-publication-practices/use-ai-research-and-scholarship-mit) · MIT | AI使用、披露、准确性、保密 | 合规规则库 | 院校规则不自动代替目标会议规则 |
| P0 | [Stanford AI in Academic Research](https://guides.library.stanford.edu/ai_research/how_to_use_AI) · Stanford Libraries | AI研究实践和评估 | 方法参考 | 学校指引并非每会议硬约束 |
| P1 | [Stanford Citation Guidelines](https://guides.library.stanford.edu/ai_research/citation_guidelines) · Stanford Libraries | AI披露与引用风格 | 写作核查 | 期刊规则优先 |
| P0 | [Stanford Research Rigor & Reproducibility](https://med.stanford.edu/sporr/support/resources.html) · Stanford Medicine | 实验室手册/复现/研究记录 | 方法参考 | 根据课题适配 |
| P0 | [UC Berkeley Agentic AI Guidance](https://ai.berkeley.edu/guidance/appropriate-use-generative-and-agentic-ai) · UC Berkeley | 数据安全、Agent工具使用 | 合规参考 | 具体数据类别敏感 |
| P1 | [UC Berkeley Reproducible Research Guide (UC Davis DataLab)](https://ucdavisdatalab.github.io/guide_reproducible_research/chapters/01_principles.html) · UC Davis | 研究日志/数据治理/复现 | 方法参考 | 注意不是Berkeley机构 |
| P0 | [ACM Policy on Authorship 2026](https://prod-www.acm.bloomreach.cloud/publications/policies/new-acm-policy-on-authorship) · ACM | 科研用AI方法描述及作者责任 | 投稿规范 | 投稿会议单独规则可能更严格 |
| P0 | [IEEE AI Generated Text Guidelines](https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/) · IEEE | AI生成内容的明确披露 | 投稿规范 | 具体期刊和会议要求可能变化 |
| P0 | [AAAI-27 Main Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/) · AAAI | AI使用、可复现性 | 投稿规范 | 与AAAI-27另一个政策页面用词存在冲突，须人工核对 |
| P0 | [AAAI-27 Author Policies](https://aaai.org/conference/aaai/aaai-27/policies-for-aaai-27-authors/) · AAAI | LLM生成文本规则 | 投稿规范 | 和AAAI主技术Track Call存在表面冲突，严禁自行取宽松解释 |
| P0 | [NeurIPS 2026 Main Track Handbook](https://nips.cc/Conferences/2026/MainTrackHandbook) · NeurIPS | LLM研究方法、Checklist、伦理 | 投稿规范 | 2027要重新核对 |
| P0 | [CCF科研行为与学术道德规范2026](https://www.ccf.org.cn/About_CCF/CCF_Constitution/2026-07-16/915412.shtml) · CCF | 人主导科研思想、AI声明、真实数据 | 投稿规范 | 需区分适用对象和不同会场 |
| P1 | [Publisher AI Policy Index](https://guides.library.cmu.edu/publishing/AI) · CMU Libraries | 出版社AI使用规则导航 | 合规索引 | 索引不能代替主办方原文 |
| P0 | [Harvard Kempner Agentic AI in Research](https://handbook.eng.kempnerinstitute.harvard.edu/s5b_agentic_ai_workflows/agentic_ai_in_research.html) · Harvard Kempner Institute | 科研Agent实验实践、权限与人工控制 | 方法参考 | 不可视作投稿期刊的唯一规范 |
| P0 | [Designing Reproducible LLM-Assisted Scientific Analyses](https://pmc.ncbi.nlm.nih.gov/articles/PMC13576654/) · Patterns (2026) | LLM处于数据路径内/外、科研可复现性 | 科研方法论 | 需保留模型版本、工具链、确定性测试 |

### 07 公司与个人工程经验（15）

|优先级|资源|角色/贡献|建议使用|风险备注|
|---|---|---|---|---|
| P0 | [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) · Anthropic | 工作流与Agent基本模式 | 架构方法 | 模式适用性需要本地评测 |
| P0 | [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · Anthropic | 跨会话初始化、进度文件、恢复 | Harness方法 | 长任务状态丢失 |
| P0 | [Multi-Agent Research System Engineering](https://www.anthropic.com/engineering/multi-agent-research-system) · Anthropic | 研究Agent并行与质量控制 | 架构方法 | 来源偏差、并行成本 |
| P0 | [Effective Context Engineering for AI Agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) · Anthropic | 上下文管理与工具信息选择 | 记忆/上下文设计 | 摘要损失重要状态 |
| P0 | [Demystifying Evals for AI Agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) · Anthropic | 多轮评测/Outcome/Trace/人工校准 | 测试原则 | LLM评审标准漂移 |
| P0 | [Hamel Husain Eval FAQ](https://hamel.dev/blog/posts/evals-faq/) · Hamel Husain & Shreya Shankar | 失败分析与人类标注指南 | 实践经验 | 经验指南非标准规范 |
| P1 | [Hamel Agentic Workflow Evals](https://hamel.dev/blog/posts/evals-faq/how-do-i-evaluate-agentic-workflows.html) · Hamel Husain & Shreya Shankar | 先终态再逐步诊断 | 实践经验 | 前期先收集足够轨迹 |
| P0 | [Karpathy autoresearch program.md](https://github.com/karpathy/autoresearch/blob/master/program.md) · Andrej Karpathy | 个人开发者可执行实验指令 | 技能模板 | 严禁裸奔无上限耗费；正式项目需预算限制 |
| P1 | [OpenAI Deep Research System Card](https://openai.com/index/deep-research-system-card/) · OpenAI | 提示注入、幻觉、隐私评估 | 安全参考 | 特定产品系统卡不等于所有Research Agent |
| P0 | [Lilian Weng Harness Engineering for Self-Improvement](https://lilianweng.github.io/posts/2026-07-04-harness/) · Lilian Weng | Harness工程与自我改进Agent | 深入研读 | 落地需实测其适用范围 |
| P1 | [Lilian Weng LLM-Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) · Lilian Weng | 规划、记忆、工具调用的系统综述 | 知识背景 | 较早文章需结合近年实务更新 |
| P1 | [Karpathy No Priors Interview on AutoResearch](https://www.youtube.com/watch?v=kwSVtQ7dziU) · No Priors / Andrej Karpathy | 开发者访谈：自动科研与研究工程 | 访谈素材 | 访谈意见≠可复现验证 |
| P0 | [Simon Willison Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/) · Simon Willison | Git、测试驱动、Agent工作方式、错误模式 | 工程手册 | 按研发环境裁剪 |
| P0 | [Simon Willison First Run the Tests](https://simonwillison.net/guides/agentic-engineering-patterns/first-run-the-tests/) · Simon Willison | Agent开始前先验证原测试、再增量迭代 | 工程工作流实践 | 仅有测试通过不等同科学结论可靠 |
| P0 | [Harvard Kempner SLURM Jobs and Cluster Workflows](https://handbook.eng.kempnerinstitute.harvard.edu/s5b_agentic_ai_workflows/slurm_jobs_and_cluster_workflows.html) · Harvard Kempner Institute | Agent只读状态查询和需审批提交任务的权限分离 | HPC权限架构方法 | 每个共享集群需遵守管理政策 |

## 下一阶段源码审计表（逐项填写）

- URL / tag / commit SHA / last_release / maintenance:
- LICENSE、NOTICE、权重license、dataset license和使用条款：
- Runtime（CPU/GPU/内存/依赖/入口命令）：
- API/MCP/CLI/Python入口、输入输出schema：
- 数据权限、密钥、网络访问、sandbox威胁模型：
- 最小端到端Demo是否运行成功：
- 质量/成本/延迟/稳定性：
- 对接点、失败恢复、替代项目、弃用策略：

## 特别提醒：AAAI-27规则表述不一致

[AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/) 与 [Policies for AAAI-27 Authors](https://aaai.org/conference/aaai/aaai-27/policies-for-aaai-27-authors/) 有关于LLM生成文本的不同措辞。不能据其一擅自判定允许；实际投稿前应核对最新说明并请会议方澄清。

## 推荐文件布局

```text
research-os/
  docs/resources/RESOURCE_CATALOG.md
  catalog/resources.json
  catalog/resources.csv
  catalog/integration-audits/
  policies/venue-ai-use/
  skills/
  connectors/
  workflows/
  evals/
  experiments/
```
