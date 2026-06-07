# Apple 容器支持

本文档描述 DeerFlow 在 macOS 容器环境中的支持。

## 概述

Apple 容器支持允许 DeerFlow 在 macOS 原生容器化环境中运行，利用 Apple 的虚拟化框架实现高效的资源隔离。

## 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        macOS 主机                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    Apple 虚拟化框架                                  │ │
│  │  ┌───────────────────────────────────────────────────────────────┐ │ │
│  │  │                    Linux 容器                                  │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │ │ │
│  │  │  │                   DeerFlow 后端                            │ │ │ │
│  │  │  │  - Gateway API                                            │ │ │ │
│  │  │  │  - 嵌入式 LangGraph 运行时                                 │ │ │ │
│  │  │  │  - 沙盒执行                                                │ │ │ │
│  │  │  └─────────────────────────────────────────────────────────┘ │ │ │
│  │  └───────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## 支持的容器运行时

### OrbStack（推荐）

OrbStack 提供 macOS 上最快的 Docker 兼容容器运行：

```bash
# 安装 OrbStack
brew install orbstack

# 启动 OrbStack
orb start

# 验证 Docker 可用
docker ps
```

### Docker Desktop

Docker Desktop 也支持 Apple Silicon：

```bash
# 从 docker.com 下载 Docker Desktop
# 或使用 Homebrew
brew install --cask docker
```

### Colima（开源替代方案）

```bash
# 安装 Colima
brew install colima

# 启动 Colima
colima start --cpu 4 --memory 8

# 设置 Docker 环境
eval $(colima docker-env)
```

## 配置

### Docker 沙盒（Apple Silicon）

在 `config.yaml` 中配置：

```yaml
sandbox:
  use: deerflow.community.aio_sandbox:AioSandboxProvider
  port: 8080
  auto_start: true
  container_prefix: deer-flow-sandbox

  # Apple Silicon 优化
  platform: linux/arm64  # 强制 ARM64 镜像
```

### 镜像支持

确保使用 ARM64 架构的镜像：

```dockerfile
# 使用多架构基础镜像
FROM --platform=linux/arm64 python:3.11-slim

# 或自动检测
FROM python:3.11-slim
```

## 性能优化

### 挂载优化

使用 virtiofs 提高文件系统性能：

```yaml
sandbox:
  mounts:
    - host_path: /Users/myuser/projects
      container_path: /workspace
      read_only: false
```

### 资源限制

合理配置容器资源：

```yaml
sandbox:
  resources:
    cpus: 2
    memory: 4g
    memory_swap: 4g
```

## 故障排除

### "容器无法启动"
- 检查 Docker/OrbStack 是否正在运行
- 验证镜像支持 ARM64 架构
- 检查端口冲突

### "性能问题"
- 使用 OrbStack 而非 Docker Desktop 以获得更好性能
- 启用 Rosetta 2 用于 x86 模拟（如果需要）
- 减少容器资源限制

### "文件系统挂载问题"
- 使用绝对路径
- 检查 macOS 权限
- 验证 virtiofs 可用

## 相关配置

- [SETUP.md](./SETUP.md) - 常规设置说明
- [CONFIGURATION.md](./CONFIGURATION.md) - 详细配置选项
