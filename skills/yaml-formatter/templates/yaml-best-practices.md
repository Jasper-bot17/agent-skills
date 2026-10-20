# YAML 格式化与校验最佳实践

> yaml-formatter 技能配套指南。

---

## 一、YAML 语法常见错误

| 错误 | 原因 | 修复 |
|---|---|---|
| `mapping values are not allowed here` | 冒号后无空格或缩进错误 | 冒号后加空格，检查缩进 |
| `found character that cannot start any token` | 使用了 Tab 缩进 | 改用空格 |
| `duplicated mapping key` | 同层出现重复键 | 删除或重命名重复键 |
| `could not find expected ':'` | 列表项/字典缩进不一致 | 统一使用 2 空格缩进 |
| `expected <block end>, but found '<block start>'` | 列表和字典缩进层级混乱 | 对齐同级元素 |

---

## 二、缩进规范

```yaml
# ✅ 正确：统一 2 空格
key:
  child: value
  list:
    - item1
    - item2

# ❌ 错误：Tab 缩进
key:
→	child: value   # YAML 不允许 Tab

# ❌ 错误：缩进不一致
key:
   child: value   # 3 空格
    other: value  # 4 空格
```

---

## 三、多行字符串选择

| 场景 | 符号 | 行为 | 示例 |
|---|---|---|---|
| 保留换行 | `|` | 换行保留为 `\n` | Shell 脚本、代码块 |
| 折叠换行 | `>` | 换行折叠为空格 | 长文本段落 |
| 去除末尾换行 | `|-` | `|` 但去掉末尾换行 | 大多数文本 |
| 保留末尾换行 | `|+` | `|` 且保留更多空行 | 需要精确换行 |

```yaml
script: |
  echo "hello"
  echo "world"

description: >
  This is a long description
  that wraps across multiple lines
  but becomes one paragraph.
```

---

## 四、K8s 配置格式化建议

```bash
# 优先排列 apiVersion/kind/metadata
python3 format_yaml.py --input deployment.yaml \
  --sort-keys --priority apiVersion,kind,metadata,spec

# 批量格式化 manifests 目录
python3 format_yaml.py --dir ./manifests --in-place
```

---

## 五、YAML ↔ JSON 转换场景

| 场景 | 命令 |
|---|---|
| K8s YAML 转 JSON 调试 | `--to-json` |
| JSON 配置转 YAML 给 Docker Compose | `--to-yaml` |
| CI 中校验 YAML 语法 | `--check` |
| 提交前格式化 | `--in-place` |

---

## 六、批量处理建议

```bash
# 格式化整个项目的 YAML
python3 format_yaml.py --dir . --in-place --ext yaml,yml

# 仅校验（CI 中使用）
python3 format_yaml.py --dir ./config --check

# 排除目录：脚本会自动跳过 .开头的隐藏目录和 __pycache__
```

---

*本指南由 yaml-formatter 技能提供*
