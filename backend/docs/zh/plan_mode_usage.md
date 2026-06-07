# 计划模式使用

本文档描述如何使用带 TodoList 中间件的计划模式。

## 概述

计划模式提供 `write_todos` 工具帮助代理：
- 分解复杂任务
- 跟踪任务进度
- 向用户展示工作流

## 启用

```python
config = RunnableConfig(
    configurable={
        "thread_id": "thread_123",
        "is_plan_mode": True  # 启用计划模式
    }
)
```

## 使用场景

代理在以下情况使用 TodoList：
- 复杂的多步骤任务（> 3 步骤）
- 需要仔细规划的任务
- 用户明确要求计划

## 任务状态

- `pending`：未开始
- `in_progress`：进行中
- `completed`：已完成

## 示例

```python
# 创建带计划模式的代理
agent = make_lead_agent(config_with_plan_mode)

# 代理自动使用 write_todos 工具
# 用户可以在 UI 中查看任务进度
```

