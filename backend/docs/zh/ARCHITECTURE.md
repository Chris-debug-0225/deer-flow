# 架构概述

本文档提供 DeerFlow 后端架构的全面概述。

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              客户端（浏览器）                              │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Nginx（2026 端口）                               │
│                       统一反向代理入口点                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  /api/langgraph/*  →  Gateway LangGraph 兼容运行时（8001）       │  │
│  │  /api/*            →  Gateway REST API（8001）                 │  │
│  │  /*                →  前端（3000）                              │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
          ┌───────────────────────┴───────────────────────┐
          │                                               │
          ▼                                               ▼
┌─────────────────────────────────────────────┐ ┌─────────────────────┐
│              Gateway API                    │ │     前端            │
│              （8001 端口）                   │ │    （3000 端口）     │
│                                             │ │                     │
│  - LangGraph 兼容运行/线程 API              │ │  - Next.js 应用     │
│  - 嵌入式代理运行时                         │ │  - React UI         │
│  - SSE 流式传输                            │ │  - 聊天界面         │
│  - 检查点                                  │ │                     │
│  - 模型、MCP、技能、上传、产物             │ │                     │
│  - 线程清理                                │ │                     │
└─────────────────────────────────────────────┘ └─────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         共享配置                                            │
│  ┌─────────────────────────┐  ┌────────────────────────────────────────┐ │
│  │      config.yaml        │  │      extensions_config.json            │ │
│  │  - 模型                 │  │  - MCP 服务器                          │ │
│  │  - 工具                 │  │  - 技能状态                            │ │
│  │  - 沙盒                 │  │                                        │ │
│  │  - 摘要                 │  │                                        │ │
│  └─────────────────────────┘  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

## 组件详情

### Gateway 嵌入式代理运行时

代理运行时嵌入在 FastAPI Gateway 中，基于 LangGraph 构建，用于健壮的多代理工作流编排。Nginx 将 `/api/langgraph/*` 重写为 Gateway 的本机 `/api/*` 路由，因此公共 API 与 LangGraph SDK 客户端兼容，无需运行单独的 LangGraph 服务器。

**入口点**：`packages/harness/deerflow/agents/lead_agent/agent.py:make_lead_agent`

**主要职责**：
- 代理创建和配置
- 线程状态管理
- 中间件链执行
- 工具执行编排
- SSE 流式传输实时响应

**图注册表**：`langgraph.json` 仍可用于工具、Studio 或直接 LangGraph 服务器兼容性。它不是默认的服务入口点；脚本和 Docker 部署运行 Gateway 嵌入式运行时。

```json
{
  "agent": {
    "type": "agent",
    "path": "deerflow.agents:make_lead_agent"
  }
}
```

### Gateway API

FastAPI 应用程序，提供 REST 端点以及公共 LangGraph 兼容的 `/api/langgraph/*` 运行路由。

**入口点**：`app/gateway/app.py`

**路由**：
- `models.py` - `/api/models` - 模型列表和详情
- `thread_runs.py` / `runs.py` - `/api/threads/{id}/runs`, `/api/runs/*` - LangGraph 兼容运行和流式传输
- `mcp.py` - `/api/mcp` - MCP 服务器配置
- `skills.py` - `/api/skills` - 技能管理
- `uploads.py` - `/api/threads/{id}/uploads` - 文件上传
- `threads.py` - `/api/threads/{id}` - LangGraph 删除后本地 DeerFlow 线程数据清理
- `artifacts.py` - `/api/threads/{id}/artifacts` - 产物服务
- `suggestions.py` - `/api/threads/{id}/suggestions` - 后续建议生成

Web 对话删除流程首先通过 LangGraph 兼容路由删除 Gateway 管理的线程状态，然后 Gateway `threads.py` 路由通过 `Paths.delete_thread_dir()` 删除 DeerFlow 管理的文件系统数据。

### 代理架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           make_lead_agent(config)                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            中间件链                                      │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 1. ThreadDataMiddleware  - 初始化工作区/上传/输出                 │   │
│  │ 2. UploadsMiddleware     - 处理上传文件                          │   │
│  │ 3. SandboxMiddleware     - 获取沙盒环境                          │   │
│  │ 4. SummarizationMiddleware - 上下文缩减（如果启用）              │   │
│  │ 5. TitleMiddleware       - 自动生成标题                          │   │
│  │ 6. TodoListMiddleware    - 任务跟踪（如果计划模式）              │   │
│  │ 7. ViewImageMiddleware   - 视觉模型支持                          │   │
│  │ 8. ClarificationMiddleware - 处理澄清                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              代理核心                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │      模型        │  │      工具        │  │    系统提示          │   │
│  │  （来自工厂）   │  │  （配置 +        │  │  （带技能）          │   │
│  │                  │  │   MCP + 内置）  │  │                      │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 线程状态

`ThreadState` 使用附加字段扩展 LangGraph 的 `AgentState`：

```python
class ThreadState(AgentState):
    # 来自 AgentState 的核心状态
    messages: list[BaseMessage]

    # DeerFlow 扩展
    sandbox: dict             # 沙盒环境信息
    artifacts: list[str]      # 生成的文件路径
    thread_data: dict         # {workspace, uploads, outputs} 路径
    title: str | None         # 自动生成的对话标题
    todos: list[dict]         # 任务跟踪（计划模式）
    viewed_images: dict       # 视觉模型图像数据
```

### 沙盒系统

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           沙盒架构                                       │
└─────────────────────────────────────────────────────────────────────────┘

                      ┌─────────────────────────┐
                      │    SandboxProvider      │ （抽象）
                      │  - acquire()            │
                      │  - get()                │
                      │  - release()            │
                      └────────────┬────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                                         │
              ▼                                         ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│  LocalSandboxProvider   │              │  AioSandboxProvider     │
│  (packages/harness/deerflow/sandbox/local.py) │              │  (packages/harness/deerflow/community/)       │
│                         │              │                         │
│  - 单例实例              │              │  - 基于 Docker          │
│  - 直接执行              │              │  - 隔离容器             │
│  - 开发使用              │              │  - 生产使用             │
└─────────────────────────┘              └─────────────────────────┘

                      ┌─────────────────────────┐
                      │        Sandbox          │ （抽象）
                      │  - execute_command()    │
                      │  - read_file()          │
                      │  - write_file()         │
                      │  - list_dir()           │
                      └─────────────────────────┘
```

**虚拟路径映射**：

| 虚拟路径 | 物理路径 |
|-------------|---------------|
| `/mnt/user-data/workspace` | `backend/.deer-flow/threads/{thread_id}/user-data/workspace` |
| `/mnt/user-data/uploads` | `backend/.deer-flow/threads/{thread_id}/user-data/uploads` |
| `/mnt/user-data/outputs` | `backend/.deer-flow/threads/{thread_id}/user-data/outputs` |
| `/mnt/skills` | `deer-flow/skills/` |

### 工具系统

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            工具来源                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   内置工具           │  │  配置的工具         │  │     MCP 工具        │
│  (packages/harness/deerflow/tools/)       │  │  (config.yaml)      │  │  (extensions.json)  │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│ - present_files     │  │ - web_search        │  │ - github            │
│ - ask_clarification │  │ - web_fetch         │  │ - filesystem        │
│ - view_image        │  │ - bash              │  │ - postgres          │
│                     │  │ - read_file         │  │ - brave-search      │
│                     │  │ - write_file        │  │ - puppeteer         │
│                     │  │ - str_replace       │  │ - ...               │
│                     │  │ - ls                │  │                     │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
           │                       │                       │
           └───────────────────────┴───────────────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │   get_available_tools() │
                      │   (packages/harness/deerflow/tools/__init__)  │
                      └─────────────────────────┘
```

### 模型工厂

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          模型工厂                                        │
│                     (packages/harness/deerflow/models/factory.py)                              │
└─────────────────────────────────────────────────────────────────────────┘

config.yaml:
┌─────────────────────────────────────────────────────────────────────────┐
│ models:                                                                  │
│   - name: gpt-4                                                         │
│     display_name: GPT-4                                                 │
│     use: langchain_openai:ChatOpenAI                                    │
│     model: gpt-4                                                        │
│     api_key: $OPENAI_API_KEY                                            │
│     max_tokens: 4096                                                    │
│     supports_thinking: false                                            │
│     supports_vision: true                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │   create_chat_model()   │
                      │  - name: str            │
                      │  - thinking_enabled     │
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │   resolve_class()       │
                      │  （反射系统）           │
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │   BaseChatModel         │
                      │  （LangChain 实例）     │
                      └─────────────────────────┘
```

**支持的提供商**：
- OpenAI (`langchain_openai:ChatOpenAI`)
- Anthropic (`langchain_anthropic:ChatAnthropic`)
- DeepSeek (`langchain_deepseek:ChatDeepSeek`)
- 通过 LangChain 集成的自定义提供商

### MCP 集成

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MCP 集成                                        │
│                        (packages/harness/deerflow/mcp/manager.py)                              │
└─────────────────────────────────────────────────────────────────────────┘

extensions_config.json:
┌─────────────────────────────────────────────────────────────────────────┐
│ {                                                                        │
│   "mcpServers": {                                                       │
│     "github": {                                                         │
│       "enabled": true,                                                  │
│       "type": "stdio",                                                  │
│       "command": "npx",                                                 │
│       "args": ["-y", "@modelcontextprotocol/server-github"],           │
│       "env": {"GITHUB_TOKEN": "$GITHUB_TOKEN"}                          │
│     }                                                                   │
│   }                                                                     │
│ }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │  MultiServerMCPClient   │
                      │  (langchain-mcp-adapters)│
                      └────────────┬────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌───────────┐        ┌───────────┐        ┌───────────┐
       │  stdio    │        │   SSE     │        │   HTTP    │
       │ transport │        │ transport │        │ transport │
       └───────────┘        └───────────┘        └───────────┘
```

### 技能系统

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          技能系统                                        │
│                       (packages/harness/deerflow/skills/loader.py)                             │
└─────────────────────────────────────────────────────────────────────────┘

目录结构：
┌─────────────────────────────────────────────────────────────────────────┐
│ skills/                                                                  │
│ ├── public/                        # 公共技能（已提交）                 │
│ │   ├── pdf-processing/                                                 │
│ │   │   └── SKILL.md                                                    │
│ │   ├── frontend-design/                                                │
│ │   │   └── SKILL.md                                                    │
│ │   └── ...                                                             │
│ └── custom/                        # 自定义技能（gitignored）              │
│     └── user-installed/                                                 │
│         └── SKILL.md                                                    │
└─────────────────────────────────────────────────────────────────────────┘

SKILL.md 格式：
┌─────────────────────────────────────────────────────────────────────────┐
│ ---                                                                      │
│ name: PDF 处理                                                          │
│ description: 高效处理 PDF 文档                                          │
│ license: MIT                                                            │
│ allowed-tools:                                                          │
│   - read_file                                                           │
│   - write_file                                                          │
│   - bash                                                                │
│ ---                                                                      │
│                                                                          │
│ # 技能指令                                                               │
│ 内容注入系统提示...                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 请求流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         请求流程示例                                     │
│                    用户向代理发送消息                                    │
└─────────────────────────────────────────────────────────────────────────┘

1. 客户端 → Nginx
   POST /api/langgraph/threads/{thread_id}/runs
   {"input": {"messages": [{"role": "user", "content": "你好"}]}}

2. Nginx → Gateway API (8001)
   `/api/langgraph/*` 被重写为 Gateway 的 LangGraph 兼容 `/api/*` 路由

3. Gateway 嵌入式运行时
   a. 加载/创建线程状态
   b. 执行中间件链：
      - ThreadDataMiddleware：设置路径
      - UploadsMiddleware：注入文件列表
      - SandboxMiddleware：获取沙盒
      - SummarizationMiddleware：检查令牌限制
      - TitleMiddleware：生成标题（如果需要）
      - TodoListMiddleware：加载待办事项（如果计划模式）
      - ViewImageMiddleware：处理图像
      - ClarificationMiddleware：检查澄清

   c. 执行代理：
      - 模型处理消息
      - 可能调用工具（bash、web_search 等）
      - 工具通过沙盒执行
      - 结果添加到消息

   d. 通过 SSE 流式传输响应

4. 客户端接收流式响应
```

## 数据流

### 文件上传流程

```
1. 客户端上传文件
   POST /api/threads/{thread_id}/uploads
   Content-Type: multipart/form-data

2. Gateway 接收文件
   - 验证文件
   - 存储在 .deer-flow/threads/{thread_id}/user-data/uploads/
   - 如果是文档：通过 markitdown 转换为 Markdown

3. 返回响应
   {
     "files": [{
       "filename": "doc.pdf",
       "path": ".deer-flow/.../uploads/doc.pdf",
       "virtual_path": "/mnt/user-data/uploads/doc.pdf",
       "artifact_url": "/api/threads/.../artifacts/mnt/.../doc.pdf"
     }]
   }

4. 下次代理运行
   - UploadsMiddleware 列出文件
   - 将文件列表注入消息
   - 代理可以通过 virtual_path 访问
```

### 线程清理流程

```
1. 客户端通过 LangGraph 兼容 Gateway 路由删除对话
   DELETE /api/langgraph/threads/{thread_id}

2. Web UI 跟进 Gateway 清理
   DELETE /api/threads/{thread_id}

3. Gateway 移除本地 DeerFlow 管理的文件
   - 递归删除 .deer-flow/threads/{thread_id}/
   - 缺失目录被视为无操作
   - 无效的线程 ID 在文件系统访问前被拒绝
```

### 配置重新加载

```
1. 客户端更新 MCP 配置
   PUT /api/mcp/config

2. Gateway 写入 extensions_config.json
   - 更新 mcpServers 部分
   - 文件 mtime 更改

3. MCP 管理器检测更改
   - get_cached_mcp_tools() 检查 mtime
   - 如果更改：重新初始化 MCP 客户端
   - 加载更新的服务器配置

4. 下次代理运行使用新工具
```

## 安全考虑

### 沙盒隔离

- 代理代码在沙盒边界内执行
- 本地沙盒：直接执行（仅开发）
- Docker 沙盒：容器隔离（推荐生产使用）
- 文件操作中的路径遍历防护

### API 安全

- 线程隔离：每个线程有单独的数据目录
- 文件验证：上传检查路径安全性
- 环境变量解析：配置中不存储密钥

### MCP 安全

- 每个 MCP 服务器在自己的进程中运行
- 环境变量在运行时解析
- 服务器可以独立启用/禁用

## 性能考虑

### 缓存

- MCP 工具使用文件 mtime 失效缓存
- 配置加载一次，文件更改时重新加载
- 技能在启动时解析，缓存在内存中

### 流式传输

- SSE 用于实时响应流式传输
- 减少首字节时间
- 为长时间操作启用进度可见性

### 上下文管理

- SummarizationMiddleware 在接近限制时减少上下文
- 可配置触发器：令牌、消息或比例
- 在摘要旧消息时保留最近消息

