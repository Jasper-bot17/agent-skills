---
name: data-masker
description: '数据脱敏助手。对 CSV、JSON、SQL 三种格式的数据文件进行敏感信息脱敏处理。内置 15+ 种敏感字段自动识别（手机号、身份证、邮箱、银行卡、姓名、地址、IP、密码、车牌号等），支持 6 种脱敏方式（掩码 mask、替换 replace、哈希 hash、截断 truncate、泛化 generalize、置空 nullify），可通过规则配置文件自定义字段匹配和脱敏策略，保留数据格式和长度，生成脱敏统计报告。适用于数据共享、测试环境准备、日志脱敏、隐私合规（GDPR/个人信息保护法）等场景。纯 Python 标准库，无外部依赖。'
---

# 数据脱敏助手

## 一、技能定位

本技能用于**对包含敏感信息的数据文件进行自动化脱敏处理**。核心价值：

- **多格式支持**：CSV、JSON、SQL（INSERT 语句）
- **15+ 内置敏感字段识别**：手机号、身份证、邮箱、银行卡、姓名、地址、IP、密码、车牌号、QQ号、微信号等
- **6 种脱敏方式**：掩码、替换、哈希、截断、泛化、置空
- **可配置规则**：通过 JSON 规则文件自定义字段匹配和脱敏策略
- **格式保留**：脱敏后保持原数据格式和长度，不破坏数据结构
- **统计报告**：生成脱敏报告，统计处理的字段数、行数、脱敏方式分布
- **纯标准库**：无外部依赖，开箱即用

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「数据脱敏」「敏感信息处理」「隐私数据处理」
2. 用户说「把手机号/身份证/邮箱打码」「数据匿名化」
3. 用户说「测试数据准备」「生产数据导出到测试环境」
4. 用户说「日志脱敏」「日志中的敏感信息处理」
5. 用户说「GDPR 合规」「个人信息保护法」「数据合规」
6. 用户说「数据共享」「给第三方的数据要脱敏」
7. 用户说「CSV/JSON/SQL 文件中的敏感字段处理」
8. 用户说「数据清洗 + 脱敏」

## 三、内置敏感字段识别

| 字段类型 | 匹配方式 | 默认脱敏方式 | 示例 |
|---|---|---|---|
| 手机号 | 字段名匹配 + 正则 | mask（保留前3后4） | `138****5678` |
| 身份证 | 字段名匹配 + 正则 | mask（保留前6后4） | `110101********1234` |
| 邮箱 | 字段名匹配 + 正则 | mask（保留首字符和域名） | `z***@example.com` |
| 银行卡 | 字段名匹配 + 正则 | mask（保留后4） | `************1234` |
| 姓名 | 字段名匹配 | mask（保留姓） | `张*` |
| 地址 | 字段名匹配 | truncate（保留省市区） | `北京市朝阳区***` |
| IP 地址 | 字段名匹配 + 正则 | mask（保留前两段） | `192.168.***.***` |
| 密码 | 字段名匹配 | nullify（置空） | `` |
| 车牌号 | 字段名匹配 + 正则 | mask（保留前2后1） | `京A****1` |
| QQ号 | 字段名匹配 + 正则 | mask（保留前2后2） | `12****67` |
| 微信号 | 字段名匹配 | mask（保留前2后2） | `we****23` |
| 工资/薪资 | 字段名匹配 | generalize（区间化） | `10000-20000` |
| 年龄 | 字段名匹配 | generalize（区间化） | `20-30` |
| 出生日期 | 字段名匹配 | generalize（只保留年） | `1990-**-**` |
| 其他自定义 | 规则配置 | 可指定 | - |

## 四、6 种脱敏方式

| 方式 | 说明 | 适用场景 | 可逆 |
|---|---|---|---|
| `mask` | 掩码，用 `*` 替换部分字符 | 展示、共享 | 否 |
| `replace` | 替换为固定值或随机值 | 测试数据 | 否 |
| `hash` | SHA-256 哈希（可加盐） | 关联分析、去重 | 否 |
| `truncate` | 截断，保留前 N 个字符 | 地址、长文本 | 否 |
| `generalize` | 泛化，区间化或粗粒度 | 统计分析 | 否 |
| `nullify` | 置空/删除 | 密码、不需要的字段 | 否 |

## 五、操作步骤

### 步骤 1：确认数据格式和敏感字段

向用户确认：
- **数据格式**：CSV / JSON / SQL
- **敏感字段**：哪些列/字段需要脱敏（可自动识别）
- **脱敏方式**：每种字段用什么方式（可使用默认）
- **输出位置**：脱敏后文件保存路径

### 步骤 2：运行脱敏脚本

```bash
# 基本用法：自动识别敏感字段并脱敏（CSV）
python3 scripts/mask_data.py --input data.csv --format csv --output masked_data.csv

# JSON 格式
python3 scripts/mask_data.py --input data.json --format json --output masked_data.json

# SQL 格式（INSERT 语句）
python3 scripts/mask_data.py --input data.sql --format sql --output masked_data.sql

# 使用自定义规则文件
python3 scripts/mask_data.py --input data.csv --format csv --rules rules.json --output masked.csv

# 指定特定字段的脱敏方式
python3 scripts/mask_data.py --input data.csv --format csv \
  --field phone:mask --field email:hash --field name:replace --output masked.csv

# 哈希加盐（提高安全性）
python3 scripts/mask_data.py --input data.csv --format csv --salt my-secret-salt --output masked.csv

# 生成脱敏报告
python3 scripts/mask_data.py --input data.csv --format csv --report --output masked.csv

# 预览模式（只显示前5行脱敏结果，不写文件）
python3 scripts/mask_data.py --input data.csv --format csv --preview
```

### 步骤 3：验证脱敏结果

- 检查输出文件中敏感字段是否已脱敏
- 查看脱敏报告确认处理的字段和行数
- 确认非敏感字段未被误处理
- 确认数据格式未被破坏

## 六、自定义规则文件格式

```json
{
  "rules": [
    {
      "field": "phone",
      "match": "name",
      "method": "mask",
      "params": {"keep_start": 3, "keep_end": 4}
    },
    {
      "field": "email",
      "match": "name",
      "method": "mask",
      "params": {"keep_start": 1, "keep_domain": true}
    },
    {
      "field": "salary",
      "match": "name",
      "method": "generalize",
      "params": {"bins": [0, 5000, 10000, 20000, 50000]}
    },
    {
      "field": "id_card",
      "match": "regex",
      "pattern": "\\d{17}[\\dXx]",
      "method": "hash",
      "params": {"salt": "my-salt"}
    }
  ],
  "auto_detect": true
}
```

## 七、命令行参数

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--input` / `-i` | 输入文件路径 | 必填 |
| `--format` / `-f` | 数据格式：csv/json/sql | 自动检测 |
| `--output` / `-o` | 输出文件路径 | `masked_<原文件名>` |
| `--rules` / `-r` | 自定义规则文件（JSON） | 内置规则 |
| `--field` | 指定字段脱敏方式，格式 `字段名:方式`，可多次 | - |
| `--salt` | 哈希加盐值 | 无 |
| `--report` | 生成脱敏报告 | 关闭 |
| `--preview` | 预览模式（前5行，不写文件） | 关闭 |
| `--no-auto-detect` | 关闭自动敏感字段识别 | 开启 |
| `--encoding` | 文件编码 | utf-8 |

## 八、常见场景处理

### 场景 1：CSV 用户数据脱敏
**用户**：「这个用户表 CSV 里有手机号和身份证，帮我脱敏」
**处理**：自动识别 phone 和 id_card 字段，默认 mask 方式，保留前3后4（手机号）和前6后4（身份证）。

### 场景 2：JSON API 响应脱敏
**用户**：「API 返回的 JSON 里有用户邮箱和地址，要脱敏后给前端」
**处理**：递归遍历 JSON，识别 email 和 address 字段，分别用 mask 和 truncate。

### 场景 3：SQL 导出文件脱敏
**用户**：「数据库导出的 INSERT 语句要脱敏后给测试环境」
**处理**：解析 INSERT 语句，识别列名中的敏感字段，对值进行脱敏，保持 SQL 语法正确。

### 场景 4：日志文件脱敏
**用户**：「日志里有用户手机号和 IP，要脱敏」
**处理**：使用正则匹配方式，对日志文本中的手机号和 IP 进行 mask 处理。

### 场景 5：哈希脱敏用于关联
**用户**：「需要脱敏但还要能关联同一个用户的数据」
**处理**：使用 hash 方式加盐，同一用户 ID 哈希后值相同，可用于关联分析但无法还原。

### 场景 6：薪资数据泛化
**用户**：「薪资数据要脱敏但还要能做统计分析」
**处理**：使用 generalize 方式，将具体薪资映射到区间（如 10000-20000），保留统计分布。

## 九、注意事项

1. **不可逆性**：mask、replace、truncate、generalize、nullify 均不可逆，hash 也不可逆，脱敏前请备份原始数据
2. **哈希加盐**：使用 hash 方式时建议加盐，防止彩虹表攻击；盐值需妥善保管
3. **自动识别局限**：自动识别基于字段名和正则，可能漏检或误检，建议人工复核
4. **嵌套 JSON**：支持递归处理嵌套 JSON 对象和数组
5. **SQL 格式**：仅支持标准 INSERT INTO 语句，不支持复杂 SQL 或存储过程
6. **编码问题**：默认 UTF-8，其他编码需用 `--encoding` 指定
7. **大文件**：流式处理，内存占用低，支持大文件
8. **合规性**：本工具辅助脱敏，具体合规要求请参考《个人信息保护法》《数据安全法》等法规
9. **不处理图片**：仅处理文本数据，图片中的敏感信息需另行处理
10. **测试验证**：脱敏后建议抽样验证，确保敏感信息已完全去除

## 十、文件结构

```
data-masker/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── masking-rules-guide.md            # 脱敏规则配置指南与最佳实践
├── scripts/
│   └── mask_data.py                      # 数据脱敏脚本
└── examples/
    ├── sample-users.csv                  # 示例用户数据（含敏感字段）
    ├── sample-users-masked.csv           # 脱敏后的 CSV
    ├── sample-api-response.json          # 示例 JSON API 响应
    ├── sample-api-response-masked.json   # 脱敏后的 JSON
    ├── sample-insert.sql                 # 示例 SQL INSERT 语句
    └── sample-rules.json                 # 自定义规则示例
```

## 十一、使用示例

### 示例 1：快速脱敏 CSV
**用户**：「帮我把这个用户表的敏感字段脱敏」
**AI**：运行 `--format csv --report` → 自动识别手机号/身份证/邮箱 → 生成脱敏文件和报告 → 汇报处理了多少行、哪些字段。

### 示例 2：哈希加盐脱敏
**用户**：「用户 ID 要脱敏但还要能关联」
**AI**：运行 `--field user_id:hash --salt my-secret` → 同一 ID 哈希值相同 → 可用于跨表关联。

### 示例 3：自定义规则
**用户**：「薪资要泛化到区间，地址只保留到区」
**AI**：创建 rules.json → 配置 salary 用 generalize、address 用 truncate → 运行 `--rules rules.json`。
