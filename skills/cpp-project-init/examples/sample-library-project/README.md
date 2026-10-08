# demo-lib

> DemoLib - C++20 静态库

## 特性

- C++20 标准
- CMake 构建系统
- Google Test 单元测试
- 跨平台支持（Linux / macOS / Windows）
- 严格编译器警告

## 项目结构

```
demo-lib/
├── CMakeLists.txt      # 构建配置
├── README.md             # 项目说明
├── .gitignore            # Git 忽略规则
├── .clang-format         # 代码格式化配置
├── include/              # 公共头文件
├── src/                  # 源代码
└── tests/                # 单元测试
```

## 快速开始

### 依赖

- CMake >= 3.14
- 支持 C++20 的编译器（GCC 8+ / Clang 7+ / MSVC 2019+）
- Git（用于下载 Google Test）

### 构建

```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 测试

```bash
cd build
ctest --output-on-failure
```

## 许可证

本项目采用 MIT 许可证。

---

*由 cpp-project-init 自动生成于 2026*
