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

