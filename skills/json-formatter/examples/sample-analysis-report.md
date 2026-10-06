# 示例：JSON 分析报告

> 本示例展示使用 `format_json.py` 对 `sample-data.json` 进行分析的输出。
> 示例数据为一个项目配置文件，包含嵌套对象、数组和多种数据类型。

---

## 基本信息

| 项目 | 值 |
|---|---|
| 文件 | sample-data.json |
| 大小 | 605 字节 |
| 校验状态 | ✅ 通过 |

---

## 结构统计

| 指标 | 值 |
|---|---|
| 总键数 | 33 |
| 最大嵌套深度 | 3 |
| 数组数量 | 3（长度：3, 3, 3） |
| 字符串 | 19 个 |
| 数字 | 6 个 |
| 布尔值 | 7 个 |
| 对象 | 8 个 |
| 数组 | 3 个 |

---

## 关键字段

| 字段路径 | 值 | 类型 |
|---|---|---|
| `name` | 示例项目 | string |
| `version` | 1.0.0 | string |
| `author.name` | 张三 | string |
| `config.debug` | true | boolean |
| `config.max_retries` | 3 | number |
| `users` | 数组（长度3） | array |
| `users[0].name` | 张三 | string |

---

## 表格转换（users 数组）

| id | name | role | active |
| --- | --- | --- | --- |
| 1 | 张三 | admin | True |
| 2 | 李四 | user | True |
| 3 | 王五 | user | False |

---

## 错误检测示例

对于以下错误 JSON：

```json
{"name": "张三" "age": 25}
```

输出：

```
❌ JSON 语法错误
错误位置：第 1 行，第 15 列
错误信息：Expecting ',' delimiter
错误内容：{"name": "张三" "age": 25}
                        ^
可能原因：可能缺少逗号，或括号/引号不匹配
```

---

## 差异比较示例

比较两个 JSON：

| 文件 A | 文件 B |
|---|---|
| name: 张三 | name: 张三 |
| age: 25 | age: 26 |
| city: 北京 | email: a@b.com |

输出：

```
➕ 新增（1项）：
  + email = "a@b.com"

➖ 删除（1项）：
  - city

✏️ 修改（1项）：
  ~ age: 25 → 26
```

---

*报告由 json-formatter 技能生成*
