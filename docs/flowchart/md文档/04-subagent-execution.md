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

> **修正说明**：旧版"配置复制 → 复制模型配置/复制工具列表/复制中间件配置"是臆造的。实际并无"深拷贝配置"步骤：`task_tool` 先用 `get_available_tools(subagent_enabled=False)` 取工具并由 `_filter_tools` 按 allow/deny 过滤，再构造 `SubagentExecutor`（**继承**父代理的 `sandbox_state / thread_data / thread_id / trace_id`）；`execute_async` 先在 `_background_tasks` 登记 `PENDING` 结果，再把 `run_task` 提交给 `_scheduler_pool`（ThreadPoolExecutor, max_workers=3），由后台线程翻转为 `RUNNING` 并把 `_aexecute` 投递到**持久复用的隔离事件循环**。

```mermaid
graph TB
    Start([LLM 调用 task 工具]) --> Validate{参数 + subagent_type<br/>有效?}
    Validate -->|否| Error[返回 Error 字符串]
    Validate -->|是| GetTools[get_available_tools<br/>subagent_enabled=False<br/>★ 禁止嵌套]

    subgraph Build["构造执行器 · 主线程同步"]
        direction TB
        GetTools --> Filter[_filter_tools<br/>按 allowed/disallowed 过滤]
        Filter --> NewExec[new SubagentExecutor<br/>继承 sandbox_state / thread_data<br/>thread_id / trace_id]
    end

    NewExec --> ExecAsync[executor.execute_async<br/>task_id = tool_call_id]

    subgraph Async["execute_async · 登记并提交"]
        direction TB
        ExecAsync --> Pending[在 _background_tasks 登记<br/>SubagentResult status=PENDING]
        Pending --> Submit[_scheduler_pool.submit（run_task）]
        Submit --> Running[run_task 线程内<br/>status=RUNNING + started_at]
        Running --> ToLoop[投递 _aexecute 到<br/>持久隔离事件循环<br/>见第 3 图]
    end

    ExecAsync --> ReturnID[返回 task_id]
    ReturnID --> Poll([进入轮询 · 见第 6 图])

    Error --> Done([结束])

    style Start fill:#1f6feb,stroke:#58a6ff,color:#fff
    style Poll fill:#238636,stroke:#3fb950,color:#fff
    style Done fill:#238636,stroke:#3fb950,color:#fff
    style GetTools fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style ToLoop fill:#3d2c5a,stroke:#bc8cff,color:#fff
    style Error fill:#3c1518,stroke:#f85149,color:#fff
    style Pending fill:#1a2a4a,stroke:#58a6ff,color:#e6edf3
```

## 3. 子代理执行引擎图

> **修正说明**：旧版"初始化执行池/设置并发限制:3/创建任务队列"与手写 LLM 循环都是臆造的。真实的 `_aexecute`（`executor.py:483`）跑在**持久复用**的隔离事件循环上（**不是每个任务新建并关闭**）：先 `_build_initial_state`（加载技能、组装 deferred 工具、把 system prompt 放进初始 messages），再 `_create_agent`（LangChain `create_agent`，复用 `build_subagent_runtime_middlewares`，`checkpointer=False`），随后 `agent.astream(recursion_limit=max_turns)` 驱动 ReAct 循环。所谓"LLM 循环"是 LangGraph 内部行为，外层只在每个 chunk 边界做**协作式取消**检查并收集 `AIMessage`。

```mermaid
graph TB
    Start([run_task 投递 _aexecute<br/>到持久隔离事件循环]) --> PreCancel{cancel_event<br/>已置位?}
    PreCancel -->|是| Cancelled[try_set_terminal<br/>CANCELLED]

    PreCancel -->|否| BuildState

    subgraph Prepare["执行前准备"]
        direction TB
        BuildState[_build_initial_state<br/>加载技能 + 组装 deferred 工具<br/>system prompt 入 messages] --> CreateAgent[_create_agent<br/>create_chat_model thinking=False<br/>build_subagent_runtime_middlewares<br/>checkpointer=False]
    end

    CreateAgent --> Stream

    subgraph Loop["agent.astream · recursion_limit=max_turns"]
        direction TB
        Stream[逐 chunk 流式迭代<br/>stream_mode=values] --> CancelChk{cancel_event<br/>已置位?}
        CancelChk -->|是| CancelMid[try_set_terminal<br/>CANCELLED 并返回]
        CancelChk -->|否| Collect[收集新 AIMessage<br/>按 id 去重]
        Collect --> More{还有 chunk?}
        More -->|是| Stream
    end

    More -->|否 流式结束| Final[提取最后一条 AIMessage<br/>作为最终结果]
    Final --> Completed[try_set_terminal<br/>COMPLETED + token 用量]

    Stream -.astream 抛异常.-> Failed[try_set_terminal<br/>FAILED + error]

    style Start fill:#1f6feb,stroke:#58a6ff,color:#fff
    style Completed fill:#238636,stroke:#3fb950,color:#fff
    style Failed fill:#3c1518,stroke:#f85149,color:#fff
    style Cancelled fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style CancelMid fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style CreateAgent fill:#3d2c5a,stroke:#bc8cff,color:#fff
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

> **重要修正**：旧版的"延迟计时器/延长延迟/有活跃引用?/持久化最终状态/更新索引/通知父代理/关闭独立事件循环"全部是臆造的。真实的 `cleanup_background_task`（`executor.py:866`）极其简单：仅当任务处于**终态**（`status.is_terminal` 或 `completed_at` 非空）时 `del _background_tasks[task_id]`，否则跳过（避免与后台线程更新条目竞争）。**持久隔离事件循环不会在每个任务后关闭**（它被所有子代理复用，仅在进程退出时由 `atexit` 关闭）。唯一的"延迟清理"出现在轮询安全网触发取消的兜底路径上。

```mermaid
graph TB
    subgraph Normal["正常路径 · task_tool 轮询命中终态后"]
        direction TB
        Term([轮询得到终态<br/>COMPLETED/FAILED<br/>CANCELLED/TIMED_OUT]) --> Call[cleanup_background_task（task_id）]
        Call --> Check{status.is_terminal<br/>或 completed_at 非空?}
        Check -->|是| Del[del _background_tasks task_id]
        Check -->|否| Skip[跳过 · 记 debug 日志<br/>防与后台线程竞争]
    end

    subgraph Safety["安全网路径 · 轮询超过上限"]
        direction TB
        Over([poll_count &gt; max_poll_count]) --> Cancel[request_cancel_background_task<br/>设置 cancel_event 协作式取消]
        Cancel --> Defer[_schedule_deferred_subagent_cleanup<br/>asyncio.create_task]
        Defer --> DLoop[_deferred_cleanup_subagent_task<br/>每 5 秒轮询]
        DLoop --> DTerm{已到终态?}
        DTerm -->|是| DDel[cleanup_background_task<br/>→ 移除条目]
        DTerm -->|否, 未超上限| DLoop
        DTerm -->|否, 超出 max_polls| DGiveup[记 warning 放弃]
    end

    Del --> Done([条目已移除])
    DDel --> Done

    style Term fill:#1f6feb,stroke:#58a6ff,color:#fff
    style Over fill:#3d2c00,stroke:#e3b341,color:#e6edf3
    style Done fill:#238636,stroke:#3fb950,color:#fff
    style Del fill:#1a3a1a,stroke:#3fb950,color:#e6edf3
    style DDel fill:#1a3a1a,stroke:#3fb950,color:#e6edf3
    style Cancel fill:#3c1518,stroke:#f85149,color:#fff
    style DGiveup fill:#3c1518,stroke:#f85149,color:#fff
```

**关键点**：
- **无显式资源释放**：子代理 `ThreadState`、sandbox 句柄等随条目从 `_background_tasks` 移除后由 GC 回收，代码中没有逐项"释放 artifacts / 关闭事件循环"的步骤。
- **终态守卫**：`cleanup_background_task` 对非终态任务直接跳过，避免删除仍在被后台线程更新的条目。
- **兜底取消是协作式的**：`request_cancel_background_task` 只设置 `cancel_event`，真正停止发生在 `_aexecute` 的 `astream` 下一个 chunk 边界。

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
1. **异步执行**: 持久复用的隔离事件循环（`_get_isolated_subagent_loop`，跨子代理复用，进程退出时由 `atexit` 关闭），而非每个任务新建/关闭
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
