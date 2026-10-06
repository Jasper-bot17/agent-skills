#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
JSON 校验与格式化脚本

功能：
- 格式化/压缩 JSON
- 校验 JSON 语法（指出错误行列）
- 提取指定字段（点路径）
- 转换 JSON 为 Markdown 表格
- 统计 JSON 结构
- 比较两个 JSON 差异

用法：
  python3 format_json.py --file data.json --mode format
  python3 format_json.py --file data.json --mode minify
  python3 format_json.py --file data.json --mode validate
  python3 format_json.py --file data.json --extract data.items[0].name
  python3 format_json.py --file data.json --mode table
  python3 format_json.py --file data.json --mode stats
  python3 format_json.py --file a.json --diff b.json
  cat data.json | python3 format_json.py --mode format
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# JSON 解析与错误定位
# ============================================================

def parse_json_with_error(text: str) -> Tuple[Optional[Any], Optional[Dict]]:
    """解析 JSON，返回数据和错误信息（如果有）"""
    try:
        data = json.loads(text)
        return data, None
    except json.JSONDecodeError as e:
        error = {
            "message": e.msg,
            "line": e.lineno,
            "column": e.colno,
            "position": e.pos,
        }
        # 提取错误行内容
        lines = text.split('\n')
        if e.lineno <= len(lines):
            error["line_content"] = lines[e.lineno - 1]
        # 给出可能的原因
        error["suggestion"] = _suggest_fix(e.msg, text, e.pos)
        return None, error


def _suggest_fix(msg: str, text: str, pos: int) -> str:
    """根据错误信息给出修复建议"""
    if "Expecting ',' delimiter" in msg:
        return "可能缺少逗号，或括号/引号不匹配"
    if "Expecting property name" in msg:
        return "对象中缺少键名，或有多余的逗号"
    if "Expecting value" in msg:
        return "值格式不正确，检查是否有多余逗号或非法值"
    if "Unterminated string" in msg:
        return "字符串未闭合，检查引号是否配对"
    if "Extra data" in msg:
        return "JSON 根节点后有多余数据，确保只有一个根元素"
    if "Invalid control character" in msg:
        return "字符串中包含非法控制字符，可能需要转义"
    return "检查 JSON 语法是否正确"


# ============================================================
# 字段提取（点路径）
# ============================================================

def extract_field(data: Any, path: str) -> Tuple[Optional[Any], Optional[str]]:
    """通过点路径提取字段"""
    # 解析路径：支持 key, key.subkey, array[0], array[*].key
    parts = _parse_path(path)
    if parts is None:
        return None, f"无效的路径格式：{path}"

    current = data
    for part in parts:
        if current is None:
            return None, f"路径 {path} 在 {part} 处为 null"

        if part["type"] == "key":
            if isinstance(current, dict) and part["value"] in current:
                current = current[part["value"]]
            else:
                return None, f"键 {part['value']} 不存在"
        elif part["type"] == "index":
            if isinstance(current, list):
                idx = part["value"]
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None, f"数组索引 {idx} 越界（长度 {len(current)}）"
            else:
                return None, f"期望数组，但得到 {type(current).__name__}"
        elif part["type"] == "wildcard":
            # 通配符：提取数组所有元素的后续路径
            if not isinstance(current, list):
                return None, f"期望数组，但得到 {type(current).__name__}"
            # 剩余路径
            remaining = _path_to_string(parts[parts.index(part) + 1:])
            results = []
            for item in current:
                if remaining:
                    val, err = extract_field(item, remaining)
                    if err is None:
                        results.append(val)
                else:
                    results.append(item)
            return results, None

    return current, None


def _parse_path(path: str) -> Optional[List[Dict]]:
    """解析点路径为部件列表"""
    parts = []
    # 匹配 key, key[0], key[*]
    pattern = re.compile(r'([^.\[\]]+)(?:\[(\d+|\*)\])?')
    for match in pattern.finditer(path):
        key = match.group(1)
        index = match.group(2)
        if key:
            parts.append({"type": "key", "value": key})
        if index == "*":
            parts.append({"type": "wildcard", "value": "*"})
        elif index is not None:
            parts.append({"type": "index", "value": int(index)})
    return parts if parts else None


def _path_to_string(parts: List[Dict]) -> str:
    """将部件列表转回路径字符串"""
    result = []
    for part in parts:
        if part["type"] == "key":
            result.append(part["value"])
        elif part["type"] == "index":
            result[-1] = result[-1] + f"[{part['value']}]"
        elif part["type"] == "wildcard":
            result[-1] = result[-1] + "[*]"
    return ".".join(result)


# ============================================================
# 结构统计
# ============================================================

class JsonStats:
    """JSON 结构统计"""
    def __init__(self):
        self.total_keys = 0
        self.max_depth = 0
        self.arrays = []  # 数组长度列表
        self.type_counts = {"string": 0, "number": 0, "boolean": 0,
                            "null": 0, "object": 0, "array": 0}


def analyze_structure(data: Any, depth: int = 0, stats: Optional[JsonStats] = None) -> JsonStats:
    """递归分析 JSON 结构"""
    if stats is None:
        stats = JsonStats()

    stats.max_depth = max(stats.max_depth, depth)

    if data is None:
        stats.type_counts["null"] += 1
    elif isinstance(data, bool):
        stats.type_counts["boolean"] += 1
    elif isinstance(data, (int, float)):
        stats.type_counts["number"] += 1
    elif isinstance(data, str):
        stats.type_counts["string"] += 1
    elif isinstance(data, list):
        stats.type_counts["array"] += 1
        stats.arrays.append(len(data))
        for item in data:
            analyze_structure(item, depth + 1, stats)
    elif isinstance(data, dict):
        stats.type_counts["object"] += 1
        stats.total_keys += len(data)
        for value in data.values():
            analyze_structure(value, depth + 1, stats)

    return stats


# ============================================================
# JSON 转 Markdown 表格
# ============================================================

def json_to_table(data: Any) -> Optional[str]:
    """将 JSON 数组转换为 Markdown 表格"""
    if not isinstance(data, list):
        # 如果是对象，尝试取第一个数组值
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    data = value
                    break
            else:
                return None
        else:
            return None

    if not data or not isinstance(data[0], dict):
        return None

    # 收集所有键
    all_keys = []
    for item in data:
        if isinstance(item, dict):
            for key in item.keys():
                if key not in all_keys:
                    all_keys.append(key)

    # 生成表格
    lines = []
    lines.append("| " + " | ".join(all_keys) + " |")
    lines.append("| " + " | ".join(["---"] * len(all_keys)) + " |")
    for item in data:
        if isinstance(item, dict):
            row = []
            for key in all_keys:
                val = item.get(key, "")
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                row.append(str(val))
            lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


# ============================================================
# JSON 差异比较
# ============================================================

def compare_json(a: Any, b: Any, path: str = "") -> List[Dict]:
    """递归比较两个 JSON，返回差异列表"""
    diffs = []

    if type(a) != type(b):
        diffs.append({"type": "modify", "path": path or "(root)",
                      "old": a, "new": b})
        return diffs

    if isinstance(a, dict):
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        for key in a_keys - b_keys:
            diffs.append({"type": "delete", "path": f"{path}.{key}" if path else key,
                          "old": a[key]})
        for key in b_keys - a_keys:
            diffs.append({"type": "add", "path": f"{path}.{key}" if path else key,
                          "new": b[key]})
        for key in a_keys & b_keys:
            diffs.extend(compare_json(a[key], b[key],
                                      f"{path}.{key}" if path else key))
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append({"type": "modify", "path": path or "(root)",
                          "old": f"数组长度 {len(a)}", "new": f"数组长度 {len(b)}"})
        for i in range(min(len(a), len(b))):
            diffs.extend(compare_json(a[i], b[i], f"{path}[{i}]" if path else f"[{i}]"))
    else:
        if a != b:
            diffs.append({"type": "modify", "path": path or "(root)",
                          "old": a, "new": b})

    return diffs


# ============================================================
# 报告格式化
# ============================================================

def format_validate_report(error: Optional[Dict], filepath: str, size: int) -> str:
    """格式化校验报告"""
    lines = []
    if error is None:
        lines.append("✅ JSON 校验通过")
        lines.append("=" * 50)
        lines.append(f"文件：{os.path.basename(filepath) if filepath else '（stdin）'}")
        lines.append(f"大小：{size:,} 字节")
    else:
        lines.append("❌ JSON 语法错误")
        lines.append("=" * 50)
        lines.append(f"文件：{os.path.basename(filepath) if filepath else '（stdin）'}")
        lines.append(f"错误位置：第 {error['line']} 行，第 {error['column']} 列")
        lines.append(f"错误信息：{error['message']}")
        if "line_content" in error:
            lines.append(f"错误内容：{error['line_content']}")
            # 标记错误位置
            pointer = " " * (error['column'] - 1) + "^"
            lines.append(f"          {pointer}")
        lines.append(f"可能原因：{error['suggestion']}")
    return "\n".join(lines)


def format_stats_report(stats: JsonStats, filepath: str, size: int) -> str:
    """格式化统计报告"""
    lines = []
    lines.append("📊 JSON 结构统计")
    lines.append("=" * 50)
    lines.append(f"文件：{os.path.basename(filepath) if filepath else '（stdin）'}")
    lines.append(f"大小：{size:,} 字节")
    lines.append("")
    lines.append("📈 统计信息：")
    lines.append(f"  总键数：{stats.total_keys}")
    lines.append(f"  最大嵌套深度：{stats.max_depth}")
    if stats.arrays:
        arr_info = ", ".join(str(l) for l in stats.arrays[:10])
        if len(stats.arrays) > 10:
            arr_info += f" ...（共{len(stats.arrays)}个数组）"
        lines.append(f"  数组数量：{len(stats.arrays)}（长度：{arr_info}）")
    else:
        lines.append("  数组数量：0")
    lines.append("")
    lines.append("📦 数据类型分布：")
    for t, count in stats.type_counts.items():
        if count > 0:
            lines.append(f"  {t}：{count} 个")
    return "\n".join(lines)


def format_diff_report(diffs: List[Dict], file_a: str, file_b: str) -> str:
    """格式化差异报告"""
    lines = []
    lines.append("🔍 JSON 差异比较")
    lines.append("=" * 50)
    lines.append(f"文件 A：{os.path.basename(file_a)}")
    lines.append(f"文件 B：{os.path.basename(file_b)}")
    lines.append("")

    if not diffs:
        lines.append("✅ 两个 JSON 完全相同")
        return "\n".join(lines)

    adds = [d for d in diffs if d["type"] == "add"]
    deletes = [d for d in diffs if d["type"] == "delete"]
    modifies = [d for d in diffs if d["type"] == "modify"]

    if adds:
        lines.append(f"➕ 新增（{len(adds)}项）：")
        for d in adds:
            lines.append(f"  + {d['path']} = {json.dumps(d['new'], ensure_ascii=False)}")
        lines.append("")

    if deletes:
        lines.append(f"➖ 删除（{len(deletes)}项）：")
        for d in deletes:
            lines.append(f"  - {d['path']}")
        lines.append("")

    if modifies:
        lines.append(f"✏️ 修改（{len(modifies)}项）：")
        for d in modifies:
            old = json.dumps(d['old'], ensure_ascii=False)
            new = json.dumps(d['new'], ensure_ascii=False)
            lines.append(f"  ~ {d['path']}: {old} → {new}")
        lines.append("")

    lines.append(f"共发现 {len(diffs)} 处差异")
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="JSON 校验与格式化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", help="JSON 文件路径")
    parser.add_argument("--mode", "-m",
                        choices=["format", "minify", "validate", "table", "stats"],
                        default="format", help="运行模式（默认 format）")
    parser.add_argument("--indent", type=int, default=2, help="格式化缩进空格数（默认 2）")
    parser.add_argument("--sort-keys", action="store_true", help="格式化时按键名排序")
    parser.add_argument("--extract", "-e", help="提取指定字段（点路径）")
    parser.add_argument("--diff", "-d", help="与另一个 JSON 文件比较差异")
    parser.add_argument("--output", "-o", help="输出文件路径")
    args = parser.parse_args()

    # 获取文本
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
        args.file = None
    else:
        print("错误：请提供文件（--file）或通过 stdin 传入", file=sys.stderr)
        sys.exit(1)

    size = len(text.encode('utf-8'))

    # 差异比较模式
    if args.diff:
        data_a, error_a = parse_json_with_error(text)
        if error_a:
            print(format_validate_report(error_a, args.file or "", size))
            sys.exit(1)
        with open(args.diff, 'r', encoding='utf-8') as f:
            text_b = f.read()
        data_b, error_b = parse_json_with_error(text_b)
        if error_b:
            print(format_validate_report(error_b, args.diff, len(text_b.encode('utf-8'))))
            sys.exit(1)
        diffs = compare_json(data_a, data_b)
        print(format_diff_report(diffs, args.file or "", args.diff))
        return

    # 字段提取模式
    if args.extract:
        data, error = parse_json_with_error(text)
        if error:
            print(format_validate_report(error, args.file or "", size))
            sys.exit(1)
        result, err = extract_field(data, args.extract)
        if err:
            print(f"❌ 提取失败：{err}", file=sys.stderr)
            sys.exit(1)
        output = json.dumps(result, indent=args.indent, ensure_ascii=False)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ 已提取到：{args.output}", file=sys.stderr)
        else:
            print(output)
        return

    # 其他模式
    if args.mode == "validate":
        _, error = parse_json_with_error(text)
        print(format_validate_report(error, args.file or "", size))
        return

    # 需要解析的模式
    data, error = parse_json_with_error(text)
    if error:
        print(format_validate_report(error, args.file or "", size))
        sys.exit(1)

    if args.mode == "format":
        output = json.dumps(data, indent=args.indent, ensure_ascii=False,
                            sort_keys=args.sort_keys)
    elif args.mode == "minify":
        output = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    elif args.mode == "table":
        output = json_to_table(data)
        if output is None:
            print("❌ 无法转换为表格：数据不是对象数组", file=sys.stderr)
            sys.exit(1)
    elif args.mode == "stats":
        stats = analyze_structure(data)
        print(format_stats_report(stats, args.file or "", size))
        return
    else:
        output = ""

    # 输出
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ 已保存到：{args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
