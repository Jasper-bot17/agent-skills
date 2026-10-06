---
name: changelog-generator
description: '变更日志生成助手。解析 Git 仓库提交历史，按 Conventional Commits 规范自动分类（feat/fix/docs/style/refactor/perf/test/chore/build/ci），支持按版本标签或日期范围分组，生成符合 Keep a Changelog 规范的 Markdown 变更日志，提供提交类型统计、作者贡献统计、未发布变更管理，可指定输出格式和版本号。适用于项目发布前生成 CHANGELOG.md、版本发布说明、提交历史回顾等场景。'
---

# 变更日志生成助手

## 一、技能定位

本技能用于**从 Git 提交历史自动生成变更日志**。核心价值：

- 解析 Git log，提取提交信息、日期、作者
- 按 Conventional Commits 规范自动分类
- 按版本标签或日期范围分组
- 生成 Keep a Changelog 格式的 Markdown 文档
- 提交统计（按类型、按作者）
- 未发布变更管理

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「生成变更日志」「写 CHANGELOG」「生成本次更新说明」
2. 用户说「整理一下这个版本的提交」「版本发布说明」
3. 用户说「看看最近改了什么」「提交历史回顾」
4. 用户说「统计一下提交记录」「谁提交得多」
5. 用户说「生成 release notes」「发布公告」
6. 用户说「按类型分类提交」「feat 和 fix 分开列」

## 三、Conventional Commits 规范

提交信息格式：`<type>(<scope>): <subject>`

### 3.1 支持的类型

| 类型 | 说明 | 变更日志分类 |
|---|---|---|
| `feat` | 新功能 | ✨ 新增功能 |
| `fix` | Bug 修复 | 🐛 问题修复 |
| `docs` | 文档变更 | 📝 文档更新 |
| `style` | 代码格式（不影响功能） | 💄 样式调整 |
| `refactor` | 重构（既不修复 bug 也不增加功能） | ♻️ 代码重构 |
| `perf` | 性能优化 | ⚡ 性能提升 |
| `test` | 测试相关 | ✅ 测试更新 |
| `build` | 构建系统或外部依赖 | 📦 构建变更 |
| `ci` | CI 配置 | 🔧 CI/CD |
| `chore` | 杂项（不修改 src 或测试） | 🔨 杂项 |
| `revert` | 回退提交 | ⏪️ 回退 |

### 3.2 示例

```
feat(auth): 添加用户登录功能
fix(api): 修复用户列表分页错误
docs(readme): 更新安装说明
refactor(user): 重构用户服务层
perf(query): 优化数据库查询性能
```

## 四、Keep a Changelog 格式

```markdown
# 更新日志

所有显著变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### ✨ 新增功能
- 用户登录功能

## [1.0.0] - 2024-01-15

### ✨ 新增功能
- 用户注册
- 密码重置

### 🐛 问题修复
- 修复登录页面样式问题
```

## 五、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 生成变更日志 / 提交统计 / 发布说明
- Git 仓库路径（默认当前目录）
- 版本范围（标签/日期/全部）
- 输出格式（Markdown/JSON/纯文本）

### 步骤 2：运行脚本

使用 `scripts/generate_changelog.py`：

```bash
# 生成完整变更日志（所有标签 + 未发布）
python3 scripts/generate_changelog.py --repo /path/to/repo

# 只生成未发布的变更
python3 scripts/generate_changelog.py --repo /path/to/repo --unreleased

# 指定版本范围
python3 scripts/generate_changelog.py --repo /path/to/repo --from v1.0.0 --to v2.0.0

# 指定日期范围
python3 scripts/generate_changelog.py --repo /path/to/repo --since 2024-01-01 --until 2024-06-30

# 指定版本号（用于未发布变更的标题）
python3 scripts/generate_changelog.py --repo /path/to/repo --version 1.2.0

# 显示提交统计
python3 scripts/generate_changelog.py --repo /path/to/repo --stats

# JSON 格式输出
python3 scripts/generate_changelog.py --repo /path/to/repo --format json

# 保存到文件
python3 scripts/generate_changelog.py --repo /path/to/repo --output CHANGELOG.md
```

### 步骤 3：解读结果

- **变更日志**：按版本分组，每个版本内按类型分类
- **提交统计**：各类型提交数量、作者贡献排名
- **未发布变更**：最新标签之后的所有提交

### 步骤 4：安全提示

1. 本技能只读取 Git 历史，不修改任何文件
2. 提交信息可能包含敏感信息，生成的日志请检查后再发布
3. 建议遵循 Conventional Commits 规范以获得最佳分类效果

## 六、输出规范

### 6.1 完整变更日志

```
# 更新日志

## [未发布]

### ✨ 新增功能
- feat(auth): 添加 OAuth 登录 (@alice)
- feat(api): 新增用户批量导出接口 (@bob)

### 🐛 问题修复
- fix(ui): 修复移动端导航栏显示问题 (@alice)

## [1.2.0] - 2024-06-15

### ✨ 新增功能
- feat(search): 添加全文搜索功能

### ⚡ 性能提升
- perf(db): 优化查询性能 40%

### 🐛 问题修复
- fix(auth): 修复 token 过期处理
```

### 6.2 提交统计

```
📊 提交统计
━━━━━━━━━━━━━━━━━━━━━━━━
总提交数：156

按类型分布：
  ✨ feat:        45 (28.8%) ████████████
  🐛 fix:         38 (24.4%) ██████████
  📝 docs:        22 (14.1%) ██████
  ♻️ refactor:    18 (11.5%) █████
  ⚡ perf:        12 ( 7.7%) ███
  ✅ test:        10 ( 6.4%) ██
  🔧 ci:           6 ( 3.8%) █
  🔨 chore:        5 ( 3.2%) █

作者贡献：
  1. alice@example.com    68 (43.6%)
  2. bob@example.com      52 (33.3%)
  3. charlie@example.com  36 (23.1%)
```

## 七、常见场景处理

### 场景 1：发布前生成 CHANGELOG
**用户**：「准备发布 v2.0，帮我生成变更日志」
**处理**：扫描 Git 历史 → 按标签分组 → 生成 Keep a Changelog 格式 → 保存为 CHANGELOG.md。

### 场景 2：只看未发布的变更
**用户**：「看看上次发布后改了什么」
**处理**：找到最新标签 → 提取之后的所有提交 → 按类型分类 → 输出未发布变更。

### 场景 3：版本发布说明
**用户**：「生成 v1.5.0 的发布说明」
**处理**：提取 v1.4.0 到 v1.5.0 之间的提交 → 按类型分类 → 生成发布说明。

### 场景 4：提交统计
**用户**：「统计一下这个月的提交情况」
**处理**：指定日期范围 → 统计类型分布和作者贡献 → 输出统计报告。

### 场景 5：非规范提交
**用户**：「我的提交信息不规范，能生成吗」
**处理**：尝试解析 Conventional Commits 格式 → 无法解析的归入「其他变更」→ 建议遵循规范。

## 八、注意事项

1. **Git 仓库**：必须在 Git 仓库中运行，或通过 --repo 指定仓库路径。
2. **提交规范**：最佳效果需要遵循 Conventional Commits 规范；不规范的提交会归入「其他变更」。
3. **版本标签**：按版本分组需要 Git 标签（如 v1.0.0）；没有标签时按日期或全部输出。
4. **日期格式**：使用 YYYY-MM-DD 格式，如 2024-01-15。
5. **作者信息**：使用 Git 配置的 user.email 作为作者标识。
6. **大仓库**：提交数量很多时可能需要较长时间，建议指定版本或日期范围。
7. **合并提交**：默认包含合并提交，可通过 --no-merges 排除。
8. **编码**：提交信息默认使用 UTF-8 编码，其他编码可能出现乱码。
9. **不修改文件**：本技能只读取 Git 历史，不会修改任何文件或提交。
10. **输出检查**：生成的变更日志请检查后再发布，确保不包含敏感信息。

## 九、文件结构

```
changelog-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── changelog-template.md              # CHANGELOG 模板与规范参考
├── scripts/
│   └── generate_changelog.py              # 变更日志生成脚本
└── examples/
    ├── sample-git-log.txt                 # 示例 Git 日志输出
    └── sample-changelog.md                # 示例生成的变更日志
```

## 十、使用示例

### 示例 1：快速生成
**用户**：「在当前项目生成变更日志」
**AI**：运行 `--repo .` → 输出完整变更日志。

### 示例 2：未发布变更
**用户**：「看看上次发布后改了什么」
**AI**：运行 `--unreleased` → 输出最新标签之后的所有变更。

### 示例 3：发布说明
**用户**：「生成 v2.0.0 的发布说明」
**AI**：运行 `--from v1.0.0 --to v2.0.0 --version 2.0.0` → 输出版本发布说明。
