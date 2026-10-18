# API 测试最佳实践指南

> api-tester 技能配套指南，帮助写出高质量的 API 测试。

---

## 一、API 测试类型

| 类型 | 说明 | 示例 |
|---|---|---|
| 功能测试 | 验证接口是否按预期工作 | 创建用户后能查询到该用户 |
| 边界测试 | 验证边界条件 | 空值、超长字符串、特殊字符 |
| 性能测试 | 验证响应时间 | 接口响应 < 500ms |
| 安全测试 | 验证认证和权限 | 未授权访问返回 401 |
| 集成测试 | 验证多接口协作 | 创建→查询→更新→删除 |
| 回归测试 | 验证修改不破坏现有功能 | 每次部署后运行全部用例 |

---

## 二、测试用例设计原则

### 1. 每个接口至少包含
- ✅ 正常请求（200/201）
- ✅ 参数缺失（400）
- ✅ 未授权访问（401）
- ✅ 资源不存在（404）
- ✅ 重复创建（409）

### 2. 断言要具体
```python
# ❌ 差：只检查状态码
self.assertEqual(status, 200)

# ✅ 好：检查状态码 + 关键字段 + 数据类型
self.assertEqual(status, 200)
self.assertIn("data", response)
self.assertIsInstance(response["data"], list)
self.assertGreater(len(response["data"]), 0)
```

### 3. 测试数据隔离
- 使用独立的测试账号和测试环境
- POST 创建的数据在测试结束后清理
- 不依赖测试执行顺序（每个用例独立）

---

## 三、认证处理

### Bearer Token
```json
{
  "auth": {"type": "bearer", "token": "your-token"}
}
```
所有请求自动添加 `Authorization: Bearer <token>` 头。

### API Key
```json
{
  "auth": {"type": "apikey", "key": "your-key", "header": "X-API-Key"}
}
```

### 环境变量（推荐）
生成的 Python 脚本支持环境变量覆盖：
```bash
export API_TOKEN=your-token
export API_BASE_URL=https://staging.example.com
python3 test_api.py
```

---

## 四、常见 HTTP 状态码

| 状态码 | 含义 | 测试要点 |
|---|---|---|
| 200 | OK | GET/PUT 成功 |
| 201 | Created | POST 创建成功 |
| 204 | No Content | DELETE 成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突/重复 |
| 422 | Unprocessable | 验证失败 |
| 429 | Too Many Requests | 限流 |
| 500 | Internal Server Error | 服务端错误 |

---

## 五、CI/CD 集成

### GitHub Actions 示例
```yaml
- name: Run API Tests
  run: |
    pip install pytest
    python3 test_api.py --report
  env:
    API_BASE_URL: ${{ secrets.STAGING_URL }}
    API_TOKEN: ${{ secrets.API_TOKEN }}
```

### 测试失败处理
- 非零退出码表示测试失败
- CI 会自动标记构建失败
- 测试报告作为 artifact 上传

---

## 六、性能基准建议

| 接口类型 | 期望响应时间 | P99 上限 |
|---|---|---|
| 简单查询（GET by ID） | < 100ms | < 500ms |
| 列表查询（GET 分页） | < 200ms | < 1s |
| 创建/更新（POST/PUT） | < 300ms | < 1s |
| 删除（DELETE） | < 200ms | < 500ms |
| 复杂查询/聚合 | < 500ms | < 2s |

在描述文件中配置 `max_response_time` 字段自动断言：
```json
{"name": "获取用户列表", "method": "GET", "path": "/users", "max_response_time": 0.5}
```

---

## 七、测试数据管理

### 数据准备
- 使用 mock 数据或测试专用数据
- 不使用生产环境真实数据
- 敏感数据（手机号、身份证）使用脱敏值

### 数据清理
- 测试创建的数据在 teardown 中删除
- 或使用独立的测试数据库，测试后重置

---

## 八、Postman 使用技巧

1. **导入集合**：Postman → Import → 选择生成的 JSON 文件
2. **环境变量**：在 Postman 中创建环境，设置 `base_url` 和 `token`
3. **批量运行**：Collection Runner 一键执行所有请求
4. **监控**：设置定时监控，定期运行 API 测试
5. **协作**：集合可分享给团队成员

---

*本指南由 api-tester 技能提供，配合 generate_api_tests.py 脚本使用*
