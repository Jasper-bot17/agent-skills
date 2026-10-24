---
name: jwt-decoder
description: "JWT（JSON Web Token）解码器与生成器。支持解析 JWT 三段结构（Header.Payload.Signature）、显示声明（Claims）、过期状态判断（exp/nbf/iat）、常用声明中文释义、签名格式校验、批量解码、JWT 生成（HS256 测试用）、JSON 输出。适用于 API 调试、认证排查、OAuth/OIDC 开发、Token 过期分析等场景。纯 Python 标准库实现，无外部依赖。"
---

# JWT 解码器与生成器

## 触发场景

当用户出现以下意图时使用本技能：

- "解析这个 JWT token"
- "这个 token 什么时候过期"
- "JWT 里的 payload 是什么"
- "帮我解码 eyJhbGciOi..."
- "这个 token 为什么无效"
- "exp 是什么意思"
- "生成一个测试 JWT"
- "JWT 的 alg 是什么"
- "OAuth token 过期时间"
- "decode jwt online"

## 核心功能

| 功能 | 说明 |
|---|---|
| JWT 解码 | 输入 Token，解析 Header 和 Payload 的 Base64Url 编码 |
| 过期状态 | 自动判断 exp/nbf/iat，显示"有效/已过期/未生效" |
| 声明释义 | 对 exp/iat/nbf/sub/iss/aud/jti/nbf 等标准声明给出中文说明 |
| 签名校验 | 显示签名算法（HS256/RS256 等）和签名字段格式（不验证签名） |
| JWT 生成 | 生成 HS256 算法的测试 JWT（用于开发调试） |
| 批量解码 | 一次解码多个 Token |
| JSON 输出 | 便于程序调用 |

## 使用方法

### 命令行工具

```bash
# 解码 JWT（从命令行参数）
python3 scripts/jwt_tool.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyNDI2MjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

# 从文件读取
python3 scripts/jwt_tool.py --file token.txt

# 批量解码
python3 scripts/jwt_tool.py <token1> <token2> <token3>

# JSON 输出
python3 scripts/jwt_tool.py <token> --json

# 生成测试 JWT
python3 scripts/jwt_tool.py --generate --secret mysecret --sub 12345 --name "Alice" --exp 3600

# 生成自定义声明
python3 scripts/jwt_tool.py --generate --secret test --role admin --iss myapp --aud web
```

### 作为模块调用

```python
from jwt_tool import decode_jwt, generate_jwt, explain_claim

# 解码
result = decode_jwt("eyJhbGci...")
print(result["header"])   # {"alg": "HS256", "typ": "JWT"}
print(result["payload"])   # {"sub": "12345", ...}
print(result["is_expired"])  # True/False
print(result["status"])    # "有效" / "已过期" / "未生效"

# 生成
token = generate_jwt({"sub": "123"}, secret="mysecret", expires_in=3600)
```

## 操作步骤

1. **确定用户需求**：解码已有 Token 或生成新 Token
2. **解码流程**：按 `.` 分割三段 → Base64Url 解码 Header 和 Payload → 解析 JSON → 判断过期状态
3. **展示结果**：Header、Payload（含中文释义）、过期状态、签名信息
4. **生成流程**：构造 Header 和 Payload → Base64Url 编码 → HMAC-SHA256 签名 → 拼接

## 输出规范

- Header：alg（签名算法）、typ（Token 类型）
- Payload：所有声明，标准声明附中文说明
- 状态：有效 / 已过期（显示过期时间）/ 未生效（显示生效时间）
- 签名：算法名称 + 签名 Base64Url 片段长度

## 注意事项

- 纯 Python 标准库实现（base64 + json + hmac + hashlib），无外部依赖
- **不验证签名**：解码工具无法验证签名真伪（需要密钥），仅解码结构
- 生成功能仅支持 HS256（HMAC-SHA256），适用于开发测试
- JWT 不加密，Payload 仅 Base64 编码，不要存放敏感信息
- 过期时间基于当前系统时间判断
