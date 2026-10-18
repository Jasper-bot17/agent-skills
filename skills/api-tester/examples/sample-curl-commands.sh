#!/bin/bash
# API 测试 - curl 命令集合
# 自动生成于 2026-10-18 20:36:26

BASE_URL="https://api.example.com"
TOKEN="test-token-123"
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo "=== 1. 获取用户列表 ==="
echo "期望状态码: 200"
curl -s -X GET "$BASE_URL/api/users?page=1&limit=10" -H "$AUTH_HEADER" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || curl -s -X GET "$BASE_URL/api/users?page=1&limit=10" -H "$AUTH_HEADER" -H "Content-Type: application/json"

echo ""

echo "=== 2. 获取用户详情 ==="
echo "期望状态码: 200"
curl -s -X GET "$BASE_URL/api/users/1" -H "$AUTH_HEADER" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || curl -s -X GET "$BASE_URL/api/users/1" -H "$AUTH_HEADER" -H "Content-Type: application/json"

echo ""

echo "=== 3. 创建用户 ==="
echo "期望状态码: 201"
curl -s -X POST "$BASE_URL/api/users" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"name": "测试用户", "email": "test@example.com", "age": 25}' | python3 -m json.tool 2>/dev/null || curl -s -X POST "$BASE_URL/api/users" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"name": "测试用户", "email": "test@example.com", "age": 25}'

echo ""

echo "=== 4. 更新用户 ==="
echo "期望状态码: 200"
curl -s -X PUT "$BASE_URL/api/users/1" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"name": "更新后的名字"}' | python3 -m json.tool 2>/dev/null || curl -s -X PUT "$BASE_URL/api/users/1" -H "$AUTH_HEADER" -H "Content-Type: application/json" -d '{"name": "更新后的名字"}'

echo ""

echo "=== 5. 删除用户 ==="
echo "期望状态码: 204"
curl -s -X DELETE "$BASE_URL/api/users/1" -H "$AUTH_HEADER" -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || curl -s -X DELETE "$BASE_URL/api/users/1" -H "$AUTH_HEADER" -H "Content-Type: application/json"

echo ""

