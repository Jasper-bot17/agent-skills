# Makefile 快速参考

> makefile-generator 技能配套指南。

---

## 一、常用 make 命令

| 命令 | 作用 |
|---|---|
| `make` | 默认编译（debug 模式） |
| `make debug` | 调试编译（带 `-g`，可 gdb 调试） |
| `make release` | 发布编译（`-O2` 优化） |
| `make run` | 编译后立即运行 |
| `make clean` | 删除 build/ 和可执行文件 |
| `make rebuild` | 清理后重新编译 |

---

## 二、编译选项说明

### Debug 模式
```
-std=c++17 -g -Wall -Wextra -O0 -I.
```
- `-g`：生成调试信息，配合 gdb 使用
- `-Wall -Wextra`：启用常用警告
- `-O0`：不优化，编译快
- `-I.`：包含当前目录头文件

### Release 模式
```
-std=c++17 -O2 -Wall -DNDEBUG -I.
```
- `-O2`：二级优化，运行快
- `-DNDEBUG`：禁用 assert 宏

---

## 三、gdb 调试示例

```bash
make debug
gdb ./myprogram
(gdb) break main
(gdb) run
(gdb) next
(gdb) print variable
(gdb) quit
```

---

## 四、常见问题

**Q: make: command not found**
- Ubuntu/Debian: `sudo apt install build-essential`
- macOS: 安装 Xcode Command Line Tools

**Q: 链接错误 undefined reference**
- 检查是否所有 .cpp 文件都在目录中
- 确认函数签名与头文件一致

**Q: 如何添加多线程**
```bash
python3 gen_makefile.py --extra-flags "-pthread"
```

---

*本指南由 makefile-generator 技能提供*
