---
name: text-diff
description: "文本对比工具。比较两段文本或两个文件的差异，支持统一 diff 格式、并排对比、逐行差异统计（新增/删除/修改行数）、相似度百分比、忽略空白/大小写选项、JSON 输出。适用于代码版本对比、配置文件变更检查、文档修订对比、日志差异分析等场景。纯 Python 标准库 difflib 实现。"
---

# 文本对比工具（text-diff）

## 触发场景

当用户出现以下意图时使用本技能：

- "比较这两段文本"
- "diff 一下"
- "看看这两个文件有什么区别"
- "对比两个版本"
- "这段代码改了什么"
- "配置文件变更"
- "文本差异"
- "新增了哪些行"
- "相似度多少"

## 核心功能

| 功能 | 说明 |
|---|---|
| 字符串对比 | 直接传入两段文本比较 |
| 文件对比 | 传入两个文件路径比较 |
| 统一 diff | 标准 unified diff 格式（`@@` 块、`+`/`-` 行） |
| 并排对比 | 左右两列并排显示，差异高亮 |
| 差异统计 | 新增行数、删除行数、修改行数、相似度百分比 |
| 忽略空白 | 比较时忽略行首行尾空白差异 |
| 忽略大小写 | 比较时不区分大小写 |
| 词级差异 | 在行内高亮具体哪些词不同 |
| JSON 输出 | 便于程序调用 |

## 使用方法

### 命令行工具

```bash
# 对比两个文件
python3 scripts/text_diff.py file1.txt file2.txt

# 对比两段字符串
python3 scripts/text_diff.py --str1 "第一行
第二行" --str2 "第一行
修改的行"

# 并排对比模式
python3 scripts/text_diff.py file1.txt file2.txt --side-by-side

# 忽略空白和大小写
python3 scripts/text_diff.py file1.txt file2.txt --ignore-whitespace --ignore-case

# JSON 输出
python3 scripts/text_diff.py file1.txt file2.txt --json

# 只看统计摘要
python3 scripts/text_diff.py file1.txt file2.txt --stats-only
```

### 作为模块调用

```python
from text_diff import TextDiffer

differ = TextDiffer()
result = differ.compare_files("old.txt", "new.txt")
print(f"相似度: {result['similarity']:.1f}%")
print(f"新增: {result['added']} 行, 删除: {result['removed']} 行")
print(result.unified_diff)
```

## 操作步骤

1. **获取对比内容**：用户提供两段文本或两个文件路径
2. **选择模式**：统一 diff（默认）或并排对比
3. **应用选项**：忽略空白、忽略大小写
4. **生成结果**：差异内容 + 统计
5. **展示**：高亮显示差异行，标注新增/删除/修改

## 输出规范

- 统一 diff 格式：`@@ start,count @@` 块头，`+` 绿色新增行，`-` 红色删除行，` ` 上下文行
- 并排对比：左列旧文本，右列新文本，差异行标注
- 统计摘要：新增行数、删除行数、修改行数、相似度百分比
- JSON：包含 added/removed/modified/similarity/diff_lines
