#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Makefile 生成器

自动扫描 C/C++ 源文件并生成完整的 Makefile。

用法：
  python3 gen_makefile.py
  python3 gen_makefile.py --target myapp
  python3 gen_makefile.py --extra-flags "-std=c++17 -pthread"
  python3 gen_makefile.py --preview
"""

import argparse
import os
import sys
from pathlib import Path


# ============================================================
# 源文件扫描
# ============================================================

C_EXTENSIONS = {".c"}
CPP_EXTENSIONS = {".cpp", ".cc", ".cxx"}
HEADER_EXTENSIONS = {".h", ".hpp", ".hh", ".hxx"}


def scan_sources(src_dir="."):
    """扫描目录中的源文件和头文件"""
    src_dir = Path(src_dir)
    c_files = []
    cpp_files = []
    header_dirs = set()

    for f in sorted(src_dir.iterdir()):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in C_EXTENSIONS:
            c_files.append(f.name)
        elif ext in CPP_EXTENSIONS:
            cpp_files.append(f.name)
        elif ext in HEADER_EXTENSIONS:
            header_dirs.add(str(f.parent))

    # 如果有 src/ 子目录，也扫描
    src_subdir = src_dir / "src"
    if src_subdir.is_dir():
        for f in sorted(src_subdir.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext in C_EXTENSIONS:
                c_files.append(f"src/{f.name}")
            elif ext in CPP_EXTENSIONS:
                cpp_files.append(f"src/{f.name}")
            elif ext in HEADER_EXTENSIONS:
                header_dirs.add("src")

    # include/ 目录
    include_dir = src_dir / "include"
    if include_dir.is_dir():
        header_dirs.add("include")

    all_sources = c_files + cpp_files
    is_cpp = len(cpp_files) > 0

    return {
        "c_files": c_files,
        "cpp_files": cpp_files,
        "all_sources": all_sources,
        "is_cpp": is_cpp,
        "header_dirs": sorted(header_dirs),
    }


# ============================================================
# Makefile 生成
# ============================================================

def generate_makefile(info, target_name="", extra_flags="", lang="auto"):
    """生成 Makefile 内容"""

    is_cpp = info["is_cpp"] if lang == "auto" else (lang == "cpp")
    compiler = "g++" if is_cpp else "gcc"

    if not target_name:
        # 用目录名作为默认目标名
        target_name = Path.cwd().name or "program"

    # 源文件列表
    sources = info["all_sources"]
    if not sources:
        return None, "未找到任何源文件（.c/.cpp/.cc/.cxx）"

    # 对象文件
    objects = []
    for s in sources:
        base = os.path.splitext(s)[0]
        objects.append(f"build/{base}.o")

    # 头文件目录
    include_flags = ""
    if info["header_dirs"]:
        for d in info["header_dirs"]:
            include_flags += f" -I{d}"
        include_flags = include_flags.strip()
    if include_flags:
        include_flags = " " + include_flags

    # 编译参数
    std_flag = "-std=c++17" if is_cpp else "-std=c11"
    extra = f" {extra_flags}" if extra_flags else ""

    debug_flags = f"{std_flag} -g -Wall -Wextra -O0{include_flags}{extra}"
    release_flags = f"{std_flag} -O2 -Wall -DNDEBUG{include_flags}{extra}"

    # 生成内容
    lines = []
    lines.append(f"# Makefile 自动生成 - {target_name}")
    lines.append(f"# 编译器: {compiler}")
    lines.append("")
    lines.append(f"CXX = {compiler}")
    lines.append(f"TARGET = {target_name}")
    lines.append(f"BUILD_DIR = build")
    lines.append("")
    lines.append(f"# 源文件")
    lines.append(f"SRCS = {' '.join(sources)}")
    lines.append(f"OBJS = {' '.join(objects)}")
    lines.append("")
    lines.append(f"# 编译参数")
    lines.append(f"DEBUG_FLAGS = {debug_flags}")
    lines.append(f"RELEASE_FLAGS = {release_flags}")
    lines.append("")
    lines.append(f"# 默认使用 debug")
    lines.append(f"CFLAGS = $(DEBUG_FLAGS)")
    lines.append("")
    lines.append(".PHONY: all debug release clean run rebuild")
    lines.append("")
    lines.append("all: $(TARGET)")
    lines.append("")
    lines.append("# 创建 build 目录")
    lines.append("$(BUILD_DIR):")
    lines.append("\tmkdir -p $(BUILD_DIR)")
    lines.append("")
    lines.append("# 编译规则")
    lines.append("$(BUILD_DIR)/%.o: %.c | $(BUILD_DIR)")
    lines.append("\t$(CXX) $(CFLAGS) -c $< -o $@")
    lines.append("")
    lines.append("$(BUILD_DIR)/%.o: %.cpp | $(BUILD_DIR)")
    lines.append("\t$(CXX) $(CFLAGS) -c $< -o $@")
    lines.append("")
    lines.append("$(BUILD_DIR)/%.o: %.cc | $(BUILD_DIR)")
    lines.append("\t$(CXX) $(CFLAGS) -c $< -o $@")
    lines.append("")
    lines.append("# 链接")
    lines.append("$(TARGET): $(OBJS)")
    lines.append("\t$(CXX) $(OBJS) -o $(TARGET)")
    lines.append("")
    lines.append("# 快捷目标")
    lines.append("debug: CFLAGS = $(DEBUG_FLAGS)")
    lines.append("debug: clean all")
    lines.append("")
    lines.append("release: CFLAGS = $(RELEASE_FLAGS)")
    lines.append("release: clean all")
    lines.append("")
    lines.append("run: all")
    lines.append("\t./$(TARGET)")
    lines.append("")
    lines.append("rebuild: clean all")
    lines.append("")
    lines.append("clean:")
    lines.append("\trm -rf $(BUILD_DIR) $(TARGET)")
    lines.append("")

    return "\n".join(lines), None


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Makefile 生成器")
    parser.add_argument("-o", "--output", default="Makefile", help="输出文件名（默认 Makefile）")
    parser.add_argument("--target", default="", help="输出程序名（默认用目录名）")
    parser.add_argument("--src-dir", default=".", help="源文件目录（默认当前目录）")
    parser.add_argument("--lang", choices=["auto", "c", "cpp"], default="auto", help="语言模式")
    parser.add_argument("--extra-flags", default="", help="附加编译参数")
    parser.add_argument("--preview", action="store_true", help="只预览不写入文件")
    args = parser.parse_args()

    # 扫描源文件
    info = scan_sources(args.src_dir)

    if not info["all_sources"]:
        print("❌ 未找到任何 C/C++ 源文件（.c/.cpp/.cc/.cxx）", file=sys.stderr)
        sys.exit(1)

    print(f"📂 扫描到 {len(info['all_sources'])} 个源文件：")
    for s in info["all_sources"]:
        print(f"   - {s}")
    print(f"   语言: {'C++' if info['is_cpp'] else 'C'}")
    if info["header_dirs"]:
        print(f"   头文件目录: {', '.join(info['header_dirs'])}")
    print()

    # 生成 Makefile
    content, err = generate_makefile(
        info,
        target_name=args.target,
        extra_flags=args.extra_flags,
        lang=args.lang,
    )

    if err:
        print(f"❌ {err}", file=sys.stderr)
        sys.exit(1)

    if args.preview:
        print("=" * 50)
        print(content)
        print("=" * 50)
        return

    # 检查是否已存在 Makefile
    output_path = args.output
    if os.path.exists(output_path):
        backup = f"{output_path}.bak"
        os.rename(output_path, backup)
        print(f"⚠️  已有 {output_path}，备份为 {backup}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已生成 {output_path}")
    print()
    print("可用命令：")
    print(f"  make            # 调试编译")
    print(f"  make release    # 发布编译")
    print(f"  make run        # 编译并运行")
    print(f"  make clean      # 清理")


if __name__ == "__main__":
    main()
