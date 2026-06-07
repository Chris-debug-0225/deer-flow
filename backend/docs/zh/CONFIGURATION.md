# 配置指南

本指南解释如何为环境配置 DeerFlow。

## 配置版本控制

`config.example.yaml` 包含一个 `config_version` 字段，用于跟踪模式更改。当示例版本高于本地 `config.yaml` 时，应用程序会发出启动警告：

```
WARNING - 您的 config.yaml（版本 0）已过期 — 最新版本是 1。
运行 `make config-upgrade` 将新字段合并到您的配置中。
```

- 配置中**缺少 `config_version`** 被视为版本 0。
- 运行 `make config-upgrade` 自动合并缺失字段（保留现有值，创建 `.bak` 备份）。
- 更改配置模式时，在 `config.example.yaml` 中增加 `config_version`。

## 配置章节

### 模型

配置代理可用的 LLM 模型：

```yaml
models:
  - name: gpt-4                    # 内部标识符
    display_name: GPT-4            # 人类可读名称
    use: langchain_openai:ChatOpenAI  # LangChain 类路径
    model: gpt-4                   # API 模型标识符
    api_key: $OPENAI_API_KEY       # API 密钥（使用环境变量）
    max_tokens: 4096               # 每次请求最大令牌数
    temperature: 0.7               # 采样温度
```

**支持的提供商**：
- OpenAI (`langchain_openai:ChatOpenAI`)
- Anthropic (`langchain_anthropic:ChatAnthropic`)
- DeepSeek (`langchain_deepseek:ChatDeepSeek`)
- Xiaomi MiMo (`deerflow.models.patched_mimo:PatchedChatMiMo`)
- Claude Code OAuth (`deerflow.models.claude_provider:ClaudeChatModel`)
- Codex CLI (`deerflow.models.openai_codex_provider:CodexChatModel`)
- 任何 LangChain 兼容的提供商

CLI 支持提供商示例：

```yaml
models:
  - name: gpt-5.4
    display_name: GPT-5.4 (Codex CLI)
    use: deerflow.models.openai_codex_provider:CodexChatModel
    model: gpt-5.4
    supports_thinking: true
    supports_reasoning_effort: true

  - name: claude-sonnet-4.6
    display_name: Claude Sonnet 4.6 (Claude Code OAuth)
    use: deerflow.models.claude_provider:ClaudeChatModel
    model: claude-sonnet-4-6
    max_tokens: 4096
    supports_thinking: true
```

**CLI 支持提供商的认证行为**：
- `CodexChatModel` 从 `~/.codex/auth.json` 加载 Codex CLI 认证
- Codex Responses 端点目前拒绝 `max_tokens` 和 `max_output_tokens`，因此 `CodexChatModel` 不公开请求级令牌上限
- `ClaudeChatModel` 接受 `CLAUDE_CODE_OAUTH_TOKEN`、`ANTHROPIC_AUTH_TOKEN`、`CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`、`CLAUDE_CODE_CREDENTIALS_PATH` 或纯文本 `~/.claude/.credentials.json`
- 在 macOS 上，DeerFlow 不会自动探测 Keychain。需要时使用 `scripts/export_claude_code_oauth.py` 显式导出 Claude Code 认证

要将 OpenAI 的 `/v1/responses` 端点与 LangChain 一起使用，继续使用 `langchain_openai:ChatOpenAI` 并设置：

```yaml
models:
  - name: gpt-5-responses
    display_name: GPT-5 (Responses API)
    use: langchain_openai:ChatOpenAI
    model: gpt-5
    api_key: $OPENAI_API_KEY
    use_responses_api: true
    output_version: responses/v1
```

对于 OpenAI 兼容网关（例如 Novita 或 OpenRouter），继续使用 `langchain_openai:ChatOpenAI` 并设置 `base_url`：

```yaml
models:
  - name: novita-deepseek-v3.2
    display_name: Novita DeepSeek V3.2
    use: langchain_openai:ChatOpenAI
    model: deepseek/deepseek-v3.2
    api_key: $NOVITA_API_KEY
    base_url: https://api.novita.ai/openai
    supports_thinking: true
    when_thinking_enabled:
      extra_body:
        thinking:
          type: enabled

  - name: minimax-m3
    display_name: MiniMax M3
    use: langchain_openai:ChatOpenAI
    model: MiniMax-M3
    api_key: $MINIMAX_API_KEY
    base_url: https://api.minimax.io/v1
    max_tokens: 4096
    temperature: 1.0  # MiniMax 要求温度在 (0.0, 1.0] 范围内
    supports_vision: true
```

如果您的 OpenRouter 密钥位于不同的环境变量名称中，请显式将 `api_key` 指向该变量（例如 `api_key: $OPENROUTER_API_KEY`）。

**思考模型**：
某些模型支持复杂推理的"思考"模式：

```yaml
models:
  - name: deepseek-v3
    supports_thinking: true
    when_thinking_enabled:
      extra_body:
        thinking:
          type: enabled
```

**通过 OpenAI 兼容网关使用 Gemini 思考模式**：

通过 OpenAI 兼容代理（Vertex AI OpenAI 兼容端点、AI Studio 或第三方网关）路由 Gemini 并启用思考模式时，API 会在响应中返回的每个工具调用对象上附加一个 `thought_signature`。每个后续重播这些助手消息的请求**必须**在工具调用条目上回显这些签名，否则 API 返回：

```
HTTP 400 INVALID_ARGUMENT: N. 内容块中的函数调用 `<tool>` 缺少 `thought_signature`。
```

标准 `langchain_openai:ChatOpenAI` 在序列化消息时静默丢弃 `thought_signature`。改用 `deerflow.models.patched_openai:PatchedChatOpenAI` — 它将工具调用签名（来自 `AIMessage.additional_kwargs["tool_calls"]`）重新注入每个传出负载：

```yaml
models:
  - name: gemini-2.5-pro-thinking
    display_name: Gemini 2.5 Pro (Thinking)
    use: deerflow.models.patched_openai:PatchedChatOpenAI
    model: google/gemini-2.5-pro-preview   # 您的网关期望的模型名称
    api_key: $GEMINI_API_KEY
    base_url: https://<your-openai-compat-gateway>/v1
    max_tokens: 16384
    supports_thinking: true
    supports_vision: true
    when_thinking_enabled:
      extra_body:
        thinking:
          type: enabled
```

对于**不启用思考模式**访问 Gemini（例如通过 OpenRouter 不激活思考模式），普通的 `langchain_openai:ChatOpenAI` 配合 `supports_thinking: false` 就足够了，不需要补丁。

**通过 OpenAI 兼容 API 使用 MiMo 思考模式**：

MiMo 在思考模式下在助手消息上返回 `reasoning_content`。在带工具调用的多轮代理对话中，后续请求必须保留助手消息上的历史 `reasoning_content`，否则 MiMo API 可能返回 HTTP 400。标准 `langchain_openai:ChatOpenAI` 会丢弃此提供商特定字段，因此使用 `deerflow.models.patched_mimo:PatchedChatMiMo`：

对于即用即付 API 密钥（`sk-...`），使用 `https://api.xiaomimimo.com/v1`。对于 Token Plan 密钥（`tp-...`），使用 MiMo 控制台中显示的区域性 Token Plan Base URL，例如 `https://token-plan-cn.xiaomimimo.com/v1`。MiMo 将这些密钥类型记录为分开且不可互换的。

`PatchedChatMiMo` 与模型 ID 无关。为您配置的每个 MiMo 思考模型条目使用它，包括由 `subagents.*.model` 覆盖引用的模型条目（例如 `mimo-v2.5-pro`、`mimo-v2.5`、`mimo-v2-pro`、`mimo-v2-omni` 或 `mimo-v2-flash`）。

```yaml
models:
  - name: mimo-v2.5-pro
    display_name: MiMo V2.5 Pro
    use: deerflow.models.patched_mimo:PatchedChatMiMo
    model: mimo-v2.5-pro
    api_key: $MIMO_API_KEY
    base_url: https://api.xiaomimimo.com/v1
    max_tokens: 8192
    supports_thinking: true
    supports_vision: false
    when_thinking_enabled:
      extra_body:
        thinking:
          type: enabled
    when_thinking_disabled:
      extra_body:
        thinking:
          type: disabled
```

`PatchedChatMiMo` 保留 MiMo 的 `choices[].message.reasoning_content`、流式传输 `delta.reasoning_content` 和请求历史助手 `reasoning_content` 字段。它不重用 DeepSeek 提供商。

### 工具组

将工具组织成逻辑组：

```yaml
tool_groups:
  - name: web          # Web 浏览和搜索
  - name: file:read    # 只读文件操作
  - name: file:write   # 写入文件操作
  - name: bash         # Shell 命令执行
```

### 工具

配置代理可用的特定工具：

```yaml
tools:
  - name: web_search
    group: web
    use: deerflow.community.tavily.tools:web_search_tool
    max_results: 5
    # api_key: $TAVILY_API_KEY  # 可选
```

**内置工具**：
- `web_search` - 搜索 Web（DuckDuckGo、Tavily、Exa、InfoQuest、Firecrawl）
- `web_fetch` - 获取网页（Jina AI、Exa、InfoQuest、Firecrawl）
- `ls` - 列出目录内容
- `read_file` - 读取文件内容
- `write_file` - 写入文件内容
- `str_replace` - 文件中的字符串替换
- `bash` - 执行 bash 命令

### 沙盒

DeerFlow 支持多种沙盒执行模式。在 `config.yaml` 中配置首选模式：

**本地执行**（在主机机器上直接运行沙盒代码）：
```yaml
sandbox:
   use: deerflow.sandbox.local:LocalSandboxProvider # 本地执行
   allow_host_bash: false # 默认；除非显式重新启用，否则禁用主机 bash
```

**Docker 执行**（在隔离的 Docker 容器中运行沙盒代码）：
```yaml
sandbox:
   use: deerflow.community.aio_sandbox:AioSandboxProvider # 基于 Docker 的沙盒
```

**带 Kubernetes 的 Docker 执行**（通过 provisioner 服务在 Kubernetes Pod 中运行沙盒代码）：

此模式在**主机机器的集群**上的隔离 Kubernetes Pod 中运行每个沙盒。需要 Docker Desktop K8s、OrbStack 或类似的本地 K8s 设置。

```yaml
sandbox:
   use: deerflow.community.aio_sandbox:AioSandboxProvider
   provisioner_url: http://provisioner:8002
```

使用 Docker 开发（`make docker-start`）时，仅当配置此 provisioner 模式时 DeerFlow 才会启动 `provisioner` 服务。在本地或普通 Docker 沙盒模式中，`provisioner` 被跳过。

有关详细配置、先决条件和故障排除，请参阅 [Provisioner 设置指南](../../docker/provisioner/README.md)。

在本地执行或基于 Docker 的隔离之间选择：

**选项 1：本地沙盒**（默认，设置更简单）：
```yaml
sandbox:
  use: deerflow.sandbox.local:LocalSandboxProvider
  allow_host_bash: false
```

`allow_host_bash` 故意默认为 `false`。DeerFlow 的本地沙盒是一种主机端便利模式，而不是安全的 shell 隔离边界。如果您需要 `bash`，请优先选择 `AioSandboxProvider`。仅对完全受信任的本地单用户工作流设置 `allow_host_bash: true`。

**选项 2：Docker 沙盒**（隔离，更安全）：
```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  port: 8080
  auto_start: true
  container_prefix: deer-flow-sandbox

  # 可选：附加挂载
  mounts:
    - host_path: /path/on/host
      container_path: /path/in/container
      read_only: false
```

配置 `sandbox.mounts` 时，DeerFlow 在代理提示中公开那些 `container_path` 值，以便代理可以发现并直接操作挂载目录，而不是假设所有内容都必须位于 `/mnt/user-data` 下。

对于使用 localhost 的裸机 Docker 沙盒运行，DeerFlow 默认将沙盒 HTTP 端口绑定到 `127.0.0.1`，因此它不会暴露在每台主机接口上。通过 `host.docker.internal` 连接的 Docker-outside-of-Docker 部署保持广泛的旧版绑定以兼容。如果您的部署需要不同的绑定地址，请显式设置 `DEER_FLOW_SANDBOX_BIND_HOST`。

### 技能

为专业工作流配置技能目录：

```yaml
skills:
  # 主机路径（可选，默认：../skills）
  path: /custom/path/to/skills

  # 容器挂载路径（默认：/mnt/skills）
  container_path: /mnt/skills
```

**技能的工作原理**：
- 技能存储在 `deer-flow/skills/{public,custom}/`
- 每个技能都有一个带元数据的 `SKILL.md` 文件
- 技能自动被发现和加载
- 在本地和 Docker 沙盒中通过路径映射可用

**每个代理的技能过滤**：
自定义代理可以通过在其 `config.yaml`（位于 `workspace/agents/<agent_name>/config.yaml`）中定义 `skills` 字段来限制加载的技能：
- **省略或 `null`**：加载所有全局启用的技能（默认回退）。
- **`[]`（空列表）**：为此特定代理禁用所有技能。
- **`["skill-name"]`**：仅加载显式指定的技能。

### 标题生成

自动生成对话标题：

```yaml
title:
  enabled: true
  max_words: 6
  max_chars: 60
  model_name: null  # 使用列表中的第一个模型
```

### GitHub API Token（GitHub 深度研究技能可选）

默认 GitHub API 速率限制非常严格。对于频繁的项目研究，我们建议使用具有只读权限的个人访问令牌（PAT）进行配置。

**配置步骤**：
1. 取消 `.env` 文件中 `GITHUB_TOKEN` 行的注释并添加您的个人访问令牌
2. 重新启动 DeerFlow 服务以应用更改

## 环境变量

DeerFlow 支持使用 `$` 前缀进行环境变量替换：

```yaml
models:
  - api_key: $OPENAI_API_KEY  # 从环境读取
```

**常见环境变量**：
- `OPENAI_API_KEY` - OpenAI API 密钥
- `ANTHROPIC_API_KEY` - Anthropic API 密钥
- `DEEPSEEK_API_KEY` - DeepSeek API 密钥
- `MIMO_API_KEY` - Xiaomi MiMo API 密钥
- `NOVITA_API_KEY` - Novita API 密钥（OpenAI 兼容端点）
- `TAVILY_API_KEY` - Tavily 搜索 API 密钥
- `DEER_FLOW_PROJECT_ROOT` - 相对运行时路径的项目根目录
- `DEER_FLOW_CONFIG_PATH` - 自定义配置文件路径
- `DEER_FLOW_EXTENSIONS_CONFIG_PATH` - 自定义扩展配置文件路径
- `DEER_FLOW_HOME` - 运行时状态目录（默认在项目根目录下的 `.deer-flow`）
- `DEER_FLOW_SKILLS_PATH` - `skills.path` 省略时的技能目录
- `GATEWAY_ENABLE_DOCS` - 设置为 `false` 以禁用 Swagger UI（`/docs`）、ReDoc（`/redoc`）和 OpenAPI 模式（`/openapi.json`）端点（默认：`true`）

## 配置位置

配置文件应放置在**项目根目录**（`deer-flow/config.yaml`）。当进程可能从另一个工作目录启动时设置 `DEER_FLOW_PROJECT_ROOT`，或设置 `DEER_FLOW_CONFIG_PATH` 指向特定文件。

## 配置优先级

DeerFlow 按此顺序搜索配置：

1. 代码中通过 `config_path` 参数指定的路径
2. `DEER_FLOW_CONFIG_PATH` 环境变量中的路径
3. `DEER_FLOW_PROJECT_ROOT` 下的 `config.yaml`，或当 `DEER_FLOW_PROJECT_ROOT` 未设置时的当前工作目录
4. 为 monorepo 兼容性的传统后端/仓库根目录位置

## 最佳实践

1. **将 `config.yaml` 放在项目根目录** - 如果运行时在其他地方启动，请设置 `DEER_FLOW_PROJECT_ROOT`
2. **永远不要提交 `config.yaml`** - 它已经在 `.gitignore` 中
3. **对密钥使用环境变量** - 不要硬编码 API 密钥
4. **保持 `config.example.yaml` 更新** - 记录所有新选项
5. **在本地测试配置更改** - 在部署之前
6. **生产环境使用 Docker 沙盒** - 更好的隔离和安全性

## 故障排除

### "找不到配置文件"
- 确保 `config.yaml` 存在于**项目根**目录（`deer-flow/config.yaml`）
- 如果运行时从项目根目录外启动，请设置 `DEER_FLOW_PROJECT_ROOT`
- 或者，将 `DEER_FLOW_CONFIG_PATH` 环境变量设置为自定义位置

### "API 密钥无效"
- 验证环境变量设置正确
- 检查环境变量引用是否使用了 `$` 前缀

### "技能未加载"
- 检查 `deer-flow/skills/` 目录是否存在
- 验证技能有有效的 `SKILL.md` 文件
- 如果使用自定义路径，请检查 `skills.path` 或 `DEER_FLOW_SKILLS_PATH`

### "Docker 沙盒无法启动"
- 确保 Docker 正在运行
- 检查端口 8080（或配置的端口）是否可用
- 验证 Docker 镜像是否可访问

## 示例

有关所有配置选项的完整示例，请参阅 `config.example.yaml`。

