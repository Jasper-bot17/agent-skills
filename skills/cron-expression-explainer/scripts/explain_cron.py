#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Cron 表达式解析脚本

功能：
- 解析标准 5 字段 cron 表达式（分 时 日 月 周）
- 用中文通俗解释每个字段的含义
- 验证表达式合法性
- 生成未来 N 次执行时间
- 支持快捷写法（@yearly/@monthly/@weekly/@daily/@hourly/@midnight）
- 生成人类可读描述
- 支持范围、列表、步长等高级语法

用法：
  python3 explain_cron.py --expr "30 9 * * *"
  python3 explain_cron.py --expr "30 9 * * *" --validate
  python3 explain_cron.py --expr "30 9 * * *" --next
  python3 explain_cron.py --expr "*/15 * * * *" --next --count 20
  python3 explain_cron.py --expr "0 18 * * 1-5" --all
  python3 explain_cron.py --expr "@daily" --all
  python3 explain_cron.py --expr "0 9 * * 1" --next --start "2026-01-01 00:00"
  python3 explain_cron.py --cheatsheet
  python3 explain_cron.py --shortcuts
"""

import argparse
import sys
from datetime import datetime, timedelta


# ============================================================
# 快捷写法映射
# ============================================================

SHORTCUTS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

SHORTCUT_DESCRIPTIONS = {
    "@yearly": "每年1月1日0点0分",
    "@annually": "每年1月1日0点0分",
    "@monthly": "每月1日0点0分",
    "@weekly": "每周日0点0分",
    "@daily": "每天0点0分",
    "@midnight": "每天0点0分（午夜）",
    "@hourly": "每小时0分",
}


# ============================================================
# 字段定义
# ============================================================

FIELD_DEFS = [
    {"name": "分钟", "index": 0, "min": 0, "max": 59, "names": {}},
    {"name": "小时", "index": 1, "min": 0, "max": 23, "names": {}},
    {"name": "日", "index": 2, "min": 1, "max": 31, "names": {}},
    {"name": "月", "index": 3, "min": 1, "max": 12,
     "names": {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
               "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}},
    {"name": "星期", "index": 4, "min": 0, "max": 7,
     "names": {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}},
]

WEEKDAY_NAMES = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
PYTHON_WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
MONTH_NAMES = ["", "1月", "2月", "3月", "4月", "5月", "6月",
               "7月", "8月", "9月", "10月", "11月", "12月"]


# ============================================================
# 解析单个字段
# ============================================================

def parse_field(field_str: str, field_def: dict) -> set:
    """解析单个 cron 字段，返回所有匹配值的集合"""
    min_val = field_def["min"]
    max_val = field_def["max"]
    names = field_def["names"]

    # 处理 ? （不指定，等同于 *）
    if field_str == "?":
        field_str = "*"

    # 处理 L（最后一天/最后一个星期几）
    if field_str == "L":
        if field_def["name"] == "日":
            return {"L"}  # 标记为最后一天
        elif field_def["name"] == "星期":
            return {"L"}  # 标记为最后一个星期几
        else:
            raise ValueError(f"L 只能用于日或星期字段")

    # 处理 W（最近工作日）
    if field_str.endswith("W") and field_str[:-1].isdigit():
        if field_def["name"] == "日":
            return {f"W{int(field_str[:-1])}"}
        else:
            raise ValueError(f"W 只能用于日字段")

    # 处理 #（第几个星期几）
    if "#" in field_str and field_def["name"] == "星期":
        parts = field_str.split("#")
        weekday = int(parts[0])
        nth = int(parts[1])
        if weekday == 7:
            weekday = 0
        return {f"#{weekday}#{nth}"}

    result = set()

    # 处理逗号分隔的列表
    for part in field_str.split(","):
        part = part.strip()

        # 处理名称（JAN, MON 等）
        if part.upper() in names:
            result.add(names[part.upper()])
            continue

        # 处理 *
        if part == "*":
            result.update(range(min_val, max_val + 1))
            continue

        # 处理步长 */n 或 a-b/n
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            if step <= 0:
                raise ValueError(f"步长必须为正整数: {step}")

            if base == "*":
                start, end = min_val, max_val
            elif "-" in base:
                start_str, end_str = base.split("-", 1)
                start = int(start_str)
                end = int(end_str)
            else:
                start = int(base)
                end = max_val

            if start < min_val or end > max_val:
                raise ValueError(f"值超出范围 {min_val}-{max_val}: {start}-{end}")

            result.update(range(start, end + 1, step))
            continue

        # 处理范围 a-b
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            if start < min_val or end > max_val:
                raise ValueError(f"值超出范围 {min_val}-{max_val}: {start}-{end}")
            if start > end:
                raise ValueError(f"范围起始值大于结束值: {start}-{end}")
            result.update(range(start, end + 1))
            continue

        # 单个值
        val = int(part)
        # 星期字段 7 等同于 0（周日）
        if field_def["name"] == "星期" and val == 7:
            val = 0
        if val < min_val or val > max_val:
            raise ValueError(f"值超出范围 {min_val}-{max_val}: {val}")
        result.add(val)

    return result


# ============================================================
# 解析完整 cron 表达式
# ============================================================

def parse_cron(expr: str) -> dict:
    """解析完整 cron 表达式，返回各字段的匹配值集合"""
    expr = expr.strip()

    # 处理快捷写法
    original_expr = expr
    is_shortcut = False
    if expr in SHORTCUTS:
        is_shortcut = True
        expr = SHORTCUTS[expr]

    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"cron 表达式必须有 5 个字段，当前有 {len(fields)} 个: {expr}")

    result = {
        "original": original_expr,
        "expanded": expr,
        "is_shortcut": is_shortcut,
        "fields": [],
    }

    for i, field_str in enumerate(fields):
        field_def = FIELD_DEFS[i]
        try:
            values = parse_field(field_str, field_def)
        except ValueError as e:
            raise ValueError(f"{field_def['name']}字段解析失败: {e}")

        result["fields"].append({
            "name": field_def["name"],
            "raw": field_str,
            "values": values,
            "def": field_def,
        })

    return result


# ============================================================
# 验证表达式
# ============================================================

def validate_cron(expr: str) -> dict:
    """验证 cron 表达式，返回验证结果"""
    result = {"valid": True, "errors": [], "warnings": []}

    try:
        parsed = parse_cron(expr)
    except ValueError as e:
        result["valid"] = False
        result["errors"].append(str(e))
        return result

    # 检查日和星期同时为 * 的情况（正常，但提示）
    day_field = parsed["fields"][2]
    weekday_field = parsed["fields"][4]

    # 检查是否包含特殊标记（L, W, #）
    for field in parsed["fields"]:
        for v in field["values"]:
            if isinstance(v, str):
                if v.startswith("L") and field["name"] not in ("日", "星期"):
                    result["errors"].append(f"{field['name']}字段不支持 L")
                if v.startswith("W") and field["name"] != "日":
                    result["errors"].append(f"{field['name']}字段不支持 W")
                if v.startswith("#") and field["name"] != "星期":
                    result["errors"].append(f"{field['name']}字段不支持 #")

    # 检查日字段是否可能不存在（如2月30日）
    day_raw = day_field["raw"]
    day_values = day_field["values"]
    if day_raw not in ("*", "?") and isinstance(day_values, set) and all(isinstance(v, int) for v in day_values):
        if 31 in day_values and len(day_values) > 1:
            result["warnings"].append("日字段包含31，但2月、4月、6月、9月、11月没有31日，这些月份不会触发")

    return result


# ============================================================
# 解释表达式
# ============================================================

def explain_field(field: dict) -> str:
    """解释单个字段"""
    name = field["name"]
    raw = field["raw"]
    values = field["values"]
    field_def = field["def"]

    # 特殊标记
    if any(isinstance(v, str) for v in values):
        special = [v for v in values if isinstance(v, str)]
        if "L" in special and name == "日":
            return "每月最后一天"
        if "L" in special and name == "星期":
            return "每月最后一个星期几"
        if any(v.startswith("W") for v in special):
            day_num = special[0][1:]
            return f"每月{day_num}日最近的工作日"
        if any(v.startswith("#") for v in special):
            parts = special[0].split("#")
            weekday = int(parts[1])
            nth = int(parts[2])
            return f"每月第{nth}个{WEEKDAY_NAMES[weekday]}"

    # 全部值
    if values == set(range(field_def["min"], field_def["max"] + 1)):
        if name == "分钟":
            return "每分钟"
        elif name == "小时":
            return "每小时"
        elif name == "日":
            return "每天"
        elif name == "月":
            return "每月"
        elif name == "星期":
            return "任意星期"

    # 单个值
    if len(values) == 1:
        val = list(values)[0]
        if name == "分钟":
            return f"第{val}分钟"
        elif name == "小时":
            period = "上午" if val < 12 else "下午"
            hour_12 = val if val <= 12 else val - 12
            if hour_12 == 0:
                hour_12 = 12
            return f"{period}{hour_12}点（{val}时）"
        elif name == "日":
            return f"{val}日"
        elif name == "月":
            return MONTH_NAMES[val]
        elif name == "星期":
            return WEEKDAY_NAMES[val]

    # 连续范围
    sorted_vals = sorted(values)
    if len(sorted_vals) > 1 and sorted_vals == list(range(sorted_vals[0], sorted_vals[-1] + 1)):
        start, end = sorted_vals[0], sorted_vals[-1]
        if name == "分钟":
            return f"第{start}到{end}分钟"
        elif name == "小时":
            return f"{start}时到{end}时"
        elif name == "日":
            return f"{start}日到{end}日"
        elif name == "月":
            return f"{MONTH_NAMES[start]}到{MONTH_NAMES[end]}"
        elif name == "星期":
            return f"{WEEKDAY_NAMES[start]}到{WEEKDAY_NAMES[end]}"

    # 步长（检测是否等间距）
    if len(sorted_vals) > 2:
        diffs = [sorted_vals[i+1] - sorted_vals[i] for i in range(len(sorted_vals)-1)]
        if len(set(diffs)) == 1 and sorted_vals[0] == field_def["min"]:
            step = diffs[0]
            if name == "分钟":
                return f"每{step}分钟"
            elif name == "小时":
                return f"每{step}小时"

    # 列表
    if name == "星期":
        return "、".join(WEEKDAY_NAMES[v] for v in sorted_vals)
    elif name == "月":
        return "、".join(MONTH_NAMES[v] for v in sorted_vals)
    else:
        return "、".join(str(v) for v in sorted_vals)


def generate_human_description(parsed: dict) -> str:
    """生成人类可读的 cron 描述"""
    fields = parsed["fields"]
    minute_desc = explain_field(fields[0])
    hour_desc = explain_field(fields[1])
    day_desc = explain_field(fields[2])
    month_desc = explain_field(fields[3])
    weekday_desc = explain_field(fields[4])

    # 构建描述
    parts = []

    # 时间部分
    if fields[0]["raw"] == "*" and fields[1]["raw"] == "*":
        time_part = "每分钟"
    elif fields[0]["raw"] == "*":
        time_part = f"{hour_desc}的每分钟"
    elif fields[1]["raw"] == "*":
        time_part = f"每小时的{minute_desc}"
    else:
        # 提取具体小时和分钟
        hour_vals = sorted(v for v in fields[1]["values"] if isinstance(v, int))
        minute_vals = sorted(v for v in fields[0]["values"] if isinstance(v, int))
        if len(hour_vals) == 1 and len(minute_vals) == 1:
            h, m = hour_vals[0], minute_vals[0]
            period = "上午" if h < 12 else "下午"
            h12 = h if h <= 12 else h - 12
            if h12 == 0:
                h12 = 12
            time_part = f"{period}{h12}点{m}分（{h:02d}:{m:02d}）"
        else:
            time_part = f"{hour_desc}，{minute_desc}"

    parts.append(time_part)

    # 日期部分
    if fields[2]["raw"] != "*" or fields[4]["raw"] != "*":
        if fields[2]["raw"] != "*" and fields[4]["raw"] != "*":
            parts.append(f"{day_desc}或{weekday_desc}")
        elif fields[2]["raw"] != "*":
            parts.append(day_desc)
        else:
            parts.append(weekday_desc)

    if fields[3]["raw"] != "*":
        parts.append(month_desc)

    return "，".join(parts) + "执行"


# ============================================================
# 预测执行时间
# ============================================================

def get_next_runs(parsed: dict, start_time: datetime, count: int = 10) -> list:
    """生成未来 N 次执行时间"""
    fields = parsed["fields"]
    minute_values = set(v for v in fields[0]["values"] if isinstance(v, int))
    hour_values = set(v for v in fields[1]["values"] if isinstance(v, int))
    day_values = set(v for v in fields[2]["values"] if isinstance(v, int))
    month_values = set(v for v in fields[3]["values"] if isinstance(v, int))
    weekday_values = set(v for v in fields[4]["values"] if isinstance(v, int))

    # 特殊标记
    day_has_L = any(v == "L" for v in fields[2]["values"])
    weekday_has_L = any(v == "L" for v in fields[4]["values"])

    results = []
    current = start_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

    max_iterations = 366 * 24 * 60 * 5  # 最多扫描5年
    iterations = 0

    while len(results) < count and iterations < max_iterations:
        iterations += 1

        # 检查月
        if current.month not in month_values:
            # 跳到下个月
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1, hour=0, minute=0)
            else:
                current = current.replace(month=current.month + 1, day=1, hour=0, minute=0)
            continue

        # 检查日
        day_match = current.day in day_values if day_values else True

        # 检查 L（最后一天）
        if day_has_L:
            import calendar
            last_day = calendar.monthrange(current.year, current.month)[1]
            if current.day == last_day:
                day_match = True

        # 检查 W（最近工作日）
        for v in fields[2]["values"]:
            if isinstance(v, str) and v.startswith("W"):
                target_day = int(v[1:])
                # 简化处理：如果当天是目标日且是工作日，或目标日最近的工作日
                if current.day == target_day and current.weekday() < 5:
                    day_match = True
                elif target_day <= current.day:
                    # 检查是否是目标日最近的工作日
                    target_date = current.replace(day=target_day)
                    if target_date.weekday() == 5:  # 周六
                        nearest = target_date - timedelta(days=1)
                    elif target_date.weekday() == 6:  # 周日
                        nearest = target_date + timedelta(days=1)
                    else:
                        nearest = target_date
                    if current.date() == nearest.date():
                        day_match = True

        # 检查星期
        weekday_match = current.weekday() in weekday_values if weekday_values else True
        # cron 星期 0=周日，Python weekday() 周一=0
        cron_weekday = (current.weekday() + 1) % 7
        if weekday_values:
            weekday_match = cron_weekday in weekday_values

        # 星期 L（最后一个星期几）
        if weekday_has_L:
            # 简化：如果是当月最后一个同星期几
            next_week = current + timedelta(days=7)
            if next_week.month != current.month:
                weekday_match = True

        # 日和星期的关系：如果两者都指定了具体值，为"或"关系
        day_specified = fields[2]["raw"] not in ("*", "?")
        weekday_specified = fields[4]["raw"] not in ("*", "?")
        if day_specified and weekday_specified:
            date_match = day_match or weekday_match
        elif day_specified:
            date_match = day_match
        elif weekday_specified:
            date_match = weekday_match
        else:
            date_match = True

        if not date_match:
            # 跳到下一天
            current = (current + timedelta(days=1)).replace(hour=0, minute=0)
            continue

        # 检查小时
        if current.hour not in hour_values:
            current = current + timedelta(hours=1)
            current = current.replace(minute=0)
            continue

        # 检查分钟
        if current.minute not in minute_values:
            current = current + timedelta(minutes=1)
            continue

        # 匹配成功
        results.append(current)
        current = current + timedelta(minutes=1)

    return results


# ============================================================
# 输出函数
# ============================================================

def print_explain(parsed: dict):
    """输出解释结果"""
    print("📖 Cron 表达式解析")
    print("=" * 60)
    print(f"  原始表达式: {parsed['original']}")
    if parsed["is_shortcut"]:
        print(f"  展开为标准: {parsed['expanded']}")
        print(f"  快捷写法含义: {SHORTCUT_DESCRIPTIONS.get(parsed['original'], '')}")
    print("-" * 60)

    field_labels = ["分钟 (0-59)", "小时 (0-23)", "日 (1-31)", "月 (1-12)", "星期 (0-6, 0=周日)"]
    for i, field in enumerate(parsed["fields"]):
        print(f"  {field_labels[i]:<16} = {field['raw']:<12} → {explain_field(field)}")

    print("-" * 60)
    print(f"  📝 人类可读: {generate_human_description(parsed)}")
    print("=" * 60)


def print_validate(result: dict, expr: str):
    """输出验证结果"""
    print("✅ Cron 表达式验证")
    print("=" * 60)
    print(f"  表达式: {expr}")
    print("-" * 60)

    if result["valid"]:
        print("  状态: ✅ 合法")
    else:
        print("  状态: ❌ 不合法")

    if result["errors"]:
        print("\n  错误:")
        for err in result["errors"]:
            print(f"    ❌ {err}")

    if result["warnings"]:
        print("\n  警告:")
        for warn in result["warnings"]:
            print(f"    ⚠️  {warn}")

    if not result["errors"] and not result["warnings"]:
        print("  无错误和警告")
    print("=" * 60)


def print_next_runs(runs: list, expr: str):
    """输出未来执行时间"""
    print("⏰ 未来执行时间预测")
    print("=" * 60)
    print(f"  表达式: {expr}")
    print(f"  预测次数: {len(runs)}")
    print("-" * 60)

    for i, dt in enumerate(runs, 1):
        weekday = PYTHON_WEEKDAY_NAMES[dt.weekday()]
        print(f"  {i:>3}. {dt.strftime('%Y-%m-%d %H:%M')}  {weekday}")

    print("=" * 60)


def print_cheatsheet():
    """输出常用 cron 表达式速查表"""
    print("📋 常用 Cron 表达式速查表")
    print("=" * 70)

    cheatsheet = [
        ("每分钟", "* * * * *"),
        ("每5分钟", "*/5 * * * *"),
        ("每15分钟", "*/15 * * * *"),
        ("每小时", "0 * * * *"),
        ("每小时第30分钟", "30 * * * *"),
        ("每天0点", "0 0 * * *"),
        ("每天上午9点", "0 9 * * *"),
        ("每天上午9点30分", "30 9 * * *"),
        ("每天下午6点", "0 18 * * *"),
        ("每天中午12点", "0 12 * * *"),
        ("每周一上午9点", "0 9 * * 1"),
        ("每周五下午6点", "0 18 * * 5"),
        ("工作日（周一至周五）上午9点", "0 9 * * 1-5"),
        ("工作日下午6点", "0 18 * * 1-5"),
        ("每周日0点", "0 0 * * 0"),
        ("每月1日0点", "0 0 1 * *"),
        ("每月1日上午9点", "0 9 1 * *"),
        ("每月15日0点", "0 0 15 * *"),
        ("每月最后一天0点", "0 0 L * *"),
        ("每季度第一天0点", "0 0 1 1,4,7,10 *"),
        ("每年1月1日0点", "0 0 1 1 *"),
        ("每天上午9点到下午5点每小时", "0 9-17 * * *"),
        ("工作日上午9点到下午5点每小时", "0 9-17 * * 1-5"),
        ("每天上午9点和下午6点", "0 9,18 * * *"),
        ("每2小时", "0 */2 * * *"),
        ("每天6点、12点、18点", "0 6,12,18 * * *"),
    ]

    print(f"  {'描述':<35} {'表达式'}")
    print("-" * 70)
    for desc, expr in cheatsheet:
        print(f"  {desc:<35} {expr}")

    print("=" * 70)


def print_shortcuts():
    """输出快捷写法"""
    print("⚡ Cron 快捷写法")
    print("=" * 60)
    print(f"  {'快捷写法':<15} {'等价表达式':<15} {'含义'}")
    print("-" * 60)
    for shortcut, expr in SHORTCUTS.items():
        desc = SHORTCUT_DESCRIPTIONS[shortcut]
        print(f"  {shortcut:<15} {expr:<15} {desc}")
    print("=" * 60)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Cron 表达式解析、验证、预测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --expr "30 9 * * *"           解释表达式
  %(prog)s --expr "30 9 * * *" --validate 验证表达式
  %(prog)s --expr "30 9 * * *" --next     预测执行时间
  %(prog)s --expr "0 18 * * 1-5" --all    全部功能
  %(prog)s --expr "@daily" --all           快捷写法
  %(prog)s --cheatsheet                     常用表达式速查
  %(prog)s --shortcuts                      快捷写法列表
        """,
    )
    parser.add_argument("--expr", "-e", help="Cron 表达式（5字段或快捷写法）")
    parser.add_argument("--explain", action="store_true", help="解释表达式（默认）")
    parser.add_argument("--validate", action="store_true", help="验证表达式合法性")
    parser.add_argument("--next", action="store_true", help="预测未来执行时间")
    parser.add_argument("--all", action="store_true", help="全部功能（解释+验证+预测）")
    parser.add_argument("--count", "-n", type=int, default=10,
                        help="预测执行时间的次数（默认10，最大1000）")
    parser.add_argument("--start", "-s", help="预测起始时间（格式：YYYY-MM-DD HH:MM，默认当前时间）")
    parser.add_argument("--cheatsheet", "-c", action="store_true", help="显示常用表达式速查表")
    parser.add_argument("--shortcuts", action="store_true", help="显示快捷写法列表")

    args = parser.parse_args()

    # 速查表
    if args.cheatsheet:
        print_cheatsheet()
        return

    # 快捷写法列表
    if args.shortcuts:
        print_shortcuts()
        return

    # 必须提供表达式
    if not args.expr:
        parser.print_help()
        print("\n错误：请使用 --expr 提供 cron 表达式，或使用 --cheatsheet 查看速查表",
              file=sys.stderr)
        sys.exit(1)

    # 默认操作：解释
    if not args.explain and not args.validate and not args.next and not args.all:
        args.explain = True

    if args.all:
        args.explain = True
        args.validate = True
        args.next = True

    # 限制次数
    count = min(max(args.count, 1), 1000)

    # 解析起始时间
    if args.start:
        try:
            start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M")
        except ValueError:
            print(f"错误：起始时间格式不正确，应为 YYYY-MM-DD HH:MM: {args.start}",
                  file=sys.stderr)
            sys.exit(1)
    else:
        start_time = datetime.now()

    # 解析表达式
    try:
        parsed = parse_cron(args.expr)
    except ValueError as e:
        print(f"❌ 表达式解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    print()

    # 解释
    if args.explain:
        print_explain(parsed)
        print()

    # 验证
    if args.validate:
        result = validate_cron(args.expr)
        print_validate(result, args.expr)
        print()

    # 预测
    if args.next:
        runs = get_next_runs(parsed, start_time, count)
        print_next_runs(runs, args.expr)
        print()


if __name__ == "__main__":
    main()
