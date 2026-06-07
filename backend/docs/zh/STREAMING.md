# 流式输出设计

本文档解释 DeerFlow 中的流式输出机制。

## 概述

流式输出允许：
- 实时向用户显示代理响应
- 减少感知延迟
- 为长时间操作提供进度可见性
- 改善用户体验

## 流式路径

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           流式数据流                                    │
└─────────────────────────────────────────────────────────────────────────┘

客户端请求
    │
    ▼
┌─────────────────┐
│   Gateway API   │
│   (FastAPI)     │
└────────┬────────┘
         │
         │ 启动代理运行
         ▼
┌─────────────────────────────────┐
│   嵌入式 LangGraph 运行时        │
│   (packages/harness/deerflow/agents)                            │
└────────┬────────────────────────┘
         │
         │ astream() / astream_events()
         │
         ▼
┌─────────────────────────────────┐
│   EventSourceResponse           │
│   (SSE 流式传输)                │
└────────┬────────────────────────┘
         │
         │ SSE 数据块
         ▼
┌─────────────────────────────────┐
│   客户端 (浏览器/Web UI)         │
│   - 实时显示                    │
│   - 渐进式渲染                  │
└─────────────────────────────────┘
```

## SSE（服务器发送事件）

DeerFlow 使用 SSE 进行流式传输：

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "token", "content": "Hello"}

data: {"type": "token", "content": " world"}

data: {"type": "tool_call", "name": "web_search", "args": {"query": "..."}}

data: {"type": "tool_result", "name": "web_search", "result": "..."}

data: {"type": "done"}
```

## LangGraph stream_mode

DeerFlow 支持多种 LangGraph 流式模式：

### 模式：values

在每个步骤后发出完整状态值：

```python
async for event in graph.astream(inputs, stream_mode="values"):
    # event = 完整状态快照
    yield {"type": "state", "data": event}
```

**使用场景**：
- 需要查看完整状态变化
- 调试和开发

### 模式：messages

作为消息发出 LLM 令牌流：

```python
async for event in graph.astream(inputs, stream_mode="messages"):
    # event = 消息令牌
    yield {"type": "token", "content": event.content}
```

**使用场景**：
- 打字机效果
- 实时 LLM 响应

### 模式：updates

在每个节点后发出状态更新：

```python
async for event in graph.astream(inputs, stream_mode="updates"):
    # event = 节点输出
    yield {"type": "update", "node": event["__run"], "data": event}
```

**使用场景**：
- 跟踪代理步骤
- 进度指示

### 模式：events

发出所有事件（最详细）：

```python
async for event in graph.astream_events(inputs, version="v2"):
    # event = 详细事件
    yield {"type": "event", "kind": event["event"], "data": event}
```

**使用场景**：
- 完整可见性
- 调试复杂工作流

## DeerFlow 实现

### Gateway 中的流式处理

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

@router.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: RunRequest):
    agent = make_lead_agent(config)

    async def event_generator():
        async for event in agent.astream(request.input, config):
            yield {
                "event": "message",
                "data": json.dumps(format_event(event))
            }

    return EventSourceResponse(event_generator())
```

### 事件格式化

```python
def format_event(event):
    if event["type"] == "token":
        return {
            "type": "content",
            "content": event["content"]
        }
    elif event["type"] == "tool_call":
        return {
            "type": "tool_call",
            "name": event["name"],
            "arguments": event["args"]
        }
    elif event["type"] == "tool_result":
        return {
            "type": "tool_result",
            "name": event["name"],
            "result": event["result"]
        }
    elif event["type"] == "error":
        return {
            "type": "error",
            "error": event["error"]
        }
```

## 客户端集成

### Web UI 流式处理

```typescript
const eventSource = new EventSource(`/api/threads/${threadId}/runs/stream`, {
  method: 'POST',
  body: JSON.stringify({ input: message })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'content':
      // 追加到显示的消息
      appendContent(data.content);
      break;
    case 'tool_call':
      // 显示工具调用指示器
      showToolCall(data.name, data.arguments);
      break;
    case 'tool_result':
      // 显示工具结果
      showToolResult(data.name, data.result);
      break;
    case 'error':
      // 显示错误
      showError(data.error);
      break;
    case 'done':
      // 完成流式处理
      eventSource.close();
      break;
  }
};
```

## 特殊事件类型

### 思考内容

对于支持思考的模型：

```json
{
  "type": "thinking",
  "content": "让我分析一下这个问题...",
  "signature": "..."
}
```

### 工具调用

```json
{
  "type": "tool_call",
  "id": "call_abc123",
  "name": "web_search",
  "arguments": {
    "query": "DeerFlow documentation"
  }
}
```

### 工具结果

```json
{
  "type": "tool_result",
  "id": "call_abc123",
  "name": "web_search",
  "result": "...",
  "is_error": false
}
```

### 待办事项更新

```json
{
  "type": "todos",
  "todos": [
    { "id": "1", "content": "搜索文档", "status": "completed" },
    { "id": "2", "content": "分析结果", "status": "in_progress" }
  ]
}
```

## 性能考虑

### 缓冲

- 小事件批量发送以减少开销
- 权衡延迟与效率

```python
buffer = []
async for event in stream:
    buffer.append(event)
    if len(buffer) >= 10 or time_since_last_send > 50ms:
        yield buffer
        buffer = []
```

### 连接管理

- 实现心跳保持连接活跃
- 处理客户端断开连接
- 资源清理

```python
async def event_generator():
    try:
        async for event in stream:
            yield event
    except asyncio.CancelledError:
        # 客户端断开连接
        await cleanup()
        raise
```

## 故障排除

### "流式传输不工作"
- 检查 SSE 端点正确配置
- 验证 EventSourceResponse 导入
- 确保没有中间件缓冲响应

### "事件未到达客户端"
- 检查 CORS 配置
- 验证 Content-Type 标头
- 确保正确的事件格式

### "性能问题"
- 考虑添加缓冲
- 减少事件频率
- 优化 JSON 序列化
