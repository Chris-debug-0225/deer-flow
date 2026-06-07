# 中间件执行流程

本文档描述 DeerFlow 代理中中间件的执行顺序和流程。

## 概述

中间件提供了一种在代理执行前后处理线程状态的方式。每个中间件可以：
- 修改线程状态
- 添加副作用（日志、监控）
- 注入额外上下文
- 管理资源

## 执行顺序

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         中间件链执行顺序                                   │
└─────────────────────────────────────────────────────────────────────────┘

用户输入
    │
    ▼
┌─────────────────────────────────┐
│ 1. ThreadDataMiddleware         │ ← 初始化线程目录结构
│    - 创建 workspace/            │
│    - 创建 uploads/              │
│    - 创建 outputs/              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 2. UploadsMiddleware            │ ← 处理上传文件
│    - 扫描 uploads/ 目录         │
│    - 注入文件列表到提示         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 3. SandboxMiddleware            │ ← 获取沙盒环境
│    - 获取或创建沙盒            │
│    - 设置虚拟路径映射           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 4. SummarizationMiddleware      │ ← 上下文管理（如果启用）
│    - 检查上下文大小            │
│    - 如果接近限制则摘要         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 5. TitleMiddleware              │ ← 自动生成标题
│    - 检查是否为第一条消息       │
│    - 异步生成标题              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 6. TodoListMiddleware           │ ← 计划模式任务跟踪（如果启用）
│    - 添加 write_todos 工具     │
│    - 加载现有待办事项          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 7. ViewImageMiddleware          │ ← 视觉模型支持
│    - 处理图像上传              │
│    - 为视觉模型准备图像        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 8. ClarificationMiddleware      │ ← 澄清流程
│    - 检查是否需要澄清          │
│    - 收集缺失信息              │
└────────┬────────────────────────┘
         │
         ▼
    代理核心执行
    - 模型处理
    - 工具调用
    - 响应生成
         │
         ▼
    响应返回
```

## 中间件接口

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseMiddleware(ABC):
    """所有中间件的基类。"""

    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    async def process(
        self,
        state: ThreadState,
        config: RunnableConfig
    ) -> ThreadState:
        """处理线程状态。

        Args:
            state: 当前线程状态
            config: 运行时配置

        Returns:
            修改后的线程状态
        """
        pass

    async def on_enter(self, state: ThreadState, config: RunnableConfig):
        """在代理执行前调用（可选）。"""
        pass

    async def on_exit(self, state: ThreadState, config: RunnableConfig):
        """在代理执行后调用（可选）。"""
        pass
```

## 中间件链

```python
class MiddlewareChain:
    """管理中间件执行链。"""

    def __init__(self):
        self.middlewares: List[BaseMiddleware] = []

    def add(self, middleware: BaseMiddleware):
        """添加中间件到链。"""
        self.middlewares.append(middleware)

    async def execute(
        self,
        state: ThreadState,
        config: RunnableConfig
    ) -> ThreadState:
        """按顺序执行所有中间件。"""
        current_state = state

        for middleware in self.middlewares:
            try:
                # 执行前置钩子
                await middleware.on_enter(current_state, config)

                # 处理状态
                current_state = await middleware.process(current_state, config)

                # 如果状态被标记为停止，中断链
                if getattr(current_state, '_stop_chain', False):
                    break

            except Exception as e:
                logger.error(f"中间件 {middleware.__class__.__name__} 错误: {e}")
                # 根据配置决定是否继续
                if not getattr(middleware, 'continue_on_error', False):
                    raise

        return current_state

    async def execute_post_hooks(
        self,
        state: ThreadState,
        config: RunnableConfig
    ):
        """执行所有后置钩子（逆序）。"""
        for middleware in reversed(self.middlewares):
            try:
                await middleware.on_exit(state, config)
            except Exception as e:
                logger.error(f"中间件 {middleware.__class__.__name__} 后置钩子错误: {e}")
```

## 各中间件详情

### ThreadDataMiddleware

```python
class ThreadDataMiddleware(BaseMiddleware):
    """初始化线程数据目录结构。"""

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        thread_id = config.get('configurable', {}).get('thread_id')

        # 创建目录结构
        thread_dir = Paths.get_thread_dir(thread_id)
        (thread_dir / 'user-data' / 'workspace').mkdir(parents=True, exist_ok=True)
        (thread_dir / 'user-data' / 'uploads').mkdir(parents=True, exist_ok=True)
        (thread_dir / 'user-data' / 'outputs').mkdir(parents=True, exist_ok=True)

        # 存储路径信息
        state.thread_data = {
            'workspace': str(thread_dir / 'user-data' / 'workspace'),
            'uploads': str(thread_dir / 'user-data' / 'uploads'),
            'outputs': str(thread_dir / 'user-data' / 'outputs')
        }

        return state
```

### UploadsMiddleware

```python
class UploadsMiddleware(BaseMiddleware):
    """将上传文件信息注入系统提示。"""

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        uploads_dir = Path(state.thread_data['uploads'])

        # 扫描上传文件
        files = []
        for file_path in uploads_dir.iterdir():
            if file_path.is_file():
                virtual_path = f"/mnt/user-data/uploads/{file_path.name}"
                files.append({
                    'name': file_path.name,
                    'virtual_path': virtual_path,
                    'size': file_path.stat().st_size
                })

        # 如果有文件，注入到提示
        if files:
            file_list = '\n'.join([f"- {f['virtual_path']}" for f in files])
            upload_context = f"\n\n可用上传文件：\n{file_list}"

            # 添加到系统消息或状态
            state.uploads_context = upload_context

        return state
```

### SandboxMiddleware

```python
class SandboxMiddleware(BaseMiddleware):
    """获取或创建沙盒环境。"""

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        # 检查是否已有沙盒
        if state.sandbox:
            return state

        # 获取沙盒提供者
        provider = get_sandbox_provider()

        # 获取或创建沙盒
        sandbox = await provider.get(
            thread_id=config.get('configurable', {}).get('thread_id'),
            mounts={
                '/mnt/user-data': state.thread_data,
                '/mnt/skills': Paths.SKILLS_MOUNT
            }
        )

        state.sandbox = sandbox
        return state
```

## 条件执行

某些中间件基于配置条件执行：

```python
def _build_middlewares(config: RunnableConfig) -> MiddlewareChain:
    """基于配置构建中间件链。"""
    chain = MiddlewareChain()

    # 始终添加的基础中间件
    chain.add(ThreadDataMiddleware())
    chain.add(UploadsMiddleware())
    chain.add(SandboxMiddleware())

    # 条件中间件
    if is_summarization_enabled(config):
        chain.add(SummarizationMiddleware())

    chain.add(TitleMiddleware())

    if is_plan_mode_enabled(config):
        chain.add(TodoListMiddleware())

    chain.add(ViewImageMiddleware())
    chain.add(ClarificationMiddleware())

    return chain
```

## 错误处理

### 中间件级别错误

```python
class ResilientMiddleware(BaseMiddleware):
    """即使失败也允许链继续的中间件。"""

    continue_on_error = True

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        try:
            # 尝试处理
            return await self._do_process(state, config)
        except Exception as e:
            logger.error(f"处理失败但继续: {e}")
            # 返回未修改的状态
            return state
```

### 状态验证

```python
class ValidationMiddleware(BaseMiddleware):
    """验证中间件间状态完整性。"""

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        # 验证必需字段
        assert state.thread_data, "ThreadDataMiddleware 必须已运行"
        assert state.sandbox, "SandboxMiddleware 必须已运行"

        return state
```

## 调试和监控

### 执行时间追踪

```python
class TimedMiddleware(BaseMiddleware):
    """包装中间件以追踪执行时间。"""

    def __init__(self, wrapped: BaseMiddleware):
        self.wrapped = wrapped

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        start = time.monotonic()
        try:
            return await self.wrapped.process(state, config)
        finally:
            duration = time.monotonic() - start
            logger.debug(f"{self.wrapped.__class__.__name__}: {duration:.3f}s")
            metrics.record_middleware_time(
                self.wrapped.__class__.__name__,
                duration
            )
```

### 状态快照

```python
class DebugMiddleware(BaseMiddleware):
    """用于调试的状态快照中间件。"""

    async def process(self, state: ThreadState, config: RunnableConfig) -> ThreadState:
        if config.get('debug', False):
            snapshot = {
                'middleware': self.__class__.__name__,
                'state_before': state.dict(),
                'timestamp': time.time()
            }
            state._debug_snapshots.append(snapshot)

        result = await self._process(state, config)

        if config.get('debug', False):
            snapshot['state_after'] = result.dict()

        return result
```
