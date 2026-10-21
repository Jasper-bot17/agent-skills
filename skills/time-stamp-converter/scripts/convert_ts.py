#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
时间戳转换助手

纯 Python 标准库实现，无外部依赖。
支持：时间戳↔日期互转、多时区、批量转换、时间差计算、日期加减。

用法：
  python3 convert_ts.py --ts 1700000000
  python3 convert_ts.py --date "2024-01-01 00:00:00"
  python3 convert_ts.py --now
  python3 convert_ts.py --batch timestamps.txt
  python3 convert_ts.py --diff 1700000000 1700100000
"""

import argparse
import re
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False


# ============================================================
# 常用时区
# ============================================================

COMMON_TIMEZONES = [
    ("UTC", "UTC"),
    ("北京时间", "Asia/Shanghai"),
    ("纽约", "America/New_York"),
    ("伦敦", "Europe/London"),
    ("东京", "Asia/Tokyo"),
    ("悉尼", "Australia/Sydney"),
    ("巴黎", "Europe/Paris"),
    ("洛杉矶", "America/Los_Angeles"),
    ("新加坡", "Asia/Singapore"),
    ("迪拜", "Asia/Dubai"),
]


def get_tz(timezone_name):
    """获取时区对象"""
    if not timezone_name or timezone_name.upper() == "UTC":
        return timezone.utc
    if HAS_ZONEINFO:
        try:
            return ZoneInfo(timezone_name)
        except Exception:
            pass
    # 回退：固定偏移
    offsets = {
        "Asia/Shanghai": 8, "Asia/Beijing": 8, "CST": 8,
        "America/New_York": -5, "EST": -5, "EDT": -4,
        "Europe/London": 0, "GMT": 0, "BST": 1,
        "Asia/Tokyo": 9, "JST": 9,
        "Australia/Sydney": 10, "AEST": 10,
        "Europe/Paris": 1, "CET": 1,
        "America/Los_Angeles": -8, "PST": -8, "PDT": -7,
        "Asia/Singapore": 8, "SGT": 8,
        "Asia/Dubai": 4, "GST": 4,
    }
    offset = offsets.get(timezone_name, 0)
    return timezone(timedelta(hours=offset))


# ============================================================
# 时间戳 → 日期
# ============================================================

def detect_unit(ts):
    """自动识别时间戳单位：秒或毫秒"""
    s = str(ts).strip()
    if s.isdigit():
        if len(s) >= 13:
            return "ms"
        return "s"
    # 浮点数
    try:
        val = float(s)
        if val > 1e12:
            return "ms"
        return "s"
    except ValueError:
        return "s"


def ts_to_date(ts, unit=None, tz_name="Asia/Shanghai"):
    """时间戳转日期，返回字典"""
    if unit is None:
        unit = detect_unit(ts)

    try:
        ts_val = float(ts)
    except (ValueError, TypeError):
        return {"error": f"无效的时间戳: {ts}"}

    if unit == "ms":
        ts_val = ts_val / 1000.0

    tz = get_tz(tz_name)
    dt = datetime.fromtimestamp(ts_val, tz=tz)
    dt_utc = datetime.fromtimestamp(ts_val, tz=timezone.utc)

    return {
        "timestamp_s": int(ts_val),
        "timestamp_ms": int(ts_val * 1000),
        "unit": unit,
        "timezone": tz_name,
        "local": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "local_date": dt.strftime("%Y-%m-%d"),
        "local_time": dt.strftime("%H:%M:%S"),
        "utc": dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "iso8601": dt.isoformat(),
        "rfc2822": dt.strftime("%a, %d %b %Y %H:%M:%S %z"),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()],
        "datetime_obj": dt,
    }


# ============================================================
# 日期 → 时间戳
# ============================================================

def parse_date(date_str):
    """解析多种日期格式"""
    s = date_str.strip()

    # 中文日期：2024年1月1日 12点30分
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})?[点时]?(\d{1,2})?分?(\d{1,2})?秒?", s)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hour = int(m.group(4)) if m.group(4) else 0
        minute = int(m.group(5)) if m.group(5) else 0
        second = int(m.group(6)) if m.group(6) else 0
        return datetime(year, month, day, hour, minute, second)

    # 2024/1/1 或 2024-1-1
    m = re.match(r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})[\sT]+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?", s)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        second = int(m.group(6)) if m.group(6) else 0
        return datetime(year, month, day, hour, minute, second)

    # 仅日期 2024-01-01
    m = re.match(r"^(\d{4})[\-/](\d{1,2})[\-/](\d{1,2})$", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # ISO 8601: 2024-01-01T00:00:00
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass

    # RFC 2822
    for fmt in [
        "%a, %d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y%m%d%H%M%S",
        "%Y%m%d",
    ]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    return None


def date_to_ts(date_str, tz_name="Asia/Shanghai"):
    """日期转时间戳"""
    dt = parse_date(date_str)
    if dt is None:
        return {"error": f"无法解析日期: {date_str}"}

    tz = get_tz(tz_name)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)

    ts = dt.timestamp()
    return {
        "input": date_str,
        "timezone": tz_name,
        "timestamp_s": int(ts),
        "timestamp_ms": int(ts * 1000),
        "timestamp_us": int(ts * 1000000),
        "iso8601": dt.isoformat(),
        "utc": dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "datetime_obj": dt,
    }


# ============================================================
# 当前时间戳
# ============================================================

def get_current_ts(unit="s"):
    """获取当前时间戳"""
    now = time.time()
    if unit == "ms":
        return int(now * 1000)
    elif unit == "us":
        return int(now * 1000000)
    return int(now)


# ============================================================
# 时间差计算
# ============================================================

def time_diff(ts1, ts2):
    """计算两个时间戳之间的差值"""
    try:
        t1 = float(ts1)
        t2 = float(ts2)
    except (ValueError, TypeError):
        return {"error": "无效的时间戳"}

    if detect_unit(ts1) == "ms":
        t1 /= 1000
    if detect_unit(ts2) == "ms":
        t2 /= 1000

    diff = abs(t2 - t1)
    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    minutes = int((diff % 3600) // 60)
    seconds = int(diff % 60)

    return {
        "ts1": int(t1),
        "ts2": int(t2),
        "total_seconds": int(diff),
        "total_minutes": int(diff / 60),
        "total_hours": int(diff / 3600),
        "total_days": round(diff / 86400, 2),
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "human": f"{days}天 {hours}小时 {minutes}分 {seconds}秒",
        "direction": "ts2 在 ts1 之后" if t2 > t1 else "ts2 在 ts1 之前",
    }


# ============================================================
# 日期加减
# ============================================================

def date_add(ts_or_date, days=0, hours=0, minutes=0, tz_name="Asia/Shanghai"):
    """日期加减"""
    # 先解析为 datetime
    if str(ts_or_date).strip().isdigit() or (str(ts_or_date).replace(".", "").isdigit()):
        result = ts_to_date(ts_or_date, tz_name=tz_name)
        if "error" in result:
            return result
        dt = result["datetime_obj"]
    else:
        result = date_to_ts(ts_or_date, tz_name)
        if "error" in result:
            return result
        dt = result["datetime_obj"]

    new_dt = dt + timedelta(days=days, hours=hours, minutes=minutes)
    new_ts = new_dt.timestamp()

    return {
        "original": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "add": f"+{days}天 +{hours}小时 +{minutes}分",
        "result": new_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_s": int(new_ts),
        "timestamp_ms": int(new_ts * 1000),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][new_dt.weekday()],
    }


# ============================================================
# 批量转换
# ============================================================

def batch_convert(filepath, tz_name="Asia/Shanghai"):
    """从文件批量转换时间戳"""
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            result = ts_to_date(line, tz_name=tz_name)
            results.append((line, result))
    return results


# ============================================================
# 输出格式化
# ============================================================

def print_ts_result(result):
    """打印时间戳转日期结果"""
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    print(f"⏰ 时间戳: {result['timestamp_s']} (秒) / {result['timestamp_ms']} (毫秒)")
    print(f"📅 本地时间 ({result['timezone']}): {result['local']} {result['weekday']}")
    print(f"🌍 UTC 时间: {result['utc']}")
    print(f"📝 ISO 8601: {result['iso8601']}")
    print(f"📧 RFC 2822: {result['rfc2822']}")


def print_date_result(result):
    """打印日期转时间戳结果"""
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    print(f"📅 输入日期: {result['input']} ({result['timezone']})")
    print(f"⏰ 时间戳(秒): {result['timestamp_s']}")
    print(f"⏰ 时间戳(毫秒): {result['timestamp_ms']}")
    print(f"⏰ 时间戳(微秒): {result['timestamp_us']}")
    print(f"🌍 UTC: {result['utc']}")
    print(f"📝 ISO 8601: {result['iso8601']}")


def print_all_timezones(ts):
    """打印所有常用时区的时间"""
    print(f"⏰ 时间戳: {ts}\n")
    print(f"{'时区':<12} {'时间':<25} {'星期'}")
    print("-" * 50)
    for name, tz_id in COMMON_TIMEZONES:
        result = ts_to_date(ts, tz_name=tz_id)
        if "error" not in result:
            print(f"{name:<12} {result['local']:<25} {result['weekday']}")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="时间戳转换助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --ts 1700000000
  %(prog)s --ts 1700000000000 --unit ms
  %(prog)s --date "2024-01-01 00:00:00"
  %(prog)s --date "2024年1月1日 12点30分"
  %(prog)s --now
  %(prog)s --now --unit ms
  %(prog)s --batch timestamps.txt
  %(prog)s --diff 1700000000 1700100000
  %(prog)s --date "2024-01-01" --add-days 3
  %(prog)s --ts 1700000000 --all-timezones
  %(prog)s --ts 1700000000 --timezone America/New_York
        """,
    )

    parser.add_argument("--ts", help="时间戳（秒或毫秒，自动识别）")
    parser.add_argument("--unit", choices=["s", "ms"], help="时间戳单位（默认自动识别）")
    parser.add_argument("--date", help="日期字符串（多种格式）")
    parser.add_argument("--timezone", default="Asia/Shanghai",
                        help="时区（默认 Asia/Shanghai，如 UTC、America/New_York）")
    parser.add_argument("--now", action="store_true", help="显示当前时间戳")
    parser.add_argument("--batch", help="批量转换文件（每行一个时间戳）")
    parser.add_argument("--diff", nargs=2, metavar=("TS1", "TS2"),
                        help="计算两个时间戳的差值")
    parser.add_argument("--add-days", type=int, default=0, help="日期加减：天数")
    parser.add_argument("--add-hours", type=int, default=0, help="日期加减：小时")
    parser.add_argument("--add-minutes", type=int, default=0, help="日期加减：分钟")
    parser.add_argument("--all-timezones", action="store_true", help="显示所有常用时区")

    args = parser.parse_args()

    # 当前时间戳
    if args.now:
        ts_s = get_current_ts("s")
        ts_ms = get_current_ts("ms")
        result = ts_to_date(ts_s, tz_name=args.timezone)
        print(f"⏰ 当前时间戳: {ts_s} (秒) / {ts_ms} (毫秒)")
        print(f"📅 本地时间: {result['local']} {result['weekday']}")
        print(f"🌍 UTC: {result['utc']}")
        return

    # 时间戳转日期
    if args.ts:
        if args.all_timezones:
            print_all_timezones(args.ts)
            return
        result = ts_to_date(args.ts, unit=args.unit, tz_name=args.timezone)
        print_ts_result(result)
        # 日期加减
        if args.add_days or args.add_hours or args.add_minutes:
            print()
            add_result = date_add(args.ts, args.add_days, args.add_hours,
                                   args.add_minutes, args.timezone)
            print(f"📅 {add_result['original']} {add_result['add']}")
            print(f"   → {add_result['result']} {add_result['weekday']}")
            print(f"   → 时间戳: {add_result['timestamp_s']}")
        return

    # 日期转时间戳
    if args.date:
        result = date_to_ts(args.date, args.timezone)
        print_date_result(result)
        # 日期加减
        if args.add_days or args.add_hours or args.add_minutes:
            print()
            add_result = date_add(args.date, args.add_days, args.add_hours,
                                   args.add_minutes, args.timezone)
            print(f"📅 {add_result['original']} {add_result['add']}")
            print(f"   → {add_result['result']} {add_result['weekday']}")
            print(f"   → 时间戳: {add_result['timestamp_s']}")
        return

    # 批量转换
    if args.batch:
        results = batch_convert(args.batch, args.timezone)
        print(f"📄 批量转换 ({len(results)} 条)\n")
        print(f"{'时间戳':<15} {'本地时间':<22} {'星期'}")
        print("-" * 50)
        for ts, result in results:
            if "error" not in result:
                print(f"{ts:<15} {result['local']:<22} {result['weekday']}")
            else:
                print(f"{ts:<15} ❌ {result['error']}")
        return

    # 时间差
    if args.diff:
        result = time_diff(args.diff[0], args.diff[1])
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print(f"⏰ TS1: {result['ts1']}")
        print(f"⏰ TS2: {result['ts2']}")
        print(f"📊 差值: {result['human']}")
        print(f"   = {result['total_seconds']} 秒")
        print(f"   = {result['total_minutes']} 分钟")
        print(f"   = {result['total_hours']} 小时")
        print(f"   = {result['total_days']} 天")
        print(f"📌 {result['direction']}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
