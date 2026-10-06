#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
日期提取与倒计时脚本

从文本中提取所有日期和截止事项，计算倒计时天数，按时间排序输出。

用法：
  python3 extract_dates.py --file notes.txt
  python3 extract_dates.py --text "报告截止3月15日"
  python3 extract_dates.py --file notes.txt --within-days 30
  python3 extract_dates.py --file notes.txt --include-overdue
  python3 extract_dates.py --file notes.txt --output json
  cat notes.txt | python3 extract_dates.py
"""

import argparse
import json
import re
import sys
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple


# ============================================================
# 数据结构
# ============================================================

class DateItem:
    """单个日期事项"""
    def __init__(self, date_str: str, context: str, raw_text: str,
                 parsed_date: Optional[date] = None, relative: bool = False):
        self.date_str = date_str          # 原始日期文本
        self.context = context            # 上下文描述
        self.raw_text = raw_text          # 整行原文
        self.parsed_date = parsed_date    # 解析后的日期
        self.relative = relative          # 是否为相对日期
        self.days_until = None            # 倒计时天数

    def __repr__(self):
        return f"<DateItem {self.date_str}>"


# ============================================================
# 日期解析
# ============================================================

# 星期映射
WEEKDAY_MAP = {
    "一": 0, "二": 1, "三": 2, "四": 3,
    "五": 4, "六": 5, "日": 6, "天": 6,
}


def parse_standard_date(text: str, today: date) -> Optional[date]:
    """解析标准日期格式"""
    # YYYY-MM-DD 或 YYYY/MM/DD 或 YYYY.MM.DD
    m = re.match(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    # YYYYMMDD
    m = re.match(r'(\d{4})(\d{2})(\d{2})$', text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    return None


def parse_chinese_date(text: str, today: date) -> Optional[date]:
    """解析中文日期格式"""
    # YYYY年M月D日
    m = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日?', text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None

    # M月D日（无年份，用当前年份）
    m = re.match(r'(\d{1,2})月(\d{1,2})日?', text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = today.year
        try:
            d = date(year, month, day)
            # 如果日期已过，推断为下一年
            if d < today - timedelta(days=7):
                d = date(year + 1, month, day)
            return d
        except ValueError:
            return None

    return None


def parse_relative_date(text: str, today: date) -> Optional[date]:
    """解析相对日期"""
    text = text.strip()

    # 今天
    if text in ("今天", "今日", "今天内", "今天截止"):
        return today

    # 明天/后天
    if text in ("明天", "明日"):
        return today + timedelta(days=1)
    if text in ("后天",):
        return today + timedelta(days=2)

    # X天后
    m = re.match(r'(\d+)天后', text)
    if m:
        return today + timedelta(days=int(m.group(1)))

    # 本周X / 这周日X
    m = re.match(r'本周([一二三四五六日天])', text)
    if m:
        target_weekday = WEEKDAY_MAP.get(m.group(1))
        if target_weekday is not None:
            days_ahead = target_weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

    # 下周X
    m = re.match(r'下周([一二三四五六日天])', text)
    if m:
        target_weekday = WEEKDAY_MAP.get(m.group(1))
        if target_weekday is not None:
            days_ahead = 7 - today.weekday() + target_weekday
            return today + timedelta(days=days_ahead)

    # 月底
    if text in ("月底", "月末", "月底前", "月末前"):
    # 下个月最后一天
        if today.month == 12:
            return date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            return date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 本周（周五前等）
    if text in ("本周", "这周", "本周内"):
        # 本周日
        days_ahead = 6 - today.weekday()
        if days_ahead < 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    return None


def extract_context(line: str, date_match: str) -> str:
    """从行中提取日期周围的上下文"""
    # 去掉日期本身，提取前后的描述
    context = line.replace(date_match, '').strip()
    # 去掉常见前缀
    context = re.sub(r'^(截止|deadline|日期|时间|before|by)\s*[:：]?\s*', '', context, flags=re.IGNORECASE)
    context = re.sub(r'[:：]\s*$', '', context)
    # 限制长度
    if len(context) > 50:
        context = context[:50] + '...'
    return context if context else '（无描述）'


def extract_dates_from_text(text: str, today: date) -> List[DateItem]:
    """从文本中提取所有日期"""
    items = []
    lines = text.split('\n')

    # 日期模式列表（按优先级排序）
    patterns = [
        # 标准日期
        (r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}(?:\s+\d{1,2}:\d{2})?', 'standard'),
        # 中文日期（带年份）
        (r'\d{4}年\d{1,2}月\d{1,2}日', 'chinese'),
        # 中文日期（不带年份）
        (r'\d{1,2}月\d{1,2}日', 'chinese'),
        # 相对日期
        (r'(?:今天|今日|明天|明日|后天|本周[一二三四五六日天]|下周[一二三四五六日天]|月底|月末|本周|这周|本周内|月底前)', 'relative'),
        # X天后
        (r'\d+天后', 'relative'),
        # YYYYMMDD
        (r'\b\d{8}\b', 'standard'),
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        for pattern, ptype in patterns:
            for m in re.finditer(pattern, line):
                date_text = m.group(0)
                parsed = None

                if ptype == 'standard':
                    parsed = parse_standard_date(date_text, today)
                elif ptype == 'chinese':
                    parsed = parse_chinese_date(date_text, today)
                elif ptype == 'relative':
                    parsed = parse_relative_date(date_text, today)

                if parsed:
                    context = extract_context(line, date_text)
                    items.append(DateItem(
                        date_str=date_text,
                        context=context,
                        raw_text=line,
                        parsed_date=parsed,
                        relative=(ptype == 'relative'),
                    ))

    # 去重（按日期和上下文）
    seen = set()
    unique_items = []
    for item in items:
        key = (item.parsed_date, item.context)
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    # 计算倒计时
    for item in unique_items:
        if item.parsed_date:
            item.days_until = (item.parsed_date - today).days

    return unique_items


# ============================================================
# 报告格式化
# ============================================================

def format_countdown(days: int) -> str:
    """格式化倒计时"""
    if days < 0:
        return f"已过期 {-days} 天"
    elif days == 0:
        return "就是今天"
    elif days == 1:
        return "明天"
    else:
        return f"{days} 天后"


def urgency_icon(days: int) -> str:
    """根据天数返回紧急度图标"""
    if days < 0:
        return "🔴"  # 已过期
    elif days <= 3:
        return "🔴"  # 3天内
    elif days <= 7:
        return "🟡"  # 一周内
    elif days <= 30:
        return "🟢"  # 一个月内
    else:
        return "⚪"  # 较远


WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def format_date(d: date) -> str:
    """格式化日期显示"""
    return f"{d.month:02d}-{d.day:02d} {WEEKDAY_CN[d.weekday()]}"


def format_report(items: List[DateItem], today: date,
                  within_days: Optional[int] = None,
                  include_overdue: bool = True) -> str:
    """格式化倒计时报告"""
    # 过滤
    upcoming = []
    overdue = []

    for item in items:
        if item.days_until is None:
            continue
        if item.days_until < 0:
            if include_overdue:
                overdue.append(item)
        else:
            if within_days is None or item.days_until <= within_days:
                upcoming.append(item)

    # 排序
    upcoming.sort(key=lambda x: x.days_until)
    overdue.sort(key=lambda x: x.days_until)

    lines = []
    lines.append("=" * 60)
    lines.append("📅 日期与截止事项倒计时清单")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"分析日期：{today.strftime('%Y-%m-%d')}")
    lines.append(f"共发现 {len(upcoming) + len(overdue)} 个日期事项")
    if within_days:
        lines.append(f"筛选范围：未来 {within_days} 天内")
    lines.append("")

    # 即将到来
    if upcoming:
        lines.append("⏳ 即将到来（按时间排序）：")
        lines.append("")
        for item in upcoming:
            icon = urgency_icon(item.days_until)
            lines.append(f"  {icon} {format_countdown(item.days_until)}（{format_date(item.parsed_date)}）")
            lines.append(f"     {item.context}")
            lines.append(f"     原文：\"{item.raw_text[:60]}\"")
            lines.append("")
    else:
        lines.append("✅ 未来一段时间内没有截止事项。")
        lines.append("")

    # 已过期
    if overdue and include_overdue:
        lines.append("⚠ 已过期：")
        lines.append("")
        for item in overdue:
            lines.append(f"  🔴 {format_countdown(item.days_until)}（{format_date(item.parsed_date)}）")
            lines.append(f"     {item.context}")
            lines.append(f"     原文：\"{item.raw_text[:60]}\"")
            lines.append("")

    # 统计
    lines.append("📊 统计：")
    in_7 = sum(1 for i in upcoming if i.days_until <= 7)
    in_30 = sum(1 for i in upcoming if i.days_until <= 30)
    lines.append(f"  未来7天内：{in_7} 项")
    lines.append(f"  未来30天内：{in_30} 项")
    lines.append(f"  已过期：{len(overdue)} 项")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="日期提取与倒计时工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", help="文本文件路径")
    parser.add_argument("--text", "-t", help="直接传入文本")
    parser.add_argument("--within-days", "-w", type=int, default=None,
                        help="只显示未来N天内的事项")
    parser.add_argument("--include-overdue", action="store_true", default=True,
                        help="包含已过期事项（默认开启）")
    parser.add_argument("--hide-overdue", action="store_true",
                        help="不显示已过期事项")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                        help="输出格式（默认text）")
    args = parser.parse_args()

    # 获取文本
    text = ""
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read()

    if not text.strip():
        print("错误：未提供文本。请使用 --file、--text 或 stdin 传入", file=sys.stderr)
        print("用法：", file=sys.stderr)
        print("  python3 extract_dates.py --file notes.txt", file=sys.stderr)
        print("  python3 extract_dates.py --text '报告截止3月15日'", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    items = extract_dates_from_text(text, today)
    include_overdue = not args.hide_overdue

    if args.output == "json":
        result = []
        for item in items:
            result.append({
                "date_text": item.date_str,
                "context": item.context,
                "raw_text": item.raw_text,
                "parsed_date": item.parsed_date.isoformat() if item.parsed_date else None,
                "days_until": item.days_until,
                "relative": item.relative,
            })
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(items, today, args.within_days, include_overdue))


if __name__ == "__main__":
    main()
