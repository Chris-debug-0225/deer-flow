# 认证设计

本文档描述 DeerFlow 的认证系统设计。

## 概述

认证系统提供：
- 用户身份验证
- 会话管理
- 访问控制
- 用户隔离

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        认证架构                                  │
└─────────────────────────────────────────────────────────────────┘

用户请求
    │
    ▼
┌─────────────────┐
│   Nginx (2026)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   Gateway API   │◄───►│   Auth Service  │
│   (FastAPI)     │     │   (认证服务)     │
└────────┬────────┘     └─────────────────┘
         │
         ▼
    受保护资源
```

## 认证流程

### 1. OAuth 登录

```
用户 → 点击"使用 GitHub 登录"
    ↓
后端 → 生成 state，重定向到 GitHub
    ↓
GitHub → 用户授权
    ↓
后端 → 验证 state，获取令牌，创建会话
    ↓
用户 → 接收 JWT cookie，访问受保护资源
```

### 2. 会话验证

```
请求 → 携带 JWT cookie
    ↓
Gateway → 验证 JWT 签名和过期时间
    ↓
        有效 → 允许访问
        无效 → 返回 401
```

## 组件

### JWT 令牌

- **Access Token**：短期（15 分钟），用于 API 访问
- **Refresh Token**：长期（7 天），用于刷新 Access Token

### 会话存储

- 支持 SQLite（开发）
- 支持 Redis（生产）

### 用户模型

```python
class User:
    id: str
    email: str
    name: str
    auth_provider: str  # github, google
    created_at: datetime
    is_active: bool
```

## 安全特性

1. **CSRF 防护**：双提交 cookie 模式
2. **安全 Cookie**：HttpOnly, Secure, SameSite
3. **会话固定防护**：登录时重新生成会话
4. **速率限制**：防止暴力破解

## 配置

```yaml
auth:
  enabled: true
  jwt_secret: ${JWT_SECRET_KEY}
  token_expiry: 900  # 15 分钟
  refresh_token_expiry: 604800  # 7 天
```

## API 端点

- `POST /auth/login` - 登录
- `POST /auth/logout` - 登出
- `POST /auth/refresh` - 刷新令牌
- `GET /auth/user` - 获取当前用户

## 用户隔离

每个用户的数据完全隔离：
- 线程存储在独立目录
- 沙盒按用户隔离
- MCP 配置按用户存储

