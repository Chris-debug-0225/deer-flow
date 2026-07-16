# 第 06 章 Lead Agent 与中间件链 ★核心★

> 🎯 本章目标：进入 deer-flow 的心脏。我们将搞懂「一个孤立的模型，是怎么变成一个完整 Agent 的」——精读 `make_lead_agent()` 工厂，理解 **19 个中间件组成的洋葱模型**。这是整个课件最精华的一章，学懂它，你就真正理解了「Agent 是怎么被组装出来的」。

---

## 6.1 学习目标

1. ✅ 理解「模型」和「Agent」的区别，知道 Agent 还需要哪些部件
2. ✅ 精读 `make_lead_agent()` 工厂的全流程
3. ✅ 彻底理解「中间件（Middleware）」概念和「洋葱模型」
4. ✅ 认识 19 个中间件的职责和执行顺序
5. ✅ 精读 3 个代表性中间件的代码实现
6. ✅ 理解 `before_model` / `after_model` / `wrap_tool_call` 三大钩子

---

## 6.2 概念铺垫：从「模型」到「Agent」还差什么

第 05 章我们造出了一个能调用的模型对象：

```python
model = create_chat_model(name="gpt-4o")
# 现在可以：model.invoke("你好") → 返回一段文字
```

但这是一个**光秃秃的模型**，它还不是 Agent。回忆第 01 章的定义：

> Agent = LLM + 一套能动手的装备 + 自己决定怎么用这些装备

光有 `model` 还缺了三样东西：

| 缺什么 | 是什么 | 作用 |
|--------|--------|------|
| **工具（Tools）** | 一堆可调用的函数 | 让 Agent 能「动手」（搜索、读写文件…） |
| **系统提示词（System Prompt）** | 一段开场指令 | 告诉模型「你是谁、你能干嘛、怎么干」 |
| **中间件（Middlewares）** | 一组「关卡」 | 在 Agent 每次思考/行动前后做额外处理 |

把这三样和模型组装在一起，才是一个完整的 Agent。这个组装过程，就是 `make_lead_agent()` 干的事。

> 💡 **类比**：模型是一个「刚入职的天才员工」。工具是他的「工具箱」，提示词是「岗位说明书」，中间件是「公司的各种流程制度」（报销要审批、出门要打卡、犯错要记录）。把员工、工具箱、岗位说明、流程制度组合起来，才是一个「能干活的组织成员」。

---

## 6.3 LangChain 的 `create_agent()`：Agent 的基本形态

deer-flow 的 Agent 最终是用 LangChain 的 `create_agent()` 创建的。我们先看看它需要什么参数（来自 `lead_agent/agent.py`）：

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,                  # ① 模型（第 05 章造的）
    tools=final_tools,            # ② 工具列表（第 07 章讲）
    middleware=middlewares,       # ③ 中间件链（本章重点）
    system_prompt=prompt_text,    # ④ 系统提示词
    state_schema=ThreadState,     # ⑤ 状态结构（第 03 章讲过）
)
```

`create_agent()` 返回的 `agent` 是一个 LangGraph 编译好的**可运行图（Runnable Graph）**。当你调用 `agent.invoke({...})` 时，它就自动进入 ReAct 循环（思考 → 用工具 → 观察 → 再思考…）。

所以 `make_lead_agent()` 的核心任务，就是**准备好上面这 5 个参数**，然后丢给 `create_agent()`。我们重点看中间件是怎么准备的。

---

## 6.4 概念重点：什么是中间件（Middleware）

中间件是本章的核心概念，我们多花点笔墨讲透。

### 🧅 类比：洋葱模型

想象 Agent 的一次「思考-行动」循环是一根穿过洋葱的线：

```
请求进来 →
    ┌─────────────────────────────────────────────┐
    │ 中间件1（最外层）：记忆注入                  │
    │  ┌───────────────────────────────────────┐  │
    │  │ 中间件2：上下文摘要                    │  │
    │  │  ┌─────────────────────────────────┐  │  │
    │  │  │ 中间件3：工具过滤                │  │  │
    │  │  │  ┌───────────────────────────┐  │  │  │
    │  │  │  │  ★ 核心：调用 LLM ★       │  │  │  │
    │  │  │  │  （或执行工具）            │  │  │  │
    │  │  │  └───────────────────────────┘  │  │  │
    │  │  └─────────────────────────────────┘  │  │
    │  └───────────────────────────────────────┘  │
    │ 中间件1：收尾（记忆抽取入队）              │
    └─────────────────────────────────────────────┘
← 响应出去
```

- 请求**进来**时，从外到内依次经过每个中间件（**before** 阶段）
- 到达**核心**（调用 LLM 或执行工具）
- 响应**出去**时，从内到外再依次经过每个中间件（**after** 阶段）

每个中间件都可以在「before」或「after」阶段做点手脚：修改请求、修改响应、甚至直接中断（不往下传了）。

### 生活中的中间件

其实你早就在用「中间件」思想了：

| 场景 | 「中间件」 | before（进来时） | after（出去时） |
|------|----------|-----------------|----------------|
| 公司报销 | 财务审批 | 检查发票合不合规 | 记账 |
| 快递 | 安检 | 查有没有违禁品 | 贴标签 |
| Web 服务器 | 鉴权中间件 | 检查你登录没 | 记录访问日志 |

deer-flow 的中间件干的事类似——在 Agent 思考前后，做「检查、注入、记录、转换」等横切关注点（cross-cutting concerns）。

### 为什么不用一个大函数搞定？

你可能会想：为什么不把所有逻辑（记忆、摘要、工具过滤…）写在一个大函数里？

因为**关注点分离**。把每件事拆成独立的中间件：
- ✅ 每个**只管一件事**，代码清晰
- ✅ 可以**独立开关**（比如不开记忆，就不加 MemoryMiddleware）
- ✅ **顺序可控**（记忆要在摘要之后）
- ✅ **可复用、可替换**（不喜欢某个中间件，换一个）

这就是「洋葱模型」的威力——用「一层一层」的方式组合功能，而不是揉成一团。

---

## 6.5 中间件的三大钩子

LangChain 的中间件（`AgentMiddleware`）有三个主要「钩子」（hook），分别在循环的不同时机触发：

```
一次 Agent 循环（ReAct 的一圈）
│
├─ ① before_model       ← 调用 LLM 之前触发
│     （可以修改要发给 LLM 的消息、注入上下文）
│
├─    ★ 调用 LLM ★
│
├─ ② after_model        ← LLM 返回之后触发
│     （可以修改 LLM 的回复、记录日志、截断工具调用）
│
├─    ★ 执行工具 ★（如果 LLM 决定调工具）
│
└─ ③ wrap_tool_call     ← 包裹工具调用（工具执行前后都能介入）
      （可以拦截工具调用、审计、错误处理）
```

| 钩子 | 时机 | 典型用途 |
|------|------|---------|
| `before_model` | LLM 调用前 | 注入记忆、注入图片、上下文摘要触发 |
| `after_model` | LLM 返回后 | 生成标题、统计 token、截断过多工具调用、检测死循环 |
| `wrap_tool_call` | 工具执行时 | 拦截澄清请求、审计 bash 命令、工具错误处理 |

> 💡 不是每个中间件都实现三个钩子，大多数只实现其中一两个。

---

## 6.6 deer-flow 的 19 个中间件全景

deer-flow 的 Lead Agent 串了 **19 个中间件**（数量会随版本微调）。我们按执行顺序列出来，每个用一句话说明：

| # | 中间件 | 钩子 | 职责 | 必选? |
|---|--------|------|------|------|
| 1 | **ThreadDataMiddleware** | before | 为每个对话创建隔离的工作目录 | 是 |
| 2 | **UploadsMiddleware** | before | 把用户上传的文件注入对话上下文 | 是 |
| 3 | **SandboxMiddleware** | before | 获取沙箱环境，存到 state 里 | 是 |
| 4 | **DanglingToolCallMiddleware** | before | 修补「悬空」的工具调用（被打断的） | 是 |
| 5 | **LLMErrorHandlingMiddleware** | wrap | 把 LLM 调用失败转成友好的错误 | 是 |
| 6 | **GuardrailMiddleware** | wrap | 工具调用的授权检查（安全护栏） | 可选 |
| 7 | **SandboxAuditMiddleware** | wrap | 审计 bash/文件操作（安全日志） | 是 |
| 8 | **ToolErrorHandlingMiddleware** | wrap | 工具报错转成错误消息，不让 Agent 崩溃 | 是 |
| 9 | **SkillActivationMiddleware** | before | 检测 `/skill-name` 斜杠命令，激活技能 | 是 |
| 10 | **DynamicContextMiddleware** | before | 注入日期、记忆等动态上下文 | 是 |
| 11 | **SummarizationMiddleware** | before | 上下文太长时自动摘要（可选） | 可选 |
| 12 | **TodoMiddleware** | before/after | 计划模式下的任务清单管理 | 可选 |
| 13 | **TokenUsageMiddleware** | after | 统计 token 消耗 | 可选 |
| 14 | **TitleMiddleware** | after | 第一轮对话后自动生成标题 | 是 |
| 15 | **MemoryMiddleware** | after | 把对话入队，等会抽取记忆 | 可选 |
| 16 | **ViewImageMiddleware** | before | 给支持视觉的模型注入图片 base64 | 条件 |
| 17 | **DeferredToolFilterMiddleware** | before | 隐藏延迟加载的 MCP 工具 | 可选 |
| 18 | **SubagentLimitMiddleware** | after | 限制每轮最多 N 个子代理调用 | 可选 |
| 19 | **LoopDetectionMiddleware** | after | 检测并打断死循环 | 可选 |
| - | **ClarificationMiddleware** | wrap | ★必须最后★ 拦截澄清请求，中断执行 | 是 |

> ⚠️ **ClarificationMiddleware 必须是最后一个**。因为它会「中断执行」（让 Agent 停下来等用户回答），如果它后面还有中间件，那些就执行不到了。

### 执行顺序的意义

中间件的**顺序非常重要**。代码里有详细注释解释为什么这么排：

```python
# 文件：lead_agent/agent.py 里的注释（节选）

# ThreadDataMiddleware 必须在 SandboxMiddleware 之前 → 保证 thread_id 已就绪
# UploadsMiddleware 要在 ThreadDataMiddleware 之后 → 才能拿到 thread_id
# DanglingToolCallMiddleware 要在模型看到历史之前 → 修补悬空调用
# SummarizationMiddleware 要靠前 → 在其他处理前先压缩上下文
# MemoryMiddleware 要在 TitleMiddleware 之后 → 标题先生成
# ViewImageMiddleware 要在 ClarificationMiddleware 之前 → 注入图片再给模型
# ClarificationMiddleware 必须最后 → 它会中断执行
```

这种「顺序敏感的组合」是中间件架构的特点，也是灵活性所在——你可以精确控制「什么事在什么事之前/之后发生」。

---

## 6.7 代码精读：`make_lead_agent()` 工厂

现在我们看这个工厂函数怎么把一切组装起来。我贴出**简化但忠实于原逻辑**的核心流程（来自 `lead_agent/agent.py`）：

```python
def make_lead_agent(config: RunnableConfig):
    """LangGraph 的图工厂函数。"""
    return _make_lead_agent(config, app_config=get_app_config())


def _make_lead_agent(config: RunnableConfig, *, app_config: AppConfig):
    # 第 1 步：从运行时配置里读各种开关
    cfg = _get_runtime_config(config)
    thinking_enabled = cfg.get("thinking_enabled", True)        # 是否开思考
    requested_model_name = cfg.get("model_name")                # 用哪个模型
    is_plan_mode = cfg.get("is_plan_mode", False)               # 是否计划模式
    subagent_enabled = cfg.get("subagent_enabled", False)       # 是否开子代理
    agent_name = validate_agent_name(cfg.get("agent_name"))     # 自定义 Agent 名

    # 第 2 步：解析最终用哪个模型
    model_name = _resolve_model_name(requested_model_name, app_config=app_config)

    # 第 3 步：注入 tracing 回调到图的根节点（第 05 章提过）
    tracing_callbacks = build_tracing_callbacks()
    if tracing_callbacks:
        config["callbacks"] = [*config.get("callbacks", []), *tracing_callbacks]

    # 第 4 步：加载工具（第 07 章详解）
    from deerflow.tools import get_available_tools
    raw_tools = get_available_tools(
        model_name=model_name,
        subagent_enabled=subagent_enabled,
        app_config=app_config,
    )

    # 第 5 步：构建中间件链 ★核心★
    middlewares = build_middlewares(
        config,
        model_name=model_name,
        agent_name=agent_name,
        app_config=app_config,
    )

    # 第 6 步：生成系统提示词（注入技能、记忆、子代理说明等）
    system_prompt = apply_prompt_template(
        subagent_enabled=subagent_enabled,
        agent_name=agent_name,
        app_config=app_config,
    )

    # 第 7 步：组装成完整 Agent！
    return create_agent(
        model=create_chat_model(                 # ① 模型
            name=model_name,
            thinking_enabled=thinking_enabled,
            attach_tracing=False,                # ★图层面已挂，模型层不重复挂
        ),
        tools=final_tools,                       # ② 工具
        middleware=middlewares,                   # ③ 中间件链
        system_prompt=system_prompt,             # ④ 提示词
        state_schema=ThreadState,                # ⑤ 状态结构
    )
```

> 💡 注意第 7 步的 `attach_tracing=False`——这正是第 05 章结尾提到的细节：tracing 回调已经在第 3 步挂在了「图层面」，模型层面就不重复挂了，避免一次调用产生重复的追踪 span。

### 整体流程图

```
make_lead_agent(config)
       │
       ├─ 读运行时开关（思考/计划/子代理/模型）
       ├─ 解析模型名
       ├─ 挂 tracing 回调到图根
       ├─ get_available_tools() → 工具列表
       ├─ build_middlewares() → ★中间件链★
       ├─ apply_prompt_template() → 系统提示词
       │
       └─ create_agent(model, tools, middleware, prompt, state)
              │
              └─ 返回一个可运行的 LangGraph Agent
```

---

## 6.8 代码精读：`build_middlewares()` 怎么组装链

这是「按条件组装中间件」的核心函数。它的逻辑是：**先加必选的，再按开关加可选的，最后加 ClarificationMiddleware**。简化版：

```python
# 文件：lead_agent/agent.py（简化）

def build_middlewares(config, model_name, agent_name=None, *, app_config=None):
    """根据运行时配置，组装中间件链。"""
    middlewares = []

    # ── 第 1 段：必选的基础中间件（来自 build_lead_runtime_middlewares）──
    # ThreadData → Uploads → Sandbox → DanglingToolCall
    # → LLMErrorHandling → Guardrail(可选) → SandboxAudit → ToolErrorHandling
    middlewares = build_lead_runtime_middlewares(app_config=app_config)

    # ── 第 2 段：动态上下文（注入日期、记忆）──
    middlewares.append(DynamicContextMiddleware(agent_name=agent_name))

    # ── 第 3 段：技能激活（检测 /skill-name 命令）──
    middlewares.append(SkillActivationMiddleware(...))

    # ── 第 4 段：摘要中间件（如果配置开启）──
    if app_config.summarization.enabled:
        middlewares.append(_create_summarization_middleware())

    # ── 第 5 段：计划模式（TodoList）──
    if is_plan_mode:
        middlewares.append(TodoMiddleware(...))

    # ── 第 6 段：Token 统计（如果开启）──
    if app_config.token_usage.enabled:
        middlewares.append(TokenUsageMiddleware())

    # ── 第 7 段：标题生成（每次都加）──
    middlewares.append(TitleMiddleware(...))

    # ── 第 8 段：记忆（每次都加，内部判断开关）──
    middlewares.append(MemoryMiddleware(agent_name=agent_name, ...))

    # ── 第 9 段：视觉支持（仅当模型支持看图）──
    model_config = app_config.get_model_config(model_name)
    if model_config and model_config.supports_vision:
        middlewares.append(ViewImageMiddleware())   # ★条件加载★

    # ── 第 10 段：延迟工具过滤（如果开了 tool_search）──
    if deferred_setup and deferred_setup.deferred_names:
        middlewares.append(DeferredToolFilterMiddleware(...))

    # ── 第 11 段：子代理并发限制（如果开了子代理）──
    if subagent_enabled:
        middlewares.append(SubagentLimitMiddleware(max_concurrent=3))

    # ── 第 12 段：死循环检测（如果开启）──
    if app_config.loop_detection.enabled:
        middlewares.append(LoopDetectionMiddleware(...))

    # ── 第 13 段：★澄清中间件必须最后加★ ──
    middlewares.append(ClarificationMiddleware())

    return middlewares
```

### 关键设计：条件加载

注意很多中间件是**条件加载**的：
- `ViewImageMiddleware` 只在模型支持视觉时加
- `SubagentLimitMiddleware` 只在开了子代理时加
- `TodoMiddleware` 只在计划模式时加

这是「**按需付费**」思想——不用的中间件根本不进链，既省资源又避免干扰。这也是为什么 deer-flow 能适配从「轻量对话」到「重型多步任务」各种场景的原因。

---

## 6.9 精读 3 个代表性中间件

光看列表不够，我们挑 3 个代表性中间件，完整读一遍代码，体会「钩子」怎么用。

### 📌 代表 1：`ClarificationMiddleware`（拦截 + 中断）

这个中间件演示了 **`wrap_tool_call` 钩子 + 中断执行**。它的作用：当 Agent 想问用户澄清问题时，**拦截这个工具调用，把问题展示给用户，然后中断 Agent 执行**（等用户回答）。

```python
# 文件：middlewares/clarification_middleware.py（简化）

class ClarificationMiddleware(AgentMiddleware):
    """拦截 ask_clarification 工具调用，中断执行并展示问题给用户。"""

    def wrap_tool_call(self, request, handler):
        """同步版：包裹工具调用。"""
        # request 里有这次要调用的工具信息
        if request.tool_call.get("name") != "ask_clarification":
            # 不是澄清调用 → 正常执行，不干预
            return handler(request)

        # 是澄清调用 → 拦截！
        return self._handle_clarification(request)

    async def awrap_tool_call(self, request, handler):
        """异步版（逻辑一样）。"""
        if request.tool_call.get("name") != "ask_clarification":
            return await handler(request)
        return self._handle_clarification(request)

    def _handle_clarification(self, request):
        """处理澄清请求：格式化问题，然后中断。"""
        args = request.tool_call.get("args", {})
        question = args.get("question", "")

        # 把问题格式化成用户友好的文本（加图标、选项等）
        formatted = self._format_clarification_message(args)

        # 构造一个 ToolMessage（会被加入消息历史）
        tool_message = ToolMessage(
            content=formatted,
            tool_call_id=request.tool_call.get("id"),
            name="ask_clarification",
        )

        # ★关键：返回 Command(goto=END) 中断执行！★
        # goto=END 表示「跳到图的终点」，Agent 循环就此停止
        # 等用户在前端回答后，才会发起新的一轮
        return Command(
            update={"messages": [tool_message]},
            goto=END,         # ← 中断！不再继续执行后续工具或 LLM 调用
        )
```

**核心技巧**：`Command(goto=END)` 是 LangGraph 的「控制流跳转」机制——它能让中间件直接改变 Agent 的执行流程（在这里是「直接跳到结束」）。这就是为什么 ClarificationMiddleware 必须在最后：它一旦触发，后面什么都不执行了。

> 💡 `handler(request)` 这个「handler」就是「原本要执行的工具」。中间件调用 `handler(request)` 表示「放行，正常执行」；不调用而是返回自己的结果，表示「拦截」。

### 📌 代表 2：`MemoryMiddleware`（after 钩子 + 异步触发）

这个中间件演示了 **`after_agent` 钩子**。它的作用：**Agent 执行完后，把这次对话塞进一个队列，等会儿异步抽取记忆**。

```python
# 文件：middlewares/memory_middleware.py（简化）

class MemoryMiddleware(AgentMiddleware):
    """Agent 执行后，把对话入队，等待异步记忆抽取。"""

    def __init__(self, agent_name=None, *, memory_config=None):
        self._agent_name = agent_name
        self._memory_config = memory_config

    def after_agent(self, state, runtime):
        """★Agent 执行完成后触发★（注意是 after，不是 before）。"""
        config = self._memory_config or get_memory_config()
        if not config.enabled:
            return None   # 记忆没开，跳过

        # 拿到这次对话的消息
        messages = state.get("messages", [])
        if not messages:
            return None

        # 过滤：只保留「用户输入」和「AI 最终回复」，丢掉工具调用细节
        filtered = filter_messages_for_memory(messages)

        # ★关键：不在这里直接抽取（太慢），而是塞进队列★
        # 队列会「去抖」（debounce），积攒一会儿后批量处理
        queue = get_memory_queue()
        queue.enqueue(
            thread_id=thread_id,
            messages=filtered,
            user_id=get_effective_user_id(),   # 按用户隔离
        )

        return None   # 这个中间件不改 state，只做「副作用」（入队）
```

**核心设计**：记忆抽取是个**耗时操作**（要调 LLM），如果放在 `after_agent` 同步做，用户要等很久。所以它用了「**入队 + 去抖 + 异步处理**」的模式——先快速入队，后台慢慢抽。这种「**把耗时操作异步化**」是 Agent 系统的性能关键，第 10 章讲记忆时会完整剖析。

### 📌 代表 3：`ViewImageMiddleware`（before 钩子 + 条件加载）

这个中间件演示了 **`before_model` 钩子 + 条件加载**。作用：**如果模型支持视觉，且对话里有图片，就把图片转成 base64 注入进去**。

```python
# 简化示意：middlewares/view_image_middleware.py

class ViewImageMiddleware(AgentMiddleware):
    """调用 LLM 前，把要看的图片转成 base64 注入。"""

    def before_model(self, state, runtime):
        """★调用 LLM 之前触发★。"""
        viewed_images = state.get("viewed_images", {})
        if not viewed_images:
            return None   # 没有图片要看，跳过

        messages = state.get("messages", [])

        # 找到最近一条 AI 消息里的 view_image 工具调用
        # 把对应的图片 base64 数据注入到消息里
        # 这样 LLM 调用时就能"看到"图片了
        for img_path, img_data in viewed_images.items():
            # img_data = {"base64": "...", "mime_type": "image/png"}
            # 构造一个包含图片的多模态消息
            ...

        return {"messages": updated_messages}   # 返回修改后的消息
```

**为什么是条件加载**：因为纯文本模型（如 DeepSeek-V3）看不懂图片，给它注入 base64 反而会报错。所以 `build_middlewares()` 里判断：

```python
if model_config and model_config.supports_vision:
    middlewares.append(ViewImageMiddleware())   # 只有视觉模型才加
```

这就是「**能力驱动的中间件加载**」——根据模型能力决定加不加某个中间件，非常精准。

---

## 6.10 系统提示词：Agent 的「岗位说明书」

除了中间件，`make_lead_agent()` 还有一个重要产物：**系统提示词（system prompt）**。它由 `apply_prompt_template()` 生成，是一段告诉模型「你是谁、你能干嘛、怎么干」的长文本。

提示词不是写死的，而是**动态拼装**的，包含：

| 组成部分 | 内容 | 来源 |
|---------|------|------|
| 基础人设 | 「你是 deer-flow，一个能干活的 AI 助手…」 | 写死的模板 |
| 技能清单 | 列出所有启用的技能及路径 | 从 skills 目录加载 |
| 记忆上下文 | 用户的偏好、事实（Top 15） | 从 memory.json 注入 |
| 子代理说明 | 可用的子代理类型、并发限制 | 动态生成 |
| 工具延迟提示 | 可搜索的 MCP 工具列表 | 动态生成 |
| 工作目录指引 | 「文件放在 /mnt/user-data/workspace/…」 | 沙箱路径约定 |

```python
# 简化示意：apply_prompt_template 的产物
system_prompt = f"""
你是 deer-flow，一个强大的 AI 助手，能够使用工具完成各种任务。

## 可用技能
{技能清单}

## 关于用户的记忆
{记忆上下文}

## 工作目录
你的文件操作应使用以下路径：
- 工作区：/mnt/user-data/workspace/
- 输出：/mnt/user-data/outputs/

## 子代理（如果开启）
{子代理说明}
...
"""
```

> 💡 **关键认知**：技能和记忆**不是写死在代码里的，而是运行时动态注入到提示词里**。这就是为什么你在界面开关一个技能，下次对话就生效——因为提示词重新生成了。这个机制第 11 章技能系统会详讲。

---

## 6.11 把一切串起来：一次完整循环

现在我们用一个具体例子，把模型、工具、中间件、提示词如何协作讲清楚。用户问「帮我搜索一下 LangGraph 是什么，把结果写到文件里」：

```
① 用户消息进入 Agent
   state.messages = [用户消息]

② 中间件链 before 阶段（从外到内）：
   - ThreadDataMiddleware：确保工作目录存在
   - SandboxMiddleware：拿到沙箱
   - DynamicContextMiddleware：注入当前日期
   - MemoryMiddleware：（after 阶段才工作）
   - ...（其他 before 钩子）

③ 调用 LLM（带上 system_prompt + messages + 工具列表）
   LLM 思考后决定：调用 web_search 工具
   返回：AIMessage(tool_calls=[{name:"web_search", args:{query:"LangGraph"}}])

④ 中间件链 after_model 阶段：
   - TokenUsageMiddleware：记录这轮 token
   - SubagentLimitMiddleware：（本轮没调 task，跳过）

⑤ 执行工具（web_search）
   中间件链 wrap_tool_call 阶段：
   - SandboxAuditMiddleware：（不是沙箱工具，跳过）
   - ToolErrorHandlingMiddleware：包裹执行，出错也不崩
   → 执行 web_search("LangGraph") → 返回搜索结果

⑥ 工具结果回到 state.messages，进入下一轮循环

⑦ 第二轮：LLM 看到搜索结果，决定调用 write_file
   → 中间件放行 → 写入文件

⑧ 第三轮：LLM 不再调工具，生成最终文字回复
   "我已经搜索了 LangGraph 并把结果写到 result.md 了"

⑨ 中间件链 after_agent 阶段（收尾）：
   - TitleMiddleware：生成对话标题
   - MemoryMiddleware：把对话入队，等会抽记忆

⑩ 返回给用户（流式推送全程发生）
```

看到没？中间件在**每个关键节点**都参与工作——before 准备、after 记录、wrap 保护。而核心的 ReAct 循环（思考-行动-观察）由 LangGraph 的 `create_agent` 编排。**deER-flow 的工程价值，就体现在这套精心设计的中间件链上**。

---

## 6.12 本章小结

- ✅ **Agent = 模型 + 工具 + 系统提示词 + 中间件链**，`make_lead_agent()` 就是组装它们的工厂
- ✅ **中间件**采用「洋葱模型」，在 Agent 循环的 before/after/wrap 三个时机介入，实现「关注点分离」
- ✅ 中间件有**三大钩子**：`before_model`（LLM 前）、`after_model`（LLM 后）、`wrap_tool_call`（工具执行时）
- ✅ deer-flow 串了 **19 个中间件**，顺序敏感，按需加载（视觉模型才加 ViewImage，计划模式才加 Todo…）
- ✅ **ClarificationMiddleware 必须最后**，因为它会用 `Command(goto=END)` 中断执行
- ✅ 系统提示词是**动态拼装**的，技能和记忆在运行时注入
- ✅ 这套中间件架构是 deer-flow 工程设计的精华——**可插拔、可组合、顺序可控**

---

### 📋 概念检查点

1. 一个光秃秃的模型，要变成 Agent 还需要哪三样东西？
2. 中间件的三大钩子分别在什么时机触发？
3. 为什么 ClarificationMiddleware 必须放在中间件链的最后？
4. ViewImageMiddleware 为什么是「条件加载」的？
5. MemoryMiddleware 为什么把对话「入队」而不是直接抽取？

---

## ➡️ 下一章预告

**第 07 章：工具系统** —— 上一章我们说 Agent = 模型 + **工具** + 提示词 + 中间件。现在你知道模型和中间件是怎么回事了，下一章我们攻克「工具」——Agent 的「手」。我们会看 `get_available_tools()` 是怎么把配置里的、内置的、MCP 的、ACP 的工具**统一组装**成一个工具列表的，并动手写一个自己的工具 🔧
