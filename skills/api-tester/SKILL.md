---
name: api-tester
description: 'API 测试助手。根据 API 描述（OpenAPI/Swagger 规范或简单的端点列表），自动生成可执行的 API 测试套件。支持生成 curl 命令集合、Python requests 测试脚本、Postman 集合（JSON）。覆盖 GET/POST/PUT/DELETE/PATCH 五种 HTTP 方法，支持请求头、查询参数、请求体、Bearer Token 认证，自动生成响应状态码验证、JSON 字段存在性检查、响应时间断言。支持批量执行测试并生成 HTML/Markdown 测试报告。适用于后端开发验证、接口联调、回归测试、CI/CD 集成测试等场景。纯 Python 标准库，无外部依赖。'
---

# API 测试助手

## 一、技能定位

本技能用于**根据 API 描述自动生成可执行的测试套件**。核心价值：

- **多格式输出**：curl 命令集合、Python requests 测试脚本、Postman 集合
- **5 种 HTTP 方法**：GET、POST、PUT、DELETE、PATCH
- **完整请求配置**：请求头、查询参数、请求体、Bearer Token 认证
- **自动断言**：状态码验证、JSON 字段检查、响应时间断言
- **批量执行**：一键运行所有测试，生成通过率统计
- **测试报告**：生成 HTML 和 Markdown 格式的测试报告
- **纯标准库**：无外部依赖，开箱即用

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我写 API 测试」「生成接口测试用例」「测试这个 API」
2. 用户说「生成 curl 命令」「把这个接口转成 curl」
3. 用户说「Postman 集合」「导入 Postman」「生成 Postman 请求」
4. 用户说「接口联调」「后端接口验证」「回归测试」
5. 用户说「CI/CD 里加 API 测试」「自动化接口测试」
6. 用户提供 OpenAPI/Swagger 文档，要求生成测试
7. 用户说「测试报告」「接口测试通过率」
8. 用户说「Python requests 测试脚本」「接口自动化」

## 三、支持的输出格式

| 格式 | 说明 | 适用场景 |
|---|---|---|
| `curl` | 生成 .sh 脚本，包含所有 curl 命令 | 快速手动测试、终端调试 |
| `python` | 生成 Python unittest 测试脚本 | 自动化测试、CI/CD 集成 |
| `postman` | 生成 Postman Collection v2.1 JSON | Postman 导入、团队协作 |
| `all` | 同时生成以上三种 | 完整测试套件 |

## 四、API 描述文件格式

使用简单的 YAML-like 或 JSON 格式描述 API：

```json
{
  "base_url": "https://api.example.com",
  "auth": {
    "type": "bearer",
    "token": "your-token-here"
  },
  "default_headers": {
    "Content-Type": "application/json"
  },
  "endpoints": [
    {
      "name": "获取用户列表",
      "method": "GET",
      "path": "/api/users",
      "params": {"page": 1, "limit": 10},
      "expect_status": 200,
      "expect_fields": ["data", "total", "page"]
    },
    {
      "name": "创建用户",
      "method": "POST",
      "path": "/api/users",
      "body": {"name": "test", "email": "test@example.com"},
      "expect_status": 201,
      "expect_fields": ["id", "name", "email"]
    }
  ]
}
```

## 五、操作步骤

### 步骤 1：准备 API 描述

向用户确认以下信息，或让用户提供 API 描述文件：
- **基础 URL**：如 `https://api.example.com`
- **认证方式**：无 / Bearer Token / API Key / Basic Auth
- **端点列表**：每个端点的方法、路径、参数、请求体、期望响应
- **输出格式**：curl / python / postman / all

### 步骤 2：运行生成脚本

```bash
# 从 JSON 描述文件生成 Python 测试脚本
python3 scripts/generate_api_tests.py --input api.json --format python --output tests/

# 生成 curl 命令集合
python3 scripts/generate_api_tests.py --input api.json --format curl --output tests/

# 生成 Postman 集合
python3 scripts/generate_api_tests.py --input api.json --format postman --output tests/

# 同时生成所有格式
python3 scripts/generate_api_tests.py --input api.json --format all --output tests/

# 直接执行测试（Python 格式）并生成报告
python3 scripts/generate_api_tests.py --input api.json --format python --run --report

# 指定基础 URL 覆盖
python3 scripts/generate_api_tests.py --input api.json --base-url https://staging.example.com

# 指定认证 Token
python3 scripts/generate_api_tests.py --input api.json --token my-secret-token
```

### 步骤 3：执行测试

```bash
# 方式1：直接运行生成的 Python 测试脚本
python3 tests/test_api.py

# 方式2：运行 curl 脚本
bash tests/api_calls.sh

# 方式3：导入 Postman 集合
# 在 Postman 中 Import -> 选择 tests/postman_collection.json
```

### 步骤 4：查看报告

- 测试执行后自动生成 `test_report.html` 和 `test_report.md`
- 报告包含：总用例数、通过数、失败数、通过率、每个用例的详细结果
- 失败用例显示：期望状态码 vs 实际状态码、响应内容、响应时间

## 六、命令行参数

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--input` / `-i` | API 描述文件路径（JSON） | 必填 |
| `--format` / `-f` | 输出格式：curl/python/postman/all | python |
| `--output` / `-o` | 输出目录 | ./api_tests |
| `--base-url` | 覆盖基础 URL | 从描述文件读取 |
| `--token` | Bearer Token | 从描述文件读取 |
| `--run` | 生成后立即执行测试（仅 python 格式） | 关闭 |
| `--report` | 生成测试报告（需配合 --run） | 关闭 |
| `--timeout` | 请求超时秒数 | 10 |
| `--verbose` / `-v` | 详细输出 | 关闭 |

## 七、生成的测试脚本结构

### Python 测试脚本示例

```python
import unittest
import json
import urllib.request
import urllib.error
import time

BASE_URL = "https://api.example.com"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer xxx"}

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.start_time = time.time()

    def tearDown(self):
        elapsed = time.time() - self.start_time
        print(f"  响应时间: {elapsed:.3f}s")

    def test_get_users(self):
        """获取用户列表"""
        url = f"{BASE_URL}/api/users?page=1&limit=10"
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read())
            self.assertIn("data", data)
            self.assertIn("total", data)

    def test_create_user(self):
        """创建用户"""
        url = f"{BASE_URL}/api/users"
        body = json.dumps({"name": "test", "email": "test@example.com"}).encode()
        req = urllib.request.Request(url, data=body, headers=HEADERS, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read())
            self.assertIn("id", data)

if __name__ == "__main__":
    unittest.main(verbosity=2)
```

### curl 脚本示例

```bash
#!/bin/bash
BASE_URL="https://api.example.com"
TOKEN="your-token"

echo "=== 1. 获取用户列表 ==="
curl -s -X GET "$BASE_URL/api/users?page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool

echo ""
echo "=== 2. 创建用户 ==="
curl -s -X POST "$BASE_URL/api/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"test@example.com"}' | python3 -m json.tool
```

## 八、常见场景处理

### 场景 1：RESTful CRUD 接口
**用户**：「帮我测试用户管理的 CRUD 接口」
**处理**：生成 GET 列表、GET 详情、POST 创建、PUT 更新、DELETE 删除五个测试用例。

### 场景 2：带认证的 API
**用户**：「接口需要 Bearer Token，怎么测试」
**处理**：在描述文件中配置 `auth.type=bearer`，或用 `--token` 参数传入，所有请求自动添加 Authorization 头。

### 场景 3：OpenAPI 文档转测试
**用户**：「我有 Swagger 文档，帮我生成测试」
**处理**：解析 OpenAPI JSON，提取 paths 和 methods，自动生成对应测试用例。

### 场景 4：CI/CD 集成
**用户**：「把 API 测试加到 CI 里」
**处理**：生成 Python unittest 脚本，在 CI 配置中添加 `python test_api.py` 步骤，非零退出码表示测试失败。

### 场景 5：快速调试单个接口
**用户**：「这个 POST 接口帮我生成个 curl」
**处理**：根据端点描述生成单个 curl 命令，包含所有请求头和请求体。

### 场景 6：响应验证
**用户**：「测试时要检查返回的字段」
**处理**：在描述文件中配置 `expect_fields`，测试脚本自动验证 JSON 响应中包含指定字段。

## 九、注意事项

1. **认证安全**：Token 不应硬编码在测试脚本中，建议使用环境变量或 `--token` 参数传入
2. **测试数据**：POST/PUT/DELETE 会修改数据，建议在测试环境运行，或使用测试账号
3. **网络依赖**：测试需要网络连接，CI 环境需确保能访问目标 API
4. **速率限制**：批量测试可能触发 API 速率限制，可在脚本中添加延迟
5. **HTTPS 证书**：自签名证书环境需额外配置，默认验证证书
6. **响应时间断言**：默认不强制响应时间断言，可在描述文件中配置 `max_response_time`
7. **不执行危险操作**：生成 DELETE 测试时会添加警告，建议用户确认后再执行
8. **纯标准库**：Python 测试脚本使用 urllib，无需安装 requests

## 十、文件结构

```
api-tester/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── api-testing-guide.md              # API 测试最佳实践指南
├── scripts/
│   └── generate_api_tests.py             # API 测试生成脚本
└── examples/
    ├── sample-api.json                   # API 描述示例（用户管理 CRUD）
    ├── sample-test-script.py             # 生成的 Python 测试脚本示例
    ├── sample-curl-commands.sh           # 生成的 curl 脚本示例
    └── sample-postman-collection.json    # 生成的 Postman 集合示例
```

## 十一、使用示例

### 示例 1：快速生成用户管理 API 测试
**用户**：「我有个用户管理 API，帮我生成测试」
**AI**：创建 api.json 描述文件 → 运行 `--format all` → 生成 curl/python/postman 三种格式 → 告知执行方法。

### 示例 2：直接运行测试并生成报告
**用户**：「直接帮我跑一下测试，出个报告」
**AI**：运行 `--format python --run --report` → 执行所有测试 → 生成 HTML + Markdown 报告 → 汇报通过率。

### 示例 3：Postman 集合导出
**用户**：「生成 Postman 集合，我要导入」
**AI**：运行 `--format postman` → 生成 v2.1 格式 JSON → 告知在 Postman 中 Import。
