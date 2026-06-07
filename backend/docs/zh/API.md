# API 参考

本文档提供 DeerFlow 后端 API 的完整参考。

## 概述

DeerFlow 后端公开两组 API：

1. **LangGraph 兼容 API** - 代理交互、线程和流式传输（`/api/langgraph/*`）
2. **Gateway API** - 模型、MCP、技能、上传和产物（`/api/*`）

所有 API 都通过 Nginx 反向代理在 2026 端口访问。

## LangGraph 兼容 API

基础 URL：`/api/langgraph`

公共 LangGraph 兼容 API 遵循 LangGraph SDK 约定。在统一的 nginx 部署中，Gateway 拥有 `/api/langgraph/*` 并将其路径转换为本地的 `/api/*` 运行、线程和流式传输路由。

### 线程

#### 创建线程

```http
POST /api/langgraph/threads
Content-Type: application/json
```

**请求体：**
```json
{
  "metadata": {}
}
```

**响应：**
```json
{
  "thread_id": "abc123",
  "created_at": "2024-01-15T10:30:00Z",
  "metadata": {}
}
```

#### 获取线程状态

```http
GET /api/langgraph/threads/{thread_id}/state
```

**响应：**
```json
{
  "values": {
    "messages": [...],
    "sandbox": {...},
    "artifacts": [...],
    "thread_data": {...},
    "title": "对话标题"
  },
  "next": [],
  "config": {...}
}
```

### 运行

#### 创建运行

使用输入执行代理。

```http
POST /api/langgraph/threads/{thread_id}/runs
Content-Type: application/json
```

**请求体：**
```json
{
  "input": {
    "messages": [
      {
        "role": "user",
        "content": "你好，你能帮我吗？"
      }
    ]
  },
  "config": {
    "recursion_limit": 100,
    "configurable": {
      "model_name": "gpt-4",
      "thinking_enabled": false,
      "is_plan_mode": false
    }
  },
  "stream_mode": ["values", "messages-tuple", "custom"]
}
```

**流模式兼容性：**
- 使用：`values`、`messages-tuple`、`custom`、`updates`、`events`、`debug`、`tasks`、`checkpoints`
- 不要使用：`tools`（在当前 `langgraph-api` 中已弃用/无效，会触发模式验证错误）

**递归限制：**

`config.recursion_limit` 限制 LangGraph 在单次运行中执行的图步骤数。统一 Gateway 路径在 `build_run_config` 中默认为 `100`（见 `backend/app/gateway/services.py`），这是计划模式或子代理密集型运行的更安全的起点。客户端仍可在请求体中显式设置 `recursion_limit`；如果您运行深度嵌套的子代理图，请增加它。

**可配置选项：**
- `model_name`（字符串）：覆盖默认模型
- `thinking_enabled`（布尔值）：为支持的模型启用扩展思考
- `is_plan_mode`（布尔值）：启用 TodoList 中间件进行任务跟踪

**响应：** 服务器发送事件（SSE）流

```
event: values
data: {"messages": [...], "title": "..."}

event: messages
data: {"content": "你好！我很乐意帮忙。", "role": "assistant"}

event: end
data: {}
```

#### 获取运行历史

```http
GET /api/langgraph/threads/{thread_id}/runs
```

**响应：**
```json
{
  "runs": [
    {
      "run_id": "run123",
      "status": "success",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 流式运行

实时流式传输响应。

```http
POST /api/langgraph/threads/{thread_id}/runs/stream
Content-Type: application/json
```

与创建运行相同的请求体。返回 SSE 流。

---

## Gateway API

基础 URL：`/api`

### 模型

#### 列出模型

从配置获取所有可用的 LLM 模型。

```http
GET /api/models
```

**响应：**
```json
{
  "models": [
    {
      "name": "gpt-4",
      "display_name": "GPT-4",
      "supports_thinking": false,
      "supports_vision": true
    },
    {
      "name": "claude-3-opus",
      "display_name": "Claude 3 Opus",
      "supports_thinking": false,
      "supports_vision": true
    },
    {
      "name": "deepseek-v3",
      "display_name": "DeepSeek V3",
      "supports_thinking": true,
      "supports_vision": false
    }
  ]
}
```

#### 获取模型详情

```http
GET /api/models/{model_name}
```

**响应：**
```json
{
  "name": "gpt-4",
  "display_name": "GPT-4",
  "model": "gpt-4",
  "max_tokens": 4096,
  "supports_thinking": false,
  "supports_vision": true
}
```

### MCP 配置

#### 获取 MCP 配置

获取当前 MCP 服务器配置。

```http
GET /api/mcp/config
```

**响应：**
```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "***"
      },
      "description": "GitHub 操作"
    }
  }
}
```

#### 更新 MCP 配置

更新 MCP 服务器配置。

```http
PUT /api/mcp/config
Content-Type: application/json
```

**请求体：**
```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "$GITHUB_TOKEN"
      },
      "description": "GitHub 操作"
    }
  }
}
```

**响应：**
```json
{
  "success": true,
  "message": "MCP 配置已更新"
}
```

### 技能

#### 列出技能

获取所有可用技能。

```http
GET /api/skills
```

**响应：**
```json
{
  "skills": [
    {
      "name": "pdf-processing",
      "display_name": "PDF 处理",
      "description": "高效处理 PDF 文档",
      "enabled": true,
      "license": "MIT",
      "path": "public/pdf-processing"
    },
    {
      "name": "frontend-design",
      "display_name": "前端设计",
      "description": "设计和构建前端界面",
      "enabled": false,
      "license": "MIT",
      "path": "public/frontend-design"
    }
  ]
}
```

#### 获取技能详情

```http
GET /api/skills/{skill_name}
```

**响应：**
```json
{
  "name": "pdf-processing",
  "display_name": "PDF 处理",
  "description": "高效处理 PDF 文档",
  "enabled": true,
  "license": "MIT",
  "path": "public/pdf-processing",
  "allowed_tools": ["read_file", "write_file", "bash"],
  "content": "# PDF 处理\n\n代理的指令..."
}
```

#### 启用技能

```http
POST /api/skills/{skill_name}/enable
```

**响应：**
```json
{
  "success": true,
  "message": "技能 'pdf-processing' 已启用"
}
```

#### 禁用技能

```http
POST /api/skills/{skill_name}/disable
```

**响应：**
```json
{
  "success": true,
  "message": "技能 'pdf-processing' 已禁用"
}
```

#### 安装技能

从 `.skill` 文件安装技能。

```http
POST /api/skills/install
Content-Type: multipart/form-data
```

**请求体：**
- `file`：要安装的 `.skill` 文件

**响应：**
```json
{
  "success": true,
  "message": "技能 'my-skill' 安装成功",
  "skill": {
    "name": "my-skill",
    "display_name": "我的技能",
    "path": "custom/my-skill"
  }
}
```

### 文件上传

#### 上传文件

上传一个或多个文件到线程。

```http
POST /api/threads/{thread_id}/uploads
Content-Type: multipart/form-data
```

**请求体：**
- `files`：要上传的一个或多个文件

**响应：**
```json
{
  "success": true,
  "files": [
    {
      "filename": "document.pdf",
      "size": 1234567,
      "path": ".deer-flow/threads/abc123/user-data/uploads/document.pdf",
      "virtual_path": "/mnt/user-data/uploads/document.pdf",
      "artifact_url": "/api/threads/abc123/artifacts/mnt/user-data/uploads/document.pdf",
      "markdown_file": "document.md",
      "markdown_path": ".deer-flow/threads/abc123/user-data/uploads/document.md",
      "markdown_virtual_path": "/mnt/user-data/uploads/document.md",
      "markdown_artifact_url": "/api/threads/abc123/artifacts/mnt/user-data/uploads/document.md"
    }
  ],
  "message": "成功上传 1 个文件"
}
```

**支持的文档格式**（自动转换为 Markdown）：
- PDF (`.pdf`)
- PowerPoint (`.ppt`, `.pptx`)
- Excel (`.xls`, `.xlsx`)
- Word (`.doc`, `.docx`)

#### 列出已上传文件

```http
GET /api/threads/{thread_id}/uploads/list
```

**响应：**
```json
{
  "files": [
    {
      "filename": "document.pdf",
      "size": 1234567,
      "path": ".deer-flow/threads/abc123/user-data/uploads/document.pdf",
      "virtual_path": "/mnt/user-data/uploads/document.pdf",
      "artifact_url": "/api/threads/abc123/artifacts/mnt/user-data/uploads/document.pdf",
      "extension": ".pdf",
      "modified": 1705997600.0
    }
  ],
  "count": 1
}
```

#### 删除文件

```http
DELETE /api/threads/{thread_id}/uploads/{filename}
```

**响应：**
```json
{
  "success": true,
  "message": "已删除 document.pdf"
}
```

### 线程清理

在 LangGraph 线程本身被删除后，移除 `.deer-flow/threads/{thread_id}` 下 DeerFlow 管理的本地线程文件。

```http
DELETE /api/threads/{thread_id}
```

**响应：**
```json
{
  "success": true,
  "message": "已删除 abc123 的本地线程数据"
}
```

**错误行为：**
- `422` 表示无效的线程 ID
- `500` 返回通用 `{"detail": "删除本地线程数据失败。"}` 响应，而完整的异常详情保留在服务器日志中

### 产物

#### 获取产物

下载或查看代理生成的产物。

```http
GET /api/threads/{thread_id}/artifacts/{path}
```

**路径示例：**
- `/api/threads/abc123/artifacts/mnt/user-data/outputs/result.txt`
- `/api/threads/abc123/artifacts/mnt/user-data/uploads/document.pdf`

**查询参数：**
- `download`（布尔值）：如果为 `true`，强制使用 Content-Disposition 标头下载

**响应：** 带有适当 Content-Type 的文件内容

---

## 错误响应

所有 API 以一致的格式返回错误：

```json
{
  "detail": "描述出错原因的错误消息"
}
```

**HTTP 状态码：**
- `400` - 错误请求：输入无效
- `404` - 未找到：资源不存在
- `422` - 验证错误：请求验证失败
- `500` - 内部服务器错误：服务器端错误

---

## 认证

DeerFlow 对所有非公共 HTTP 路由强制执行认证。公共路由仅限于健康检查/文档元数据和这些公共认证端点：

- `POST /api/v1/auth/initialize` 在没有管理员存在时创建第一个管理员账户。
- `POST /api/v1/auth/login/local` 使用邮箱/密码登录并设置 HttpOnly `access_token` cookie。
- `POST /api/v1/auth/register` 创建普通 `user` 账户并设置会话 cookie。
- `POST /api/v1/auth/logout` 清除会话 cookie。
- `GET /api/v1/auth/setup-status` 报告是否仍需要创建第一个管理员。

认证后的认证端点有：

- `GET /api/v1/auth/me` 返回当前用户。
- `POST /api/v1/auth/change-password` 更改密码，可选在设置期间更改邮箱，递增 `token_version`，并重新签发 cookie。

受保护的状态更改请求也需要 CSRF 双重提交令牌：将 `csrf_token` cookie 值作为 `X-CSRF-Token` 标头发送。登录/注册/初始化/注销是引导认证端点：它们免于双重提交令牌，但仍会拒绝恶意的浏览器 `Origin` 标头。

从认证的用户上下文强制执行用户隔离：

- 线程元数据按 `threads_meta.user_id` 限定范围；搜索/读/写/删除 API 仅公开当前用户的线程。
- 线程文件位于 `{base_dir}/users/{user_id}/threads/{thread_id}/user-data/` 下，在沙盒中作为 `/mnt/user-data/` 公开。
- 内存和自定义代理存储在 `{base_dir}/users/{user_id}/...` 下。

注意：MCP 出站连接仍可为配置的 HTTP/SSE MCP 服务器使用 OAuth；这与 DeerFlow API 认证是分开的。

---

## 速率限制

默认情况下未实现速率限制。对于生产部署，在 Nginx 中配置速率限制：

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

---

## 流式传输支持

Gateway 的 LangGraph 兼容 API 使用服务器发送事件（SSE）流式传输运行事件：

```http
POST /api/langgraph/threads/{thread_id}/runs/stream
Accept: text/event-stream
```

---

## SDK 使用

### Python（LangGraph SDK）

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2026/api/langgraph")

# 创建线程
thread = await client.threads.create()

# 运行代理
async for event in client.runs.stream(
    thread["thread_id"],
    "lead_agent",
    input={"messages": [{"role": "user", "content": "你好"}]},
    config={"configurable": {"model_name": "gpt-4"}},
    stream_mode=["values", "messages-tuple", "custom"],
):
    print(event)
```

### JavaScript/TypeScript

```typescript
// 使用 fetch 访问 Gateway API
const response = await fetch('/api/models');
const data = await response.json();
console.log(data.models);

// 创建运行并流式传输 SSE 事件
const streamResponse = await fetch(`/api/langgraph/threads/${threadId}/runs/stream`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  },
  body: JSON.stringify({
    input: { messages: [{ role: "user", content: "你好" }] },
    stream_mode: ["values", "messages-tuple", "custom"],
  }),
});

const reader = streamResponse.body?.getReader();
// 在您的客户端代码中从读取器解码和解析 SSE 帧。
```

### cURL 示例

```bash
# 列出模型
curl http://localhost:2026/api/models

# 获取 MCP 配置
curl http://localhost:2026/api/mcp/config

# 上传文件
curl -X POST http://localhost:2026/api/threads/abc123/uploads \
  -F "files=@document.pdf"

# 启用技能
curl -X POST http://localhost:2026/api/skills/pdf-processing/enable

# 创建线程并运行代理
curl -X POST http://localhost:2026/api/langgraph/threads \
  -H "Content-Type: application/json" \
  -d '{}'

curl -X POST http://localhost:2026/api/langgraph/threads/abc123/runs \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"messages": [{"role": "user", "content": "你好"}]},
    "config": {
      "recursion_limit": 100,
      "configurable": {"model_name": "gpt-4"}
    }
  }'
```

> 统一 Gateway 路径默认将 `config.recursion_limit` 设置为 100，用于计划模式和子代理密集型运行。客户端仍可显式设置 `config.recursion_limit` — 详情请参见[创建运行](#创建运行)部分。

