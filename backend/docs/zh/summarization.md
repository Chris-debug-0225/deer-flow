# 上下文摘要机制

本文档描述 DeerFlow 中实现的上下文摘要机制，用于避免长时间对话中的上下文爆炸。

## 问题：上下文爆炸

在长时间对话中：
- 消息列表不断增长
- 超出模型的上下文窗口限制
- 导致错误和性能下降
- 早期重要信息丢失

## 解决方案：上下文摘要

当上下文接近限制时：
1. 保留最近 N 条消息（保持上下文）
2. 摘要旧消息为简洁摘要
3. 用摘要替换旧消息
4. 继续对话

## 配置

```yaml
summarization:
  enabled: true
  trigger: token_count      # 触发条件：token_count / message_count / ratio
  max_tokens: 12000         # 最大令牌数，触发摘要
  keep_recent_count: 10     # 保留的最新消息数
```

## 摘要流程

```
1. 监控上下文大小
   ↓
2. 检查是否超过阈值
   ↓
3. 保留最近 N 条消息
   ↓
4. 摘要旧消息
   ↓
5. 替换旧消息为摘要
   ↓
6. 继续对话
```

## 实现

### SummarizationMiddleware

位置：`packages/harness/deerflow/agents/middlewares/summarization_middleware.py`

**职责**：
- 监控线程状态中的令牌数
- 当接近限制时触发摘要
- 管理摘要过程
- 保留重要消息

### 摘要策略

1. **基于令牌计数**（默认）
   - 跟踪累积令牌数
   - 达到 `max_tokens` 阈值时触发
   - 最准确的方法

2. **基于消息计数**
   - 当消息数超过限制时触发
   - 简单但不考虑消息长度

3. **基于比例**
   - 上下文窗口使用达到一定百分比时触发
   - 自适应但依赖于估计

### 消息选择

```python
# 保留的消息类型
KEEP_TYPES = [
    "system",           # 系统提示
    "human_recent",     # 最近的用户消息
    "ai_recent",        # 最近的助手回复
    "tool_recent",      # 最近的工具结果
]

# 摘要的消息类型
SUMMARIZE_TYPES = [
    "old_conversation", # 旧对话历史
    "tool_history",    # 旧工具调用
]
```

## 摘要质量

### 保留关键信息

摘要提示指导 LLM：
- 保留关键事实和决策
- 保留未完成任务
- 保留用户偏好
- 移除冗余或已解决的内容

### 摘要提示

```jinja2
请摘要以下对话，保留关键信息：

{{ messages }}

摘要要求：
- 保留所有重要事实和决策
- 保留任何未完成任务
- 保留用户偏好和约束
- 使用简洁的项目符号格式
```

## 与中间件链集成

```
中间件链：
1. ThreadDataMiddleware
2. UploadsMiddleware
3. SandboxMiddleware
4. SummarizationMiddleware  ← 在这里
5. TitleMiddleware
6. TodoListMiddleware（如果计划模式）
7. ViewImageMiddleware
8. ClarificationMiddleware
```

## 使用示例

### 默认配置

```yaml
summarization:
  enabled: true
  trigger: token_count
  max_tokens: 12000
  keep_recent_count: 10
```

### 禁用摘要

```yaml
summarization:
  enabled: false
```

### 自定义阈值

```yaml
summarization:
  enabled: true
  trigger: ratio
  max_ratio: 0.8          # 80% 上下文窗口
  keep_recent_count: 5
```

## 注意事项

- 摘要**异步执行**以避免阻塞
- 使用专用轻量级模型进行摘要（可配置）
- 摘要错误优雅降级（保留更多消息）
- 用户可以通过配置完全禁用
