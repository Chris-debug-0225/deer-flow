# 自动标题生成

本文档描述自动线程标题生成功能。

## 概述

自动标题生成在对话开始时创建简洁的线程标题。

## 配置

```yaml
title:
  enabled: true
  max_words: 6
  max_chars: 60
  model_name: null  # 使用默认模型
```

## 工作原理

1. 用户发送第一条消息
2. TitleMiddleware 调用轻量级模型
3. 生成简洁标题（例如："Python 斐波那契函数"）
4. 存储在线程状态中

## 提示模板

```
根据用户查询生成标题（最多6个词）：
{{ user_message }}

标题：
```

