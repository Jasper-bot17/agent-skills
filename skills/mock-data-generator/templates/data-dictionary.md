# 模拟数据字段字典

> mock-data-generator 技能支持的所有数据字段和预设模板说明。

---

## 一、基础标识字段

| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `id` | integer | 自增ID，从1开始 | 1, 2, 3 |
| `uuid` | string | UUID v4 随机唯一标识 | a1b2c3d4-e5f6-7890-abcd-ef1234567890 |

## 二、个人信息字段

| 字段名 | 类型 | 说明 | 中文示例 | 英文示例 |
|---|---|---|---|---|
| `name` | string | 姓名 | 张三 | John Smith |
| `gender` | string | 性别 | 男/女 | Male/Female |
| `age` | integer | 年龄（18-80） | 25 | 32 |
| `email` | string | 邮箱 | zhangsan@example.com | john.smith@gmail.com |
| `phone` | string | 手机号 | 13812345678 | +1-555-0123 |
| `id_card` | string | 身份证号（仅中文） | 110101199001011234 | N/A |

## 三、地址字段

| 字段名 | 类型 | 说明 | 中文示例 | 英文示例 |
|---|---|---|---|---|
| `address` | string | 完整地址 | 北京市朝阳区中山路1号 | 123 Main St, New York, NY 10001 |
| `city` | string | 城市 | 北京 | New York |
| `province` | string | 省份/州 | 北京市 | California |
| `country` | string | 国家 | 中国 | United States |
| `zip_code` | string | 邮编 | 100000 | 10001 |

## 四、时间字段

| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `date` | string | 日期（过去5年内随机） | 2024-03-15 |
| `datetime` | string | 日期时间 | 2024-03-15 14:30:00 |
| `timestamp` | integer | Unix 时间戳 | 1710493800 |
| `hire_date` | string | 入职日期 | 2023-06-01 |
| `enrollment_date` | string | 入学日期 | 2022-09-01 |
| `order_date` | string | 订单日期 | 2024-01-15 |
| `publish_date` | string | 发布日期 | 2024-02-20 |

## 五、职业/公司字段

| 字段名 | 类型 | 说明 | 中文示例 | 英文示例 |
|---|---|---|---|---|
| `company` | string | 公司名 | 阿里巴巴集团 | Acme Corporation |
| `job_title` | string | 职位 | 软件工程师 | Software Engineer |
| `department` | string | 部门 | 技术部 | Engineering |
| `salary` | integer | 薪资 | 15000 | 75000 |

## 六、商业字段

| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `user_id` | integer | 用户ID（1-10000随机） | 4567 |
| `product_name` | string | 产品名 | 高端手机 | Premium Phone |
| `category` | string | 分类 | 电子产品 | Electronics |
| `price` | float | 价格（1-10000） | 99.50 |
| `quantity` | integer | 数量（1-100） | 3 |
| `total` | float | 总价（数量×价格） | 298.50 |
| `order_status` | string | 订单状态 | 已完成 | completed |
| `stock` | integer | 库存（0-1000） | 150 |
| `sku` | string | SKU编码 | ABC12345 |
| `views` | integer | 浏览量（0-100000） | 5234 |

## 七、文章/内容字段

| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `article_title` | string | 文章标题 | 科技与创新的研究 | Technology and Innovation: A Study |
| `author` | string | 作者 | 李四 | Jane Doe |
| `content` | string | 文章内容（段落） | 多句文本... | Lorem ipsum... |
| `description` | string | 描述（单句） | 这是一个测试。 | This is a test. |
| `word` | string | 随机词 | 科技 | technology |
| `sentence` | string | 随机句子 | 这是一段测试文本。 | Lorem ipsum dolor... |
| `paragraph` | string | 随机段落 | 多句组合 | Multi-sentence text |
| `text` | string | 文本（同paragraph） | 同上 | 同上 |

## 八、网络字段

| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `ip` | string | IP地址 | 192.168.1.1 |
| `url` | string | 网址 | https://www.example.com/api/users |
| `method` | string | HTTP方法 | GET |
| `path` | string | URL路径 | /api/users |
| `status` | integer | HTTP状态码 | 200 |
| `response_time` | integer | 响应时间(ms) | 234 |

## 九、其他字段

| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `boolean` | boolean | 布尔值 | true/false |
| `color` | string | 颜色名 | 红色 | Red |
| `hex_color` | string | 十六进制颜色 | #FF5733 |
| `grade` | string | 年级 | 大三 | Junior |
| `major` | string | 专业 | 计算机科学 | Computer Science |
| `school` | string | 学校 | 清华大学 | MIT |

---

## 十、预设模板

### user（用户表）
字段：`id, name, email, phone, gender, age, address, city, country`

### customer（客户表）
字段：`id, name, email, phone, company, job_title, address, city`

### employee（员工表）
字段：`id, name, email, phone, job_title, department, salary, hire_date`

### order（订单表）
字段：`id, user_id, product_name, quantity, price, total, order_date, order_status`

### product（商品表）
字段：`id, product_name, category, price, stock, description, sku`

### article（文章表）
字段：`id, article_title, author, content, publish_date, category, views`

### log（日志表）
字段：`id, timestamp, ip, method, path, status, response_time`

### student（学生表）
字段：`id, name, gender, age, grade, major, school, enrollment_date`

---

## 十一、输出格式

### CSV
标准逗号分隔值，首行为列名，可用 Excel 直接打开。

### JSON
JSON 数组，每个元素为一条记录的对象，支持 `python3 -m json.tool` 验证。

### SQL
`INSERT INTO 表名 (列名) VALUES (值);` 语句，每条记录一行，可用 sqlite3/MySQL 执行。

---

*数据字典由 mock-data-generator 技能提供，使用 `python3 generate_mock_data.py --list` 查看最新字段列表*
