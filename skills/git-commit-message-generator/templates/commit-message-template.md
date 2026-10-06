# Conventional Commits 提交信息模板

## 通用格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

---

## 各类型提交信息模板与示例

### feat（新功能）

**模板：**
```
feat(<scope>): <简短描述新增功能>

- <关键变更点 1>
- <关键变更点 2>
- <关键变更点 3>

Closes #<issue编号>
```

**示例：**
```
feat(auth): 添加微信扫码登录功能

- 新增 WeChatAuthService 处理微信 OAuth 流程
- 登录页添加扫码登录入口，支持二维码轮询状态
- 用户表新增 wechat_openid 字段，兼容已有账号绑定

Closes #42
```

---

### fix（Bug 修复）

**模板：**
```
fix(<scope>): <简短描述修复的问题>

<问题原因和修复方案说明>

Closes #<issue编号>
```

**示例：**
```
fix(order): 修复订单金额计算精度丢失

使用浮点数计算订单金额时，0.1 + 0.2 导致精度丢失。
改用 Decimal 类型进行金额计算，保留两位小数。

Closes #156
```

---

### docs（文档变更）

**模板：**
```
docs(<scope>): <简短描述文档变更>

<文档变更说明，可选>
```

**示例：**
```
docs: 更新 README 中的安装说明

- 添加 Python 3.11 兼容性说明
- 补充环境变量配置示例
- 修复快速开始中的命令错误
```

---

### style（代码格式）

**模板：**
```
style(<scope>): <简短描述格式变更>
```

**示例：**
```
style: 统一代码格式（prettier 自动格式化）
```

```
style(import): 按字母顺序排序 import 语句
```

---

### refactor（重构）

**模板：**
```
refactor(<scope>): <简短描述重构内容>

- <重构点 1>
- <重构点 2>

<重构原因，可选>
```

**示例：**
```
refactor(user): 提取用户信息查询为独立服务

- 将 UserController 中的查询逻辑移至 UserQueryService
- 统一异常处理，减少重复代码
- 为查询服务添加单元测试

不改变对外 API 行为。
```

---

### perf（性能优化）

**模板：**
```
perf(<scope>): <简短描述性能优化>

<优化前/后对比数据>

<优化方案说明>
```

**示例：**
```
perf(api): 优化订单列表查询性能

- 添加 user_id + status 联合索引
- 改用分页游标替代 OFFSET 分页
- 查询耗时从 1200ms 降至 80ms

大数据量下 OFFSET 分页性能随页数增长而下降，
游标分页避免了扫描大量无关行。
```

---

### test（测试）

**模板：**
```
test(<scope>): <简短描述测试变更>

- <新增/修改的测试 1>
- <新增/修改的测试 2>
```

**示例：**
```
test(auth): 添加登录接口单元测试

- 测试正常登录流程
- 测试密码错误场景
- 测试账号被锁定场景
- 测试参数校验边界
```

---

### build（构建系统/依赖）

**模板：**
```
build(<scope>): <简短描述构建/依赖变更>

- <变更点 1>
- <变更点 2>
```

**示例：**
```
build(deps): 升级 react 至 18.2.0

- 升级 react 和 react-dom 至 18.2.0
- 适配 createRoot 新 API
- 移除已废弃的 ReactDOM.render 调用
```

---

### ci（CI/CD）

**模板：**
```
ci(<scope>): <简短描述 CI/CD 变更>
```

**示例：**
```
ci: 添加 Python 3.11 到测试矩阵

- GitHub Actions 测试矩阵新增 3.11
- 修复 3.11 下的兼容性警告
```

---

### chore（杂项）

**模板：**
```
chore(<scope>): <简短描述杂项变更>
```

**示例：**
```
chore: 更新 .gitignore，忽略 .env.local 文件
```

```
chore(release): 发布 v1.2.0
```

---

### revert（回滚）

**模板：**
```
revert: <被回滚提交的 subject>

<回滚原因>

此提交回滚了 <commit-hash>。
```

**示例：**
```
revert: feat(auth): 添加微信扫码登录功能

该功能导致登录页白屏，临时回滚。
此提交回滚了 abc1234。
```

---

## 破坏性变更模板

```
<type>(<scope>): <subject>

<body>

BREAKING CHANGE: <破坏性变更描述>

<迁移方案说明>
```

**示例：**
```
refactor(api): 重构用户接口返回格式

将 /api/users 接口返回从数组改为分页对象，
包含 total、page、pageSize 和 data 字段。

BREAKING CHANGE: /api/users 接口返回格式变更，
前端需适配新的分页结构。旧格式将在 v2.0 移除。

迁移方案：将 `res.data` 改为 `res.data.data`，
分页信息从 `res.data.total` 获取。
```

---

## 提交信息检查清单

生成提交信息后，逐项确认：

- [ ] type 为以下之一：feat / fix / docs / style / refactor / perf / test / build / ci / chore / revert
- [ ] subject 为祈使句（「添加」而非「添加了」）
- [ ] subject 具体而非笼统（不用「update」「fix」「changes」）
- [ ] subject 长度 ≤ 50 字符
- [ ] subject 句末无句号
- [ ] scope 准确反映变更模块（或合理省略）
- [ ] body 每行 ≤ 72 字符（如有 body）
- [ ] body 说明「为什么」而非「怎么做」（如有 body）
- [ ] 破坏性变更已标注 `BREAKING CHANGE`
- [ ] 关联 issue 已在 footer 标注（如有）
- [ ] 提交信息与实际 diff 内容一致
- [ ] 无敏感信息（密码、token、内部链接）
