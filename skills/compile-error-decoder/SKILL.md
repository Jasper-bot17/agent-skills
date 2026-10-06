---
name: compile-error-decoder
description: '编译错误解码助手。解析 GCC/Clang 等编译器的错误输出，自动识别 50+ 种常见错误模式（语法错误、类型不匹配、未声明、链接错误、头文件缺失、警告等），用中文通俗解释每条错误的原因，给出具体的修复建议和代码示例，统计错误类型分布，标记高频易错点，生成学习笔记。适用于 C/C++ 初学者排查编译错误、理解报错信息、总结常见错误规律。'
---

# 编译错误解码助手

## 一、技能定位

本技能用于**解析和解释编译器错误输出**。核心价值：

- 自动识别 50+ 种 GCC/Clang 常见错误模式
- 用中文通俗解释每条错误的根本原因
- 给出具体的修复建议和代码对比示例
- 统计错误类型分布，找出薄弱环节
- 标记高频易错点，生成学习笔记
- 支持从文件读取编译输出或管道传入

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户粘贴编译报错信息，说「这是什么意思」「怎么改」
2. 用户说「帮我看看这个编译错误」「这个报错怎么解决」
3. 用户说「gcc 报错看不懂」「clang 错误解释一下」
4. 用户上传包含编译输出的文本文件
5. 用户说「总结一下我常犯的编译错误」
6. 用户说「这个 undefined reference 是什么」
7. 用户说「expected 开头的错误怎么修」

## 三、支持的错误类型

### 3.1 语法错误（Syntax）

| 错误模式 | 说明 |
|---|---|
| `expected ';' before` | 缺少分号 |
| `expected '}' at end of input` | 缺少右大括号 |
| `expected unqualified-id before` | 语法位置错误 |
| `expected primary-expression before` | 表达式不完整 |
| `expected constructor, destructor, or type conversion` | 函数定义语法错误 |
| `stray '\xxx' in program` | 非法字符（中文标点等） |

### 3.2 声明与作用域错误（Declaration/Scope）

| 错误模式 | 说明 |
|---|---|
| `was not declared in this scope` | 变量/函数未声明 |
| `does not name a type` | 类型名错误或缺少头文件 |
| `redefinition of` | 重复定义 |
| `previous declaration of` | 与之前声明冲突 |
| `is not a member of` | 类/命名空间中无此成员 |
| `'xxx' has not been declared` | 名称未声明 |

### 3.3 类型错误（Type）

| 错误模式 | 说明 |
|---|---|
| `invalid conversion from` | 类型转换不合法 |
| `no matching function for call to` | 函数参数不匹配 |
| `cannot convert` | 类型无法转换 |
| `ambiguous overload for` | 重载歧义 |
| `no type named in` | 类型不存在 |
| `incompatible types in assignment` | 赋值类型不兼容 |

### 3.4 链接错误（Linker）

| 错误模式 | 说明 |
|---|---|
| `undefined reference to` | 函数/变量未定义（只有声明没有实现） |
| `multiple definition of` | 重复定义 |
| `relocation truncated to fit` | 代码段过大（大模型问题） |
| `ld returned 1 exit status` | 链接失败汇总 |

### 3.5 头文件与文件错误（Header/File）

| 错误模式 | 说明 |
|---|---|
| `fatal error: xxx: No such file or directory` | 头文件不存在 |
| `error: xxx: Permission denied` | 文件权限不足 |
| `fatal error: too many errors emitted` | 错误过多停止编译 |

### 3.6 警告（Warning）

| 警告模式 | 说明 |
|---|---|
| `unused variable` | 变量声明未使用 |
| `unused function` | 函数定义未使用 |
| `control reaches end of non-void function` | 非 void 函数缺少 return |
| `division by zero` | 除零 |
| `array subscript is above array bounds` | 数组越界 |
| `format expects argument of type` | printf/scanf 格式不匹配 |
| `implicit declaration of function` | 函数隐式声明（C 语言） |
| `return type defaults to 'int'` | 返回类型默认 int（C 语言） |

## 四、操作步骤

### 步骤 1：获取编译输出

- 用户直接粘贴编译报错文本
- 或用户上传包含编译输出的文件
- 或通过管道传入：`g++ main.cpp 2>&1 | python3 decode_errors.py`

### 步骤 2：运行脚本

使用 `scripts/decode_errors.py`：

```bash
# 从文件读取编译输出
python3 scripts/decode_errors.py --file compile_output.txt

# 从标准输入读取
g++ main.cpp 2>&1 | python3 scripts/decode_errors.py

# 只显示错误（忽略警告）
python3 scripts/decode_errors.py --file output.txt --no-warnings

# 显示前 N 条错误
python3 scripts/decode_errors.py --file output.txt --limit 10

# JSON 格式输出
python3 scripts/decode_errors.py --file output.txt --format json

# 生成学习笔记
python3 scripts/decode_errors.py --file output.txt --notes
```

### 步骤 3：解读结果

- **错误统计**：错误/警告数量、类型分布
- **逐条解码**：原始错误、中文解释、修复建议、代码示例
- **高频易错点**：标记最常出现的错误类型
- **学习笔记**：总结错误规律和预防方法

### 步骤 4：安全提示

1. 本技能只解释错误，不自动修改代码
2. 修复建议仅供参考，请结合实际代码判断
3. 某些错误可能是由之前的错误连锁引起的，建议从第一条错误开始修
4. 警告也可能隐藏严重问题，不要忽视

## 五、输出规范

### 5.1 解码报告

```
🔍 编译错误解码报告
━━━━━━━━━━━━━━━━━━━━━━━━
源文件：compile_output.txt
错误数：3
警告数：2
编译器：GCC/Clang

📊 错误类型分布：
  语法错误：1 个
  声明错误：1 个
  链接错误：1 个

━━━━━━━━━━━━━━━━━━━━━━━━
❌ 错误 1/3（语法错误）
━━━━━━━━━━━━━━━━━━━━━━━━
📄 位置：main.cpp:5:18
📝 原始：error: expected ';' before '}' token
💡 中文解释：
  第 5 行第 18 列缺少分号。编译器在遇到 '}' 时期望前面有
  分号结尾，通常是上一行语句忘记写分号。
🔧 修复建议：
  检查第 5 行附近的语句，确保每条语句以分号结尾。
  错误示例：
    int x = 5    // ← 缺少分号
    }
  正确写法：
    int x = 5;   // ← 加上分号
    }

━━━━━━━━━━━━━━━━━━━━━━━━
❌ 错误 2/3（声明错误）
━━━━━━━━━━━━━━━━━━━━━━━━
📄 位置：main.cpp:8:5
📝 原始：error: 'cout' was not declared in this scope
💡 中文解释：
  'cout' 在当前作用域中未声明。cout 是 std 命名空间中的
  对象，需要包含 <iostream> 头文件并使用 std::cout 或
  using namespace std。
🔧 修复建议：
  1. 确保文件开头包含 #include <iostream>
  2. 使用 std::cout 代替 cout，或添加 using namespace std;
  错误示例：
    #include <iostream>
    int main() {
        cout << "hello";  // ← 缺少 std:: 前缀
    }
  正确写法：
    #include <iostream>
    int main() {
        std::cout << "hello";  // ← 加上 std:: 前缀
    }

━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  警告 1/2
━━━━━━━━━━━━━━━━━━━━━━━━
📄 位置：main.cpp:12:9
📝 原始：warning: unused variable 'x' [-Wunused-variable]
💡 中文解释：
  变量 'x' 声明了但从未使用。这可能是忘记使用，也可能
  是调试时遗留的代码。
🔧 修复建议：
  - 如果确实不需要，删除该变量声明
  - 如果需要使用，补充使用逻辑
  - 如果是有意保留，可加 (void)x; 消除警告

📚 学习笔记：
  本次编译最常见的错误类型是：语法错误
  建议重点复习：语句结尾分号、命名空间使用
  预防方法：
  1. 写完一行语句立即加分号
  2. 使用标准库函数前确认包含对应头文件
  3. 养成使用 std:: 前缀的习惯
```

## 六、常见场景处理

### 场景 1：初学者看不懂报错
**用户**：「这个 expected ';' before 是什么意思啊」
**处理**：解析错误 → 中文解释 → 给出代码对比示例 → 提醒检查上一行。

### 场景 2：大量错误不知从何下手
**用户**：「一下报了 20 个错误，怎么改」
**处理**：统计错误类型 → 指出第一条错误往往是根源 → 建议逐条修复重新编译。

### 场景 3：链接错误 undefined reference
**用户**：「undefined reference to 是什么，代码明明写了函数」
**处理**：解释声明与定义的区别 → 检查函数实现是否编译链接 → 检查函数签名是否一致。

### 场景 4：头文件找不到
**用户**：「fatal error: iostream: No such file or directory」
**处理**：检查头文件拼写 → 确认编译器是否正确安装 → 检查 include 路径。

### 场景 5：总结常犯错误
**用户**：「帮我总结一下我这些错误的规律」
**处理**：统计错误类型分布 → 标记高频错误 → 生成学习笔记和预防建议。

## 七、注意事项

1. **错误连锁反应**：一个语法错误可能引发后续多条错误，建议从第一条开始修，修完重新编译。
2. **警告不可忽视**：某些警告（如数组越界、除零）可能导致运行时崩溃。
3. **行号定位**：错误行号可能指向错误发生的下一行，需要结合上下文判断。
4. **编译器差异**：GCC 和 Clang 的错误信息格式略有不同，本技能兼容两种主要格式。
5. **中文标点**：代码中混入中文分号、引号会导致 `stray` 错误，注意区分中英文标点。
6. **不修改代码**：本技能只提供解释和建议，不自动修改用户代码。
7. **模式匹配局限**：无法匹配所有可能的错误信息，未匹配的错误会原样显示并标注"未识别模式"。
8. **C 与 C++**：部分错误（如 implicit declaration）只在 C 语言中出现，C++ 中会直接报错。
9. **模板错误**：C++ 模板错误信息通常很长且复杂，本技能会提取关键信息。
10. **建议仅供参考**：修复建议基于常见模式，具体修复需结合实际代码上下文。

## 八、文件结构

```
compile-error-decoder/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── error-patterns-reference.md       # 错误模式速查表
├── scripts/
│   └── decode_errors.py                  # 错误解码脚本（含 50+ 模式数据库）
└── examples/
    ├── sample-compile-output.txt          # 示例编译输出（含多种错误）
    └── sample-decode-report.md            # 示例解码报告
```

## 九、使用示例

### 示例 1：快速解码
**用户**：粘贴编译报错
**AI**：运行 `--file output.txt` → 输出逐条解码报告。

### 示例 2：管道传入
**用户**：「帮我看看编译结果」
**AI**：运行 `g++ main.cpp 2>&1 | python3 decode_errors.py` → 实时解码。

### 示例 3：生成学习笔记
**用户**：「总结一下这些错误」
**AI**：运行 `--notes` → 输出错误规律总结和预防建议。
