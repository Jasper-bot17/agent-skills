---
name: yaml-formatter
description: "YAML 格式化与校验助手。格式化/压缩 YAML 文件，语法错误定位（行列号+原因），键值排序，多行字符串处理，YAML↔JSON 互转，K8s/Docker Compose/GitHub Actions 配置检查，重复键检测，锚点引用解析。纯 Python 标准库实现，无外部依赖。适用于编辑 YAML 配置、排查 YAML 语法错误、在 YAML 和 JSON 之间转换、批量格式化 YAML 文件等场景。"
---

# YAML 格式化与校验助手

## 触发场景

当用户出现以下意图时使用本技能：

- "格式化这个 YAML" / "整理一下 yaml" / "美化 yaml"
- "YAML 报错了" / "yaml 语法错误" / "yaml parse error" / "第X行列Y"
- "把 YAML 转 JSON" / "JSON 转 YAML"
- "压缩 YAML" / "单行输出 yaml"
- "检查 K8s 配置" / "检查 docker-compose" / "检查 GitHub Actions"
- "YAML 重复键" / "yaml duplicate key"
- "排序 yaml 的键"

## 核心功能

| 功能 | 说明 |
|---|---|
| 格式化 | 缩进规范化（默认2空格）、键值对齐、列表风格统一 |
| 压缩 | 单行 flow 风格输出 |
| 语法校验 | 定位错误行列号、错误原因、上下文提示 |
| YAML↔JSON | 双向转换 |
| 重复键检测 | 发现同层重复的键 |
| 键排序 | 按字母序或自定义优先级排序 |
| 配置检查 | K8s/Compose/Actions 常见结构检查 |
| 批量处理 | 递归目录批量格式化 |

## 使用方法

### 命令行工具

```bash
# 格式化 YAML 文件（原地修改）
python3 scripts/format_yaml.py --input config.yaml --in-place

# 格式化并输出到新文件
python3 scripts/format_yaml.py --input config.yaml --output formatted.yaml

# 语法校验（不修改文件，仅报告错误）
python3 scripts/format_yaml.py --input config.yaml --check

# 压缩为单行 flow 风格
python3 scripts/format_yaml.py --input config.yaml --compact

# YAML 转 JSON
python3 scripts/format_yaml.py --input config.yaml --to-json --output config.json

# JSON 转 YAML
python3 scripts/format_yaml.py --input config.json --to-yaml --output config.yaml

# 检测重复键
python3 scripts/format_yaml.py --input config.yaml --find-duplicates

# 按键名排序（K8s 常用顺序：apiKind 在前）
python3 scripts/format_yaml.py --input config.yaml --sort-keys --priority apiVersion,kind,metadata

# 批量处理目录下所有 .yaml/.yml
python3 scripts/format_yaml.py --dir ./configs --in-place --ext yaml,yml

# 自定义缩进（默认2空格）
python3 scripts/format_yaml.py --input config.yaml --indent 4
```

### 作为模块调用

```python
from format_yaml import format_yaml, validate_yaml, yaml_to_json

# 格式化
result = format_yaml("name: test\nvalue: 123")

# 校验
errors = validate_yaml("name: test\n  bad: indent")
for e in errors:
    print(f"行 {e['line']}, 列 {e['col']}: {e['message']}")

# YAML 转 JSON
json_str = yaml_to_json("name: test\nvalue: 123")
```

## 操作步骤

1. **确定输入**：用户提供 YAML 文件路径或直接粘贴 YAML 内容
2. **确定操作**：根据用户意图选择 format/check/convert/compact/sort/duplicates
3. **执行**：运行脚本，捕获输出
4. **报告结果**：
   - 格式化成功：展示结果摘要（行数、键数）
   - 校验失败：展示错误位置和原因，给出修复建议
   - 转换成功：展示输出文件路径
5. **如用户需要**：原地修改或输出到指定文件

## 输出规范

- 格式化输出使用 2 空格缩进
- 字符串优先使用纯文本风格（不加引号），仅在必要时加引号
- 多行字符串使用 `|`（保留换行）或 `>`（折叠换行）
- 列表使用 `- ` 短横线风格
- 键值之间冒号后保留一个空格
- 顶层文档之间用 `---` 分隔（多文档 YAML）

## 注意事项

- 纯 Python 标准库实现，不依赖 PyYAML（内置简易 YAML 解析器）
- 支持 YAML 1.2 常用语法：键值对、列表、嵌套、多行字符串、锚点 `&`/引用 `*`
- 不支持复杂的自定义类型标签（`!!python/object` 等）
- K8s 多文档 YAML（`---` 分隔）完整支持
- 校验时如果检测到 Tab 缩进会给出明确警告（YAML 不允许 Tab）
