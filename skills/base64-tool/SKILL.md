---
name: base64-tool
description: "Base64 编解码助手。支持文本 Base64 编码/解码（标准与 URL-safe 两种变体）、文件 Base64 编解码、批量编解码、随机 Base64 字符串生成、padding 分析、JSON 输出、字符集参考。适用于 Web 开发（Data URL、Basic Auth）、API 调试、配置文件处理、二进制数据传输等场景。纯 Python 标准库实现，无外部依赖。"
---

# Base64 编解码助手

## 触发场景

当用户出现以下意图时使用本技能：

- "把这段文字转成 Base64"
- "解码这个 Base64 字符串"
- "Base64 encode hello"
- "Base64 decode SGVsbG8="
- "URL-safe Base64"
- "把图片转 Base64"
- "Data URL 格式"
- "生成随机 Base64"
- "Basic Auth 编码"
- "这个 Base64 有没有 padding"

## 核心功能

| 功能 | 说明 |
|---|---|
| 文本编码 | 任意 UTF-8 文本 → Base64 字符串 |
| 文本解码 | Base64 字符串 → UTF-8 文本 |
| URL-safe 变体 | 使用 `-` 和 `_` 代替 `+` 和 `/`，去除 `=` padding |
| 文件编解码 | 将任意文件（图片、PDF、二进制）转为 Base64 或还原 |
| 批量模式 | 一次编解码多个字符串 |
| 随机生成 | 生成指定字节长度的随机 Base64 字符串 |
| Padding 分析 | 检测 Base64 字符串的 padding 状态和长度 |
| JSON 输出 | 便于程序调用 |
| Data URL | 生成 `data:image/png;base64,...` 格式 |

## 使用方法

### 命令行工具

```bash
# 编码文本
python3 scripts/b64_tool.py encode "Hello World"

# 解码文本
python3 scripts/b64_tool.py decode "SGVsbG8gV29ybGQ="

# URL-safe 编码
python3 scripts/b64_tool.py encode "Hello World" --url-safe

# URL-safe 解码
python3 scripts/b64_tool.py decode "SGVsbG8gV29ybGQ" --url-safe

# 从文件读取编码
python3 scripts/b64_tool.py encode --file input.txt

# 编码文件（生成 Base64）
python3 scripts/b64_tool.py encode-file image.png

# 解码并保存文件
python3 scripts/b64_tool.py decode-file "iVBORw0KGgo..." --output image.png

# 批量编解码
python3 scripts/b64_tool.py encode "hello" "world" "test"

# 生成随机 Base64（16字节 = 24字符）
python3 scripts/b64_tool.py random 16

# 生成随机 URL-safe Base64（无 padding）
python3 scripts/b64_tool.py random 32 --url-safe

# JSON 输出
python3 scripts/b64_tool.py encode "Hello" --json

# 生成 Data URL
python3 scripts/b64_tool.py encode-file image.png --data-url
```

### 作为模块调用

```python
from b64_tool import encode, decode, encode_urlsafe, decode_urlsafe, random_b64

# 编码
result = encode("Hello World")
# "SGVsbG8gV29ybGQ="

# 解码
text = decode("SGVsbG8gV29ybGQ=")
# "Hello World"

# URL-safe
b64 = encode_urlsafe("Hello World")  # "SGVsbG8gV29ybGQ"
text = decode_urlsafe("SGVsbG8gV29ybGQ")  # "Hello World"

# 随机
token = random_b64(16)  # 16字节随机数的 Base64 表示
```

## 操作步骤

1. **确定方向**：用户要编码（文本→Base64）还是解码（Base64→文本）
2. **确定变体**：标准 Base64 还是 URL-safe Base64
3. **确定输入源**：命令行字符串、文件、还是批量
4. **执行编解码**：使用 Python 标准库 `base64` 模块
5. **展示结果**：编码/解码后的内容 + 附加信息（长度、padding 状态）

## 输出规范

- 编码结果：Base64 字符串 + 长度信息
- 解码结果：原始文本 + 字符长度
- Padding 分析：是否有 `=` padding、原始字节长度
- 文件模式：文件大小、Base64 长度
- Data URL：完整的 `data:` URI

## 注意事项

- 纯 Python 标准库实现（`base64` + `os`），无外部依赖
- 文本使用 UTF-8 编码
- URL-safe 变体自动处理 padding（去除 `=`，解码时自动补全）
- 文件编解码适用于二进制文件（图片、PDF、压缩包等）
- Base64 编码后体积增大约 33%（每 3 字节变为 4 字符）
- Data URL 适合小文件（图标、头像），大文件不建议内嵌
