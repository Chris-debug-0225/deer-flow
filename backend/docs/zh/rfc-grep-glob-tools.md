# RFC: Grep 和 Glob 工具

## 概述

添加代码库搜索工具。

## Grep 工具

在文件内容中搜索：

```python
{
    "tool": "grep",
    "arguments": {
        "pattern": "class.*Middleware",
        "file_pattern": "*.py"
    }
}
```

## Glob 工具

基于模式查找文件：

```python
{
    "tool": "glob",
    "arguments": {
        "pattern": "**/*.py"
    }
}
```

## 安全

- 路径验证
- 最大结果限制
- 文件大小限制

