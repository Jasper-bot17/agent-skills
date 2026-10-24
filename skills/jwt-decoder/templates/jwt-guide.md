# JWT 调试速查指南

> jwt-decoder 技能配套指南。

---

## 一、JWT 结构

JWT 由三部分组成，用 `.` 分隔：

```
xxxxx.yyyyy.zzzzz
  │     │    │
  │     │    └── Signature（签名）：防止篡改
  │     └─────── Payload（载荷）：存放声明（Claims）
  └───────────── Header（头部）：描述签名算法和 Token 类型
```

---

## 二、常用声明（Claims）速查

| 声明 | 全称 | 类型 | 说明 |
|---|---|---|---|
| `iss` | Issuer | string | 签发者 |
| `sub` | Subject | string | 用户标识 |
| `aud` | Audience | string/array | 接收方 |
| `exp` | Expiration | number | 过期时间（Unix 秒） |
| `nbf` | Not Before | number | 生效时间（Unix 秒） |
| `iat` | Issued At | number | 签发时间（Unix 秒） |
| `jti` | JWT ID | string | 唯一标识（防重放） |

---

## 三、常见签名算法

| 算法 | 类型 | 说明 |
|---|---|---|
| HS256 | 对称 | HMAC + SHA-256，用同一个密钥签名和验证 |
| HS384 | 对称 | HMAC + SHA-384 |
| HS512 | 对称 | HMAC + SHA-512 |
| RS256 | 非对称 | RSA + SHA-256，私钥签名，公钥验证 |
| ES256 | 非对称 | ECDSA + SHA-256 |

---

## 四、常见问题排查

### 401 Unauthorized

| 可能原因 | 检查方法 |
|---|---|
| Token 过期 | 解码查看 exp，是否小于当前时间 |
| Token 未生效 | 解码查看 nbf，是否大于当前时间 |
| 未携带 Token | 检查 Authorization: Bearer <token> 头 |
| Token 格式错误 | 确认有三段，用 `.` 分隔 |
| 签名不匹配 | 密钥错误或 Token 被篡改 |

### Token 过期但仍能访问

- 检查服务端是否正确校验 exp
- 检查是否有 refresh token 机制
- 检查是否有时钟漂移（服务端与客户端时间差）

### CORS 问题

- JWT 放在 Authorization 头中，不通过 Cookie 传递
- 确保前端正确设置 `Authorization: Bearer <token>`

---

## 五、安全注意事项

1. **不要存放敏感信息**：JWT 的 Payload 仅 Base64 编码，任何人可解码
2. **使用 HTTPS**：防止 Token 在传输中被截获
3. **设置合理过期时间**：Access Token 建议 15~60 分钟
4. **使用强密钥**：HS256 密钥长度至少 32 字节
5. **不要将 JWT 存在 localStorage**：XSS 攻击可窃取（优先 HttpOnly Cookie）
6. **黑名单/吊销**：JWT 签发后无法主动失效，需配合黑名单机制

---

## 六、快速测试命令

```bash
# 解码任意 Token
python3 scripts/jwt_tool.py <粘贴 JWT>

# 生成有效测试 Token（1小时过期）
python3 scripts/jwt_tool.py --generate --secret test123 --sub 1 --name "Test" --exp 3600

# 生成已过期 Token（用于测试 401）
python3 scripts/jwt_tool.py --generate --secret test123 --sub 1 --exp -3600
```

---

*本指南由 jwt-decoder 技能提供*
