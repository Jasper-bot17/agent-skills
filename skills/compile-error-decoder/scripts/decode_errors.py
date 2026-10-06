#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
编译错误解码脚本

解析 GCC/Clang 编译输出，识别 50+ 种常见错误模式，
用中文解释原因并给出修复建议。

用法：
  python3 decode_errors.py --file compile_output.txt
  g++ main.cpp 2>&1 | python3 decode_errors.py
  python3 decode_errors.py --file output.txt --no-warnings
  python3 decode_errors.py --file output.txt --limit 10
  python3 decode_errors.py --file output.txt --format json
  python3 decode_errors.py --file output.txt --notes
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ============================================================
# 错误模式数据库
# ============================================================
# 每个模式：(regex, category, severity, explanation, fix, example)

ERROR_PATTERNS = [
    # --- 语法错误 ---
    (
        r"error:\s*expected\s+';'\s+before",
        "语法错误", "error",
        "缺少分号。编译器在遇到某个标记时期望前面有分号结尾，"
        "通常是上一行语句忘记写分号。",
        "检查错误位置附近的语句，确保每条语句以分号结尾。特别注意上一行。",
        "错误：int x = 5    // 缺少分号\n正确：int x = 5;   // 加上分号"
    ),
    (
        r"error:\s*expected\s+'}'\s+at\s+end\s+of\s+input",
        "语法错误", "error",
        "缺少右大括号。文件结束时仍有未闭合的大括号，通常是某个函数、"
        "循环或条件语句的 '}' 被遗漏。",
        "从文件末尾向前检查大括号配对，找到缺少 '}' 的位置。"
        "可以使用编辑器的括号匹配功能辅助定位。",
        "错误：if (x > 0) {\n        do_something();\n      // 缺少 }\n正确：if (x > 0) {\n        do_something();\n      }"
    ),
    (
        r"error:\s*expected\s+unqualified-id\s+before",
        "语法错误", "error",
        "语法位置错误。在期望出现标识符（变量名、函数名等）的位置出现了"
        "不合法的标记，通常是多余的符号或拼写错误。",
        "检查错误位置附近的语法，删除多余符号或修正拼写。",
        None
    ),
    (
        r"error:\s*expected\s+primary-expression\s+before",
        "语法错误", "error",
        "表达式不完整。在期望出现表达式（变量、常量、函数调用等）的位置"
        "出现了不合法的内容，通常是运算符后缺少操作数。",
        "检查错误位置，确保运算符两侧都有合法的操作数。",
        "错误：int x = + ;    // 运算符后缺少操作数\n正确：int x = 5 + 3;"
    ),
    (
        r"error:\s*expected\s+constructor,\s*destructor,\s*or\s+type\s+conversion",
        "语法错误", "error",
        "函数定义语法错误。通常是函数名拼写错误、返回类型缺失，"
        "或类名与构造函数名不匹配。",
        "检查函数定义的返回类型、函数名和参数列表是否正确。"
        "如果是构造函数，确保函数名与类名完全一致。",
        None
    ),
    (
        r"error:\s*stray\s+'[^']+'\s+in\s+program",
        "语法错误", "error",
        "程序中出现非法字符。最常见的原因是代码中混入了中文标点"
        "（中文分号、中文引号、中文逗号等）。",
        "检查错误位置，将中文标点替换为英文标点。特别注意分号、引号、逗号。",
        "错误：int x = 5；   // 中文分号\n正确：int x = 5;    // 英文分号"
    ),
    (
        r"error:\s*expected\s+expression",
        "语法错误", "error",
        "期望表达式但未找到。通常是括号内为空、函数调用缺少参数，"
        "或条件语句中缺少条件。",
        "检查错误位置，确保括号内有合法的表达式。",
        "错误：if () { }        // 条件为空\n正确：if (x > 0) { }"
    ),

    # --- 声明与作用域错误 ---
    (
        r"error:\s*'([^']+)'\s+was\s+not\s+declared\s+in\s+this\s+scope",
        "声明错误", "error",
        "变量或函数在当前作用域中未声明。可能的原因：①变量名拼写错误；"
        "②变量在其他作用域（如函数内）声明；③缺少 using 声明；"
        "④标准库对象缺少 std:: 前缀。",
        "1. 检查变量名拼写是否正确\n2. 确认变量声明的作用域是否包含使用位置\n"
        "3. 如果是标准库对象（cout/cin/string等），确保包含对应头文件并使用 std:: 前缀",
        "错误：cout << \"hello\";   // 缺少 std:: 前缀\n正确：std::cout << \"hello\";"
    ),
    (
        r"error:\s*'([^']+)'\s+does\s+not\s+name\s+a\s+type",
        "声明错误", "error",
        "类型名错误或缺少头文件。编译器不认识这个类型名，可能是：①类型名拼写错误；"
        "②缺少包含该类型定义的头文件；③自定义类型未定义或未包含。",
        "1. 检查类型名拼写\n2. 确认包含了定义该类型的头文件\n"
        "3. 如果是自定义类型，确保类/结构体定义在使用之前",
        "错误：string s;           // 缺少 <string> 头文件\n正确：#include <string>\n      std::string s;"
    ),
    (
        r"error:\s*redefinition\s+of",
        "声明错误", "error",
        "重复定义。同一个变量、函数或类被定义了多次。可能是：①头文件缺少 include guard 导致重复包含；"
        "②同一作用域内重复声明同名变量；③函数在头文件中定义而非声明。",
        "1. 检查是否有重复的定义\n2. 头文件添加 #ifndef/#define/#endif 或 #pragma once\n"
        "3. 头文件中只放声明，实现放在 .cpp 文件中",
        "错误：int x = 5;\n      int x = 10;   // 重复定义\n正确：int x = 5;\n      x = 10;      // 重新赋值"
    ),
    (
        r"error:\s*previous\s+declaration\s+of",
        "声明错误", "error",
        "与之前的声明冲突。当前声明与之前的声明不一致，通常是函数参数列表不同"
        "或变量类型不同。",
        "检查之前的声明位置，确保所有声明一致。如果是函数重载，确保参数列表有明显区别。",
        None
    ),
    (
        r"error:\s*'([^']+)'\s+is\s+not\s+a\s+member\s+of",
        "声明错误", "error",
        "类或命名空间中没有这个成员。可能是：①成员名拼写错误；②成员是私有的无法访问；"
        "③成员在基类中但继承方式为 private。",
        "1. 检查成员名拼写\n2. 确认成员的访问权限（public/protected/private）\n"
        "3. 检查继承方式是否正确",
        None
    ),
    (
        r"error:\s*'([^']+)'\s+has\s+not\s+been\s+declared",
        "声明错误", "error",
        "名称未声明。编译器不认识这个名称，可能是拼写错误、缺少头文件或作用域问题。",
        "检查名称拼写，确认包含了必要的头文件，确认名称在当前作用域内可见。",
        None
    ),
    (
        r"error:\s*'([^']+)'\s+was\s+not\s+declared\s+in\s+this\s+scope",
        "声明错误", "error",
        "名称在当前作用域未声明。同上，检查拼写、头文件和作用域。",
        "检查名称拼写，确认包含必要头文件，使用 std:: 前缀或 using 声明。",
        None
    ),

    # --- 类型错误 ---
    (
        r"error:\s*invalid\s+conversion\s+from",
        "类型错误", "error",
        "类型转换不合法。试图将一种类型转换为另一种不兼容的类型，"
        "例如将 int* 转为 int，或将 const char* 转为 char*。",
        "检查赋值或参数传递的类型是否匹配。如果确实需要转换，使用显式类型转换"
        "（static_cast 等），但要确保转换是安全的。",
        "错误：int* p = 5;         // 不能将 int 转为 int*\n正确：int x = 5;\n      int* p = &x;"
    ),
    (
        r"error:\s*no\s+matching\s+function\s+for\s+call\s+to",
        "类型错误", "error",
        "函数参数不匹配。调用函数时传入的参数类型/数量与函数声明不匹配。"
        "编译器会列出所有候选函数及其参数。",
        "1. 检查传入参数的数量是否正确\n2. 检查每个参数的类型是否匹配\n"
        "3. 查看编译器列出的候选函数，选择最合适的重载\n4. 必要时添加类型转换",
        "错误：void func(int x);\n      func(\"hello\");  // 参数类型不匹配\n正确：func(5);"
    ),
    (
        r"error:\s*cannot\s+convert",
        "类型错误", "error",
        "类型无法转换。两种类型之间不存在隐式转换路径。",
        "检查赋值或参数传递的类型，使用显式转换或修改数据类型。",
        None
    ),
    (
        r"error:\s*ambiguous\s+overload\s+for",
        "类型错误", "error",
        "重载歧义。多个重载函数都能匹配调用，编译器无法确定使用哪一个。",
        "1. 查看编译器列出的候选函数\n2. 添加显式类型转换以匹配特定重载\n"
        "3. 考虑修改函数签名减少歧义",
        None
    ),
    (
        r"error:\s*incompatible\s+types\s+in\s+assignment",
        "类型错误", "error",
        "赋值类型不兼容。等号左侧和右侧的类型无法匹配。",
        "检查赋值两侧的类型，修改变量类型或添加类型转换。",
        None
    ),
    (
        r"error:\s*no\s+type\s+named\s+'([^']+)'\s+in",
        "类型错误", "error",
        "指定的命名空间或类中不存在该类型。可能是类型名错误或缺少 using 声明。",
        "检查类型名拼写，确认类型在指定的命名空间/类中定义。",
        None
    ),

    # --- 链接错误 ---
    (
        r"undefined\s+reference\s+to",
        "链接错误", "error",
        "函数或变量未定义。代码中有声明（头文件中），但链接器找不到对应的实现（定义）。"
        "常见原因：①函数只声明未实现；②实现文件未加入编译；③函数签名（参数类型）与声明不一致；"
        "④C++ 函数在 C 文件中实现导致名字修饰不匹配。",
        "1. 确认函数/变量有对应的实现代码\n2. 确认实现文件（.cpp）已加入编译命令\n"
        "3. 检查函数签名（参数类型、const 修饰）是否与声明完全一致\n"
        "4. 如果是 C/C++ 混合，使用 extern \"C\" 包裹 C 函数声明",
        "// 声明（头文件）\nvoid func(int x);\n// 实现（.cpp 文件）— 必须存在且签名一致\nvoid func(int x) { /* ... */ }\n// 编译时必须包含实现文件：g++ main.cpp func.cpp"
    ),
    (
        r"multiple\s+definition\s+of",
        "链接错误", "error",
        "重复定义。同一个函数或变量在多个目标文件中都有定义。"
        "常见原因：①函数在头文件中定义（而非声明），被多个 .cpp 包含；"
        "②全局变量在头文件中定义；③同一个 .cpp 被多次编译链接。",
        "1. 将函数定义从头文件移到 .cpp 文件，头文件只放声明\n"
        "2. 全局变量在头文件中用 extern 声明，在 .cpp 中定义\n"
        "3. 检查编译命令，确保每个 .cpp 只编译一次",
        "// 头文件中：只声明\nvoid func();  // 声明，不是定义\n// .cpp 文件中：定义\nvoid func() { /* ... */ }"
    ),
    (
        r"relocation\s+truncated\s+to\s+fit",
        "链接错误", "error",
        "代码段过大，超出寻址范围。通常出现在大型程序中，"
        "32 位相对跳转无法到达目标地址。",
        "1. 使用 -mcmodel=large 编译选项（GCC）\n2. 将代码拆分为多个共享库\n"
        "3. 减少单个目标文件的大小",
        None
    ),
    (
        r"ld\s+returned\s+1\s+exit\s+status",
        "链接错误", "error",
        "链接失败汇总。这是链接器的总结性错误，真正的原因在上面的错误信息中"
        "（通常是 undefined reference 或 multiple definition）。",
        "向上滚动查看具体的链接错误信息，根据具体错误修复。本条本身不需要单独处理。",
        None
    ),

    # --- 头文件与文件错误 ---
    (
        r"fatal\s+error:\s*([^:]+):\s*No\s+such\s+file\s+or\s+directory",
        "头文件错误", "error",
        "头文件不存在。编译器找不到指定的头文件。可能原因：①头文件名拼写错误；"
        "②头文件未安装（标准库或第三方库）；③include 路径不正确；④自定义头文件路径错误。",
        "1. 检查头文件名拼写和大小写\n2. 确认库已正确安装\n"
        "3. 使用 -I 选项添加 include 路径\n4. 自定义头文件使用正确的相对路径或引号包含",
        "错误：#include <iostream.h>   // 旧风格头文件，不存在\n正确：#include <iostream>      // 标准 C++ 头文件"
    ),
    (
        r"error:\s*([^:]+):\s*Permission\s+denied",
        "文件错误", "error",
        "文件权限不足。无法读取或写入指定文件。",
        "检查文件权限，使用 chmod 修改权限，或以合适的用户身份运行。",
        None
    ),
    (
        r"fatal\s+error:\s*too\s+many\s+errors\s+emitted",
        "编译限制", "error",
        "错误过多，编译器停止输出。这不是新的错误，而是编译器达到了错误数量上限"
        "（默认 20 个）后停止报告。",
        "修复前面的错误后重新编译。可以使用 -fmax-errors=N 选项调整上限。",
        None
    ),

    # --- 警告 ---
    (
        r"warning:\s*unused\s+variable",
        "警告", "warning",
        "变量声明了但从未使用。可能是忘记使用，也可能是调试时遗留的代码。",
        "如果确实不需要，删除该变量声明；如果需要使用，补充使用逻辑；"
        "如果是有意保留，可加 (void)变量名; 消除警告。",
        "错误：int x = 5;   // x 从未使用\n修复：删除该行，或添加 (void)x;"
    ),
    (
        r"warning:\s*unused\s+function",
        "警告", "warning",
        "函数定义了但从未调用。可能是调试遗留代码，或函数声明在头文件中但未被使用。",
        "如果不需要，删除该函数；如果是库函数，可在头文件中声明而不报警告。",
        None
    ),
    (
        r"(?:warning|error):\s*control\s+reaches\s+end\s+of\s+non-void\s+function",
        "警告", "warning",
        "非 void 函数缺少 return 语句。函数声明了返回类型，但某些代码路径"
        "（特别是条件分支中）没有 return 语句。这会导致未定义行为！",
        "检查函数的所有代码路径，确保每个分支都有 return 语句。"
        "特别注意 if-else、switch 等条件语句。",
        "错误：int func(int x) {\n        if (x > 0) return 1;\n        // x <= 0 时没有 return\n      }\n正确：int func(int x) {\n        if (x > 0) return 1;\n        return 0;   // 添加默认 return\n      }"
    ),
    (
        r"warning:\s*division\s+by\s+zero",
        "警告", "warning",
        "检测到除零操作。除数为常量 0，这会导致运行时崩溃或未定义行为。",
        "检查除数，确保不会为零。如果除数是变量，添加除零检查。",
        "错误：int x = 5 / 0;   // 除零\n修复：确保除数不为零"
    ),
    (
        r"warning:\s*array\s+subscript\s+is\s+above\s+array\s+bounds",
        "警告", "warning",
        "数组下标越界。访问数组时使用了超出数组大小的下标，"
        "这会导致缓冲区溢出和未定义行为。",
        "检查数组下标，确保在 0 到 数组大小-1 的范围内。注意数组下标从 0 开始。",
        "错误：int arr[5];\n      arr[5] = 10;   // 越界，有效下标是 0-4\n正确：arr[4] = 10;"
    ),
    (
        r"warning:\s*format\s+'[^']+'\s+expects\s+argument\s+of\s+type",
        "警告", "warning",
        "printf/scanf 格式说明符与参数类型不匹配。例如用 %d 打印字符串，"
        "或用 %s 打印整数。这会导致未定义行为。",
        "检查格式说明符与对应参数的类型是否匹配。%d 对应 int，%s 对应 char*，"
        "%f 对应 double，%c 对应 char，%p 对应指针。",
        "错误：printf(\"%d\", \"hello\");  // %d 对应 int，传入了字符串\n正确：printf(\"%s\", \"hello\");"
    ),
    (
        r"warning:\s*implicit\s+declaration\s+of\s+function",
        "警告", "warning",
        "函数隐式声明（C 语言）。在 C 中调用未声明的函数时，编译器会假设其返回 int。"
        "在 C++ 中这会直接报错。",
        "在调用函数前包含声明该函数的头文件，或添加函数前向声明。",
        "错误：int main() {\n        func();   // func 未声明\n      }\n正确：void func();  // 前向声明\n      int main() {\n        func();\n      }"
    ),
    (
        r"warning:\s*return\s+type\s+defaults\s+to\s+'int'",
        "警告", "warning",
        "返回类型默认为 int（C 语言）。函数定义时未指定返回类型，"
        "C 语言默认返回 int。C++ 中不允许。",
        "显式指定函数返回类型，即使是 int 也要写出来。",
        "错误：func() { return 0; }   // 缺少返回类型\n正确：int func() { return 0; }"
    ),
    (
        r"warning:\s*suggest\s+parentheses\s+around",
        "警告", "warning",
        "建议添加括号。运算符优先级可能导致与预期不同的计算顺序。",
        "添加括号明确表达计算意图，提高代码可读性。",
        None
    ),
    (
        r"warning:\s*comparison\s+between\s+signed\s+and\s+unsigned",
        "警告", "warning",
        "有符号与无符号整数比较。这可能导致意外结果，因为有符号数会被转换为无符号数。",
        "确保比较两侧类型一致，使用显式转换，或使用相同类型的变量。",
        None
    ),
    (
        r"warning:\s*uninitialized\s+use",
        "警告", "warning",
        "使用了未初始化的变量。变量声明后未赋值就被使用，值是不确定的。",
        "在使用变量前进行初始化。声明时立即赋初值是好习惯。",
        "错误：int x; cout << x;   // x 未初始化\n正确：int x = 0; cout << x;"
    ),

    # --- 其他常见错误 ---
    (
        r"error:\s*'([^']+)'\s+undeclared\s+\(first\s+use\s+in\s+this\s+function\)",
        "声明错误", "error",
        "名称未声明（首次在该函数中使用）。同上，检查拼写、头文件和作用域。",
        "检查名称拼写，确认包含必要头文件，使用 std:: 前缀或 using 声明。",
        None
    ),
    (
        r"error:\s*lvalue\s+required\s+as\s+left\s+operand",
        "语法错误", "error",
        "赋值号左侧需要左值。左值是可以出现在赋值号左侧的表达式（变量、解引用指针等），"
        "不能是常量或临时值。",
        "检查赋值号左侧是否是可修改的变量。注意 ==（比较）和 =（赋值）的区别。",
        "错误：5 = x;   // 常量不能被赋值\n正确：x = 5;"
    ),
    (
        r"error:\s*invalid\s+use\s+of\s+non-static\s+member",
        "类型错误", "error",
        "非法使用非静态成员。在静态成员函数或没有对象实例的情况下访问了非静态成员。",
        "1. 如果是静态函数中访问非静态成员，需要传入对象实例\n"
        "2. 确认通过对象实例（obj.member）或指针（ptr->member）访问成员",
        None
    ),
    (
        r"error:\s*'([^']+)'\s+is\s+private",
        "声明错误", "error",
        "访问了私有成员。类的 private 成员只能在类内部访问，外部无法直接访问。",
        "1. 将成员改为 public（不推荐，破坏封装）\n2. 添加 public 的 getter/setter 函数\n"
        "3. 将访问代码移到类的成员函数或友元函数中",
        None
    ),
    (
        r"error:\s*expected\s+initializer\s+before",
        "语法错误", "error",
        "期望初始化表达式。变量声明时缺少初始化值，或语法结构不完整。",
        "检查变量声明，确保有正确的初始化值或使用默认构造。",
        None
    ),
    (
        r"error:\s*'operator\s+[^']+'\s+must\s+be\s+a\s+member\s+function",
        "类型错误", "error",
        "运算符必须是成员函数。某些运算符（如 =、()、[]、->）必须作为成员函数重载，"
        "不能作为全局函数。",
        "将该运算符重载移到类内部作为成员函数。",
        None
    ),
    (
        r"error:\s*template\s+argument",
        "类型错误", "error",
        "模板参数错误。模板实例化时传入的参数不满足模板要求。",
        "检查模板参数的类型和数量是否与模板声明匹配。",
        None
    ),
    (
        r"error:\s*'([^']+)'\s+does\s+not\s+have\s+class\s+type",
        "类型错误", "error",
        "对象不是类类型。对非类类型的变量使用了 . 或 -> 运算符访问成员。",
        "检查变量类型，确保它是类/结构体/联合体，或使用正确的访问方式。",
        "错误：int x; x.func();   // int 没有成员函数\n正确：定义类类型的对象"
    ),
    (
        r"error:\s*request\s+for\s+member\s+'([^']+)'\s+in",
        "类型错误", "error",
        "请求成员失败。在某个对象中找不到指定的成员，可能是成员名错误或对象类型不对。",
        "检查成员名拼写，确认对象类型确实有该成员。注意 . 和 -> 的使用区别。",
        None
    ),
    (
        r"error:\s*cannot\s+declare\s+variable\s+to\s+be\s+of\s+abstract\s+type",
        "类型错误", "error",
        "不能声明抽象类型的变量。类中有纯虚函数（=0）导致类成为抽象类，"
        "抽象类不能实例化。",
        "1. 在派生类中实现所有纯虚函数\n2. 使用指针或引用指向抽象类（多态）",
        None
    ),
    (
        r"error:\s*no\s+matching\s+function\s+for\s+call\s+to\s+'([^']+)'",
        "类型错误", "error",
        "构造函数调用不匹配。创建对象时传入的参数与任何构造函数都不匹配。",
        "检查构造函数的参数列表，确保传入参数的数量和类型匹配。",
        None
    ),
]


# ============================================================
# 编译输出行解析
# ============================================================

# GCC/Clang 错误行格式：
#   file:line:col: error: message
#   file:line: error: message
#   file:line:col: warning: message [-Wflag]
LINE_PATTERN = re.compile(
    r'^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+)?\s*:\s*'
    r'(?P<severity>error|warning|fatal error):\s*(?P<message>.+)$'
)

# 有些格式没有列号
LINE_PATTERN_NOCOL = re.compile(
    r'^(?P<file>[^:]+):(?P<line>\d+):\s*'
    r'(?P<severity>error|warning|fatal error):\s*(?P<message>.+)$'
)


class CompileIssue:
    """一条编译问题"""
    def __init__(self, file: str, line: int, col: Optional[int],
                 severity: str, message: str, raw_line: str):
        self.file = file
        self.line = line
        self.col = col
        self.severity = severity  # error / warning / fatal error
        self.message = message
        self.raw_line = raw_line
        self.category = "未识别"
        self.explanation = ""
        self.fix = ""
        self.example = None
        self.matched = False

    def match_pattern(self):
        """匹配错误模式"""
        # 构造包含 severity 的完整字符串用于匹配
        full_text = f"{self.severity}: {self.message}"
        for pattern, category, severity, explanation, fix, example in ERROR_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                self.category = category
                self.explanation = explanation
                self.fix = fix
                self.example = example
                self.matched = True
                return
        # 未匹配
        self.category = "其他"
        self.explanation = "未匹配到已知错误模式。请仔细阅读原始错误信息，" \
                           "或检查错误位置附近的代码语法。"
        self.fix = "1. 仔细阅读原始错误信息\n2. 检查错误行及附近代码\n" \
                   "3. 确认拼写、标点、括号配对\n4. 搜索错误关键词获取更多信息"
        self.matched = False


def parse_compile_output(text: str) -> List[CompileIssue]:
    """解析编译输出"""
    issues = []
    for line in text.split('\n'):
        line = line.rstrip()
        if not line:
            continue

        match = LINE_PATTERN.match(line)
        if not match:
            match = LINE_PATTERN_NOCOL.match(line)
        if match:
            severity = match.group('severity')
            if severity == 'fatal error':
                severity = 'error'

            issue = CompileIssue(
                file=match.group('file'),
                line=int(match.group('line')),
                col=int(match.group('col')) if match.group('col') else None,
                severity=severity,
                message=match.group('message'),
                raw_line=line,
            )
            issue.match_pattern()
            issues.append(issue)
            continue

        # 链接错误：undefined reference to / multiple definition of
        linker_match = re.search(r"(undefined reference to|multiple definition of)\s+`?([^']+)'?", line)
        if linker_match:
            # 尝试提取文件名
            file_match = re.match(r'^([^:]+):', line)
            issue = CompileIssue(
                file=file_match.group(1) if file_match else "(linker)",
                line=0,
                col=None,
                severity="error",
                message=f"error: {linker_match.group(0)}",
                raw_line=line,
            )
            issue.match_pattern()
            issues.append(issue)
            continue

        # collect2 链接错误汇总
        if 'ld returned' in line and 'error' in line:
            issue = CompileIssue(
                file="(linker)",
                line=0,
                col=None,
                severity="error",
                message="error: ld returned 1 exit status",
                raw_line=line,
            )
            issue.match_pattern()
            issues.append(issue)

    return issues


# ============================================================
# 输出格式化
# ============================================================

def format_report(issues: List[CompileIssue], limit: int = 0,
                  show_warnings: bool = True, show_notes: bool = False) -> str:
    """格式化解码报告"""
    errors = [i for i in issues if i.severity == 'error']
    warnings = [i for i in issues if i.severity == 'warning']

    if not show_warnings:
        display_issues = errors
    else:
        display_issues = issues

    if limit > 0:
        display_issues = display_issues[:limit]

    lines = []
    lines.append("🔍 编译错误解码报告")
    lines.append("━" * 40)
    lines.append(f"错误数：{len(errors)}")
    lines.append(f"警告数：{len(warnings)}")
    if not show_warnings:
        lines.append("（已忽略警告）")

    # 类型分布
    cat_counts = defaultdict(int)
    for i in issues:
        cat_counts[i.category] += 1
    if cat_counts:
        lines.append("")
        lines.append("📊 错误类型分布：")
        for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat}：{count} 个")

    # 逐条解码
    for idx, issue in enumerate(display_issues, 1):
        lines.append("")
        if issue.severity == 'error':
            lines.append(f"❌ 错误 {idx}/{len(display_issues)}（{issue.category}）")
        else:
            lines.append(f"⚠️  警告 {idx}/{len(display_issues)}（{issue.category}）")
        lines.append("━" * 40)

        # 位置
        if issue.col:
            lines.append(f"📄 位置：{issue.file}:{issue.line}:{issue.col}")
        else:
            lines.append(f"📄 位置：{issue.file}:{issue.line}")

        # 原始信息
        lines.append(f"📝 原始：{issue.severity}: {issue.message}")

        # 中文解释
        lines.append("💡 中文解释：")
        for expl_line in issue.explanation.split('\n'):
            lines.append(f"  {expl_line}")

        # 修复建议
        lines.append("🔧 修复建议：")
        for fix_line in issue.fix.split('\n'):
            lines.append(f"  {fix_line}")

        # 代码示例
        if issue.example:
            lines.append("📝 代码示例：")
            for ex_line in issue.example.split('\n'):
                lines.append(f"  {ex_line}")

    # 学习笔记
    if show_notes and issues:
        lines.append("")
        lines.append("📚 学习笔记")
        lines.append("━" * 40)

        # 最常见错误类型
        if cat_counts:
            top_cat = max(cat_counts.items(), key=lambda x: x[1])
            lines.append(f"本次最常见的错误类型：{top_cat[0]}（{top_cat[1]} 个）")

        # 未匹配的错误
        unmatched = [i for i in issues if not i.matched]
        if unmatched:
            lines.append(f"未识别模式：{len(unmatched)} 个（建议手动检查）")

        # 通用建议
        lines.append("")
        lines.append("💡 通用建议：")
        lines.append("  1. 从第一条错误开始修，修完重新编译")
        lines.append("  2. 一个语法错误可能引发多条连锁错误")
        lines.append("  3. 注意中英文标点区别，代码中必须用英文标点")
        lines.append("  4. 使用标准库前确认包含对应头文件")
        lines.append("  5. 警告也可能隐藏严重问题，不要忽视")
        lines.append("  6. 善用编辑器的语法高亮和括号匹配功能")
        lines.append("━" * 40)

    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="编译错误解码工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", help="编译输出文件路径（不指定则从标准输入读取）")
    parser.add_argument("--no-warnings", action="store_true", help="只显示错误，忽略警告")
    parser.add_argument("--limit", "-n", type=int, default=0, help="最多显示 N 条（0 表示全部）")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--notes", action="store_true", help="生成学习笔记")
    parser.add_argument("--output", "-o", metavar="FILE", help="输出到文件")
    args = parser.parse_args()

    # 读取输入
    if args.file:
        if not os.path.exists(args.file):
            print(f"错误：文件不存在：{args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    else:
        if sys.stdin.isatty():
            print("请通过 --file 指定文件，或通过管道传入编译输出：", file=sys.stderr)
            print("  g++ main.cpp 2>&1 | python3 decode_errors.py", file=sys.stderr)
            sys.exit(1)
        text = sys.stdin.read()

    if not text.strip():
        print("未检测到编译输出。", file=sys.stderr)
        sys.exit(0)

    # 解析
    issues = parse_compile_output(text)

    if not issues:
        print("✅ 未检测到编译错误或警告。编译成功！")
        return

    # 输出
    if args.format == 'json':
        data = {
            "total_errors": len([i for i in issues if i.severity == 'error']),
            "total_warnings": len([i for i in issues if i.severity == 'warning']),
            "issues": [
                {
                    "file": i.file,
                    "line": i.line,
                    "col": i.col,
                    "severity": i.severity,
                    "message": i.message,
                    "category": i.category,
                    "explanation": i.explanation,
                    "fix": i.fix,
                    "example": i.example,
                    "matched": i.matched,
                }
                for i in issues
            ]
        }
        output = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        output = format_report(issues, limit=args.limit,
                                show_warnings=not args.no_warnings,
                                show_notes=args.notes)

    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output + "\n")
        print(f"\n已保存到：{args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
