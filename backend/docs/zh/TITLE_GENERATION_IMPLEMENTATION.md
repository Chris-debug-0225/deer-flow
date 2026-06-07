# 标题生成实现

本文档描述 DeerFlow 中自动标题生成功能的技术实现细节。

## 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         标题生成流程                                     │
└─────────────────────────────────────────────────────────────────────────┘

用户消息
    │
    ▼
┌─────────────────────────────────┐
│   TitleMiddleware               │
│   (middlewares/title_middleware.py)                           │
└────────┬────────────────────────┘
         │
         │ 1. 检查条件
         │    - 线程是否已有标题？
         │    - 标题生成是否启用？
         │    - 是否为第一条消息？
         │
         ▼
┌─────────────────────────────────┐
│   标题生成服务                   │
│   (services/title_service.py)   │
└────────┬────────────────────────┘
         │
         │ 2. 准备提示
         │    - 加载模板
         │    - 注入用户消息
         │
         ▼
┌─────────────────────────────────┐
│   模型调用                       │
│   - 使用配置的模型              │
│   - 或默认模型                  │
└────────┬────────────────────────┘
         │
         │ 3. 生成标题
         │    - 调用 LLM
         │    - 清理输出
         │
         ▼
┌─────────────────────────────────┐
│   存储标题                       │
│   - ThreadState.title           │
│   - LangGraph 元数据            │
└─────────────────────────────────┘
         │
         ▼
    返回给用户界面
```

## 核心组件

### TitleMiddleware

位置：`packages/harness/deerflow/agents/middlewares/title_middleware.py`

```python
class TitleMiddleware(BaseMiddleware):
    """为线程自动生成标题的中间件。"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config.get('title', {})
        self.enabled = self.config.get('enabled', True)
        self.max_words = self.config.get('max_words', 6)
        self.max_chars = self.config.get('max_chars', 60)
        self.model_name = self.config.get('model_name')

    async def process(
        self,
        state: ThreadState,
        config: RunnableConfig
    ) -> ThreadState:
        # 检查是否应生成标题
        if not self._should_generate_title(state):
            return state

        # 获取用户消息
        user_message = self._get_first_user_message(state)
        if not user_message:
            return state

        # 生成标题
        title = await self._generate_title(user_message)

        # 存储标题
        state.title = title

        return state

    def _should_generate_title(self, state: ThreadState) -> bool:
        """检查是否应该为此线程生成标题。"""
        if not self.enabled:
            return False

        if state.title:  # 已有标题
            return False

        # 检查消息历史
        messages = state.messages
        if len(messages) != 1:  # 不是第一条消息
            return False

        if not isinstance(messages[0], HumanMessage):
            return False

        return True

    async def _generate_title(self, user_message: str) -> str:
        """使用 LLM 生成标题。"""
        # 加载提示模板
        template = self._load_template()

        # 准备提示
        prompt = template.render(
            user_message=user_message,
            max_words=self.max_words,
            max_chars=self.max_chars
        )

        # 获取模型
        model = self._get_model()

        # 调用模型
        response = await model.ainvoke(prompt)

        # 清理标题
        title = self._clean_title(response.content)

        return title

    def _clean_title(self, raw_title: str) -> str:
        """清理和格式化生成的标题。"""
        # 移除引号
        title = raw_title.strip().strip('"\'')

        # 截断到词数限制
        words = title.split()
        if len(words) > self.max_words:
            title = ' '.join(words[:self.max_words])

        # 截断到字符限制
        if len(title) > self.max_chars:
            title = title[:self.max_chars].rsplit(' ', 1)[0]

        return title

    def _load_template(self) -> Template:
        """加载标题生成提示模板。"""
        template_path = Path(__file__).parent / 'templates' / 'title_generation.j2'
        with open(template_path) as f:
            return Template(f.read())

    def _get_model(self):
        """获取用于标题生成的模型。"""
        if self.model_name:
            return get_model(self.model_name)
        return get_default_model()
```

### 提示模板

位置：`templates/title_generation.j2`

```jinja2
为以下用户查询生成一个简短、描述性的标题。

用户查询：
{{ user_message }}

要求：
- 最多 {{ max_words }} 个词
- 最多 {{ max_chars }} 个字符
- 简洁且描述性强
- 不使用引号或特殊字符
- 直接返回标题，无需解释

标题：
```

### 模型选择

```python
def get_title_model(config: dict) -> BaseChatModel:
    """为标题生成获取合适的模型。"""
    model_name = config.get('model_name')

    if model_name:
        return create_chat_model(model_name)

    # 使用默认模型，但参数优化速度
    default = get_default_model()
    if hasattr(default, 'max_tokens'):
        # 标题生成不需要太多令牌
        default.max_tokens = 50

    return default
```

## 数据流

### 首次消息处理

```
1. 用户发送消息
   ↓
2. Lead Agent 处理
   - 运行中间件链
   ↓
3. TitleMiddleware 执行
   - 检查：是第一条消息？无现有标题？
   - 提取用户消息内容
   - 异步生成标题
   ↓
4. 标题存储
   - state.title = "生成的标题"
   ↓
5. 响应返回
   - 标题包含在响应中
   ↓
6. Web UI 显示
   - 线程列表显示生成的标题
```

### 存储位置

```python
# 1. ThreadState（运行时状态）
state.title = "Python Fibonacci Function"

# 2. LangGraph 检查点（持久化）
checkpoint_metadata = {
    "title": "Python Fibonacci Function",
    "created_by": "auto",
    "thread_id": "thread_abc123"
}

# 3. Gateway 响应（传递给 UI）
response = {
    "title": "Python Fibonacci Function",
    "messages": [...]
}
```

## 配置选项

```yaml
title:
  enabled: true              # 启用/禁用
  max_words: 6               # 最大词数
  max_chars: 60              # 最大字符数
  model_name: null           # 特定模型（null = 默认）
  temperature: 0.3           # 创造性 vs 确定性
  timeout: 5                 # 生成超时（秒）
```

## 性能优化

### 异步执行

```python
# 标题生成不阻塞主响应
async def generate_title_async(self, message: str):
    # 在后台任务中运行
    asyncio.create_task(self._generate_and_store_title(message))

# 主要响应立即返回
return {"message": "处理中...", "title_pending": True}
```

### 缓存

```python
class TitleCache:
    """缓存常见查询的标题以减少 LLM 调用。"""

    def __init__(self):
        self.cache = {}
        self.max_size = 1000

    def get(self, query_hash: str) -> Optional[str]:
        return self.cache.get(query_hash)

    def set(self, query_hash: str, title: str):
        if len(self.cache) >= self.max_size:
            # LRU 淘汰
            oldest = min(self.cache, key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest]

        self.cache[query_hash] = {
            'title': title,
            'timestamp': time.time()
        }
```

## 错误处理

```python
async def _generate_title_safe(self, message: str) -> Optional[str]:
    """安全地生成标题，优雅地处理错误。"""
    try:
        return await asyncio.wait_for(
            self._generate_title(message),
            timeout=self.config.get('timeout', 5)
        )
    except asyncio.TimeoutError:
        logger.warning("标题生成超时")
        return None
    except Exception as e:
        logger.error(f"标题生成错误: {e}")
        return None
```

## 测试

### 单元测试

```python
async def test_title_generation():
    middleware = TitleMiddleware({
        'title': {
            'enabled': True,
            'max_words': 6,
            'max_chars': 60
        }
    })

    state = ThreadState(
        messages=[HumanMessage(content="写一个 Python 函数计算斐波那契数列")]
    )

    result = await middleware.process(state, {})

    assert result.title is not None
    assert len(result.title.split()) <= 6
    assert len(result.title) <= 60
    assert "斐波那契" in result.title or "Python" in result.title
```

### 集成测试

```python
async def test_title_in_conversation():
    # 创建新线程
    thread_id = create_thread()

    # 发送第一条消息
    response = await send_message(thread_id, "解释量子计算")

    # 验证返回了标题
    assert response.title is not None
    assert "量子" in response.title
```

## 监控

### 指标

```python
class TitleMetrics:
    titles_generated: Counter
    generation_time: Histogram
    generation_errors: Counter
    cache_hits: Counter
    cache_misses: Counter
```

### 日志

```
INFO - 为线程 thread_abc123 生成标题
DEBUG - 标题生成提示: "为以下查询生成标题..."
INFO - 生成标题: "Python 斐波那契函数"（耗时 0.8s）
WARNING - 标题生成超时（线程 thread_def456）
```
