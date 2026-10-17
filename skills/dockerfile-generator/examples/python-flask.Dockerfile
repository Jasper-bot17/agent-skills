# Dockerfile for Python application
# Base image: python:3.12-slim

FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如需额外库请在此添加）
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 使用非 root 用户运行
RUN useradd -m -u 10001 appuser
USER appuser

EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
