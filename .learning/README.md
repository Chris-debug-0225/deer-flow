# DeerFlow 学习系列

这套学习资料的目标，不是讲一套泛化的 Agent 理论，而是帮助读者通过 `.learning/html/` 里的章节，理解 DeerFlow 当前仓库中的真实设计、真实运行边界和真实实现路径。

## 概述

当前课程包含 19 个 HTML 页面，其中 17 个核心章节已经按 DeerFlow-first 方式完成重构。重构后的核心章节都遵循同一骨架：

1. 这项能力在 DeerFlow 中解决什么问题
2. 这项能力在代码库中的位置
3. 真实运行链路或数据链路
4. 配置面与使用方式
5. 关键实现细节与权衡
6. 当前限制、边界与非目标
7. 它与 DeerFlow 其他能力的关系

这意味着读者看完之后，应该能直接回答两类问题：

- DeerFlow 里这项能力到底是在哪实现的？
- DeerFlow 里这项能力到底是怎么运行的？

## 学习目标

完成这套教程后，你将能够：

✅ 理解 DeerFlow 的默认系统主路径，而不是只记概念  
✅ 阅读和追踪 DeerFlow 的核心源码入口  
✅ 配置和使用 DeerFlow 当前已有能力  
✅ 编写自定义 Skills，并理解它们如何进入运行时  
✅ 基于当前边界扩展自定义 Agent  
✅ 从 DeerFlow 当前实现中抽取可复用的系统设计经验  

## 课程结构

### 第一部分：基础概念与背景（4个文件）

| 序号 | 文件 | 内容 | 时间 |
|------|------|------|------|
| 1 | `00-agent-fundamentals.html` | Agent基础概念与设计思想 | 45-60分钟 |
| 2 | `01-langgraph-basics.html` | LangGraph框架基础 | 50-70分钟 |
| 3 | `02-llm-and-tools.html` | LLM调用与工具系统 | 50-70分钟 |
| 4 | `03-deerflow-overview.html` | DeerFlow整体架构概览 | 60-80分钟 |

学习时间：约 4-5 小时  
难度：简单  
前置知识：基本编程概念

### 第二部分：核心模块深度学习（6个文件）

| 序号 | 文件 | 内容 | 时间 |
|------|------|------|------|
| 5 | `10-agent-execution-engine.html` | Agent执行引擎的设计与实现 | 70-90分钟 |
| 6 | `11-skills-system.html` | Skills系统：Agent的能力扩展 | 60-80分钟 |
| 7 | `12-sandbox-execution.html` | Sandbox与安全执行环境 | 70-90分钟 |
| 8 | `13-memory-system.html` | 长期记忆系统 | 60-80分钟 |
| 9 | `14-sub-agents.html` | Sub-Agents：多Agent协作 | 50-70分钟 |
| 10 | `15-gateway-api.html` | Gateway API：与外界的接口 | 60-80分钟 |

学习时间：约 8-10 小时  
难度：中等  
前置知识：完成第一部分

### 第三部分：高级特性与扩展（4个文件）

| 序号 | 文件 | 内容 | 时间 |
|------|------|------|------|
| 11 | `20-context-engineering.html` | 上下文工程：提升Agent智能 | 50-70分钟 |
| 12 | `21-model-integration.html` | 模型集成：支持多种LLM | 60-80分钟 |
| 13 | `22-channels-integration.html` | 多渠道集成：从IM到API | 50-70分钟 |
| 14 | `23-advanced-patterns.html` | 高级模式和最佳实践 | 50-70分钟 |

学习时间：约 6-8 小时  
难度：较难  
前置知识：完成第二部分

### 第四部分：实战与扩展（3个文件）

| 序号 | 文件 | 内容 | 时间 |
|------|------|------|------|
| 15 | `30-custom-skills-guide.html` | 自定义Skills完全指南 | 70-90分钟 |
| 16 | `31-building-custom-agents.html` | 构建自定义Agent | 70-90分钟 |
| 17 | `32-from-scratch-guide.html` | 从零构建Agent系统 | 80-100分钟 |

学习时间：约 8-10 小时  
难度：困难  
前置知识：完成第三部分

### 第五部分：参考与工具（2个文件）

| 序号 | 文件 | 内容 | 时间 |
|------|------|------|------|
| 18 | `40-source-code-guide.html` | 源码导航与阅读指南 | 40-60分钟 |
| 19 | `41-troubleshooting-faq.html` | 常见问题与故障排除 | 30-50分钟 |

学习时间：约 2-3 小时  
难度：简单  
前置知识：可随时查阅

## 核心章节与源码入口总索引

下面这张表适合在阅读 HTML 时配合源码一起使用。它不是完整清单，而是每章最值得先看的第一批入口。

| 章节 | 主题 | 建议先看 |
|------|------|----------|
| `02-llm-and-tools.html` | LLM调用与工具系统 | `backend/packages/harness/deerflow/tools/tools.py` `backend/packages/harness/deerflow/agents/factory.py` |
| `03-deerflow-overview.html` | DeerFlow整体架构概览 | `backend/docs/ARCHITECTURE.md` `backend/app/gateway/app.py` |
| `10-agent-execution-engine.html` | Agent执行引擎的设计与实现 | `backend/packages/harness/deerflow/agents/lead_agent/agent.py` `backend/packages/harness/deerflow/runtime/runs/worker.py` |
| `11-skills-system.html` | Skills系统：Agent的能力扩展 | `backend/packages/harness/deerflow/skills/installer.py` `backend/app/gateway/routers/skills.py` |
| `12-sandbox-execution.html` | Sandbox与安全执行环境 | `backend/packages/harness/deerflow/sandbox/tools.py` `backend/packages/harness/deerflow/sandbox/local/local_sandbox_provider.py` |
| `13-memory-system.html` | 长期记忆系统 | `backend/packages/harness/deerflow/agents/memory/storage.py` `backend/packages/harness/deerflow/agents/memory/updater.py` |
| `14-sub-agents.html` | Sub-Agents：多Agent协作 | `backend/packages/harness/deerflow/tools/builtins/task_tool.py` `backend/packages/harness/deerflow/subagents/executor.py` |
| `15-gateway-api.html` | Gateway API：与外界的接口 | `backend/app/gateway/app.py` `backend/app/gateway/routers/thread_runs.py` |
| `20-context-engineering.html` | 上下文工程：提升Agent智能 | `backend/packages/harness/deerflow/agents/lead_agent/prompt.py` `backend/packages/harness/deerflow/agents/middlewares/` |
| `21-model-integration.html` | 模型集成：支持多种LLM | `backend/packages/harness/deerflow/config/app_config.py` `backend/app/gateway/routers/models.py` |
| `22-channels-integration.html` | 多渠道集成：从IM到API | `backend/app/channels/manager.py` `backend/app/gateway/routers/channel_connections.py` |
| `23-advanced-patterns.html` | 高级模式和最佳实践 | `backend/packages/harness/deerflow/tools/builtins/tool_search.py` `backend/docs/STREAMING.md` |
| `30-custom-skills-guide.html` | 自定义Skills完全指南 | `backend/packages/harness/deerflow/skills/` `backend/app/gateway/routers/skills.py` |
| `31-building-custom-agents.html` | 构建自定义Agent | `backend/packages/harness/deerflow/client.py` `backend/docs/rfc-create-deerflow-agent.md` |
| `32-from-scratch-guide.html` | 从零构建Agent系统 | `backend/docs/ARCHITECTURE.md` `backend/docs/AUTH_DESIGN.md` |
| `40-source-code-guide.html` | 源码导航与阅读指南 | `backend/app/gateway/` `backend/packages/harness/deerflow/agents/` |
| `41-troubleshooting-faq.html` | 常见问题与故障排除 | `backend/docs/CONFIGURATION.md` `backend/docs/STREAMING.md` |

## 快速开始

### 1. 打开学习资料

在浏览器中打开 `index.html` 查看完整的课程目录：

```
.learning/html/index.html
```

### 2. 按推荐顺序学习

**推荐学习路径：**

```
第一部分（基础）
  ├─ 00-agent-fundamentals.html
  ├─ 01-langgraph-basics.html
  ├─ 02-llm-and-tools.html
  └─ 03-deerflow-overview.html
        ↓
第二部分（核心）
  ├─ 10-agent-execution-engine.html
  ├─ 11-skills-system.html
  ├─ 12-sandbox-execution.html
  ├─ 13-memory-system.html
  ├─ 14-sub-agents.html
  └─ 15-gateway-api.html
        ↓
第三部分（高级）
  ├─ 20-context-engineering.html
  ├─ 21-model-integration.html
  ├─ 22-channels-integration.html
  └─ 23-advanced-patterns.html
        ↓
第四部分（实战）
  ├─ 30-custom-skills-guide.html
  ├─ 31-building-custom-agents.html
  └─ 32-from-scratch-guide.html
        ↓
第五部分（参考）
  ├─ 40-source-code-guide.html
  └─ 41-troubleshooting-faq.html
```

### 3. 动手实践

每学完一个模块，都要：
- 理解核心概念
- 阅读源码示例
- 运行代码示例
- 做一个小项目练习

## 学习建议

### 时间规划

- 快速学习：2-3 周，只学第一部分和第二部分核心模块
- 标准学习：4-6 周，学完第一、二、三部分
- 深度学习：8-12 周，学完所有部分并做实战项目

### 学习方法

1. 先看章节里的 DeerFlow 运行职责和代码入口，再深入源码。
2. 每读完一章，至少把文中点名的 2-3 个核心文件打开一遍。
3. 对 boundary 特别敏感：哪些是当前已实现，哪些只是兼容层、RFC 或未来方向。
4. 遇到疑问时，优先回到对应文档和源码，而不是靠概念类比。

### 常见问题

**Q: 我没有编程基础，能学吗？**  
A: 可以，但更适合已经具备基本 Python 和 Web/API 概念的读者。

**Q: 学习顺序可以改变吗？**  
A: 不建议。每个部分都建立在前一部分的基础上。

**Q: 需要多长时间完成？**  
A: 取决于你的背景和学习速度。通常需要2-3个月。

**Q: 学完后能做什么？**  
A: 你可以更稳地配置、扩展、排查 DeerFlow，或者基于 DeerFlow 的真实设计去做自定义能力开发。

## 文件结构

```
.learning/
├── html/                          # 所有HTML学习资料
│   ├── index.html                # 课程目录（从这里开始）
│   ├── 00-agent-fundamentals.html
│   ├── 01-langgraph-basics.html
│   ├── 02-llm-and-tools.html
│   ├── 03-deerflow-overview.html
│   ├── 10-agent-execution-engine.html
│   ├── 11-skills-system.html
│   ├── 12-sandbox-execution.html
│   ├── 13-memory-system.html
│   ├── 14-sub-agents.html
│   ├── 15-gateway-api.html
│   ├── 20-context-engineering.html
│   ├── 21-model-integration.html
│   ├── 22-channels-integration.html
│   ├── 23-advanced-patterns.html
│   ├── 30-custom-skills-guide.html
│   ├── 31-building-custom-agents.html
│   ├── 32-from-scratch-guide.html
│   ├── 40-source-code-guide.html
│   └── 41-troubleshooting-faq.html
└── README.md                      # 本文件
```

## 相关资源

### 官方资源

- **官方网站**：https://deerflow.tech
- **GitHub仓库**：https://github.com/bytedance/deer-flow
- **官方文档**：https://github.com/bytedance/deer-flow/tree/main/docs

### 推荐阅读

- **LangGraph文档**：https://langchain-ai.github.io/langgraph/
- **LangChain文档**：https://python.langchain.com/
- **OpenAI API文档**：https://platform.openai.com/docs

### 社区资源

- **GitHub Discussions**：https://github.com/bytedance/deer-flow/discussions
- **Discord社区**：（如果有的话）
- **中文社区**：（如果有的话）

## 课程一致性校验

在批量修改 `.learning/html` 章节后，运行下面的命令确认核心章节仍然满足 DeerFlow-first 约束：

```bash
python3 scripts/validate_learning_html.py
```

校验重点包括：

- 章节标题是否仍然匹配目标章节
- 是否包含统一的 DeerFlow-first 结构标题
- 是否包含该章必须出现的核心代码锚点

说明：

- 当前 validator 校验的是 17 个核心章节，不包含 `00-agent-fundamentals.html` 和 `01-langgraph-basics.html`
- 在整套重构尚未完成的中途阶段，校验失败是预期现象；全部完成后应看到 `Validated 17 learning chapters successfully.`

## 学习进度追踪

使用以下表格追踪你的学习进度：

| 部分 | 模块 | 完成 | 日期 | 笔记 |
|------|------|------|------|------|
| 第一部分 | Agent基础概念 | ☐ | | |
| | LangGraph框架 | ☐ | | |
| | LLM调用与工具 | ☐ | | |
| | DeerFlow架构 | ☐ | | |
| 第二部分 | Agent执行引擎 | ☐ | | |
| | Skills系统 | ☐ | | |
| | Sandbox执行 | ☐ | | |
| | 记忆系统 | ☐ | | |
| | Sub-Agents | ☐ | | |
| | Gateway API | ☐ | | |
| ... | ... | ... | ... | ... |

## 学习成果评估

完成学习后，你应该能够：

### 第一部分
- [ ] 解释什么是Agent及其核心能力
- [ ] 理解LangGraph的Graph、Node、Edge、State概念
- [ ] 解释LLM API调用和Function Calling的原理
- [ ] 描述DeerFlow的整体架构和各个组件的作用

### 第二部分
- [ ] 追踪Agent执行的完整生命周期
- [ ] 编写一个简单的Skill
- [ ] 理解Sandbox的隔离机制
- [ ] 解释记忆系统的工作原理
- [ ] 描述Sub-Agents的协作方式
- [ ] 使用Gateway API调用Agent

### 第三部分
- [ ] 优化Agent的上下文
- [ ] 配置多个LLM模型
- [ ] 集成新的IM渠道
- [ ] 实现错误处理和重试机制

### 第四部分
- [ ] 开发一个完整的自定义Skill
- [ ] 构建一个自定义Agent应用
- [ ] 从零实现一个简化版的Agent系统

## 📝 更新日志

### 版本 1.0（2026-06-11）
- ✅ 完成第一部分（4个文件）
- ✅ 创建课程目录和README
- 📅 第二部分开发中...

## 📧 反馈与建议

如果你对这套教程有任何建议或发现了错误，欢迎：

1. 在GitHub上提Issue
2. 提交Pull Request
3. 在讨论区留言

## 📄 许可证

本教程采用 MIT 许可证。你可以自由使用、修改和分发。

## 🙏 致谢

感谢DeerFlow团队和所有贡献者的工作。这套教程的目标是帮助更多开发者学习和使用DeerFlow。

---

**开始学习：** 打开 `index.html` 开始你的Agent学习之旅！

**祝你学习愉快！** 🚀
