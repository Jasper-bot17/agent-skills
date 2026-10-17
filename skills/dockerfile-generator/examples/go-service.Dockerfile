# Dockerfile for Go application
# Multi-stage build | Runtime: alpine:3.19

# ===== 构建阶段 =====
FROM golang:1.22-alpine AS builder
WORKDIR /build

# 先复制依赖文件，利用缓存
COPY go.mod go.sum ./
RUN go mod download

# 复制源码并编译
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /build/app .

# ===== 运行阶段 =====
FROM alpine:3.19

# 安装运行时依赖
RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

# 从构建阶段复制二进制文件
COPY --from=builder /build/app .

# 使用非 root 用户运行
RUN adduser -D -u 10001 appuser
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/healthz || exit 1

# 启动命令
ENTRYPOINT ["./app"]
