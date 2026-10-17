#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Dockerfile 生成脚本

功能：
- 支持 8 种编程语言：Python, Node.js, Go, Java, C++, Rust, PHP, Ruby
- 支持多阶段构建（multi-stage build）
- 支持 slim / alpine / distroless 基础镜像策略
- 自动生成 .dockerignore
- 支持健康检查、非 root 用户、环境变量配置
- 纯 Python 标准库，无外部依赖

用法：
  python3 generate_dockerfile.py --lang python
  python3 generate_dockerfile.py --lang go --multi-stage --healthcheck
  python3 generate_dockerfile.py --lang node --port 3000 --base alpine --output ./project
"""

import argparse
import os
import sys


# ============================================================
# 语言配置
# ============================================================

LANG_CONFIG = {
    "python": {
        "display_name": "Python",
        "default_entry": "app.py",
        "default_port": 8000,
        "default_base": "slim",
        "builder_image": "python:3.12-slim",
        "runtime_images": {
            "slim": "python:3.12-slim",
            "alpine": "python:3.12-alpine",
            "distroless": "gcr.io/distroless/python3-debian12",
        },
        "dep_files": ["requirements.txt", "pyproject.toml", "Pipfile"],
        "dockerignore": [
            "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
            "*.egg-info", ".eggs", "dist", "build", ".venv", "venv",
            "env", ".env", ".git", ".gitignore", "*.md", "Dockerfile",
            ".dockerignore", "tests", "test", ".pytest_cache", ".mypy_cache",
            ".coverage", "htmlcov", "*.log", ".idea", ".vscode", "*.swp",
        ],
    },
    "node": {
        "display_name": "Node.js",
        "default_entry": "index.js",
        "default_port": 3000,
        "default_base": "alpine",
        "builder_image": "node:20-alpine",
        "runtime_images": {
            "slim": "node:20-slim",
            "alpine": "node:20-alpine",
            "distroless": "gcr.io/distroless/nodejs20-debian12",
        },
        "dep_files": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
        "dockerignore": [
            "node_modules", "npm-debug.log", "yarn-debug.log", "yarn-error.log",
            ".git", ".gitignore", "*.md", "Dockerfile", ".dockerignore",
            ".env", ".env.local", "dist", "build", "coverage", ".nyc_output",
            ".idea", ".vscode", "*.swp", "*.log", "test", "tests",
            ".npm", ".cache",
        ],
    },
    "go": {
        "display_name": "Go",
        "default_entry": "main.go",
        "default_port": 8080,
        "default_base": "alpine",
        "builder_image": "golang:1.22-alpine",
        "runtime_images": {
            "slim": "debian:bookworm-slim",
            "alpine": "alpine:3.19",
            "distroless": "gcr.io/distroless/static-debian12",
        },
        "dep_files": ["go.mod", "go.sum"],
        "dockerignore": [
            "*.exe", "*.exe~", "*.dll", "*.so", "*.dylib", "*.test",
            "*.out", "vendor", ".git", ".gitignore", "*.md", "Dockerfile",
            ".dockerignore", ".env", "bin", "dist", "build", ".idea",
            ".vscode", "*.swp", "*.log",
        ],
    },
    "java": {
        "display_name": "Java",
        "default_entry": "target/app.jar",
        "default_port": 8080,
        "default_base": "slim",
        "builder_image": "maven:3.9-eclipse-temurin-17",
        "runtime_images": {
            "slim": "eclipse-temurin:17-jre-slim",
            "alpine": "eclipse-temurin:17-jre-alpine",
            "distroless": "gcr.io/distroless/java17-debian12",
        },
        "dep_files": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "dockerignore": [
            "target", "build", ".gradle", ".mvn", ".git", ".gitignore",
            "*.md", "Dockerfile", ".dockerignore", ".env", "*.class",
            "*.jar", "*.war", ".idea", ".vscode", "*.swp", "*.log",
            "src/test",
        ],
    },
    "cpp": {
        "display_name": "C++",
        "default_entry": "main.cpp",
        "default_port": None,
        "default_base": "slim",
        "builder_image": "gcc:13",
        "runtime_images": {
            "slim": "debian:bookworm-slim",
            "alpine": "alpine:3.19",
            "distroless": "gcr.io/distroless/base-debian12",
        },
        "dep_files": ["CMakeLists.txt", "Makefile", "vcpkg.json", "conanfile.txt"],
        "dockerignore": [
            "build", "cmake-build-*", "*.o", "*.obj", "*.a", "*.so",
            "*.dylib", "*.dll", "*.exe", "CMakeCache.txt", "CMakeFiles",
            "cmake_install.cmake", "install_manifest.txt", ".git",
            ".gitignore", "*.md", "Dockerfile", ".dockerignore", ".env",
            ".idea", ".vscode", "*.swp", "*.log", "bin", "lib",
        ],
    },
    "rust": {
        "display_name": "Rust",
        "default_entry": "src/main.rs",
        "default_port": 8080,
        "default_base": "slim",
        "builder_image": "rust:1.77-slim",
        "runtime_images": {
            "slim": "debian:bookworm-slim",
            "alpine": "alpine:3.19",
            "distroless": "gcr.io/distroless/static-debian12",
        },
        "dep_files": ["Cargo.toml", "Cargo.lock"],
        "dockerignore": [
            "target", "*.rs.bk", ".git", ".gitignore", "*.md", "Dockerfile",
            ".dockerignore", ".env", "bin", "dist", "build", ".idea",
            ".vscode", "*.swp", "*.log", "tests",
        ],
    },
    "php": {
        "display_name": "PHP",
        "default_entry": "index.php",
        "default_port": 80,
        "default_base": "slim",
        "builder_image": "php:8.3-apache",
        "runtime_images": {
            "slim": "php:8.3-apache",
            "alpine": "php:8.3-fpm-alpine",
            "distroless": None,
        },
        "dep_files": ["composer.json", "composer.lock"],
        "dockerignore": [
            "vendor", ".git", ".gitignore", "*.md", "Dockerfile",
            ".dockerignore", ".env", "node_modules", "tests", "test",
            ".idea", ".vscode", "*.swp", "*.log", "composer.phar",
        ],
    },
    "ruby": {
        "display_name": "Ruby",
        "default_entry": "config.ru",
        "default_port": 3000,
        "default_base": "slim",
        "builder_image": "ruby:3.3-slim",
        "runtime_images": {
            "slim": "ruby:3.3-slim",
            "alpine": "ruby:3.3-alpine",
            "distroless": None,
        },
        "dep_files": ["Gemfile", "Gemfile.lock"],
        "dockerignore": [
            ".git", ".gitignore", "*.md", "Dockerfile", ".dockerignore",
            ".env", "log", "tmp", "vendor/bundle", "node_modules",
            "test", "spec", ".idea", ".vscode", "*.swp", "*.log",
            "public/assets", "storage",
        ],
    },
}

# 编译型语言默认多阶段构建
COMPILED_LANGS = {"go", "java", "cpp", "rust"}


# ============================================================
# Dockerfile 生成器
# ============================================================

class DockerfileGenerator:
    def __init__(self, lang, entry=None, port=None, base=None,
                 multi_stage=True, dockerignore=True, healthcheck=False,
                 health_url="/health", health_interval="30s",
                 env_vars=None, workdir="/app", non_root=True,
                 framework=None):
        self.lang = lang
        self.config = LANG_CONFIG[lang]
        self.entry = entry or self.config["default_entry"]
        self.port = port if port is not None else self.config["default_port"]
        self.base = base or self.config["default_base"]
        self.multi_stage = multi_stage
        self.dockerignore = dockerignore
        self.healthcheck = healthcheck
        self.health_url = health_url
        self.health_interval = health_interval
        self.env_vars = env_vars or []
        self.workdir = workdir
        self.non_root = non_root
        self.framework = framework

        # distroless 不支持的语言回退到 slim
        if self.base == "distroless" and self.config["runtime_images"].get("distroless") is None:
            self.base = "slim"

        self.runtime_image = self.config["runtime_images"].get(
            self.base, self.config["runtime_images"]["slim"]
        )

    def generate(self):
        """生成 Dockerfile 内容"""
        if self.multi_stage and self.lang in COMPILED_LANGS:
            return self._generate_multistage()
        return self._generate_simple()

    def _env_lines(self, indent=""):
        """生成 ENV 行"""
        lines = []
        for ev in self.env_vars:
            if "=" in ev:
                key, val = ev.split("=", 1)
                lines.append(f"{indent}ENV {key.strip()}={val.strip()}")
        return "\n".join(lines)

    def _healthcheck_line(self):
        """生成 HEALTHCHECK 行"""
        if not self.healthcheck:
            return ""
        if self.lang in ("go", "rust", "cpp"):
            # 编译型语言用 wget/curl
            return (f'HEALTHCHECK --interval={self.health_interval} --timeout=3s '
                    f'CMD wget -qO- http://localhost:{self.port}{self.health_url} || exit 1')
        else:
            return (f'HEALTHCHECK --interval={self.health_interval} --timeout=3s '
                    f'CMD curl -f http://localhost:{self.port}{self.health_url} || exit 1')

    def _non_root_lines(self, indent=""):
        """生成非 root 用户行"""
        if not self.non_root:
            return ""
        if self.base == "alpine":
            return (f"{indent}RUN adduser -D -u 10001 appuser\n"
                    f"{indent}USER appuser")
        else:
            return (f"{indent}RUN useradd -m -u 10001 appuser\n"
                    f"{indent}USER appuser")

    def _expose_line(self):
        if self.port:
            return f"EXPOSE {self.port}"
        return ""

    # ----------------------------------------------------------
    # 简单构建（解释型语言）
    # ----------------------------------------------------------

    def _generate_simple(self):
        lines = []
        lines.append(f"# Dockerfile for {self.config['display_name']} application")
        lines.append(f"# Base image: {self.runtime_image}")
        lines.append("")

        if self.lang == "python":
            lines.extend(self._python_simple())
        elif self.lang == "node":
            lines.extend(self._node_simple())
        elif self.lang == "php":
            lines.extend(self._php_simple())
        elif self.lang == "ruby":
            lines.extend(self._ruby_simple())
        elif self.lang in COMPILED_LANGS:
            # 编译型语言但禁用了多阶段
            lines.extend(self._compiled_simple())

        return "\n".join(lines) + "\n"

    def _python_simple(self):
        lines = []
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")
        lines.append("# 设置工作目录")
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")

        # 环境变量
        env = self._env_lines()
        if env:
            lines.append("# 环境变量")
            lines.append(env)
            lines.append("")

        lines.append("# 安装系统依赖（如需额外库请在此添加）")
        if self.base == "alpine":
            lines.append("RUN apk add --no-cache gcc musl-dev libffi-dev")
        else:
            lines.append("RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*")
        lines.append("")

        lines.append("# 先复制依赖文件，利用 Docker 层缓存")
        lines.append("COPY requirements.txt .")
        lines.append("RUN pip install --no-cache-dir -r requirements.txt")
        lines.append("")

        lines.append("# 复制应用代码")
        lines.append("COPY . .")
        lines.append("")

        # 非 root
        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        # 端口
        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        # 健康检查
        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        # 启动命令
        lines.append("# 启动命令")
        if self.framework and "flask" in self.framework.lower():
            lines.append('CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]')
        elif self.framework and "django" in self.framework.lower():
            lines.append('CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]')
        else:
            lines.append(f'CMD ["python", "{self.entry}"]')

        return lines

    def _node_simple(self):
        lines = []
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")
        lines.append("# 设置工作目录")
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")

        env = self._env_lines()
        if env:
            lines.append("# 环境变量")
            lines.append(env)
            lines.append("")

        lines.append("# 先复制依赖文件，利用 Docker 层缓存")
        lines.append("COPY package*.json ./")
        lines.append("RUN npm ci --only=production || npm install --production")
        lines.append("")

        lines.append("# 复制应用代码")
        lines.append("COPY . .")
        lines.append("")

        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# 启动命令")
        lines.append(f'CMD ["node", "{self.entry}"]')

        return lines

    def _php_simple(self):
        lines = []
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")
        lines.append("# 安装 PHP 扩展（如需额外扩展请在此添加）")
        if self.base == "alpine":
            lines.append("RUN docker-php-ext-install pdo pdo_mysql mysqli")
        else:
            lines.append("RUN docker-php-ext-install pdo pdo_mysql mysqli")
        lines.append("")

        lines.append("# 设置工作目录")
        lines.append(f"WORKDIR /var/www/html")
        lines.append("")

        env = self._env_lines()
        if env:
            lines.append("# 环境变量")
            lines.append(env)
            lines.append("")

        lines.append("# 复制应用代码")
        lines.append("COPY . /var/www/html/")
        lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# Apache 会自动启动")
        lines.append('CMD ["apache2-foreground"]')

        return lines

    def _ruby_simple(self):
        lines = []
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")
        lines.append("# 安装系统依赖")
        if self.base == "alpine":
            lines.append("RUN apk add --no-cache build-base nodejs tzdata")
        else:
            lines.append("RUN apt-get update && apt-get install -y --no-install-recommends build-essential nodejs && rm -rf /var/lib/apt/lists/*")
        lines.append("")

        lines.append("# 设置工作目录")
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")

        env = self._env_lines()
        if env:
            lines.append("# 环境变量")
            lines.append(env)
            lines.append("")

        lines.append("# 先复制依赖文件")
        lines.append("COPY Gemfile Gemfile.lock ./")
        lines.append("RUN bundle install --without development test")
        lines.append("")

        lines.append("# 复制应用代码")
        lines.append("COPY . .")
        lines.append("")

        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# 启动命令")
        lines.append(f'CMD ["ruby", "{self.entry}"]')

        return lines

    def _compiled_simple(self):
        """编译型语言的简单构建（不推荐，仅在禁用多阶段时使用）"""
        lines = []
        lines.append(f"FROM {self.config['builder_image']}")
        lines.append("")
        lines.append("# 警告：这是单阶段构建，镜像体积较大。建议使用 --multi-stage。")
        lines.append("")
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("COPY . .")
        lines.append("")

        if self.lang == "go":
            lines.append("RUN go mod download && CGO_ENABLED=0 go build -o app .")
            lines.append(f'CMD ["./app"]')
        elif self.lang == "rust":
            lines.append("RUN cargo build --release")
            lines.append('CMD ["./target/release/app"]')
        elif self.lang == "cpp":
            lines.append("RUN g++ -o app main.cpp -O2")
            lines.append('CMD ["./app"]')
        elif self.lang == "java":
            lines.append("RUN mvn clean package -DskipTests")
            lines.append(f'CMD ["java", "-jar", "{self.entry}"]')

        exp = self._expose_line()
        if exp:
            lines.insert(-2, exp)

        return lines

    # ----------------------------------------------------------
    # 多阶段构建（编译型语言）
    # ----------------------------------------------------------

    def _generate_multistage(self):
        lines = []
        lines.append(f"# Dockerfile for {self.config['display_name']} application")
        lines.append(f"# Multi-stage build | Runtime: {self.runtime_image}")
        lines.append("")

        if self.lang == "go":
            lines.extend(self._go_multistage())
        elif self.lang == "java":
            lines.extend(self._java_multistage())
        elif self.lang == "cpp":
            lines.extend(self._cpp_multistage())
        elif self.lang == "rust":
            lines.extend(self._rust_multistage())

        return "\n".join(lines) + "\n"

    def _go_multistage(self):
        lines = []
        # 构建阶段
        lines.append("# ===== 构建阶段 =====")
        lines.append(f"FROM {self.config['builder_image']} AS builder")
        lines.append(f"WORKDIR /build")
        lines.append("")
        lines.append("# 先复制依赖文件，利用缓存")
        lines.append("COPY go.mod go.sum ./")
        lines.append("RUN go mod download")
        lines.append("")
        lines.append("# 复制源码并编译")
        lines.append("COPY . .")
        lines.append("RUN CGO_ENABLED=0 GOOS=linux go build -ldflags=\"-s -w\" -o /build/app .")
        lines.append("")

        # 运行阶段
        lines.append("# ===== 运行阶段 =====")
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")

        if self.base == "alpine":
            lines.append("# 安装运行时依赖")
            lines.append("RUN apk add --no-cache ca-certificates tzdata")
            lines.append("")
        elif self.base == "slim":
            lines.append("# 安装运行时依赖")
            lines.append("RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates tzdata && rm -rf /var/lib/apt/lists/*")
            lines.append("")

        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")
        lines.append("# 从构建阶段复制二进制文件")
        lines.append("COPY --from=builder /build/app .")
        lines.append("")

        env = self._env_lines()
        if env:
            lines.append("# 环境变量")
            lines.append(env)
            lines.append("")

        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# 启动命令")
        lines.append('ENTRYPOINT ["./app"]')

        return lines

    def _java_multistage(self):
        lines = []
        # 构建阶段
        lines.append("# ===== 构建阶段 =====")
        lines.append(f"FROM {self.config['builder_image']} AS builder")
        lines.append("WORKDIR /build")
        lines.append("")
        lines.append("# 先复制依赖文件")
        lines.append("COPY pom.xml .")
        lines.append("RUN mvn dependency:go-offline -B")
        lines.append("")
        lines.append("# 复制源码并构建")
        lines.append("COPY src ./src")
        lines.append("RUN mvn clean package -DskipTests -B")
        lines.append("")

        # 运行阶段
        lines.append("# ===== 运行阶段 =====")
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")
        lines.append("# 从构建阶段复制 JAR 文件")
        lines.append("COPY --from=builder /build/target/*.jar app.jar")
        lines.append("")

        env = self._env_lines()
        if env:
            lines.append("# 环境变量")
            lines.append(env)
            lines.append("")

        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# JVM 参数和启动命令")
        lines.append('ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"')
        lines.append('ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]')

        return lines

    def _cpp_multistage(self):
        lines = []
        # 构建阶段
        lines.append("# ===== 构建阶段 =====")
        lines.append(f"FROM {self.config['builder_image']} AS builder")
        lines.append("WORKDIR /build")
        lines.append("")
        lines.append("# 安装构建工具")
        lines.append("RUN apt-get update && apt-get install -y --no-install-recommends cmake make && rm -rf /var/lib/apt/lists/*")
        lines.append("")
        lines.append("# 复制源码并编译")
        lines.append("COPY . .")
        lines.append("RUN g++ -o /build/app main.cpp -O2 -std=c++17 -static")
        lines.append("")

        # 运行阶段
        lines.append("# ===== 运行阶段 =====")
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")
        lines.append("# 从构建阶段复制二进制文件")
        lines.append("COPY --from=builder /build/app .")
        lines.append("")

        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# 启动命令")
        lines.append('CMD ["./app"]')

        return lines

    def _rust_multistage(self):
        lines = []
        # 构建阶段
        lines.append("# ===== 构建阶段 =====")
        lines.append(f"FROM {self.config['builder_image']} AS builder")
        lines.append("WORKDIR /build")
        lines.append("")
        lines.append("# 先复制依赖文件")
        lines.append("COPY Cargo.toml Cargo.lock ./")
        lines.append("RUN mkdir src && echo 'fn main() {}' > src/main.rs && cargo build --release && rm -rf src")
        lines.append("")
        lines.append("# 复制源码并编译")
        lines.append("COPY . .")
        lines.append("RUN cargo build --release")
        lines.append("")

        # 运行阶段
        lines.append("# ===== 运行阶段 =====")
        lines.append(f"FROM {self.runtime_image}")
        lines.append("")

        if self.base == "alpine":
            lines.append("RUN apk add --no-cache ca-certificates")
            lines.append("")

        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")
        lines.append("# 从构建阶段复制二进制文件")
        lines.append("COPY --from=builder /build/target/release/app .")
        lines.append("")

        nr = self._non_root_lines()
        if nr:
            lines.append("# 使用非 root 用户运行")
            lines.append(nr)
            lines.append("")

        exp = self._expose_line()
        if exp:
            lines.append(exp)
            lines.append("")

        hc = self._healthcheck_line()
        if hc:
            lines.append(hc)
            lines.append("")

        lines.append("# 启动命令")
        lines.append('CMD ["./app"]')

        return lines

    # ----------------------------------------------------------
    # .dockerignore 生成
    # ----------------------------------------------------------

    def generate_dockerignore(self):
        """生成 .dockerignore 内容"""
        entries = self.config["dockerignore"]
        lines = [f"# .dockerignore for {self.config['display_name']} project", ""]
        lines.extend(entries)
        lines.append("")
        return "\n".join(lines) + "\n"


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Dockerfile 生成器（支持 8 种语言、多阶段构建、健康检查）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --lang python
  %(prog)s --lang go --multi-stage --healthcheck
  %(prog)s --lang node --port 3000 --base alpine --output ./project
  %(prog)s --lang java --env "SPRING_PROFILES_ACTIVE=prod" --healthcheck
        """,
    )

    parser.add_argument("--lang", "-l", required=True,
                        choices=list(LANG_CONFIG.keys()),
                        help="编程语言")
    parser.add_argument("--entry", "-e", help="应用入口文件")
    parser.add_argument("--port", "-p", type=int, help="暴露端口")
    parser.add_argument("--output", "-o", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--base", "-b", choices=["slim", "alpine", "distroless"],
                        help="基础镜像策略")
    parser.add_argument("--multi-stage", "-m", action="store_true", default=None,
                        help="启用多阶段构建")
    parser.add_argument("--no-multi-stage", action="store_true",
                        help="禁用多阶段构建")
    parser.add_argument("--dockerignore", "-d", action="store_true", default=True,
                        help="生成 .dockerignore（默认开启）")
    parser.add_argument("--no-dockerignore", action="store_true",
                        help="不生成 .dockerignore")
    parser.add_argument("--healthcheck", action="store_true",
                        help="添加健康检查")
    parser.add_argument("--health-url", default="/health", help="健康检查 URL 路径")
    parser.add_argument("--health-interval", default="30s", help="健康检查间隔")
    parser.add_argument("--env", action="append", default=[], help="环境变量（可多次使用）")
    parser.add_argument("--workdir", default="/app", help="工作目录")
    parser.add_argument("--non-root", action="store_true", default=True,
                        help="使用非 root 用户（默认开启）")
    parser.add_argument("--no-non-root", action="store_true",
                        help="使用 root 用户")
    parser.add_argument("--framework", help="框架名称（影响默认配置）")

    args = parser.parse_args()

    # 确定多阶段构建
    multi_stage = args.multi_stage
    if args.no_multi_stage:
        multi_stage = False
    elif multi_stage is None:
        multi_stage = args.lang in COMPILED_LANGS

    # 确定是否生成 dockerignore
    gen_dockerignore = args.dockerignore and not args.no_dockerignore

    # 确定非 root
    non_root = args.non_root and not args.no_non_root

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    # 生成 Dockerfile
    gen = DockerfileGenerator(
        lang=args.lang,
        entry=args.entry,
        port=args.port,
        base=args.base,
        multi_stage=multi_stage,
        dockerignore=gen_dockerignore,
        healthcheck=args.healthcheck,
        health_url=args.health_url,
        health_interval=args.health_interval,
        env_vars=args.env,
        workdir=args.workdir,
        non_root=non_root,
        framework=args.framework,
    )

    dockerfile_content = gen.generate()
    dockerfile_path = os.path.join(args.output, "Dockerfile")
    with open(dockerfile_path, "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    print(f"✅ Dockerfile 已生成: {dockerfile_path}")

    # 生成 .dockerignore
    if gen_dockerignore:
        dockerignore_content = gen.generate_dockerignore()
        dockerignore_path = os.path.join(args.output, ".dockerignore")
        with open(dockerignore_path, "w", encoding="utf-8") as f:
            f.write(dockerignore_content)
        print(f"✅ .dockerignore 已生成: {dockerignore_path}")

    # 输出构建命令提示
    print("")
    print("构建命令:")
    print(f"  docker build -t myapp {args.output}")
    print("")
    if args.port:
        print("运行命令:")
        print(f"  docker run -p {args.port}:{args.port} myapp")
    print("")
    print(f"语言: {LANG_CONFIG[args.lang]['display_name']} | "
          f"镜像策略: {gen.base} | "
          f"多阶段: {'是' if multi_stage else '否'} | "
          f"健康检查: {'是' if args.healthcheck else '否'}")


if __name__ == "__main__":
    main()
