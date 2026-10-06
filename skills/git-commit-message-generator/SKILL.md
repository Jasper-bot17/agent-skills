---
name: git-commit-message-generator
description: 'Git 提交信息生成助手。根据 git diff（暂存区/工作区/指定 commit）自动分析代码变更，生成符合 Conventional Commits 规范的提交信息，包含 type、scope、subject、body 和 footer。支持变更类型自动识别（feat/fix/refactor/docs/style/test/chore/ci/perf）、影响范围推断、破坏性变更标记，以及提交信息规范校验。适用于日常开发提交、PR 整理、开源项目贡献等场景。'
---

# Git 提交信息生成助手

## 一、技能定位

本技能用于**根据代码变更自动生成高质量、规范化的 Git 提交信息**。核心价值：

- 消除「写提交信息比写代码还难」的痛点
- 确保提交信息符合 Conventional Commits 规范，便于自动化生成 CHANGELOG 和语义化版本
- 从 diff 中提取关键变更点，避免提交信息过于笼统（如「update」「fix bug」）
- 支持批量整理（如将多个零散提交整理为规范的 PR 提交信息）

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户在 Git 仓库中做了修改，说「帮我写个 commit message」「生成提交信息」「这次改动怎么写提交说明」
2. 用户提供了 git diff 输出，要求生成提交信息
3. 用户说「帮我整理一下这次 PR 的提交记录」「把这些提交合并成一个规范的提交信息」
4. 用户的提交信息不规范，要求检查或修正
5. 用户说「按照 Conventional Commits 规范生成提交信息」
6. 用户需要生成 CHANGELOG 或语义化版本，需要规范的提交历史

## 三、输入要求

| 输入项 | 是否必需 | 说明 |
|---|---|---|
| Git 仓库或 diff 内容 | 必需 | 当前目录为 Git 仓库，或用户直接提供 diff 文本 |
| 变更范围（scope） | 可选 | 如未提供，从变更文件路径推断 |
| 提交类型（type） | 可选 | 如未提供，从变更内容自动识别 |
| 关联 issue/PR | 可选 | 用于 footer 中的引用（如 `Closes #123`） |
| 破坏性变更说明 | 可选 | 如有 API 变更、配置变更等，需在 footer 中标注 `BREAKING CHANGE` |

## 四、Conventional Commits 规范

提交信息格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 4.1 type（提交类型）

| type | 说明 | 典型变更 |
|---|---|---|
| `feat` | 新功能 | 新增 API、页面、功能模块 |
| `fix` | Bug 修复 | 修复崩溃、逻辑错误、边界问题 |
| `docs` | 文档变更 | README、注释、文档更新 |
| `style` | 代码格式（不影响功能） | 空格、分号、格式化、lint 修复 |
| `refactor` | 重构（既不修复 bug 也不添加功能） | 重命名、提取函数、结构调整 |
| `perf` | 性能优化 | 算法优化、缓存、减少查询 |
| `test` | 测试相关 | 新增测试、修改测试、测试框架 |
| `build` | 构建系统或外部依赖 | npm/pip 依赖、webpack、构建脚本 |
| `ci` | CI/CD 配置 | GitHub Actions、Jenkins、Dockerfile |
| `chore` | 杂项（不修改 src 或 test） | 配置文件、.gitignore、工具链 |
| `revert` | 回滚提交 | `revert: feat(xxx): ...` |

### 4.2 scope（影响范围）

- 通常是模块名、组件名或功能区域
- 从变更文件路径推断：如 `src/auth/` → `auth`，`components/Button/` → `button`
- 多模块变更时用最主要的模块，或省略 scope
- 示例：`feat(auth): 添加微信登录`、`fix(api): 修复用户接口空指针`

### 4.3 subject（简短描述）

- 祈使句开头（「添加」「修复」「重构」而非「添加了」「修复了」）
- 不超过 50 个字符（中文约 25 字）
- 句末不加句号
- 具体而非笼统：用「修复登录页验证码不刷新」而非「fix bug」

### 4.4 body（详细描述，可选）

- 说明「为什么」做这个变更，而非「怎么做」的
- 每行不超过 72 字符
- 与 subject 之间空一行
- 可包含背景、方案对比、影响范围

### 4.5 footer（页脚，可选）

- `BREAKING CHANGE: <描述>` — 破坏性变更
- `Closes #123` / `Fixes #456` — 关联 issue
- `Co-authored-by: 名字 <邮箱>` — 共同作者
- 与 body 之间空一行

## 五、操作步骤

### 步骤 1：获取代码变更

根据用户输入选择获取方式：

**方式 A：当前目录为 Git 仓库**
```bash
# 查看暂存区变更（推荐，因为 commit 的是暂存区内容）
git diff --cached

# 如果暂存区为空，查看工作区变更
git diff

# 查看最近一次提交的变更
git show HEAD
```

**方式 B：用户直接提供 diff 文本**
- 直接使用用户提供的内容

**方式 C：用户指定 commit 或分支**
```bash
git diff <base>..<head>
git show <commit-hash>
```

### 步骤 2：使用辅助脚本分析 diff（可选但推荐）

对于较大的 diff，使用 `scripts/analyze_diff.py` 进行结构化分析：

```bash
# 分析当前暂存区
git diff --cached | python3 scripts/analyze_diff.py

# 分析指定 diff 文件
python3 scripts/analyze_diff.py --input changes.diff

# 输出 JSON 格式（供后续处理）
python3 scripts/analyze_diff.py --input changes.diff --format json
```

脚本会输出：
- 变更文件列表（新增/修改/删除）
- 每个文件的变更统计（增删行数）
- 推断的变更类型（feat/fix/refactor 等）
- 推断的影响范围（scope）
- 关键变更点摘要（从新增/修改的代码行中提取）
- 是否包含破坏性变更的线索

### 步骤 3：AI 语义分析与提交信息生成

基于 diff 内容和脚本分析结果，进行以下判断：

#### 3.1 确定 type
- 新增函数/类/API/页面/功能 → `feat`
- 修改现有逻辑修复错误 → `fix`
- 仅修改文档/注释 → `docs`
- 仅修改格式（空格、分号、import 排序）→ `style`
- 重构代码结构但不改变行为 → `refactor`
- 优化性能（算法、缓存、查询）→ `perf`
- 新增/修改测试 → `test`
- 修改构建配置/依赖 → `build`
- 修改 CI 配置 → `ci`
- 杂项配置 → `chore`

**混合变更处理**：如果一次提交包含多种类型，选择最主要的类型；如果变更过于分散，建议用户拆分为多个提交。

#### 3.2 确定 scope
- 从变更最集中的目录/模块推断
- 前端项目：组件名、页面名
- 后端项目：模块名、服务名
- 全栈项目：`api`、`ui`、`db`、`config` 等
- 如果变更跨多个不相关模块，可省略 scope

#### 3.3 编写 subject
- 用一句话概括「这次提交做了什么」
- 祈使句，具体，不超过 50 字符
- 避免：「update」「fix」「changes」「misc」等无信息词汇
- 推荐：「添加用户头像上传功能」「修复订单列表分页越界」

#### 3.4 编写 body（如需要）
- 变更较复杂、有背景故事、有设计决策时才需要
- 说明「为什么」而非「怎么做」
- 可列出关键变更点（用 `-` 列表）

#### 3.5 编写 footer（如需要）
- 检测到 API 变更、配置变更、数据库迁移 → 添加 `BREAKING CHANGE`
- 用户提到关联 issue → 添加 `Closes #xxx`
- 破坏性变更描述需说明变更内容和迁移方案

### 步骤 4：质量自检

生成提交信息后，逐项检查：

- [ ] type 是否在规范列表中？
- [ ] subject 是否为祈使句？是否具体（而非「update code」）？
- [ ] subject 长度是否 ≤ 50 字符？
- [ ] scope 是否准确反映了变更模块？
- [ ] body 每行是否 ≤ 72 字符？
- [ ] 是否有破坏性变更未标注？
- [ ] 提交信息是否与实际 diff 内容一致？（禁止编造不存在的变更）
- [ ] 是否包含了不该出现在提交信息中的敏感信息（密码、token、内部链接）？

### 步骤 5：输出与交付

1. 输出生成的提交信息（代码块格式，方便复制）
2. 简要说明选择该 type/scope 的理由
3. 如检测到问题（如变更过于分散建议拆分、有未提交的敏感信息），主动提醒
4. 如用户需要，可直接执行 `git commit` 命令（需用户确认）

## 六、输出格式

### 标准提交信息

```
feat(auth): 添加微信扫码登录功能

- 新增 WeChatAuthService 处理微信 OAuth 流程
- 登录页添加扫码登录入口，支持二维码轮询状态
- 用户表新增 wechat_openid 字段，兼容已有账号绑定

Closes #42
```

### 破坏性变更提交信息

```
refactor(api): 重构用户接口返回格式

将 /api/users 接口返回从数组改为分页对象，
包含 total、page、pageSize 和 data 字段。

BREAKING CHANGE: /api/users 接口返回格式变更，
前端需适配新的分页结构。旧格式将在 v2.0 移除。
```

### 简单提交信息（无需 body）

```
fix(order): 修复订单金额计算精度丢失
```

## 七、常见场景处理

### 场景 1：变更过于分散
如果 diff 涉及 5 个以上不相关模块，提醒用户：
> 本次变更涉及多个不相关模块（auth、order、payment、docs），建议拆分为多个提交：
> 1. `feat(auth): ...`
> 2. `fix(order): ...`
> 3. `docs: ...`

### 场景 2：仅格式化变更
如果 diff 全是空格、换行、import 排序：
```
style: 统一代码格式（prettier 自动格式化）
```

### 场景 3：依赖升级
```
build(deps): 升级 react 至 18.2.0

- 升级 react 和 react-dom 至 18.2.0
- 适配 createRoot 新 API
- 移除已废弃的 ReactDOM.render 调用
```

### 场景 4：回滚提交
```
revert: feat(auth): 添加微信扫码登录功能

该功能导致登录页白屏，临时回滚。
此提交回滚了 abc1234。
```

### 场景 5：修复线上紧急 bug
```
fix(payment): 修复支付回调重复通知导致的订单状态错误

支付回调在网络重试时会重复触发，导致订单状态
从「已支付」回退为「处理中」。添加幂等校验，
已支付订单忽略重复回调。

Closes #156
```

## 八、注意事项

1. **不编造变更**：提交信息必须严格基于实际 diff 内容，不得添加不存在的功能或修复。
2. **敏感信息检查**：如果 diff 中包含密码、API key、token 等敏感信息，提醒用户不要提交，并建议使用环境变量或 secrets 管理。
3. **中文/英文一致性**：根据项目已有提交历史的语言风格选择语言；新项目默认与用户输入语言一致。
4. **大文件检查**：如果 diff 中包含大文件（>10MB）或二进制文件，提醒用户考虑使用 Git LFS 或不要提交。
5. **提交粒度建议**：如果一次变更包含多个独立功能，建议拆分为多个提交，便于 code review 和回滚。
6. **scope 命名一致性**：参考项目已有提交中使用的 scope 命名，保持一致。
7. **不自动执行 commit**：生成提交信息后，需用户确认后才可执行 `git commit`，不得自动提交。

## 九、文件结构

```
git-commit-message-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── commit-message-template.md        # 提交信息模板（含各 type 示例）
├── scripts/
│   └── analyze_diff.py                   # Git diff 分析脚本（变更统计、类型推断、关键变更提取）
└── examples/
    ├── sample-feature.diff               # 示例：新功能 diff
    ├── sample-bugfix.diff                # 示例：bug 修复 diff
    └── sample-commit-messages.md         # 示例：生成的提交信息
```

## 十、使用示例

### 示例 1：日常开发提交
**用户**：（在 Git 仓库中）「帮我写个 commit message」
**处理**：执行 `git diff --cached` 获取变更 → 分析 diff → 生成提交信息 → 输出。

### 示例 2：提供 diff 文本
**用户**：粘贴一段 diff，说「根据这个生成提交信息」
**处理**：直接分析用户提供的 diff → 生成提交信息。

### 示例 3：PR 提交整理
**用户**：「帮我把这个 PR 的 10 个提交整理成一个规范的提交信息」
**处理**：执行 `git log <base>..<head>` 获取所有提交 → 合并分析 → 生成一个汇总的提交信息。

### 示例 4：提交信息校验
**用户**：「帮我看看这个提交信息合不合规：`update stuff`」
**处理**：检查 type 是否缺失、subject 是否笼统 → 给出修正建议和改进后的提交信息。
