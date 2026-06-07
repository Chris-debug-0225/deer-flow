# 文件上传

本文档描述 DeerFlow 中的文件上传功能。

## 概述

文件上传允许用户：
- 上传文档、图像和其他文件
- 自动将文档转换为 Markdown
- 在代理上下文中访问上传的文件
- 管理每个线程的附件

## 支持的文件类型

### 文档
- PDF (`.pdf`)
- Word (`.doc`, `.docx`)
- PowerPoint (`.ppt`, `.pptx`)
- Excel (`.xls`, `.xlsx`)
- 文本 (`.txt`, `.md`, `.csv`)
- HTML (`.html`, `.htm`)

### 图像
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)
- SVG (`.svg`)

### 其他
- 代码文件 (`.py`, `.js`, `.ts`, `.java`, `.cpp`, `.go`, `.rs` 等)
- 配置文件 (`.json`, `.yaml`, `.yml`, `.xml`)

## 上传流程

```
1. 客户端上传文件
   POST /api/threads/{thread_id}/uploads
   Content-Type: multipart/form-data
   
2. Gateway 处理文件
   - 验证文件类型和大小
   - 存储在临时位置
   - 如果是文档：通过 markitdown 转换为 Markdown

3. 保存到线程目录
   .deer-flow/threads/{thread_id}/user-data/uploads/

4. 返回响应
   {
     "files": [{
       "filename": "doc.pdf",
       "original_name": "document.pdf",
       "path": ".deer-flow/.../uploads/doc.pdf",
       "virtual_path": "/mnt/user-data/uploads/doc.pdf",
       "artifact_url": "/api/threads/.../artifacts/mnt/.../doc.pdf",
       "converted": true,      # 如果转换为 Markdown
       "converted_path": ".deer-flow/.../uploads/doc.md"
     }]
   }

5. 代理访问
   - UploadsMiddleware 将文件列表注入系统提示
   - 代理通过 virtual_path 访问文件
   - 支持 read_file 工具读取内容
```

## API 端点

### 上传文件

```http
POST /api/threads/{thread_id}/uploads
Content-Type: multipart/form-data

------Boundary
Content-Disposition: form-data; name="files"; filename="doc.pdf"
Content-Type: application/pdf

[二进制内容]
------Boundary--
```

**响应**：
```json
{
  "files": [
    {
      "filename": "doc.pdf",
      "original_name": "document.pdf",
      "path": ".deer-flow/threads/abc123/user-data/uploads/doc.pdf",
      "virtual_path": "/mnt/user-data/uploads/doc.pdf",
      "artifact_url": "/api/threads/abc123/artifacts/mnt/user-data/uploads/doc.pdf",
      "size": 1024567,
      "mime_type": "application/pdf",
      "converted": true,
      "converted_path": ".deer-flow/threads/abc123/user-data/uploads/doc.md",
      "converted_mime_type": "text/markdown"
    }
  ]
}
```

### 列出现有上传

```http
GET /api/threads/{thread_id}/uploads
```

**响应**：
```json
{
  "files": [
    {
      "filename": "doc.pdf",
      "path": ".deer-flow/threads/abc123/user-data/uploads/doc.pdf",
      "virtual_path": "/mnt/user-data/uploads/doc.pdf",
      "size": 1024567,
      "uploaded_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 删除上传

```http
DELETE /api/threads/{thread_id}/uploads/{filename}
```

**响应**：
```json
{
  "success": true,
  "deleted": "doc.pdf"
}
```

## 文档转换

上传的文档自动通过 `markitdown` 转换为 Markdown：

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
markdown_content = result.text_content
```

### 转换的文件类型

| 原始格式 | 转换后 | 说明 |
|----------|--------|------|
| PDF | Markdown | 提取文本和基本结构 |
| Word | Markdown | 保留标题、列表、表格 |
| PowerPoint | Markdown | 每页转换为部分 |
| Excel | Markdown | 转换为表格格式 |
| HTML | Markdown | 清理并简化 |

### 访问转换后的内容

代理可以通过两种方式访问上传的文档：

1. **原始文件**（通过 `virtual_path`）
   ```
   /mnt/user-data/uploads/document.pdf
   ```

2. **转换后的 Markdown**（通过 `converted_virtual_path`）
   ```
   /mnt/user-data/uploads/document.md
   ```

## 上传管理

### 存储结构

```
backend/.deer-flow/
└── threads/
    └── {thread_id}/
        └── user-data/
            └── uploads/
                ├── document.pdf          # 原始文件
                ├── document.md            # 转换后的 Markdown
                ├── image.png
                └── data.csv
```

### 大小限制

| 类型 | 最大大小 | 说明 |
|------|----------|------|
| 单个文件 | 50MB | 可配置 |
| 每次请求 | 100MB | 所有文件总计 |
| 每个线程 | 500MB | 累积限制 |

### 清理

- 删除线程时自动清理上传的文件
- 可以通过 API 单独删除文件
- 转换后的文件在原始文件删除时同步删除

## 在代理中使用

### 自动注入

UploadsMiddleware 自动将文件列表注入系统提示：

```
可用上传文件：
1. /mnt/user-data/uploads/document.md (从 PDF 转换)
2. /mnt/user-data/uploads/image.png
3. /mnt/user-data/uploads/data.csv
```

### 访问文件

代理可以使用标准文件工具：

```python
# 读取转换后的文档
read_file(path="/mnt/user-data/uploads/document.md")

# 查看图像（视觉模型）
view_image(path="/mnt/user-data/uploads/image.png")

# 分析 CSV 数据
read_file(path="/mnt/user-data/uploads/data.csv")
```

## 安全考虑

### 文件验证

1. **类型检查**：验证文件扩展名和 MIME 类型
2. **大小限制**：强制执行最大文件大小
3. **路径安全**：防止路径遍历攻击
4. **内容扫描**：可选的恶意内容检测

### 隔离

- 每个线程的上传文件隔离
- 线程删除时文件自动清理
- 无跨线程文件访问

## 最佳实践

1. **文档上传**：PDF 和 Word 文件会自动转换为 Markdown 以提高代理可读性
2. **图像上传**：视觉模型支持图像分析
3. **代码文件**：保留原始格式以进行精确编辑
4. **大文件**：对于非常大的文档，考虑拆分为多个文件
5. **组织**：使用描述性文件名以便代理轻松识别

## 故障排除

### "文件太大"
- 检查文件是否超过大小限制
- 考虑压缩或拆分为多个文件
- 联系管理员增加限制

### "不支持文件类型"
- 检查文件扩展名是否在支持列表中
- 将文件转换为支持的格式
- 对于代码文件，确保使用标准扩展名

### "转换失败"
- 某些 PDF 或复杂文档可能无法完美转换
- 代理仍可以访问原始文件
- 对于图像 PDF，可能需要 OCR 预处理

### "找不到上传文件"
- 验证线程 ID 正确
- 检查文件是否被手动删除
- 重新上传文件
