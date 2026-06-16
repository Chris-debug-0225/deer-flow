# DeerFlow Lead Agent 调用链图

本文档包含 Lead Agent 的完整调用链 Mermaid 流程图，展示从请求入口到最终响应的完整调用关系。

## 1. Lead Agent 构建图

> **重要修正**：代码中**不存在** `LeadAgentFactory` 工厂类。Lead Agent 由模块级函数 `make_lead_agent(config)`（`agent.py:402`）构建，内部调用 `build_middlewares(...)`（`agent.py:270`）装配中间件链，最终交给 LangChain `create_react_agent` / `create_agent` 编译为可执行图。

```mermaid
graph TB
    subgraph "入口函数"
        Entry[make_lead_agent&#40;config&#41;<br/>LangGraph 图工厂入口] --> ParseCfg[解析 RunnableConfig]
    end
    
    subgraph "配置解析"
        ParseCfg --> AppCfg[get_app_config]
        AppCfg --> ModelCfg[模型配置]
        AppCfg --> SkillsCfg[可用技能集合]
        ParseCfg --> RuntimeCfg[运行时配置<br/>is_plan_mode / subagent_enabled]
    end
    
    subgraph "中间件装配"
        RuntimeCfg --> BuildChain[build_middlewares<br/>两阶段条件构建]
        ModelCfg --> BuildChain
        BuildChain --> Runtime[build_lead_runtime_middlewares<br/>阶段1: 固定基础链]
        Runtime --> Append[阶段2: 条件性追加]
        SkillsCfg --> Append
    end
    
    subgraph "Agent 编译"
        Append --> MakeTools[装配工具<br/>内置/MCP/task]
        MakeTools --> CreateAgent[create_agent<br/>LangChain]
        CreateAgent --> Compile[编译为可执行图]
        Compile --> Agent[Lead Agent 实例]
    end
    
    style Entry fill:#e1f5ff
    style Agent fill:#e1ffe1
    style BuildChain fill:#fff4e1
    style Runtime fill:#f0e1ff
```

## 2. 请求处理调用链图

展示单个请求从 API 到响应的完整调用链。

```mermaid
graph TB
    subgraph "API 层"
        API[API Endpoint<br/>/api/runs] --> Controller[RunsController]
        Controller --> Validate[验证请求]
        Validate --> CreateRun[创建 Run 对象]
        CreateRun --> Stream[启动流式器]
    end
    
    subgraph "Agent 运行时"
        Stream --> Invoke[Agent.invoke<br/>异步]
        Invoke --> Execute[执行图节点]
        Execute --> State[获取 ThreadState]
    end
    
    subgraph "中间件链执行"
        State --> BeforeMiddleware[before_model 中间件链]
        
        BeforeMiddleware --> M1[ToolOutputBudget<br/>before_model]
        M1 --> M2[ThreadDataMiddleware<br/>before_model]
        M2 --> M3[UploadsMiddleware<br/>before_model]
        M3 --> M4[SandboxMiddleware<br/>before_model]
        M4 --> M5[DanglingToolCall<br/>before_model]
        M5 --> M6[DynamicContext<br/>before_model]
        M6 --> M7[SkillActivation<br/>before_model]
        M7 --> M8[Clarification<br/>总在最后]
        
        M8 --> CallAgent[调用 LLM 节点]
    end
    
    subgraph "LLM 执行"
        CallAgent --> BuildPrompt[构建提示词]
        BuildPrompt --> AddContext[添加上下文]
        AddContext --> LLMAPI[LLM API 调用]
        LLMAPI --> Response[获取响应]
        Response --> Parse[解析响应]
    end
    
    subgraph "工具执行"
        Parse --> ToolCheck{工具调用？}
        ToolCheck -->|是 | ToolExec[执行工具]
        ToolCheck -->|否 | Format[格式化输出]
        
        ToolExec --> ToolResult[工具结果]
        ToolResult --> UpdateState[更新状态]
        UpdateState --> CallAgent
    end
    
    subgraph "After 中间件"
        Format --> AfterMiddleware[after_model 中间件链 逆序]
        
        AfterMiddleware --> M9[Clarification<br/>after_model 先触发]
        M9 --> M10[LoopDetection<br/>after_model]
        M10 --> M11[SubagentLimit<br/>after_model]
        M11 --> M12[Memory<br/>after_model]
        M12 --> M13[Title<br/>after_model]
        M13 --> M14[ToolErrorHandling<br/>after_model 后触发]
    end
    
    subgraph "完成"
        M14 --> Yield[Yield 完成]
        Yield --> FinalState[返回最终状态]
        FinalState --> Persist[持久化]
        Persist --> SSE[SSE 完成事件]
    end
    
    style API fill:#e1f5ff
    style CallAgent fill:#fff4e1
    style ToolExec fill:#f0e1ff
    style Persist fill:#e1ffe1
    style SSE fill:#e1f5ff
```

## 3. 中间件链调用顺序图

> **修正说明**：实际为两阶段条件构建，最多 22 个中间件。`before_model` 按注册顺序触发，`after_model` 按注册逆序触发。下图展示典型完整链的钩子触发顺序（省略部分条件性中间件）。

```mermaid
sequenceDiagram
    participant Caller as 调用者
    participant Chain as 中间件链
    participant M1 as ToolOutputBudget
    participant M2 as ThreadData
    participant M3 as Sandbox
    participant M4 as DanglingToolCall
    participant M5 as LLMErrorHandling
    participant M6 as ToolErrorHandling
    participant M7 as DynamicContext
    participant M8 as SkillActivation
    participant M9 as Summarization
    participant M10 as Title
    participant M11 as Memory
    participant M12 as Clarification
    participant Agent as LLM 节点
    
    Note over Caller,Agent: before_model 阶段（正序触发）
    Caller->>Chain: 进入链
    Chain->>M1: before_model
    M1-->>Chain: 返回状态
    Chain->>M2: before_model
    M2-->>Chain: 返回状态
    Chain->>M3: before_model
    M3-->>Chain: 返回状态
    Chain->>M4: before_model
    M4-->>Chain: 返回状态
    Chain->>M5: before_model
    M5-->>Chain: 返回状态
    Chain->>M6: before_model
    M6-->>Chain: 返回状态
    Chain->>M7: before_model
    M7-->>Chain: 注入日期/记忆
    Chain->>M8: before_model
    M8-->>Chain: 激活技能
    Chain->>M9: before_model
    M9-->>Chain: 准备摘要
    Chain->>M10: before_model
    M10-->>Chain: 返回状态
    Chain->>M11: before_model
    M11-->>Chain: 返回状态
    Chain->>M12: before_model
    M12-->>Chain: 返回状态
    
    Chain->>Agent: 调用 LLM
    Agent-->>Chain: 返回响应
    
    Note over Caller,Agent: after_model 阶段（逆序触发）
    Chain->>M12: after_model
    M12-->>Chain: 处理澄清
    Chain->>M11: after_model
    M11-->>Chain: 保存记忆
    Chain->>M10: after_model
    M10-->>Chain: 生成标题
    Chain->>M9: after_model
    M9-->>Chain: 返回状态
    Chain->>M8: after_model
    M8-->>Chain: 返回状态
    Chain->>M7: after_model
    M7-->>Chain: 返回状态
    Chain->>M6: after_model
    M6-->>Chain: 处理错误
    Chain->>M5: after_model
    M5-->>Chain: 返回状态
    Chain->>M4: after_model
    M4-->>Chain: 返回状态
    Chain->>M3: after_model
    M3-->>Chain: 返回状态
    Chain->>M2: after_model
    M2-->>Chain: 返回状态
    Chain->>M1: after_model
    M1-->>Chain: 返回状态
    
    Chain-->>Caller: 返回最终状态
```

## 4. 条件中间件启用图

> **修正说明**：旧版"有工具？/有沙盒？/需要澄清？"等判断多数是臆造的。下图依据 `_build_runtime_middlewares()`（`tool_error_handling_middleware.py:129`）与 `build_middlewares()`（`agent.py:270-377`）的真实代码编写。两点关键修正：① `GuardrailMiddleware` 注册在**基础链内部**（`LLMErrorHandling` 与 `SandboxAudit` 之间），不是基础链之后；② `ClarificationMiddleware` **永远最后注册**（无任何条件），并非旧版画的"需要澄清才启用"。
>
> 图例：**实心方块 = 总是注册**；**菱形 = 条件判断**；条件命中才会插入对应中间件。

```mermaid
graph TD
    Start([开始装配中间件链]) --> Phase1

    subgraph Phase1["阶段 1 · 基础运行时链 &#40;build_lead_runtime_middlewares&#41;"]
        direction TB
        B1[ToolOutputBudget] --> B2[ThreadData]
        B2 --> B3[Uploads<br/>仅 Lead Agent]
        B3 --> B4[Sandbox]
        B4 --> B5[DanglingToolCall]
        B5 --> B6[LLMErrorHandling]
        B6 --> GQ{guardrails.enabled<br/>且配置 provider?}
        GQ -->|是| BG[Guardrail]
        GQ -->|否| B7
        BG --> B7[SandboxAudit]
        B7 --> B8[ToolErrorHandling]
    end

    B8 --> P2A[DynamicContext<br/>注入日期/记忆]
    P2A --> P2B[SkillActivation]

    subgraph Phase2["阶段 2 · 条件追加 &#40;build_middlewares&#41;"]
        direction TB
        P2B --> C1{summarization<br/>.enabled?}
        C1 -->|是| A1[Summarization]
        C1 -->|否| C2
        A1 --> C2{is_plan_mode?}
        C2 -->|是| A2[Todo]
        C2 -->|否| C3
        A2 --> C3{token_usage<br/>.enabled?}
        C3 -->|是| A3[TokenUsage]
        C3 -->|否| FIX1
        A3 --> FIX1[Title 总是注册]
        FIX1 --> FIX2[Memory 总是注册]
        FIX2 --> C4{model<br/>.supports_vision?}
        C4 -->|是| A4[ViewImage]
        C4 -->|否| C5
        A4 --> C5{deferred_setup<br/>有 deferred 工具?}
        C5 -->|是| A5[DeferredToolFilter]
        C5 -->|否| C6
        A5 --> C6{subagent_enabled?}
        C6 -->|是| A6[SubagentLimit<br/>max=3]
        C6 -->|否| C7
        A6 --> C7{loop_detection<br/>.enabled?}
        C7 -->|是| A7[LoopDetection]
        C7 -->|否| CUS
        A7 --> CUS[custom_middlewares<br/>注入点]
        CUS --> C8{safety_finish_reason<br/>.enabled?}
        C8 -->|是| A8[SafetyFinishReason]
        C8 -->|否| CLA
        A8 --> CLA[Clarification<br/>★ 永远最后]
    end

    CLA --> End([返回完整中间件链<br/>最多 22 个])

    style Start fill:#1f6feb,stroke:#58a6ff,color:#fff
    style End fill:#238636,stroke:#3fb950,color:#fff
    style BG fill:#3c1518,stroke:#f85149,color:#fff
    style FIX1 fill:#1a3a1a,stroke:#3fb950,color:#e6edf3
    style FIX2 fill:#1a3a1a,stroke:#3fb950,color:#e6edf3
    style CLA fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style P2A fill:#1a2a4a,stroke:#58a6ff,color:#e6edf3
    style P2B fill:#1a2a4a,stroke:#58a6ff,color:#e6edf3
```

**真实启用条件速查表**：

| 中间件 | 启用条件 | 代码位置 |
|---|---|---|
| ThreadData / Sandbox / Title / Memory | 总是注册 | agent.py |
| Summarization | `summarization.enabled` | agent.py:316 |
| Todo | `is_plan_mode == True` | agent.py:322 |
| TokenUsage | `token_usage.enabled` | agent.py:328 |
| ViewImage | `model_config.supports_vision` | agent.py:340 |
| SubagentLimit | `subagent_enabled`，max 默认 3 | agent.py:352 |
| LoopDetection | `loop_detection.enabled` | agent.py:359 |
| Guardrail | `guardrails.enabled` 且配置 `provider`（注册在基础链内部） | tool_error_handling_middleware.py:162 |
| SafetyFinishReason | `safety_finish_reason.enabled` | agent.py:372 |
| Clarification | **总是注册，必为最后** | agent.py:376 |

## 5. LLM 节点调用图

> **修正说明**：旧版臆造了"提取消息→构建历史→选择模型→温度/MaxTokens/Top P"等步骤。实际上 Lead Agent 由 LangChain `create_agent` 编译为 **ReAct 图**，并**没有**自定义 LLM 节点。模型节点的行为由中间件钩子决定：`before_model` 钩子按注册顺序修改 `ModelRequest`（注入上下文），`wrap_model_call` 包裹真正的模型调用（重试/降级），`after_model` 钩子按**逆序**处理响应。下图展示这一真实结构。

```mermaid
graph TB
    State([ThreadState · messages 累积历史]) --> BM

    subgraph BM["before_model 钩子 · 正序修改 ModelRequest"]
        direction TB
        H1[DynamicContext<br/>注入 system-reminder<br/>当前日期 + 记忆] --> H2[SkillActivation<br/>/skill 命令注入 SKILL.md]
        H2 --> H3[Summarization<br/>超长则压缩历史]
        H3 --> H4[Todo<br/>plan 模式注入待办]
        H4 --> H5[其余 before_model 钩子]
    end

    BM --> WRAP

    subgraph WRAP["wrap_model_call · 包裹真正的模型调用"]
        direction TB
        W1[LLMErrorHandling<br/>熔断检查 + 重试包裹] --> W2[model.bind_tools<br/>静态 system_prompt + 绑定工具]
        W2 --> W3[Provider 流式 API<br/>create_chat_model 构建]
    end

    WRAP --> RESP[AIMessage<br/>content + tool_calls?]
    RESP --> AM

    subgraph AM["after_model 钩子 · 逆序处理响应"]
        direction TB
        R1[Clarification<br/>拦截澄清请求] --> R2[Memory<br/>排队记忆更新]
        R2 --> R3[Title<br/>首轮生成标题]
        R3 --> R4[Loop/Subagent 计数等]
    end

    AM --> ROUTE{AIMessage<br/>含 tool_calls?}
    ROUTE -->|否| Done([结束 · 返回最终 AIMessage])
    ROUTE -->|是 · 工具结果回灌后回到本图顶部| ToolNode([→ ToolNode 执行工具<br/>见第 6 图])

    style State fill:#1f6feb,stroke:#58a6ff,color:#fff
    style Done fill:#238636,stroke:#3fb950,color:#fff
    style ToolNode fill:#3d2c5a,stroke:#bc8cff,color:#fff
    style RESP fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style W3 fill:#1a2a4a,stroke:#58a6ff,color:#e6edf3
```

## 6. 工具调用处理图

> **修正说明**：旧版"验证参数→获取工具→再次调用 LLM→继续？"是泛化描述。实际工具执行由 LangChain `ToolNode` 完成：模型产出 `tool_calls` 后进入 `ToolNode`，按工具名从注册表分发；`ToolErrorHandlingMiddleware.wrap_tool_call` 包裹每次调用，捕获异常并把结果统一封装为 `ToolMessage` 回灌历史，再回到模型节点形成 ReAct 循环，直到某次响应不含 `tool_calls` 为止。

```mermaid
graph TB
    Model([模型节点输出 AIMessage]) --> HasCalls{含 tool_calls?}
    HasCalls -->|否| Done([结束 · 返回最终 AIMessage])
    HasCalls -->|是| ToolNode

    subgraph ToolNode["ToolNode · 按注册表分发并行执行"]
        direction TB
        Dispatch[按 tool_call.name<br/>查工具注册表] --> Wrap

        subgraph Wrap["wrap_tool_call 包裹 · 逐个工具"]
            direction TB
            Try[执行工具 handler] --> Kind{工具类别}
            Kind -->|内置工具| Builtin[bash · ls · read_file<br/>write_file · str_replace<br/>glob · grep · web_search ...]
            Kind -->|MCP 工具| MCP[MCP server 远程调用]
            Kind -->|task 子代理| Sub[task_tool<br/>见第 7 图]
        end
    end

    Builtin --> Outcome
    MCP --> Outcome
    Sub --> Outcome
    Outcome{执行结果}
    Outcome -->|成功| OK[ToolMessage<br/>task 工具加盖 subagent_status]
    Outcome -->|抛异常| Err["ToolMessage status=error<br/>Error: Tool '…' failed …"]
    Outcome -->|GraphBubbleUp| Bubble[中断/暂停信号<br/>原样上抛, 不拦截]

    OK --> Append[追加到 messages]
    Err --> Append
    Append --> Loop([回到模型节点])
    Loop -.下一轮 ReAct.-> Model

    style Model fill:#1f6feb,stroke:#58a6ff,color:#fff
    style Done fill:#238636,stroke:#3fb950,color:#fff
    style Sub fill:#3d2c5a,stroke:#bc8cff,color:#fff
    style Err fill:#3c1518,stroke:#f85149,color:#fff
    style Bubble fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style OK fill:#1a3a1a,stroke:#3fb950,color:#e6edf3
```

## 7. 子代理工具调用图

展示子代理工具 `task_tool` 的完整调用链。

```mermaid
graph TB
    subgraph "工具触发"
        LLM[LLM 决定] --> CallTaskTool[调用 task 工具<br/>tool 名为 task]
        CallTaskTool --> ValidateTask[验证参数与 subagent_type]
        ValidateTask --> CreateTaskObj[创建任务对象]
    end
    
    subgraph "任务创建"
        CreateTaskObj --> AssignTaskID[分配任务 ID]
        AssignTaskID --> InitSubagent[初始化子代理]
        InitSubagent --> CopyConfig[复制配置]
        CopyConfig --> SetParent[设置父线程]
    end
    
    subgraph "异步执行"
        SetParent --> StartExec[启动异步执行]
        StartExec --> IsolatedLoop[独立事件循环]
        IsolatedLoop --> SubagentChain[子代理中间件链]
        SubagentChain --> SubagentLLM[子代理 LLM]
    end
    
    subgraph "状态轮询"
        StartExec --> PollLoop[每 5 秒轮询一次]
        PollLoop --> CheckStatus{检查状态}
        CheckStatus -->|PENDING | Wait[继续等待]
        CheckStatus -->|RUNNING | UpdateStatus[更新状态]
        CheckStatus -->|COMPLETED | GetResult[获取结果]
        CheckStatus -->|FAILED | HandleError[处理错误]
        CheckStatus -->|TIMED_OUT | HandleTimeout[处理超时]
        CheckStatus -->|CANCELLED | HandleCancel[处理取消]
    end
    
    subgraph "结果处理"
        GetResult --> FormatSubagentResult[格式化结果]
        FormatSubagentResult --> ReturnResult[返回结果]
        
        HandleError --> ErrorHandler[错误处理]
        ErrorHandler --> ReturnResult
        
        HandleTimeout --> TimeoutMsg[超时消息]
        TimeoutMsg --> ReturnResult
        
        HandleCancel --> CancelMsg[取消消息]
        CancelMsg --> ReturnResult
    end
    
    subgraph "清理"
        ReturnResult --> DelayCleanup[延迟清理]
        DelayCleanup --> RemoveTask[移除任务]
        RemoveTask --> Done[完成]
    end
    
    style LLM fill:#e1f5ff
    style Done fill:#e1ffe1
    style IsolatedLoop fill:#fff4e1
    style SubagentLLM fill:#f0e1ff
```

## 8. 错误处理调用图

> **修正说明**：旧版臆造了"预算错误/系统错误/安全模式/降级处理"等分支。实际错误处理由**两个独立中间件**承担，职责清晰：
> - **LLMErrorHandling**（`wrap_model_call`）：包裹模型调用，分类错误→可重试则指数退避重试→失败兜底为 `AIMessage`，并带熔断器。
> - **ToolErrorHandling**（`wrap_tool_call`）：包裹工具调用，捕获异常→封装为 `status=error` 的 `ToolMessage`→让 ReAct 循环继续。
>
> 二者均放行 `GraphBubbleUp`（中断/暂停/恢复等 LangGraph 控制流信号）。

```mermaid
graph TB
    subgraph LLM["① LLMErrorHandling · wrap_model_call"]
        direction TB
        L0([模型调用请求]) --> LCirc{熔断器开启?}
        LCirc -->|是| LFback[兜底 AIMessage<br/>circuit_open]
        LCirc -->|否| LTry[调用 handler]
        LTry --> LResult{结果}
        LResult -->|成功| LOK[记录成功<br/>返回响应]
        LResult -->|GraphBubbleUp| LBubble[原样上抛]
        LResult -->|异常| LClass[_classify_error]
        LClass --> LKind{可重试?}
        LKind -->|transient / busy| LRetryQ{attempt &lt; max?}
        LKind -->|quota / auth / generic| LFail[兜底 AIMessage<br/>deerflow_error_fallback]
        LRetryQ -->|是| LRetry[指数退避 sleep<br/>emit llm_retry 事件] --> LTry
        LRetryQ -->|否| LFail
    end

    subgraph TOOL["② ToolErrorHandling · wrap_tool_call"]
        direction TB
        T0([工具调用请求]) --> TTry[调用 handler]
        TTry --> TResult{结果}
        TResult -->|成功| TOK[ToolMessage<br/>task 加盖 subagent_status]
        TResult -->|GraphBubbleUp| TBubble[原样上抛]
        TResult -->|异常| TErr["ToolMessage status=error<br/>Error: Tool '…' failed with …"]
    end

    LOK --> Cont([继续 ReAct 循环])
    LFail --> Cont
    TOK --> Cont
    TErr --> Cont

    style L0 fill:#1f6feb,stroke:#58a6ff,color:#fff
    style T0 fill:#1f6feb,stroke:#58a6ff,color:#fff
    style Cont fill:#238636,stroke:#3fb950,color:#fff
    style LFail fill:#3c1518,stroke:#f85149,color:#fff
    style LFback fill:#3c1518,stroke:#f85149,color:#fff
    style TErr fill:#3c1518,stroke:#f85149,color:#fff
    style LRetry fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style LBubble fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style TBubble fill:#3d2c00,stroke:#e3b341,color:#e6edf3
```

## 图表说明

### 组件颜色图例
- `#e1f5ff` (蓝色): 输入/起始状态
- `#fff4e1` (黄色): 处理/执行状态
- `#f0e1ff` (紫色): 特殊功能/子代理
- `#e1ffe1` (绿色): 完成/输出状态
- `#ffe1e1` (红色): 错误/异常状态

### 关键调用链
1. **请求处理链**: API → Agent → before_model 链 → 模型节点 → ToolNode → after_model 链（逆序）→ 响应
2. **中间件链**: 最多 22 个中间件，两阶段条件构建，before_model 正序、after_model 逆序触发
3. **工具执行链**: 模型产出 tool_calls → ToolNode 按注册表分发（内置/MCP/task）→ wrap_tool_call 包裹 → ToolMessage 回灌 → 回到模型节点循环
4. **子代理链**: 触发（task 工具）→ 创建 → ThreadPoolExecutor 异步执行 → 每 5 秒轮询 → 结果 → 清理

### 设计模式
1. **图工厂模式**: `make_lead_agent` 作为 LangGraph 图工厂函数构建 Lead Agent（非工厂类）
2. **责任链模式**: 中间件链通过顺序调用实现关注点分离
3. **策略模式**: 不同工具类型使用不同的执行策略
4. **异步模式**: 子代理（ThreadPoolExecutor + 独立事件循环）和记忆提取使用异步执行
5. **状态模式**: ThreadState 管理所有运行时状态

### 扩展性设计
- 中间件可插拔，通过条件启用控制
- 工具系统支持内置、MCP、子代理等多种类型
- 模型配置可动态选择
- 错误处理策略可配置
