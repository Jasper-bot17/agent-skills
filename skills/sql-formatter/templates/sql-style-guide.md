# SQL 编码规范与风格指南

> 适用于 MySQL / PostgreSQL / SQLite / Oracle / SQL Server 等主流数据库。

---

## 一、命名规范

### 1.1 表名
- 使用小写字母和下划线，如 `user_info`、`order_items`
- 使用复数形式，如 `users`、`orders`
- 避免使用保留字，如 `order` → `orders`、`user` → `users`
- 前缀区分模块，如 `prod_products`、`ord_orders`

### 1.2 列名
- 使用小写字母和下划线，如 `created_at`、`user_name`
- 主键统一用 `id`
- 外键用 `表名_id`，如 `user_id`、`order_id`
- 布尔值用 `is_` 前缀，如 `is_active`、`is_deleted`
- 时间戳用 `_at` 后缀，如 `created_at`、`updated_at`

### 1.3 别名
- 表别名使用有意义的缩写，如 `users u`、`orders o`、`order_items oi`
- 列别名使用 AS 关键字，如 `COUNT(*) AS total`

---

## 二、格式规范

### 2.1 关键字大写
所有 SQL 关键字大写：
```sql
SELECT id, name FROM users WHERE status = 'active';
```

### 2.2 缩进
- 使用 4 空格缩进
- 子查询缩进一级
- SELECT 列各占一行并缩进

```sql
SELECT
    u.id,
    u.name,
    COUNT(o.id) AS order_count
FROM
    users u
LEFT JOIN
    orders o ON u.id = o.user_id
WHERE
    u.status = 'active'
GROUP BY
    u.id,
    u.name
ORDER BY
    order_count DESC
LIMIT 10;
```

### 2.3 空格
- 运算符两侧加空格：`id = 1`、`age > 18`
- 逗号后加空格：`id, name, email`
- 括号内不加空格：`COUNT(id)`、`WHERE id IN (1, 2, 3)`

### 2.4 换行
- 每个顶层子句（SELECT/FROM/WHERE/GROUP BY/HAVING/ORDER BY/LIMIT）单独成行
- SELECT 列各占一行
- 多个 AND/OR 条件各占一行
- 语句末尾加分号

---

## 三、查询规范

### 3.1 避免 SELECT *
明确指定需要的列：
```sql
-- 不推荐
SELECT * FROM users;

-- 推荐
SELECT id, name, email FROM users;
```

### 3.2 使用表别名
多表查询时使用别名：
```sql
SELECT u.id, u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id;
```

### 3.3 WHERE 条件
- 避免在列上使用函数，导致索引失效
- 范围查询使用 BETWEEN 或 >= / <=
- 模糊查询避免前导通配符

```sql
-- 不推荐（索引失效）
WHERE YEAR(created_at) = 2024
WHERE name LIKE '%张%'

-- 推荐
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
WHERE name LIKE '张%'
```

### 3.4 JOIN 规范
- 明确指定 JOIN 类型（INNER/LEFT/RIGHT/FULL）
- ON 子句写连接条件，WHERE 写过滤条件
- 避免超过 3 个表的 JOIN

### 3.5 排序与分页
- ORDER BY 必须指定 ASC/DESC
- 大表分页避免深偏移（LIMIT 100000, 10）
- 使用游标分页或延迟关联优化深分页

---

## 四、性能建议

### 4.1 索引
- WHERE、JOIN、ORDER BY、GROUP BY 涉及的列考虑加索引
- 联合索引遵循最左前缀原则
- 避免在索引列上使用函数或隐式类型转换

### 4.2 子查询 vs JOIN
- 优先使用 JOIN 替代子查询（大多数情况）
- IN 子查询在数据量大时可能性能较差
- EXISTS 比 IN 更适合外表大、内表小的场景

### 4.3 聚合查询
- 聚合前尽量过滤数据
- 避免在 HAVING 中使用复杂条件
- 考虑使用覆盖索引

---

## 五、安全规范

### 5.1 防止 SQL 注入
- 使用参数化查询/预编译语句
- 禁止拼接用户输入到 SQL
- 对输入进行白名单校验

### 5.2 权限控制
- 应用账号只授予必要权限
- 禁止使用 root/sa 账号运行应用
- 敏感字段加密存储

### 5.3 数据保护
- 生产环境查询避免 SELECT *
- 导出数据前脱敏
- 日志中不记录完整 SQL 参数

---

## 六、常见错误

| 错误 | 说明 | 修正 |
|---|---|---|
| 引号未闭合 | 字符串缺少结束引号 | 检查单引号配对 |
| 括号不匹配 | 函数或子查询括号未闭合 | 逐层检查括号 |
| 缺少 FROM | SELECT 语句没有 FROM（非常量查询） | 添加 FROM 子句 |
| 列名歧义 | 多表查询中列名不唯一 | 使用表别名限定列名 |
| 保留字冲突 | 表名或列名使用了 SQL 保留字 | 重命名或加引号 |
| 类型不匹配 | 比较运算符两侧类型不一致 | 显式转换类型 |
| GROUP BY 错误 | SELECT 中非聚合列未在 GROUP BY 中 | 添加到 GROUP BY 或使用聚合函数 |

---

*规范参考由 sql-formatter 技能提供*
