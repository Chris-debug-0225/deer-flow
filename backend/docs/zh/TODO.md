# 待办事项列表

## 已完成的功能

- [x] 仅在首次调用文件系统或 bash 工具后启动沙盒
- [x] 为整个流程添加澄清流程
- [x] 实现上下文摘要机制以避免上下文爆炸
- [x] 集成 MCP（模型上下文协议）以实现可扩展工具
- [x] 添加文件上传支持，自动转换文档
- [x] 实现自动线程标题生成
- [x] 添加带 TodoList 中间件的计划模式
- [x] 使用 ViewImageMiddleware 添加视觉模型支持
- [x] 带有 SKILL.md 格式的技能系统
- [x] 在 `packages/harness/deerflow/tools/builtins/task_tool.py` 中将 `time.sleep(5)` 替换为 `asyncio.sleep()`（子代理轮询）

## 计划功能

- [ ] 池化沙盒资源以减少沙盒容器数量
- [ ] 添加认证/授权层
- [ ] 实现速率限制
- [ ] 添加指标和监控
- [ ] 上传中支持更多文档格式
- [ ] 技能市场 / 远程技能安装
- [ ] 优化代理热路径中的异步并发（IM 渠道多任务场景）
- [ ] 在 `packages/harness/deerflow/sandbox/local/local_sandbox.py` 中将 `subprocess.run()` 替换为 `asyncio.create_subprocess_shell()`
  - 在社区工具（tavily、jina_ai、firecrawl、infoquest、image_search）中将同步 `requests` 替换为 `httpx.AsyncClient`
  - [x] 在 title_middleware 和内存更新器中将同步 `model.invoke()` 替换为异步 `model.ainvoke()`
  - 考虑为剩余的阻塞文件 I/O 使用 `asyncio.to_thread()` 包装器
  - 对于生产环境：为长时间运行的代理工作负载调整 Gateway 工作程序/运行时设置

## 已解决的问题

- [x] 确保 `state.artifacts` 中没有重复文件
- [x] 长时间思考但内容为空（答案在思考过程中）

