# 内存改进

本文档描述 DeerFlow 的内存优化改进。

## 问题

1. **沙盒泄漏**：空闲沙盒不清理
2. **大消息缓存**：无有效驱逐策略
3. **MCP 连接**：保持不必要连接

## 改进

### 1. 沙盒生命周期

```python
# 自动清理空闲沙盒
sandbox_provider = ManagedSandboxProvider()
sandbox_provider.start_cleanup_task()
```

### 2. 消息摘要

```python
# 自动摘要旧消息
if message_count > 50:
    await summarize_old_messages()
```

### 3. MCP 连接池

```python
# 连接池管理
pool = MCPConnectionPool(max_connections=10)
```

## 配置

```yaml
memory:
  sandbox:
    idle_timeout: 300
    max_concurrent: 10
  messages:
    summary_trigger: 50
```

