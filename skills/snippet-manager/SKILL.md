---
name: snippet-manager
description: '代码片段管理助手。扫描指定目录中的代码文件，自动提取带元数据标记的代码片段（标题、描述、标签、语言），按编程语言和分类组织，支持关键词和标签搜索，生成 Markdown 格式的片段库文档，导出 VS Code 片段格式（JSON），统计语言分布和标签云。适用于管理常用代码模板、算法模板、工具函数、学习笔记中的代码示例等场景。'
---

# 代码片段管理助手

## 一、技能定位

本技能用于**管理和组织代码片段**。核心价值：

- 自动扫描代码文件，提取带元数据标记的片段
- 按编程语言和分类自动组织
- 支持关键词和标签搜索
- 生成 Markdown 格式的片段库文档
- 导出 VS Code 片段格式（可直接导入编辑器）
- 统计语言分布和标签使用情况

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我整理一下这些代码片段」「管理代码模板」
2. 用户说「生成一个代码片段库」「把这些代码整理成文档」
3. 用户说「导出 VS Code 片段」「生成 .code-snippets 文件」
4. 用户说「搜索一下有没有某某功能的代码」「查找包含某标签的片段」
5. 用户说「统计一下我有哪些语言的代码片段」
6. 用户说「把常用算法模板整理一下」
7. 用户说「生成一个代码片段索引」

## 三、片段元数据格式

在代码文件中使用特殊注释标记片段：

### 3.1 单行标记（推荐）

```cpp
// @snippet(title="快速排序", desc="快速排序算法实现", tags=["排序","算法","分治"])
void quickSort(int arr[], int low, int high) {
    // ... 实现代码
}
// @end-snippet
```

### 3.2 多行标记

```python
# @snippet
# title: 二分查找
# desc: 在有序数组中查找目标值
# tags: 查找,算法,二分
# language: python
def binary_search(arr, target):
    # ... 实现代码
# @end-snippet
```

### 3.3 元数据字段说明

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | 是 | 片段标题，简洁描述功能 |
| `desc` | 否 | 片段详细描述 |
| `tags` | 否 | 标签列表，用于分类和搜索 |
| `language` | 否 | 编程语言（默认从文件扩展名推断） |
| `category` | 否 | 自定义分类 |

## 四、支持的功能

### 4.1 目录扫描

- 递归扫描指定目录
- 支持指定文件扩展名过滤
- 自动识别编程语言（从扩展名）
- 跳过二进制文件和过大文件
- 统计扫描进度

### 4.2 片段提取

- 识别 `@snippet` / `@end-snippet` 标记
- 解析单行和多行元数据格式
- 提取片段代码内容
- 自动推断语言（从文件扩展名）
- 记录片段所在文件和行号

### 4.3 搜索与过滤

- 按关键词搜索标题和描述
- 按标签过滤
- 按编程语言过滤
- 按分类过滤
- 支持多条件组合搜索

### 4.4 文档生成

- 生成 Markdown 格式的片段库
- 按语言/分类分组
- 包含标题、描述、标签、代码
- 生成目录索引
- 支持按标签生成索引

### 4.5 VS Code 导出

- 导出为 VS Code 片段格式（JSON）
- 每个片段包含 prefix、body、description
- 支持全局片段和语言特定片段
- 可直接放入 `.vscode/` 目录使用

### 4.6 统计分析

- 按编程语言统计片段数量
- 标签使用频率统计（标签云）
- 片段大小分布
- 按分类统计

## 五、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 扫描目录 / 搜索片段 / 生成文档 / 导出 VS Code 格式 / 统计
- 目标目录路径
- 搜索关键词或过滤条件
- 输出格式

### 步骤 2：运行脚本

使用 `scripts/manage_snippets.py`：

```bash
# 扫描目录并列出所有片段
python3 scripts/manage_snippets.py --dir /path/to/code

# 搜索包含关键词的片段
python3 scripts/manage_snippets.py --dir /path/to/code --search "排序"

# 按标签过滤
python3 scripts/manage_snippets.py --dir /path/to/code --tag "算法"

# 按语言过滤
python3 scripts/manage_snippets.py --dir /path/to/code --language python

# 生成 Markdown 片段库
python3 scripts/manage_snippets.py --dir /path/to/code --format markdown --output snippets.md

# 导出 VS Code 片段
python3 scripts/manage_snippets.py --dir /path/to/code --format vscode --output cpp.code-snippets

# 只扫描特定扩展名
python3 scripts/manage_snippets.py --dir /path/to/code --ext ".cpp,.h,.py"

# 显示统计信息
python3 scripts/manage_snippets.py --dir /path/to/code --stats

# JSON 格式输出
python3 scripts/manage_snippets.py --dir /path/to/code --format json
```

### 步骤 3：解读结果

- **片段列表**：标题、语言、标签、文件位置
- **搜索结果**：匹配的片段及匹配位置
- **Markdown 文档**：可直接使用的片段库文档
- **VS Code 片段**：可导入编辑器的 JSON 文件
- **统计信息**：语言分布、标签频率

### 步骤 4：安全提示

1. 本技能只读取和整理代码，不修改原始文件
2. 导出的片段文件请检查后再使用
3. 敏感代码（密钥、密码）不要放入片段库
4. 注意代码版权，不要分享未经授权的代码

## 六、输出规范

### 6.1 片段列表

```
📚 代码片段库
━━━━━━━━━━━━━━━━━━━━━━━━
扫描目录：/path/to/code
片段总数：12
语言分布：C++ 5个, Python 4个, JavaScript 3个

📋 片段列表：
  1. [C++] 快速排序 — 标签：排序,算法,分治
     文件：src/sort.cpp:15
  2. [Python] 二分查找 — 标签：查找,算法
     文件：utils/search.py:8
  3. [C++] 链表反转 — 标签：链表,数据结构
     文件：src/linkedlist.cpp:42
  ...
```

### 6.2 搜索结果

```
🔍 搜索结果：关键词「排序」
━━━━━━━━━━━━━━━━━━━━━━━━
找到 2 个匹配片段：

  1. [C++] 快速排序 — 标签：排序,算法,分治
     匹配：标题包含「排序」
     文件：src/sort.cpp:15
     ┌─ 代码预览 ──────────────
     │ void quickSort(int arr[], int low, int high) {
     │     if (low < high) {
     │         int pi = partition(arr, low, high);
     │         ...
     └──────────────────────────

  2. [Python] 归并排序 — 标签：排序,算法
     匹配：标题包含「排序」
     ...
```

### 6.3 Markdown 片段库

```markdown
# 代码片段库

## 目录

- [C++ 片段](#c-片段)
  - [快速排序](#快速排序)
  - [二分查找](#二分查找)
- [Python 片段](#python-片段)

---

## C++ 片段

### 快速排序

**描述**：快速排序算法实现，平均时间复杂度 O(n log n)

**标签**：排序、算法、分治

**文件**：src/sort.cpp:15

```cpp
void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}
```

---
```

### 6.4 VS Code 片段格式

```json
{
  "快速排序": {
    "prefix": "qsort",
    "body": [
      "void quickSort(int arr[], int low, int high) {",
      "    if (low < high) {",
      "        int pi = partition(arr, low, high);",
      "        quickSort(arr, low, pi - 1);",
      "        quickSort(arr, pi + 1, high);",
      "    }",
      "}"
    ],
    "description": "快速排序算法实现 [排序,算法,分治]"
  }
}
```

## 七、常见场景处理

### 场景 1：整理算法模板
**用户**：「帮我把常用算法模板整理成文档」
**处理**：扫描目录 → 提取所有带 @snippet 标记的算法代码 → 生成 Markdown 文档 → 按分类组织。

### 场景 2：导出 VS Code 片段
**用户**：「把这些 C++ 代码片段导出成 VS Code 能用的格式」
**处理**：扫描目录 → 过滤 C++ 片段 → 生成 .code-snippets JSON 文件 → 说明放置位置。

### 场景 3：搜索特定功能
**用户**：「有没有动态规划相关的代码片段」
**处理**：扫描目录 → 按标签「动态规划」过滤 → 显示匹配片段及代码预览。

### 场景 4：统计片段库
**用户**：「统计一下我收集了多少代码片段」
**处理**：扫描目录 → 统计语言分布、标签频率、片段大小 → 生成统计报告。

### 场景 5：新建片段库
**用户**：「我想开始整理代码片段，怎么弄」
**处理**：说明 @snippet 标记格式 → 提供模板 → 建议目录结构 → 演示扫描和生成流程。

## 八、注意事项

1. **标记格式**：必须使用 `@snippet` 开始和 `@end-snippet` 结束，两者成对出现。
2. **元数据解析**：支持单行 `@snippet(title="...", tags=[...])` 和多行键值对两种格式。
3. **语言推断**：未指定 language 时从文件扩展名推断，常见语言均支持。
4. **大文件跳过**：超过 1MB 的代码文件会被跳过，避免性能问题。
5. **嵌套片段**：不支持嵌套的 @snippet 标记，内层标记会被当作普通代码。
6. **编码问题**：默认使用 UTF-8 编码读取，其他编码可能出现乱码。
7. **不修改原文件**：本技能只读取和整理，不会修改任何原始代码文件。
8. **VS Code prefix**：导出时 prefix 从标题自动生成（拼音/英文），可手动调整。
9. **标签建议**：建议使用统一的标签体系（如：算法、数据结构、工具函数、模板），便于搜索和组织。
10. **增量更新**：每次扫描都是全量扫描，不支持增量更新；片段数量大时可能需要较长时间。

## 九、文件结构

```
snippet-manager/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── snippet-template.md                # 片段标记模板与示例
├── scripts/
│   └── manage_snippets.py                # 片段管理脚本
└── examples/
    ├── snippets/                          # 示例代码片段
    │   ├── quicksort.cpp                  # C++ 快速排序
    │   ├── binary_search.py               # Python 二分查找
    │   └── debounce.js                    # JavaScript 防抖函数
    └── sample-library.md                   # 示例生成的片段库
```

## 十、使用示例

### 示例 1：快速扫描
**用户**：「看看这个目录里有哪些代码片段」
**AI**：运行 `--dir /path/to/code` → 输出片段列表和统计。

### 示例 2：生成文档
**用户**：「把这些片段整理成 Markdown 文档」
**AI**：运行 `--format markdown --output snippets.md` → 生成可直接使用的文档。

### 示例 3：导出编辑器
**用户**：「导出成 VS Code 片段」
**AI**：运行 `--format vscode --output my.code-snippets` → 生成 JSON 文件，说明放入 `.vscode/` 目录。
