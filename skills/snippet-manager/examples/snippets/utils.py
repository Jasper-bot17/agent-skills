# Python 常用工具函数

# @snippet(title="计时器装饰器", desc="用于测量函数执行时间的装饰器", tags=["装饰器","工具","性能"])
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
# @end-snippet

# @snippet(title="读取大文件", desc="逐行读取大文件，避免内存溢出", tags=["文件","IO","性能"])
def read_large_file(filepath, encoding='utf-8'):
    with open(filepath, 'r', encoding=encoding) as f:
        for line in f:
            yield line.strip()
# @end-snippet

# @snippet
# title: 字典默认值
# desc: 安全获取字典值，支持默认值和嵌套访问
# tags: 字典,工具
def get_nested(d, keys, default=None):
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
# @end-snippet
