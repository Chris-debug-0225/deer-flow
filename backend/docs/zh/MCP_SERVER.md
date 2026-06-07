# MCP 服务器

本文档描述如何配置 MCP（模型上下文协议）服务器。

## 概述

MCP 服务器提供外部工具：
- GitHub 集成
- 数据库访问
- 搜索功能
- 文件系统操作

## 配置

```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "$GITHUB_TOKEN"
      }
    }
  }
}
```

## 常用服务器

- **github**：仓库管理、问题跟踪
- **postgres**：数据库查询
- **brave-search**：Web 搜索
- **filesystem**：文件操作

## API

```http
GET /api/mcp/config      # 获取配置
PUT /api/mcp/config      # 更新配置
GET /api/mcp/tools       # 列出工具
```

## 安全

- 使用环境变量存储密钥
- 每个服务器独立进程
- 可单独启用/禁用

