# 路径示例

本文档展示 DeerFlow 中使用的各种路径示例。

## 虚拟路径映射

| 虚拟路径 | 物理路径 |
|---------|---------|
| `/mnt/user-data/workspace` | `.deer-flow/threads/{id}/user-data/workspace` |
| `/mnt/user-data/uploads` | `.deer-flow/threads/{id}/user-data/uploads` |
| `/mnt/user-data/outputs` | `.deer-flow/threads/{id}/user-data/outputs` |
| `/mnt/skills` | `deer-flow/skills/` |

## API 路径

```
/api/threads/{id}/runs          # 运行代理
/api/threads/{id}/uploads       # 文件上传
/api/threads/{id}/artifacts     # 访问产物
/api/models                     # 模型列表
/api/mcp                        # MCP 配置
/api/skills                     # 技能管理
```

## 文件路径工具

```python
from deerflow.utils.paths import Paths

# 获取线程目录
thread_dir = Paths.get_thread_dir("thread_abc123")

# 虚拟路径转物理路径
physical = Paths.virtual_to_physical("/mnt/user-data/workspace/file.txt")

# 删除线程数据
Paths.delete_thread_dir("thread_abc123")
```

