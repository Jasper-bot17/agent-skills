# C++ 编码规范与项目结构指南

> 适用于 C++11/14/17/20/23 项目开发。

---

## 一、项目结构规范

### 1.1 标准目录结构

```
project-name/
├── CMakeLists.txt          # 顶层构建配置
├── README.md               # 项目说明
├── LICENSE                 # 许可证文件
├── .gitignore              # Git 忽略规则
├── .clang-format           # 代码格式化配置
├── .clang-tidy             # 静态分析配置（可选）
├── docs/                   # 文档
├── include/                # 公共头文件
│   └── project_name/       # 按项目名组织
│       ├── api.h
│       └── utils.h
├── src/                    # 源代码
│   ├── main.cpp            # 入口文件（仅可执行文件）
│   ├── api.cpp
│   └── utils.cpp
├── tests/                  # 单元测试
│   ├── CMakeLists.txt
│   ├── test_api.cpp
│   └── test_utils.cpp
├── examples/               # 示例代码（可选）
├── third_party/            # 第三方依赖（可选）
└── cmake/                  # CMake 模块（可选）
```

### 1.2 命名规范

| 类型 | 规范 | 示例 |
|---|---|---|
| 项目名 | 小写字母+连字符 | `my-project` |
| 命名空间 | 小写字母+下划线 | `my_project` |
| 类名 | 大驼峰 | `MyClass` |
| 函数名 | 小驼峰 | `doSomething` |
| 变量名 | 小写下划线 | `my_variable` |
| 成员变量 | 小写下划线+尾下划线 | `member_var_` |
| 常量 | 全大写下划线 | `MAX_SIZE` |
| 枚举值 | 全大写下划线 | `RED_COLOR` |
| 头文件 | 小写下划线 | `my_class.h` |
| 源文件 | 小写下划线 | `my_class.cpp` |
| 头文件保护 | 全大写下划线+H | `MY_CLASS_H` |

### 1.3 头文件规范

```cpp
// 1. 使用 #ifndef 保护（不使用 #pragma once，兼容性更好）
#ifndef MY_CLASS_H
#define MY_CLASS_H

// 2. 包含标准库头文件
#include <string>
#include <vector>

// 3. 包含项目头文件
#include "my_project/other_class.h"

namespace my_project {

// 4. 类声明
class MyClass {
public:
    MyClass();
    ~MyClass();

    // 5. 公共接口
    void doSomething();
    int getValue() const;

private:
    // 6. 私有成员
    int value_;
};

}  // namespace my_project

#endif  // MY_CLASS_H
```

### 1.4 源文件规范

```cpp
// 1. 首先包含对应头文件
#include "my_project/my_class.h"

// 2. 然后包含标准库
#include <iostream>

// 3. 最后包含其他项目头文件
#include "my_project/helper.h"

namespace my_project {

MyClass::MyClass() : value_(0) {}

MyClass::~MyClass() = default;

void MyClass::doSomething() {
    // 实现
}

int MyClass::getValue() const {
    return value_;
}

}  // namespace my_project
```

---

## 二、CMake 最佳实践

### 2.1 基本配置

```cmake
cmake_minimum_required(VERSION 3.14)
project(my-project VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 默认构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 编译选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wshadow)
elseif(MSVC)
    add_compile_options(/W4 /permissive-)
endif()
```

### 2.2 目标配置

```cmake
# 可执行文件
add_executable(my-app src/main.cpp)
target_include_directories(my-app PRIVATE include)
target_link_libraries(my-app PRIVATE my-lib)

# 静态库
add_library(my-lib STATIC src/my_lib.cpp)
target_include_directories(my-lib PUBLIC include)

# 头文件库
add_library(my-header INTERFACE)
target_include_directories(my-header INTERFACE include)
```

### 2.3 测试配置

```cmake
enable_testing()

include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

add_executable(tests test_my_lib.cpp)
target_link_libraries(tests PRIVATE GTest::gtest_main my-lib)

include(GoogleTest)
gtest_discover_tests(tests)
```

### 2.4 安装配置

```cmake
include(GNUInstallDirs)

install(TARGETS my-lib
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
```

---

## 三、现代 C++ 特性使用

### 3.1 智能指针

```cpp
// 优先使用 std::unique_ptr
auto obj = std::make_unique<MyClass>();

// 共享所有权使用 std::shared_ptr
auto shared = std::make_shared<MyClass>();

// 避免使用裸指针拥有资源
// 不推荐: MyClass* obj = new MyClass();
```

### 3.2 移动语义

```cpp
// 优先使用移动而非拷贝
std::vector<int> createVector() {
    std::vector<int> v;
    v.push_back(1);
    return v;  // 自动移动或 NRVO
}

// 显式移动
std::vector<int> v1 = {1, 2, 3};
std::vector<int> v2 = std::move(v1);
```

### 3.3 类型推导

```cpp
// 使用 auto 简化类型声明
auto value = 42;
auto text = std::string("hello");

// 范围 for 循环
for (const auto& item : container) {
    // 使用 item
}
```

### 3.4 Lambda 表达式

```cpp
// 简单 lambda
auto add = [](int a, int b) { return a + b; };

// 捕获变量
int factor = 2;
auto multiply = [factor](int x) { return x * factor; };

// 泛型 lambda (C++14)
auto print = [](const auto& value) { std::cout << value; };
```

### 3.5 结构化绑定 (C++17)

```cpp
std::map<std::string, int> scores = {{"Alice", 95}, {"Bob", 87}};

for (const auto& [name, score] : scores) {
    std::cout << name << ": " << score << std::endl;
}

// 函数返回多值
auto [iter, inserted] = scores.insert({"Charlie", 90});
```

### 3.6 Concepts (C++20)

```cpp
template <typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

template <Addable T>
T add(T a, T b) {
    return a + b;
}
```

---

## 四、常见错误与陷阱

| 错误 | 说明 | 修正 |
|---|---|---|
| 头文件循环包含 | A.h 包含 B.h，B.h 包含 A.h | 使用前向声明 |
| 未初始化成员变量 | 构造函数未初始化所有成员 | 使用成员初始化列表 |
| 虚析构函数缺失 | 基类无虚析构函数导致内存泄漏 | 基类析构函数声明为 virtual |
| 切片问题 | 按值传递派生类对象 | 使用引用或指针 |
| 隐式类型转换 | 单参数构造函数导致隐式转换 | 使用 explicit 关键字 |
| 悬垂引用 | 返回局部变量的引用 | 按值返回或使用智能指针 |
| 迭代器失效 | 修改容器后使用旧迭代器 | 重新获取迭代器 |
| 未检查空指针 | 解引用可能为空的指针 | 使用断言或空指针检查 |
| 异常安全 | 构造函数中抛出异常导致资源泄漏 | 使用 RAII |
| 未定义行为 | 有符号整数溢出、空指针解引用等 | 避免未定义行为 |

---

## 五、编译与调试

### 5.1 常用编译选项

```bash
# Debug 构建
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 构建
cmake -DCMAKE_BUILD_TYPE=Release ..

# 启用地址消毒 (AddressSanitizer)
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address -g" ..

# 启用未定义行为消毒 (UBSan)
cmake -DCMAKE_CXX_FLAGS="-fsanitize=undefined -g" ..

# 生成编译数据库（用于 clangd 等工具）
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..
```

### 5.2 调试技巧

```bash
# 使用 gdb 调试
gdb ./my-app
(gdb) break main
(gdb) run
(gdb) print variable
(gdb) backtrace
(gdb) next
(gdb) step

# 使用 valgrind 检查内存泄漏
valgrind --leak-check=full ./my-app

# 使用 strace 跟踪系统调用
strace ./my-app
```

---

*规范参考由 cpp-project-init 技能提供*
