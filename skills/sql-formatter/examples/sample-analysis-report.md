SELECT
    u.id,
    u.name,
    u.email,
    COUNT(o.id) AS order_count,
    SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id=o.user_id
WHERE u.status='active'
AND o.created_at>='2024-01-01'
GROUP BY
    u.id,
    u.name,
    u.email
HAVING COUNT(o.id)>5
ORDER BY
    total_spent DESC
LIMIT 10


📋 SQL 语法校验报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 括号匹配：通过
✅ 引号匹配：通过
✅ 关键字检查：通过

💡 建议：
   - 建议在 SQL 语句末尾添加分号 ';'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
结果：通过（0 个错误，0 个警告，1 条建议）

📊 查询分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
涉及表（2个）：
  1. users (别名 u)
  2. orders (别名 o)

涉及列（5个）：
  - count(o.id)
  - sum(o.total)
  - u.email
  - u.id
  - u.name

JOIN 关系：
  - u.id = o.user_id

WHERE 条件：
  - u.status='active'
  - o.created_at>='2024-01-01'

GROUP BY（3个字段）：
  - u.id
  - u.name
  - u.email

ORDER BY（1个字段）：
  - total_spent desc

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 查询结构解释
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
执行顺序：
  1. FROM/JOIN：从 users 表查询，连接 1 个表
  2. WHERE：筛选 1 个条件
  3. GROUP BY：按 3 个字段分组
  4. HAVING：筛选分组结果
  5. SELECT：选择 5 个字段，包含聚合函数
  6. ORDER BY：按 1 个字段降序排序
  7. LIMIT：取前 10 条

子句分析：
  - SELECT：选择 5 个字段，包含聚合函数
  - FROM/JOIN：从 users 表查询，连接 1 个表
  - WHERE：筛选 1 个条件
  - GROUP BY：按 3 个字段分组
  - HAVING：筛选分组结果
  - ORDER BY：按 1 个字段降序排序
  - LIMIT：取前 10 条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
