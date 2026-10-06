# 密码策略模板

> 复制此模板，根据实际需求修改策略项。

---

## 策略名称：`<企业/系统名称> 密码策略`

### 基本要求

| 策略项 | 要求 | 说明 |
|---|---|---|
| 最小长度 | `12` 位 | 建议至少 12 位 |
| 最大长度 | `64` 位 | 防止 DoS 攻击 |
| 密码有效期 | `90` 天 | 到期需更换 |
| 历史密码 | 禁止使用最近 `5` 次密码 | 防止密码循环 |

### 字符要求

| 策略项 | 是否必须 | 说明 |
|---|---|---|
| 大写字母 (A-Z) | ✅ 必须 | 至少 1 个 |
| 小写字母 (a-z) | ✅ 必须 | 至少 1 个 |
| 数字 (0-9) | ✅ 必须 | 至少 1 个 |
| 特殊符号 | ✅ 必须 | 至少 1 个，如 !@#$%^&* |

### 禁止项

- ❌ 禁止使用常见弱密码（如 password、123456、qwerty）
- ❌ 禁止包含用户名、邮箱、姓名
- ❌ 禁止包含连续字符（如 abc123、111111）
- ❌ 禁止纯数字或纯字母
- ❌ 禁止与其他系统密码相同

### 锁定策略

| 策略项 | 值 |
|---|---|
| 最大尝试次数 | `5` 次 |
| 锁定时长 | `30` 分钟 |
| 解锁方式 | 管理员解锁 / 邮箱验证 |

### 存储要求

- 密码必须使用 bcrypt / Argon2 等慢哈希算法存储
- 禁止明文存储或可逆加密
- 盐值必须随机且唯一

---

## 策略字符串（用于脚本检查）

```
min-length=12,max-length=64,require-upper,require-lower,require-number,require-symbol,forbid-common
```

### 使用示例

```bash
# 检查密码是否符合策略
python3 generate_password.py --check "MyP@ssw0rd!" --policy "min-length=12,require-upper,require-lower,require-number,require-symbol,forbid-common"

# 生成符合策略的密码
python3 generate_password.py --length 16
```

---

*模板由 password-generator 技能提供*
