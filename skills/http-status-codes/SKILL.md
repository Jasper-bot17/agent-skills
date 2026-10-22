---
name: http-status-codes
description: "HTTP 状态码速查助手。内置完整 HTTP 状态码数据库（1xx~5xx，100+状态码），支持按代码查询、按分类浏览、按关键词搜索、常见原因与排查建议、请求示例。适用于 API 开发、接口调试、前端排错、后端日志分析、学习 HTTP 协议等场景。纯 Python 标准库实现，无外部依赖。"
---

# HTTP 状态码速查助手

## 触发场景

当用户出现以下意图时使用本技能：

- "403 是什么意思" / "404 状态码" / "状态码 500"
- "HTTP 状态码大全" / "所有状态码"
- "429 怎么办" / "401 和 403 区别"
- "301 和 302 区别" / "304 是什么"
- "API 返回 502" / "网关错误"
- "状态码 200 和 204" / "什么时候返回 201"
- "查一下 418" / "HTTP猫"
- "列出所有 4xx 错误" / "5xx 有哪些"

## 核心功能

| 功能 | 说明 |
|---|---|
| 按代码查询 | 输入状态码，返回名称、描述、原因、排查建议 |
| 按分类浏览 | 1xx/2xx/3xx/4xx/5xx 分类列表 |
| 关键词搜索 | 按描述关键词搜索相关状态码 |
| 对比查询 | 对比两个状态码的区别（如 401 vs 403） |
| 常见原因 | 每个状态码附带常见原因和排查步骤 |
| 请求示例 | 附带 curl 示例说明典型使用场景 |
| 完整数据库 | 100+ 状态码，涵盖 RFC 标准和常用扩展 |

## 使用方法

### 命令行工具

```bash
# 查询单个状态码
python3 scripts/lookup_status.py 404

# 按分类列出所有状态码
python3 scripts/lookup_status.py --category 4xx

# 关键词搜索
python3 scripts/lookup_status.py --search "未授权"

# 对比两个状态码
python3 scripts/lookup_status.py --compare 301 302

# 列出所有分类概要
python3 scripts/lookup_status.py --categories

# 输出为 JSON 格式（便于程序调用）
python3 scripts/lookup_status.py 500 --json

# 批量查询
python3 scripts/lookup_status.py 200 201 204 301 404 500
```

### 作为模块调用

```python
from lookup_status import lookup_code, search_by_keyword, list_by_category

# 查询状态码
info = lookup_code(404)
print(info["name"])        # Not Found
print(info["category"])    # 4xx Client Error
print(info["description"]) # 请求的资源不存在
print(info["causes"])      # 常见原因列表
print(info["tips"])        # 排查建议

# 关键词搜索
results = search_by_keyword("未授权")

# 按分类列出
codes = list_by_category("5xx")
```

## 操作步骤

1. **确定查询方式**：用户给出状态码数字、分类、关键词或对比需求
2. **执行查询**：运行脚本，从内置数据库中检索
3. **格式化输出**：展示状态码名称、描述、常见原因、排查建议
4. **按需扩展**：如用户需要更多细节，附带 curl 示例或对比说明

## 输出规范

- 每个状态码输出：代码、名称、中文名称、分类、描述、常见原因、排查建议、典型示例
- 对比查询输出：两个状态码的定义和核心区别
- 分类列表输出：表格形式，代码 | 名称 | 简要描述
- 搜索结果输出：匹配的状态码列表及匹配理由

## 注意事项

- 内置数据库涵盖 RFC 7231、RFC 2518、RFC 6585、RFC 7538 等标准
- 包含 WebDAV 扩展状态码（207、422、423、424 等）
- 包含常见非标准但广泛使用的状态码（如 418 I'm a teapot）
- 纯 Python 标准库实现，无外部依赖
- 状态码分类：1xx 信息、2xx 成功、3xx 重定向、4xx 客户端错误、5xx 服务端错误
