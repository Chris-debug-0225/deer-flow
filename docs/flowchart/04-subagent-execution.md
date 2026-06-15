# DeerFlow 子代理执行流程图

本文档包含子代理系统的完整 Mermaid 流程图，展示子代理的创建、执行、状态管理和结果处理。

## 1. 子代理生命周期图

展示子代理从创建到完成的完整生命周期。

```mermaid
stateDiagram-v2
    [*] --> PENDING: 任务创建
    PENDING --> RUNNING: 开始执行（分配执行器）
    RUNNING --> COMPLETED: 任务完成
    RUNNING --> FAILED: 执行失败
    RUNNING --> TIMED_OUT: 超时（仅 timeout_seconds=900s 一种）
    RUNNING --> CANCELLED: 用户取消
    
    COMPLETED --> [*]: 返回结果
    FAILED --> [*]: 返回错误
    TIMED_OUT --> [*]: 返回超时
    CANCELLED --> [*]: 返回取消
    
    note right of PENDING
        等待 ThreadPoolExecutor 空闲槽位
        (max_workers=3)
    end note
    
    note right of RUNNING
        SubagentExecutor 分配执行器
        启动独立事件循环
        执行 LLM 循环（含工具调用）
    end note
    
    note right of COMPLETED
        收集所有工具结果
        生成最终响应
        清理临时资源
    end note
```

> **修正说明**：旧版含虚构的 `EXECUTING` 子状态与 `TIMEOUT` 状态名。实际 `SubagentStatus` 枚举为 `PENDING / RUNNING / COMPLETED / FAILED / CANCELLED / TIMED_OUT`（`executor.py:47-55`），无 `EXECUTING`，`RUNNING` 直接覆盖整个执行阶段。

## 2. 子代理创建流程图

展示子代理创建的完整流程。

```mermaid
graph TB
    subgraph "触发阶段"
        Start[LLM 调用 task_tool] --> ParseArgs[解析参数]
        ParseArgs --> Validate{参数有效？}
        Validate -->|是 | CreateTask[创建任务对象]
        Validate -->|否 | Error[返回错误]
    end
    
    subgraph "任务对象创建"
        CreateTask --> GenTaskID[生成任务 ID]
        GenTaskID --> InitState[初始化状态]
        InitState --> SetParent[设置父线程信息]
        SetParent --> CopyConfig[复制配置]
    end
    
    subgraph "配置复制"
        CopyConfig --> CopyModel[复制模型配置]
        CopyConfig --> CopyTools[复制工具列表]
        CopyConfig --> CopyMiddleware[复制中间件配置]
        CopyConfig --> SetTimeout[设置超时时间]
    end
    
    subgraph "资源分配"
        SetTimeout --> SubmitPool[_scheduler_pool.submit<br/>ThreadPoolExecutor max_workers=3]
        SubmitPool --> CheckSlot{有空闲 worker？}
        CheckSlot -->|是 | AssignExec[分配执行器]
        CheckSlot -->|否 阻塞 | WaitWorker[阻塞等待 worker 释放]
        WaitWorker --> CheckCancel{cancel_event？}
        CheckCancel -->|是 | CancelErr[取消错误]
        CheckCancel -->|否 | AssignExec
    end
    
    subgraph "执行器初始化"
        AssignExec --> CreateLoop[创建事件循环]
        CreateLoop --> InitAgent[初始化子代理]
        InitAgent --> StartExec[启动执行]
        StartExec --> UpdateStatus[更新状态：RUNNING]
    end
    
    subgraph "结果返回"
        UpdateStatus --> ReturnID[返回任务 ID]
        ReturnID --> PollStart[开始轮询]
        
        Error --> ReturnErr[返回错误信息]
        CancelErr --> ReturnErr
        
        ReturnID --> End([完成])
        ReturnErr --> End
    end
    
    style Start fill:#e1f5ff
    style End fill:#e1ffe1
    style AssignExec fill:#fff4e1
    style PollStart fill:#f0e1ff
```

## 3. 子代理执行引擎图

展示子代理执行引擎的核心执行流程。

```mermaid
graph TB
    subgraph "执行器初始化"
        Start[SubagentExecutor] --> InitPool[初始化执行池]
        InitPool --> SetLimit[设置并发限制：3]
        SetLimit --> CreateQueue[创建任务队列]
    end
    
    subgraph "任务执行"
        CreateQueue --> GetTask[获取任务]
        GetTask --> CheckStatus{状态检查}
        CheckStatus -->|有效 | CreateIsolatedLoop[创建独立事件循环]
        CheckStatus -->|取消 | SkipExec[跳过执行]
    end
    
    subgraph "独立事件循环"
        CreateIsolatedLoop --> NewLoop[asyncio.new_event_loop]
        NewLoop --> SetEventLoop[设置事件循环]
        SetEventLoop --> InitSubagent[初始化子代理实例]
        InitSubagent --> InvokeSubagent[Invoke 子代理]
    end
    
    subgraph "LLM 循环"
        InvokeSubagent --> GetState[获取 ThreadState]
        GetState --> CallMiddleware[调用中间件链]
        CallMiddleware --> CallLLM[调用 LLM]
        CallLLM --> ParseResponse[解析响应]
        
        ParseResponse --> HasTools{有工具？}
        HasTools -->|是 | ExecuteTools
        HasTools -->|否 | FormatOutput
        
        ExecuteTools[执行工具] --> ToolResult[工具结果]
        ToolResult --> UpdateState[更新状态]
        UpdateState --> CallLLM
        
        FormatOutput[格式化输出] --> CheckComplete{完成？}
        CheckComplete -->|是 | ReturnResult
        CheckComplete -->|否 | GetState
    end
    
    subgraph "状态管理"
        ReturnResult[返回结果] --> SetStatus[设置状态：COMPLETED]
        SetStatus --> CollectResult[收集结果]
        CollectResult --> Cleanup[清理资源]
        
        SkipExec --> SetStatusCancel[设置状态：CANCELLED]
        SetStatusCancel --> Cleanup
    end
    
    subgraph "错误处理"
        InvokeSubagent --> TryCatch[Try-Catch]
        TryCatch -->|异常 | SetStatusFail[设置状态：FAILED]
        SetStatusFail --> GetException[获取异常]
        GetException --> FormatError[格式化错误]
        FormatError --> ReturnError[返回错误结果]
    end
    
    style Start fill:#e1f5ff
    style ReturnResult fill:#e1ffe1
    style CreateIsolatedLoop fill:#fff4e1
    style ExecuteTools fill:#f0e1ff
    style SetStatusFail fill:#ffe1e1
```

## 4. 子代理状态流转图

展示子代理状态机的完整流转逻辑。

```mermaid
stateDiagram-v2
    direction TB

    [*] --> PENDING: 创建任务
    PENDING --> RUNNING: 分配 ThreadPoolExecutor worker
    PENDING --> CANCELLED: 等待期间取消

    RUNNING --> COMPLETED: 正常完成
    RUNNING --> FAILED: 执行失败
    RUNNING --> TIMED_OUT: timeout_seconds=900s 超时
    RUNNING --> CANCELLED: 用户取消

    COMPLETED --> [*]: 返回结果
    FAILED --> [*]: 返回错误
    TIMED_OUT --> [*]: 返回超时
    CANCELLED --> [*]: 返回取消

    note right of PENDING
        内部子状态：QUEUED（等待 _scheduler_pool 槽位）
        可被取消
    end note

    note right of RUNNING
        内部子状态流转：
        INITIALIZING -> LLM_LOOP -> TOOL_CALL
        （TOOL_CALL 完成后回到 LLM_LOOP）
        timeout_seconds 保护（默认 900s）
    end note

    note left of COMPLETED
        收集所有输出
        清理临时数据
        返回最终结果
    end note

    note left of FAILED
        记录错误信息
        清理执行资源
        返回错误详情
    end note
```

> **修正说明**：旧版含虚构的 `EXECUTING` 顶层状态、`TIMEOUT` 状态名以及"30 秒队列超时"。实际为 `PENDING → RUNNING`（内含 INITIALIZING/LLM_LOOP/TOOL_CALL 子状态），超时统一为 `TIMED_OUT`，无独立队列超时。

## 5. 子代理并发控制图

展示子代理的并发执行和队列管理机制。

```mermaid
graph TB
    subgraph "并发限制 (ThreadPoolExecutor)"
        Start[任务请求<br/>_scheduler_pool.submit] --> CheckConcurrency{空闲 worker &lt; 3?}
        CheckConcurrency -->|是 有空闲 worker | AllowExec[获得 worker]
        CheckConcurrency -->|否 3 个都在忙 | EnqueueTask[阻塞等待]
    end
    
    subgraph "任务队列"
        EnqueueTask --> QueueOrder[ThreadPoolExecutor 内部队列]
        QueueOrder --> WaitSlot[等待 worker 释放]
        WaitSlot --> CheckCancel{cancel_event 被设置？}
        CheckCancel -->|是 | CancelTask[取消任务]
        CheckCancel -->|否 | WaitSlot
        
        CancelTask --> ReturnCancel[返回取消]
    end
    
    subgraph "槽位管理"
        AllowExec --> AssignSlot[分配执行槽位]
        AssignSlot --> ExecuteTask[执行任务]
        
        ExecuteTask --> OnComplete[完成执行]
        OnComplete --> ReleaseSlot[释放 worker]
        ReleaseSlot --> NotifyQueue[唤醒阻塞任务]
    end
    
    subgraph "队列通知"
        NotifyQueue --> CheckQueue{队列非空？}
        CheckQueue -->|是 | NextTask[取下一个任务]
        CheckQueue -->|否 | Idle[空闲状态]
        
        NextTask --> AssignSlot
    end
    
    subgraph "执行超时控制（无队列超时）"
        ExecuteTask --> ExecTimeout{future.result 超时<br/>timeout_seconds=900s?}
        ExecTimeout -->|是 | ExecTimeoutErr[设置 TIMED_OUT]
        ExecTimeout -->|否 完成 | OnComplete
    end
    
    style Start fill:#e1f5ff
    style AllowExec fill:#e1ffe1
    style EnqueueTask fill:#fff4e1
    style CancelTask fill:#ffe1e1
    style NotifyQueue fill:#f0e1ff
```

## 6. 子代理结果轮询图

展示父代理轮询子代理结果的完整流程。

```mermaid
sequenceDiagram
    participant Parent as 父代理
    participant Poller as 轮询器
    participant Executor as 执行器
    participant Storage as 状态存储
    
    Parent->>Poller: 启动轮询 (task_id)
    
    loop 轮询循环
        Poller->>Storage: 获取任务状态
        Storage-->>Poller: 返回状态
        
        alt PENDING
            Poller->>Poller: asyncio.sleep(5)
        else RUNNING
            Poller->>Poller: asyncio.sleep(5)
        else COMPLETED
            Poller->>Storage: 获取结果
            Storage-->>Poller: 返回结果
            Poller->>Parent: 返回结果
            break 退出轮询
        else FAILED
            Poller->>Storage: 获取错误
            Storage-->>Poller: 返回错误
            Poller->>Parent: 返回错误
            break 退出轮询
        else TIMED_OUT
            Poller->>Parent: 返回超时
            break 退出轮询
        else CANCELLED
            Poller->>Parent: 返回取消
            break 退出轮询
        end
        
        Poller->>Poller: asyncio.sleep(5)
    end
    
    Parent->>Poller: 停止轮询 (可选)
    Poller-->>Parent: 轮询停止
```

## 7. 子代理嵌套调用图（嵌套被禁止）

> **重要修正**：旧版此处画了"子代理 1 → 子代理 2 → 子代理 3"的三层嵌套调用图。**代码明确禁止嵌套**：`task_tool.py:290-295` 中子代理创建时强制 `subagent_enabled=False`，注释写明 *"Subagents should not have subagent tools enabled (prevent recursive nesting)"*。因此子代理无法再创建孙代理。

```mermaid
graph TB
    subgraph "父代理（Lead Agent）"
        Start[父代理执行] --> CallTask[调用 task 工具]
        CallTask --> CreateSub[创建子代理<br/>subagent_enabled=False]
    end
    
    subgraph "子代理（不可再委托）"
        CreateSub --> SubExec[SubagentExecutor 执行]
        SubExec --> SubLLM[子代理 LLM 循环]
        SubLLM --> SubTools[可用工具中<br/>不包含 task 工具]
        SubTools --> SubFinal[生成最终响应]
    end
    
    subgraph "结果返回（单层，无递归）"
        SubFinal --> ReturnSub[返回结果给父代理]
        ReturnSub --> ParentResult[父代理接收并继续]
    end
    
    Forbidden[禁止：子代理调用 task 创建孙代理]
    SubTools -.->|设计上不可达| Forbidden
    
    style Start fill:#e1f5ff
    style ParentResult fill:#e1ffe1
    style CreateSub fill:#fff4e1
    style Forbidden fill:#ffe1e1
```

**设计意图**：禁用嵌套可避免递归爆炸、简化状态管理与资源回收，并让父子任务边界清晰。需要并行/分解任务时，应由父代理并行调用多个子代理（受 `max_concurrent_subagents=3` 限制），而非让子代理层层下钻。

## 8. 子代理超时控制图

> **重要修正**：旧版声称存在"总体 15 分钟 / 空闲 5 分钟 / 队列 30 秒"三重超时。**代码中"空闲超时"和"队列超时"完全不存在**，仅有单一执行超时 `timeout_seconds`（默认 900 秒 = 15 分钟，`config.py:35`）加一个轮询安全网。

```mermaid
graph TB
    Start[任务创建] --> ReadConfig[读取 config.timeout_seconds<br/>默认 900s]
    ReadConfig --> Submit[_scheduler_pool.submit]
    Submit --> ExecTimeout[执行超时: future.result timeout=900s]
    
    ExecTimeout --> ExecCheck{future 超时？}
    ExecCheck -->|否 正常完成| SetCompleted[设置状态: COMPLETED]
    ExecCheck -->|是 超时| SetTimedOut[设置状态: TIMED_OUT]
    
    SetTimedOut --> LogErr[记录超时错误]
    LogErr --> ReturnTimeout[返回超时结果]
    SetCompleted --> ReturnNormal[返回正常结果]
    
    ReturnTimeout --> PollNet[父代理轮询安全网<br/>轮询上限 = 900/60+1 次<br/>每 5 秒一次]
    ReturnNormal --> PollNet
    PollNet --> Catch{是否超过轮询上限？}
    Catch -->|是 卡住的安全网| CancelTask[request_cancel_background_task<br/>协作式取消]
    Catch -->|否| Cleanup[cleanup_background_task]
    CancelTask --> Cleanup
    
    style Start fill:#e1f5ff
    style ExecTimeout fill:#fff4e1
    style SetTimedOut fill:#ffe1e1
    style CancelTask fill:#ffe1e1
    style Cleanup fill:#e1ffe1
```

**真实超时机制**：
- **执行超时**：`future.result(timeout=self.config.timeout_seconds)`（`executor.py:693`、`executor.py:801`），由 `ThreadPoolExecutor` 的 `Future` 实现，唯一超时来源。
- **轮询安全网**：`task_tool.py:400-415`，作为"线程池超时万一失效"的兜底，轮询计数超过 `max_poll_count` 后协作式取消。
- **可配置**：`timeout_seconds` 可在 `config.yaml` 的 `subagents` 全局或 `agents.<name>` 单代理级别覆盖（`registry.py:83-90`）。

## 9. 子代理清理机制图

展示子代理完成后的资源清理流程。

```mermaid
graph TB
    subgraph "触发清理"
        Start[任务完成] --> TriggerCleanup[触发清理]
        TriggerCleanup --> DelayCheck{延迟清理？}
    end
    
    subgraph "延迟清理"
        DelayCheck -->|是 | StartDelay[启动延迟计时器]
        StartDelay --> DelayWait[等待延迟时间]
        DelayWait --> ActiveCheck{有活跃引用？}
        
        ActiveCheck -->|是 | ExtendDelay[延长延迟]
        ExtendDelay --> DelayWait
        
        ActiveCheck -->|否 | ProceedCleanup
        DelayCheck -->|否 | ProceedCleanup
    end
    
    subgraph "状态清理"
        ProceedCleanup[执行清理] --> ClearState[清除子代理 ThreadState]
        ClearState --> ClearArtifacts[释放临时 artifacts 引用]
        ClearArtifacts --> ClearSandbox[释放 sandbox 句柄]
        ClearSandbox --> ReleaseLoop[关闭独立事件循环]
    end
    
    subgraph "资源释放"
        ReleaseLoop --> ReleaseExecutor[释放 ThreadPoolExecutor 槽位]
        ReleaseExecutor --> RemoveTask[从 _background_tasks 移除]
        RemoveTask --> UpdatePool[更新任务表]
    end
    
    subgraph "持久化"
        UpdatePool --> PersistFinal[持久化最终状态]
        PersistFinal --> UpdateIndex[更新索引]
        UpdateIndex --> NotifyParent[通知父代理]
    end
    
    subgraph "错误清理"
        Start --> ErrorCheck{执行失败？}
        ErrorCheck -->|是 | ErrorCleanup[错误清理]
        ErrorCheck -->|否 | TriggerCleanup
        
        ErrorCleanup --> SaveErrorLog[保存错误日志]
        SaveErrorLog --> PartialCleanup[部分清理]
        PartialCleanup --> UpdateStatus[更新状态]
        UpdateStatus --> ErrNotify[通知父代理]
    end
    
    style Start fill:#e1f5ff
    style UpdatePool fill:#e1ffe1
    style ErrorCleanup fill:#ffe1e1
    style NotifyParent fill:#f0e1ff
```

## 10. 子代理工具调用时序图

展示子代理工具调用的完整时序。

```mermaid
sequenceDiagram
    participant LLM as LLM
    participant Parser as 解析器
    participant Tool as task_tool
    participant Executor as SubagentExecutor
    participant Parent as 父线程
    participant Storage as 存储
    
    LLM->>Parser: 输出工具调用
    Parser->>Tool: 调用 task_tool(args)
    
    Tool->>Tool: 验证参数
    Tool->>Executor: 创建执行器实例
    Executor->>Executor: 初始化子代理
    Executor->>Storage: 保存任务状态 (PENDING)
    
    Executor->>Executor: 检查并发限制
    alt 有可用槽位
        Executor->>Executor: 启动执行
        Executor->>Storage: 更新状态 (RUNNING)
    else 无可用槽位
        Executor->>Storage: 加入队列
        Storage->>Executor: 队列位置
    end
    
    Tool->>Executor: 返回 task_id
    Tool->>Parser: 返回工具调用结果
    
    Parser->>LLM: 继续执行 (task_id 待完成)
    
    loop 轮询结果
        Tool->>Storage: 查询任务状态
        Storage-->>Tool: 返回状态
        
        alt PENDING/RUNNING
            Tool->>Tool: 等待 5 秒
        else COMPLETED
            Storage->>Tool: 返回结果
            Tool->>Parser: 返回完整结果
            break
        else FAILED/TIMED_OUT/CANCELLED
            Storage->>Tool: 返回错误
            Tool->>Parser: 返回错误
            break
        end
    end
    
    Parser->>LLM: 工具调用结果
    LLM->>LLM: 生成最终响应
```

## 图表说明

### 状态图例
- **PENDING**: 任务已创建，等待 `_scheduler_pool`（ThreadPoolExecutor）槽位
- **RUNNING**: 正在执行，已分配执行器，内部含 INITIALIZING/LLM_LOOP/TOOL_CALL 子状态
- **COMPLETED**: 正常完成，有有效结果
- **FAILED**: 执行失败，有错误信息
- **TIMED_OUT**: 超时（单一执行超时 `timeout_seconds`，默认 900s）
- **CANCELLED**: 用户主动取消（协作式，经 `cancel_event`）

> 注：旧版的 `EXECUTING` 顶层状态与 `TIMEOUT` 状态名均已修正（无 EXECUTING，TIMEOUT→TIMED_OUT）。

### 关键参数
- **最大并发**: `MAX_CONCURRENT_SUBAGENTS = 3`，由 `_scheduler_pool = ThreadPoolExecutor(max_workers=3)` 实现（`executor.py:141`、`executor.py:821`）
- **执行超时**: `timeout_seconds` 默认 900 秒（15 分钟），`config.py:35`，可全局或单代理覆盖
- **轮询间隔**: **5 秒**（`asyncio.sleep(5)`，`task_tool.py:397`）
- **轮询安全网上限**: `timeout_seconds // 60 + 1` 次（`task_tool.py:400`）

### 设计特点
1. **异步执行**: 独立事件循环隔离子代理（`asyncio.new_event_loop`）
2. **并发控制**: `_scheduler_pool` 线程池限制最大并发数；另有 `SubagentLimitMiddleware` 截断 LLM 输出的并行 task 工具调用
3. **单一执行超时**: 由 `Future.result(timeout=...)` 实现，加轮询安全网兜底（无空闲/队列超时）
4. **状态轮询**: 父代理每 5 秒轮询子代理状态
5. **延迟清理**: `cleanup_background_task` 仅在终态移除，防止过早清理活跃资源
6. **禁止嵌套**: 子代理强制 `subagent_enabled=False`，无法创建孙代理（`task_tool.py:290-295`）
7. **错误隔离**: 子代理错误不影响父代理，以错误结果返回

### 使用场景
- 复杂任务分解（父代理并行派发多个子代理）
- 长时间运行任务（受 900s 超时保护）
- 需要独立环境的任务
- 并行任务执行（≤3 并发）
- 资源密集型任务
