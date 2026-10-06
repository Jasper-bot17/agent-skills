#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
任务优先级排序脚本

将待办事项按艾森豪威尔矩阵（紧急×重要）分类，综合评分后输出执行顺序。

用法：
  python3 prioritize_tasks.py --file tasks.txt
  python3 prioritize_tasks.py --file tasks.csv --format csv
  python3 prioritize_tasks.py --task "完成报告" --task "回邮件"
  python3 prioritize_tasks.py --file tasks.txt --work-hours 6
  cat tasks.txt | python3 prioritize_tasks.py
  python3 prioritize_tasks.py --file tasks.csv --format csv --output json
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, date
from typing import List, Optional, Tuple


# ============================================================
# 任务数据结构
# ============================================================

class Task:
    """单个任务"""
    def __init__(self, name: str, importance: str = "中", urgency: str = "本周",
                 duration_min: int = 30, deadline: Optional[str] = None,
                 blocks_others: bool = False, note: str = ""):
        self.name = name
        self.importance = importance  # 高/中/低
        self.urgency = urgency       # 立即/本周/本月/无
        self.duration_min = duration_min
        self.deadline = deadline     # YYYY-MM-DD 或 None
        self.blocks_others = blocks_others
        self.note = note
        self.score = 0.0
        self.quadrant = ""

    def __repr__(self):
        return f"<Task {self.name}>"


# ============================================================
# 文本解析
# ============================================================

# 重要度关键词
HIGH_IMPORTANCE = {"重要", "关键", "核心", "紧急", "必须", "老板", "客户", "项目", "截止", "deadline"}
LOW_IMPORTANCE = {"可以", "有空", "顺便", "不急", "有空再", "可选", "有空的话"}

# 紧急度关键词
URGENT_NOW = {"今天", "今天内", "立即", "马上", "立刻", "now", "今天就要", "今天截止"}
URGENT_WEEK = {"本周", "这周", "周五", "周一", "明天", "后天", "这周内"}
URGENT_MONTH = {"本月", "这个月", "下周", "月底", "月底前"}


def parse_duration(text: str) -> int:
    """从文本中解析预计耗时，返回分钟数"""
    text = text.lower()
    # X小时/X h/Xh
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:小时|h|hour)', text)
    if m:
        return int(float(m.group(1)) * 60)
    # X分钟/X min/X分钟
    m = re.search(r'(\d+)\s*(?:分钟|min|分钟)', text)
    if m:
        return int(m.group(1))
    # X个小时
    m = re.search(r'(\d+(?:\.\d+)?)\s*个?\s*小时', text)
    if m:
        return int(float(m.group(1)) * 60)
    return 30  # 默认30分钟


def parse_deadline(text: str) -> Optional[str]:
    """从文本中解析截止日期"""
    # YYYY-MM-DD 或 YYYY/MM/DD
    m = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def infer_importance(text: str) -> str:
    """推断重要度"""
    for kw in HIGH_IMPORTANCE:
        if kw in text:
            return "高"
    for kw in LOW_IMPORTANCE:
        if kw in text:
            return "低"
    return "中"


def infer_urgency(text: str) -> str:
    """推断紧急度"""
    for kw in URGENT_NOW:
        if kw in text:
            return "立即"
    for kw in URGENT_WEEK:
        if kw in text:
            return "本周"
    for kw in URGENT_MONTH:
        if kw in text:
            return "本月"
    return "无"


def parse_text_tasks(text: str) -> List[Task]:
    """从纯文本解析任务列表"""
    tasks = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # 去掉列表符号
        line = re.sub(r'^[-*•\d.)\s]+', '', line).strip()
        if not line:
            continue

        duration = parse_duration(line)
        deadline = parse_deadline(line)
        importance = infer_importance(line)
        urgency = infer_urgency(line)
        blocks = any(kw in line for kw in {"阻塞", "等待", "别人", "团队在等"})

        # 清理任务名（去掉耗时/日期等附加信息）
        name = re.sub(r'\d+(?:\.\d+)?\s*(?:小时|分钟|h|min)', '', line)
        name = re.sub(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', '', name)
        name = re.sub(r'[（(].*?[）)]', '', name)
        name = name.strip(' ，。、,')

        if name:
            tasks.append(Task(
                name=name,
                importance=importance,
                urgency=urgency,
                duration_min=duration,
                deadline=deadline,
                blocks_others=blocks,
            ))
    return tasks


def parse_csv_tasks(filepath: str) -> List[Task]:
    """从 CSV 解析任务"""
    tasks = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('任务', row.get('task', '')).strip()
            if not name:
                continue
            importance = row.get('重要度', row.get('importance', '中')).strip() or '中'
            urgency = row.get('紧急度', row.get('urgency', '本周')).strip() or '本周'
            duration_str = row.get('预计耗时', row.get('duration', '30分钟')).strip()
            duration = parse_duration(duration_str)
            deadline = row.get('截止日期', row.get('deadline', '')).strip() or None
            note = row.get('备注', row.get('note', '')).strip()
            blocks = any(kw in note for kw in {"阻塞", "等待", "别人在等"})

            tasks.append(Task(
                name=name,
                importance=importance,
                urgency=urgency,
                duration_min=duration,
                deadline=deadline,
                blocks_others=blocks,
                note=note,
            ))
    return tasks


# ============================================================
# 评分与分类
# ============================================================

def days_until(deadline: Optional[str], today: date) -> float:
    """计算距截止日期的天数"""
    if not deadline:
        return 365  # 无截止日期，很远
    try:
        dl = datetime.strptime(deadline, '%Y-%m-%d').date()
        return (dl - today).days
    except ValueError:
        return 365


def importance_score(importance: str) -> float:
    """重要度分数"""
    return {"高": 100, "中": 60, "低": 30}.get(importance, 60)


def urgency_score(urgency: str) -> float:
    """紧急度分数"""
    return {"立即": 100, "本周": 60, "本月": 30, "无": 10}.get(urgency, 60)


def deadline_score(deadline: Optional[str], today: date) -> float:
    """截止日期临近度分数"""
    days = days_until(deadline, today)
    if days < 0:
        return 100  # 已过期
    if days == 0:
        return 100
    if days <= 1:
        return 90
    if days <= 3:
        return 75
    if days <= 7:
        return 55
    if days <= 14:
        return 35
    if days <= 30:
        return 20
    return 10


def duration_penalty(duration_min: int) -> float:
    """耗时惩罚（越长分越低，防止拖延困难任务）"""
    if duration_min <= 30:
        return 100
    if duration_min <= 60:
        return 85
    if duration_min <= 120:
        return 65
    if duration_min <= 180:
        return 45
    return 30


def calculate_score(task: Task, today: date) -> float:
    """计算综合优先级分数（0-100）"""
    dl_score = deadline_score(task.deadline, today)
    imp_score = importance_score(task.importance)
    urg_score = urgency_score(task.urgency)
    dur_penalty = duration_penalty(task.duration_min)
    block_bonus = 20 if task.blocks_others else 0

    score = (
        dl_score * 0.35 +
        imp_score * 0.30 +
        urg_score * 0.20 +
        dur_penalty * 0.10 +
        block_bonus * 0.05
    )
    return round(min(score, 100), 1)


def assign_quadrant(task: Task) -> str:
    """分配到艾森豪威尔象限"""
    important = task.importance in ("高",)
    urgent = task.urgency in ("立即",) or deadline_score(task.deadline, date.today()) >= 75

    if important and urgent:
        return "Q1"
    elif important and not urgent:
        return "Q2"
    elif not important and urgent:
        return "Q3"
    else:
        return "Q4"


# ============================================================
# 报告格式化
# ============================================================

QUADRANT_INFO = {
    "Q1": ("🟥", "立即做", "紧急且重要——今天就做"),
    "Q2": ("🟧", "计划做", "重要不紧急——安排时间专注做"),
    "Q3": ("🟨", "委托/快做", "紧急不重要——批量处理或委托"),
    "Q4": ("🟩", "删除/延后", "不紧急不重要——考虑不做"),
}


def format_duration(minutes: int) -> str:
    """格式化耗时"""
    if minutes < 60:
        return f"{minutes}分钟"
    hours = minutes / 60
    if hours == int(hours):
        return f"{int(hours)}小时"
    return f"{hours:.1f}小时"


def format_deadline(deadline: Optional[str], today: date) -> str:
    """格式化截止日期"""
    if not deadline:
        return "无截止"
    days = days_until(deadline, today)
    if days < 0:
        return f"{deadline}（已逾期{-int(days)}天）"
    if days == 0:
        return f"{deadline}（今天截止）"
    if days == 1:
        return f"{deadline}（明天截止）"
    return f"{deadline}（还剩{int(days)}天）"


def format_report(tasks: List[Task], work_hours: float) -> str:
    """格式化优先级报告"""
    today = date.today()

    # 计算分数和象限
    for task in tasks:
        task.score = calculate_score(task, today)
        task.quadrant = assign_quadrant(task)

    # 按象限分组
    quadrants = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
    for task in tasks:
        quadrants[task.quadrant].append(task)

    # 每个象限内按分数排序
    for q in quadrants.values():
        q.sort(key=lambda t: t.score, reverse=True)

    total_minutes = sum(t.duration_min for t in tasks)
    work_minutes = int(work_hours * 60)

    lines = []
    lines.append("=" * 60)
    lines.append("📋 任务优先级分析报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"总任务数：{len(tasks)} | 总预计耗时：{format_duration(total_minutes)}")
    lines.append(f"每日可用时间：{work_hours}小时")
    lines.append("")

    # 各象限
    for qid in ["Q1", "Q2", "Q3", "Q4"]:
        q_tasks = quadrants[qid]
        icon, qname, qdesc = QUADRANT_INFO[qid]
        q_minutes = sum(t.duration_min for t in q_tasks)
        lines.append(f"{icon} {qname}（{len(q_tasks)}个，共{format_duration(q_minutes)}）")
        lines.append(f"   {qdesc}")
        if not q_tasks:
            lines.append("   （无）")
        for i, t in enumerate(q_tasks, 1):
            dl = format_deadline(t.deadline, today)
            note = f" → {t.note}" if t.note else ""
            if t.blocks_others:
                note += "（阻塞他人）"
            lines.append(f"   {i}. {t.name} [{format_duration(t.duration_min)}] [{dl}]")
            lines.append(f"      评分：{t.score}/100 | 重要度：{t.importance} | 紧急度：{t.urgency}{note}")
        lines.append("")

    # 今日执行建议
    lines.append(f"⏱ 今日执行建议（{work_hours}小时）：")
    remaining = work_minutes
    line_num = 1
    # Q1 全部安排
    for t in quadrants["Q1"]:
        if remaining <= 0:
            break
        actual = min(t.duration_min, remaining)
        lines.append(f"  {line_num}. {t.name}（{format_duration(actual)}）")
        remaining -= actual
        line_num += 1
    # Q2 安排前几个
    for t in quadrants["Q2"]:
        if remaining <= 0:
            break
        if t.duration_min <= remaining:
            lines.append(f"  {line_num}. {t.name}（{format_duration(t.duration_min)}）")
            remaining -= t.duration_min
            line_num += 1
    # Q3 快速处理
    if remaining > 0 and quadrants["Q3"]:
        q3_time = min(remaining, 30)
        q3_names = "、".join(t.name for t in quadrants["Q3"])
        lines.append(f"  {line_num}. 快速处理：{q3_names}（{format_duration(q3_time)}）")
        remaining -= q3_time
        line_num += 1

    if remaining > 0:
        lines.append(f"  （剩余 {format_duration(remaining)} 可用于休息或处理突发）")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="任务优先级排序工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", help="任务文件路径（txt 或 csv）")
    parser.add_argument("--format", choices=["auto", "txt", "csv"], default="auto",
                        help="文件格式（默认自动检测）")
    parser.add_argument("--task", "-t", action="append", default=[],
                        help="直接传入任务（可多次）")
    parser.add_argument("--work-hours", "-w", type=float, default=8.0,
                        help="每日可用工作时间（小时，默认8）")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                        help="输出格式（默认text）")
    args = parser.parse_args()

    tasks = []

    # 从 --task 直接传入
    if args.task:
        for t in args.task:
            tasks.extend(parse_text_tasks(t))

    # 从文件读取
    if args.file:
        fmt = args.format
        if fmt == "auto":
            fmt = "csv" if args.file.endswith(".csv") else "txt"

        if fmt == "csv":
            tasks = parse_csv_tasks(args.file)
        else:
            with open(args.file, 'r', encoding='utf-8') as f:
                tasks = parse_text_tasks(f.read())

    # 从 stdin 读取
    if not tasks and not sys.stdin.isatty():
        text = sys.stdin.read()
        if text.strip():
            tasks = parse_text_tasks(text)

    if not tasks:
        print("错误：未提供任务。请使用 --file、--task 或 stdin 传入任务", file=sys.stderr)
        print("用法：", file=sys.stderr)
        print("  python3 prioritize_tasks.py --file tasks.txt", file=sys.stderr)
        print("  python3 prioritize_tasks.py --task '完成报告' --task '回邮件'", file=sys.stderr)
        sys.exit(1)

    # 输出
    if args.output == "json":
        today = date.today()
        result = []
        for t in tasks:
            t.score = calculate_score(t, today)
            t.quadrant = assign_quadrant(t)
            result.append({
                "name": t.name,
                "importance": t.importance,
                "urgency": t.urgency,
                "duration_min": t.duration_min,
                "deadline": t.deadline,
                "blocks_others": t.blocks_others,
                "score": t.score,
                "quadrant": t.quadrant,
            })
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(tasks, args.work_hours))


if __name__ == "__main__":
    main()
