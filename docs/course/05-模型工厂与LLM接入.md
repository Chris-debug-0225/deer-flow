# 第 05 章 模型工厂与 LLM 接入

> 🎯 本章目标：搞懂 deer-flow 是怎么把 `config.yaml` 里的一行字符串 `langchain_openai:ChatOpenAI` 变成一个真正能调用的模型对象的。我们会精读 `create_chat_model()` 这个核心函数，理解反射机制、思考模式开关、视觉支持等关键设计。

---

## 5.1 学习目标

1. ✅ 理解为什么需要「模型工厂」而不是直接 `new` 一个模型
2. ✅ 看懂 `resolve_class()` / `resolve_variable()` 反射机制的工作原理
3. ✅ 精读 `create_chat_model()` 函数的完整流程
4. ✅ 理解思考模式（thinking）的动态开关原理
5. ✅ 掌握对接各类 LLM 的配置方法

---

## 5.2 概念铺垫：什么是「工厂模式」

先讲个故事。假设你开了一家餐厅，菜单上有「汉堡」「披萨」「沙拉」。

**笨办法**：厨师记住每种食物的做法，客人点什么就现场做。
```python
if 客人要 == "汉堡":
    食物 = 汉堡(牛肉, 生菜, 面包)
elif 客人要 == "披萨":
    食物 = 披萨(面团, 芝士, 番茄)
```
问题：新增一种食物（比如「寿司」），要改厨师代码。

**工厂办法**：把「做什么食物」这件事交给一个「订单处理器」，它根据订单动态决定做哪个。
```python
食物 = 厨房工厂.制作(订单)   # 工厂内部根据订单决定实例化哪个类
```
新增寿司？只要在工厂的「配方表」里加一条，厨师代码不用改。

### deer-flow 的模型工厂

deer-flow 面对的问题一模一样。它要支持 OpenAI、DeepSeek、豆包、Claude、Gemini、Ollama……几十种模型。如果用 `if-else`：

```python
# 笨办法：每加一个模型就要改代码
if model_name == "gpt-4o":
    model = ChatOpenAI(...)
elif model_name == "claude":
    model = ChatAnthropic(...)
elif model_name == "gemini":
    model = ChatGoogleGenerativeAI(...)
# ... 几十个分支
```

deer-flow 用了**工厂模式 + 反射**，把「用哪个类」也变成了**配置**：

```python
# 工厂办法：根据配置里的字符串动态加载对应的类
model = create_chat_model(name="gpt-4o")
# 工厂内部：读 config.yaml → 发现 use: langchain_openai:ChatOpenAI
#         → 动态导入这个类 → 实例化它
```

这样**新增一种模型完全不用改代码**，只要在 `config.yaml` 里写对 `use` 字段就行。这就是第 04 章说的「配置驱动」的精髓。

---

## 5.3 核心机制：反射（Reflection）

工厂能动态加载类的关键技术叫**反射（Reflection）**。

> 反射：在程序运行时，根据一个**字符串**（类名/模块路径），动态地导入模块、找到类、实例化对象。

### deer-flow 的反射实现

deer-flow 的反射代码非常简洁（`reflection/resolvers.py`）。我们逐行精读：

```python
# 文件：packages/harness/deerflow/reflection/resolvers.py

from importlib import import_module

def resolve_variable(variable_path, expected_type=None):
    """从一个路径字符串解析出变量/对象。

    例：resolve_variable("langchain_openai:ChatOpenAI")
        → 导入 langchain_openai 模块 → 返回 ChatOpenAI 这个类
    """
    # 第 1 步：把 "模块:变量名" 拆开
    try:
        module_path, variable_name = variable_path.rsplit(":", 1)
        # "langchain_openai:ChatOpenAI"
        #   → module_path = "langchain_openai"
        #   → variable_name = "ChatOpenAI"
    except ValueError as err:
        raise ImportError(f"路径格式不对，应该是 模块:变量名")

    # 第 2 步：动态导入模块
    try:
        module = import_module(module_path)
        # 等价于 import langchain_openai
        # 但这是运行时根据字符串导入的！
    except ImportError as err:
        # ★友好报错：告诉用户该装什么包
        hint = _build_missing_dependency_hint(module_path, err)
        raise ImportError(f"导入失败：{hint}")

    # 第 3 步：从模块里取出变量（类/函数）
    try:
        variable = getattr(module, variable_name)
        # 等价于 langchain_openai.ChatOpenAI
    except AttributeError:
        raise ImportError(f"模块 {module_path} 里没有 {variable_name}")

    # 第 4 步：类型校验（可选）
    if expected_type is not None:
        if not isinstance(variable, expected_type):
            raise ValueError(f"类型不对，期望 {expected_type}")

    return variable
```

### 一个更友好的错误提示

注意第 2 步的 `_build_missing_dependency_hint`，这是 deer-flow 的人性化设计：

```python
# 模块名 → 该装的包名 的映射表
MODULE_TO_PACKAGE_HINTS = {
    "langchain_google_genai": "langchain-google-genai",
    "langchain_anthropic":    "langchain-anthropic",
    "langchain_openai":       "langchain-openai",
}

def _build_missing_dependency_hint(module_path, err):
    """当你忘了装依赖时，告诉你该装什么"""
    package_name = MODULE_TO_PACKAGE_HINTS.get(module_root, ...)
    return f"缺少依赖 '{module_root}'。用 `uv add {package_name}` 安装后重启。"
```

所以如果你配了 Gemini 但没装对应的包，deer-flow 不会甩给你一个看不懂的 `ModuleNotFoundError`，而是友好地说：

> 「缺少依赖 `langchain_google_genai`。用 `uv add langchain-google-genai` 安装后重启。」

这种「**出错时给出可执行建议**」的工程细节，值得学习。

### `resolve_class`：专门解析类

`resolve_class` 是 `resolve_variable` 的特化版，多了一步「校验是不是类、是不是某个基类的子类」：

```python
def resolve_class(class_path, base_class=None):
    """从一个路径字符串解析出类。

    例：resolve_class("langchain_openai:ChatOpenAI", base_class=BaseChatModel)
        → 确保解析出来的是 BaseChatModel 的子类
    """
    model_class = resolve_variable(class_path, expected_type=type)

    if not isinstance(model_class, type):
        raise ValueError(f"{class_path} 不是一个类")

    # ★校验是不是某个基类的子类
    if base_class is not None and not issubclass(model_class, base_class):
        raise ValueError(f"{class_path} 不是 {base_class.__name__} 的子类")

    return model_class
```

这个校验很重要——它能防止你把一个「不是模型的东西」当成模型用，提前在加载阶段就报错，而不是等运行时莫名其妙地崩。

---

## 5.4 代码精读：`create_chat_model()` 全流程

现在我们看模型工厂的核心——`create_chat_model()`。这个函数接收一个模型名，返回一个可调用的模型实例。我会贴出**简化但忠实于原逻辑**的版本，逐段讲解。

### 函数签名

```python
# 文件：packages/harness/deerflow/models/factory.py

def create_chat_model(
    name: str | None = None,          # 模型名（对应 config.yaml 里的 name）
    thinking_enabled: bool = False,   # 是否开启思考模式
    *,
    app_config: AppConfig | None = None,   # 显式传配置（测试用）
    attach_tracing: bool = True,           # 是否挂载 tracing 回调
    **kwargs,                              # 其他额外参数
) -> BaseChatModel:
    """从配置创建一个聊天模型实例。"""
```

### 第 1 步：读取配置，找到这个模型

```python
    config = app_config or get_app_config()   # 拿到全局配置（第 04 章讲过）
    if name is None:
        name = config.models[0].name          # 没指定就用第一个（默认模型）

    model_config = config.get_model_config(name)   # 在 models 列表里找这个模型
    if model_config is None:
        raise ValueError(f"配置里找不到模型 {name}")
```

### 第 2 步：用反射加载模型类

```python
    # model_config.use 就是 config.yaml 里写的 "langchain_openai:ChatOpenAI"
    # 用反射把它变成真正的类
    model_class = resolve_class(model_config.use, BaseChatModel)
    # 例：model_class 现在是 <class 'langchain_openai.ChatOpenAI'>
```

### 第 3 步：准备构造参数

模型类的构造函数需要很多参数（api_key、model、temperature…）。这些参数都在 `config.yaml` 里，现在要把它们取出来：

```python
    # 把 model_config（Pydantic 对象）转成字典，排除掉一些非构造参数
    model_settings = model_config.model_dump(
        exclude_none=True,
        exclude={
            "use",                 # "langchain_openai:ChatOpenAI" 不是构造参数
            "name",                # "gpt-4o" 标识符，不是构造参数
            "display_name",
            "supports_thinking",   # 这些是 deer-flow 自己用的标记
            "supports_vision",
            # ...
        },
    )
    # 此时 model_settings 大致是：
    # {"model": "gpt-4o", "api_key": "sk-xxx", "temperature": 0.7, "max_tokens": 4096, ...}
```

### 第 4 步：处理思考模式开关 ★关键★

这是整个函数最精妙的部分。回忆一下 `config.yaml`：

```yaml
- name: deepseek-reasoner
  supports_thinking: true
  when_thinking_enabled:          # ★开启思考时，加这些参数
    extra_body:
      thinking: {type: enabled}
  when_thinking_disabled:         # ★关闭思考时，加这些参数
    extra_body:
      thinking: {type: disabled}
```

代码怎么处理：

```python
    has_thinking_settings = (
        model_config.when_thinking_enabled is not None
        or model_config.thinking is not None
    )

    if thinking_enabled and has_thinking_settings:
        # 用户想开思考 + 模型支持思考 → 把 when_thinking_enabled 的参数合并进去
        if not model_config.supports_thinking:
            raise ValueError("这个模型不支持思考模式")
        model_settings.update(model_config.when_thinking_enabled)
        # → model_settings 里现在多了 extra_body: {thinking: {type: enabled}}

    if not thinking_enabled:
        # 用户不想开思考 → 用 when_thinking_disabled 的参数（或自动构造关闭参数）
        if model_config.when_thinking_disabled is not None:
            model_settings.update(model_config.when_thinking_disabled)
        else:
            # 自动构造「关闭思考」的参数（针对不同模型有不同策略）
            # ...（OpenAI、Anthropic、vLLM 的关闭方式各不相同）
```

> 💡 **为什么要这么麻烦？** 因为不同模型开关思考的「参数」完全不一样：
> - OpenAI 系：`extra_body: {thinking: {type: enabled/disabled}}`
> - Anthropic：`thinking: {type: enabled, budget_tokens: 4096}`
> - vLLM/Qwen：`extra_body: {chat_template_kwargs: {enable_thinking: true/false}}`
>
> 用 `when_thinking_enabled/disabled` 两套配置，把这些差异**完全交给用户在 YAML 里声明**，代码只负责「按需合并」。这是非常优雅的「声明式」设计。

### 第 5 步：实例化模型

```python
    # 把所有参数传给模型类的构造函数
    model_instance = model_class(**kwargs, **model_settings)
    # 等价于：
    # ChatOpenAI(model="gpt-4o", api_key="sk-xxx", temperature=0.7, ...)
```

### 第 6 步：挂载 tracing（可选）

```python
    if attach_tracing:
        callbacks = build_tracing_callbacks()   # LangSmith/Langfuse 回调
        if callbacks:
            model_instance.callbacks = [*model_instance.callbacks, *callbacks]
    return model_instance
```

tracing（链路追踪）用于把每次 LLM 调用记录到 LangSmith/Langfuse 这样的观测平台，方便调试和监控。第 06 章会看到，**Agent 主循环里的模型调用会关掉这个（`attach_tracing=False`），改在图层面挂载**，避免重复追踪。这种细节体现了对可观测性的精细控制。

### 完整流程图

```
create_chat_model(name="gpt-4o", thinking_enabled=True)
        │
        ▼
  ┌─ 读 config.yaml，找到 gpt-4o 的 ModelConfig
  │
  ├─ resolve_class("langchain_openai:ChatOpenAI")
  │     → import_module("langchain_openai")
  │     → getattr(module, "ChatOpenAI")
  │     → 得到 ChatOpenAI 类
  │
  ├─ ModelConfig → dict（提取构造参数）
  │     {model, api_key, temperature, max_tokens, ...}
  │
  ├─ 处理思考模式开关
  │     thinking_enabled=True → 合并 when_thinking_enabled 的参数
  │
  ├─ ChatOpenAI(**参数) → model_instance
  │
  └─ 挂载 tracing 回调 → 返回
```

---

## 5.5 为什么 `use` 字段要兼容这么多模型

回到第 04 章的表格，现在你应该能理解为什么这么多模型用同一个 `use` 值了：

| 模型 | `use` | 为什么 |
|------|-------|--------|
| OpenAI | `langchain_openai:ChatOpenAI` | 原生 |
| DeepSeek | `langchain_openai:ChatOpenAI` | 兼容 OpenAI 接口 + `base_url` |
| 豆包 | `langchain_openai:ChatOpenAI` | 同上 |
| Kimi | `langchain_openai:ChatOpenAI` | 同上 |
| Claude | `langchain_anthropic:ChatAnthropic` | 接口不兼容，用专用适配器 |
| Gemini | `langchain_google_genai:...` | 接口不兼容，用专用适配器 |
| Ollama | `langchain_ollama:ChatOllama` | 原生接口（/api/chat） |
| vLLM | `deerflow.models.vllm_provider:VllmChatModel` | deer-flow 自己写的适配器 |

### 为什么 vLLM 要 deer-flow 自己写适配器？

因为 vLLM 虽然也兼容 OpenAI 接口，但它在**思考模式（reasoning）**上有一些非标准行为——比如返回的 `reasoning` 字段格式特殊，在多轮工具调用对话里需要特殊处理才能正确回放。deer-flow 的 `VllmChatModel` 继承自 `ChatOpenAI`，专门处理这些差异：

```python
# 简化示意：deerflow/models/vllm_provider.py
class VllmChatModel(ChatOpenAI):
    """vLLM 专用适配器，处理非标准的 reasoning 字段。"""
    # 在完整响应、流式增量、后续工具调用轮次中
    # 都正确保留 vLLM 的 reasoning 字段
    ...
```

这就是为什么有些模型要用 `deerflow.models.xxx:PatchedXxx` 这种 deer-flow 自己的适配器——**为了修补各家模型在「思考模式」「工具调用」上的非标准行为**，让它们在 Agent 多轮对话里表现一致。

> 💡 **学习启示**：当你自己接某个新模型，如果发现它在 Agent 循环里「思考内容丢失」「工具调用出错」，多半要写一个类似的 Patched 适配器。deer-flow 已经为 DeepSeek、MiniMax、StepFun、MiMo 等都写了。

---

## 5.6 动手实验：理解一次模型创建的完整过程

我们用一个具体例子把这一章串起来。假设你的 `config.yaml` 里有：

```yaml
models:
  - name: my-deepseek
    use: langchain_openai:ChatOpenAI
    model: deepseek-chat
    api_key: $DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/v1
    supports_thinking: false
```

当 deer-flow 执行 `create_chat_model(name="my-deepseek")` 时，按顺序发生了：

1. **读配置**：`get_model_config("my-deepseek")` 找到上面这段
2. **反射加载类**：`resolve_class("langchain_openai:ChatOpenAI")`
   - `import_module("langchain_openai")` → 导入模块
   - `getattr(module, "ChatOpenAI")` → 拿到类
   - `issubclass(ChatOpenAI, BaseChatModel)` → 校验通过 ✅
3. **提取参数**：`model_dump(exclude=...)` 得到
   ```python
   {"model": "deepseek-chat",
    "api_key": "sk-真实key",      # $DEEPSEEK_API_KEY 已被替换
    "base_url": "https://api.deepseek.com/v1"}
   ```
4. **思考模式**：`supports_thinking: false`，跳过相关逻辑
5. **实例化**：`ChatOpenAI(model="deepseek-chat", api_key="sk-...", base_url="...")`
6. **返回**：一个配置好的、可以直接 `.invoke()` 调用的模型对象

整个过程对用户透明——你只写了几行 YAML，deer-flow 自动完成了「找类、校验、配参、实例化」全套流程。

---

## 5.7 代码精读补充：工厂模式的一致性

你会发现，deer-flow 里**不止模型用了工厂 + 反射**，工具、沙箱、甚至安全检测器都用同一套机制：

| 配置段落 | `use` 示例 | 反射后得到 |
|---------|-----------|-----------|
| `models` | `langchain_openai:ChatOpenAI` | 模型类 |
| `tools` | `deerflow.sandbox.tools:write_file_tool` | 工具对象 |
| `sandbox` | `deerflow.sandbox.local:LocalSandboxProvider` | 沙箱 Provider 类 |
| `safety_finish_reason.detectors` | `...:OpenAICompatibleContentFilterDetector` | 检测器类 |

**一套反射机制，服务所有「可配置的组件」**。这是 deer-flow 架构的一致性体现——学会了一个，其他的都触类旁通。这种「**用同一种模式解决同一类问题**」的设计思想，非常值得在自己的项目里借鉴。

---

## 5.8 本章小结

- ✅ **工厂模式**解决「新增模型不改代码」的问题，deer-flow 用**工厂 + 反射**实现
- ✅ **反射** `resolve_class("模块:类名")` 能在运行时根据字符串动态加载类，核心是 `import_module` + `getattr`
- ✅ `create_chat_model()` 的流程：**读配置 → 反射加载类 → 提取参数 → 处理思考开关 → 实例化 → 挂 tracing**
- ✅ **思考模式开关**用 `when_thinking_enabled/disabled` 两套参数声明，代码只负责「按需合并」，优雅地处理了不同模型的差异
- ✅ 兼容 OpenAI 接口的模型都用 `langchain_openai:ChatOpenAI`；非标准行为（vLLM、DeepSeek 思考）用 deer-flow 自己的 Patched 适配器
- ✅ 同一套反射机制服务**模型、工具、沙箱、检测器**所有可配置组件——架构一致性的典范

---

### 📋 概念检查点

1. 为什么 deer-flow 用工厂 + 反射，而不是 `if-else` 判断模型类型？
2. `resolve_class("langchain_openai:ChatOpenAI", BaseChatModel)` 这个调用，`BaseChatModel` 参数的作用是什么？
3. `when_thinking_enabled` 和 `when_thinking_disabled` 为什么需要两套配置？
4. 为什么 DeepSeek 和 OpenAI 可以用同一个 `use` 值，而 Claude 不行？

---

## ➡️ 下一章预告

**第 06 章：Lead Agent 与中间件链 ★核心★** —— 我们终于要进入 deer-flow 的心脏了！现在你已经知道怎么造一个模型（第 05 章），但一个孤立的模型还不是 Agent。下一章我们看 `make_lead_agent()` 是怎么把「模型 + 工具 + 中间件 + 提示词」组装成一个完整的、能 ReAct 循环的 Agent 的。其中最精彩的是 **19 个中间件组成的「洋葱模型」**——这是 deer-flow 工程设计的精华所在 🧅
