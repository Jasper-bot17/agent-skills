# Diff 快速参考指南

> text-diff 技能配套指南。

---

## 一、Diff 类型

| 类型 | 说明 | 适用场景 |
|---|---|---|
| 行级 diff | 整行比较，显示哪些行新增/删除/修改 | 代码对比、配置文件 |
| 词级 diff | 行内逐词比较 | 文档修订、小改动 |
| 字符级 diff | 逐字符比较 | 高精度对比 |

---

## 二、统一 diff 格式解读

```
--- 旧文件
+++ 新文件
@@ -1,3 +1,4 @@
 上下文行
-删除行
+新增行
 上下文行
```

- `@@ -旧起始行,旧行数 +新起始行,新行数 @@`：变更块位置
- `-`：旧文件有、新文件没有的行（删除）
- `+`：新文件有、旧文件没有的行（新增）
- 无前缀：两行相同的上下文行

---

## 三、常用命令

```bash
# 基本对比
python3 text_diff.py old.txt new.txt

# 并排显示
python3 text_diff.py old.txt new.txt --side-by-side

# 统一 diff 格式
python3 text_diff.py old.txt new.txt --unified

# 忽略空白和大小写
python3 text_diff.py old.txt new.txt -w -i

# 只看统计
python3 text_diff.py old.txt new.txt --stats-only

# JSON 输出（用于脚本）
python3 text_diff.py old.txt new.txt --json
```

---

## 四、相似度参考

| 相似度 | 含义 |
|---|---|
| 100% | 完全相同 |
| 90%+ | 高度相似，少量修改 |
| 70-90% | 有一定差异 |
| 50-70% | 差异较大 |
| <50% | 基本是不同文本 |

---

## 五、常见场景

### 代码版本对比
```bash
python3 text_diff.py v1.py v2.py --unified
```

### 配置文件变更检查
```bash
python3 text_diff.py config_old.yaml config_new.yaml
```

### 日志差异分析
```bash
python3 text_diff.py log_2024.txt log_2025.txt --stats-only
```

---

*本指南由 text-diff 技能提供*
