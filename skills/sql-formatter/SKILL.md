---
name: sql-formatter
description: 'SQL 格式化与分析助手。对 SQL 查询进行专业格式化（关键字大写、缩进对齐、换行规范），支持多种 SQL 方言（MySQL/PostgreSQL/SQLite/Oracle/SQL Server），提供语法校验（括号匹配、关键字检查、常见错误检测），自动提取查询中的表名和列名，解释查询结构（SELECT/FROM/WHERE/GROUP BY/ORDER BY/JOIN 等子句分析），支持压缩输出和 FROM 子句美化。适用于 SQL 代码美化、查询审查、表结构分析、SQL 学习等场景。'
---

# SQL 格式化与分析助手

## 一、技能定位

本技能用于**SQL 查询的格式化、校验与分析**。核心价值：

- 专业格式化：关键字大写、缩进对齐、换行规范
- 多方言支持：MySQL / PostgreSQL / SQLite / Oracle / SQL Server
- 语法校验：括号匹配、关键字检查、常见错误检测
- 表列提取：自动识别查询中的表名和列名
- 结构解释：分析各子句（SELECT/FROM/WHERE/GROUP BY/ORDER BY/JOIN）
- 压缩输出：去除多余空格和换行，生成紧凑 SQL

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「格式化 SQL」「美化 SQL」「整理一下这条 SQL」
2. 用户说「检查 SQL 语法」「这条 SQL 有没有问题」
3. 用户说「提取 SQL 中的表」「看看查了哪些表和字段」
4. 用户说「解释这条 SQL」「分析一下查询结构」
5. 用户说「压缩 SQL」「把 SQL 变成一行」
6. 用户说「SQL 代码审查」「看看这条查询效率如何」
7. 用户上传 .sql 文件要求处理

## 三、SQL 关键字与格式化规范

### 3.1 关键字大写

以下关键字统一大写：

- **查询类**：SELECT、FROM、WHERE、GROUP BY、HAVING、ORDER BY、LIMIT、OFFSET、DISTINCT、UNION、UNION ALL、INTERSECT、EXCEPT
- **连接类**：JOIN、INNER JOIN、LEFT JOIN、RIGHT JOIN、FULL JOIN、CROSS JOIN、ON、USING
- **条件类**：AND、OR、NOT、IN、EXISTS、BETWEEN、LIKE、IS NULL、IS NOT NULL、AS
- **聚合类**：COUNT、SUM、AVG、MIN、MAX、GROUP_CONCAT
- **函数类**：COALESCE、NULLIF、CAST、CONVERT、CASE、WHEN、THEN、ELSE、END
- **数据操作**：INSERT、UPDATE、DELETE、MERGE、INTO、VALUES、SET
- **数据定义**：CREATE、ALTER、DROP、TABLE、INDEX、VIEW、DATABASE、SCHEMA
- **事务类**：BEGIN、COMMIT、ROLLBACK、TRANSACTION
- **其他**：WITH、RECURSIVE、ASC、DESC、ALL、ANY、SOME

### 3.2 格式化示例

**格式化前：**
```sql
select u.id,u.name,u.email,count(o.id) as order_count from users u left join orders o on u.id=o.user_id where u.status='active' and o.created_at>='2024-01-01' group by u.id,u.name,u.email having count(o.id)>5 order by order_count desc limit 10
```

**格式化后：**
```sql
SELECT
    u.id,
    u.name,
    u.email,
    COUNT(o.id) AS order_count
FROM
    users u
LEFT JOIN
    orders o ON u.id = o.user_id
WHERE
    u.status = 'active'
    AND o.created_at >= '2024-01-01'
GROUP BY
    u.id,
    u.name,
    u.email
HAVING
    COUNT(o.id) > 5
ORDER BY
    order_count DESC
LIMIT 10
```

## 四、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 格式化 / 校验 / 提取表列 / 解释结构 / 压缩
- SQL 方言（默认通用 SQL）
- 输入方式（直接输入 / 文件）

### 步骤 2：运行脚本

使用 `scripts/format_sql.py`：

```bash
# 格式化 SQL（从文件）
python3 scripts/format_sql.py --file query.sql

# 格式化 SQL（直接输入）
python3 scripts/format_sql.py --sql "select * from users where id=1"

# 指定 SQL 方言
python3 scripts/format_sql.py --file query.sql --dialect mysql

# 语法校验
python3 scripts/format_sql.py --file query.sql --check

# 提取表和列
python3 scripts/format_sql.py --file query.sql --extract

# 解释查询结构
python3 scripts/format_sql.py --file query.sql --explain

# 压缩输出
python3 scripts/format_sql.py --file query.sql --minify

# 保存到文件
python3 scripts/format_sql.py --file query.sql --output formatted.sql

# 全部功能（格式化+校验+提取+解释）
python3 scripts/format_sql.py --file query.sql --all
```

### 步骤 3：解读结果

- **格式化输出**：规范的 SQL 代码
- **校验报告**：语法错误、警告、建议
- **表列提取**：涉及的表名、列名、JOIN 关系
- **结构解释**：各子句的作用和执行顺序
- **压缩输出**：单行紧凑 SQL

### 步骤 4：安全提示

1. 本技能只做静态分析，不执行 SQL，不会连接数据库
2. SQL 中可能包含敏感信息（表名、字段名、数据），处理后请注意清理
3. 语法校验为基础检查，不能替代数据库的实际执行验证

## 五、输出规范

### 5.1 格式化输出

```sql
SELECT
    column1,
    column2
FROM
    table1
WHERE
    condition
ORDER BY
    column1 ASC
```

### 5.2 校验报告

```
📋 SQL 语法校验报告
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 括号匹配：通过
✅ 关键字检查：通过
⚠️  警告：SELECT * 不建议在生产环境使用
💡 建议：为表添加别名以提高可读性
━━━━━━━━━━━━━━━━━━━━━━━━
结果：通过（1 个警告，1 条建议）
```

### 5.3 表列提取

```
📊 查询分析
━━━━━━━━━━━━━━━━━━━━━━━━
涉及表（2个）：
  1. users (别名 u)
  2. orders (别名 o)

涉及列（5个）：
  - users.id
  - users.name
  - users.email
  - orders.id
  - orders.user_id

JOIN 关系：
  users.id = orders.user_id (LEFT JOIN)

WHERE 条件：
  - users.status = 'active'
  - orders.created_at >= '2024-01-01'
```

### 5.4 结构解释

```
🔍 查询结构解释
━━━━━━━━━━━━━━━━━━━━━━━━
执行顺序：
  1. FROM/JOIN：从 users 表左连接 orders 表
  2. WHERE：筛选 status='active' 且 2024年后的订单
  3. GROUP BY：按用户分组
  4. HAVING：筛选订单数 > 5 的用户
  5. SELECT：选择用户信息和订单数
  6. ORDER BY：按订单数降序
  7. LIMIT：取前 10 条

子句分析：
  - SELECT：5 个字段，1 个聚合函数
  - FROM：1 个主表
  - JOIN：1 个左连接
  - WHERE：2 个条件
  - GROUP BY：3 个分组字段
  - HAVING：1 个聚合条件
  - ORDER BY：1 个排序字段
  - LIMIT：10 条
```

## 六、常见场景处理

### 场景 1：格式化复杂 SQL
**用户**：「帮我把这条 SQL 格式化一下」
**处理**：运行格式化 → 输出规范 SQL → 如有问题给出建议。

### 场景 2：SQL 语法检查
**用户**：「这条 SQL 有没有语法错误」
**处理**：运行校验 → 检查括号匹配、关键字、常见错误 → 输出报告。

### 场景 3：分析查询涉及的表
**用户**：「看看这条 SQL 查了哪些表和字段」
**处理**：运行提取 → 列出表名、列名、JOIN 关系、WHERE 条件。

### 场景 4：解释 SQL 执行逻辑
**用户**：「解释一下这条 SQL 是怎么执行的」
**处理**：运行解释 → 按执行顺序分析各子句 → 说明查询逻辑。

### 场景 5：压缩 SQL
**用户**：「把这条 SQL 变成一行，我要放到代码里」
**处理**：运行压缩 → 去除多余空格和换行 → 输出单行 SQL。

## 七、注意事项

1. **静态分析**：本技能只做静态文本分析，不连接数据库，不执行 SQL。
2. **方言差异**：不同数据库的 SQL 语法有差异，指定方言可获得更准确的结果。
3. **复杂 SQL**：嵌套子查询、CTE、窗口函数等复杂语法可能无法完全解析。
4. **动态 SQL**：包含变量、模板、拼接的 SQL 可能无法正确解析。
5. **格式化风格**：默认使用 4 空格缩进，关键字大写，可通过参数调整。
6. **编码**：SQL 文件默认使用 UTF-8 编码，其他编码可能出现乱码。
7. **不修改文件**：默认输出到终端，使用 --output 才会写入文件。
8. **大文件**：SQL 文件过大时可能需要较长时间，建议分批处理。

## 八、文件结构

```
sql-formatter/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── sql-style-guide.md                 # SQL 编码规范与风格指南
├── scripts/
│   └── format_sql.py                      # SQL 格式化与分析脚本
└── examples/
    ├── sample-query.sql                   # 示例 SQL 查询
    ├── sample-formatted.sql               # 示例格式化输出
    └── sample-analysis-report.md          # 示例分析报告
```

## 九、使用示例

### 示例 1：快速格式化
**用户**：「格式化这条 SQL：select * from users where age > 18」
**AI**：运行 `--sql` → 输出格式化后的 SQL。

### 示例 2：全面分析
**用户**：「帮我看看这条 SQL，格式化一下，再检查有没有问题」
**AI**：运行 `--all` → 输出格式化 SQL + 校验报告 + 表列提取 + 结构解释。

### 示例 3：压缩 SQL
**用户**：「把这个 SQL 文件压缩成一行」
**AI**：运行 `--minify --output compact.sql` → 生成单行 SQL 文件。
