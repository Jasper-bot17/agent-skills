# CI/CD 最佳实践指南

> 适用于 GitHub Actions 和 GitLab CI 的持续集成/持续部署最佳实践。

---

## 一、流水线设计原则

### 1.1 快速反馈

- CI 流水线应在 5-10 分钟内完成
- 将耗时较长的任务（如集成测试、部署）放在独立阶段
- 使用依赖缓存加速构建
- 合理使用矩阵构建，避免不必要的组合

### 1.2 失败优先

- 将最可能失败的步骤放在前面
- 代码检查（lint）在测试之前
- 快速测试在慢速测试之前
- 使用 `fail-fast: false` 在矩阵构建中运行所有组合

### 1.3 可重复性

- 固定依赖版本（使用 lock 文件）
- 固定 CI 镜像版本（不要使用 latest）
- 避免在 CI 中手动操作
- 所有配置文件纳入版本控制

### 1.4 安全性

- 不在配置文件中硬编码密钥
- 使用 Secrets/Variables 管理敏感信息
- 限制 Secrets 的使用范围（Protected/Masked）
- 定期轮换密钥
- 不在日志中输出敏感信息

---

## 二、GitHub Actions 最佳实践

### 2.1 工作流组织

```
.github/workflows/
├── ci.yml           # 构建和测试
├── lint.yml         # 代码检查
├── docker.yml       # Docker 构建
└── release.yml      # 发布
```

- 每个工作流专注一个职责
- 使用 `on` 精确控制触发条件
- 合理使用 `paths` 过滤，避免不必要的运行

### 2.2 触发条件

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'tests/**'
      - 'package.json'
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # 每周一凌晨2点
```

### 2.3 并发控制

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

- 同一分支的新提交会取消之前的运行
- 节省 CI 资源，加快反馈

### 2.4 依赖缓存

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

- 使用 `hashFiles` 生成精确的缓存键
- 提供 `restore-keys` 作为回退
- 缓存路径根据语言调整

### 2.5 矩阵构建

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    node-version: ['18', '20', '22']
    exclude:
      - os: windows-latest
        node-version: '18'
```

- 使用 `exclude` 排除不必要的组合
- `fail-fast: false` 确保所有组合都运行
- 注意矩阵组合数量，避免资源浪费

### 2.6 产物上传

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: |
      **/test-results/**
      **/coverage/**
    if-no-files-found: ignore
    retention-days: 7
```

- 使用 `if-no-files-found: ignore` 避免无文件时失败
- 设置合理的保留天数
- 产物名称应清晰描述内容

---

## 三、GitLab CI 最佳实践

### 3.1 阶段设计

```yaml
stages:
  - lint
  - build
  - test
  - deploy
```

- 阶段按执行顺序排列
- 同一阶段的任务并行执行
- 使用 `needs` 建立任务间依赖（DAG）

### 3.2 缓存配置

```yaml
cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/
  policy: pull-push
```

- 使用 `key.files` 基于 lock 文件生成缓存键
- `policy: pull` 用于只读任务（加速）
- `policy: pull-push` 用于需要更新缓存的任务

### 3.3 规则触发

```yaml
job:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_TAG
```

- 使用 `rules` 替代已废弃的 `only/except`
- 条件按顺序匹配，第一个匹配生效
- 可以组合多个条件

### 3.4 工件管理

```yaml
job:
  artifacts:
    name: "$CI_JOB_NAME-$CI_COMMIT_SHORT_SHA"
    paths:
      - build/
      - dist/
    expire_in: 1 week
    when: on_failure
```

- `expire_in` 设置自动过期时间
- `when: on_failure` 仅在失败时保留
- 工件名称包含作业名和提交 SHA

### 3.5 并行矩阵

```yaml
job:
  parallel:
    matrix:
      - VERSION: ['18', '20', '22']
  image: node:${VERSION}
```

- GitLab 13.3+ 支持 `parallel:matrix`
- 变量在作业中直接使用
- 可以组合多个变量维度

---

## 四、Docker 构建最佳实践

### 4.1 多阶段构建

```dockerfile
# 构建阶段
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- 最终镜像不包含构建工具
- 显著减小镜像体积
- 提高安全性

### 4.2 层缓存优化

```dockerfile
# 先复制依赖文件，利用缓存
COPY package*.json ./
RUN npm ci

# 再复制源代码
COPY . .
RUN npm run build
```

- 依赖文件变化频率低于源代码
- 利用 Docker 层缓存加速构建
- 按变化频率从低到高排列 COPY 指令

### 4.3 多架构构建

```yaml
- uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: user/app:latest
```

- 使用 Buildx 支持多架构
- 覆盖主流平台（AMD64、ARM64）
- 注意构建时间会增加

---

## 五、发布策略

### 5.1 语义化版本

- 版本号格式：`MAJOR.MINOR.PATCH`
- MAJOR：不兼容的 API 变更
- MINOR：向后兼容的功能新增
- PATCH：向后兼容的问题修复
- 预发布版本：`1.0.0-alpha.1`、`1.0.0-beta.2`

### 5.2 发布流程

1. 开发功能（feature 分支）
2. 代码审查（Pull Request / Merge Request）
3. CI 通过（构建、测试、lint）
4. 合并到主分支
5. 打标签（`git tag v1.0.0`）
6. 自动发布（CI 触发）
7. 生成发布说明
8. 通知用户

### 5.3 发布说明模板

```markdown
## [1.0.0] - 2024-01-15

### Added
- 新功能 A
- 新功能 B

### Changed
- 功能 C 的行为变更

### Fixed
- 修复 Bug #123
- 修复 Bug #456

### Removed
- 移除已废弃的功能 D

### BREAKING CHANGES
- API 接口 E 的参数变更
```

---

## 六、常见问题

| 问题 | 原因 | 解决方案 |
|---|---|---|
| CI 运行缓慢 | 未使用缓存、矩阵过大 | 配置依赖缓存、精简矩阵 |
| 缓存不生效 | 缓存键不正确 | 使用 hashFiles 生成精确键 |
| 密钥泄露 | 日志中输出敏感信息 | 使用 mask 功能、检查脚本 |
| 构建不可重复 | 依赖版本浮动 | 使用 lock 文件固定版本 |
| 测试不稳定 | 依赖外部服务、时序问题 | 使用 mock、增加重试 |
| 磁盘空间不足 | 产物未清理 | 配置过期时间、定期清理 |
| 权限不足 | GITHUB_TOKEN 权限不够 | 配置 permissions 字段 |
| 跨平台问题 | 路径分隔符、换行符 | 使用 path 模块、配置 .gitattributes |

---

*规范参考由 ci-cd-generator 技能提供*
