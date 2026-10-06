# 示例：生成的提交信息

以下为基于示例 diff 生成的提交信息，供参考。

---

## 示例 1：新功能（基于 sample-feature.diff）

**Diff 分析结果：**
- 变更文件：4 个（新增 2，修改 2）
- 新增行：+157，删除行：-0
- 推断类型：feat（置信度：high）
- 推断 scope：auth
- 关键变更：新增 WeChatAuthService、新增 /wechat/qrcode 和 /wechat/callback 接口、用户表新增 wechat_openid 和 avatar 字段、新增数据库迁移

**生成的提交信息：**

```
feat(auth): 添加微信扫码登录功能

- 新增 WeChatAuthService 处理微信 OAuth 扫码登录流程
- 登录接口新增 /wechat/qrcode 获取二维码和 /wechat/callback 处理回调
- 用户表新增 wechat_openid 和 avatar 字段，支持已有账号绑定
- 新增数据库迁移脚本 add_wechat_fields

Closes #42
```

---

## 示例 2：Bug 修复（基于 sample-bugfix.diff）

**Diff 分析结果：**
- 变更文件：2 个（修改 2）
- 新增行：+28，删除行：-12
- 推断类型：fix（置信度：medium）
- 推断 scope：order
- 关键变更：calculate_total 方法改用 Decimal、新增精度测试用例
- 检测到关键词：修复、精度

**生成的提交信息：**

```
fix(order): 修复订单金额计算精度丢失

使用浮点数计算订单金额时，0.1 + 0.2 导致精度丢失
（实际结果为 0.30000000000000004）。改用 Decimal 类型
进行金额计算，四舍五入保留两位小数。

- 新增 test_calculate_total_precision 精度测试
- 新增 test_calculate_total_large_numbers 大额订单测试

Closes #156
```

---

## 示例 3：纯格式变更

**Diff 特征：** 仅修改空格、分号、import 排序，无逻辑变更

**生成的提交信息：**

```
style: 统一代码格式（prettier 自动格式化）
```

---

## 示例 4：依赖升级

**Diff 特征：** 修改 package.json / requirements.txt 等依赖文件

**生成的提交信息：**

```
build(deps): 升级 react 至 18.2.0

- 升级 react 和 react-dom 至 18.2.0
- 适配 createRoot 新 API
- 移除已废弃的 ReactDOM.render 调用
```

---

## 示例 5：破坏性变更

**Diff 特征：** 修改 API 返回格式、删除导出的接口/字段

**生成的提交信息：**

```
refactor(api): 重构用户接口返回格式

将 /api/users 接口返回从数组改为分页对象，
包含 total、page、pageSize 和 data 字段。

BREAKING CHANGE: /api/users 接口返回格式变更，
前端需适配新的分页结构。旧格式将在 v2.0 移除。

迁移方案：将 res.data 改为 res.data.data，
分页信息从 res.data.total 获取。
```

---

## 示例 6：文档更新

**Diff 特征：** 仅修改 README、注释、文档文件

**生成的提交信息：**

```
docs: 更新 README 中的安装说明

- 添加 Python 3.11 兼容性说明
- 补充环境变量配置示例
- 修复快速开始中的命令错误
```
