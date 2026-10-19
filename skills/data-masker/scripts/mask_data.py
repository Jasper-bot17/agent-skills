#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
数据脱敏脚本

功能：
- 支持 CSV、JSON、SQL 三种格式的数据脱敏
- 内置 15+ 种敏感字段自动识别
- 支持 6 种脱敏方式：mask、replace、hash、truncate、generalize、nullify
- 可通过规则文件自定义脱敏策略
- 生成脱敏统计报告
- 纯 Python 标准库，无外部依赖

用法：
  python3 mask_data.py --input data.csv --format csv --output masked.csv
  python3 mask_data.py --input data.json --format json --report
  python3 mask_data.py --input data.sql --format sql --rules rules.json
  python3 mask_data.py --input data.csv --field phone:mask --field email:hash
"""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time


# ============================================================
# 内置敏感字段规则
# ============================================================

BUILTIN_RULES = [
    # 手机号
    {"field": "phone", "aliases": ["phone", "mobile", "tel", "telephone", "手机", "电话", "联系方式"],
     "method": "mask", "params": {"keep_start": 3, "keep_end": 4}},
    # 身份证
    {"field": "id_card", "aliases": ["id_card", "idcard", "id_number", "身份证", "证件号", "身份证号"],
     "method": "mask", "params": {"keep_start": 6, "keep_end": 4}},
    # 邮箱
    {"field": "email", "aliases": ["email", "mail", "邮箱", "电子邮件"],
     "method": "mask", "params": {"keep_start": 1, "keep_domain": True}},
    # 银行卡
    {"field": "bank_card", "aliases": ["bank_card", "card_number", "银行卡", "卡号", "credit_card"],
     "method": "mask", "params": {"keep_start": 0, "keep_end": 4}},
    # 姓名
    {"field": "name", "aliases": ["name", "full_name", "姓名", "真实姓名", "用户名", "user_name"],
     "method": "mask", "params": {"keep_start": 1, "keep_end": 0}},
    # 地址
    {"field": "address", "aliases": ["address", "addr", "地址", "住址", "收货地址", "家庭住址"],
     "method": "truncate", "params": {"keep_chars": 9}},
    # IP 地址
    {"field": "ip", "aliases": ["ip", "ip_address", "ipaddr", "IP地址", "客户端IP"],
     "method": "mask", "params": {"keep_start": 2, "keep_end": 0, "separator": "."}},
    # 密码
    {"field": "password", "aliases": ["password", "passwd", "pwd", "密码", "口令"],
     "method": "nullify", "params": {}},
    # 车牌号
    {"field": "plate", "aliases": ["plate", "plate_number", "car_plate", "车牌", "车牌号"],
     "method": "mask", "params": {"keep_start": 2, "keep_end": 1}},
    # QQ号
    {"field": "qq", "aliases": ["qq", "qq_number", "QQ号"],
     "method": "mask", "params": {"keep_start": 2, "keep_end": 2}},
    # 微信号
    {"field": "wechat", "aliases": ["wechat", "weixin", "wx", "微信", "微信号"],
     "method": "mask", "params": {"keep_start": 2, "keep_end": 2}},
    # 工资/薪资
    {"field": "salary", "aliases": ["salary", "wage", "income", "工资", "薪资", "收入", "月薪", "年薪"],
     "method": "generalize", "params": {"bins": [0, 3000, 5000, 8000, 12000, 20000, 30000, 50000, 100000]}},
    # 年龄
    {"field": "age", "aliases": ["age", "年龄"],
     "method": "generalize", "params": {"bins": [0, 18, 25, 35, 45, 55, 65, 100]}},
    # 出生日期
    {"field": "birthday", "aliases": ["birthday", "birth_date", "dob", "出生日期", "生日", "出生年月"],
     "method": "generalize", "params": {"keep_year": True}},
    # 身份证号正则兜底
    {"field": "id_card_regex", "match": "regex", "pattern": r"\b\d{17}[\dXx]\b",
     "method": "mask", "params": {"keep_start": 6, "keep_end": 4}},
    # 手机号正则兜底
    {"field": "phone_regex", "match": "regex", "pattern": r"\b1[3-9]\d{9}\b",
     "method": "mask", "params": {"keep_start": 3, "keep_end": 4}},
    # 邮箱正则兜底
    {"field": "email_regex", "match": "regex", "pattern": r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
     "method": "mask", "params": {"keep_start": 1, "keep_domain": True}},
]


# ============================================================
# 脱敏方法实现
# ============================================================

def mask_value(value, params):
    """掩码脱敏：用 * 替换部分字符"""
    if value is None or value == "":
        return value
    s = str(value)
    keep_start = params.get("keep_start", 0)
    keep_end = params.get("keep_end", 0)
    keep_domain = params.get("keep_domain", False)
    separator = params.get("separator", None)

    if keep_domain and "@" in s:
        local, domain = s.split("@", 1)
        if len(local) <= keep_start:
            masked_local = local[0] + "*" * (len(local) - 1) if len(local) > 1 else local
        else:
            masked_local = local[:keep_start] + "*" * (len(local) - keep_start)
        return f"{masked_local}@{domain}"

    if separator:
        parts = s.split(separator)
        keep_parts = params.get("keep_start", 2)
        for i in range(keep_parts, len(parts)):
            parts[i] = "*" * len(parts[i])
        return separator.join(parts)

    if len(s) <= keep_start + keep_end:
        return "*" * len(s)
    middle = len(s) - keep_start - keep_end
    return s[:keep_start] + "*" * middle + s[len(s) - keep_end:] if keep_end > 0 else s[:keep_start] + "*" * middle


def replace_value(value, params):
    """替换脱敏：替换为固定值或随机值"""
    replacement = params.get("replacement", "***")
    if params.get("random", False):
        import random
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        length = params.get("length", 8)
        return "".join(random.choice(chars) for _ in range(length))
    return replacement


def hash_value(value, params):
    """哈希脱敏：SHA-256（可加盐）"""
    if value is None or value == "":
        return value
    salt = params.get("salt", "")
    algorithm = params.get("algorithm", "sha256")
    length = params.get("length", 16)
    data = f"{salt}{value}".encode("utf-8")
    if algorithm == "md5":
        h = hashlib.md5(data).hexdigest()
    elif algorithm == "sha1":
        h = hashlib.sha1(data).hexdigest()
    else:
        h = hashlib.sha256(data).hexdigest()
    return h[:length]


def truncate_value(value, params):
    """截断脱敏：保留前 N 个字符"""
    if value is None or value == "":
        return value
    s = str(value)
    keep_chars = params.get("keep_chars", 4)
    suffix = params.get("suffix", "***")
    if len(s) <= keep_chars:
        return s
    return s[:keep_chars] + suffix


def generalize_value(value, params):
    """泛化脱敏：区间化或粗粒度"""
    if value is None or value == "":
        return value

    # 出生日期泛化：只保留年份
    if params.get("keep_year", False):
        s = str(value)
        match = re.match(r"(\d{4})", s)
        if match:
            return f"{match.group(1)}-**-**"
        return s

    # 数值区间化
    bins = params.get("bins", [0, 10, 20, 30, 40, 50, 100])
    try:
        num = float(value)
    except (ValueError, TypeError):
        return value

    for i in range(len(bins) - 1):
        if bins[i] <= num < bins[i + 1]:
            return f"{bins[i]}-{bins[i+1]}"
    if num >= bins[-1]:
        return f"{bins[-1]}+"
    return f"<{bins[0]}"


def nullify_value(value, params):
    """置空脱敏"""
    return ""


MASK_METHODS = {
    "mask": mask_value,
    "replace": replace_value,
    "hash": hash_value,
    "truncate": truncate_value,
    "generalize": generalize_value,
    "nullify": nullify_value,
}


# ============================================================
# 规则匹配
# ============================================================

def build_field_map(rules):
    """构建字段名 -> 规则的映射"""
    field_map = {}
    for rule in rules:
        if rule.get("match", "name") == "name":
            for alias in rule.get("aliases", [rule.get("field", "")]):
                field_map[alias.lower()] = rule
    return field_map


def match_rule_by_field(field_name, field_map):
    """根据字段名匹配规则"""
    key = field_name.lower().strip()
    if key in field_map:
        return field_map[key]
    # 模糊匹配：字段名包含别名（要求双方至少3字符，避免 id 误匹配 id_card）
    for alias, rule in field_map.items():
        if len(key) >= 3 and len(alias) >= 3 and (alias in key or key in alias):
            return rule
    return None


def apply_mask(value, rule, salt=None):
    """应用脱敏规则到单个值"""
    method = rule.get("method", "mask")
    params = dict(rule.get("params", {}))
    if salt and method == "hash":
        params["salt"] = salt
    func = MASK_METHODS.get(method, mask_value)
    return func(value, params)


# ============================================================
# CSV 处理
# ============================================================

def process_csv(input_path, output_path, rules, salt=None, report=None):
    """处理 CSV 文件"""
    field_map = build_field_map(rules)
    regex_rules = [r for r in rules if r.get("match") == "regex"]
    masked_fields = set()
    row_count = 0

    with open(input_path, "r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        # 预匹配每列的规则
        column_rules = {}
        for col in fieldnames:
            rule = match_rule_by_field(col, field_map)
            if rule:
                column_rules[col] = rule
                masked_fields.add(col)

        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                row_count += 1
                for col, rule in column_rules.items():
                    if col in row and row[col]:
                        row[col] = apply_mask(row[col], rule, salt)
                # 正则兜底：对所有字段值进行正则匹配
                if regex_rules:
                    for col in fieldnames:
                        if col in row and row[col]:
                            for rrule in regex_rules:
                                pattern = rrule.get("pattern", "")
                                if pattern and re.search(pattern, str(row[col])):
                                    row[col] = apply_mask(row[col], rrule, salt)
                                    masked_fields.add(col + "(regex)")
                                    break
                writer.writerow(row)

    if report is not None:
        report["rows_processed"] = row_count
        report["fields_masked"] = list(masked_fields)
        report["format"] = "csv"

    return row_count, masked_fields


# ============================================================
# JSON 处理
# ============================================================

def process_json_value(obj, field_map, regex_rules, salt, report, path=""):
    """递归处理 JSON 值"""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            rule = match_rule_by_field(key, field_map)
            current_path = f"{path}.{key}" if path else key
            if rule and obj[key] is not None:
                if isinstance(obj[key], (str, int, float)):
                    obj[key] = apply_mask(obj[key], rule, salt)
                    report["fields_masked"].add(current_path)
                else:
                    process_json_value(obj[key], field_map, regex_rules, salt, report, current_path)
            else:
                process_json_value(obj[key], field_map, regex_rules, salt, report, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            process_json_value(item, field_map, regex_rules, salt, report, f"{path}[{i}]")
    elif isinstance(obj, str) and regex_rules:
        for rrule in regex_rules:
            pattern = rrule.get("pattern", "")
            if pattern and re.search(pattern, obj):
                return apply_mask(obj, rrule, salt)
    return obj


def process_json(input_path, output_path, rules, salt=None, report=None):
    """处理 JSON 文件"""
    field_map = build_field_map(rules)
    regex_rules = [r for r in rules if r.get("match") == "regex"]

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if report is not None:
        report["fields_masked"] = set()

    process_json_value(data, field_map, regex_rules, salt, report)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if report is not None:
        report["fields_masked"] = list(report["fields_masked"])
        report["format"] = "json"

    return len(report.get("fields_masked", [])) if report else 0


# ============================================================
# SQL 处理
# ============================================================

def process_sql(input_path, output_path, rules, salt=None, report=None):
    """处理 SQL INSERT 语句"""
    field_map = build_field_map(rules)
    regex_rules = [r for r in rules if r.get("match") == "regex"]
    masked_fields = set()
    statement_count = 0

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 INSERT INTO table (col1, col2, ...) VALUES (v1, v2, ...), ...
    insert_pattern = re.compile(
        r"(INSERT\s+INTO\s+[\w`\"]+\s*\(([^)]+)\)\s*VALUES\s*)(.+?)(;)",
        re.IGNORECASE | re.DOTALL,
    )

    def process_values(match):
        nonlocal statement_count
        prefix = match.group(1)
        columns_str = match.group(2)
        values_str = match.group(3)
        suffix = match.group(4)

        columns = [c.strip().strip("`\"'") for c in columns_str.split(",")]
        col_rules = []
        for col in columns:
            rule = match_rule_by_field(col, field_map)
            col_rules.append(rule)
            if rule:
                masked_fields.add(col)

        # 解析 VALUES 中的每一行
        result_lines = []
        # 简单解析：按 ),( 分割多行
        rows = re.split(r"\),\s*\(", values_str.strip())
        for row in rows:
            row = row.strip().lstrip("(").rstrip(")")
            # 解析值（处理引号和逗号）
            values = parse_sql_values(row)
            new_values = []
            for i, val in enumerate(values):
                if i < len(col_rules) and col_rules[i] and val not in ("NULL", "null", ""):
                    # 去掉引号后脱敏，再加回引号
                    is_string = val.startswith("'") and val.endswith("'")
                    inner = val[1:-1] if is_string else val
                    masked = apply_mask(inner, col_rules[i], salt)
                    new_values.append(f"'{masked}'" if is_string else str(masked))
                else:
                    # 正则兜底
                    matched = False
                    if regex_rules:
                        for rrule in regex_rules:
                            pattern = rrule.get("pattern", "")
                            inner = val[1:-1] if val.startswith("'") and val.endswith("'") else val
                            if pattern and re.search(pattern, inner):
                                masked = apply_mask(inner, rrule, salt)
                                new_values.append(f"'{masked}'" if val.startswith("'") else str(masked))
                                masked_fields.add(f"regex:{rrule.get('field')}")
                                matched = True
                                break
                    if not matched:
                        new_values.append(val)
            result_lines.append("(" + ", ".join(new_values) + ")")

        statement_count += 1
        return prefix + ", ".join(result_lines) + suffix

    masked_content = insert_pattern.sub(process_values, content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(masked_content)

    if report is not None:
        report["statements_processed"] = statement_count
        report["fields_masked"] = list(masked_fields)
        report["format"] = "sql"

    return statement_count, masked_fields


def parse_sql_values(s):
    """解析 SQL VALUES 中的值列表（处理引号内的逗号）"""
    values = []
    current = []
    in_string = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == "'" and (i == 0 or s[i-1] != "\\"):
            in_string = not in_string
            current.append(c)
        elif c == "," and not in_string:
            values.append("".join(current).strip())
            current = []
        else:
            current.append(c)
        i += 1
    if current:
        values.append("".join(current).strip())
    return values


# ============================================================
# 报告生成
# ============================================================

def generate_report(report, output_path):
    """生成脱敏报告"""
    lines = []
    lines.append("# 数据脱敏报告")
    lines.append("")
    lines.append(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**数据格式**: {report.get('format', 'unknown')}")
    if "rows_processed" in report:
        lines.append(f"**处理行数**: {report['rows_processed']}")
    if "statements_processed" in report:
        lines.append(f"**处理 SQL 语句数**: {report['statements_processed']}")
    lines.append(f"**脱敏字段数**: {len(report.get('fields_masked', []))}")
    lines.append("")
    lines.append("## 脱敏字段列表")
    lines.append("")
    for field in report.get("fields_masked", []):
        lines.append(f"- {field}")
    lines.append("")
    lines.append("## 脱敏方式统计")
    lines.append("")
    method_count = {}
    for field in report.get("fields_masked", []):
        method_count[field] = method_count.get(field, 0) + 1
    for method, count in method_count.items():
        lines.append(f"- {method}: {count} 个字段")

    content = "\n".join(lines) + "\n"
    report_path = output_path + ".report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    return report_path


# ============================================================
# 主函数
# ============================================================

def detect_format(filepath):
    """根据文件扩展名自动检测格式"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return "csv"
    elif ext == ".json":
        return "json"
    elif ext in (".sql", ".txt"):
        return "sql"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="数据脱敏工具（支持 CSV/JSON/SQL，15+ 敏感字段自动识别）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --input data.csv --format csv --output masked.csv
  %(prog)s --input data.json --format json --report
  %(prog)s --input data.sql --format sql --rules rules.json
  %(prog)s --input data.csv --field phone:mask --field email:hash --salt mysecret
  %(prog)s --input data.csv --preview
        """,
    )

    parser.add_argument("--input", "-i", required=True, help="输入文件路径")
    parser.add_argument("--format", "-f", choices=["csv", "json", "sql"],
                        help="数据格式（默认自动检测）")
    parser.add_argument("--output", "-o", help="输出文件路径（默认 masked_<原文件名>）")
    parser.add_argument("--rules", "-r", help="自定义规则文件（JSON）")
    parser.add_argument("--field", action="append", default=[],
                        help="指定字段脱敏方式，格式 字段名:方式，可多次使用")
    parser.add_argument("--salt", help="哈希加盐值")
    parser.add_argument("--report", action="store_true", help="生成脱敏报告")
    parser.add_argument("--preview", action="store_true", help="预览模式（前5行，不写文件）")
    parser.add_argument("--no-auto-detect", action="store_true", help="关闭自动敏感字段识别")
    parser.add_argument("--encoding", default="utf-8", help="文件编码（默认 utf-8）")

    args = parser.parse_args()

    # 检测格式
    fmt = args.format or detect_format(args.input)
    if not fmt:
        print("❌ 无法自动检测数据格式，请用 --format 指定 csv/json/sql", file=sys.stderr)
        sys.exit(1)

    # 输出路径
    if not args.output:
        base = os.path.basename(args.input)
        args.output = os.path.join(os.path.dirname(args.input) or ".", f"masked_{base}")

    # 加载规则
    rules = []
    if not args.no_auto_detect:
        rules.extend(BUILTIN_RULES)

    if args.rules:
        with open(args.rules, "r", encoding="utf-8") as f:
            custom = json.load(f)
            if isinstance(custom, dict) and "rules" in custom:
                rules.extend(custom["rules"])
            elif isinstance(custom, list):
                rules.extend(custom)

    # 命令行指定的字段规则
    for field_spec in args.field:
        if ":" in field_spec:
            field_name, method = field_spec.split(":", 1)
            rules.append({
                "field": field_name,
                "aliases": [field_name],
                "method": method,
                "params": {},
            })

    if not rules:
        print("⚠️  没有配置任何脱敏规则，文件将原样复制", file=sys.stderr)

    # 预览模式
    if args.preview:
        print(f"🔍 预览模式（格式: {fmt}）")
        print(f"   输入: {args.input}")
        print(f"   规则数: {len(rules)}")
        print()
        if fmt == "csv":
            with open(args.input, "r", encoding=args.encoding, newline="") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i > 5:
                        break
                    print(" | ".join(row[:8]))
        elif fmt == "json":
            with open(args.input, "r", encoding=args.encoding) as f:
                data = json.load(f)
            print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
        elif fmt == "sql":
            with open(args.input, "r", encoding=args.encoding) as f:
                print(f.read()[:2000])
        return

    # 执行脱敏
    report = {}
    print(f"🚀 开始脱敏（格式: {fmt}）")
    print(f"   输入: {args.input}")
    print(f"   输出: {args.output}")
    print(f"   规则数: {len(rules)}")
    print()

    if fmt == "csv":
        rows, fields = process_csv(args.input, args.output, rules, args.salt, report)
        print(f"✅ 处理完成: {rows} 行，{len(fields)} 个字段脱敏")
    elif fmt == "json":
        fields = process_json(args.input, args.output, rules, args.salt, report)
        print(f"✅ 处理完成: {fields} 个字段脱敏")
    elif fmt == "sql":
        stmts, fields = process_sql(args.input, args.output, rules, args.salt, report)
        print(f"✅ 处理完成: {stmts} 条 INSERT 语句，{len(fields)} 个字段脱敏")

    # 生成报告
    if args.report:
        report_path = generate_report(report, args.output)
        print(f"📄 报告: {report_path}")

    print(f"\n📁 输出文件: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
