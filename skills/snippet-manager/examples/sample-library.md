# 代码片段库

> 共 6 个代码片段

## 目录

- [C++ 片段](#c-片段)（3 个）
  - [快速排序](#快速排序)
  - [二分查找](#二分查找)
  - [链表反转](#链表反转)
- [Python 片段](#python-片段)（3 个）
  - [计时器装饰器](#计时器装饰器)
  - [读取大文件](#读取大文件)
  - [字典默认值](#字典默认值)

---

## C++ 片段

### 快速排序

**描述**：快速排序算法实现，平均时间复杂度 O(n log n)

**标签**：排序、算法、分治

**文件**：`/runtime/user_skills/snippet-manager/examples/snippets/algorithms.cpp:2`

```cpp
void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pivot = arr[high];
        int i = low - 1;
        for (int j = low; j < high; j++) {
            if (arr[j] <= pivot) {
                i++;
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;
        int pi = i + 1;
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}
```

---

### 二分查找

**描述**：在有序数组中查找目标值，时间复杂度 O(log n)

**标签**：查找、算法、二分

**文件**：`/runtime/user_skills/snippet-manager/examples/snippets/algorithms.cpp:25`

```cpp
int binarySearch(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
```

---

### 链表反转

**描述**：反转单链表，时间复杂度 O(n)

**标签**：链表、数据结构、指针

**文件**：`/runtime/user_skills/snippet-manager/examples/snippets/algorithms.cpp:38`

```cpp
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

ListNode* reverseList(ListNode* head) {
    ListNode* prev = nullptr;
    ListNode* curr = head;
    while (curr) {
        ListNode* next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
    }
    return prev;
}
```

---

## Python 片段

### 计时器装饰器

**描述**：用于测量函数执行时间的装饰器

**标签**：装饰器、工具、性能

**文件**：`/runtime/user_skills/snippet-manager/examples/snippets/utils.py:3`

```python
import time
from functools import wraps

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} 耗时: {elapsed:.4f}秒")
        return result
    return wrapper
```

---

### 读取大文件

**描述**：逐行读取大文件，避免内存溢出

**标签**：文件、IO、性能

**文件**：`/runtime/user_skills/snippet-manager/examples/snippets/utils.py:18`

```python
def read_large_file(filepath, encoding='utf-8'):
    with open(filepath, 'r', encoding=encoding) as f:
        for line in f:
            yield line.strip()
```

---

### 字典默认值

**描述**：安全获取字典值，支持默认值和嵌套访问

**标签**：字典、工具

**文件**：`/runtime/user_skills/snippet-manager/examples/snippets/utils.py:25`

```python
def get_nested(d, keys, default=None):
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
```

---

