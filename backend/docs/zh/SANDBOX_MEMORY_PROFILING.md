# 沙盒内存分析

本文档描述 DeerFlow 沙盒系统的内存分析和优化。

## 概述

沙盒执行可能消耗大量内存。本文档提供分析内存使用和优化沙盒配置的指导。

## 内存使用源

### 1. 容器运行时

每个沙盒容器使用内存：
- **基础镜像**：100-500MB（取决于镜像）
- **运行时开销**：50-100MB
- **应用程序**：变量（Python 解释器等）

### 2. 文件系统挂载

挂载的卷消耗内存：
- **工作区文件**：加载的文件
- **技能目录**：技能文件缓存
- **上传文件**：用户上传的内容

### 3. 进程执行

运行的进程使用内存：
- **Shell 进程**：每个 bash 调用
- **Python 解释器**：代码执行
- **子进程**：工具执行

## 分析工具

### Docker 统计

```bash
# 查看容器内存使用
docker stats --no-stream

# 特定容器
docker stats deer-flow-sandbox-abc123 --no-stream
```

### Python 内存分析

```python
# 在沙盒中分析内存
import tracemalloc

tracemalloc.start()

# 执行代码
result = execute_code()

# 获取内存使用
current, peak = tracemalloc.get_traced_memory()
print(f"当前: {current / 1024 / 1024:.1f} MB")
print(f"峰值: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

### 内置监控

```python
class MemoryProfiler:
    """沙盒内存使用分析器。"""

    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.measurements = []

    async def profile_execution(self, command: str):
        """分析命令执行。"""
        # 执行前测量
        before = await self._get_memory_usage()

        # 执行命令
        start_time = time.monotonic()
        result = await self.sandbox.execute_command(command)
        duration = time.monotonic() - start_time

        # 执行后测量
        after = await self._get_memory_usage()

        measurement = {
            "command": command,
            "before_mb": before,
            "after_mb": after,
            "delta_mb": after - before,
            "duration_s": duration
        }
        self.measurements.append(measurement)

        return measurement

    async def _get_memory_usage(self) -> float:
        """获取当前内存使用（MB）。"""
        # Docker API 调用获取容器统计
        stats = await self.sandbox.get_stats()
        return stats.memory_usage / 1024 / 1024
```

## 内存优化

### 1. 镜像优化

```dockerfile
# 使用精简基础镜像
FROM python:3.11-slim

# 仅安装必要包
RUN pip install --no-cache-dir \
    requests \
    numpy

# 清理
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

### 2. 资源限制

```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  resources:
    memory: 2g          # 内存限制
    memory_swap: 2g     # 交换限制
    cpus: 2             # CPU 限制
```

### 3. 连接池

```python
# 复用 HTTP 连接
import httpx

class OptimizedSandbox:
    def __init__(self):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=5)
        )

    async def execute_http_request(self, url: str):
        # 复用连接
        response = await self.client.get(url)
        return response
```

### 4. 流式处理

```python
# 流式处理大文件而非加载到内存
async def process_large_file(file_path: str):
    async with aiofiles.open(file_path, 'r') as f:
        async for line in f:
            # 逐行处理
            process_line(line)
```

## 配置指南

### 开发环境

```yaml
# 宽松限制用于开发
sandbox:
  resources:
    memory: 4g
    cpus: 4
```

### 生产环境

```yaml
# 严格限制用于生产
sandbox:
  resources:
    memory: 1g
    memory_swap: 1g
    cpus: 1
  max_concurrent: 5  # 限制并发沙盒
```

### CI/CD 环境

```yaml
# 最小化用于 CI
sandbox:
  resources:
    memory: 512m
    cpus: 1
```

## 监控

### 指标收集

```python
class SandboxMetrics:
    """收集沙盒内存指标。"""

    def __init__(self):
        self.memory_usage = Gauge(
            'sandbox_memory_mb',
            '沙盒内存使用（MB）',
            ['sandbox_id']
        )
        self.execution_time = Histogram(
            'sandbox_execution_seconds',
            '命令执行时间'
        )

    async def record_metrics(self, sandbox_id: str):
        """记录沙盒指标。"""
        stats = await get_sandbox_stats(sandbox_id)
        self.memory_usage.labels(sandbox_id).set(
            stats.memory_usage / 1024 / 1024
        )
```

### 告警

```yaml
# 内存告警规则
alerts:
  - name: HighMemoryUsage
    condition: sandbox_memory_mb > 1800
    duration: 5m
    severity: warning

  - name: CriticalMemoryUsage
    condition: sandbox_memory_mb > 1900
    duration: 2m
    severity: critical
```

## 故障排除

### "内存不足"错误

```
Error: Container out of memory
```

**解决方案**：
1. 增加内存限制
2. 优化代码内存使用
3. 处理大文件时使用流式

### "无法启动沙盒"

```
Error: failed to start container: OCI runtime create failed
```

**解决方案**：
1. 检查 Docker 守护进程
2. 验证镜像存在
3. 检查磁盘空间

### 缓慢执行

**诊断**：
```bash
# 分析容器性能
docker stats

# 检查宿主机资源
top
htop
```

**解决方案**：
1. 限制并发沙盒数
2. 优化资源分配
3. 使用更快的存储

## 最佳实践

1. **设置限制**：始终为沙盒设置内存和 CPU 限制
2. **监控使用**：定期监控沙盒内存使用
3. **优化镜像**：使用最小化 Docker 镜像
4. **清理资源**：及时清理未使用的沙盒
5. **流式处理**：处理大文件时使用流式
