---
name: json-formatter
description: 'JSON 校验与格式化助手。格式化/压缩 JSON、校验语法错误（指出错误行列）、提取指定字段（支持点路径）、转换 JSON 为 Markdown 表格、统计 JSON 结构（键数/嵌套深度/数组长度）、比较两个 JSON 差异。适用于 API 响应调试、配置文件检查、数据结构分析、JSON 数据处理等场景。'
---

# JSON 校验与格式化助手

## 一、技能定位

本技能用于**校验、格式化和分析 JSON 数据**。核心价值：

- 格式化：将压缩的 JSON 格式化为易读的缩进格式
- 压缩：将格式化的 JSON 压缩为单行
- 语法校验：检测 JSON 语法错误，指出错误行号和列号
- 字段提取：通过点路径（如 `data.items[0].name`）提取指定字段
- 转表格：将 JSON 数组转换为 Markdown 表格
- 结构统计：键数、嵌套深度、数组长度、数据类型分布
- 差异比较：比较两个 JSON 文件的差异

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我格式化一下这个 JSON」「这个 JSON 太乱了」
2. 用户说「这个 JSON 报错了，帮我看看哪里错了」
3. 用户说「帮我提取 JSON 里的某个字段」
4. 用户说「把这个 JSON 转成表格」
5. 用户说「帮我看看这个 JSON 的结构」
6. 用户说「压缩一下这个 JSON」
7. 用户说「比较这两个 JSON 有什么不同」
8. 用户提供 JSON 数据或文件，要求"处理""分析""检查"

## 三、支持的操作

### 3.1 格式化与压缩

| 操作 | 说明 |
|---|---|
| 格式化 | 2空格缩进，键排序可选，输出易读 JSON |
| 压缩 | 去除所有空格和换行，输出单行 JSON |
| 自定义缩进 | 支持 2/4 空格或 Tab 缩进 |

### 3.2 语法校验

| 检查项 | 说明 |
|---|---|
| 语法错误 | 括号不匹配、缺少逗号、多余逗号、字符串未闭合 |
| 错误定位 | 指出错误的行号和列号 |
| 错误建议 | 给出可能的修复建议 |

### 3.3 字段提取

支持点路径语法：

| 路径 | 说明 |
|---|---|
| `name` | 提取顶层键 name |
| `data.items` | 提取嵌套字段 |
| `data.items[0]` | 提取数组第一个元素 |
| `data.items[0].name` | 提取数组元素的字段 |
| `data.items[*].name` | 提取数组所有元素的 name 字段 |

### 3.4 结构统计

| 指标 | 说明 |
|---|---|
| 总键数 | JSON 中所有键的数量 |
| 最大嵌套深度 | 最深的嵌套层级 |
| 数组数量 | 数组的个数和各自长度 |
| 数据类型分布 | string/number/boolean/null/object/array 的数量 |
| 文件大小 | 格式化前后的字节数 |

### 3.5 转表格

将 JSON 数组（元素为对象）转换为 Markdown 表格，自动提取所有键作为列名。

### 3.6 差异比较

比较两个 JSON，输出：
- 新增的键
- 删除的键
- 值发生变化的键
- 数组长度变化

## 四、操作步骤

### 步骤 1：接收 JSON 数据

确认用户输入的 JSON 来源：
- 直接粘贴的 JSON 文本
- JSON 文件路径
- API 响应内容

### 步骤 2：运行处理脚本

使用 `scripts/format_json.py` 进行处理：

```bash
# 格式化 JSON
python3 scripts/format_json.py --file data.json --mode format

# 压缩 JSON
python3 scripts/format_json.py --file data.json --mode minify

# 校验语法
python3 scripts/format_json.py --file data.json --mode validate

# 提取字段
python3 scripts/format_json.py --file data.json --extract data.items[0].name

# 转换为表格
python3 scripts/format_json.py --file data.json --mode table

# 统计结构
python3 scripts/format_json.py --file data.json --mode stats

# 比较两个 JSON
python3 scripts/format_json.py --file a.json --diff b.json

# 从 stdin 读取
cat data.json | python3 scripts/format_json.py --mode format
```

### 步骤 3：解读结果

根据不同模式输出相应结果：

- **format**：输出格式化后的 JSON
- **validate**：输出校验结果（通过/失败+错误位置）
- **extract**：输出提取的字段值
- **table**：输出 Markdown 表格
- **stats**：输出结构统计报告
- **diff**：输出两个 JSON 的差异

### 步骤 4：与用户确认

1. 格式化结果是否符合预期？
2. 提取的字段是否正确？
3. 表格列是否需要调整？
4. 是否需要进一步处理？

## 五、输出规范

### 5.1 校验报告

```
✅ JSON 校验通过
━━━━━━━━━━━━━━━━━━
文件：data.json
大小：1,234 字节
顶层键数：5
最大嵌套深度：3
```

```
❌ JSON 语法错误
━━━━━━━━━━━━━━━━━━
文件：data.json
错误位置：第 5 行，第 12 列
错误信息：Expecting ',' delimiter
错误内容：  "name": "张三"
                     ^
可能原因：缺少逗号或括号不匹配
```

### 5.2 结构统计

```
📊 JSON 结构统计
━━━━━━━━━━━━━━━━━━
文件：data.json
大小：1,234 字节

📈 统计信息：
  总键数：15
  最大嵌套深度：4
  数组数量：3（长度分别为 10, 5, 2）
  字符串：8 个
  数字：4 个
  布尔值：2 个
  null：1 个
```

### 5.3 差异比较

```
🔍 JSON 差异比较
━━━━━━━━━━━━━━━━━━
文件 A：a.json
文件 B：b.json

新增（B 中有，A 中没有）：
  + data.new_field = "value"

删除（A 中有，B 中没有）：
  - data.old_field

修改：
  ~ data.name: "张三" → "李四"
  ~ data.age: 25 → 26
```

## 六、常见场景处理

### 场景 1：格式化 API 响应
**用户**：「这个 API 返回的 JSON 太乱了，帮我格式化一下」
**处理**：运行 format 模式 → 输出格式化后的 JSON。

### 场景 2：排查 JSON 错误
**用户**：「这个 JSON 解析报错了，帮我看看哪里错了」
**处理**：运行 validate 模式 → 指出错误行列 → 给出修复建议。

### 场景 3：提取数据
**用户**：「帮我从这个 JSON 里提取所有用户的名字」
**处理**：使用 --extract users[*].name → 输出所有名字。

### 场景 4：JSON 转表格
**用户**：「把这个 JSON 数组转成表格」
**处理**：运行 table 模式 → 输出 Markdown 表格。

### 场景 5：比较配置差异
**用户**：「帮我看看这两个配置文件有什么不同」
**处理**：运行 diff 模式 → 输出新增/删除/修改的键。

## 七、注意事项

1. **不修改原始文件**：处理结果输出到 stdout 或新文件，原始文件保持不变。
2. **大文件处理**：超过 10MB 的 JSON 文件可能需要较长时间，建议先提取需要的部分。
3. **编码假设**：假设文件为 UTF-8 编码。
4. **JSON5 不支持**：不支持注释、尾逗号等 JSON5 语法，仅支持标准 JSON。
5. **路径语法**：字段提取使用简单点路径，不支持完整 JSONPath 表达式。
6. **表格转换限制**：只有数组且元素为对象时才能转换为表格。
7. **差异比较深度**：递归比较所有嵌套层级，大文件可能较慢。
8. **数字精度**：Python 的 float 可能有精度问题，大数字建议用字符串。
9. **不替代专业工具**：复杂的 JSON 处理（如 JSON Schema 校验）建议使用专业库。
10. **隐私保护**：JSON 内容不离开本地，处理过程在本地完成。

## 八、文件结构

```
json-formatter/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── json-report-template.md            # JSON 分析报告模板
├── scripts/
│   └── format_json.py                    # JSON 处理脚本
└── examples/
    ├── sample-data.json                   # 示例：JSON 数据
    └── sample-analysis-report.md          # 示例：分析报告
```

## 九、使用示例

### 示例 1：格式化
**用户**：「帮我格式化这个 JSON」
**AI**：运行 format 模式 → 输出格式化后的 JSON。

### 示例 2：校验
**用户**：「这个 JSON 报错了，帮我看看」
**AI**：运行 validate 模式 → 指出错误位置和原因。

### 示例 3：提取
**用户**：「帮我提取 data.items 里所有 name 字段」
**AI**：运行 --extract data.items[*].name → 输出字段值列表。
