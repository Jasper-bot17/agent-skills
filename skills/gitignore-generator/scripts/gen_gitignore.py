#!/usr/bin/env python3
"""
.gitignore 生成器
根据项目类型自动生成标准 .gitignore 文件
"""

import argparse
import os
import sys

# ===== 模板定义 =====

TEMPLATES = {
    "common": """\
# ===== OS 文件 =====
.DS_Store
.DS_Store?
._*
Thumbs.db
Desktop.ini
$RECYCLE.BIN/

# ===== 编辑器/IDE =====
.vscode/
.idea/
*.swp
*.swo
*~
.history/
*.sublime-project
*.sublime-workspace

# ===== 日志 =====
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# ===== 环境变量 =====
.env
.env.local
.env.*.local
""",

    "node": """\
# ===== Node.js =====
node_modules/
dist/
build/
.next/
.nuxt/
out/
*.tsbuildinfo

# ===== 包管理器 =====
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
package-lock.json
yarn.lock
pnpm-lock.yaml

# ===== 缓存 =====
.cache/
.eslintcache
.parcel-cache/
.turbo/
""",

    "python": """\
# ===== Python =====
__pycache__/
*.py[cod]
*$py.class
*.so

# ===== 虚拟环境 =====
venv/
.venv/
env/
.env/

# ===== 打包/发布 =====
*.egg-info/
*.egg
dist/
build/
eggs/
*.whl

# ===== 测试/覆盖率 =====
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.nox/
coverage.xml
*.cover

# ===== Jupyter =====
.ipynb_checkpoints/

# ===== mypy =====
.mypy_cache/
""",

    "java": """\
# ===== Java =====
*.class
target/
*.jar
*.war
*.ear
*.nar

# ===== Maven =====
mvnw
mvnw.cmd
.mvn/

# ===== Gradle =====
.gradle/
build/
!gradle/wrapper/gradle-wrapper.jar

# ===== IDE =====
.idea/
*.iml
*.iws
*.ipr
.vscode/
.settings/
.project
.classpath
""",

    "cpp": """\
# ===== C/C++ 构建产物 =====
build/
bin/
obj/
*.o
*.obj
*.so
*.dll
*.dylib
*.exe
*.out
*.a
*.lib

# ===== CMake =====
CMakeLists.txt.user
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
install_manifest.txt
compile_commands.json
CTestTestfile.cmake
_deps/

# ===== Visual Studio =====
.vs/
*.suo
*.sln.docstates
*.user
""",

    "go": """\
# ===== Go =====
# 二进制
*.exe
*.exe~
*.dll
*.so
*.dylib

# 测试覆盖率
*.test
*.out
coverage.txt

# 工作目录
vendor/

# Go workspace
go.work
go.work.sum
""",

    "rust": """\
# ===== Rust =====
target/
Cargo.lock

# 日志
*.log
""",

    "web": """\
# ===== Web 前端 =====
node_modules/
dist/
build/
out/
.next/
.nuxt/
.parcel-cache/
.cache/

# 环境变量
.env
.env.local
.env.*.local

# 上传目录
uploads/
""",
}

# ===== 交互式选择 =====

INTERACTIVE_TYPES = [
    ("common", "通用（OS文件、编辑器、日志、环境变量）"),
    ("node", "Node.js / 前端"),
    ("python", "Python"),
    ("java", "Java / Maven / Gradle"),
    ("cpp", "C/C++ / CMake"),
    ("go", "Go"),
    ("rust", "Rust"),
    ("web", "Web 项目"),
]


def generate_gitignore(types):
    """根据类型列表生成 .gitignore 内容"""
    lines = [".gitignore 自动生成", "=" * 50, ""]
    seen = set()

    for t in types:
        t = t.strip().lower()
        if t in TEMPLATES:
            if t not in seen:
                lines.append(f"# >>> {t} 项目")
                lines.append(TEMPLATES[t].rstrip())
                lines.append("")
                seen.add(t)
        else:
            print(f"⚠️  未知类型: {t}，跳过", file=sys.stderr)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=".gitignore 生成器")
    parser.add_argument("--type", "-t", help="项目类型（逗号分隔），如 node,python")
    parser.add_argument("--output", "-o", default=".gitignore", help="输出文件路径（默认 .gitignore）")
    parser.add_argument("--preview", "-p", action="store_true", help="仅预览不写入")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式选择")
    args = parser.parse_args()

    types = []

    if args.interactive:
        print("选择项目类型（输入编号，逗号分隔，如 1,2,3）：")
        for i, (key, desc) in enumerate(INTERACTIVE_TYPES, 1):
            print(f"  {i}. {desc}")
        choices = input("> ").strip()
        for c in choices.split(","):
            try:
                idx = int(c.strip()) - 1
                if 0 <= idx < len(INTERACTIVE_TYPES):
                    types.append(INTERACTIVE_TYPES[idx][0])
            except ValueError:
                pass
    elif args.type:
        types = [t.strip() for t in args.type.split(",")]
    else:
        # 默认加上 common
        types = ["common"]
        print("未指定类型，默认使用 common", file=sys.stderr)

    if not types:
        print("未选择任何类型，退出", file=sys.stderr)
        sys.exit(1)

    content = generate_gitignore(types)

    if args.preview:
        print(content)
        return

    # 备份已有文件
    if os.path.exists(args.output):
        backup = args.output + ".bak"
        os.rename(args.output, backup)
        print(f"📦 已备份原有文件到 {backup}")

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已生成 {args.output}")
    print(f"   包含类型: {', '.join(types)}")
    print(f"   共 {len(content.splitlines())} 行")


if __name__ == "__main__":
    main()
