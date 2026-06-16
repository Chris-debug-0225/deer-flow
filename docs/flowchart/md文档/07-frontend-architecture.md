# DeerFlow 前端架构与交互流程图

本文档包含 DeerFlow 前端系统的完整流程图，展示页面路由、组件架构、状态管理和用户交互流程。

---

## 目录

1. [前端整体架构图](#1-前端整体架构图)
2. [页面路由结构图](#2-页面路由结构图)
3. [工作区布局组件图](#3-工作区布局组件图)
4. [输入框组件交互图](#4-输入框组件交互图)
5. [消息渲染组件图](#5-消息渲染组件图)
6. [状态管理架构](#6-状态管理架构)
7. [流式响应处理流程](#7-流式响应处理流程)
8. [线程生命周期管理](#8-线程生命周期管理)
9. [文件上传流程](#9-文件上传流程)
10. [技能建议系统](#10-技能建议系统)
11. [组件依赖关系图](#11-组件依赖关系图)

---

## 1. 前端整体架构图

```mermaid
graph TB
    subgraph "前端应用层"
        A[Next.js 16 应用]
        A --> B[着陆页面 LandingPage]
        A --> C[工作区 Workspace]
        A --> D[设置页面 Settings]
    end

    subgraph "核心组件层"
        B --> E[Landing 组件]
        C --> F[Workspace 组件]
        D --> G[Settings 组件]
        
        E --> E1[Header]
        E --> E2[Hero]
        E --> E3[CaseStudySection]
        
        F --> F1[WorkspaceContainer]
        F --> F2[WorkspaceSidebar]
        F --> F3[WorkspaceHeader]
        F --> F4[WorkspaceBody]
    end

    subgraph "功能组件层"
        F4 --> H[InputBox 输入框]
        F4 --> I[Messages 消息列表]
        F4 --> J[Artifacts 工件展示]
        F4 --> K[TodoList 待办列表]
        F4 --> L[Channels 频道选择]
    end

    subgraph "UI 组件库"
        H --> M[Shadcn UI]
        I --> M
        J --> M
        K --> M
        L --> M
    end

    subgraph "核心服务层"
        N[React Query 状态管理]
        O[API 客户端]
        P[i18n 国际化]
        Q[主题提供者]
    end

    F --> N
    F --> O
    F --> P
    F --> Q
    H --> N
    I --> N
```

**图例说明:**
- **前端应用层**: Next.js 16 构建的多页面应用，包含着陆页、工作区和设置页
- **核心组件层**: 各页面的主要布局组件
- **功能组件层**: 工作区内的核心功能组件
- **UI 组件库**: 基于 Shadcn UI 的组件系统
- **核心服务层**: 状态管理、API 调用、国际化等公共服务

---

## 2. 页面路由结构图

```mermaid
graph LR
    A[/] --> B[LandingPage]
    A --> C[Workspace 重定向]
    
    C --> D{是否有历史线程？}
    D -->|是 | E["/workspace/chats/[thread_id]"]
    D -->|否 | F["/workspace/chats?new=true"]
    
    E --> G[ChatPage]
    F --> G
    
    H[/settings] --> I[SettingsPage]
    J[/docs] --> K[DocsPage]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#fff3e0
    style D fill:#ffe0b2
    style E fill:#e8f5e9
    style F fill:#e8f5e9
    style G fill:#e8f5e9
    style H fill:#f3e5f5
    style I fill:#f3e5f5
    style J fill:#fce4ec
    style K fill:#fce4ec
```

**路由说明:**

| 路由 | 组件 | 功能 |
|------|------|------|
| `/` | `LandingPage` | 着陆页面，展示产品介绍和案例研究 |
| `/workspace` | 重定向组件 | 根据历史线程重定向到聊天页或新建聊天 |
| `/workspace/chats/[thread_id]` | `ChatPage` | 聊天工作区核心页面 |
| `/workspace/chats?new=true` | `ChatPage` | 新建聊天入口 |
| `/settings` | `SettingsPage` | 用户设置页面 |
| `/docs` | `DocsPage` | 文档页面 |

---

## 3. 工作区布局组件图

```mermaid
graph TB
    subgraph "WorkspaceContainer 根容器"
        A[WorkspaceContainer<br/>flex h-screen flex-col]
        
        A --> B[WorkspaceHeader<br/>h-16 面包屑 + GitHub 链接]
        A --> C[WorkspaceBody<br/>flex-1 主内容区]
    end

    subgraph "WorkspaceBody 内部结构"
        C --> D[Sidebar 侧边栏]
        C --> E[MainContent 主内容区]
    end

    subgraph "Sidebar 侧边栏"
        D --> D1[RecentChatList<br/>最近聊天列表]
        D --> D2[NavMenu<br/>导航菜单]
        D --> D3[ThreadChannelSource<br/>频道数据源]
    end

    subgraph "MainContent 主内容区"
        E --> E1[Messages 消息列表]
        E --> E2[InputBox 输入框]
        E --> E3[Artifacts 工件展示]
        E --> E4[TodoList 待办列表]
    end

    subgraph "Shared 共享组件"
        F[Tooltip 提示]
        G[CopyButton 复制按钮]
        H[StreamingIndicator<br/>流式指示器]
        I[TokenUsageIndicator<br/>Token 使用指示器]
    end

    E1 --> F
    E2 --> F
    E1 --> H
    E1 --> G
    E --> I
```

**组件职责:**

- **WorkspaceContainer**: 全屏 flex 布局容器，包含 header 和 body
- **WorkspaceHeader**: 顶部导航栏，显示面包屑导航和 GitHub 链接
- **WorkspaceBody**: 主内容区域，分为侧边栏和主内容区
- **Sidebar**: 左侧边栏，显示最近聊天列表和导航菜单
- **MainContent**: 主内容区，包含消息列表、输入框、工件和待办列表

---

## 4. 输入框组件交互图

```mermaid
sequenceDiagram
    participant U as 用户
    participant IB as InputBox 组件
    participant S as Skills 服务
    participant API as Backend API
    participant LG as LangGraph SDK
    
    U->>IB: 输入文本"/python"
    IB->>IB: getMatchingSkillSuggestions 匹配技能
    IB-->>U: 显示技能建议列表
    
    U->>IB: 选择模式"pro"
    IB->>IB: handleModeSelect 设置 mode 和 reasoning_effort
    IB-->>U: 更新 UI 显示选中模式
    
    U->>IB: 选择模型"gpt-4o"
    IB->>IB: handleModelSelect 检查模型能力
    IB->>IB: 自动调整模式为 ultra
    IB-->>U: 更新模型和模式
    
    U->>IB: 点击发送按钮
    IB->>IB: handleSubmit 检查流式状态
    IB->>IB: 创建 optimistic messages
    IB->>IB: 上传文件 (如果有)
    IB->>API: uploadFiles 上传文件
    
    API-->>IB: 返回上传结果 (virtual_path)
    IB->>IB: 更新 optimistic messages 为 uploaded 状态
    
    IB->>API: POST /runs (包含消息和 context)
    API->>LG: thread.submit()
    LG-->>API: 开始流式响应
    
    API-->>IB: streamSubgraphs=true 流式事件
    
    loop 流式事件处理
        IB->>IB: onLangChainEvent 处理工具调用
        IB->>IB: onUpdateEvent 处理状态更新
        IB->>IB: onCustomEvent 处理 task_running/llm_retry
        IB->>IB: 更新 messages 状态
        IB-->>U: 实时显示 AI 回复
    end
    
    API-->>IB: onFinish 流式完成
    IB->>API: 获取后续问题建议 API
    API-->>IB: 返回 followup suggestions
    IB-->>U: 显示后续问题建议
    
    U->>IB: 点击后续问题
    IB->>IB: handleFollowupClick
    IB->>IB: 替换或追加到输入框
    IB-->>U: 更新输入框内容
```

**关键交互流程:**

1. **技能建议**: 用户输入 `/` 触发技能建议匹配
2. **模式选择**: 支持 flash/thinking/pro/ultra 四种模式
3. **模型选择**: 根据模型能力自动调整模式
4. **消息发送**: 创建乐观消息 → 上传文件 → 提交 API → 流式响应
5. **流式处理**: 实时显示 AI 回复，处理工具调用和状态更新
6. **后续建议**: 流式完成后获取并显示后续问题建议

---

## 5. 消息渲染组件图

```mermaid
graph TB
    A[Messages 列表容器] --> B[MessageItem 消息项]
    
    B --> C{消息类型}
    C -->|human| D[UserMessage 用户消息]
    C -->|ai| E[AIMessage AI 消息]
    C -->|system| F[SystemMessage 系统消息]
    C -->|tool| G[ToolMessage 工具消息]
    
    D --> D1[TextContent 文本内容]
    D --> D2[FileContent 文件内容]
    
    E --> E1[ThinkingBlock 思考块]
    E --> E2[TextContent 文本内容]
    E --> E3[CodeBlock 代码块]
    E --> E4[Artifact 工件展示]
    
    G --> G1[ToolCall 工具调用]
    G --> G2[ToolResult 工具结果]
    
    subgraph "消息工具"
        H[CopyButton 复制按钮]
        I[ThumbDown 反馈按钮]
        J[Citation 引用展示]
    end
    
    D --> H
    E --> H
    E --> I
    G --> J
```

**消息类型说明:**

| 消息类型 | 组件 | 功能 |
|----------|------|------|
| human | `UserMessage` | 用户输入的消息，包含文本和文件 |
| ai | `AIMessage` | AI 回复，包含思考块、文本、代码和工件 |
| system | `SystemMessage` | 系统消息，通常隐藏显示 |
| tool | `ToolMessage` | 工具调用结果消息 |

---

## 6. 状态管理架构

```mermaid
graph TB
    subgraph "React Query 状态管理"
        A[TanStack Query 核心]
        
        A --> B[Thread Queries]
        A --> C[Run Queries]
        A --> D[Token Usage]
        A --> E[Search Cache]
    end

    subgraph "Hooks 层"
        B --> F[useThreads 线程搜索]
        B --> G[useInfiniteThreads 无限滚动]
        B --> H[useThreadHistory 历史加载]
        B --> I[useThreadStream 流式响应]
        
        C --> J[useThreadRuns 运行列表]
        C --> K[useRunDetail 运行详情]
        
        D --> L[useThreadTokenUsage Token 使用]
        
        B --> M[useDeleteThread 删除线程]
        B --> N[useRenameThread 重命名]
    end

    subgraph "状态数据"
        O[AgentThread 线程对象]
        P[Run 运行对象]
        Q[Message 消息数组]
        R[ThreadState 线程状态]
    end

    subgraph "缓存管理"
        S[Search Cache 搜索缓存]
        T[Infinite Cache 无限滚动缓存]
        U[Optimistic Messages 乐观消息]
    end

    F --> O
    G --> O
    H --> O
    I --> O
    
    J --> P
    K --> P
    
    H --> Q
    I --> Q
    
    I --> R
    
    I --> U
    F --> S
    G --> T
```

**状态管理特点:**

- **React Query**: 使用 TanStack Query 进行服务端状态管理
- **Hooks 分层**: 提供多个专用 hooks 处理不同场景
- **缓存优化**: 搜索缓存和无限滚动缓存协同工作
- **乐观更新**: 在服务器响应前显示乐观消息提升体验

---

## 7. 流式响应处理流程

```mermaid
sequenceDiagram
    participant FE as Frontend Hooks
    participant LG as LangGraph SDK
    participant BE as Backend Server
    participant DB as Database
    
    FE->>LG: useStream({threadId, assistantId})
    LG->>BE: 建立 SSE 连接
    
    alt 新线程
        BE->>DB: 创建新 thread
        DB-->>BE: thread_id
        BE-->>FE: onCreated(meta)
        FE->>FE: upsertThreadInSearchCache
        FE->>FE: upsertThreadInInfiniteCache
    end
    
    FE->>LG: thread.submit(messages)
    LG->>BE: POST /runs (streamSubgraphs=true)
    
    loop 流式事件循环
        BE-->>FE: LangChainEvent (on_tool_start)
        FE->>FE: onLangChainEvent 处理工具调用
        FE->>FE: 更新 UI 显示工具执行
        
        BE-->>FE: UpdateEvent (state update)
        FE->>FE: onUpdateEvent 处理状态更新
        FE->>FE: 提取 summarization 消息
        FE->>FE: appendMessages 追加消息
        
        BE-->>FE: CustomEvent (task_running)
        FE->>FE: onCustomEvent 更新 subtask
        FE->>FE: 显示任务进度
        
        BE-->>FE: CustomEvent (llm_retry)
        FE->>FE: onCustomEvent 显示重试提示
    end
    
    BE-->>FE: onFinish(state)
    FE->>FE: listeners.onFinish 调用回调
    FE->>FE: queryClient.invalidateQueries
    FE->>FE: 清理 optimistic messages
    
    FE->>BE: 获取后续问题建议
    BE-->>FE: 返回 followup suggestions
    FE->>FE: 显示建议按钮
```

**流式处理关键点:**

1. **连接建立**: 使用 LangGraph SDK 的 `useStream` Hook 建立 SSE 连接
2. **事件处理**: 处理 LangChainEvent、UpdateEvent、CustomEvent 三种事件
3. **消息合并**: 合并历史消息、流式消息和乐观消息
4. **去重机制**: 基于 `messageIdentity` 进行消息去重
5. **缓存更新**: 流式完成后 invalidation 查询缓存

---

## 8. 线程生命周期管理

```mermaid
stateDiagram-v2
    [*] --> New: 用户进入 workspace
    New --> Loading: 加载历史线程
    Loading --> Active: 加载完成
    
    Active --> Streaming: 发送消息
    Streaming --> Processing: 服务器处理中
    Processing --> Active: 流式完成
    
    Active --> Deleting: 删除线程
    Deleting --> [*]: 删除成功
    
    Active --> Renaming: 重命名线程
    Renaming --> Active: 重命名完成
    
    Streaming --> Error: 发生错误
    Error --> Active: 错误处理
    
    note right of New
        创建新的线程对象
        optimisticThreadId = null
    end note
    
    note right of Loading
        调用 useThreadHistory
        分页加载消息历史
    end note
    
    note right of Active
        显示消息列表
        监听流式事件
    end note
    
    note right of Streaming
        创建 optimistic messages
        上传文件
        提交到服务器
    end note
    
    note right of Error
        清空 optimistic messages
        显示错误提示
        清理状态
    end note
```

**线程状态:**

| 状态 | 描述 | 关键操作 |
|------|------|----------|
| New | 新建线程 | 创建线程对象，准备发送消息 |
| Loading | 加载历史 | 分页加载消息历史 |
| Active | 活跃状态 | 显示消息，监听事件 |
| Streaming | 流式发送 | 上传文件，提交 API |
| Processing | 处理中 | 服务器处理，流式返回 |
| Error | 错误状态 | 错误提示，状态清理 |
| Deleting | 删除中 | 删除线程，清理缓存 |
| Renaming | 重命名中 | 更新线程标题 |

---

## 9. 文件上传流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant IB as InputBox
    participant FS as File System
    participant API as Upload API
    participant BE as Backend
    
    U->>IB: 选择文件
    IB->>IB: 创建 PromptInputFilePart
    IB->>IB: 设置 uploading 状态
    
    IB->>IB: handleSubmit 触发上传
    IB->>FS: 转换 FilePart 为 File 对象
    FS-->>IB: 返回 File 对象
    
    loop 上传每个文件
        IB->>API: POST /uploads (file)
        API->>BE: 接收文件
        BE->>BE: 保存到临时目录
        BE->>BE: 创建虚拟路径 /mnt/user-data/xxx
        API-->>IB: 返回 UploadedFileInfo
        
        IB->>IB: 更新 optimistic message
        IB->>IB: 状态改为 uploaded
        IB->>IB: 添加 virtual_path
    end
    
    IB->>BE: POST /runs (包含 files metadata)
    BE->>BE: 验证文件路径
    BE->>BE: 映射到 Sandbox 路径
    BE-->>IB: 开始流式处理
```

**文件上传步骤:**

1. **选择文件**: 用户选择文件，创建 `PromptInputFilePart`
2. **转换文件**: 将 FilePart 转换为浏览器 File 对象
3. **上传文件**: 调用 Upload API，返回 `UploadedFileInfo`
4. **更新状态**: 将文件状态从 `uploading` 改为 `uploaded`
5. **提交消息**: 将文件 metadata 包含在消息中提交
6. **后端处理**: 后端验证并映射到 Sandbox 虚拟路径

---

## 10. 技能建议系统

```mermaid
graph TB
    A[用户输入框] --> B{输入检测}
    
    B -->|输入 '/' | C[触发技能搜索]
    B -->|输入其他 | D[隐藏技能列表]
    
    C --> E[getMatchingSkillSuggestions]
    E --> F{匹配模式}
    
    F -->|精确匹配 | G[显示匹配技能]
    F -->|前缀匹配 | H[显示相关技能]
    F -->|无匹配 | I[显示所有技能]
    
    G --> J[渲染技能列表]
    H --> J
    I --> J
    
    J --> K{用户操作}
    
    K -->|点击技能 | L[applySkillSuggestion]
    K -->|键盘上下 | M[高亮选中]
    K -->|Enter/Tab | N[应用技能]
    K -->|Escape | O[关闭列表]
    
    L --> P[设置光标位置]
    L --> Q[插入技能文本]
    L --> R[关闭技能列表]
    
    M --> S[更新 selectedIndex]
    S --> J
    
    N --> L
    O --> D
    
    style A fill:#e1f5ff
    style C fill:#fff3e0
    style J fill:#e8f5e9
    style L fill:#fce4ec
```

**技能建议功能:**

- **触发机制**: 输入 `/` 触发技能搜索
- **匹配模式**: 支持精确匹配、前缀匹配和全量显示
- **键盘导航**: 支持上下箭头选择，Enter/Tab 应用，Escape 关闭
- **光标定位**: 应用技能后自动定位光标到合适位置
- **实时过滤**: 根据输入实时过滤技能列表

---

## 11. 组件依赖关系图

```mermaid
graph TB
    subgraph "页面层"
        A[LandingPage]
        B[ChatPage]
        C[SettingsPage]
    end
    
    subgraph "布局组件"
        D[WorkspaceContainer]
        E[WorkspaceHeader]
        F[WorkspaceBody]
        G[WorkspaceSidebar]
    end
    
    subgraph "核心功能组件"
        H[InputBox]
        I[Messages]
        J[Artifacts]
        K[TodoList]
        L[Channels]
    end
    
    subgraph "消息子组件"
        M[UserMessage]
        N[AIMessage]
        O[ToolMessage]
        P[ThinkingBlock]
        Q[CodeBlock]
    end
    
    subgraph "UI 组件"
        R[Button]
        S[DropdownMenu]
        T[Dialog]
        U[Tooltip]
        V[Badge]
    end
    
    subgraph "Hooks 层"
        W[useThreadStream]
        X[useThreadHistory]
        Y[useThreads]
        Z[useDeleteThread]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    F --> G
    F --> H
    F --> I
    F --> J
    F --> K
    F --> L

    I --> M
    I --> N
    I --> O
    N --> P
    N --> Q

    H --> R
    H --> S
    C --> T
    I --> U
    J --> V
    
    H --> W
    I --> W
    I --> X
    G --> Y
    G --> Z
    
    style A fill:#e1f5ff
    style B fill:#e1f5ff
    style C fill:#e1f5ff
    style D fill:#fff3e0
    style H fill:#e8f5e9
    style I fill:#e8f5e9
    style W fill:#fce4ec
```

**组件依赖说明:**

- **页面层**: 顶层页面组件，作为应用入口
- **布局组件**: 提供整体布局结构
- **核心功能组件**: 工作区的核心功能实现
- **消息子组件**: 消息类型的细分组件
- **UI 组件**: 基础 UI 组件库
- **Hooks 层**: 状态管理和数据获取

---

## 技术栈总结

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | Next.js | 16 |
| 运行时 | React | 19 |
| 样式 | Tailwind CSS | 4 |
| UI 组件 | Shadcn UI | 最新 |
| 状态管理 | TanStack Query | 最新 |
| 语言 | TypeScript | 最新 |
| 国际化 | next-intl | 最新 |
| 客户端 | LangGraph SDK | 最新 |

---

## 关键设计模式

1. **乐观更新模式**: 在服务器响应前显示用户输入
2. **消息去重机制**: 基于 `messageIdentity` 的唯一性识别
3. **流式响应处理**: 使用 LangGraph SDK 的 `useStream` Hook
4. **无限滚动加载**: 使用 React Query 的无限查询
5. **技能建议系统**: 基于输入触发的实时建议
6. **文件上传优化**: 上传前显示乐观状态，完成后更新路径
