# CHANGELOG 模板与规范参考

> 遵循 Keep a Changelog 规范和 Conventional Commits 规范。

---

## 一、CHANGELOG.md 模板

```markdown
# 更新日志

所有显著变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### ✨ 新增功能
- 待添加的新功能

## [1.0.0] - 2024-01-15

### ✨ 新增功能
- 用户注册功能
- 密码重置功能

### 🐛 问题修复
- 修复登录页面样式问题

### ⚡ 性能提升
- 优化首页加载速度

### 📝 文档更新
- 更新 API 文档
```

---

## 二、Conventional Commits 提交规范

### 2.1 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 2.2 类型说明

| 类型 | 说明 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat(auth): 添加登录功能` |
| `fix` | Bug 修复 | `fix(api): 修复分页错误` |
| `docs` | 文档变更 | `docs(readme): 更新安装说明` |
| `style` | 代码格式（不影响功能） | `style(format): 统一缩进` |
| `refactor` | 重构 | `refactor(user): 重构用户服务` |
| `perf` | 性能优化 | `perf(query): 优化查询性能` |
| `test` | 测试相关 | `test(auth): 添加登录测试` |
| `build` | 构建系统/依赖 | `build(webpack): 优化构建配置` |
| `ci` | CI 配置 | `ci(pipeline): 添加自动部署` |
| `chore` | 杂项 | `chore(deps): 更新依赖` |
| `revert` | 回退 | `revert: 回退上次提交` |

### 2.3 不兼容变更

在类型后加 `!` 标记：

```
feat(api)!: 重构 API 接口（不兼容变更）
```

或在 body 中添加 `BREAKING CHANGE:`：

```
feat(api): 重构 API 接口

BREAKING CHANGE: /api/v1 接口已移除，请使用 /api/v2
```

### 2.4 范围（scope）

可选，用于说明影响的模块：

```
feat(auth): 添加 OAuth 登录
fix(user/profile): 修复头像上传
```

---

## 三、语义化版本（SemVer）

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └─ PATCH：Bug 修复（向后兼容）
  │     └─────── MINOR：新增功能（向后兼容）
  └───────────── MAJOR：不兼容变更
```

- **MAJOR**：有不兼容的 API 变更
- **MINOR**：向后兼容的新增功能
- **PATCH**：向后兼容的 Bug 修复

预发布版本：`1.0.0-alpha.1`、`1.0.0-beta.2`、`1.0.0-rc.1`

---

## 四、版本发布流程

1. 确保所有功能已合并到主分支
2. 更新版本号（package.json / pom.xml 等）
3. 运行 `python3 generate_changelog.py --unreleased --version 1.2.0` 生成变更日志
4. 将变更日志追加到 CHANGELOG.md
5. 提交：`git commit -m "chore(release): 发布 v1.2.0"`
6. 打标签：`git tag -a v1.2.0 -m "Release v1.2.0"`
7. 推送：`git push && git push --tags`

---

## 五、常见问题

**Q: 提交信息不规范怎么办？**
A: 不规范的提交会归入「其他变更」分类。建议团队统一使用 Conventional Commits 规范。

**Q: 如何只看某个版本的变更？**
A: 使用 `--from v1.0.0 --to v2.0.0` 指定版本范围。

**Q: 如何看上次发布后的所有变更？**
A: 使用 `--unreleased` 参数，会自动获取最新标签之后的所有提交。

---

*规范参考由 changelog-generator 技能提供*
