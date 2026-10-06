# 编译错误模式速查表

> 常见 GCC/Clang 编译错误模式、原因和修复方法速查。

---

## 语法错误

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `expected ';' before` | 缺少分号 | 检查上一行语句末尾 |
| `expected '}' at end of input` | 缺少右大括号 | 从后向前检查括号配对 |
| `stray '\xxx' in program` | 非法字符（中文标点） | 将中文标点替换为英文 |
| `expected primary-expression before` | 表达式不完整 | 确保运算符两侧有操作数 |
| `lvalue required as left operand` | 赋值号左侧不是变量 | 检查 = 左侧是否为可修改变量 |

## 声明与作用域错误

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `'xxx' was not declared in this scope` | 变量/函数未声明 | 检查拼写、头文件、std:: 前缀 |
| `'xxx' does not name a type` | 类型名错误或缺头文件 | 检查类型拼写，包含对应头文件 |
| `redefinition of` | 重复定义 | 头文件加 include guard，定义放 .cpp |
| `'xxx' is not a member of` | 类中无此成员 | 检查成员名拼写和访问权限 |
| `'xxx' is private` | 访问私有成员 | 添加 getter/setter 或改为 public |

## 类型错误

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `invalid conversion from` | 类型转换不合法 | 检查赋值/参数类型，使用显式转换 |
| `no matching function for call to` | 函数参数不匹配 | 检查参数数量和类型 |
| `ambiguous overload for` | 重载歧义 | 添加显式类型转换 |
| `cannot convert` | 类型无法转换 | 修改变量类型或添加转换 |
| `incompatible types in assignment` | 赋值类型不兼容 | 检查等号两侧类型 |

## 链接错误

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `undefined reference to` | 函数只有声明没有实现 | 确认实现存在且 .cpp 已编译 |
| `multiple definition of` | 重复定义 | 头文件只放声明，定义放 .cpp |
| `ld returned 1 exit status` | 链接失败汇总 | 查看上方具体链接错误 |

## 头文件错误

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `fatal error: xxx: No such file or directory` | 头文件不存在 | 检查拼写，确认库已安装，添加 -I 路径 |

## 常见警告

| 警告信息 | 原因 | 修复 |
|---|---|---|
| `unused variable` | 变量未使用 | 删除或添加 (void)x; |
| `control reaches end of non-void function` | 缺少 return | 确保所有分支有 return |
| `division by zero` | 除零 | 确保除数不为零 |
| `array subscript is above array bounds` | 数组越界 | 检查下标范围（0 到 size-1） |
| `format '%d' expects argument of type` | 格式不匹配 | 检查 %d/%s/%f 与参数类型 |
| `implicit declaration of function` | 函数未声明（C） | 添加前向声明或包含头文件 |
| `uninitialized use` | 变量未初始化 | 声明时立即赋初值 |

---

## 调试技巧

1. **从第一条错误开始修**：一个语法错误可能引发多条连锁错误
2. **修完重新编译**：不要试图一次修完所有错误
3. **注意行号偏移**：错误行号可能指向错误发生的下一行
4. **区分中英文标点**：中文分号（；）和英文分号（;）是不同的字符
5. **警告也要看**：某些警告可能导致运行时崩溃
6. **使用 -Wall -Wextra**：开启更多警告帮助发现潜在问题
7. **简化代码定位**：注释掉部分代码缩小错误范围

---

*速查表由 compile-error-decoder 技能提供*
