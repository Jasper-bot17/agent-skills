---
name: ci-cd-generator
description: 'CI/CD 流水线生成助手。一键生成 GitHub Actions 和 GitLab CI 配置文件，支持多种流水线场景（构建测试、代码检查、Docker 构建推送、发布部署），覆盖 Python/Node.js/Go/Rust/C++/Java 六种语言，内置矩阵构建、依赖缓存、密钥管理、分支触发、并发控制等最佳实践。适用于快速为项目搭建持续集成/持续部署流水线、CI 配置审查与优化、多平台 CI 配置迁移等场景。'
---

# CI/CD 流水线生成助手

## 一、技能定位

本技能用于**快速生成标准 CI/CD 流水线配置文件**。核心价值：

- 支持两种 CI 平台：GitHub Actions、GitLab CI
- 支持四种流水线场景：构建测试、代码检查、Docker 构建推送、发布部署
- 支持六种编程语言：Python、Node.js、Go、Rust、C++、Java
- 内置依赖缓存配置（pip、npm、go modules、cargo、maven、ccache）
- 支持矩阵构建（多版本/多平台）
- 支持分支触发、标签触发、PR 触发
- 支持密钥管理（Secrets）
- 支持并发控制与取消冗余运行
- 生成状态徽章 Markdown

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「创建 CI/CD 流水线」「配置 GitHub Actions」「生成 GitLab CI」
2. 用户说「给项目加自动化测试」「配置持续集成」
3. 用户说「Docker 自动构建推送」「配置镜像构建」
4. 用户说「自动发布」「配置部署流水线」「CD 配置」
5. 用户说「代码检查自动化」「lint CI 配置」
6. 用户说「多版本测试矩阵」「多平台 CI」
7. 用户说「从 GitHub Actions 迁移到 GitLab CI」或反向迁移

## 三、流水线场景说明

### 3.1 构建测试（build-test）

最常用的流水线场景，在每次提交或 PR 时自动构建并运行测试。

包含步骤：
1. 检出代码
2. 配置语言环境
3. 缓存依赖
4. 安装依赖
5. 构建项目
6. 运行测试
7. 上传测试报告（可选）

### 3.2 代码检查（lint）

在构建测试基础上增加代码质量检查。

包含步骤：
1. 检出代码
2. 配置语言环境
3. 安装 lint 工具
4. 运行代码格式化检查
5. 运行静态分析
6. 运行类型检查（如适用）

### 3.3 Docker 构建推送（docker）

自动构建 Docker 镜像并推送到镜像仓库。

包含步骤：
1. 检出代码
2. 设置 Docker Buildx
3. 登录镜像仓库（Docker Hub / GHCR / 自定义）
4. 构建镜像（多架构支持）
5. 推送镜像
6. 生成镜像摘要

### 3.4 发布部署（release）

在标签推送时自动发布版本并部署。

包含步骤：
1. 检出代码
2. 配置语言环境
3. 构建项目
4. 生成发布说明
5. 创建 GitHub Release / GitLab Release
6. 上传构建产物
7. 部署到目标环境（SSH / 云平台）

## 四、操作步骤

### 步骤 1：确认需求

确认用户需要：
- CI 平台（GitHub Actions / GitLab CI）
- 流水线场景（build-test / lint / docker / release）
- 编程语言（python / nodejs / go / rust / cpp / java）
- 输出目录

### 步骤 2：运行脚本

使用 `scripts/generate_ci_cd.py`：

```bash
# 基本用法（GitHub Actions，构建测试，Python）
python3 scripts/generate_ci_cd.py --platform github --scenario build-test --language python

# GitLab CI，代码检查，Node.js
python3 scripts/generate_ci_cd.py --platform gitlab --scenario lint --language nodejs

# Docker 构建推送
python3 scripts/generate_ci_cd.py --platform github --scenario docker --language python

# 发布部署
python3 scripts/generate_ci_cd.py --platform github --scenario release --language python

# 指定语言版本
python3 scripts/generate_ci_cd.py --platform github --scenario build-test --language python --versions "3.10,3.11,3.12"

# 启用矩阵构建
python3 scripts/generate_ci_cd.py --platform github --scenario build-test --language python --matrix

# 指定输出目录
python3 scripts/generate_ci_cd.py --platform github --scenario build-test --language python --output /path/to/project

# 生成所有场景
python3 scripts/generate_ci_cd.py --platform github --language python --all
```

### 步骤 3：配置密钥（如需要）

对于 Docker 推送和发布场景，需要在 CI 平台配置密钥：

**GitHub Actions**：Settings → Secrets and variables → Actions
- `DOCKER_USERNAME` / `DOCKER_PASSWORD`（Docker Hub）
- `GHCR_TOKEN`（GitHub Container Registry，使用 GITHUB_TOKEN 即可）
- `DEPLOY_SSH_KEY`（SSH 部署密钥）

**GitLab CI**：Settings → CI/CD → Variables
- 同上，配置为 Protected / Masked 变量

### 步骤 4：安全提示

1. 本技能只生成配置文件，不执行 CI/CD 流水线
2. 生成的配置为通用模板，复杂项目可能需要手动调整
3. Docker 推送和部署场景需要配置密钥，不要在配置文件中硬编码密码
4. 建议先在测试分支验证流水线，再合并到主分支
5. 矩阵构建会增加 CI 运行时间和成本，根据需要启用

## 五、GitHub Actions 配置说明

### 5.1 基本结构

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
      - run: pip install -r requirements.txt
      - run: pytest
```

### 5.2 矩阵构建

```yaml
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

### 5.3 并发控制

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### 5.4 Docker 构建推送

```yaml
jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: user/app:latest
```

## 六、GitLab CI 配置说明

### 6.1 基本结构

```yaml
stages:
  - build
  - test

build:
  stage: build
  image: python:3.12
  script:
    - pip install -r requirements.txt
    - python -m compileall .

test:
  stage: test
  image: python:3.12
  script:
    - pip install -r requirements.txt
    - pytest
  cache:
    paths:
      - .cache/pip
```

### 6.2 矩阵构建（parallel）

```yaml
test:
  parallel:
    matrix:
      - PYTHON_VERSION: ['3.10', '3.11', '3.12']
  image: python:${PYTHON_VERSION}
  script:
    - pytest
```

### 6.3 规则触发

```yaml
job:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### 6.4 Docker 构建

```yaml
docker:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $DOCKER_USER -p $DOCKER_PASSWORD
    - docker build -t user/app:$CI_COMMIT_SHORT_SHA .
    - docker push user/app:$CI_COMMIT_SHORT_SHA
```

## 七、常见场景处理

### 场景 1：Python 项目 CI
**用户**：「给我的 Python 项目加 GitHub Actions 测试」
**处理**：生成 build-test 场景，Python 语言，含 pip 缓存、pytest 测试。

### 场景 2：Node.js 项目 lint
**用户**：「配置 Node.js 项目的代码检查 CI」
**处理**：生成 lint 场景，Node.js 语言，含 npm 缓存、ESLint、Prettier 检查。

### 场景 3：Go 项目多版本测试
**用户**：「Go 项目需要多版本矩阵测试」
**处理**：生成 build-test 场景，Go 语言，启用矩阵，含 go mod 缓存。

### 场景 4：Docker 镜像自动构建
**用户**：「配置 Docker 镜像自动构建推送到 Docker Hub」
**处理**：生成 docker 场景，含 Buildx、多架构构建、Docker Hub 登录推送。

### 场景 5：自动发布
**用户**：「打标签时自动发布版本」
**处理**：生成 release 场景，含标签触发、构建、创建 Release、上传产物。

### 场景 6：C++ 项目 CI
**用户**：「给 C++ 项目配置 CI」
**处理**：生成 build-test 场景，C++ 语言，含 CMake 构建、ccache 缓存、CTest 测试。

## 八、注意事项

1. **平台选择**：GitHub Actions 生成 `.github/workflows/ci.yml`，GitLab CI 生成 `.gitlab-ci.yml`。
2. **语言版本**：默认使用当前 LTS 版本，可通过 `--versions` 指定多个版本。
3. **矩阵构建**：启用 `--matrix` 会生成多版本/多平台矩阵，增加 CI 运行时间。
4. **依赖缓存**：自动配置各语言的依赖缓存，加速后续运行。
5. **密钥管理**：Docker 推送和部署需要配置 Secrets，配置文件中使用变量引用。
6. **分支触发**：默认在 main 分支推送和 PR 时触发，可根据需要修改。
7. **并发控制**：默认启用并发控制，同一分支的新提交会取消之前的运行。
8. **测试报告**：自动配置测试报告上传（如适用），方便在 CI 界面查看。
9. **不修改系统**：本技能只在指定目录生成配置文件，不修改系统配置。
10. **手动调整**：复杂项目（多服务、自定义部署流程）可能需要手动修改生成的配置。

## 九、文件结构

```
ci-cd-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── ci-cd-best-practices.md           # CI/CD 最佳实践指南
├── scripts/
│   └── generate_ci_cd.py                  # CI/CD 配置生成脚本
└── examples/
    ├── github-python-build-test.yml       # 示例：GitHub Actions Python 构建测试
    ├── github-nodejs-lint.yml             # 示例：GitHub Actions Node.js 代码检查
    ├── github-docker.yml                  # 示例：GitHub Actions Docker 构建推送
    ├── gitlab-python-build-test.yml       # 示例：GitLab CI Python 构建测试
    └── sample-badge.md                    # 示例：状态徽章
```

## 十、使用示例

### 示例 1：快速创建
**用户**：「给我的 Python 项目加 GitHub Actions」
**AI**：运行 `--platform github --scenario build-test --language python` → 生成 `.github/workflows/ci.yml`。

### 示例 2：Docker 构建
**用户**：「配置 Docker 镜像自动构建推送」
**AI**：运行 `--platform github --scenario docker` → 生成 Docker 构建推送工作流，提示配置 DOCKER_USERNAME/DOCKER_PASSWORD。

### 示例 3：多平台 CI
**用户**：「同时生成 GitHub Actions 和 GitLab CI」
**AI**：分别运行两次，指定不同 `--platform`。
