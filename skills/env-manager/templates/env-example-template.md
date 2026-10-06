# .env.example 模板说明

> 复制此文件为 `.env`，填写实际值后使用。
> **切勿**将包含真实密钥的 `.env` 文件提交到版本控制。

---

## 模板结构

```
# 分组注释
# 说明这个分组的用途

# 变量说明（可选）
VARIABLE_NAME=value

# 密钥变量（留空，部署时填写）
SECRET_KEY=
```

## 最佳实践

### 1. 分组管理

按功能分组，每组前加注释：

```
# === 数据库 ===
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp

# === 认证 ===
JWT_SECRET=
API_KEY=
```

### 2. 密钥留空

所有密钥、密码、Token 在模板中留空：

```
DATABASE_URL=
AWS_SECRET_ACCESS_KEY=
STRIPE_API_KEY=
```

### 3. 提供默认值

非敏感变量提供合理默认值：

```
PORT=3000
LOG_LEVEL=info
NODE_ENV=development
```

### 4. 添加注释说明

每个变量前说明用途和可选值：

```
# 日志级别：debug, info, warn, error
LOG_LEVEL=info

# 是否启用调试模式：true, false
DEBUG=false
```

### 5. .gitignore 配置

确保 `.env` 已加入 `.gitignore`：

```
# .gitignore
.env
.env.local
.env.*.local
*.pem
*.key
```

## 生成命令

```bash
# 从现有 .env 生成模板
python3 manage_env.py --file .env --template --output .env.example
```

## 检查清单

- [ ] 所有密钥已留空或替换为占位符
- [ ] 非敏感变量有合理默认值
- [ ] 每个分组有注释说明
- [ ] .env 已加入 .gitignore
- [ ] 模板可直接复制使用

---

*模板由 env-manager 技能提供*
