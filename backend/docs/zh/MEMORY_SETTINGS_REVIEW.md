# 内存设置审查

本文档审查内存相关配置。

## 问题

1. 沙盒无清理策略
2. 标题生成无内存限制
3. 缺少全局上限

## 建议配置

```yaml
sandbox:
  lifecycle:
    idle_timeout: 300
    max_lifetime: 3600
  pool:
    max_size: 10

memory_management:
  process:
    max_heap_mb: 4096
  monitoring:
    warning_threshold: 70
    critical_threshold: 85
```

