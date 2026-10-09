#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CI/CD 流水线生成脚本

功能：
- 生成 GitHub Actions 工作流文件（.github/workflows/ci.yml）
- 生成 GitLab CI 配置文件（.gitlab-ci.yml）
- 支持四种场景：build-test、lint、docker、release
- 支持六种语言：python、nodejs、go、rust、cpp、java
- 支持矩阵构建（多版本/多平台）
- 内置依赖缓存配置
- 支持并发控制
- 生成状态徽章 Markdown

用法：
  python3 generate_ci_cd.py --platform github --scenario build-test --language python
  python3 generate_ci_cd.py --platform gitlab --scenario lint --language nodejs
  python3 generate_ci_cd.py --platform github --scenario docker
  python3 generate_ci_cd.py --platform github --scenario release --language python
  python3 generate_ci_cd.py --platform github --scenario build-test --language python --matrix
  python3 generate_ci_cd.py --platform github --language python --all
  python3 generate_ci_cd.py --platform github --scenario build-test --language python --output /path/to/project
"""

import argparse
import os
import sys


# ============================================================
# 语言配置
# ============================================================

LANGUAGE_CONFIG = {
    "python": {
        "name": "Python",
        "default_versions": ["3.10", "3.11", "3.12"],
        "setup_action": "actions/setup-python@v5",
        "setup_version_key": "python-version",
        "docker_image": "python:{version}",
        "cache_path": "~/.cache/pip",
        "cache_key": "${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}",
        "gitlab_cache_paths": [".cache/pip"],
        "install_cmd": "pip install -r requirements.txt",
        "build_cmd": "python -m compileall .",
        "test_cmd": "pytest",
        "lint_cmds": [
            "pip install flake8 black isort",
            "flake8 .",
            "black --check .",
            "isort --check-only .",
        ],
        "badge_color": "3776AB",
    },
    "nodejs": {
        "name": "Node.js",
        "default_versions": ["18", "20", "22"],
        "setup_action": "actions/setup-node@v4",
        "setup_version_key": "node-version",
        "docker_image": "node:{version}",
        "cache_path": "~/.npm",
        "cache_key": "${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}",
        "gitlab_cache_paths": ["node_modules/", ".npm/"],
        "install_cmd": "npm ci",
        "build_cmd": "npm run build",
        "test_cmd": "npm test",
        "lint_cmds": [
            "npm ci",
            "npm run lint",
            "npm run format:check",
        ],
        "badge_color": "339933",
    },
    "go": {
        "name": "Go",
        "default_versions": ["1.21", "1.22", "1.23"],
        "setup_action": "actions/setup-go@v5",
        "setup_version_key": "go-version",
        "docker_image": "golang:{version}",
        "cache_path": "~/go/pkg/mod",
        "cache_key": "${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}",
        "gitlab_cache_paths": ["~/go/pkg/mod/"],
        "install_cmd": "go mod download",
        "build_cmd": "go build ./...",
        "test_cmd": "go test ./... -v",
        "lint_cmds": [
            "go install golang.org/x/tools/cmd/goimports@latest",
            "go vet ./...",
            "test -z \"$(goimports -l .)\"",
        ],
        "badge_color": "00ADD8",
    },
    "rust": {
        "name": "Rust",
        "default_versions": ["stable", "beta", "nightly"],
        "setup_action": "dtolnay/rust-toolchain@stable",
        "setup_version_key": None,
        "docker_image": "rust:{version}",
        "cache_path": "~/.cargo/registry, ~/.cargo/git, target",
        "cache_key": "${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}",
        "gitlab_cache_paths": ["~/.cargo/registry/", "target/"],
        "install_cmd": "cargo fetch",
        "build_cmd": "cargo build --release",
        "test_cmd": "cargo test",
        "lint_cmds": [
            "rustup component add clippy rustfmt",
            "cargo clippy -- -D warnings",
            "cargo fmt -- --check",
        ],
        "badge_color": "000000",
    },
    "cpp": {
        "name": "C++",
        "default_versions": ["17", "20", "23"],
        "setup_action": None,
        "setup_version_key": None,
        "docker_image": "gcc:latest",
        "cache_path": "~/.ccache",
        "cache_key": "${{ runner.os }}-ccache-${{ github.sha }}",
        "gitlab_cache_paths": ["~/.ccache/"],
        "install_cmd": "sudo apt-get update && sudo apt-get install -y cmake g++ ccache",
        "build_cmd": "mkdir -p build && cd build && cmake .. && make -j$(nproc)",
        "test_cmd": "cd build && ctest --output-on-failure",
        "lint_cmds": [
            "sudo apt-get install -y clang-format clang-tidy",
            "find . -name '*.cpp' -o -name '*.h' | xargs clang-format --dry-run --Werror",
            "mkdir -p build && cd build && cmake .. && run-clang-tidy",
        ],
        "badge_color": "00599C",
    },
    "java": {
        "name": "Java",
        "default_versions": ["11", "17", "21"],
        "setup_action": "actions/setup-java@v4",
        "setup_version_key": "java-version",
        "docker_image": "eclipse-temurin:{version}",
        "cache_path": "~/.m2/repository",
        "cache_key": "${{ runner.os }}-maven-${{ hashFiles('**/pom.xml') }}",
        "gitlab_cache_paths": ["~/.m2/repository/"],
        "install_cmd": "mvn dependency:resolve",
        "build_cmd": "mvn package -DskipTests",
        "test_cmd": "mvn test",
        "lint_cmds": [
            "mvn checkstyle:check",
            "mvn spotbugs:check",
        ],
        "badge_color": "ED8B00",
    },
}


# ============================================================
# GitHub Actions 生成器
# ============================================================

def generate_github_build_test(language: str, versions: list, matrix: bool) -> str:
    """生成 GitHub Actions 构建测试工作流"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]

    lines = []
    lines.append(f"name: {lang_name} CI")
    lines.append("")
    lines.append("on:")
    lines.append("  push:")
    lines.append("    branches: [main, master, develop]")
    lines.append("  pull_request:")
    lines.append("    branches: [main, master]")
    lines.append("")
    lines.append("concurrency:")
    lines.append("  group: ${{ github.workflow }}-${{ github.ref }}")
    lines.append("  cancel-in-progress: true")
    lines.append("")
    lines.append("jobs:")
    lines.append("  build-test:")
    lines.append("    runs-on: ubuntu-latest")

    if matrix:
        lines.append("    strategy:")
        lines.append("      fail-fast: false")
        lines.append("      matrix:")
        if cfg["setup_version_key"]:
            vers_str = ", ".join(f"'{v}'" for v in versions)
            lines.append(f"        {cfg['setup_version_key']}: [{vers_str}]")
        else:
            lines.append(f"        version: {versions}")
        lines.append("")

    lines.append("    steps:")
    lines.append("      - name: Checkout code")
    lines.append("        uses: actions/checkout@v4")
    lines.append("")

    # 语言环境设置
    if cfg["setup_action"]:
        lines.append(f"      - name: Setup {lang_name}")
        lines.append(f"        uses: {cfg['setup_action']}")
        lines.append("        with:")
        if cfg["setup_version_key"]:
            if matrix:
                lines.append(f"          {cfg['setup_version_key']}: ${{{{ matrix.{cfg['setup_version_key']} }}}}")
            else:
                lines.append(f"          {cfg['setup_version_key']}: '{versions[0]}'")
        if language == "java":
            lines.append("          distribution: 'temurin'")
        lines.append("")
    elif language == "cpp":
        lines.append("      - name: Install build dependencies")
        lines.append("        run: |")
        lines.append("          sudo apt-get update")
        lines.append("          sudo apt-get install -y cmake g++ ccache")
        lines.append("")

    # 依赖缓存
    if cfg["cache_path"]:
        lines.append("      - name: Cache dependencies")
        lines.append("        uses: actions/cache@v4")
        lines.append("        with:")
        lines.append(f"          path: {cfg['cache_path']}")
        lines.append(f"          key: {cfg['cache_key']}")
        lines.append("          restore-keys: |")
        lines.append(f"            ${{{{ runner.os }}}}-{language}-")
        lines.append("")

    # 安装依赖
    lines.append(f"      - name: Install dependencies")
    lines.append(f"        run: {cfg['install_cmd']}")
    lines.append("")

    # 构建
    lines.append(f"      - name: Build")
    lines.append(f"        run: {cfg['build_cmd']}")
    lines.append("")

    # 测试
    lines.append(f"      - name: Run tests")
    lines.append(f"        run: {cfg['test_cmd']}")
    lines.append("")

    # 上传测试报告
    lines.append("      - name: Upload test results")
    lines.append("        if: always()")
    lines.append("        uses: actions/upload-artifact@v4")
    lines.append("        with:")
    lines.append("          name: test-results")
    lines.append("          path: |")
    lines.append("            **/test-results/**")
    lines.append("            **/coverage/**")
    lines.append("          if-no-files-found: ignore")
    lines.append("")

    return "\n".join(lines)


def generate_github_lint(language: str, versions: list) -> str:
    """生成 GitHub Actions 代码检查工作流"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]

    lines = []
    lines.append(f"name: {lang_name} Lint")
    lines.append("")
    lines.append("on:")
    lines.append("  push:")
    lines.append("    branches: [main, master, develop]")
    lines.append("  pull_request:")
    lines.append("    branches: [main, master]")
    lines.append("")
    lines.append("concurrency:")
    lines.append("  group: ${{ github.workflow }}-${{ github.ref }}")
    lines.append("  cancel-in-progress: true")
    lines.append("")
    lines.append("jobs:")
    lines.append("  lint:")
    lines.append("    runs-on: ubuntu-latest")
    lines.append("    steps:")
    lines.append("      - name: Checkout code")
    lines.append("        uses: actions/checkout@v4")
    lines.append("")

    if cfg["setup_action"]:
        lines.append(f"      - name: Setup {lang_name}")
        lines.append(f"        uses: {cfg['setup_action']}")
        lines.append("        with:")
        if cfg["setup_version_key"]:
            lines.append(f"          {cfg['setup_version_key']}: '{versions[0]}'")
        if language == "java":
            lines.append("          distribution: 'temurin'")
        lines.append("")

    lines.append("      - name: Run linters")
    lines.append("        run: |")
    for cmd in cfg["lint_cmds"]:
        lines.append(f"          {cmd}")
    lines.append("")

    return "\n".join(lines)


def generate_github_docker(language: str) -> str:
    """生成 GitHub Actions Docker 构建推送工作流"""
    cfg = LANGUAGE_CONFIG[language]

    lines = []
    lines.append("name: Docker Build")
    lines.append("")
    lines.append("on:")
    lines.append("  push:")
    lines.append("    branches: [main, master]")
    lines.append("    tags: ['v*']")
    lines.append("  pull_request:")
    lines.append("    branches: [main, master]")
    lines.append("")
    lines.append("concurrency:")
    lines.append("  group: ${{ github.workflow }}-${{ github.ref }}")
    lines.append("  cancel-in-progress: true")
    lines.append("")
    lines.append("env:")
    lines.append("  REGISTRY: docker.io")
    lines.append("  IMAGE_NAME: ${{ github.repository }}")
    lines.append("")
    lines.append("jobs:")
    lines.append("  docker:")
    lines.append("    runs-on: ubuntu-latest")
    lines.append("    permissions:")
    lines.append("      contents: read")
    lines.append("      packages: write")
    lines.append("    steps:")
    lines.append("      - name: Checkout code")
    lines.append("        uses: actions/checkout@v4")
    lines.append("")
    lines.append("      - name: Set up Docker Buildx")
    lines.append("        uses: docker/setup-buildx-action@v3")
    lines.append("")
    lines.append("      - name: Log in to Docker Hub")
    lines.append("        if: github.event_name != 'pull_request'")
    lines.append("        uses: docker/login-action@v3")
    lines.append("        with:")
    lines.append("          username: ${{ secrets.DOCKER_USERNAME }}")
    lines.append("          password: ${{ secrets.DOCKER_PASSWORD }}")
    lines.append("")
    lines.append("      - name: Extract metadata")
    lines.append("        id: meta")
    lines.append("        uses: docker/metadata-action@v5")
    lines.append("        with:")
    lines.append("          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}")
    lines.append("          tags: |")
    lines.append("            type=ref,event=branch")
    lines.append("            type=ref,event=pr")
    lines.append("            type=semver,pattern={{version}}")
    lines.append("            type=semver,pattern={{major}}.{{minor}}")
    lines.append("            type=sha")
    lines.append("")
    lines.append("      - name: Build and push")
    lines.append("        uses: docker/build-push-action@v5")
    lines.append("        with:")
    lines.append("          context: .")
    lines.append("          push: ${{ github.event_name != 'pull_request' }}")
    lines.append("          tags: ${{ steps.meta.outputs.tags }}")
    lines.append("          labels: ${{ steps.meta.outputs.labels }}")
    lines.append("          cache-from: type=gha")
    lines.append("          cache-to: type=gha,mode=max")
    lines.append("          platforms: linux/amd64,linux/arm64")
    lines.append("")

    return "\n".join(lines)


def generate_github_release(language: str, versions: list) -> str:
    """生成 GitHub Actions 发布工作流"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]

    lines = []
    lines.append("name: Release")
    lines.append("")
    lines.append("on:")
    lines.append("  push:")
    lines.append("    tags: ['v*']")
    lines.append("")
    lines.append("permissions:")
    lines.append("  contents: write")
    lines.append("")
    lines.append("jobs:")
    lines.append("  release:")
    lines.append("    runs-on: ubuntu-latest")
    lines.append("    steps:")
    lines.append("      - name: Checkout code")
    lines.append("        uses: actions/checkout@v4")
    lines.append("        with:")
    lines.append("          fetch-depth: 0")
    lines.append("")

    if cfg["setup_action"]:
        lines.append(f"      - name: Setup {lang_name}")
        lines.append(f"        uses: {cfg['setup_action']}")
        lines.append("        with:")
        if cfg["setup_version_key"]:
            lines.append(f"          {cfg['setup_version_key']}: '{versions[0]}'")
        if language == "java":
            lines.append("          distribution: 'temurin'")
        lines.append("")

    lines.append(f"      - name: Install dependencies")
    lines.append(f"        run: {cfg['install_cmd']}")
    lines.append("")
    lines.append(f"      - name: Build")
    lines.append(f"        run: {cfg['build_cmd']}")
    lines.append("")
    lines.append("      - name: Generate release notes")
    lines.append("        id: release_notes")
    lines.append("        uses: release-drafter/release-drafter@v6")
    lines.append("        with:")
    lines.append("          disable-autolabeler: true")
    lines.append("        env:")
    lines.append("          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}")
    lines.append("")
    lines.append("      - name: Create Release")
    lines.append("        uses: softprops/action-gh-release@v2")
    lines.append("        with:")
    lines.append("          generate_release_notes: true")
    lines.append("          files: |")
    lines.append("            dist/**")
    lines.append("            build/**")
    lines.append("            target/release/*")
    lines.append("          fail_on_unmatched_files: false")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# GitLab CI 生成器
# ============================================================

def generate_gitlab_build_test(language: str, versions: list, matrix: bool) -> str:
    """生成 GitLab CI 构建测试配置"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]

    lines = []
    lines.append(f"# {lang_name} CI/CD")
    lines.append("")
    lines.append("stages:")
    lines.append("  - build")
    lines.append("  - test")
    lines.append("")

    if matrix and len(versions) > 1:
        vers_str = ", ".join(f"'{v}'" for v in versions)
        lines.append(f".{language}_test_template:")
        lines.append("  stage: test")
        lines.append(f"  image: {cfg['docker_image'].format(version='${VERSION}')}")
        lines.append("  parallel:")
        lines.append("    matrix:")
        lines.append(f"      - VERSION: [{vers_str}]")
        lines.append("  cache:")
        lines.append("    key: ${CI_COMMIT_REF_SLUG}-${VERSION}")
        lines.append("    paths:")
        for path in cfg["gitlab_cache_paths"]:
            lines.append(f"      - {path}")
        lines.append("  script:")
        lines.append(f"    - {cfg['install_cmd']}")
        lines.append(f"    - {cfg['test_cmd']}")
        lines.append("")
        lines.append(f"{language}-test:")
        lines.append(f"  extends: .{language}_test_template")
        lines.append("")
    else:
        version = versions[0]
        lines.append(f"{language}-build:")
        lines.append("  stage: build")
        lines.append(f"  image: {cfg['docker_image'].format(version=version)}")
        lines.append("  cache:")
        lines.append("    key: ${CI_COMMIT_REF_SLUG}")
        lines.append("    paths:")
        for path in cfg["gitlab_cache_paths"]:
            lines.append(f"      - {path}")
        lines.append("  script:")
        lines.append(f"    - {cfg['install_cmd']}")
        lines.append(f"    - {cfg['build_cmd']}")
        lines.append("  artifacts:")
        lines.append("    paths:")
        lines.append("      - build/")
        lines.append("      - dist/")
        lines.append("      - target/")
        lines.append("    expire_in: 1 week")
        lines.append("")
        lines.append(f"{language}-test:")
        lines.append("  stage: test")
        lines.append(f"  image: {cfg['docker_image'].format(version=version)}")
        lines.append("  cache:")
        lines.append("    key: ${CI_COMMIT_REF_SLUG}")
        lines.append("    paths:")
        for path in cfg["gitlab_cache_paths"]:
            lines.append(f"      - {path}")
        lines.append("  script:")
        lines.append(f"    - {cfg['install_cmd']}")
        lines.append(f"    - {cfg['test_cmd']}")
        lines.append("")

    # 规则
    lines.append("workflow:")
    lines.append("  rules:")
    lines.append("    - if: $CI_COMMIT_BRANCH == 'main' || $CI_COMMIT_BRANCH == 'master'")
    lines.append("    - if: $CI_COMMIT_BRANCH == 'develop'")
    lines.append("    - if: $CI_PIPELINE_SOURCE == 'merge_request_event'")
    lines.append("")

    return "\n".join(lines)


def generate_gitlab_lint(language: str, versions: list) -> str:
    """生成 GitLab CI 代码检查配置"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]
    version = versions[0]

    lines = []
    lines.append(f"# {lang_name} Lint")
    lines.append("")
    lines.append("stages:")
    lines.append("  - lint")
    lines.append("")
    lines.append(f"{language}-lint:")
    lines.append("  stage: lint")
    lines.append(f"  image: {cfg['docker_image'].format(version=version)}")
    lines.append("  script:")
    for cmd in cfg["lint_cmds"]:
        lines.append(f"    - {cmd}")
    lines.append("")

    return "\n".join(lines)


def generate_gitlab_docker(language: str) -> str:
    """生成 GitLab CI Docker 构建配置"""
    lines = []
    lines.append("# Docker Build")
    lines.append("")
    lines.append("stages:")
    lines.append("  - build")
    lines.append("")
    lines.append("docker-build:")
    lines.append("  stage: build")
    lines.append("  image: docker:latest")
    lines.append("  services:")
    lines.append("    - docker:dind")
    lines.append("  variables:")
    lines.append("    DOCKER_HOST: tcp://docker:2376")
    lines.append("    DOCKER_TLS_CERTDIR: /certs")
    lines.append("    DOCKER_DRIVER: overlay2")
    lines.append("  before_script:")
    lines.append("    - docker login -u $DOCKER_USER -p $DOCKER_PASSWORD")
    lines.append("  script:")
    lines.append("    - |")
    lines.append("      if [ -n \"$CI_COMMIT_TAG\" ]; then")
    lines.append("        TAG=$CI_COMMIT_TAG")
    lines.append("      else")
    lines.append("        TAG=$CI_COMMIT_SHORT_SHA")
    lines.append("      fi")
    lines.append("    - docker build -t $CI_REGISTRY_IMAGE:$TAG .")
    lines.append("    - docker push $CI_REGISTRY_IMAGE:$TAG")
    lines.append("    - |")
    lines.append("      if [ \"$CI_COMMIT_BRANCH\" = \"main\" ] || [ \"$CI_COMMIT_BRANCH\" = \"master\" ]; then")
    lines.append("        docker tag $CI_REGISTRY_IMAGE:$TAG $CI_REGISTRY_IMAGE:latest")
    lines.append("        docker push $CI_REGISTRY_IMAGE:latest")
    lines.append("      fi")
    lines.append("  rules:")
    lines.append("    - if: $CI_COMMIT_BRANCH == 'main' || $CI_COMMIT_BRANCH == 'master'")
    lines.append("    - if: $CI_COMMIT_TAG")
    lines.append("")

    return "\n".join(lines)


def generate_gitlab_release(language: str, versions: list) -> str:
    """生成 GitLab CI 发布配置"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]
    version = versions[0]

    lines = []
    lines.append("# Release")
    lines.append("")
    lines.append("stages:")
    lines.append("  - build")
    lines.append("  - release")
    lines.append("")
    lines.append(f"{language}-build:")
    lines.append("  stage: build")
    lines.append(f"  image: {cfg['docker_image'].format(version=version)}")
    lines.append("  script:")
    lines.append(f"    - {cfg['install_cmd']}")
    lines.append(f"    - {cfg['build_cmd']}")
    lines.append("  artifacts:")
    lines.append("    paths:")
    lines.append("      - dist/")
    lines.append("      - build/")
    lines.append("      - target/release/")
    lines.append("  rules:")
    lines.append("    - if: $CI_COMMIT_TAG")
    lines.append("")
    lines.append("release:")
    lines.append("  stage: release")
    lines.append("  image: registry.gitlab.com/gitlab-org/release-cli:latest")
    lines.append("  needs:")
    lines.append(f"    - job: {language}-build")
    lines.append("      artifacts: true")
    lines.append("  script:")
    lines.append("    - echo 'Creating release...'")
    lines.append("  release:")
    lines.append("    name: 'Release $CI_COMMIT_TAG'")
    lines.append("    description: 'Release $CI_COMMIT_TAG'")
    lines.append("    tag_name: '$CI_COMMIT_TAG'")
    lines.append("    assets:")
    lines.append("      links:")
    lines.append("        - name: 'Build artifacts'")
    lines.append("          url: '$CI_PROJECT_URL/-/jobs/artifacts/$CI_COMMIT_TAG/download?job=build'")
    lines.append("  rules:")
    lines.append("    - if: $CI_COMMIT_TAG")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# 徽章生成
# ============================================================

def generate_badge(platform: str, language: str, repo: str = "") -> str:
    """生成状态徽章 Markdown"""
    cfg = LANGUAGE_CONFIG[language]
    lang_name = cfg["name"]

    lines = []
    lines.append(f"## {lang_name} CI/CD 状态徽章")
    lines.append("")

    if platform == "github":
        if repo:
            lines.append(f"[![{lang_name} CI](https://github.com/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{repo}/actions)")
        else:
            lines.append("```markdown")
            lines.append("![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)")
            lines.append("```")
    elif platform == "gitlab":
        if repo:
            lines.append(f"[![pipeline status](https://gitlab.com/{repo}/badges/main/pipeline.svg)](https://gitlab.com/{repo}/-/commits/main)")
            lines.append(f"[![coverage report](https://gitlab.com/{repo}/badges/main/coverage.svg)](https://gitlab.com/{repo}/-/commits/main)")
        else:
            lines.append("```markdown")
            lines.append("[![pipeline status](https://gitlab.com/GROUP/PROJECT/badges/main/pipeline.svg)](https://gitlab.com/GROUP/PROJECT/-/commits/main)")
            lines.append("```")

    lines.append("")
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="CI/CD 流水线生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--platform", "-p", required=True,
                        choices=["github", "gitlab"],
                        help="CI 平台")
    parser.add_argument("--scenario", "-s", default="build-test",
                        choices=["build-test", "lint", "docker", "release"],
                        help="流水线场景（默认 build-test）")
    parser.add_argument("--language", "-l", default="python",
                        choices=list(LANGUAGE_CONFIG.keys()),
                        help="编程语言（默认 python）")
    parser.add_argument("--versions", "-v", default="",
                        help="语言版本，逗号分隔（如 '3.10,3.11,3.12'）")
    parser.add_argument("--matrix", action="store_true",
                        help="启用矩阵构建（多版本）")
    parser.add_argument("--output", "-o", default=".",
                        help="输出目录（默认当前目录）")
    parser.add_argument("--all", action="store_true",
                        help="生成所有场景的配置")
    parser.add_argument("--repo", default="",
                        help="仓库地址（用于生成徽章，如 owner/repo）")
    args = parser.parse_args()

    # 解析版本
    if args.versions:
        versions = [v.strip() for v in args.versions.split(",") if v.strip()]
    else:
        versions = LANGUAGE_CONFIG[args.language]["default_versions"]

    cfg = LANGUAGE_CONFIG[args.language]
    lang_name = cfg["name"]

    # 确定要生成的场景
    scenarios = ["build-test", "lint", "docker", "release"] if args.all else [args.scenario]

    generated_files = []

    for scenario in scenarios:
        print(f"正在生成 {args.platform} {scenario} ({lang_name})...")

        # 生成配置内容
        if args.platform == "github":
            if scenario == "build-test":
                content = generate_github_build_test(args.language, versions, args.matrix)
                filename = ".github/workflows/ci.yml"
            elif scenario == "lint":
                content = generate_github_lint(args.language, versions)
                filename = ".github/workflows/lint.yml"
            elif scenario == "docker":
                content = generate_github_docker(args.language)
                filename = ".github/workflows/docker.yml"
            elif scenario == "release":
                content = generate_github_release(args.language, versions)
                filename = ".github/workflows/release.yml"
        else:  # gitlab
            if scenario == "build-test":
                content = generate_gitlab_build_test(args.language, versions, args.matrix)
                filename = ".gitlab-ci.yml"
            elif scenario == "lint":
                content = generate_gitlab_lint(args.language, versions)
                filename = ".gitlab-ci-lint.yml"
            elif scenario == "docker":
                content = generate_gitlab_docker(args.language)
                filename = ".gitlab-ci-docker.yml"
            elif scenario == "release":
                content = generate_gitlab_release(args.language, versions)
                filename = ".gitlab-ci-release.yml"

        # 写入文件
        filepath = os.path.join(args.output, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        generated_files.append(filepath)
        print(f"  创建: {filepath}")

    # 生成徽章
    badge_content = generate_badge(args.platform, args.language, args.repo)
    badge_path = os.path.join(args.output, "CI-BADGE.md")
    with open(badge_path, "w", encoding="utf-8") as f:
        f.write(badge_content)
    generated_files.append(badge_path)
    print(f"  创建: {badge_path}")

    print("")
    print("✅ CI/CD 配置生成完成！")
    print("")
    print("生成的文件：")
    for f in generated_files:
        print(f"  - {f}")
    print("")

    # 后续步骤提示
    if "docker" in scenarios or "release" in scenarios:
        print("⚠️  注意：Docker 推送和发布场景需要配置密钥：")
        if args.platform == "github":
            print("  GitHub: Settings → Secrets and variables → Actions")
            print("  - DOCKER_USERNAME / DOCKER_PASSWORD（Docker Hub）")
        else:
            print("  GitLab: Settings → CI/CD → Variables")
            print("  - DOCKER_USER / DOCKER_PASSWORD")
        print("")


if __name__ == "__main__":
    main()
