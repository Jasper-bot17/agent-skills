---
name: cpp-project-init
description: 'C++ 项目初始化助手。一键生成标准 C++ 项目结构，包含 CMakeLists.txt 构建配置、src/ 源码目录、include/ 头文件目录、tests/ 测试目录、.gitignore、README.md、.clang-format 等文件。支持三种项目类型（可执行文件/静态库/头文件库），支持 C++11/14/17/20/23 标准选择，内置 Google Test 测试框架配置，支持编译器选项、警告级别、构建类型配置。适用于快速搭建 C++ 项目脚手架、课程作业项目初始化、开源项目结构规范等场景。'
---

# C++ 项目初始化助手

## 一、技能定位

本技能用于**快速生成标准 C++ 项目脚手架**。核心价值：

- 一键生成完整项目结构（CMakeLists.txt、src/、include/、tests/）
- 三种项目类型：可执行文件、静态库、头文件库
- 支持 C++11/14/17/20/23 标准
- 内置 Google Test 测试框架配置
- 生成 .gitignore、.clang-format、README.md
- 编译器警告级别配置
- 构建类型配置（Debug/Release/RelWithDebInfo）

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「创建 C++ 项目」「初始化 C++ 工程」「搭建 C++ 项目结构」
2. 用户说「生成 CMakeLists.txt」「CMake 项目模板」
3. 用户说「C++ 课程作业项目」「算法项目初始化」
4. 用户说「C++ 静态库项目」「头文件库项目」
5. 用户说「C++ 单元测试配置」「Google Test 配置」
6. 用户说「C++ 项目规范」「C++ 项目结构最佳实践」

## 三、项目结构规范

### 3.1 可执行文件项目

```
my-project/
├── CMakeLists.txt          # 顶层构建配置
├── README.md               # 项目说明
├── .gitignore              # Git 忽略规则
├── .clang-format           # 代码格式化配置
├── include/                # 公共头文件
│   └── my_project/
│       └── utils.h
├── src/                    # 源代码
│   ├── main.cpp            # 入口文件
│   └── utils.cpp
└── tests/                  # 单元测试
    ├── CMakeLists.txt
    └── test_utils.cpp
```

### 3.2 静态库项目

```
my-library/
├── CMakeLists.txt
├── README.md
├── .gitignore
├── .clang-format
├── include/
│   └── my_library/
│       └── api.h
├── src/
│   └── api.cpp
└── tests/
    ├── CMakeLists.txt
    └── test_api.cpp
```

### 3.3 头文件库项目

```
my-header-only/
├── CMakeLists.txt
├── README.md
├── .gitignore
├── .clang-format
├── include/
│   └── my_header_only/
│       └── utils.h
└── tests/
    ├── CMakeLists.txt
    └── test_utils.cpp
```

## 四、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 项目名称
- 项目类型（可执行文件/静态库/头文件库）
- C++ 标准（11/14/17/20/23）
- 是否需要单元测试
- 输出目录

### 步骤 2：运行脚本

使用 `scripts/init_cpp_project.py`：

```bash
# 基本用法（可执行文件项目，C++17，含测试）
python3 scripts/init_cpp_project.py --name my-project

# 指定项目类型
python3 scripts/init_cpp_project.py --name my-lib --type library
python3 scripts/init_cpp_project.py --name my-header --type header-only

# 指定 C++ 标准
python3 scripts/init_cpp_project.py --name my-project --std 20

# 不包含测试
python3 scripts/init_cpp_project.py --name my-project --no-tests

# 指定输出目录
python3 scripts/init_cpp_project.py --name my-project --output /path/to/projects

# 指定作者
python3 scripts/init_cpp_project.py --name my-project --author "Your Name"

# 指定许可证
python3 scripts/init_cpp_project.py --name my-project --license MIT

# 完整配置
python3 scripts/init_cpp_project.py \
    --name my-project \
    --type executable \
    --std 17 \
    --author "Your Name" \
    --license MIT \
    --output /path/to/projects
```

### 步骤 3：构建项目

```bash
cd my-project
mkdir build && cd build
cmake ..
make -j$(nproc)

# 运行可执行文件
./my-project

# 运行测试（如果启用了测试）
ctest --output-on-failure
```

### 步骤 4：安全提示

1. 本技能只生成项目文件，不执行编译或安装
2. 生成的 CMakeLists.txt 为通用模板，复杂项目可能需要手动调整
3. Google Test 通过 FetchContent 下载，需要网络连接
4. 建议根据实际需求修改 README.md 和项目描述

## 五、CMake 配置说明

### 5.1 核心配置

```cmake
cmake_minimum_required(VERSION 3.14)
project(my-project VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 编译器警告
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wshadow -Wconversion)
endif()
```

### 5.2 目标配置

```cmake
# 可执行文件
add_executable(my-project src/main.cpp src/utils.cpp)
target_include_directories(my-project PRIVATE include)

# 静态库
add_library(my-library STATIC src/api.cpp)
target_include_directories(my-library PUBLIC include)

# 头文件库
add_library(my-header-only INTERFACE)
target_include_directories(my-header-only INTERFACE include)
```

### 5.3 测试配置

```cmake
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(tests test_utils.cpp)
target_link_libraries(tests PRIVATE GTest::gtest_main my-library)
include(GoogleTest)
gtest_discover_tests(tests)
```

## 六、常见场景处理

### 场景 1：课程作业项目
**用户**：「帮我创建一个 C++ 课程作业项目」
**处理**：生成可执行文件项目，C++17，含基本 main.cpp 和 .gitignore。

### 场景 2：算法竞赛项目
**用户**：「创建一个算法练习项目」
**处理**：生成可执行文件项目，C++17，关闭测试，添加常用头文件模板。

### 场景 3：开源库项目
**用户**：「创建一个 C++ 静态库项目，要支持单元测试」
**处理**：生成静态库项目，含 Google Test 配置，MIT 许可证，详细 README。

### 场景 4：头文件库项目
**用户**：「创建一个 header-only 的 C++ 工具库」
**处理**：生成头文件库项目，INTERFACE 库类型，含测试和示例。

### 场景 5：现代 C++ 项目
**用户**：「创建一个 C++20 项目」
**处理**：生成项目，C++20 标准，启用 concepts/ranges 相关警告。

## 七、注意事项

1. **CMake 版本**：生成的 CMakeLists.txt 要求 CMake 3.14 或更高版本。
2. **网络依赖**：Google Test 通过 FetchContent 下载，首次构建需要网络连接。
3. **编译器支持**：C++20/23 需要较新版本的 GCC（10+）、Clang（10+）或 MSVC（2019+）。
4. **项目命名**：项目名称建议使用小写字母和连字符，避免空格和特殊字符。
5. **目录冲突**：如果目标目录已存在且非空，脚本会提示并退出，不会覆盖已有文件。
6. **跨平台**：生成的 CMakeLists.txt 支持 Linux、macOS、Windows（MSYS2/MinGW/MSVC）。
7. **警告级别**：默认启用 -Wall -Wextra -Wpedantic，可根据需要调整。
8. **构建类型**：默认 Release，调试时使用 `-DCMAKE_BUILD_TYPE=Debug`。
9. **不修改系统**：本技能只在指定目录生成文件，不修改系统配置。
10. **手动调整**：复杂项目（多库依赖、自定义构建步骤）可能需要手动修改 CMakeLists.txt。

## 八、文件结构

```
cpp-project-init/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── cpp-style-guide.md                 # C++ 编码规范与项目结构指南
├── scripts/
│   └── init_cpp_project.py                # C++ 项目初始化脚本
└── examples/
    ├── sample-executable-project/         # 示例可执行文件项目
    ├── sample-library-project/            # 示例静态库项目
    └── sample-cmake-output.txt            # 示例 CMake 配置输出
```

## 九、使用示例

### 示例 1：快速创建
**用户**：「创建一个叫 hello 的 C++ 项目」
**AI**：运行 `--name hello` → 生成可执行文件项目（C++17，含测试）。

### 示例 2：静态库项目
**用户**：「创建一个 C++ 静态库项目，名字叫 math-lib，C++20」
**AI**：运行 `--name math-lib --type library --std 20` → 生成静态库项目。

### 示例 3：无测试项目
**用户**：「创建一个简单的 C++ 项目，不需要测试」
**AI**：运行 `--name simple --no-tests` → 生成不含测试目录的项目。
