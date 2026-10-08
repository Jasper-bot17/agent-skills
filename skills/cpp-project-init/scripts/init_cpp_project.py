#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
C++ 项目初始化脚本

功能：
- 一键生成标准 C++ 项目结构
- 支持三种项目类型：可执行文件(executable)、静态库(library)、头文件库(header-only)
- 支持 C++11/14/17/20/23 标准
- 内置 Google Test 测试框架配置
- 生成 CMakeLists.txt、.gitignore、.clang-format、README.md
- 支持自定义作者、许可证、输出目录

用法：
  python3 init_cpp_project.py --name my-project
  python3 init_cpp_project.py --name my-lib --type library
  python3 init_cpp_project.py --name my-header --type header-only
  python3 init_cpp_project.py --name my-project --std 20
  python3 init_cpp_project.py --name my-project --no-tests
  python3 init_cpp_project.py --name my-project --output /path/to/projects
  python3 init_cpp_project.py --name my-project --author "Your Name" --license MIT
"""

import argparse
import os
import re
import sys
from datetime import datetime


# ============================================================
# 工具函数
# ============================================================

def to_camel_case(name: str) -> str:
    """将 kebab-case 或 snake_case 转为 CamelCase"""
    parts = re.split(r'[-_]', name)
    return ''.join(p.capitalize() for p in parts)


def to_snake_case(name: str) -> str:
    """将 kebab-case 或 CamelCase 转为 snake_case"""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.replace('-', '_').lower()


def write_file(path: str, content: str, verbose: bool = True):
    """写入文件并创建父目录"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    if verbose:
        print(f"  创建: {path}")


# ============================================================
# CMakeLists.txt 模板
# ============================================================

def generate_top_cmake(name: str, project_type: str, cpp_std: str,
                        author: str, license: str, has_tests: bool) -> str:
    """生成顶层 CMakeLists.txt"""
    camel = to_camel_case(name)
    snake = to_snake_case(name)
    year = datetime.now().year

    lines = []
    lines.append("cmake_minimum_required(VERSION 3.14)")
    lines.append(f"project({name} VERSION 1.0.0 LANGUAGES CXX)")
    lines.append("")
    lines.append("# C++ 标准")
    lines.append(f"set(CMAKE_CXX_STANDARD {cpp_std})")
    lines.append("set(CMAKE_CXX_STANDARD_REQUIRED ON)")
    lines.append("set(CMAKE_CXX_EXTENSIONS OFF)")
    lines.append("")
    lines.append("# 构建类型")
    lines.append("if(NOT CMAKE_BUILD_TYPE)")
    lines.append("    set(CMAKE_BUILD_TYPE Release)")
    lines.append("endif()")
    lines.append("")
    lines.append("# 编译器警告选项")
    lines.append("if(CMAKE_CXX_COMPILER_ID MATCHES \"GNU|Clang\")")
    lines.append("    add_compile_options(")
    lines.append("        -Wall")
    lines.append("        -Wextra")
    lines.append("        -Wpedantic")
    lines.append("        -Wshadow")
    lines.append("        -Wnon-virtual-dtor")
    lines.append("    )")
    lines.append("elseif(MSVC)")
    lines.append("    add_compile_options(/W4 /permissive-)")
    lines.append("endif()")
    lines.append("")
    lines.append("# 输出目录")
    lines.append("set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)")
    lines.append("set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)")
    lines.append("set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)")
    lines.append("")

    if project_type == "executable":
        lines.append(f"# 可执行文件目标")
        lines.append(f"add_executable({name}")
        lines.append(f"    src/main.cpp")
        lines.append(f"    src/{snake}.cpp")
        lines.append(f")")
        lines.append(f"target_include_directories({name} PRIVATE include)")
        lines.append("")
    elif project_type == "library":
        lines.append(f"# 静态库目标")
        lines.append(f"add_library({name} STATIC")
        lines.append(f"    src/{snake}.cpp")
        lines.append(f")")
        lines.append(f"target_include_directories({name} PUBLIC include)")
        lines.append(f"target_compile_definitions({name} PRIVATE {snake.upper()}_EXPORTS)")
        lines.append("")
    elif project_type == "header-only":
        lines.append(f"# 头文件库目标（INTERFACE）")
        lines.append(f"add_library({name} INTERFACE)")
        lines.append(f"target_include_directories({name} INTERFACE include)")
        lines.append(f"target_compile_features({name} INTERFACE cxx_std_{cpp_std})")
        lines.append("")

    if has_tests:
        lines.append("# 单元测试")
        lines.append("enable_testing()")
        lines.append("add_subdirectory(tests)")
        lines.append("")

    lines.append("# 安装规则")
    if project_type == "executable":
        lines.append(f"install(TARGETS {name} RUNTIME DESTINATION bin)")
    elif project_type == "library":
        lines.append(f"install(TARGETS {name} ARCHIVE DESTINATION lib)")
        lines.append(f"install(DIRECTORY include/ DESTINATION include)")
    elif project_type == "header-only":
        lines.append(f"install(DIRECTORY include/ DESTINATION include)")
    lines.append("")

    return "\n".join(lines) + "\n"


def generate_test_cmake(name: str, project_type: str) -> str:
    """生成 tests/CMakeLists.txt"""
    snake = to_snake_case(name)

    lines = []
    lines.append("# Google Test 通过 FetchContent 获取")
    lines.append("include(FetchContent)")
    lines.append("FetchContent_Declare(")
    lines.append("    googletest")
    lines.append("    GIT_REPOSITORY https://github.com/google/googletest.git")
    lines.append("    GIT_TAG v1.14.0")
    lines.append(")")
    lines.append("# 防止 Google Test 覆盖父项目的编译器/链接器设置")
    lines.append("set(gtest_force_shared_crt ON CACHE BOOL \"\" FORCE)")
    lines.append("FetchContent_MakeAvailable(googletest)")
    lines.append("")
    lines.append(f"add_executable(tests test_{snake}.cpp)")
    lines.append(f"target_link_libraries(tests PRIVATE GTest::gtest_main)")

    if project_type in ("library", "header-only"):
        lines.append(f"target_link_libraries(tests PRIVATE {name})")
    elif project_type == "executable":
        # 可执行文件项目中，测试直接包含源文件
        lines.append(f"target_include_directories(tests PRIVATE ${{CMAKE_SOURCE_DIR}}/include)")
        lines.append(f"target_sources(tests PRIVATE ${{CMAKE_SOURCE_DIR}}/src/{snake}.cpp)")

    lines.append("")
    lines.append("include(GoogleTest)")
    lines.append("gtest_discover_tests(tests)")
    lines.append("")

    return "\n".join(lines) + "\n"


# ============================================================
# 源代码模板
# ============================================================

def generate_header(name: str, project_type: str) -> str:
    """生成头文件"""
    snake = to_snake_case(name)
    camel = to_camel_case(name)
    guard = f"{snake.upper()}_H"
    year = datetime.now().year
    is_header_only = (project_type == "header-only")

    lines = []
    lines.append(f"#ifndef {guard}")
    lines.append(f"#define {guard}")
    lines.append("")
    lines.append(f"/// @file {snake}.h")
    lines.append(f"/// @brief {camel} 工具类")
    lines.append(f"/// @author Auto-generated")
    lines.append(f"/// @date {year}")
    lines.append("")
    lines.append(f"namespace {snake} {{")
    lines.append("")
    lines.append(f"/**")
    lines.append(f" * @brief 示例工具类")
    lines.append(f" */")
    lines.append(f"class {camel} {{")
    lines.append("public:")
    lines.append(f"    {camel}() = default;")
    lines.append(f"    ~{camel}() = default;")
    lines.append("")
    lines.append(f"    /// @brief 示例方法")
    lines.append(f"    /// @param x 输入值")
    lines.append(f"    /// @return 计算结果")
    if is_header_only:
        lines.append(f"    int add(int x, int y) const {{ return x + y; }}")
    else:
        lines.append(f"    int add(int x, int y) const;")
    lines.append("")
    lines.append("private:")
    lines.append(f"    int value_ = 0;  ///< 示例成员变量")
    lines.append("};")
    lines.append("")
    lines.append(f"}}  // namespace {snake}")
    lines.append("")
    lines.append(f"#endif  // {guard}")
    lines.append("")

    return "\n".join(lines)


def generate_source(name: str, project_type: str) -> str:
    """生成源文件"""
    snake = to_snake_case(name)
    camel = to_camel_case(name)

    lines = []
    lines.append(f"#include \"{snake}/{snake}.h\"")
    lines.append("")
    lines.append(f"namespace {snake} {{")
    lines.append("")
    lines.append(f"int {camel}::add(int x, int y) const {{")
    lines.append("    return x + y;")
    lines.append("}")
    lines.append("")
    lines.append(f"}}  // namespace {snake}")
    lines.append("")

    return "\n".join(lines)


def generate_main(name: str) -> str:
    """生成 main.cpp"""
    snake = to_snake_case(name)
    camel = to_camel_case(name)

    lines = []
    lines.append(f"#include <iostream>")
    lines.append(f"#include \"{snake}/{snake}.h\"")
    lines.append("")
    lines.append("int main(int argc, char* argv[]) {")
    lines.append("    (void)argc;")
    lines.append("    (void)argv;")
    lines.append("")
    lines.append(f"    {snake}::{camel} app;")
    lines.append(f"    std::cout << \"{name} v1.0.0\" << std::endl;")
    lines.append(f"    std::cout << \"2 + 3 = \" << app.add(2, 3) << std::endl;")
    lines.append("")
    lines.append("    return 0;")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def generate_test(name: str, project_type: str) -> str:
    """生成测试文件"""
    snake = to_snake_case(name)
    camel = to_camel_case(name)

    lines = []
    lines.append("#include <gtest/gtest.h>")
    lines.append(f"#include \"{snake}/{snake}.h\"")
    lines.append("")
    lines.append(f"TEST({camel}Test, AddPositiveNumbers) {{")
    lines.append(f"    {snake}::{camel} obj;")
    lines.append("    EXPECT_EQ(obj.add(2, 3), 5);")
    lines.append("    EXPECT_EQ(obj.add(0, 0), 0);")
    lines.append("}")
    lines.append("")
    lines.append(f"TEST({camel}Test, AddNegativeNumbers) {{")
    lines.append(f"    {snake}::{camel} obj;")
    lines.append("    EXPECT_EQ(obj.add(-1, 1), 0);")
    lines.append("    EXPECT_EQ(obj.add(-5, -3), -8);")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# 配置文件模板
# ============================================================

def generate_gitignore() -> str:
    """生成 .gitignore"""
    return """# 构建目录
build/
cmake-build-*/
out/
bin/
lib/

# CMake
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
install_manifest.txt
compile_commands.json
CTestTestfile.cmake
_deps/

# 编译产物
*.o
*.obj
*.a
*.lib
*.so
*.dll
*.dylib
*.exe
*.out
*.app

# 调试文件
*.pdb
*.ilk
*.idb
*.suo
*.user
*.userosscache
*.sln.docstates

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# 测试覆盖率
*.gcno
*.gcda
coverage.info
coverage/

# 文档
docs/html/
docs/latex/
"""


def generate_clang_format() -> str:
    """生成 .clang-format"""
    return """---
Language: Cpp
BasedOnStyle: LLVM
IndentWidth: 4
TabWidth: 4
UseTab: Never
ColumnLimit: 100
AccessModifierOffset: -4
AlignAfterOpenBracket: Align
AlignConsecutiveAssignments: false
AlignConsecutiveDeclarations: false
AlignEscapedNewlines: Right
AlignOperands: true
AlignTrailingComments: true
AllowAllParametersOfDeclarationOnNextLine: true
AllowShortBlocksOnASingleLine: false
AllowShortCaseLabelsOnASingleLine: false
AllowShortFunctionsOnASingleLine: Inline
AllowShortIfStatementsOnASingleLine: false
AllowShortLoopsOnASingleLine: false
AlwaysBreakAfterDefinitionReturnType: None
AlwaysBreakAfterReturnType: None
AlwaysBreakBeforeMultilineStrings: true
BreakBeforeBinaryOperators: None
BreakBeforeBraces: Attach
BreakBeforeTernaryOperators: true
BreakConstructorInitializers: BeforeColon
CompactNamespaces: false
ConstructorInitializerAllOnOneLineOrOnePerLine: true
Cpp11BracedListStyle: true
DerivePointerAlignment: false
FixNamespaceComments: true
IncludeBlocks: Regroup
IndentCaseLabels: true
IndentPPDirectives: None
NamespaceIndentation: None
PointerAlignment: Left
ReflowComments: true
SortIncludes: true
SortUsingDeclarations: true
SpaceAfterCStyleCast: false
SpaceAfterTemplateKeyword: true
SpaceBeforeAssignmentOperators: true
SpaceBeforeParens: ControlStatements
SpaceInEmptyParentheses: false
SpacesBeforeTrailingComments: 2
SpacesInAngles: false
SpacesInContainerLiterals: true
SpacesInCStyleCastParentheses: false
SpacesInParentheses: false
Standard: c++17
...
"""


def generate_readme(name: str, project_type: str, cpp_std: str,
                     author: str, license: str, has_tests: bool) -> str:
    """生成 README.md"""
    camel = to_camel_case(name)
    year = datetime.now().year

    type_desc = {
        "executable": "可执行文件",
        "library": "静态库",
        "header-only": "头文件库",
    }

    lines = []
    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"> {camel} - C++{cpp_std} {type_desc.get(project_type, '项目')}")
    lines.append("")
    lines.append("## 特性")
    lines.append("")
    lines.append(f"- C++{cpp_std} 标准")
    lines.append("- CMake 构建系统")
    if has_tests:
        lines.append("- Google Test 单元测试")
    lines.append("- 跨平台支持（Linux / macOS / Windows）")
    lines.append("- 严格编译器警告")
    lines.append("")
    lines.append("## 项目结构")
    lines.append("")
    lines.append("```")
    lines.append(f"{name}/")
    lines.append("├── CMakeLists.txt      # 构建配置")
    lines.append("├── README.md             # 项目说明")
    lines.append("├── .gitignore            # Git 忽略规则")
    lines.append("├── .clang-format         # 代码格式化配置")
    lines.append("├── include/              # 公共头文件")
    if project_type == "executable":
        lines.append("├── src/                  # 源代码")
        lines.append("│   ├── main.cpp          # 入口文件")
    else:
        lines.append("├── src/                  # 源代码")
    if has_tests:
        lines.append("└── tests/                # 单元测试")
    lines.append("```")
    lines.append("")
    lines.append("## 快速开始")
    lines.append("")
    lines.append("### 依赖")
    lines.append("")
    lines.append("- CMake >= 3.14")
    lines.append(f"- 支持 C++{cpp_std} 的编译器（GCC 8+ / Clang 7+ / MSVC 2019+）")
    if has_tests:
        lines.append("- Git（用于下载 Google Test）")
    lines.append("")
    lines.append("### 构建")
    lines.append("")
    lines.append("```bash")
    lines.append("mkdir build && cd build")
    lines.append("cmake ..")
    lines.append("make -j$(nproc)")
    lines.append("```")
    lines.append("")
    if project_type == "executable":
        lines.append("### 运行")
        lines.append("")
        lines.append("```bash")
        lines.append(f"./bin/{name}")
        lines.append("```")
        lines.append("")
    if has_tests:
        lines.append("### 测试")
        lines.append("")
        lines.append("```bash")
        lines.append("cd build")
        lines.append("ctest --output-on-failure")
        lines.append("```")
        lines.append("")
    lines.append("## 许可证")
    lines.append("")
    if license and license.lower() != "none":
        lines.append(f"本项目采用 {license} 许可证。")
    else:
        lines.append("未指定许可证。")
    lines.append("")
    if author:
        lines.append(f"## 作者")
        lines.append("")
        lines.append(f"{author}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*由 cpp-project-init 自动生成于 {year}*")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="C++ 项目初始化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--name", "-n", required=True, help="项目名称")
    parser.add_argument("--type", "-t", default="executable",
                        choices=["executable", "library", "header-only"],
                        help="项目类型（默认 executable）")
    parser.add_argument("--std", "-s", default="17",
                        choices=["11", "14", "17", "20", "23"],
                        help="C++ 标准（默认 17）")
    parser.add_argument("--author", "-a", default="", help="作者名称")
    parser.add_argument("--license", "-l", default="MIT",
                        help="许可证（默认 MIT，填 none 不指定）")
    parser.add_argument("--output", "-o", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--no-tests", action="store_true", help="不包含单元测试")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制覆盖已存在的目录")
    args = parser.parse_args()

    # 验证项目名称
    if not re.match(r'^[a-z][a-z0-9-]*$', args.name):
        print("错误：项目名称只能包含小写字母、数字和连字符，且以字母开头",
              file=sys.stderr)
        sys.exit(1)

    has_tests = not args.no_tests
    project_dir = os.path.join(args.output, args.name)

    # 检查目录是否存在
    if os.path.exists(project_dir) and os.listdir(project_dir):
        if not args.force:
            print(f"错误：目录 {project_dir} 已存在且非空。使用 --force 覆盖。",
                  file=sys.stderr)
            sys.exit(1)

    snake = to_snake_case(args.name)
    print(f"正在创建 C++ 项目: {args.name}")
    print(f"  类型: {args.type}")
    print(f"  C++ 标准: {args.std}")
    print(f"  单元测试: {'是' if has_tests else '否'}")
    print(f"  输出目录: {project_dir}")
    print("")

    # 1. 顶层 CMakeLists.txt
    write_file(
        os.path.join(project_dir, "CMakeLists.txt"),
        generate_top_cmake(args.name, args.type, args.std,
                            args.author, args.license, has_tests)
    )

    # 2. README.md
    write_file(
        os.path.join(project_dir, "README.md"),
        generate_readme(args.name, args.type, args.std,
                         args.author, args.license, has_tests)
    )

    # 3. .gitignore
    write_file(os.path.join(project_dir, ".gitignore"), generate_gitignore())

    # 4. .clang-format
    write_file(os.path.join(project_dir, ".clang-format"), generate_clang_format())

    # 5. 头文件
    write_file(
        os.path.join(project_dir, "include", snake, f"{snake}.h"),
        generate_header(args.name, args.type)
    )

    # 6. 源文件
    if args.type != "header-only":
        write_file(
            os.path.join(project_dir, "src", f"{snake}.cpp"),
            generate_source(args.name, args.type)
        )

    # 7. main.cpp（仅可执行文件）
    if args.type == "executable":
        write_file(
            os.path.join(project_dir, "src", "main.cpp"),
            generate_main(args.name)
        )

    # 8. 测试文件
    if has_tests:
        write_file(
            os.path.join(project_dir, "tests", "CMakeLists.txt"),
            generate_test_cmake(args.name, args.type)
        )
        write_file(
            os.path.join(project_dir, "tests", f"test_{snake}.cpp"),
            generate_test(args.name, args.type)
        )

    print("")
    print("✅ 项目创建完成！")
    print("")
    print("构建命令：")
    print(f"  cd {args.name}")
    print("  mkdir build && cd build")
    print("  cmake ..")
    print("  make -j$(nproc)")
    if args.type == "executable":
        print(f"  ./bin/{args.name}")
    if has_tests:
        print("  ctest --output-on-failure")


if __name__ == "__main__":
    main()
