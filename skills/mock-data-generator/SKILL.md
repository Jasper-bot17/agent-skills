---
name: mock-data-generator
description: '模拟数据生成器。快速生成真实感的测试数据，支持 15+ 种数据字段（中文/英文姓名、邮箱、手机号、身份证号、地址、日期、数字、UUID、IP地址、URL、公司名、职位、颜色、Lorem Ipsum文本等），支持 CSV、JSON、SQL INSERT 三种输出格式，可自定义字段组合、数据量、随机种子、输出文件。适用于开发测试、数据库填充、前端演示、性能测试、原型开发等场景。纯 Python 标准库，无外部依赖。'
---

# 模拟数据生成器

## 一、技能定位

本技能用于**快速生成真实感的模拟测试数据**。核心价值：

- **15+ 种数据字段**：姓名、邮箱、手机号、身份证号、地址、日期、数字、UUID、IP地址、URL、公司名、职位、颜色、Lorem Ipsum 文本等
- **中英文双语**：支持中文和英文两种数据风格
- **三种输出格式**：CSV、JSON、SQL INSERT
- **可自定义字段组合**：通过 `--fields` 指定需要哪些字段
- **可复现**：支持 `--seed` 固定随机种子，生成相同数据
- **批量生成**：支持任意数据量（`--count`）
- **输出到文件**：支持 `--output` 写入文件
- **纯标准库**：无外部依赖，开箱即用

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「生成测试数据」「模拟数据」「假数据」「mock data」
2. 用户说「生成用户数据」「生成订单数据」「生成员工数据」
3. 用户说「填充数据库」「数据库测试数据」「SQL 插入数据」
4. 用户说「CSV 测试数据」「JSON 测试数据」
5. 用户说「前端演示数据」「原型数据」「demo data」
6. 用户说「性能测试数据」「压力测试数据」「大量数据」
7. 用户说「生成姓名列表」「生成邮箱列表」「生成手机号」
8. 用户说「随机数据生成」「数据生成器」

## 三、支持的数据字段

| 字段名 | 说明 | 示例（中文） | 示例（英文） |
|---|---|---|---|
| `id` | 自增ID | 1, 2, 3 | 1, 2, 3 |
| `uuid` | UUID v4 | a1b2c3d4-... | a1b2c3d4-... |
| `name` | 姓名 | 张三、李四 | John Smith |
| `email` | 邮箱 | zhangsan@example.com | john.smith@gmail.com |
| `phone` | 手机号 | 13812345678 | +1-555-0123 |
| `id_card` | 身份证号 | 110101199001011234 | N/A |
| `address` | 地址 | 北京市朝阳区xxx路1号 | 123 Main St, New York |
| `city` | 城市 | 北京 | New York |
| `province` | 省份/州 | 北京市 | California |
| `country` | 国家 | 中国 | United States |
| `zip_code` | 邮编 | 100000 | 10001 |
| `date` | 日期 | 2024-03-15 | 2024-03-15 |
| `datetime` | 日期时间 | 2024-03-15 14:30:00 | 2024-03-15 14:30:00 |
| `timestamp` | Unix时间戳 | 1710493800 | 1710493800 |
| `age` | 年龄 | 25 | 25 |
| `gender` | 性别 | 男/女 | Male/Female |
| `company` | 公司名 | 阿里巴巴集团 | Acme Corporation |
| `job_title` | 职位 | 软件工程师 | Software Engineer |
| `salary` | 薪资 | 15000 | 75000 |
| `price` | 价格 | 99.50 | 99.50 |
| `quantity` | 数量 | 3 | 3 |
| `boolean` | 布尔值 | true/false | true/false |
| `ip` | IP地址 | 192.168.1.1 | 192.168.1.1 |
| `url` | 网址 | https://example.com | https://example.com |
| `color` | 颜色 | 红色 | Red |
| `hex_color` | 十六进制颜色 | #FF5733 | #FF5733 |
| `text` | Lorem Ipsum文本 | 这是一段模拟文本... | Lorem ipsum dolor... |
| `word` | 随机词 | 科技 | technology |
| `sentence` | 随机句子 | 这是一个测试句子。 | This is a test sentence. |
| `paragraph` | 随机段落 | 多句文本... | Multi-sentence text... |

## 四、预设数据模板

| 模板名 | 字段组合 | 适用场景 |
|---|---|---|
| `user` | id, name, email, phone, gender, age, address, city, country | 用户表 |
| `customer` | id, name, email, phone, company, job_title, address, city | 客户表 |
| `employee` | id, name, email, phone, job_title, department, salary, hire_date | 员工表 |
| `order` | id, user_id, product_name, quantity, price, total, order_date, status | 订单表 |
| `product` | id, name, category, price, stock, description, sku | 商品表 |
| `article` | id, title, author, content, publish_date, category, views | 文章表 |
| `log` | id, timestamp, ip, method, url, status, response_time | 日志表 |
| `student` | id, name, gender, age, grade, major, school, enrollment_date | 学生表 |

## 五、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 数据量（`--count`，默认 10）
- 输出格式（`--format`：csv/json/sql，默认 csv）
- 字段组合（`--fields` 或 `--template`）
- 语言风格（`--lang`：zh/en，默认 zh）
- 输出文件（`--output`，可选）
- 随机种子（`--seed`，可选，用于复现）

### 步骤 2：运行脚本

使用 `scripts/generate_mock_data.py`：

```bash
# 基本用法：生成 10 条用户数据（CSV）
python3 scripts/generate_mock_data.py --template user --count 10

# 生成 JSON 格式
python3 scripts/generate_mock_data.py --template user --count 20 --format json

# 生成 SQL INSERT 语句
python3 scripts/generate_mock_data.py --template user --count 50 --format sql --table users

# 自定义字段
python3 scripts/generate_mock_data.py --fields id,name,email,phone,city --count 100

# 英文数据
python3 scripts/generate_mock_data.py --template user --count 10 --lang en

# 固定随机种子（可复现）
python3 scripts/generate_mock_data.py --template user --count 10 --seed 42

# 输出到文件
python3 scripts/generate_mock_data.py --template user --count 1000 --output users.csv

# 列出所有可用字段和模板
python3 scripts/generate_mock_data.py --list
```

### 步骤 3：验证输出

- CSV：可用 Excel 或文本编辑器打开，检查列数和数据格式
- JSON：可用 `python3 -m json.tool` 验证格式
- SQL：可用 `sqlite3 :memory: < output.sql` 验证语法

### 步骤 4：安全提示

1. 本技能生成的所有数据均为随机模拟数据，不包含任何真实个人信息
2. 身份证号为按规则生成的模拟号码，不对应真实人员
3. 手机号为符合格式规则的随机号码，请勿用于实际联系
4. 邮箱域名使用 example.com 等保留域名，不会发送真实邮件
5. 生成的数据仅用于开发测试，不得用于欺诈或其他非法用途
6. 如需真实数据用于生产环境，请使用经过授权的数据源

## 六、常见场景处理

### 场景 1：生成用户测试数据
**用户**：「帮我生成 100 条用户测试数据」
**处理**：`--template user --count 100 --format csv`

### 场景 2：生成数据库插入语句
**用户**：「生成 SQL 插入语句，往 users 表插 50 条数据」
**处理**：`--template user --count 50 --format sql --table users`

### 场景 3：生成订单数据
**用户**：「生成一些订单测试数据」
**处理**：`--template order --count 20 --format json`

### 场景 4：自定义字段
**用户**：「只要姓名、邮箱、手机号三列」
**处理**：`--fields name,email,phone --count 50`

### 场景 5：英文数据
**用户**：「生成英文的测试数据」
**处理**：`--template user --count 10 --lang en`

### 场景 6：可复现数据
**用户**：「每次生成一样的数据」
**处理**：`--template user --count 10 --seed 12345`

### 场景 7：大量数据
**用户**：「生成 10000 条数据做性能测试」
**处理**：`--template user --count 10000 --output large_data.csv`

### 场景 8：生成日志数据
**用户**：「生成模拟的访问日志」
**处理**：`--template log --count 100 --format csv`

## 七、注意事项

1. **数据量限制**：理论上无上限，但超过 100 万条时建议输出到文件，避免终端输出过大
2. **SQL 表名**：使用 `--table` 指定表名，默认 `mock_data`
3. **字段顺序**：`--fields` 中指定的顺序即为输出列的顺序
4. **ID 字段**：`id` 为自增整数，从 1 开始；`uuid` 为随机 UUID v4
5. **日期范围**：`date` 字段默认生成过去 5 年内的随机日期
6. **薪资/价格**：`salary` 默认 5000-50000（中文）或 30000-150000（英文）；`price` 默认 1-10000
7. **中文姓名**：从常见姓氏和名字库中随机组合
8. **英文姓名**：从常见英文名和姓氏库中随机组合
9. **不修改文件**：除非指定 `--output`，否则只输出到终端
10. **纯标准库**：不需要安装任何第三方包

## 八、文件结构

```
mock-data-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── data-dictionary.md                # 数据字段字典与预设模板说明
├── scripts/
│   └── generate_mock_data.py             # 模拟数据生成脚本
└── examples/
    ├── sample-users.csv                  # 示例用户数据（CSV）
    ├── sample-orders.json                # 示例订单数据（JSON）
    └── sample-employees.sql              # 示例员工数据（SQL）
```

## 九、使用示例

### 示例 1：用户数据（CSV）
**用户**：「生成 5 条用户数据」
**AI**：运行 `--template user --count 5` → 输出包含 id、name、email、phone、gender、age、address、city、country 的 CSV

### 示例 2：订单数据（JSON）
**用户**：「生成 JSON 格式的订单数据」
**AI**：运行 `--template order --count 10 --format json` → 输出包含 id、user_id、product_name、quantity、price、total、order_date、status 的 JSON 数组

### 示例 3：员工数据（SQL）
**用户**：「生成 SQL 插入语句」
**AI**：运行 `--template employee --count 20 --format sql --table employees` → 输出 `INSERT INTO employees (...) VALUES (...);` 语句
