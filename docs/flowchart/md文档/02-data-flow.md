# DeerFlow 数据流图

本文档包含 DeerFlow 项目的数据流相关 Mermaid 流程图，展示数据如何在系统各组件之间流动。

## 1. 请求数据流图

展示用户请求从前端到后端处理的完整数据流动过程。

```mermaid
graph TB
    Start([用户请求]) --> Auth[API Gateway<br/>AuthMiddleware 认证<br/>+ CSRF 校验]
    Auth --> Parse[请求解析<br/>POST /api/threads/&#123;id&#125;/runs/stream]
    
    Parse --> ThreadCheck{线程已有运行中 Run？}
    ThreadCheck -->|是，且需等待| JoinRun[joinStream 重连现有 Run]
    ThreadCheck -->|否| NewRun[创建新 Run]
    
    JoinRun --> BuildChain[构建中间件链]
    NewRun --> BuildChain
    
    BuildChain --> BeforeChain[before_model 中间件链<br/>按注册顺序触发]
    
    BeforeChain --> Prepare[准备 LLM 请求]
    Prepare --> ContextBuild[构建上下文]
    ContextBuild --> ModelSelect[模型选择]
    
    ModelSelect --> LLMCall[LLM API 调用]
    LLMCall --> ToolCheck{LLM 输出含工具调用？}
    
    ToolCheck -->|是，普通工具| ToolExec[工具执行]
    ToolCheck -->|是，task 工具| SubAgent[委托子代理]
    ToolCheck -->|否| FormatResp[格式化响应]
    
    ToolExec --> ToolResult[工具结果]
    ToolResult --> UpdateState[更新 ThreadState]
    UpdateState --> LLMCall
    
    SubAgent --> ToolResult
    FormatResp --> AfterChain[after_model 中间件链<br/>按注册逆序触发]
    
    AfterChain --> MemoryUpdate[更新 Memory<br/>MemoryMiddleware 异步]
    AfterChain --> StatePersist[状态持久化]
    
    MemoryUpdate --> Persist[持久化]
    StatePersist --> Persist
    
    Persist --> SSE[通过 SSE 连接返回]
    Frontend[前端经 SSE 长连接接收]
    SSE --> Frontend
    Frontend --> End([完成])
    
    style Start fill:#e1f5ff
    style End fill:#ffe1e1
    style LLMCall fill:#fff4e1
    style ToolExec fill:#f0e1ff
    style Persist fill:#e1ffe1
```

## 2. 流式响应数据流图

展示 SSE 流式响应的数据流动过程。

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端
    participant API as API Gateway
    participant Agent as Agent Runtime
    participant Middleware as 中间件链
    participant LLM as LLM Provider
    participant State as 状态存储
    
    User->>Frontend: 发送消息
    Frontend->>API: POST /api/threads/&#123;id&#125;/runs/stream (SSE)
    API->>Agent: 创建运行
    Agent->>Middleware: before_model 中间件链
    
    loop 流式生成
        Middleware->>LLM: 流式请求
        LLM-->>Middleware: 流式 token
        Middleware->>Middleware: 中间件处理
        Middleware->>Agent: yield token
        Agent->>API: 发送 SSE 事件
        API->>Frontend: SSE: token
        Frontend->>User: 显示 token
    end
    
    loop 工具调用
        LLM-->>Middleware: 工具调用
        Middleware->>Agent: 执行工具
        Agent-->>Middleware: 工具结果
        Middleware->>LLM: 携带工具结果继续
        LLM-->>Middleware: 更多 token
    end
    
    Agent->>Middleware: after_model 中间件链 (逆序)
    Agent->>Agent: 完成标记
    Agent->>State: 持久化 ThreadState
    Agent->>API: 完成事件
    API->>Frontend: SSE: end
    Frontend->>User: 显示完成
```

## 3. 状态数据流图

展示 ThreadState 在各中间件之间的数据流动和更新。

```mermaid
graph TB
    subgraph "ThreadState 初始状态"
        Init[空状态] --> Sandbox[SandboxState]
        Init --> ThreadData[ThreadDataState]
        Init --> Artifacts[Artifacts]
        Init --> Todos[Todos]
    end
    
    subgraph "before_model 中间件 (顺序)"
        ThreadLoad[ThreadDataMiddleware<br/>加载线程数据]
        SandboxInit[SandboxMiddleware<br/>初始化沙盒]
        DynamicCtx[DynamicContextMiddleware<br/>注入日期/记忆]
        SkillAct[SkillActivationMiddleware<br/>激活技能]
        Summarize[SummarizationMiddleware<br/>准备摘要 条件]
        TodoCheck[TodoMiddleware<br/>检查待办 仅 plan_mode]
    end
    
    subgraph "after_model 中间件 (逆序)"
        ErrorHandle[ToolErrorHandling<br/>错误处理]
        TitleGen[TitleMiddleware<br/>生成标题]
        MemorySave[MemoryMiddleware<br/>保存记忆]
        ViewImg[ViewImageMiddleware<br/>记录查看 仅 supports_vision]
    end
    
    subgraph "State 更新操作"
        MergeArtifacts[合并 artifacts]
        MergeTodos[合并 todos]
        MergeImages[合并查看图像]
        UpdateThreadData[更新线程数据]
    end
    
    Init --> ThreadLoad
    ThreadLoad --> SandboxInit
    SandboxInit --> DynamicCtx
    DynamicCtx --> SkillAct
    SkillAct --> Summarize
    Summarize --> TodoCheck
    TodoCheck --> LLM[LLM 执行]
    LLM --> ErrorHandle
    ErrorHandle --> TitleGen
    TitleGen --> MemorySave
    MemorySave --> ViewImg
    
    ViewImg --> MergeArtifacts
    ViewImg --> MergeTodos
    ViewImg --> MergeImages
    ViewImg --> UpdateThreadData
    
    MergeArtifacts --> FinalState[最终 ThreadState]
    MergeTodos --> FinalState
    MergeImages --> FinalState
    UpdateThreadData --> FinalState
    
    FinalState --> Persist[持久化到存储]
    
    style Init fill:#e1f5ff
    style LLM fill:#fff4e1
    style FinalState fill:#ffe1e1
    style Persist fill:#e1ffe1
```

## 4. 工具调用数据流图

展示工具调用的完整数据流，包括内置工具和 MCP 工具。

```mermaid
graph TB
    Start[LLM 输出工具调用] --> ParseTool[解析工具调用]
    ParseTool --> ToolType{工具名称？}
    
    ToolType -->|内置工具名<br/>如 present_file/view_image| BuiltIn[内置工具库]
    ToolType -->|MCP 注册的工具名| MCP[MCP 客户端]
    ToolType -->|task| SubAgent[子代理执行]
    
    subgraph "内置工具执行"
        BuiltIn --> Validate[参数验证]
        Validate --> ExecLocal[本地执行]
        ExecLocal --> ResultLocal[返回结果]
    end
    
    subgraph "MCP 工具执行"
        MCP --> MCPExec[MCP 服务器执行<br/>stdio/sse/http 传输]
        MCPExec --> MCPResult[返回 MCP 结果]
    end
    
    subgraph "子代理执行"
        SubAgent --> CreateTask[创建任务<br/>subagent_enabled=False]
        CreateTask --> AsyncExec[ThreadPoolExecutor 异步执行]
        AsyncExec --> Poll[每 5 秒轮询状态]
        Poll --> SubResult[返回子代理结果]
    end
    
    ResultLocal --> FormatOutput[格式化输出]
    MCPResult --> FormatOutput
    SubResult --> FormatOutput
    
    FormatOutput --> UpdateContext[更新 LLM 上下文]
    UpdateContext --> Continue[继续生成]
    
    style Start fill:#e1f5ff
    style Continue fill:#fff4e1
    style SubAgent fill:#f0e1ff
    style MCP fill:#ffe1e1
```

## 5. 记忆系统数据流图

展示 Memory 系统的数据提取、存储和检索流程。

```mermaid
graph TB
    subgraph "记忆提取阶段"
        Conversation[对话完成] --> Filter[过滤消息]
        Filter --> UserMsg[用户消息]
        Filter --> AIResp[AI 响应]
        
        UserMsg --> Queue[记忆队列]
        AIResp --> Queue
        
        Queue --> Extract[异步提取器]
    end
    
    subgraph "记忆处理"
        Extract --> Summarize[摘要生成]
        Summarize --> KeyExtract[关键信息提取]
        KeyExtract --> MemoryObj[创建记忆对象]
    end
    
    subgraph "记忆存储"
        MemoryObj --> Dedup[去重检查]
        Dedup --> Storage[持久化存储]
        Storage --> UpdateIndex[更新索引]
    end
    
    subgraph "记忆检索阶段"
        NewThread[新线程开始] --> ContextBuild[构建上下文]
        ContextBuild --> Retrieve[检索相关记忆]
        Retrieve --> Rank[排序相关度]
        Rank --> Select[选择 Top-K 记忆]
        Select --> Inject[注入上下文]
    end
    
    subgraph "记忆更新"
        UpdateIndex --> Merge[合并相似记忆]
        Merge --> Prune[过期清理]
        Prune --> Storage
    end
    
    style Conversation fill:#e1f5ff
    style Storage fill:#e1ffe1
    style Inject fill:#fff4e1
```

## 6. Sandbox 文件系统数据流图

展示 Sandbox 中的虚拟路径映射和文件系统操作。

```mermaid
graph TB
    subgraph "虚拟路径层"
        UserPath["/mnt/user-data/<br/>workspace / uploads / outputs"]
        SkillsPath["/mnt/skills/"]
        WorkspacePath["/mnt/acp-workspace/<br/>(ACP 代理只读工作区)"]
    end
    
    subgraph "映射层"
        UserPath --> MapUser[映射到用户目录]
        SkillsPath --> MapSkills[映射到 skills 目录]
        WorkspacePath --> MapWS[映射到工作区]
    end
    
    subgraph "Sandbox 层"
        MapUser --> SandboxFS[Sandbox 文件系统]
        MapSkills --> SandboxFS
        MapWS --> SandboxFS
        
        SandboxFS --> Isolate[隔离执行环境]
    end
    
    subgraph "执行层"
        Isolate --> PythonExec[Python 执行器]
        PythonExec --> FileOps[文件操作]
    end
    
    subgraph "真实文件系统"
        MapUser --> RealUser[真实用户目录]
        MapSkills --> RealSkills[真实 skills 目录]
        MapWS --> RealWS[真实工作区]
    end
    
    FileOps --> OpType{操作类型？}
    OpType -->|读取| RealUser
    OpType -->|读取| RealSkills
    OpType -->|读取| RealWS
    OpType -->|写入| RealUser
    OpType -->|写入| RealSkills
    OpType -->|写入| RealWS
    
    style UserPath fill:#e1f5ff
    style SkillsPath fill:#fff4e1
    style WorkspacePath fill:#f0e1ff
    style RealUser fill:#e1ffe1
    style RealSkills fill:#e1ffe1
    style RealWS fill:#e1ffe1
```

## 7. 子代理执行数据流图

展示子代理的异步执行和状态流转。

```mermaid
graph TB
    subgraph "子代理创建"
        Parent[父代理] --> CreateTask[创建任务]
        CreateTask --> AssignID[分配任务 ID]
        AssignID --> InitState[初始化状态]
    end
    
    subgraph "状态流转"
        InitState --> PENDING[状态：PENDING]
        PENDING --> Dispatch[分发到执行器]
        Dispatch --> RUNNING[状态：RUNNING]
        RUNNING --> Exec[执行 LLM 循环]
        Exec --> CheckStatus{状态检查}
    end
    
    subgraph "执行状态"
        CheckStatus -->|完成 | COMPLETED[状态：COMPLETED]
        CheckStatus -->|超时 | TIMED_OUT[状态：TIMED_OUT]
        CheckStatus -->|错误 | FAILED[状态：FAILED]
        CheckStatus -->|取消 | CANCELLED[状态：CANCELLED]
    end
    
    subgraph "结果处理"
        COMPLETED --> Collect[收集结果]
        TIMED_OUT --> Collect
        FAILED --> Collect
        CANCELLED --> Collect
        
        Collect --> FormatResult[格式化结果]
        FormatResult --> ReturnToParent[返回给父代理]
    end
    
    subgraph "并发控制"
        Executor[执行器池] --> Limit{并发限制？}
        Limit -->|是 | Queue[加入队列]
        Limit -->|否 | Exec
        Queue --> Available[可用时执行]
        Available --> Exec
    end
    
    style PENDING fill:#fff4e1
    style RUNNING fill:#e1f5ff
    style COMPLETED fill:#e1ffe1
    style FAILED fill:#ffe1e1
    style ReturnToParent fill:#f0e1ff
```

## 图表说明

### 颜色图例
- `#e1f5ff` (蓝色): 起始/输入状态
- `#fff4e1` (黄色): 处理/执行状态
- `#f0e1ff` (紫色): 特殊功能
- `#e1ffe1` (绿色): 完成/输出状态
- `#ffe1e1` (红色): 错误/终止状态

### 数据流特点
1. **流式处理**: 所有响应都通过 SSE 流式传输，实现实时交互
2. **状态管理**: ThreadState 作为单一事实源，所有中间件共享和更新
3. **异步执行**: 子代理、记忆提取等操作异步执行，不阻塞主流程
4. **隔离执行**: Sandbox 提供隔离的执行环境，保护系统安全
5. **持久化**: 所有状态和记忆都会持久化到存储，支持跨会话

### 关键数据对象
- **ThreadState**: 包含所有运行时状态的 TypedDict
- **Run**: 运行记录，包含完整的执行历史
- **Memory**: 持久化的对话记忆
- **Artifact**: 工具执行产生的数据文件
- **Todo**: 待办事项列表
