# 认证升级指南

本文档描述如何升级到新的认证系统。

## 升级步骤

### 1. 备份数据

```bash
cp .deer-flow/database.db .deer-flow/database.db.backup
cp config.yaml config.yaml.backup
```

### 2. 更新配置

添加认证配置：

```yaml
auth:
  enabled: true
  jwt_secret: ${JWT_SECRET_KEY}
  oauth:
    github:
      client_id: ${GITHUB_CLIENT_ID}
      client_secret: ${GITHUB_CLIENT_SECRET}
```

### 3. 运行迁移

```bash
python scripts/migrate_auth.py
```

### 4. 重启服务

```bash
make restart-backend
```

## 回滚

```bash
cp .deer-flow/database.db.backup .deer-flow/database.db
cp config.yaml.backup config.yaml
make restart-backend
```

