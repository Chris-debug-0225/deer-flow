# Docker 认证测试

本文档描述在 Docker 环境中测试认证的注意事项。

## 网络架构

```
Nginx (2026) → Gateway (8001) → Auth Service
```

## 常见问题

1. **Cookie 传递**：确保 Nginx 传递 cookie 到后端
2. **OAuth 回调**：使用正确的回调 URL
3. **DNS 解析**：容器可能需要外部 DNS

## 配置

```yaml
services:
  nginx:
    ports:
      - "2026:2026"
  gateway:
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
```

## 测试

```bash
# 测试登录流程
curl http://localhost:2026/auth/github/login

# 验证 cookie
curl -v http://localhost:2026/api/threads
```

