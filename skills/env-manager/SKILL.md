---
name: env-manager
description: '环境变量管理助手。解析和管理 .env 配置文件，支持多环境对比（dev/staging/prod）、缺失变量检测、重复变量检测、格式校验（URL/端口/邮箱/路径等）、密钥脱敏显示、生成 .env.example 模板、导出为 shell/JSON/Docker/YAML 格式。适用于项目配置管理、多环境部署、配置审计、密钥安全检查等场景。'
---

# 环境变量管理助手

## 一、技能定位

本技能用于**管理和审计环境变量配置文件**。核心价值：

- 解析 `.env` 文件，支持注释、引号、多行值
- 多环境对比，快速发现配置差异
- 自动检测缺失变量、重复变量、空值
- 格式校验（URL、端口、邮箱、路径、布尔值等）
- 密钥脱敏，安全展示配置
- 生成 `.env.example` 模板
- 多格式导出（shell / JSON / Docker / YAML）

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我看看这个 .env 文件」「检查一下环境变量配置」
2. 用户说「对比一下开发和生产环境的配置」「看看 staging 和 prod 有什么不同」
3. 用户说「生成一个 .env.example」「把敏感信息去掉做个模板」
4. 用户说「检查一下哪些变量没填」「看看有没有缺失的配置」
5. 用户说「把 .env 转成 JSON / YAML / Docker 格式」
6. 用户说「这个配置有没有问题」「帮我审计一下环境变量」
7. 用户说「哪些是密钥需要脱敏」「安全检查一下配置」

## 三、支持的功能

### 3.1 .env 文件解析

- 支持 `KEY=VALUE` 格式
- 支持注释（`#` 开头）
- 支持引号包裹的值（单引号、双引号）
- 支持 `export KEY=VALUE` 格式
- 保留原始顺序和注释
- 支持空值和默认值

### 3.2 多环境对比

- 对比两个或多个 .env 文件
- 找出仅在 A 中存在的变量
- 找出仅在 B 中存在的变量
- 找出值不同的变量
- 输出差异报告

### 3.3 配置审计

- **缺失检测**：值为空的变量
- **重复检测**：同名变量多次定义
- **格式校验**：
  - URL 格式（http/https）
  - 端口范围（1-65535）
  - 邮箱格式
  - 文件路径存在性
  - 布尔值（true/false/yes/no/1/0）
  - 整数范围
- **密钥检测**：识别可能的密钥/Token（含 key、secret、token、password 等关键词）

### 3.4 密钥脱敏

- 自动识别敏感变量
- 显示时替换为 `***`
- 可自定义脱敏规则
- 支持部分显示（如前4后4）

### 3.5 模板生成

- 从 .env 生成 .env.example
- 自动移除敏感值
- 保留注释和结构
- 添加填写说明

### 3.6 多格式导出

- **Shell**：`export KEY=VALUE`
- **JSON**：`{"KEY": "VALUE"}`
- **Docker**：`-e KEY=VALUE` 或 Docker Compose 格式
- **YAML**：键值对格式

## 四、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 解析单个文件 / 对比多个文件 / 生成模板 / 格式转换 / 安全审计
- 文件路径
- 输出格式

### 步骤 2：运行脚本

使用 `scripts/manage_env.py`：

```bash
# 解析并显示 .env（自动脱敏）
python3 scripts/manage_env.py --file .env

# 对比两个环境
python3 scripts/manage_env.py --file .env.dev --compare .env.prod

# 生成 .env.example
python3 scripts/manage_env.py --file .env --template

# 格式校验
python3 scripts/manage_env.py --file .env --validate

# 导出为 JSON
python3 scripts/manage_env.py --file .env --export json

# 导出为 Docker 格式
python3 scripts/manage_env.py --file .env --export docker

# 导出为 YAML
python3 scripts/manage_env.py --file .env --export yaml

# 完整审计报告
python3 scripts/manage_env.py --file .env --audit

# 不脱敏显示（谨慎使用）
python3 scripts/manage_env.py --file .env --no-mask
```

### 步骤 3：解读结果

- **解析模式**：显示所有变量，密钥自动脱敏
- **对比模式**：输出差异列表（仅A有、仅B有、值不同）
- **审计模式**：输出问题清单（缺失、重复、格式错误、密钥未脱敏）
- **模板模式**：生成可分享的 .env.example

### 步骤 4：安全提示

1. 不要将包含真实密钥的 .env 文件提交到 Git
2. .env 文件应加入 .gitignore
3. 生产环境密钥应使用密钥管理服务（如 Vault、AWS Secrets Manager）
4. 定期轮换密钥
5. 不同环境使用不同密钥

## 五、输出规范

### 5.1 解析结果

```
📋 环境变量解析结果
━━━━━━━━━━━━━━━━━━━━━━━━
文件：.env
变量数：12
注释行：3
空行：2

🔐 敏感变量（已脱敏）：
  DATABASE_URL=postgresql://user:***@localhost:5432/db
  API_KEY=sk-***4f2a
  SECRET_KEY=***

📝 普通变量：
  NODE_ENV=production
  PORT=3000
  LOG_LEVEL=info
  DEBUG=false
```

### 5.2 对比结果

```
🔍 环境对比报告
━━━━━━━━━━━━━━━━━━━━━━━━
文件 A：.env.dev（15 个变量）
文件 B：.env.prod（18 个变量）

⚠️  仅在 A 中存在（3 个）：
  - DEBUG=true
  - DEV_MODE=enabled
  - LOCAL_CACHE=true

⚠️  仅在 B 中存在（6 个）：
  - PRODUCTION_SECRET=***
  - CDN_URL=https://cdn.example.com
  - SSL_CERT_PATH=/etc/ssl/cert.pem
  ...

❌ 值不同（2 个）：
  - NODE_ENV: A=development, B=production
  - PORT: A=3000, B=8080

✅ 相同（10 个）
```

### 5.3 审计报告

```
🔒 配置审计报告
━━━━━━━━━━━━━━━━━━━━━━━━
文件：.env
总变量数：15

❌ 问题发现：

1. 空值变量（2 个）：
   - EMAIL_PASSWORD=（未填写）
   - BACKUP_KEY=（未填写）

2. 重复定义（1 个）：
   - PORT 定义了 2 次（第 5 行、第 12 行）

3. 格式错误（1 个）：
   - PORT=99999（超出范围 1-65535）
   - API_URL=not-a-url（不是有效的 URL）

4. 疑似密钥（4 个）：
   - DATABASE_URL（含密码）
   - API_KEY
   - SECRET_KEY
   - JWT_SECRET

✅ 校验通过：11 个变量

💡 建议：
  - 空值变量请尽快填写
  - 重复定义会导致后值覆盖前值
  - 确保 .env 已加入 .gitignore
```

## 六、常见场景处理

### 场景 1：新项目初始化
**用户**：「帮我从这个 .env 生成一个可以提交到 Git 的模板」
**处理**：运行 `--template` → 生成 .env.example → 提醒将 .env 加入 .gitignore。

### 场景 2：部署前检查
**用户**：「上线前帮我检查一下生产环境配置」
**处理**：运行 `--audit` → 检查空值、格式、密钥 → 输出问题清单。

### 场景 3：多环境同步
**用户**：「看看开发和生产环境配置差了什么」
**处理**：运行 `--compare` → 输出差异 → 提醒同步必要变量。

### 场景 4：格式转换
**用户**：「把 .env 转成 Docker Compose 能用的格式」
**处理**：运行 `--export docker` → 输出 environment 块格式。

### 场景 5：安全审计
**用户**：「检查一下有没有密钥泄露风险」
**处理**：运行 `--audit` → 识别所有密钥变量 → 检查是否有硬编码 → 给出安全建议。

## 七、注意事项

1. **安全第一**：默认所有输出自动脱敏，使用 `--no-mask` 时需提醒用户风险。
2. **不修改原文件**：脚本默认只读，生成模板或导出时写入新文件，不覆盖原 .env。
3. **格式容错**：解析时容忍常见格式问题（多余空格、缺少引号等），但会在审计中报告。
4. **密钥识别**：基于变量名关键词（key、secret、token、password、pass、auth、credential 等）和值特征识别，可能有误报，审计时需人工确认。
5. **路径校验**：检查文件路径是否存在时，基于当前运行环境，不同机器结果可能不同。
6. **多行值**：支持双引号包裹的多行值，但不支持未闭合的引号。
7. **编码**：默认 UTF-8 编码读取，其他编码可能需要转换。
8. **大文件**：支持任意大小的 .env 文件，但建议变量数不超过 500 个以便阅读。
9. **不执行**：脚本不会执行 .env 中的任何命令或变量替换，仅做文本解析。
10. **导出格式**：导出时保留原始值（不脱敏），导出文件需妥善保管。

## 八、文件结构

```
env-manager/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── env-example-template.md            # .env.example 模板说明
├── scripts/
│   └── manage_env.py                     # 环境变量管理脚本
└── examples/
    ├── sample.env                         # 示例 .env 文件
    └── sample-audit-report.md             # 示例审计报告
```

## 九、使用示例

### 示例 1：快速查看
**用户**：「看看这个 .env 里有什么」
**AI**：运行 `--file .env` → 显示所有变量（密钥脱敏）→ 统计变量数和类型。

### 示例 2：生成模板
**用户**：「生成一个 .env.example，把敏感信息去掉」
**AI**：运行 `--file .env --template` → 生成 .env.example → 提醒加入 .gitignore。

### 示例 3：环境对比
**用户**：「对比 .env.dev 和 .env.prod」
**AI**：运行 `--compare` → 输出差异 → 提醒生产环境缺少的变量。
