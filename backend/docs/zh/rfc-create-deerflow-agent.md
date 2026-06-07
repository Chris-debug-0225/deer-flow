# RFC: 创建 DeerFlow 代理

## 概述

此 RFC 提议创建一种标准化的 DeerFlow 代理定义格式，允许用户轻松创建自定义代理。

## 背景

当前创建自定义代理需要：
1. 深入理解 LangGraph
2. 了解中间件系统
3. 手动配置所有组件
4. 处理样板代码

我们需要简化的声明式代理定义格式。

## 提案

### 代理配置文件格式

```yaml
# agents/custom-research-agent/agent.yaml
name: custom-research-agent
display_name: 自定义研究代理
description: 专门用于深度研究的代理

# 继承基础配置
extends: default

# 模型配置
model:
  name: gpt-4
  temperature: 0.7
  max_tokens: 4096

# 工具选择
tools:
  include:
    - web_search
    - web_fetch
    - read_file
    - write_file
  exclude:
    - bash

# 中间件配置
middlewares:
  - type: summarization
    enabled: true
    max_tokens: 12000
  - type: todo_list
    enabled: true

# 自定义系统提示
system_prompt: |
  你是一个专门的研究助手。你的职责是：
  1. 进行全面的信息搜索
  2. 分析来源的可靠性
  3. 提供结构化的研究报告
  4. 引用所有使用的来源

# 技能
skills:
  - academic-research
  - data-analysis

# 沙盒配置
sandbox:
  type: docker
  resources:
    memory: 4g
    cpus: 2
```

### 代理注册表

```python
class AgentRegistry:
    """管理可用代理的注册表。"""

    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}

    def register(self, agent_def: AgentDefinition):
        """注册代理定义。"""
        self._agents[agent_def.name] = agent_def

    def get(self, name: str) -> Optional[AgentDefinition]:
        """按名称获取代理定义。"""
        return self._agents.get(name)

    def list_agents(self) -> List[AgentDefinition]:
        """列出所有可用代理。"""
        return list(self._agents.values())
```

### 加载器实现

```python
class AgentLoader:
    """从配置文件加载代理定义。"""

    def load_from_file(self, path: Path) -> AgentDefinition:
        """从 YAML 文件加载代理。"""
        with open(path) as f:
            config = yaml.safe_load(f)

        return AgentDefinition(
            name=config['name'],
            display_name=config.get('display_name', config['name']),
            description=config.get('description', ''),
            model_config=self._parse_model(config.get('model', {})),
            tools_config=self._parse_tools(config.get('tools', {})),
            middlewares=self._parse_middlewares(config.get('middlewares', [])),
            system_prompt=config.get('system_prompt'),
            skills=config.get('skills', []),
            sandbox_config=config.get('sandbox', {})
        )

    def load_all_from_directory(self, directory: Path) -> List[AgentDefinition]:
        """从目录加载所有代理。"""
        agents = []
        for agent_file in directory.rglob('agent.yaml'):
            try:
                agent = self.load_from_file(agent_file)
                agents.append(agent)
            except Exception as e:
                logger.error(f"加载代理 {agent_file} 失败: {e}")
        return agents
```

### 运行时创建

```python
class AgentFactory:
    """从定义创建代理实例。"""

    def create_agent(self, agent_def: AgentDefinition) -> CompiledGraph:
        """从定义创建代理。"""
        # 1. 创建基础状态
        state = self._create_state(agent_def)

        # 2. 构建中间件链
        middleware_chain = self._build_middlewares(agent_def)

        # 3. 配置模型
        model = self._create_model(agent_def.model_config)

        # 4. 加载工具
        tools = self._load_tools(agent_def.tools_config)

        # 5. 创建图
        graph = self._build_graph(
            state=state,
            model=model,
            tools=tools,
            middlewares=middleware_chain,
            system_prompt=agent_def.system_prompt
        )

        return graph.compile()
```

## 目录结构

```
deer-flow/
├── agents/
│   ├── default/                    # 默认代理
│   │   └── agent.yaml
│   ├── custom-research-agent/      # 自定义研究代理
│   │   ├── agent.yaml
│   │   └── skills/
│   │       └── research-prompts.md
│   └── code-assistant-agent/       # 代码助手代理
│       └── agent.yaml
```

## API 集成

```python
@app.get("/api/agents")
async def list_agents() -> List[AgentInfo]:
    """列出所有可用代理。"""
    return [
        {
            "name": agent.name,
            "display_name": agent.display_name,
            "description": agent.description
        }
        for agent in agent_registry.list_agents()
    ]

@app.post("/api/agents/{agent_name}/runs")
async def run_agent(
    agent_name: str,
    request: AgentRunRequest
) -> EventSourceResponse:
    """使用指定代理运行。"""
    agent_def = agent_registry.get(agent_name)
    if not agent_def:
        raise HTTPException(404, f"代理 '{agent_name}' 不存在")

    agent = agent_factory.create_agent(agent_def)

    return EventSourceResponse(
        run_agent_stream(agent, request.input)
    )
```

## 迁移路径

### 阶段 1：配置文件支持
- 添加配置文件解析
- 保持向后兼容

### 阶段 2：代理注册表
- 实现注册表系统
- 添加发现机制

### 阶段 3：UI 集成
- 代理选择器界面
- 代理管理功能

## 好处

1. **易用性**：非技术用户可创建代理
2. **可维护性**：声明式配置易于理解
3. **可共享**：代理可作为包共享
4. **一致性**：标准化代理结构
5. **可扩展**：易于添加新功能
