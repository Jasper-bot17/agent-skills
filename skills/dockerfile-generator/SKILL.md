---
name: dockerfile-generator
description: 'Dockerfile 生成助手。根据项目语言和框架，自动生成优化的 Dockerfile 和 .dockerignore 文件。支持 8 种编程语言（Python、Node.js、Go、Java、C++、Rust、PHP、Ruby），支持多阶段构建（multi-stage build）、多种基础镜像（slim/alpine/distroless）、健康检查、非 root 用户运行、端口暴露、环境变量配置。自动应用 Docker 最佳实践，生成镜像体积优化建议。适用于容器化部署、CI/CD 流水线、本地开发环境搭建等场景。纯 Python 标准库，无外部依赖。'
---

# Dockerfile 生成助手

## 一、技能定位

本技能用于**根据项目语言和配置自动生成专业的 Dockerfile 和 .dockerignore**。核心价值：

- **多语言支持**：Python、Node.js、Go、Java、C++、Rust、PHP、Ruby 共 8 种语言
- **多阶段构建**：自动生成 builder + runtime 两阶段构建，显著减小最终镜像体积
- **镜像优化**：支持 slim / alpine / distroless 三种基础镜像策略
- **安全最佳实践**：自动创建非 root 用户、设置健康检查、最小化攻击面
- **.dockerignore**：自动生成对应的 .dockerignore 文件，减少构建上下文
- **可配置**：支持自定义端口、环境变量、启动命令、工作目录等
- **纯标准库**：无外部依赖，开箱即用

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我写 Dockerfile」「生成 Dockerfile」「容器化这个项目」
2. 用户说「Docker 镜像优化」「减小镜像体积」「多阶段构建」
3. 用户说「把这个项目 Docker 化」「创建 Docker 配置」
4. 用户说「Python/Node/Go/Java 项目怎么写 Dockerfile」
5. 用户说「生成 .dockerignore」「Docker 构建上下文优化」
6. 用户说「CI/CD 里的 Docker 构建」「Docker 镜像最佳实践」
7. 用户提供项目代码或项目结构，要求生成 Docker 配置
8. 用户说「健康检查」「非 root 运行」「Docker 安全配置」

## 三、支持的语言和默认配置

| 语言 | 默认基础镜像 | 包管理器 | 默认端口 | 构建工具 |
|---|---|---|---|---|
| Python | python:3.12-slim | pip | 8000 | - |
| Node.js | node:20-alpine | npm | 3000 | - |
| Go | golang:1.22-alpine | go mod | 8080 | go build |
| Java | eclipse-temurin:17-jdk | maven/gradle | 8080 | mvn/gradle |
| C++ | gcc:13 | cmake/make | - | g++/cmake |
| Rust | rust:1.77-slim | cargo | 8080 | cargo build |
| PHP | php:8.3-apache | composer | 80 | - |
| Ruby | ruby:3.3-slim | bundler | 3000 | - |

## 四、操作步骤

### 步骤 1：确认项目信息

向用户确认以下信息（用户可提供全部或部分，未提供时使用合理默认值）：
- **编程语言**：Python / Node.js / Go / Java / C++ / Rust / PHP / Ruby
- **框架**（可选）：如 Flask、Django、Express、Spring Boot 等
- **应用入口**：如 app.py、index.js、main.go
- **暴露端口**：如 8000、3000、8080
- **环境变量**（可选）：如 NODE_ENV=production
- **构建类型**：简单构建 或 多阶段构建（默认多阶段）
- **镜像策略**：slim / alpine / distroless（默认 slim 或 alpine）

### 步骤 2：运行生成脚本

```bash
# 基本用法：生成 Python 项目的 Dockerfile
python3 scripts/generate_dockerfile.py --lang python

# 指定端口和入口文件
python3 scripts/generate_dockerfile.py --lang node --port 3000 --entry server.js

# 多阶段构建（Go 项目）
python3 scripts/generate_dockerfile.py --lang go --multi-stage --entry main.go

# alpine 镜像策略
python3 scripts/generate_dockerfile.py --lang python --base alpine

# 指定输出目录
python3 scripts/generate_dockerfile.py --lang java --output ./myproject

# 同时生成 .dockerignore（默认开启）
python3 scripts/generate_dockerfile.py --lang python --dockerignore

# 自定义环境变量
python3 scripts/generate_dockerfile.py --lang node --env "NODE_ENV=production" --env "PORT=3000"

# 健康检查
python3 scripts/generate_dockerfile.py --lang python --healthcheck --health-url /health
```

### 步骤 3：验证和调整

- 检查生成的 Dockerfile 是否符合项目实际结构
- 确认入口文件路径和包管理器命令正确
- 如项目有特殊依赖（如系统库），在 Dockerfile 中补充 apt-get/apk 安装
- 本地测试构建：`docker build -t myapp .`
- 测试运行：`docker run -p 8000:8000 myapp`

### 步骤 4：输出交付

- Dockerfile：项目根目录
- .dockerignore：项目根目录
- 构建和运行命令说明

## 五、命令行参数

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--lang` / `-l` | 编程语言：python/node/go/java/cpp/rust/php/ruby | 必填 |
| `--entry` / `-e` | 应用入口文件 | 按语言默认 |
| `--port` / `-p` | 暴露端口 | 按语言默认 |
| `--output` / `-o` | 输出目录 | 当前目录 |
| `--base` / `-b` | 基础镜像策略：slim/alpine/distroless | 按语言默认 |
| `--multi-stage` / `-m` | 启用多阶段构建 | 开启（编译型语言默认） |
| `--no-multi-stage` | 禁用多阶段构建 | - |
| `--dockerignore` / `-d` | 生成 .dockerignore | 开启 |
| `--no-dockerignore` | 不生成 .dockerignore | - |
| `--healthcheck` | 添加健康检查 | 关闭 |
| `--health-url` | 健康检查 URL 路径 | /health |
| `--health-interval` | 健康检查间隔 | 30s |
| `--env` | 环境变量（可多次使用） | - |
| `--workdir` | 工作目录 | /app |
| `--non-root` | 使用非 root 用户运行 | 开启 |
| `--no-non-root` | 使用 root 用户运行 | - |
| `--framework` | 框架名称（影响默认配置） | - |

## 六、生成的 Dockerfile 结构说明

### 多阶段构建示例（Go 项目）

```dockerfile
# ===== 构建阶段 =====
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/server .

# ===== 运行阶段 =====
FROM alpine:3.19
RUN apk add --no-cache ca-certificates tzdata
WORKDIR /app
COPY --from=builder /app/server .
RUN adduser -D -u 10001 appuser
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/health || exit 1
ENTRYPOINT ["./server"]
```

### 关键优化点

1. **依赖层缓存**：先复制依赖文件（go.mod/package.json/requirements.txt），再复制源码
2. **多阶段构建**：编译工具链不进入最终镜像
3. **非 root 用户**：创建专用用户运行应用
4. **.dockerignore**：排除 node_modules、.git、__pycache__ 等
5. **健康检查**：自动添加 HEALTHCHECK 指令
6. **最小化层**：合并 RUN 指令，清理包管理器缓存

## 七、常见场景处理

### 场景 1：Python Flask 项目
**用户**：「帮我写个 Flask 项目的 Dockerfile」
**处理**：`--lang python --entry app.py --port 5000`，使用 gunicorn 作为生产服务器。

### 场景 2：Node.js Express 项目
**用户**：「Node 项目怎么 Docker 化」
**处理**：`--lang node --entry server.js --port 3000 --base alpine`，npm ci 替代 npm install。

### 场景 3：Go 微服务
**用户**：「生成 Go 项目的多阶段构建 Dockerfile」
**处理**：`--lang go --multi-stage --entry main.go --healthcheck`，distroless 最终镜像。

### 场景 4：Java Spring Boot
**用户**：「Spring Boot 项目 Docker 配置」
**处理**：`--lang java --entry target/app.jar --port 8080 --multi-stage`，Maven 构建 + JRE 运行。

### 场景 5：C++ 项目
**用户**：「C++ 项目怎么写 Dockerfile」
**处理**：`--lang cpp --entry main.cpp`，使用 cmake 构建，gcc 镜像。

### 场景 6：已有 Dockerfile 优化
**用户**：「我的镜像太大了，帮我优化」
**处理**：分析现有 Dockerfile，建议改用多阶段构建、alpine/distroless 基础镜像、合并层、清理缓存。

## 八、注意事项

1. **入口文件**：生成的 Dockerfile 使用默认入口，用户需根据实际项目调整
2. **系统依赖**：如项目需要特定系统库（如 libxml2、opencv），需手动添加到 apt-get/apk
3. **私有依赖**：私有 npm/pip 仓库需要配置认证，脚本不包含密钥
4. **架构兼容**：Apple Silicon (ARM64) 构建时需注意基础镜像架构支持
5. **健康检查**：需要应用实际提供健康检查端点，否则 HEALTHCHECK 会持续失败
6. **非 root 用户**：如应用需要绑定 1024 以下端口，需调整或使用 root
7. **构建上下文**：.dockerignore 排除了常见无关文件，特殊项目需手动调整
8. **不执行构建**：本技能只生成配置文件，不执行 docker build

## 九、文件结构

```
dockerfile-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── dockerfile-best-practices.md      # Dockerfile 最佳实践指南
├── scripts/
│   └── generate_dockerfile.py            # Dockerfile 生成脚本
└── examples/
    ├── python-flask.Dockerfile           # Python Flask 示例
    ├── node-express.Dockerfile           # Node.js Express 示例
    ├── go-service.Dockerfile             # Go 微服务示例（多阶段）
    └── sample.dockerignore               # .dockerignore 示例
```

## 十、使用示例

### 示例 1：快速生成 Python Dockerfile
**用户**：「我有个 Python 项目，帮我生成 Dockerfile」
**AI**：运行 `--lang python --port 8000` → 生成 Dockerfile + .dockerignore，告知构建和运行命令。

### 示例 2：Go 多阶段构建 + 健康检查
**用户**：「Go 项目，要多阶段构建和健康检查」
**AI**：运行 `--lang go --multi-stage --healthcheck --health-url /healthz` → 生成优化的两阶段 Dockerfile。

### 示例 3：Node.js alpine 镜像
**用户**：「Node 项目，用 alpine 镜像，端口 4000」
**AI**：运行 `--lang node --base alpine --port 4000` → 生成轻量级 Dockerfile。
