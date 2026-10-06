# 代码片段标记模板

> 使用以下格式在代码文件中标记可被 snippet-manager 识别的代码片段。

---

## 格式一：单行标记（推荐）

在片段开始行使用 `@snippet(...)` 内联元数据，结束行使用 `@end-snippet`。

### C/C++ 示例

```cpp
// @snippet(title="快速排序", desc="平均时间复杂度 O(n log n)", tags=["排序","算法"])
void quickSort(int arr[], int low, int high) {
    // ... 实现
}
// @end-snippet
```

### Python 示例

```python
# @snippet(title="计时器装饰器", desc="测量函数执行时间", tags=["装饰器","工具"])
def timer(func):
    # ... 实现
# @end-snippet
```

### JavaScript 示例

```javascript
// @snippet(title="防抖函数", desc="延迟执行函数", tags=["工具","性能"])
function debounce(fn, delay) {
    // ... 实现
}
// @end-snippet
```

---

## 格式二：多行标记

在 `@snippet` 后紧跟多行 `key: value` 元数据（每行需是注释），然后是代码，最后 `@end-snippet`。

```cpp
// @snippet
// title: 链表反转
// desc: 反转单链表，时间复杂度 O(n)
// tags: 链表,数据结构,指针
// language: cpp
ListNode* reverseList(ListNode* head) {
    // ... 实现
}
// @end-snippet
```

---

## 元数据字段说明

| 字段 | 必填 | 说明 | 示例 |
|---|---|---|---|
| `title` | 是 | 片段标题 | `title="快速排序"` |
| `desc` | 否 | 详细描述 | `desc="O(n log n) 排序算法"` |
| `tags` | 否 | 标签列表 | `tags=["排序","算法"]` |
| `language` | 否 | 编程语言（默认从扩展名推断） | `language="python"` |
| `category` | 否 | 自定义分类 | `category="算法模板"` |

---

## 最佳实践

1. **标题简洁**：用 2-6 个字概括功能，如「快速排序」「二分查找」
2. **标签统一**：建议使用统一标签体系（算法、数据结构、工具函数、模板、性能）
3. **描述有用**：包含时间/空间复杂度、使用场景等关键信息
4. **代码完整**：片段应可独立运行或清晰标注依赖
5. **注释规范**：片段内的关键步骤添加注释

---

## 目录结构建议

```
my-snippets/
├── algorithms/          # 算法模板
│   ├── sorting.cpp
│   ├── searching.cpp
│   └── dp.cpp
├── data-structures/     # 数据结构
│   ├── linkedlist.cpp
│   ├── tree.cpp
│   └── graph.cpp
├── utils/               # 工具函数
│   ├── common.py
│   └── io.cpp
└── templates/           # 代码模板
    ├── main.cpp
    └── class-template.cpp
```
