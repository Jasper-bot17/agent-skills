# Dockerfile 最佳实践指南

> dockerfile-generator 技能配套指南，帮助写出高质量的 Dockerfile。

---

## 一、镜像体积优化

### 1. 选择合适的基础镜像

| 镜像类型 | 大小 | 适用场景 |
|---|---|---|
| `*-slim` | 中等 | 大多数应用，兼容性好 |
| `*-alpine` | 小（~5MB） | 追求最小体积，注意 musl libc 兼容性 |
| `distroless` | 极小 | 生产环境，无 shell，安全性最高 |
| `*-debian` | 大 | 需要完整工具链的构建阶段 |

### 2. 多阶段构建（Multi-stage Build）

```dockerfile
# 构建阶段：包含完整工具链
FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o app .

# 运行阶段：只包含运行时
FROM alpine:3.19
COPY --from=builder /build/app .
CMD ["./app"]
```

**效果**：Go 镜像从 ~300MB 降到 ~15MB。

### 3. 利用层缓存

- 把变化频率低的指令放前面（如依赖安装）
- 把变化频率高的指令放后面（如复制源码）
- 先复制依赖文件，再复制全部源码

```dockerfile
# ✅ 好：依赖层可缓存
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# ❌ 差：每次代码变更都重新安装依赖
COPY . .
RUN npm ci
```

### 4. 合并 RUN 指令

```dockerfile
# ✅ 好：一次 RUN，清理缓存
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# ❌ 差：多层，缓存未清理
RUN apt-get update
RUN apt-get install -y gcc
```

---

## 二、安全最佳实践

### 1. 使用非 root 用户

```dockerfile
RUN useradd -m -u 10001 appuser
USER appuser
```

### 2. 健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

### 3. 最小化攻击面

- 使用 distroless 镜像（无 shell、无包管理器）
- 不安装不必要的工具
- 不在镜像中包含源码和构建工具

### 4. 不要在镜像中存储密钥

```dockerfile
# ❌ 禁止：硬编码密钥
ENV API_KEY=secret123

# ✅ 好：运行时注入
ENV API_KEY=
# 运行时：docker run -e API_KEY=xxx myapp
```

---

## 三、各语言优化要点

### Python
- 使用 `--no-cache-dir` 安装 pip 包
- 多阶段构建中用 venv 复制依赖
- 生产环境用 gunicorn/uwsgi，不用开发服务器

### Node.js
- 使用 `npm ci` 替代 `npm install`（确定性安装）
- `--only=production` 排除开发依赖
- 使用 `.dockerignore` 排除 node_modules

### Go
- `CGO_ENABLED=0` 静态编译
- `-ldflags="-s -w"` 去除调试信息
- distroless/static 作为运行镜像

### Java
- JRE 镜像替代 JDK 镜像
- `-XX:+UseContainerSupport` 支持容器内存限制
- `-XX:MaxRAMPercentage=75.0` 合理设置堆内存

### C++
- 静态编译 `-static`
-  strip 去除符号表
- 使用 distroless/base 运行

---

## 四、.dockerignore 重要性

.dockerignore 减少构建上下文大小，加快构建速度：

```
# 版本控制
.git
.gitignore

# 依赖目录
node_modules
vendor
__pycache__
.venv

# 构建产物
dist
build
target
*.jar
*.exe

# IDE
.idea
.vscode
*.swp

# 环境
.env
*.log

# Docker 自身
Dockerfile
.dockerignore
```

---

## 五、常见错误

| 错误 | 后果 | 修复 |
|---|---|---|
| `COPY . .` 在依赖安装前 | 缓存失效，每次重装依赖 | 先复制依赖文件 |
| 不清理 apt 缓存 | 镜像体积增大 | `rm -rf /var/lib/apt/lists/*` |
| root 用户运行 | 安全风险 | 创建非 root 用户 |
| 每次构建 `apt-get update` | 层缓存失效 | 合并 update 和 install |
| 包含 node_modules | 上下文巨大 | .dockerignore 排除 |
| 健康检查指向不存在的端点 | 容器一直 unhealthy | 确保应用提供该端点 |
| `latest` 标签 | 不可复现构建 | 使用具体版本号 |

---

## 六、构建和调试命令

```bash
# 构建
docker build -t myapp .

# 不使用缓存构建（调试用）
docker build --no-cache -t myapp .

# 查看镜像大小
docker images myapp

# 查看镜像层历史
docker history myapp

# 运行并进入 shell（调试）
docker run -it --entrypoint sh myapp

# 查看镜像中文件
docker run --rm myapp ls -la /app

# 多平台构建（需 buildx）
docker buildx build --platform linux/amd64,linux/arm64 -t myapp .
```

---

*本指南由 dockerfile-generator 技能提供，配合 generate_dockerfile.py 脚本使用*
