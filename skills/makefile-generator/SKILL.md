---
name: makefile-generator
description: "Makefile 生成器。自动扫描目录中的 C/C++ 源文件（.c/.cpp/.cc/.cxx），生成完整可用的 Makefile，支持 debug/release 双模式、自动编译器检测、头文件依赖、clean/run/install 目标。适用于学生作业、小型 C/C++ 项目快速构建。"
---

# Makefile 生成器（makefile-generator）

## 触发场景

当用户出现以下意图时使用本技能：

- "帮我生成 Makefile"
- "编译这个 C++ 项目"
- "没有 Makefile 怎么编译"
- "写个 Makefile"
- "C++ 项目构建"
- "make 命令怎么配置"
- "自动编译多个源文件"

## 核心功能

| 功能 | 说明 |
|---|---|
| 自动扫描 | 扫描目录下所有 .c/.cpp/.cc/.cxx 文件 |
| 编译器检测 | 自动选择 gcc/g++ |
| Debug 模式 | `-g -Wall -Wextra -O0`，带调试信息 |
| Release 模式 | `-O2 -Wall -DNDEBUG`，优化编译 |
| 头文件依赖 | 自动检测 .h/.hpp 目录 |
| 常用目标 | all、clean、run、debug、release |
| 自定义选项 | 支持指定输出文件名、附加编译参数 |
| 预览模式 | 先看生成内容再决定是否写入 |

## 使用方法

### 命令行工具

```bash
# 扫描当前目录并生成 Makefile
python3 scripts/gen_makefile.py

# 指定输出文件名
python3 scripts/gen_makefile.py -o Makefile

# 指定项目名/输出程序名
python3 scripts/gen_makefile.py --target myprogram

# 附加编译参数
python3 scripts/gen_makefile.py --extra-flags "-std=c++17 -pthread"

# 指定源文件目录
python3 scripts/gen_makefile.py --src-dir src

# 预览模式（不写入文件）
python3 scripts/gen_makefile.py --preview

# 指定语言（C 项目）
python3 scripts/gen_makefile.py --lang c
```

### 生成的 Makefile 用法

```bash
make            # 默认编译（debug 模式）
make debug      # 调试模式
make release    # 发布模式
make run        # 编译并运行
make clean      # 清理编译产物
make rebuild    # 重新编译
```

## 操作步骤

1. **扫描源文件**：在目标目录下查找 .c/.cpp/.cc/.cxx
2. **自动检测**：根据文件类型选择 gcc/g++，查找头文件目录
3. **生成 Makefile**：输出到当前目录
4. **验证**：提示用户运行 `make` 测试

## 注意事项

- 生成前如果已有 Makefile，会自动备份为 `Makefile.bak`
- 默认使用 C++17 标准
- 不递归扫描子目录（避免复杂项目）
