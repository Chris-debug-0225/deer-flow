# 阻塞 I/O 检测

本文档描述如何检测异步代码中的阻塞 I/O 操作。

## 问题

同步 I/O 阻塞事件循环：
- `requests.get()` 阻塞
- `time.sleep()` 阻塞
- 文件 I/O 阻塞

## 解决方案

### 使用异步替代

| 同步 | 异步 |
|------|------|
| `requests` | `httpx.AsyncClient` |
| `time.sleep` | `asyncio.sleep` |
| `open()` | `aiofiles.open()` |

### 检测工具

```python
import warnings

# 启用警告
warnings.filterwarnings('default', category=asyncio.BlockingIOWarning)

# 包装同步调用
result = await asyncio.to_thread(sync_function)
```

## 监控

```python
@contextmanager
def detect_blocking(operation):
    start = time.monotonic()
    yield
    duration = time.monotonic() - start
    if duration > 0.05:
        logger.warning(f"潜在阻塞: {operation} 耗时 {duration:.2f}s")
```

