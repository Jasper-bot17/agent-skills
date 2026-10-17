# Dockerfile for Node.js application
# Base image: node:20-alpine

FROM node:20-alpine

# 设置工作目录
WORKDIR /app

# 环境变量
ENV NODE_ENV=production

# 先复制依赖文件，利用 Docker 层缓存
COPY package*.json ./
RUN npm ci --only=production || npm install --production

# 复制应用代码
COPY . .

# 使用非 root 用户运行
RUN adduser -D -u 10001 appuser
USER appuser

EXPOSE 3000

# 启动命令
CMD ["node", "index.js"]
