# DeerFlow 配置与技能系统流程图

本文档包含 DeerFlow 项目的配置系统、技能系统、工具系统、上传系统、频道系统、模型系统、消息处理系统、认证授权系统、监控日志系统、部署架构等补充流程图。

---

## 1. 配置系统架构

### 1.1 配置加载流程

```mermaid
graph TB
    Start([开始]) --> LoadConfig[加载配置文件<br/>config.yaml]
    LoadConfig --> CheckEnv{检查环境变量}
    CheckEnv -->|存在 | OverrideConfig[覆盖配置项]
    CheckEnv -->|不存在 | SkipOverride[跳过覆盖]
    OverrideConfig --> ValidateConfig[验证配置]
    SkipOverride --> ValidateConfig
    ValidateConfig --> CheckModel{检查模型配置}
    CheckModel -->|未配置 | LoadDefault[加载默认模型]
    CheckModel -->|已配置 | LoadCustom[加载自定义模型]
    LoadDefault --> InitSandbox[初始化 Sandbox]
    LoadCustom --> InitSandbox
    InitSandbox --> InitSkills[初始化 Skills]
    InitSkills --> InitTools[初始化工具系统]
    InitTools --> InitMiddleware[初始化中间件]
    InitMiddleware --> BuildAgent[构建 Lead Agent]
    BuildAgent --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style LoadConfig fill:#fff3cd
    style ValidateConfig fill:#f8d7da
    style BuildAgent fill:#d1ecf1
```

### 1.2 配置结构

```mermaid
graph TB
    Config[配置根节点]
    
    Config --> Server[服务器配置]
    Config --> Model[模型配置]
    Config --> Sandbox[Sandbox 配置]
    Config --> Skills[Skills 配置]
    Config --> Tools[工具配置]
    Config --> Middleware[中间件配置]
    Config --> Memory[记忆配置]
    Config --> Upload[上传配置]
    Config --> Features[功能特性]
    
    Server --> ServerHost[主机地址]
    Server --> ServerPort[端口]
    Server --> ServerWorkers[工作进程数]
    
    Model --> DefaultModel[默认模型]
    Model --> ModelList[模型列表]
    Model --> ProviderConfig[提供商配置]
    
    Sandbox --> SandboxMode[Sandbox 模式<br/>docker/local]
    Sandbox --> SandboxImage[Docker 镜像]
    Sandbox --> SandboxTimeout[超时设置]
    
    Skills --> SkillList[技能列表]
    Skills --> SkillAutoLoad[自动加载策略]
    
    Tools --> ToolList[工具列表]
    Tools --> ToolTimeout[工具超时]
    
    Middleware --> MiddlewareChain[中间件链顺序]
    Middleware --> MiddlewareConfig[各中间件配置]
    
    Memory --> MemoryEnabled[记忆启用]
    Memory --> MemoryRetention[记忆保留期]
    
    Upload --> UploadDir[上传目录]
    Upload --> UploadMaxSize[最大文件大小]
    
    Features --> FeatureFlags[功能标志]
    Features --> Experimental[实验性功能]
    
    style Config fill:#e1f5ff
    style Server fill:#d1ecf1
    style Model fill:#d1ecf1
    style Sandbox fill:#d1ecf1
    style Skills fill:#d1ecf1
    style Tools fill:#d1ecf1
    style Middleware fill:#d1ecf1
    style Memory fill:#d1ecf1
    style Upload fill:#d1ecf1
    style Features fill:#d1ecf1
```

### 1.3 配置热重载

```mermaid
sequenceDiagram
    participant User as 用户
    participant File as 配置文件
    participant Watcher as 文件监听器
    participant Loader as 配置加载器
    participant Agent as Lead Agent
    participant Cache as 配置缓存
    
    User->>File: 修改配置文件
    File-->>Watcher: 文件变更事件
    Watcher->>Loader: 触发重载
    Loader->>Cache: 清除旧配置
    Loader->>File: 读取新配置
    Loader->>Loader: 验证配置
    alt 配置有效
        Loader->>Cache: 存储新配置
        Loader->>Agent: 重新构建 Agent
        Agent-->>Cache: 返回新实例
        Cache-->>Loader: 重载完成
        Loader-->>Watcher: 重载成功
    else 配置无效
        Loader-->>Watcher: 重载失败
        Watcher-->>User: 错误提示
    end
    
    Note over User,Cache: 系统无缝切换新配置
```

---

## 2. Skills 系统

### 2.1 Skills 加载机制

```mermaid
graph TB
    Start([启动]) --> LoadConfig[读取 Skills 配置]
    LoadConfig --> CheckAutoLoad{检查自动加载策略}
    
    CheckAutoLoad -->|All| LoadAll[加载所有 Skills]
    CheckAutoLoad -->|OnDemand| CheckContext[检查上下文]
    CheckAutoLoad -->|Manual| WaitTrigger[等待用户触发]
    
    LoadAll --> InitAllSkills[初始化所有 Skill 实例]
    CheckContext --> MatchSkill{匹配相关 Skill}
    MatchSkill -->|匹配 | LoadSkill[加载对应 Skill]
    MatchSkill -->|不匹配 | SkipLoad[跳过加载]
    WaitTrigger --> UserAction[用户操作]
    UserAction --> TriggerSkill[触发 Skill]
    TriggerSkill --> LoadSkill
    
    InitAllSkills --> RegisterSkill[注册 Skill]
    LoadSkill --> RegisterSkill
    SkipLoad --> CheckMore{检查更多 Skill}
    
    RegisterSkill --> CheckMore
    CheckMore -->|有更多 | CheckAutoLoad
    CheckMore -->|无更多 | BuildRegistry[构建 Skill 注册表]
    
    BuildRegistry --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style LoadConfig fill:#fff3cd
    style RegisterSkill fill:#d1ecf1
    style BuildRegistry fill:#d1ecf1
```

### 2.2 Skill 发现与匹配

```mermaid
graph LR
    Input[用户输入] --> ParseInput[解析输入]
    ParseInput --> ExtractIntent[提取意图]
    ExtractIntent --> SearchSkills[搜索相关 Skills]
    
    SearchSkills --> MatchName{名称匹配}
    MatchName -->|精确 | ScoreSkill[评分]
    MatchName -->|模糊 | SemanticMatch[语义匹配]
    SemanticMatch --> ScoreSkill
    
    ScoreSkill --> CheckContext{上下文匹配}
    CheckContext -->|满足 | CheckPermissions{权限检查}
    CheckContext -->|不满足 | SkipSkill[跳过]
    
    CheckPermissions -->|允许 | AddToPool[加入候选池]
    CheckPermissions -->|拒绝 | SkipSkill
    
    AddToPool --> SortSkills[排序 Skills]
    SortSkills --> SelectTop[选择 Top Skills]
    SelectTop --> InjectToContext[注入到上下文]
    InjectToContext --> Ready([就绪])
    
    style Input fill:#e1f5ff
    style Ready fill:#d4edda
    style SearchSkills fill:#fff3cd
    style ScoreSkill fill:#d1ecf1
    style SelectTop fill:#d4edda
```

### 2.3 Skill 生命周期

```mermaid
stateDiagram-v2
    [*] --> Unloaded: 系统启动
    Unloaded --> Loading: 需要加载
    Loading --> Loaded: 加载完成
    Loaded --> Active: 被调用
    Active --> Idle: 调用结束
    Idle --> Loaded: 保留在内存
    Idle --> Unloaded: 内存清理
    
    Loaded --> Unloading: 标记卸载
    Unloading --> Unloaded: 卸载完成
    
    Active --> Error: 调用错误
    Error --> Loaded: 恢复
    
    Unloaded --> Loading: 按需加载
    Loading --> Error: 加载失败
    Error --> Unloaded: 回滚
    
    note right of Loaded: 已加载到内存<br/>可快速调用
    note right of Active: 正在执行中
    note right of Idle: 空闲状态<br/>可快速恢复
    note right of Unloaded: 未加载<br/>节省内存
```

### 2.4 Skill 注册与发现

```mermaid
graph TB
    Start([开始]) --> ScanDir[扫描 Skills 目录]
    ScanDir --> ParseManifest[解析 manifest.json]
    ParseManifest --> ValidateManifest{验证清单}
    
    ValidateManifest -->|有效 | ExtractInfo[提取技能信息]
    ValidateManifest -->|无效 | LogError[记录错误]
    LogError --> SkipSkill[跳过该 Skill]
    
    ExtractInfo --> RegisterSkill[注册到注册表]
    SkipSkill --> CheckMore{检查更多}
    RegisterSkill --> CheckMore
    
    CheckMore -->|有更多 | ScanDir
    CheckMore -->|无更多 | BuildIndex[构建索引]
    
    BuildIndex --> IndexName[按名称索引]
    IndexName --> IndexTag[按标签索引]
    IndexTag --> IndexCategory[按分类索引]
    IndexCategory --> IndexCapability[按能力索引]
    
    IndexCapability --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style ScanDir fill:#fff3cd
    style BuildIndex fill:#d1ecf1
    style IndexName fill:#d1ecf1
    style IndexTag fill:#d1ecf1
    style IndexCategory fill:#d1ecf1
    style IndexCapability fill:#d1ecf1
```

---

## 3. 工具系统

### 3.1 工具注册与发现

```mermaid
graph TB
    Start([启动]) --> ScanTools[扫描工具目录]
    ScanTools --> LoadBuiltins[加载内置工具]
    ScanTools --> LoadCustom[加载自定义工具]
    
    LoadBuiltins --> ParseTool[解析工具定义]
    LoadCustom --> ParseTool
    
    ParseTool --> ValidateTool{验证工具}
    ValidateTool -->|有效 | RegisterTool[注册工具]
    ValidateTool -->|无效 | LogError[记录错误]
    
    RegisterTool --> AddToRegistry[添加到工具注册表]
    LogError --> CheckMore{检查更多}
    AddToRegistry --> CheckMore
    
    CheckMore -->|有更多 | ScanTools
    CheckMore -->|无更多 | BuildRegistry[构建完整注册表]
    
    BuildRegistry --> IndexTools[建立工具索引]
    IndexTools --> AutoComplete[生成自动完成]
    AutoComplete --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style ScanTools fill:#fff3cd
    style BuildRegistry fill:#d1ecf1
    style IndexTools fill:#d1ecf1
```

### 3.2 工具调用流程

```mermaid
sequenceDiagram
    participant Agent as Lead Agent
    participant ToolRegistry as 工具注册表
    participant Tool as 工具实例
    participant Sandbox as Sandbox
    participant Result as 结果处理器
    
    Agent->>ToolRegistry: 查找工具
    ToolRegistry-->>Agent: 返回工具定义
    Agent->>Tool: 调用工具
    Tool->>Tool: 参数验证
    alt 参数有效
        Tool->>Sandbox: 在沙盒中执行
        Sandbox->>Sandbox: 执行工具逻辑
        Sandbox-->>Tool: 返回结果
        Tool->>Result: 处理结果
        Result-->>Agent: 返回工具结果
    else 参数无效
        Tool-->>Agent: 返回错误
    end
    
    Agent->>Agent: 将结果注入上下文
    Note over Agent,Result: 工具调用完成
```

### 3.3 工具错误处理

```mermaid
graph TB
    Start([工具调用开始]) --> ExecuteTool[执行工具]
    ExecuteTool --> CheckError{检查错误}
    
    CheckError -->|无错误 | ProcessResult[处理结果]
    CheckError -->|参数错误 | ValidateParams[验证参数]
    CheckError -->|执行错误 | RetryTool{是否可重试}
    CheckError -->|超时错误 | TimeoutHandler[超时处理]
    
    ValidateParams --> FixParams[修复参数]
    FixParams --> ExecuteTool
    
    RetryTool -->|是 | RetryExecute[重新执行]
    RetryTool -->|否 | ErrorHandler[错误处理]
    
    RetryExecute --> CheckError
    TimeoutHandler --> ErrorHandler
    ErrorHandler --> ReportError[报告错误]
    
    ProcessResult --> InjectContext[注入上下文]
    ReportError --> InjectContext
    
    InjectContext --> End([结束])
    
    style Start fill:#e1f5ff
    style End fill:#d4edda
    style ExecuteTool fill:#fff3cd
    style CheckError fill:#f8d7da
    style ProcessResult fill:#d4edda
```

---

## 4. 上传系统

### 4.1 文件上传流程

```mermaid
graph TB
    Start([开始上传]) --> InitUpload[初始化上传]
    InitUpload --> CheckFile{检查文件}
    
    CheckFile -->|大小检查 | ValidateSize{文件大小}
    CheckFile -->|类型检查 | ValidateType{文件类型}
    CheckFile -->|病毒扫描 | ScanVirus[病毒扫描]
    
    ValidateSize -->|超过限制 | RejectUpload[拒绝上传]
    ValidateSize -->|符合 | CheckType{类型检查}
    CheckType -->|不支持 | RejectUpload
    CheckType -->|支持 | ScanVirus
    
    ScanVirus -->|发现病毒 | RejectUpload
    ScanVirus -->|干净 | CreateTemp[创建临时文件]
    
    CreateTemp --> StreamUpload[流式上传]
    StreamUpload --> CalculateHash[计算文件哈希]
    CalculateHash --> DedupCheck{去重检查}
    
    DedupCheck -->|已存在 | ReturnExisting[返回现有文件]
    DedupCheck -->|新文件 | SaveFile[保存文件]
    
    SaveFile --> UpdateMetadata[更新元数据]
    UpdateMetadata --> GeneratePath[生成访问路径]
    GeneratePath --> NotifyUpload[通知上传完成]
    
    NotifyUpload --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style CheckFile fill:#fff3cd
    style SaveFile fill:#d1ecf1
    style GeneratePath fill:#d1ecf1
```

### 4.2 虚拟文件系统

```mermaid
graph TB
    VirtualFS[虚拟文件系统]
    
    VirtualFS --> MntUserdata[/mnt/user-data]
    VirtualFS --> MntSkills[/mnt/skills]
    VirtualFS --> MntWorkspace[/mnt/acp-workspace]
    
    MntUserdata --> UserFiles[用户文件]
    MntUserdata --> Uploads[上传目录]
    
    MntSkills --> SkillFiles[Skill 文件]
    MntSkills --> Templates[模板文件]
    
    MntWorkspace --> ProjectFiles[项目文件]
    MntWorkspace --> Cache[缓存文件]
    
    UserFiles --> MapPath[路径映射]
    Uploads --> MapPath
    SkillFiles --> MapPath
    Templates --> MapPath
    ProjectFiles --> MapPath
    Cache --> MapPath
    
    MapPath --> RealFS[真实文件系统]
    
    style VirtualFS fill:#e1f5ff
    style MntUserdata fill:#d1ecf1
    style MntSkills fill:#d1ecf1
    style MntWorkspace fill:#d1ecf1
    style RealFS fill:#d4edda
```

---

## 5. 频道系统

### 5.1 频道创建与管理

```mermaid
graph TB
    Start([开始]) --> InitChannel[初始化频道]
    InitChannel --> CreateMetadata[创建元数据]
    CreateMetadata --> GenerateID[生成频道 ID]
    GenerateID --> SaveMetadata[保存元数据]
    
    SaveMetadata --> Subscribe[订阅频道]
    Subscribe --> ConnectWebSocket[建立 WebSocket 连接]
    ConnectWebSocket --> Ready([就绪])
    
    Ready --> ReceiveMessage[接收消息]
    ReceiveMessage --> ProcessMessage[处理消息]
    ProcessMessage --> Broadcast[广播消息]
    Broadcast --> Ready
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style InitChannel fill:#fff3cd
    style ConnectWebSocket fill:#d1ecf1
```

### 5.2 频道消息流转

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant Channel as 频道服务
    participant Storage as 存储层
    participant WebSocket as WebSocket 服务
    
    Client->>Channel: 发送消息
    Channel->>Storage: 保存消息
    Storage-->>Channel: 保存成功
    Channel->>Channel: 处理消息
    Channel->>WebSocket: 广播消息
    WebSocket-->>Client: 推送消息
    Note over Client,WebSocket: 消息实时同步
```

---

## 6. 模型系统

### 6.1 模型选择流程

```mermaid
graph TB
    Start([开始]) --> GetRequest[获取请求]
    GetRequest --> CheckModel{指定模型}
    
    CheckModel -->|已指定 | UseModel[使用指定模型]
    CheckModel -->|未指定 | AutoSelect[自动选择]
    
    AutoSelect --> CheckThread{检查线程历史}
    CheckThread -->|有历史 | UseThreadModel[使用线程模型]
    CheckThread -->|无历史 | CheckDefault[检查默认模型]
    
    CheckDefault -->|有默认 | UseDefault[使用默认模型]
    CheckDefault -->|无默认 | SelectBest[选择最佳模型]
    
    SelectBest --> CheckContext[检查上下文]
    CheckContext --> CheckCost[检查成本]
    CheckCost --> CheckSpeed[检查速度]
    CheckSpeed --> SelectModel[选择最优模型]
    
    UseModel --> ValidateModel{模型验证}
    UseThreadModel --> ValidateModel
    UseDefault --> ValidateModel
    SelectModel --> ValidateModel
    
    ValidateModel -->|有效 | Ready([就绪])
    ValidateModel -->|无效 | SelectModel
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style AutoSelect fill:#fff3cd
    style SelectBest fill:#d1ecf1
```

### 6.2 模型路由

```mermaid
graph LR
    Request[请求] --> Router[路由器]
    
    Router --> ProviderA[提供商 A]
    Router --> ProviderB[提供商 B]
    Router --> ProviderC[提供商 C]
    
    ProviderA --> ModelA1[模型 A1]
    ProviderA --> ModelA2[模型 A2]
    ProviderB --> ModelB1[模型 B1]
    ProviderB --> ModelB2[模型 B2]
    ProviderC --> ModelC1[模型 C1]
    ProviderC --> ModelC2[模型 C2]
    
    style Request fill:#e1f5ff
    style Router fill:#fff3cd
    style ProviderA fill:#d1ecf1
    style ProviderB fill:#d1ecf1
    style ProviderC fill:#d1ecf1
```

---

## 7. 消息处理系统

### 7.1 消息处理流程

```mermaid
graph TB
    Start([消息到达]) --> ParseMessage[解析消息]
    ParseMessage --> ValidateMessage{验证消息}
    
    ValidateMessage -->|有效 | ProcessMessage[处理消息]
    ValidateMessage -->|无效 | RejectMessage[拒绝消息]
    
    ProcessMessage --> ExtractContent[提取内容]
    ExtractContent --> DetectType{检测类型}
    
    DetectType -->|文本 | TextProcess[文本处理]
    DetectType -->|图片 | ImageProcess[图片处理]
    DetectType -->|文件 | FileProcess[文件处理]
    DetectType -->|工具调用 | ToolProcess[工具处理]
    
    TextProcess --> EnrichMessage[增强消息]
    ImageProcess --> EnrichMessage
    FileProcess --> EnrichMessage
    ToolProcess --> EnrichMessage
    
    EnrichMessage --> StoreMessage[存储消息]
    StoreMessage --> BroadcastMessage[广播消息]
    BroadcastMessage --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style ProcessMessage fill:#fff3cd
    style EnrichMessage fill:#d1ecf1
    style StoreMessage fill:#d1ecf1
```

### 7.2 消息去重与合并

```mermaid
graph TB
    Start([消息到达]) --> GenerateID[生成消息 ID]
    GenerateID --> CheckCache{检查缓存}
    
    CheckCache -->|新消息 | StoreMessage[存储消息]
    CheckCache -->|重复 | SkipMessage[跳过消息]
    CheckCache -->|部分匹配 | MergeMessage[合并消息]
    
    StoreMessage --> UpdateCache[更新缓存]
    SkipMessage --> End([结束])
    MergeMessage --> UpdateCache
    
    UpdateCache --> Notify[通知更新]
    Notify --> End
    
    style Start fill:#e1f5ff
    style End fill:#d4edda
    style CheckCache fill:#fff3cd
    style MergeMessage fill:#d1ecf1
```

---

## 8. 认证与授权系统

### 8.1 认证流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant Auth as 认证服务
    participant UserDB as 用户数据库
    participant Token as Token 服务
    
    Client->>Auth: 提交凭证
    Auth->>UserDB: 验证用户
    UserDB-->>Auth: 返回用户信息
    Auth->>Auth: 验证凭证
    alt 验证成功
        Auth->>Token: 生成 Token
        Token-->>Auth: 返回 Token
        Auth-->>Client: 返回 Token
    else 验证失败
        Auth-->>Client: 返回错误
    end
    
    Note over Client,Token: 认证完成
```

### 8.2 授权流程

```mermaid
graph TB
    Start([请求到达]) --> ExtractToken[提取 Token]
    ExtractToken --> ValidateToken{验证 Token}
    
    ValidateToken -->|有效 | ExtractClaims[提取声明]
    ValidateToken -->|无效 | RejectRequest[拒绝请求]
    
    ExtractClaims --> CheckPermission{检查权限}
    CheckPermission -->|有权限 | AllowRequest[允许请求]
    CheckPermission -->|无权限 | DenyRequest[拒绝请求]
    
    AllowRequest --> ProcessRequest[处理请求]
    DenyRequest --> LogAccess[记录访问]
    RejectRequest --> LogAccess
    
    LogAccess --> End([结束])
    
    style Start fill:#e1f5ff
    style End fill:#d4edda
    style ValidateToken fill:#fff3cd
    style CheckPermission fill:#f8d7da
    style AllowRequest fill:#d4edda
```

---

## 9. 监控与日志系统

### 9.1 日志收集流程

```mermaid
graph TB
    Start([服务运行]) --> GenerateLog[生成日志]
    GenerateLog --> FormatLog[格式化日志]
    FormatLog --> TagLog[添加标签]
    TagLog --> RouteLog{路由日志}
    
    RouteLog -->|错误 | ErrorLog[错误日志]
    RouteLog -->|警告 | WarnLog[警告日志]
    RouteLog -->|信息 | InfoLog[信息日志]
    RouteLog -->|调试 | DebugLog[调试日志]
    
    ErrorLog --> StoreLog[存储日志]
    WarnLog --> StoreLog
    InfoLog --> StoreLog
    DebugLog --> StoreLog
    
    StoreLog --> IndexLog[索引日志]
    IndexLog --> Ready([就绪])
    
    style Start fill:#e1f5ff
    style Ready fill:#d4edda
    style GenerateLog fill:#fff3cd
    style RouteLog fill:#f8d7da
    style StoreLog fill:#d1ecf1
```

### 9.2 监控指标收集

```mermaid
graph LR
    Collector[监控收集器]
    
    Collector --> MetricA[请求指标]
    Collector --> MetricB[延迟指标]
    Collector --> MetricC[错误指标]
    Collector --> MetricD[资源指标]
    
    MetricA --> StoreMetrics[存储指标]
    MetricB --> StoreMetrics
    MetricC --> StoreMetrics
    MetricD --> StoreMetrics
    
    StoreMetrics --> Dashboard[监控面板]
    StoreMetrics --> Alerting[告警系统]
    
    style Collector fill:#e1f5ff
    style StoreMetrics fill:#d1ecf1
    style Dashboard fill:#d4edda
    style Alerting fill:#fff3cd
```

---

## 10. 部署架构

### 10.1 容器化部署

```mermaid
graph TB
    Docker[Docker 容器]
    
    Docker --> Backend[后端容器]
    Docker --> Frontend[前端容器]
    Docker --> Database[数据库容器]
    Docker --> Cache[缓存容器]
    Docker --> Queue[消息队列容器]
    
    Backend --> API[API 服务]
    Backend --> Worker[后台任务]
    
    Frontend --> Web[Web 服务]
    
    Database --> DBInstance[数据库实例]
    Cache --> CacheInstance[缓存实例]
    Queue --> QueueInstance[队列实例]
    
    LoadBalancer[负载均衡器]
    LoadBalancer --> Backend
    LoadBalancer --> Frontend
    
    style Docker fill:#e1f5ff
    style LoadBalancer fill:#fff3cd
    style Backend fill:#d1ecf1
    style Frontend fill:#d1ecf1
```

### 10.2 云原生部署

```mermaid
graph TB
    Cloud[云平台]
    
    Cloud --> K8s[Kubernetes 集群]
    Cloud --> Serverless[无服务器函数]
    Cloud --> ManagedDB[托管数据库]
    Cloud --> ManagedCache[托管缓存]
    
    K8s --> Namespace[命名空间]
    Namespace --> Deployment[部署]
    Namespace --> Service[服务]
    Namespace --> Ingress[入口]
    
    Deployment --> Pod[Pod]
    Pod --> Container[容器]
    
    Serverless --> Function[函数]
    Function --> Event[事件触发]
    
    ManagedDB --> DBInstance[数据库实例]
    ManagedCache --> CacheInstance[缓存实例]
    
    style Cloud fill:#e1f5ff
    style K8s fill:#d1ecf1
    style Serverless fill:#d1ecf1
    style ManagedDB fill:#d1ecf1
    style ManagedCache fill:#d1ecf1
```

---

## 总结

本章节涵盖了 DeerFlow 项目的补充系统流程图，包括：

1. **配置系统**：配置加载、结构、热重载机制
2. **Skills 系统**：加载机制、发现与匹配、生命周期、注册与发现
3. **工具系统**：注册与发现、调用流程、错误处理
4. **上传系统**：文件上传流程、虚拟文件系统
5. **频道系统**：创建与管理、消息流转
6. **模型系统**：选择流程、路由机制
7. **消息处理系统**：处理流程、去重与合并
8. **认证与授权系统**：认证流程、授权流程
9. **监控与日志系统**：日志收集、指标收集
10. **部署架构**：容器化部署、云原生部署

这些流程图与前面的架构、数据流、核心组件等流程图一起，构成了完整的 DeerFlow 项目文档体系。
