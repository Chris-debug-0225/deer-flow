# DeerFlow 学习 HTML 重构设计说明

**目标：** 深度重构 `.learning/html/` 下与 DeerFlow 核心架构、执行引擎、扩展机制和实战构建直接相关的一组学习章节，使读者在读完后掌握的是 DeerFlow 当前仓库里的真实架构、运行时边界和具体实现，而不是“通用 Agent 系统教程 + 少量 DeerFlow 例子”。

**范围：** 本设计覆盖以下章节的成体系重构，同时保持它们的文件名、导航顺序和入口关系不变：

- `.learning/html/02-llm-and-tools.html`
- `.learning/html/03-deerflow-overview.html`
- `.learning/html/10-agent-execution-engine.html`
- `.learning/html/11-skills-system.html`

- `.learning/html/12-sandbox-execution.html`
- `.learning/html/13-memory-system.html`
- `.learning/html/14-sub-agents.html`
- `.learning/html/15-gateway-api.html`
- `.learning/html/20-context-engineering.html`
- `.learning/html/21-model-integration.html`
- `.learning/html/22-channels-integration.html`
- `.learning/html/23-advanced-patterns.html`
- `.learning/html/30-custom-skills-guide.html`
- `.learning/html/31-building-custom-agents.html`
- `.learning/html/32-from-scratch-guide.html`
- `.learning/html/40-source-code-guide.html`
- `.learning/html/41-troubleshooting-faq.html`

**非目标：**

- 不重命名章节文件，不改变当前顶层课程导航顺序。
- 不重写无关章节，除非为了术语统一或交叉引用必须同步调整。
- 不继续保留那些 DeerFlow 并未真实实现、却以“通用业界最佳实践”名义出现的大段内容；除非明确标注为背景知识且与 DeerFlow 当前实现分开。

---

## 一、为什么必须重写

当前 `.learning/html` 这一套学习资料的选题方向基本正确，但这些核心章节存在一个共同问题：它们并不稳定地以 DeerFlow 为中心展开。部分页面更像“通用 Agent 教程”，只是夹带了一些 DeerFlow 示例或术语。这会带来 3 类学习偏差：

1. 读者读完后，对 DeerFlow 当前真实能力边界形成错误心智模型。
2. 读者无法稳定定位 DeerFlow 的真实代码入口、运行路径、配置面和架构边界。
3. 读者会把“通用概念上可以这么做”误解成“DeerFlow 现在就是这么实现的”。

因此，这次重构不能再以旧 HTML 为主、源码为辅，而必须反过来：**以 DeerFlow 当前仓库实现为真相来源，以教学表达服务于源码理解。**

## 二、真相来源优先级

当不同材料之间出现冲突时，章节内容必须遵循下面的优先级：

1. `backend/app/gateway/` 与 `backend/packages/harness/deerflow/` 下的真实运行时代码
2. 仓库中的一手文档，如 `README.md`、`backend/docs/ARCHITECTURE.md`、`backend/docs/API.md`、`backend/docs/AUTH_DESIGN.md`、`backend/docs/CONFIGURATION.md` 以及相关专题设计文档
3. 锁定行为的测试
4. 现有 `.learning/html` 内容

如果 DeerFlow 当前没有实现某个旧章节里提到的能力，那么该内容必须删除，或者明确改写成“背景知识，不代表 DeerFlow 当前实现”。

## 三、读者最终应获得什么

完成这一组章节后，读者应当能够：

- 解释 DeerFlow 的 Gateway-embedded runtime 与独立 LangGraph Server 部署之间的差异。
- 追踪 sandbox、memory、subagents、models、channels、skills、custom agents 在 DeerFlow 中是如何通过代码与配置串起来的。
- 找到每项能力的主要代码入口。
- 理解 DeerFlow 当前的安全边界、持久化边界、多用户边界与部署边界。
- 在扩展 DeerFlow 时不依赖错误抽象，而是基于真实实现做判断。

## 四、统一章节骨架

这些重写后的章节都必须使用同一套 DeerFlow-first 骨架，只根据复杂度调整篇幅：

1. **这项能力在 DeerFlow 中解决什么问题**
2. **这项能力在代码库中的位置**
3. **真实运行链路或数据链路**
4. **配置面与使用方式**
5. **关键实现细节与权衡**
6. **当前限制、边界与非目标**
7. **它与 DeerFlow 其他能力的关系**

这套骨架的目的，是确保每章都在回答两个关键问题：

- “DeerFlow 里这东西到底在哪实现？”
- “DeerFlow 里这东西到底是怎么工作的？”

通用理论只能作为短背景引入，不能再喧宾夺主。

## 五、内容重写规则

### 规则 1：必须 DeerFlow-first 开场

每章开头必须从 DeerFlow 的实际问题与实现职责切入，而不是从教科书式定义切入。

### 规则 2：必须给出真实代码入口

每章都必须明确指出实现该能力的具体文件、模块、router、middleware 或配置入口。高价值入口包括但不限于：

- `backend/app/gateway/app.py`
- `backend/app/gateway/routers/*.py`
- `backend/packages/harness/deerflow/agents/*`
- `backend/packages/harness/deerflow/sandbox/*`
- `backend/packages/harness/deerflow/subagents/*`
- `backend/packages/harness/deerflow/skills/*`
- `backend/packages/harness/deerflow/client.py`

### 规则 3：必须写清真实运行链路

不能只罗列类名与文件名。每章都必须至少解释一条真实执行路径或数据路径，让读者知道请求从哪里进入、状态在哪里变化、结果如何输出。

### 规则 4：配置不是附录，而是实现的一部分

如果某项行为受 `config.yaml`、环境变量、feature flag 或运行时配置控制，那么章节里必须把这些配置面当成核心设计的一部分来讲，而不是作为末尾补充。

### 规则 5：限制与边界必须显式写出

每章都必须说明 DeerFlow 当前有哪些限制或明确边界。仓库中已经能确认的例子包括：

- Gateway 的 run state 是进程内持有的，因此默认 worker 数受到约束。
- Local sandbox 是便捷模式，不是安全 shell 隔离边界。
- IM channel 复用 Gateway runtime 语义和内部认证机制。
- 某些公共 API 兼容性依赖翻译层或兼容 shim。

### 规则 6：禁止写无法被仓库验证的泛化结论

像“系统可以水平无限扩展”“支持任意长期学习”“多个 agent 通过共享记忆协作”这类表述，除非当前仓库实现能够直接支撑，否则不能出现。

## 六、章节分组与重构设计

### A. 架构总览与执行主线章节

这几章负责先把 DeerFlow 的总图、模型与工具主线、执行主线和扩展主线讲清楚，否则后续 sandbox、memory、gateway、skills、custom agent 等章节会各说各话。

### 02. LLM 调用与工具系统

**在 DeerFlow 中的核心定位**

把 DeerFlow 中“模型”和“工具”如何共同构成 agent 能力底座讲清楚，为后续执行引擎、skills、sandbox、subagents、context engineering 打基础。

**主要代码锚点**

- `backend/packages/harness/deerflow/tools/tools.py`
- `backend/packages/harness/deerflow/tools/builtins/*`
- `backend/packages/harness/deerflow/agents/factory.py`
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `backend/packages/harness/deerflow/config/app_config.py`
- `backend/docs/CONFIGURATION.md`
- `README.md`

**必须覆盖的内容**

- DeerFlow 里模型能力与工具能力分别由什么配置面和运行时路径接入。
- built-in tools、configured tools、MCP tools 在 DeerFlow 中如何汇总到 agent 可用能力集合。
- tool groups、tool exposure、tool search 与 prompt 提示之间的关系。
- 为什么“LLM 调用”在 DeerFlow 中不能脱离 tools、skills、memory、middleware 单独理解。
- 这一章与 `10-agent-execution-engine`、`11-skills-system`、`20-context-engineering` 的边界。

**重点修正方向**

- 删除把工具系统写成 LangChain/LLM 通用概论的段落，改成 DeerFlow 的真实装配路径。
- 强调 DeerFlow 里“模型 + 工具 + prompt/runtime 装配”是一个联动系统，而不是三个松散主题。

### 03. DeerFlow 整体架构概览

**在 DeerFlow 中的核心定位**

把 DeerFlow 作为一个整体系统先讲清楚：统一入口、Gateway-embedded runtime、frontend、channels、sandbox、memory、skills、custom agents、embedded client 之间的关系。

**主要代码锚点**

- `README.md`
- `backend/docs/ARCHITECTURE.md`
- `backend/app/gateway/app.py`
- `backend/packages/harness/deerflow/client.py`
- `backend/packages/harness/deerflow/agents/lead_agent/agent.py`

**必须覆盖的内容**

- nginx、Gateway、frontend 的整体关系。
- 为什么 DeerFlow 的默认运行时不是“单独起一个 LangGraph Server 再外接一层 API”。
- 哪些是共享 runtime 组件，哪些是外围接入层。
- 这一章如何为后续执行引擎、skills、sandbox、memory、channels、custom agents 建立统一心智模型。

**重点修正方向**

- 如果旧文仍然把 DeerFlow 讲成松散拼装的框架，需要改成“有明确默认运行时主路径的 super agent harness”。

### 10. Agent 执行引擎的设计与实现

**在 DeerFlow 中的核心定位**

把 DeerFlow 的执行引擎讲成一条真实可追踪的运行主线：请求如何进入 lead agent、middleware 如何参与、tools 如何被装配、run/stream 如何被 Gateway 持有，以及运行态状态如何流动。

**主要代码锚点**

- `backend/packages/harness/deerflow/agents/lead_agent/agent.py`
- `backend/packages/harness/deerflow/agents/factory.py`
- `backend/packages/harness/deerflow/agents/thread_state.py`
- `backend/packages/harness/deerflow/agents/middlewares/*`
- `backend/packages/harness/deerflow/runtime/runs/worker.py`
- `backend/app/gateway/routers/thread_runs.py`
- `backend/docs/ARCHITECTURE.md`
- `backend/docs/STREAMING.md`

**必须覆盖的内容**

- lead agent 的构建入口与 runtime feature 装配。
- middleware 链在 DeerFlow 中的真实职责，而不是抽象设计模式展示。
- `ThreadState` 扩展了哪些 DeerFlow 特有状态。
- tools、memory、sandbox、subagent、view-image、todo、summarization 如何进入执行主线。
- Gateway 路径与 `DeerFlowClient` 路径的共性与差异。
- streaming、run lifecycle、事件流转与状态持有边界。

**重点修正方向**

- 删除“执行引擎只是一个 while-loop + tool calling”的简化叙事。
- 明确 DeerFlow 执行引擎是“agent 构建 + middleware + tool/runtime orchestration + stream/run ownership”的组合。

### 11. Skills 系统：Agent 的能力扩展

**在 DeerFlow 中的核心定位**

讲清 DeerFlow 的 skills 系统如何参与 prompt/runtime 扩展、安装与存储，以及它和 tools、tool_search、custom agents 的关系。

**主要代码锚点**

- `backend/packages/harness/deerflow/skills/*`
- `backend/packages/harness/deerflow/skills/installer.py`
- `backend/app/gateway/routers/skills.py`
- `backend/packages/harness/deerflow/tools/builtins/tool_search.py`
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `README.md`

**必须覆盖的内容**

- DeerFlow 中 skill 的角色边界：它不是简单等于 tool，也不是默认等于代码插件。
- skill 如何被发现、安装、存储、启用与注入 prompt。
- Gateway 安装 skill 与本地 skill 生命周期的区别。
- skill 与 tool_search、tool groups、custom agent persona 之间的衔接。
- 为什么 11、30 两章不能重复讲成一回事。

**重点修正方向**

- 第 11 章偏“系统设计与运行机制”，第 30 章偏“用户如何定义与构建自定义 skill”。
- 删除把 skills 与 tools 混为一谈的旧表述。

### 12. Sandbox 与安全执行环境

**在 DeerFlow 中的核心定位**

说明 DeerFlow 如何为 Agent 提供文件与命令执行能力，同时把“抽象的 sandbox 契约”与“具体的 provider 实现”分层开。

**主要代码锚点**

- `backend/packages/harness/deerflow/sandbox/tools.py`
- `backend/packages/harness/deerflow/sandbox/sandbox.py`
- `backend/packages/harness/deerflow/sandbox/sandbox_provider.py`
- `backend/packages/harness/deerflow/sandbox/local/local_sandbox_provider.py`
- `backend/packages/harness/deerflow/sandbox/security.py`
- `backend/docs/CONFIGURATION.md`
- `README.md`

**必须覆盖的内容**

- sandbox tool 第一次被调用时的 lazy acquisition 机制。
- `LocalSandboxProvider` 与 `AioSandboxProvider` 的差异。
- 线程级虚拟路径契约（`/mnt/user-data/...`）及其存在原因。
- `allow_host_bash` 为什么默认是 `false`。
- 本地模式的便利性与容器模式的隔离性差异。
- sandox 文件工具如何避免直接依赖宿主机路径假设。
- 仓库中已有的安全强化细节，包括 artifact serving 为降低 XSS 风险所做的处理。

**重点修正方向**

- 删除“所有 DeerFlow sandbox 模式安全性等价”这类误导。
- 删除与当前 provider 或配置不一致的泛泛容器安全叙述。

### 13. 长期记忆系统

**在 DeerFlow 中的核心定位**

说明 DeerFlow 的 memory 不是抽象的“Agent 大脑”，而是一套明确的存储、注入、更新、用户隔离与事实管理流水线。

**主要代码锚点**

- `backend/packages/harness/deerflow/agents/memory/prompt.py`
- `backend/packages/harness/deerflow/agents/memory/storage.py`
- `backend/packages/harness/deerflow/agents/memory/updater.py`
- `backend/app/gateway/app.py`
- `backend/docs/MEMORY_IMPROVEMENTS_SUMMARY.md`
- `backend/docs/AUTH_DESIGN.md`
- `README.md`

**必须覆盖的内容**

- memory 数据结构与存储实现。
- per-user 与 per-agent 的 memory 路径隔离。
- memory 如何注入 prompt。
- 基于 LLM 的 memory 更新流程与后处理保护。
- memory、summarization、thread history、runtime state 之间的区别。
- 持久化与 in-memory fallback 等运行层注意事项。

**重点修正方向**

- 删除“DeerFlow 默认采用向量数据库长期记忆架构”这类不实暗示，除非明确标成扩展背景而非默认实现。
- 明确区分长期记忆、线程 checkpoint 历史与 Run/Event 存储。

### 14. Sub-Agents：多 Agent 协作

**在 DeerFlow 中的核心定位**

讲清 DeerFlow 当前真实的 subagent 模型：通过内置 `task` tool 发起委派任务，在隔离上下文中执行，通过 registry/config 决定类型，并把 token/结果回传给父运行。

**主要代码锚点**

- `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
- `backend/packages/harness/deerflow/subagents/executor.py`
- `backend/packages/harness/deerflow/subagents/registry.py`
- `backend/packages/harness/deerflow/subagents/config.py`
- `backend/packages/harness/deerflow/config/subagents_config.py`
- `README.md`
- `backend/docs/task_tool_improvements.md`

**必须覆盖的内容**

- lead agent 是通过 `task` tool 委派，而不是走独立编排服务。
- built-in subagent 与 custom subagent 的差异。
- 隔离上下文模型，以及为什么默认不递归继续拉起 subagent。
- timeout、polling、cleanup、协作式取消机制。
- subagent token usage 如何归因回父级 dispatch 步骤。
- sandbox 可用性如何影响 subagent 的暴露集合。

**重点修正方向**

- 删除“多 agent 共享黑板 / 共享记忆协作”之类泛化叙述，除非仓库里真有对应实现。
- 强调结构化委派与上下文隔离，而不是“群体智能”式比喻。

### 15. Gateway API：与外界的接口

**在 DeerFlow 中的核心定位**

说明 Gateway 不是薄代理层，而是 DeerFlow 默认运行时的主要承载体：负责 agent 执行、公共 API、兼容层、streaming、配置访问、uploads、artifacts 与 thread cleanup。

**主要代码锚点**

- `backend/app/gateway/app.py`
- `backend/app/gateway/routers/thread_runs.py`
- `backend/app/gateway/routers/threads.py`
- `backend/app/gateway/routers/uploads.py`
- `backend/app/gateway/routers/artifacts.py`
- `backend/docs/API.md`
- `backend/docs/ARCHITECTURE.md`
- `README.md`

**必须覆盖的内容**

- nginx 如何把 `/api/langgraph/*` 重写到 Gateway 拥有的 LangGraph-compatible 路由。
- `/api/langgraph/*` 公共兼容路径与 Gateway-native router 的区别。
- SSE streaming 路径与 run lifecycle 由谁持有。
- 为什么 Gateway worker 默认是 1。
- `DeerFlowClient` 与 Gateway 的一致性与有意差异。
- CORS、CSRF、auth、内部 channel 调用机制。

**重点修正方向**

- 删除“DeerFlow 默认运行时是独立 LangGraph Server”这种错误暗示。
- 准确区分 Gateway-owned 路径与 embedded client 路径。

### 20. 上下文工程：提升 Agent 智能

**在 DeerFlow 中的核心定位**

把“上下文工程”重写成 DeerFlow 里的真实上下文塑形机制：lead-agent prompt 构造、skills 注入、memory 注入、tool availability、middleware 注入状态、summarization，以及 upload/view-image 上下文拼接。

**主要代码锚点**

- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `backend/packages/harness/deerflow/agents/factory.py`
- `backend/packages/harness/deerflow/agents/middlewares/*`
- `backend/packages/harness/deerflow/tools/builtins/tool_search.py`
- `backend/packages/harness/deerflow/agents/memory/prompt.py`

**必须覆盖的内容**

- prompt 的不同 section 如何由 config、skills、memory、mounts、runtime capabilities 拼出来。
- middleware 为什么也是上下文塑形器，而不只是拦截器。
- summarization 与 memory 如何缓解或重塑上下文压力。
- tool exposure 与 tool-search 提示为什么也是上下文工程的一部分。
- 图片与上传内容如何进入模型上下文。

**重点修正方向**

- 删除与 DeerFlow runtime surface 无关的大段 prompt engineering 泛论。
- 用 DeerFlow 的真实上下文层替代纯通用的 “system / user / tool prompt” 图示。

### 21. 模型集成：支持多种 LLM

**在 DeerFlow 中的核心定位**

讲清 DeerFlow 的模型抽象与配置方式，以及不同运行角色如何解析、继承或覆盖模型选择。

**主要代码锚点**

- `backend/packages/harness/deerflow/config/app_config.py`
- `backend/packages/harness/deerflow/subagents/config.py`
- `backend/packages/harness/deerflow/config/subagents_config.py`
- `backend/app/gateway/routers/models.py`
- `backend/packages/harness/deerflow/client.py`
- `backend/docs/CONFIGURATION.md`

**必须覆盖的内容**

- 模型配置位于 `config.yaml`。
- runtime 组件如何通过 DeerFlow 的配置/工厂边界消费模型。
- subagent 如何继承或覆盖模型选择。
- 与模型能力差异相关的实现点，例如 vision support、memory-update model。
- Gateway API 与 embedded client 如何暴露和使用模型配置，但入口不同。

**重点修正方向**

- 删除“DeerFlow 已内建任意 provider 自动路由器”之类超出当前实现的叙述。
- 优先解释当前配置与运行时解析路径，而不是臆想式策略模式。

### 22. 多渠道集成：从 IM 到 API

**在 DeerFlow 中的核心定位**

说明 DeerFlow 如何通过统一的 Gateway-centered runtime 同时服务浏览器/API 与 IM channels，并用 adapter 处理不同渠道的消息接入、身份传播和状态连续性。

**主要代码锚点**

- `backend/app/channels/manager.py`
- `backend/app/channels/base.py`
- `backend/app/channels/feishu.py`
- `backend/app/gateway/routers/channels.py`
- `backend/app/gateway/routers/channel_connections.py`
- `README.md`
- `backend/docs/AUTH_DESIGN.md`

**必须覆盖的内容**

- API 路径与 IM channel 路径的关系。
- channel worker 如何在内部调用 Gateway 的 LangGraph-compatible API。
- browser-connectable channel connections 与静态渠道配置的区别。
- identity propagation、CSRF/internal auth 要求。
- 外部文件/资源如何同步成 sandbox 可见路径。
- Docker Compose 或分离部署下的运行注意事项。

**重点修正方向**

- 删除“每个渠道都有独立 agent runtime”这种错误图景。
- 强调 channel 是 shared runtime 的接入层，而不是平行编排系统。

### 23. 高级模式和最佳实践

**在 DeerFlow 中的核心定位**

这一章不能再写成脱离代码的“高级技巧合集”，而要总结 DeerFlow 当前仓库中已经成形的高级模式，例如 Gateway-embedded runtime、tool search、subagent delegation、shared runtime + channel adapters、sandbox-aware execution、memory/summarization 协作等。

**主要代码锚点**

- `README.md`
- `backend/docs/ARCHITECTURE.md`
- `backend/docs/STREAMING.md`
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
- `backend/packages/harness/deerflow/tools/builtins/tool_search.py`
- `backend/packages/harness/deerflow/agents/middlewares/*`

**必须覆盖的内容**

- DeerFlow 当前已经采用的模式，而不是抽象模式 catalog。
- 什么是 DeerFlow 里的推荐做法，什么只是通用背景。
- 各模式如何在真实仓库中落地并彼此配合。

**重点修正方向**

- 删除“泛化最佳实践列表”式写法，改成“DeerFlow 已采用的高级模式总结”。

### 30. 自定义 Skills 完全指南

**在 DeerFlow 中的核心定位**

讲清 DeerFlow 里的 skill 到底是什么、如何打包、发现、安装、存储和注入运行时，而不是停留在“skill 就是一段 prompt 模板”或“skill 就是插件”的泛化描述上。

**主要代码锚点**

- `backend/packages/harness/deerflow/skills/*`
- `backend/app/gateway/routers/skills.py`
- `backend/packages/harness/deerflow/skills/installer.py`
- `backend/packages/harness/deerflow/tools/builtins/tool_search.py`
- `README.md`

**必须覆盖的内容**

- DeerFlow 中 skill 的定义与存储位置。
- 通过 Gateway 安装 skill 与本地使用 skill 的方式。
- runtime discovery 与 prompt inclusion 机制。
- skills、tools、tool groups、custom agents 之间的关系。
- README 中已提到的 skill archive 兼容性说明。

**重点修正方向**

- 如果旧文把 skills 默认讲成“代码插件系统”，需要纠正为 DeerFlow 当前真实的 skill 生命周期模型。
- 清楚区分“skill 元数据/安装流程”和“tool 实现生命周期”。

### 31. 构建自定义 Agent

**在 DeerFlow 中的核心定位**

说明 DeerFlow 的 custom agent 是如何建立在共享 runtime 之上的，而不是每建一个 agent 就重新造一套执行栈。

**主要代码锚点**

- `backend/packages/harness/deerflow/client.py`
- `backend/packages/harness/deerflow/agents/factory.py`
- `backend/docs/rfc-create-deerflow-agent.md`
- `README.md`
- 与 custom agent 存储与管理相关的 Gateway 路径与 auth/design 文档

**必须覆盖的内容**

- lead agent、custom agent persona/config、完整 runtime 构造之间的区别。
- features、middleware、tools、memory、sandbox 设置如何继承或覆盖。
- custom agent 的存储位置与 per-user 隔离。
- 通过 Gateway 与 embedded client 使用 custom agent 的不同入口。

**重点修正方向**

- 删除“自定义 agent 等于独立部署 / 独立服务”的误导。
- 清楚说明共享 runtime 与局部特化之间的边界。

### 32. 从零构建 Agent 系统

**在 DeerFlow 中的核心定位**

把 DeerFlow 当作一个真实工作样本，讲清一个生产级 agent 系统至少需要哪些部件；同时诚实地区分“可复用原则”和“DeerFlow 当前实现选择”。

**主要代码锚点**

- `README.md`
- `backend/docs/ARCHITECTURE.md`
- `backend/docs/API.md`
- `backend/docs/AUTH_DESIGN.md`
- agents、gateway、sandbox、memory、channels、skills 等代表性运行时模块

**必须覆盖的内容**

- 从 DeerFlow 抽象出来的最小生产级组件地图：runtime host、prompt/context assembly、tools、sandbox、memory、API、streaming、persistence、auth、channels、extensibility。
- DeerFlow 为什么把 runtime 嵌入 Gateway。
- 哪些是通用架构原则，哪些是 DeerFlow 当前取舍。
- 如何从简单单 agent runtime 逐步演进到 DeerFlow 这种 harness。

**重点修正方向**

- 不把 DeerFlow 讲成唯一正确架构。
- 明确标注哪些结论是原则，哪些只是当前实现决策。

### 40. 源码导航与阅读指南

**在 DeerFlow 中的核心定位**

这一章负责把前面所有章节的代码锚点收束成一套稳定的阅读入口，帮助读者按“从架构到执行，再到扩展与集成”的顺序进入仓库。

**主要代码锚点**

- `backend/docs/ARCHITECTURE.md`
- `backend/app/gateway/`
- `backend/packages/harness/deerflow/agents/`
- `backend/packages/harness/deerflow/runtime/`
- `backend/packages/harness/deerflow/sandbox/`
- `backend/packages/harness/deerflow/skills/`
- `backend/packages/harness/deerflow/subagents/`
- `backend/app/channels/`

**必须覆盖的内容**

- 推荐阅读顺序。
- 各目录在 DeerFlow 整体架构中的职责。
- 哪些文件是主入口，哪些是辅助实现，哪些是专题文档。
- 如何把本套学习章节与源码阅读联动起来。

**重点修正方向**

- 删除泛泛的“阅读大仓库的一般技巧”，改成 DeerFlow 专属导航图。

### 41. 常见问题与故障排除

**在 DeerFlow 中的核心定位**

这一章要成为前面各章的“落地补充”，基于 DeerFlow 当前真实部署与运行问题，总结最常见的误区、配置问题和诊断入口。

**主要代码锚点**

- `README.md`
- `backend/docs/CONFIGURATION.md`
- `backend/docs/STREAMING.md`
- `backend/docs/AUTH_DESIGN.md`
- `backend/app/gateway/`
- `backend/app/channels/`

**必须覆盖的内容**

- Gateway、sandbox、channels、skills、memory、streaming、auth 相关常见误区。
- 问题应该去哪个模块、哪个文档、哪个配置面排查。
- FAQ 与前面各章如何互相引用。

**重点修正方向**

- 不能再做泛化 FAQ；要围绕 DeerFlow 真实运行问题组织。

## 七、跨章节必须统一的核心事实

这些章节在涉及共同架构事实时，必须保持完全一致：

### 1. Runtime host

DeerFlow 默认的 Web/生产/开发主运行时是 Gateway-embedded runtime，由 nginx 将 `/api/langgraph/*` 重写到 Gateway 管理的兼容路由。

### 2. Sandbox boundary

Local sandbox 是路径作用域下的便捷模式，host bash 默认关闭；容器型 sandbox 才是更强隔离路径。

### 3. Memory boundary

长期记忆不是 thread checkpoint history，不是 summarization，也不是 event store。

### 4. Channels boundary

IM channels 是 shared runtime 的接入适配层，不是独立编排栈。

### 5. Custom agent boundary

Custom agent 是在共享 runtime 上通过 config、prompts、tools、skills、features 做特化，而不是默认独立成一套系统。

### 6. 执行引擎边界

执行引擎章节必须与 Gateway、memory、sandbox、subagents、channels 的运行链路描述一致，不能另起一套抽象世界观。

### 7. Skills 边界

第 11 章与第 30 章必须分工明确：前者讲 skills 系统如何工作，后者讲用户如何定义和构建自定义 skills。

### 8. 模型与工具边界

第 02 章必须聚焦“模型调用与工具系统如何成为 DeerFlow 的能力底座”，不能和第 10 章的执行引擎主线、第 11 章的 skills 机制、第 20 章的上下文塑形机制互相重复。

## 八、验收标准

只有当最终 HTML 改写满足以下全部检查项时，才算达成目标：

1. **DeerFlow-first 开场检查**
   每章都从 DeerFlow 的实现问题切入，而不是从泛化理论切入。

2. **代码锚点检查**
   每章都有明确仓库路径、模块名或实现入口。

3. **运行链路检查**
   每章至少解释一条真实执行链路或数据链路。

4. **边界检查**
   每章都写清当前限制、实现边界或非目标。

5. **跨章节一致性检查**
   Gateway、sandbox、memory、channels、custom agents 的重复事实不能互相冲突。

6. **读者理解检查**
   读者在看完每章后，应能回答“它在 DeerFlow 里哪里实现？”和“它在 DeerFlow 里怎么工作？”。

## 九、实施策略

这批工作量已经从“10 章局部修正”提升为“核心课程体系重构”，适合并行执行，但必须在统一设计约束下进行。

### 阶段 1：逐章审计与提纲重建

- 审计本次纳入范围的所有当前 HTML 文件。
- 标记其中不准确的通用教程段落、缺失的 DeerFlow 锚点和需要交叉引用的内容。
- 为每章生成符合统一骨架的新提纲。

### 阶段 2：并行重写

可以拆成 4 条并行工作线：

- Track A：`02`、`03`、`10`、`11`
  聚焦模型与工具底座、总览、执行引擎、skills 系统。

- Track B：`12`、`13`、`14`
  聚焦 runtime internals：sandbox、memory、subagents。

- Track C：`15`、`20`、`21`、`22`、`23`
  聚焦 runtime host、context shaping、model selection、多渠道集成与高级模式。

- Track D：`30`、`31`、`32`、`40`、`41`
  聚焦扩展机制、自定义 agent、从零构建、源码导航与 FAQ。

### 阶段 3：一致性总校

- 统一术语。
- 对齐共享事实与代码引用。
- 清理互相矛盾的图示、表述和运行时假设。

### 阶段 4：回到原始目标做终检

用最初用户目标做最后一道验证：

> “用户看完 `.learning/html` 之后，就能掌握 DeerFlow 的真实设计和具体实现。”

凡是“有助于泛化学习、但削弱这一目标”的内容，都应改写或删除。

## 十、风险与缓解

### 风险 1：又写回通用教程

**缓解：** 严格执行“真相来源优先级”与 DeerFlow-first 开场规则。

### 风险 2：改成代码堆砌，失去教学可读性

**缓解：** 使用统一章节骨架，强调运行路径、设计意图和边界，而不是只堆文件名。

### 风险 3：并行改写后术语和架构事实冲突

**缓解：** 保留独立的一致性总校阶段，并以“跨章节必须统一的核心事实”作为检查清单。

### 风险 4：旧图示在新语义下变成误导

**缓解：** 只保留能被当前仓库验证的图示；宁可图少，也不要概念正确但实现不对。

## 十一、最终交付物

基于本设计实施后，最终应交付：

- 本次纳入范围的全部目标 HTML 章节的重写版本。
- 必要的共享术语、交叉引用与导航细化。
- 一轮最终核验，确认这些章节已经从“泛化 Agent 课程”切换为“DeerFlow 真实设计与实现课程”，并且第 03、10、11、12-15、20-23、30-32、40、41 之间在架构口径上完全一致。
