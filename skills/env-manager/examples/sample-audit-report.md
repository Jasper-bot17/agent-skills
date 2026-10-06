# 示例：环境变量审计报告

> 使用 `manage_env.py --file sample.env --audit` 生成。

---

## 基本信息

| 项目 | 值 |
|---|---|
| 文件 | sample.env |
| 总变量数 | 26 |
| 敏感变量 | 8 个 |
| 空值变量 | 1 个 |
| 格式问题 | 4 个（含误报） |

---

## 问题清单

### 1. 空值变量

| 变量名 | 行号 | 说明 |
|---|---|---|
| `EMAIL_PASSWORD` | 42 | 未填写，邮件功能将无法使用 |

**建议**：填写 SMTP 密码，或如果不使用邮件功能，移除相关配置。

### 2. 疑似密钥（已脱敏）

| 变量名 | 行号 | 脱敏值 |
|---|---|---|
| `DATABASE_URL` | 15 | `postgresql://app_user:***@db.example.com:5432/production` |
| `JWT_SECRET` | 20 | `my-s***2026` |
| `API_KEY` | 22 | `sk-l***1d0e` |
| `STRIPE_SECRET_KEY` | 25 | `sk_t***9r0q` |
| `SENDGRID_API_KEY` | 26 | `SG.a***9012` |
| `AWS_ACCESS_KEY_ID` | 27 | `AKIA***MPLE` |
| `AWS_SECRET_ACCESS_KEY` | 28 | `wJal***EKEY` |

**建议**：
- 生产环境密钥建议使用密钥管理服务（Vault / AWS Secrets Manager）
- 定期轮换密钥
- 确保 .env 已加入 .gitignore

### 3. 格式提示（可能为误报）

| 变量名 | 提示 | 说明 |
|---|---|---|
| `HOST=0.0.0.0` | 可能不是有效 URL | 实际为绑定地址，属正常配置 |
| `CACHE_TTL=3600` | 可能不是布尔值 | 实际为秒数，变量名含 cache 触发误报 |
| `EMAIL_HOST=smtp.example.com` | 可能不是有效 URL/邮箱 | 实际为 SMTP 主机名，属正常 |

> 注：格式校验基于启发式规则，可能存在误报，请结合实际场景判断。

---

## 安全建议

1. **立即行动**：填写 `EMAIL_PASSWORD` 空值
2. **短期改进**：将 8 个密钥迁移到密钥管理服务
3. **长期规划**：建立密钥轮换机制，每 90 天轮换一次
4. **版本控制**：确认 `.env` 已加入 `.gitignore`，检查 Git 历史中是否有泄露

---

## 校验通过的变量（25 个）

`NODE_ENV`, `DEBUG`, `PORT`, `API_URL`, `DB_POOL_SIZE`, `DB_TIMEOUT`, `JWT_EXPIRES_IN`, `LOG_LEVEL`, `LOG_FORMAT`, `REDIS_URL`, `CACHE_TTL`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `ENABLE_ANALYTICS`, `ENABLE_SSL`, `MAINTENANCE_MODE` 等。

---

*报告由 env-manager 技能生成*
