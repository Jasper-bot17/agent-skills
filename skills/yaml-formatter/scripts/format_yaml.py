#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
YAML 格式化与校验助手

纯 Python 标准库实现，无外部依赖。
支持：格式化、校验、YAML↔JSON 转换、重复键检测、键排序、压缩输出。

用法：
  python3 format_yaml.py --input config.yaml --in-place
  python3 format_yaml.py --input config.yaml --check
  python3 format_yaml.py --input config.yaml --to-json --output config.json
  python3 format_yaml.py --input config.yaml --find-duplicates
  python3 format_yaml.py --dir ./configs --in-place
"""

import argparse
import json
import os
import re
import sys


# ============================================================
# 简易 YAML 解析器（仅支持常用语法）
# ============================================================

class YamlError(Exception):
    def __init__(self, message, line=0, col=0, context=""):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col
        self.context = context


def parse_scalar(s):
    """解析标量值"""
    s = s.strip()
    if s == "":
        return None
    if s in ("true", "True", "yes", "Yes", "on"):
        return True
    if s in ("false", "False", "no", "No", "off"):
        return False
    if s in ("null", "Null", "~", "None"):
        return None
    # 数字
    try:
        if s.startswith("0x"):
            return int(s, 16)
        if s.startswith("0o"):
            return int(s, 8)
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        pass
    # 去掉引号
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def parse_yaml(text):
    """解析 YAML 文本为 Python 数据结构。返回 (data, errors, duplicates)"""
    errors = []
    duplicates = []
    lines = text.split("\n")
    # 预处理：去除注释、空行，记录原始行号
    processed = []  # (indent, content, original_line_num)
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        # 多行字符串 | 或 >
        if stripped and (stripped.endswith("|") or stripped.endswith(">") or
                         stripped.endswith("|-") or stripped.endswith(">-") or
                         stripped.endswith("|+") or stripped.endswith(">+")):
            indent = len(raw) - len(raw.lstrip())
            key_part = stripped.rstrip("|>-+ ").rstrip()
            if key_part.endswith(":"):
                key = key_part[:-1].strip()
                processed.append((indent, ("multiline", key, stripped[-1]), i + 1))
                i += 1
                # 收集后续缩进的行
                content_lines = []
                while i < len(lines):
                    next_raw = lines[i]
                    if next_raw.strip() == "":
                        content_lines.append("")
                        i += 1
                        continue
                    next_indent = len(next_raw) - len(next_raw.lstrip())
                    if next_indent <= indent and next_raw.strip():
                        break
                    content_lines.append(next_raw)
                    i += 1
                # 计算公共缩进
                non_empty = [l for l in content_lines if l.strip()]
                if non_empty:
                    common = min(len(l) - len(l.lstrip()) for l in non_empty)
                    text_content = "\n".join(l[common:] if l.strip() else "" for l in content_lines)
                else:
                    text_content = ""
                processed.append((indent + 2, ("multiline_content", text_content), i))
                continue
        # 跳过空行、注释和文档分隔符 ---
        if stripped == "" or stripped.startswith("#") or stripped == "---":
            i += 1
            continue
        # 去掉行内注释（简单处理：不在引号内的 #）
        in_s = False
        in_d = False
        comment_pos = -1
        for ci, ch in enumerate(raw):
            if ch == "'" and not in_d:
                in_s = not in_s
            elif ch == '"' and not in_s:
                in_d = not in_d
            elif ch == "#" and not in_s and not in_d:
                comment_pos = ci
                break
        if comment_pos > 0:
            raw = raw[:comment_pos]
        indent = len(raw) - len(raw.lstrip())
        content = raw.strip()
        processed.append((indent, content, i + 1))
        i += 1

    if not processed:
        return None, errors, duplicates

    def parse_block(idx, base_indent):
        """从 processed[idx] 开始解析一个块，返回 (parsed_data, next_idx)"""
        if idx >= len(processed):
            return None, idx

        indent, content, orig_line = processed[idx]
        if indent < base_indent:
            return None, idx

        # 判断是列表还是字典
        is_list = content.startswith("- ") or content == "-"
        result = [] if is_list else {}
        seen_keys = {} if not is_list else None

        while idx < len(processed):
            indent, content, orig_line = processed[idx]
            if indent < base_indent:
                break
            if indent > base_indent:
                # 不应该发生（由递归处理）
                idx += 1
                continue

            if isinstance(content, tuple):
                kind = content[0]
                if kind == "multiline":
                    key = content[1]
                    # 下一行应该是 multiline_content
                    val = ""
                    if idx + 1 < len(processed) and isinstance(processed[idx + 1][1], tuple) \
                            and processed[idx + 1][1][0] == "multiline_content":
                        val = processed[idx + 1][1][1]
                        idx += 2
                    else:
                        idx += 1
                    if isinstance(result, dict):
                        if key in result:
                            duplicates.append((orig_line, key))
                        result[key] = val
                    continue

            if is_list:
                # 列表项
                item_content = content[2:].strip() if content.startswith("- ") else ""
                if item_content == "":
                    # 嵌套块
                    child, idx = parse_block(idx + 1, indent + 2)
                    result.append(child)
                    continue
                elif ":" in item_content and not item_content.startswith("{"):
                    # 字典列表项: "- key: value"
                    item_dict = {}
                    key_str, _, val_str = item_content.partition(":")
                    key_str = key_str.strip()
                    val_str = val_str.strip()
                    if val_str:
                        item_dict[key_str] = parse_scalar(val_str)
                        idx += 1
                        # 继续读取同级键（缩进 = indent + 2，即 "- " 之后的位置）
                        sibling_indent = indent + 2
                        while idx < len(processed):
                            s_indent, s_content, s_orig = processed[idx]
                            if s_indent != sibling_indent or s_indent < base_indent:
                                break
                            if isinstance(s_content, tuple):
                                break
                            if s_content.startswith("- "):
                                break
                            if ":" not in s_content:
                                break
                            s_key, _, s_val = s_content.partition(":")
                            s_key = s_key.strip()
                            s_val = s_val.strip()
                            if s_val:
                                item_dict[s_key] = parse_scalar(s_val)
                                idx += 1
                            else:
                                child, idx2 = parse_block(idx + 1, sibling_indent + 2)
                                item_dict[s_key] = child
                                idx = idx2
                    else:
                        child, idx2 = parse_block(idx + 1, indent + 2)
                        item_dict[key_str] = child
                        idx = idx2
                    result.append(item_dict)
                    continue
                else:
                    result.append(parse_scalar(item_content))
                    idx += 1
                    continue
            else:
                # 字典键值对
                if ":" not in content:
                    errors.append(f"行 {orig_line}: 缺少冒号分隔符: '{content}'")
                    idx += 1
                    continue
                key_str, _, val_str = content.partition(":")
                key_str = key_str.strip()
                val_str = val_str.strip()

                if seen_keys is not None and key_str in seen_keys:
                    duplicates.append((orig_line, key_str))
                if seen_keys is not None:
                    seen_keys[key_str] = orig_line

                if val_str == "":
                    # 嵌套块或空值
                    child, idx2 = parse_block(idx + 1, base_indent + 2)
                    result[key_str] = child
                    idx = idx2
                else:
                    result[key_str] = parse_scalar(val_str)
                    idx += 1
                continue

        return result, idx

    data, _ = parse_block(0, processed[0][0])
    return data, errors, duplicates


# ============================================================
# YAML 序列化器（Python 数据 → YAML 文本）
# ============================================================

def format_scalar(val):
    """将标量转为 YAML 表示"""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val)
    # 多行字符串
    if "\n" in s:
        return "|"
    # 需要引号的情况
    if s == "" or s.startswith((" ", "-", "?", ":", ",", "[", "]", "{", "}", "#", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`")):
        return f'"{s}"'
    if s.endswith(" ") or s.endswith("\t"):
        return f'"{s}"'
    if s.lower() in ("true", "false", "yes", "no", "on", "off", "null", "~"):
        return f'"{s}"'
    if re.match(r"^[\d.+-]+$", s):
        return f'"{s}"'
    return s


def dump_yaml(data, indent=0, indent_size=2, sort_keys=False, priority_keys=None):
    """将 Python 数据转为 YAML 文本"""
    lines = []
    prefix = " " * indent

    if isinstance(data, dict):
        if not data:
            return "{}"
        keys = list(data.keys())
        if sort_keys:
            if priority_keys:
                ordered = []
                for pk in priority_keys:
                    if pk in keys:
                        ordered.append(pk)
                        keys.remove(pk)
                keys = ordered + sorted(keys)
            else:
                keys = sorted(keys)
        for key in keys:
            val = data[key]
            if isinstance(val, (dict, list)) and val:
                lines.append(f"{prefix}{key}:")
                lines.append(dump_yaml(val, indent + indent_size, indent_size, sort_keys, priority_keys))
            elif isinstance(val, str) and "\n" in val:
                lines.append(f"{prefix}{key}: |")
                for dl in val.split("\n"):
                    lines.append(f"{' ' * (indent + indent_size)}{dl}")
            elif val is None:
                lines.append(f"{prefix}{key}: null")
            else:
                lines.append(f"{prefix}{key}: {format_scalar(val)}")
    elif isinstance(data, list):
        if not data:
            return "[]"
        for item in data:
            if isinstance(item, dict) and item:
                first = True
                for key, val in item.items():
                    if first:
                        if isinstance(val, (dict, list)) and val:
                            lines.append(f"{prefix}- {key}:")
                            lines.append(dump_yaml(val, indent + indent_size + 2, indent_size, sort_keys, priority_keys))
                        elif isinstance(val, str) and "\n" in val:
                            lines.append(f"{prefix}- {key}: |")
                            for dl in val.split("\n"):
                                lines.append(f"{' ' * (indent + indent_size + 2)}{dl}")
                        else:
                            lines.append(f"{prefix}- {key}: {format_scalar(val)}")
                        first = False
                    else:
                        if isinstance(val, (dict, list)) and val:
                            lines.append(f"{prefix}  {key}:")
                            lines.append(dump_yaml(val, indent + indent_size + 2, indent_size, sort_keys, priority_keys))
                        elif val is None:
                            lines.append(f"{prefix}  {key}: null")
                        else:
                            lines.append(f"{prefix}  {key}: {format_scalar(val)}")
            elif isinstance(item, list) and item:
                lines.append(f"{prefix}-")
                lines.append(dump_yaml(item, indent + indent_size, indent_size, sort_keys, priority_keys))
            else:
                lines.append(f"{prefix}- {format_scalar(item)}")
    else:
        return f"{prefix}{format_scalar(data)}"

    return "\n".join(lines)


def compact_yaml(data):
    """生成单行 flow 风格 YAML"""
    if isinstance(data, dict):
        if not data:
            return "{}"
        items = []
        for k, v in data.items():
            items.append(f"{k}: {compact_yaml(v)}")
        return "{" + ", ".join(items) + "}"
    if isinstance(data, list):
        if not data:
            return "[]"
        return "[" + ", ".join(compact_yaml(v) for v in data) + "]"
    return format_scalar(data)


# ============================================================
# 校验
# ============================================================

def validate_yaml_text(text):
    """校验 YAML 文本，返回错误列表"""
    errors = []
    lines = text.split("\n")

    for i, line in enumerate(lines, 1):
        # 检查 Tab 缩进
        if "\t" in line[:len(line) - len(line.lstrip())]:
            errors.append({"line": i, "col": 1, "message": "YAML 不允许使用 Tab 缩进，请用空格"})
        stripped = line.strip()
        # 跳过空行、注释和文档分隔符
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        # 检查冒号后是否有空格（key: value 格式）
        if ":" in stripped and not stripped.startswith("-"):
            key_part = stripped.split(":", 1)[0]
            rest = stripped.split(":", 1)[1]
            if rest and not rest.startswith(" ") and not rest.startswith("#"):
                errors.append({"line": i, "col": line.index(":") + 1,
                               "message": "冒号后应有一个空格，如 'key: value'"})
        # 检查列表项格式
        if stripped.startswith("-") and len(stripped) > 1 and stripped[1] not in (" ", "\t"):
            errors.append({"line": i, "col": 2, "message": "列表短横线后应有一个空格，如 '- item'"})

    # 尝试解析（按文档分别检测重复键）
    try:
        doc_texts = split_documents(text)
        for doc_text in doc_texts:
            if not doc_text.strip():
                continue
            data, parse_errors, duplicates = parse_yaml(doc_text)
            for pe in parse_errors:
                errors.append({"line": 0, "col": 0, "message": pe})
            for dup_line, dup_key in duplicates:
                errors.append({"line": dup_line, "col": 0,
                               "message": f"重复键 '{dup_key}'（YAML 中后出现的键会覆盖前面的）"})
    except YamlError as e:
        errors.append({"line": e.line, "col": e.col, "message": e.message})

    return errors


# ============================================================
# JSON 转换
# ============================================================

def yaml_to_json_str(text, indent=2):
    """YAML 文本转 JSON 字符串"""
    data, _, _ = parse_yaml(text)
    return json.dumps(data, ensure_ascii=False, indent=indent)


def json_to_yaml_text(json_str, indent_size=2, sort_keys=False):
    """JSON 字符串转 YAML 文本"""
    data = json.loads(json_str)
    return dump_yaml(data, indent=0, indent_size=indent_size, sort_keys=sort_keys)


# ============================================================
# 多文档 YAML 处理
# ============================================================

def split_documents(text):
    """按 --- 分隔多文档 YAML"""
    docs = []
    current = []
    for line in text.split("\n"):
        if line.strip() == "---":
            if current:
                docs.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        docs.append("\n".join(current))
    return docs


# ============================================================
# 主函数
# ============================================================

def process_file(filepath, args):
    """处理单个 YAML 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    basename = os.path.basename(filepath)

    # 校验模式
    if args.check:
        errors = validate_yaml_text(text)
        if not errors:
            print(f"✅ {basename}: 语法正确")
            return True
        else:
            print(f"❌ {basename}: 发现 {len(errors)} 个问题")
            for e in errors:
                loc = f"行 {e['line']}" if e['line'] else ""
                print(f"   {loc}: {e['message']}")
            return False

    # 重复键检测（按文档分别检测）
    if args.find_duplicates:
        doc_texts = split_documents(text)
        total_dups = []
        offset = 0
        for doc_text in doc_texts:
            if not doc_text.strip():
                continue
            _, _, duplicates = parse_yaml(doc_text)
            # 计算行号偏移
            doc_lines = doc_text.split("\n")
            for line, key in duplicates:
                total_dups.append((line, key))
            offset += len(doc_lines) + 1
        if not total_dups:
            print(f"✅ {basename}: 未发现重复键")
        else:
            print(f"⚠️  {basename}: 发现 {len(total_dups)} 个重复键")
            for line, key in total_dups:
                print(f"   行 {line}: '{key}'")
        return len(total_dups) == 0

    # YAML 转 JSON（多文档时合并为数组）
    if args.to_json:
        doc_texts = split_documents(text)
        docs = []
        for doc_text in doc_texts:
            if doc_text.strip():
                data, _, _ = parse_yaml(doc_text)
                docs.append(data)
        if len(docs) == 1:
            result = json.dumps(docs[0], ensure_ascii=False, indent=args.indent)
        else:
            result = json.dumps(docs, ensure_ascii=False, indent=args.indent)
        out_path = args.output or filepath.replace(
            os.path.splitext(basename)[1], ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ {basename} → {os.path.basename(out_path)} (JSON, {len(docs)} 个文档)")
        return True

    # JSON 转 YAML
    if args.to_yaml:
        result = json_to_yaml_text(text, indent_size=args.indent, sort_keys=args.sort_keys)
        out_path = args.output or filepath.replace(
            os.path.splitext(basename)[1], ".yaml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"✅ {basename} → {os.path.basename(out_path)} (YAML)")
        return True

    # 格式化（支持多文档 YAML）
    doc_texts = split_documents(text)
    formatted_docs = []
    total_errors = []
    for doc_text in doc_texts:
        if not doc_text.strip():
            continue
        data, errors, duplicates = parse_yaml(doc_text)
        total_errors.extend(errors)
        if args.compact:
            formatted_docs.append(compact_yaml(data))
        else:
            result = dump_yaml(data, indent=0, indent_size=args.indent,
                               sort_keys=args.sort_keys,
                               priority_keys=args.priority)
            formatted_docs.append(result)

    if total_errors:
        print(f"⚠️  {basename}: 解析时发现 {len(total_errors)} 个错误")
        for e in total_errors:
            print(f"   {e}")

    result = "\n---\n".join(formatted_docs)
    if not result.endswith("\n"):
        result += "\n"

    if args.in_place:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ {basename}: 已格式化（{len(result.split(chr(10)))} 行）")
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ {basename} → {os.path.basename(args.output)}")
    else:
        print(result)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="YAML 格式化与校验助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --input config.yaml --in-place
  %(prog)s --input config.yaml --check
  %(prog)s --input config.yaml --to-json --output config.json
  %(prog)s --input config.json --to-yaml
  %(prog)s --input config.yaml --find-duplicates
  %(prog)s --input config.yaml --sort-keys --priority apiVersion,kind,metadata
  %(prog)s --dir ./configs --in-place
        """,
    )

    parser.add_argument("--input", "-i", help="输入 YAML/JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出文件路径（默认原地修改或同名文件）")
    parser.add_argument("--in-place", action="store_true", help="原地修改文件")
    parser.add_argument("--check", action="store_true", help="仅校验语法，不修改")
    parser.add_argument("--compact", action="store_true", help="压缩为单行 flow 风格")
    parser.add_argument("--to-json", action="store_true", help="YAML 转 JSON")
    parser.add_argument("--to-yaml", action="store_true", help="JSON 转 YAML")
    parser.add_argument("--find-duplicates", action="store_true", help="检测重复键")
    parser.add_argument("--sort-keys", action="store_true", help="按键名排序")
    parser.add_argument("--priority", help="排序时优先排列的键（逗号分隔）")
    parser.add_argument("--indent", type=int, default=2, help="缩进空格数（默认2）")
    parser.add_argument("--dir", "-d", help="批量处理目录（递归查找 .yaml/.yml/.json）")
    parser.add_argument("--ext", default="yaml,yml", help="批量处理的扩展名（默认 yaml,yml）")

    args = parser.parse_args()

    if args.priority:
        args.priority = [k.strip() for k in args.priority.split(",")]
    else:
        args.priority = None

    if args.dir:
        exts = set("." + e.strip().lower() for e in args.ext.split(","))
        count = 0
        for root, dirs, files in os.walk(args.dir):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for fname in sorted(files):
                if os.path.splitext(fname)[1].lower() in exts:
                    fpath = os.path.join(root, fname)
                    print(f"\n📄 {fpath}")
                    process_file(fpath, args)
                    count += 1
        print(f"\n{'='*50}")
        print(f"共处理 {count} 个文件")
    elif args.input:
        process_file(args.input, args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
