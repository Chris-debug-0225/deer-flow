# 第 12 章 Gateway API 与前端

> 🎯 本章目标：搞懂 Agent 是怎么「对外服务」的。前面 6 章我们学的都是 Agent 内部怎么运作，这一章看它怎么通过 Gateway API 把能力暴露给前端和外部，以及 SSE 流式响应、嵌入式客户端等关键设计。

---

## 12.1 学习目标

1. ✅ 理解 Gateway API 的角色（FastAPI REST 接口）
2. ✅ 认识核心 API 端点（threads / runs / models / skills / memory）
3. ✅ 理解 RunManager 如何管理一次 Agent 运行
4. ✅ 搞懂 SSE 流式响应的原理
5. ✅ 了解嵌入式客户端 DeerFlowClient（不用 HTTP 也能跑）

---

## 12.2 Gateway API 是什么

前面我们学的所有东西（Agent、工具、沙箱、记忆、技能）都在 **Harness 层**（`packages/harness/deerflow/`）。但用户怎么用到这些能力？总不能让用户写 Python 代码调吧。

**Gateway API** 就是答案——它是 deer-flow 的「**对外窗口**」，用一组 **REST API**（基于 FastAPI）把 Harness 层的能力暴露出去。

```
┌──────────────────────────────────────────────┐
│  前端（浏览器）/ IM / 第三方程序             │
└──────────────────┬───────────────────────────┘
                   │ HTTP 请求（GET/POST/SSE）
                   ▼
┌──────────────────────────────────────────────┐
│  Gateway API（FastAPI，端口 8001）           │  ← 本章
│  • 接收 HTTP 请求                             │
│  • 调用 Harness 层的 Agent 运行时             │
│  • 返回结果                                   │
└──────────────────┬───────────────────────────┘
                   │ 内部调用
                   ▼
┌──────────────────────────────────────────────┐
│  Harness 层（前面 6 章学的）                  │
│  make_lead_agent()、工具、沙箱、记忆、技能…  │
└──────────────────────────────────────────────┘
```

### Gateway 在三层架构中的位置

回忆第 03 章的三层架构：**Nginx → Gateway → Frontend**。Gateway 是中间的「业务大脑」：
- 接收 Nginx 转发来的请求
- 处理业务逻辑（创建对话、跑 Agent、管记忆）
- 把结果返回给前端

> 💡 Gateway = FastAPI 后端 + 内嵌的 Agent 运行时。它不只是个 API 服务器，还直接在里面跑 Agent。

---

## 12.3 核心 API 端点一览

Gateway 提供了一组 REST 端点，分成几大类。我们只看最核心的（完整的看 `backend/README.md`）。

### 对话与运行（最核心）

| 端点 | 方法 | 作用 |
|------|------|------|
| `/api/threads/{id}/runs/stream` | POST | ★发起一次对话并流式返回（核心！） |
| `/api/threads/{id}/runs` | POST | 发起一次对话（后台运行） |
| `/api/threads/{id}/runs/{rid}/cancel` | POST | 取消运行 |
| `/api/threads/{id}/runs/{rid}/messages` | GET | 分页获取消息历史 |

### 配置与管理

| 端点 | 方法 | 作用 |
|------|------|------|
| `/api/models` | GET | 列出可用模型 |
| `/api/skills` | GET/PUT | 列出/开关技能 |
| `/api/mcp/config` | GET/PUT | 管理 MCP 服务器 |
| `/api/memory` | GET | 获取记忆数据 |
| `/api/memory/reload` | POST | 强制重载记忆 |

### 文件与产物

| 端点 | 方法 | 作用 |
|------|------|------|
| `/api/threads/{id}/uploads` | POST | 上传文件 |
| `/api/threads/{id}/artifacts/{path}` | GET | 获取 Agent 生成的产物 |

### 一个典型流程

前端发一条消息的完整 API 调用：

```
1. POST /api/threads/{id}/runs/stream
   请求体：{ "input": {"messages": [{"role":"user","content":"你好"}]},
             "config": {"model_name": "gpt-4o", ...} }
   ↓
2. Gateway 创建一个 Run（用 RunManager）
   ↓
3. RunManager 启动 run_agent() → 跑 Lead Agent
   ↓
4. 通过 SSE 流式推送：
   data: {"event": "messages-tuple", "content": "你"}  ← 一个字一个字推
   data: {"event": "messages-tuple", "content": "好"}
   data: {"event": "messages-tuple", "content": "！"}
   ...
   data: {"event": "end"}                             ← 结束
```

---

## 12.4 ★核心★RunManager：管理一次 Agent 运行

`RunManager` 是 Gateway 里管理 Agent 执行的核心组件。每次你发一条消息，就创建一个 **Run（运行）**。

### Run 的生命周期

```
用户发消息
    │
    ▼
RunManager.create_or_reject(...)
    → 创建 RunRecord（id、状态、关联的 thread_id）
    → 状态：pending
    │
    ▼
后台启动 run_agent(task, run_id)
    → 状态：running
    → 实际调用 Lead Agent 执行
    │
    ├─ 通过 StreamBridge 把 Agent 的输出实时推给 SSE
    │
    ▼
Agent 执行完毕
    → 状态：completed（或 failed / cancelled / timed_out）
    → 结果存入 RunRecord
```

### StreamBridge：流式输出的桥梁

注意上面有个 `StreamBridge`——这是「**Agent 在后台跑，前端要实时看输出**」的关键。

```
后台线程：Agent 在跑（产生 token 流）
    │
    │ 把每个 token 推给 StreamBridge
    ▼
StreamBridge（一个缓冲队列）
    │
    │ SSE 端点从 StreamBridge 拉数据
    ▼
SSE 响应 → Nginx → 前端（打字机效果）
```

StreamBridge 解决了「**生产者（Agent）和消费者（HTTP 响应）解耦**」的问题——Agent 按自己的速度产生输出，SSE 按网络速度推送，互不阻塞。

### Run 的状态机

```
        create
          │
          ▼
       pending ──start──▶ running ──┬──success──▶ completed
                                     ├──error────▶ failed
                                     ├──cancel───▶ cancelled
                                     └──timeout──▶ timed_out
```

前端通过轮询 `/api/threads/{id}/runs/{rid}` 或 SSE 实时获取状态变化，据此更新 UI（转圈、显示完成、显示错误）。

---

## 12.5 SSE 流式响应原理

第 02 章我们提到 deer-flow 用 SSE 实现打字机效果。现在深入讲讲。

### 什么是 SSE

**SSE（Server-Sent Events，服务器发送事件）** 是一种 HTTP 协议的扩展，允许服务器**持续向客户端推送数据**。

```
普通 HTTP：
  客户端请求 → 服务器算完 → 一次性返回整个响应 → 连接关闭

SSE：
  客户端请求 → 服务器保持连接打开
              → 推一条数据
              → 推一条数据
              → ...持续推送...
              → 推送结束 → 连接关闭
```

### SSE 的数据格式

SSE 响应的 Content-Type 是 `text/event-stream`，每条消息以 `data: ` 开头，用空行分隔：

```
data: {"content": "你"}

data: {"content": "好"}

data: {"content": "，"}

data: {"content": "世界"}

data: [DONE]
```

浏览器收到每一条就处理一次（比如 append 到聊天框），实现「打字机」效果。

### 为什么 Agent 必须用 SSE

因为 **LLM 是流式生成的**——它一个 token 一个 token 吐出来。如果用普通 HTTP，用户要等 LLM 把整句话生成完才看到，可能等 10 秒，体验很差。

用 SSE，LLM 吐一个 token 就立刻推给前端，用户**边生成边看到**，体感延迟极低。这就是所有现代 AI 聊天产品（ChatGPT、Claude…）都用流式响应的原因。

### deer-flow 的流式模式

deer-flow 用 LangGraph 的 `stream_mode` 控制 SSE 推什么：

| 模式 | 推什么 | 用途 |
|------|--------|------|
| `messages-tuple` | 每个 token 增量（AI 文字的 delta） | 打字机效果 |
| `values` | 完整状态快照 | 同步完整状态 |
| `custom` | 自定义事件（工具调用、子代理状态） | 工具卡片、子代理进度 |
| `end` | 流结束 | 关闭连接 |

前端组合这些模式，就能渲染出「文字打字机 + 工具调用卡片 + 子代理进度」的丰富界面。

---

## 12.6 LangGraph 兼容 API

一个重要细节：Gateway 对外暴露的是 **LangGraph 兼容的 API 格式**。

这意味着什么？意味着 deer-flow 的 API 路径和 LangGraph 官方 Server 一致：

```
LangGraph 官方格式：
  POST /threads/{id}/runs/stream

deer-flow 的 Gateway（经过 Nginx）：
  POST /api/langgraph/threads/{id}/runs/stream
            ^^^^^^^^^
            Nginx 会把这个前缀改写成 /api/
```

**为什么要兼容 LangGraph 格式**？因为这样 deer-flow 可以直接复用 LangGraph 生态的工具——比如 **LangGraph SDK**（前端用的客户端库）、**LangGraph Studio**（调试工具）。前端用标准的 LangGraph SDK 就能连 deer-flow，不用改代码。

> 💡 这是一种「**拥抱标准**」的设计哲学——不另起炉灶，而是兼容主流标准，借力生态。

---

## 12.7 嵌入式客户端：DeerFlowClient

除了通过 HTTP API 调用，deer-flow 还提供了一种**不用 HTTP 也能用**的方式——`DeerFlowClient`（嵌入式客户端）。

### 它是什么

`DeerFlowClient` 是一个 Python 类，让你**在代码里直接调用** Agent，不需要启动 HTTP 服务：

```python
from deerflow.client import DeerFlowClient

client = DeerFlowClient()

# 直接对话（不需要 HTTP）
response = client.chat("帮我写个 hello.txt", thread_id="my-thread")

# 流式
for event in client.stream("你好"):
    if event.type == "messages-tuple":
        print(event.data["content"], end="")

# 管理功能
models = client.list_models()
skills = client.list_skills()
client.update_skill("deep-research", enabled=True)
```

### 两种模式对比

| | HTTP API（Gateway） | 嵌入式（DeerFlowClient） |
|--|-------------------|------------------------|
| 怎么用 | 发 HTTP 请求 | 直接调 Python 方法 |
| 要启动服务吗 | 要（Gateway + Nginx） | **不用** |
| 适合 | Web 应用、多用户 | 脚本、批处理、集成到别的 Python 程序 |
| 返回格式 | HTTP 响应（JSON/流） | Python 对象/dict |

### 为什么有两种

因为不同的使用场景：

- **做 Web 应用**（像 deer-flow 自带的网页）→ 用 HTTP API，因为浏览器只能发 HTTP
- **写脚本/批处理**（比如「自动跑 100 个研究任务」）→ 用嵌入式，省去 HTTP 开销，更简单
- **集成到别的系统**（比如嵌入到你自己的 Python 后端）→ 用嵌入式

### 一致性保证

一个很赞的设计：**DeerFlowClient 的返回格式和 Gateway API 完全一致**。

```python
# HTTP 方式
response = requests.get("http://localhost:8001/api/models")
# → {"models": [...]}

# 嵌入式方式
models = client.list_models()
# → {"models": [...]}   ← 一模一样的结构！
```

 deer-flow 用**一致性测试**（`TestGatewayConformance`）保证两者不漂移——如果 Gateway 加了字段但 Client 没加，CI 会报错。这样你可以**在两种模式间无缝切换**，代码几乎不用改。

---

## 12.8 前端如何与后端通信

最后简单说说前端。deer-flow 的前端是 Next.js 应用，它通过 **LangGraph SDK**（`@langchain/langgraph-sdk`）连后端：

```
浏览器（Next.js 前端）
    │
    │ 用 LangGraph SDK 发请求
    │   client.runs.stream(threadId, ...)
    ▼
Nginx (:2026)
    │
    │ /api/langgraph/* → 改写成 /api/* → 转发
    ▼
Gateway (:8001)
    │
    │ 跑 Agent，返回 SSE 流
    ▼
前端实时渲染（打字机、工具卡片、子代理进度）
```

前端的核心工作是：
1. **发请求**（用户输入 → 调 `/runs/stream`）
2. **处理 SSE 流**（收 token → 更新 UI；收 custom 事件 → 渲染工具卡片）
3. **管理状态**（对话列表、当前模型、设置…）

前端代码不是本课件重点（我们聚焦 Agent 后端），但你要知道：**前端和后端完全通过标准 HTTP/SSE 通信，中间没有任何魔法**。理解了 Gateway API，你就理解了前端怎么和 Agent 交互。

---

## 12.9 动手实验：直接调 API

来感受一下「绕过前端，直接调 API」。

### 步骤 1：确保服务跑着（make dev）

### 步骤 2：用 curl 调一个简单 API

```bash
# 列出可用模型（绕过前端，直接问 Gateway）
curl http://localhost:8001/api/models

# 健康检查
curl http://localhost:8001/health

# 列出技能
curl http://localhost:8001/api/skills
```

你会看到 JSON 响应——这就是前端界面背后真正在调的东西。

### 步骤 3：理解 Nginx 转发

```bash
# 通过 Nginx（端口 2026）调，结果一样
curl http://localhost:2026/api/models
```

这验证了第 03 章说的「Nginx 把 `/api/*` 转发给 Gateway」。

### 步骤 4：试嵌入式客户端（可选）

如果你想在 Python 里直接调：

```python
# 在 backend 目录下
from deerflow.client import DeerFlowClient

client = DeerFlowClient()
print(client.list_models())
response = client.chat("你好", thread_id="test-thread")
print(response)
```

不用启动任何 HTTP 服务，直接在 Python 里和 Agent 对话——这就是嵌入式客户端的便利。

---

## 12.10 本章小结

✅ **Gateway API** 是 deer-flow 的「对外窗口」，用 FastAPI 把 Harness 层能力暴露成 REST 接口
✅ 核心 API：**`/runs/stream`（流式对话）**、`/models`、`/skills`、`/memory`、`/uploads`、`/artifacts`
✅ **RunManager** 管理一次 Agent 运行的生命周期（pending → running → completed/failed）
✅ **StreamBridge** 解耦「Agent 生产」和「HTTP 消费」，实现流式输出
✅ **SSE** 让 LLM 边生成边推送，实现打字机效果（所有现代 AI 聊天标配）
✅ Gateway 兼容 **LangGraph 标准 API 格式**，借力生态（SDK、Studio）
✅ **DeerFlowClient** 提供「不用 HTTP 也能用」的嵌入式方式，返回格式与 API 一致
✅ 前端通过 LangGraph SDK + SSE 与后端通信，无魔法

---

### 📋 概念检查点

1. Gateway API 在三层架构里扮演什么角色？
2. 为什么 Agent 聊天要用 SSE 而不是普通 HTTP？
3. RunManager 和 StreamBridge 分别解决什么问题？
4. DeerFlowClient 和 HTTP API 两种方式，各自适合什么场景？
5. 为什么 Gateway 要兼容 LangGraph 标准 API 格式？

---

## ➡️ 下一章预告

**第 13 章：IM 渠道集成** —— 除了网页，deer-flow 还能从飞书、Telegram、Slack 等聊天软件接收任务。下一章我们看 IM 渠道的消息总线架构、消息流转全链路，以及流式卡片更新机制。这是 deer-flow 「无处不在」能力的来源 💬
