# RFC: 提取共享模块

## 概述

将通用组件提取到共享包。

## 当前问题

- 工具逻辑重复
- MCP 代码分散
- 无中央工具位置

## 提案

```
packages/harness/deerflow/
├── core/           # 基础类型和工具
├── tools/          # 共享工具基类
└── mcp/            # MCP 共享逻辑
```

## 基类

```python
class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass
```

## 好处

- 代码重用
- 一致性
- 可测试性

