# Guardrails 设计

本文档描述了 DeerFlow 中 tool-call pre-authorization guardrails 的设计。

## 概述

Guardrails 允许代理在调用敏感或破坏性工具之前征求用户批准。这为代理行为添加了安全检查层。

## 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Guardrails 系统                                 │
└─────────────────────────────────────────────────────────────────────────┘

                      ┌─────────────────────────┐
                      │   GuardrailsProvider    │ （抽象）
                      │  - pre_approval()       │
                      │  - on_action()          │
                      │  - filter_action()      │
                      └────────────┬────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                                         │
              ▼                                         ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│  ManualGuardrails       │              │  AutoGuardrails         │
│  Provider               │              │  Provider               │
│                         │              │                         │
│  - 等待用户批准          │              │  - 基于启发式自动批准    │
│  - 交互式对话            │              │  - 基于条件允许/拒绝     │
└─────────────────────────┘              └─────────────────────────┘
```

## 工具调用前批准流程

1. 代理请求调用工具
2. GuardrailsProvider 拦截调用
3. 检查工具是否在保护列表中
4. 如果受保护：
   - ManualGuardrails：暂停并询问用户批准
   - AutoGuardrails：基于启发式评估
5. 获得批准后，工具执行
6. 结果被返回给代理

## 三种提供者选项

### 1. ManualGuardrailsProvider

完全交互式模式。每个保护工具调用都暂停等待用户确认。

**使用场景**：
- 生产环境需要人工监督
- 敏感操作（文件删除、系统命令）
- 调试和测试

**配置**：
```python
from deerflow.guardrails import ManualGuardrailsProvider

provider = ManualGuardrailsProvider(
    protected_tools=["bash", "write_file", "delete_file"]
)
```

### 2. AutoGuardrailsProvider

基于启发式自动批准/拒绝。适用于自动化工作流。

**使用场景**：
- 已知安全模式
- 自动化 CI/CD 工作流
- 受信任环境

**配置**：
```python
from deerflow.guardrails import AutoGuardrailsProvider

provider = AutoGuardrailsProvider(
    protected_tools=["bash"],
    rules=[
        # 只允许读取命令
        {"tool": "bash", "allow": "^ls|^cat|^grep|^find"},
    ]
)
```

### 3. DisabledGuardrailsProvider

无保护措施。所有工具调用无中断执行。

**使用场景**：
- 开发和测试
- 完全受信任环境
- 沙盒隔离环境

**配置**：
```python
from deerflow.guardrails import DisabledGuardrailsProvider

provider = DisabledGuardrailsProvider()
```

## 集成到代理

```python
from deerflow.agents.lead_agent.agent import make_lead_agent
from deerflow.guardrails import ManualGuardrailsProvider

# 创建 guardrails 提供者
guardrails = ManualGuardrailsProvider(
    protected_tools=["bash", "write_file"]
)

# 启用 guardrails 创建代理
agent = make_lead_agent(
    config=config,
    guardrails=guardrails
)
```

## 默认保护工具

| 工具 | 风险级别 | 说明 |
|------|----------|------|
| `bash` | 高 | 任意代码执行 |
| `write_file` | 中 | 文件系统修改 |
| `delete_file` | 高 | 破坏性操作 |
| `str_replace` | 中 | 代码修改 |

## 自定义保护

### 添加自定义工具

```python
provider = ManualGuardrailsProvider(
    protected_tools=["bash", "custom_api_call"]
)
```

### 自定义批准提示

```python
provider = ManualGuardrailsProvider(
    protected_tools=["bash"],
    approval_prompt=lambda tool, args: f"""
代理想要执行：{tool}({args})

这可能有风险。批准吗？（yes/no）
"""
)
```

## 注意事项

- Guardrails 是**可选的** — 默认不启用
- 生产环境建议启用适当保护
- 结合 Docker 沙盒提供多层安全
- 始终验证用户输入和工具参数
