#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
习惯追踪器

记录和追踪日常习惯，支持打卡、连续天数、完成率统计。

用法：
  python3 habit_tracker.py add "早起" --category "健康"
  python3 habit_tracker.py check "早起"
  python3 habit_tracker.py uncheck "早起"
  python3 habit_tracker.py dashboard
  python3 habit_tracker.py week
  python3 habit_tracker.py month
  python3 habit_tracker.py list
  python3 habit_tracker.py remove "早起"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta


# ============================================================
# 存储管理
# ============================================================

DEFAULT_DATA_DIR = os.path.expanduser("~/.habit_tracker")
DEFAULT_DATA_FILE = os.path.join(DEFAULT_DATA_DIR, "habits.json")


def load_data(data_path=DEFAULT_DATA_FILE):
    """加载数据，不存在则返回空结构"""
    if not os.path.exists(data_path):
        return {"habits": {}}
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"habits": {}}


def save_data(data, data_path=DEFAULT_DATA_FILE):
    """保存数据"""
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 核心逻辑
# ============================================================

def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def calc_streak(checkins, today=None):
    """计算当前连续天数"""
    if today is None:
        today = datetime.now().date()
    else:
        today = datetime.strptime(today, "%Y-%m-%d").date()

    dates = set()
    for c in checkins:
        try:
            dates.add(datetime.strptime(c, "%Y-%m-%d").date())
        except ValueError:
            continue

    if not dates:
        return 0

    streak = 0
    current = today
    # 如果今天还没打卡，从昨天开始算
    if current not in dates:
        current = current - timedelta(days=1)

    while current in dates:
        streak += 1
        current = current - timedelta(days=1)

    return streak


def calc_longest_streak(checkins):
    """计算最长连续天数"""
    dates = set()
    for c in checkins:
        try:
            dates.add(datetime.strptime(c, "%Y-%m-%d").date())
        except ValueError:
            continue

    if not dates:
        return 0

    sorted_dates = sorted(dates)
    longest = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def completion_rate(checkins, days=7):
    """计算最近 N 天的完成率"""
    end = datetime.now().date()
    start = end - timedelta(days=days - 1)
    dates_set = set()
    for c in checkins:
        try:
            d = datetime.strptime(c, "%Y-%m-%d").date()
            if start <= d <= end:
                dates_set.add(d)
        except ValueError:
            continue
    return len(dates_set), days


# ============================================================
# 彩色输出
# ============================================================

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# ============================================================
# 命令处理
# ============================================================

def cmd_add(args):
    data = load_data(args.data)
    name = args.name.strip()
    if not name:
        print("❌ 习惯名称不能为空", file=sys.stderr)
        sys.exit(1)

    if name in data["habits"]:
        print(f"⚠️  习惯「{name}」已存在", file=sys.stderr)
        sys.exit(1)

    data["habits"][name] = {
        "category": args.category or "未分类",
        "created": today_str(),
        "checkins": [],
    }
    save_data(data, args.data)
    print(f"✅ 已添加习惯：{Colors.BOLD}{name}{Colors.RESET}（分类：{args.category or '未分类'}）")


def cmd_check(args):
    data = load_data(args.data)
    name = args.name.strip()
    if name not in data["habits"]:
        print(f"❌ 习惯「{name}」不存在，使用 add 命令创建", file=sys.stderr)
        sys.exit(1)

    today = today_str()
    checkins = data["habits"][name]["checkins"]
    if today in checkins:
        print(f"⚠️  「{name}」今天已经打过卡了")
        return

    checkins.append(today)
    save_data(data, args.data)

    streak = calc_streak(checkins)
    print(f"✅ 已打卡：{Colors.GREEN}{name}{Colors.RESET}")
    print(f"   当前连续：{Colors.YELLOW}{streak} 天{Colors.RESET}")


def cmd_uncheck(args):
    data = load_data(args.data)
    name = args.name.strip()
    if name not in data["habits"]:
        print(f"❌ 习惯「{name}」不存在", file=sys.stderr)
        sys.exit(1)

    today = today_str()
    checkins = data["habits"][name]["checkins"]
    if today not in checkins:
        print(f"⚠️  「{name}」今天还没打卡")
        return

    checkins.remove(today)
    save_data(data, args.data)
    print(f"↩️  已撤销今日打卡：{name}")


def cmd_list(args):
    data = load_data(args.data)
    if not data["habits"]:
        print("还没有习惯，使用 add 命令添加")
        return

    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  所有习惯{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    for name, habit in data["habits"].items():
        streak = calc_streak(habit["checkins"])
        longest = calc_longest_streak(habit["checkins"])
        print(f"  {Colors.CYAN}{name}{Colors.RESET} [{habit['category']}]")
        print(f"    连续 {streak} 天 | 最长 {longest} 天 | 总打卡 {len(habit['checkins'])} 次")


def cmd_dashboard(args):
    data = load_data(args.data)
    if not data["habits"]:
        print("还没有习惯，使用 add 命令添加")
        return

    today = today_str()
    print()
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  📊 习惯仪表盘  {today}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    print()

    header = f"  {'习惯':<16} {'分类':<8} {'连续':>4} {'最长':>4} {'本周':>6} {'状态':<6}"
    print(header)
    print(f"  {'-'*66}")

    for name, habit in data["habits"].items():
        streak = calc_streak(habit["checkins"])
        longest = calc_longest_streak(habit["checkins"])
        done, total = completion_rate(habit["checkins"], 7)
        rate = f"{done}/{total}"
        checked_today = today in habit["checkins"]
        status = f"{Colors.GREEN}✓ 已打卡{Colors.RESET}" if checked_today else f"{Colors.GRAY}○ 待打卡{Colors.RESET}"
        print(f"  {name:<16} {habit['category']:<8} {streak:>4} {longest:>4} {rate:>6}  {status}")

    print()


def cmd_week(args):
    data = load_data(args.data)
    if not data["habits"]:
        print("还没有习惯")
        return

    today = datetime.now().date()
    # 本周一到周日
    weekday = today.weekday()  # 周一=0
    week_start = today - timedelta(days=weekday)
    days = [week_start + timedelta(days=i) for i in range(7)]
    day_labels = ["一", "二", "三", "四", "五", "六", "日"]

    print()
    print(f"{Colors.BOLD}  📅 本周概览 ({week_start.strftime('%m/%d')} - {(week_start+timedelta(days=6)).strftime('%m/%d')}){Colors.RESET}")
    print()

    header = f"  {'习惯':<16}"
    for i, d in enumerate(days):
        marker = f" {day_labels[i]} "
        if d == today:
            header += f" {Colors.YELLOW}{marker}{Colors.RESET}"
        else:
            header += f" {Colors.GRAY}{marker}{Colors.RESET}"
    print(header)
    print()

    for name, habit in data["habits"].items():
        checkin_dates = set()
        for c in habit["checkins"]:
            try:
                checkin_dates.add(datetime.strptime(c, "%Y-%m-%d").date())
            except ValueError:
                continue

        row = f"  {name:<16}"
        for d in days:
            if d in checkin_dates:
                row += f" {Colors.GREEN} ✓ {Colors.RESET}"
            elif d == today:
                row += f" {Colors.YELLOW} · {Colors.RESET}"
            elif d > today:
                row += f" {Colors.GRAY} · {Colors.RESET}"
            else:
                row += f" {Colors.RED} ✗ {Colors.RESET}"
        print(row)

    print()


def cmd_month(args):
    data = load_data(args.data)
    if not data["habits"]:
        print("还没有习惯")
        return

    today = datetime.now().date()
    month_start = today.replace(day=1)
    # 本月天数
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    days_in_month = (next_month - month_start).days
    month_days = [month_start + timedelta(days=i) for i in range(days_in_month)]

    print()
    print(f"{Colors.BOLD}  📆 本月概览 ({today.strftime('%Y年%m月')}){Colors.RESET}")
    print()

    for name, habit in data["habits"].items():
        checkin_dates = set()
        for c in habit["checkins"]:
            try:
                d = datetime.strptime(c, "%Y-%m-%d").date()
                if d.year == today.year and d.month == today.month:
                    checkin_dates.add(d)
            except ValueError:
                continue

        streak = calc_streak(habit["checkins"])
        longest = calc_longest_streak(habit["checkins"])
        done = len(checkin_dates)
        rate = done / days_in_month * 100

        bar_len = 20
        filled = int(rate / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        print(f"  {Colors.CYAN}{name}{Colors.RESET}")
        print(f"    {Colors.GREEN}{bar}{Colors.RESET} {done}/{days_in_month} 天 ({rate:.0f}%)")
        print(f"    当前连续 {streak} 天 | 最长连续 {longest} 天")
        print()


def cmd_remove(args):
    data = load_data(args.data)
    name = args.name.strip()
    if name not in data["habits"]:
        print(f"❌ 习惯「{name}」不存在", file=sys.stderr)
        sys.exit(1)

    del data["habits"][name]
    save_data(data, args.data)
    print(f"🗑️  已删除习惯：{name}")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="习惯追踪器")
    parser.add_argument("--data", default=DEFAULT_DATA_FILE, help="数据文件路径")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    p_add = subparsers.add_parser("add", help="添加习惯")
    p_add.add_argument("name", help="习惯名称")
    p_add.add_argument("--category", "-c", help="分类")

    p_check = subparsers.add_parser("check", help="今日打卡")
    p_check.add_argument("name", help="习惯名称")

    p_uncheck = subparsers.add_parser("uncheck", help="取消今日打卡")
    p_uncheck.add_argument("name", help="习惯名称")

    subparsers.add_parser("list", help="列出所有习惯")
    subparsers.add_parser("dashboard", help="仪表盘")
    subparsers.add_parser("week", help="本周概览")
    subparsers.add_parser("month", help="本月概览")

    p_remove = subparsers.add_parser("remove", help="删除习惯")
    p_remove.add_argument("name", help="习惯名称")

    args = parser.parse_args()

    commands = {
        "add": cmd_add,
        "check": cmd_check,
        "uncheck": cmd_uncheck,
        "list": cmd_list,
        "dashboard": cmd_dashboard,
        "week": cmd_week,
        "month": cmd_month,
        "remove": cmd_remove,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
