#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
日志分析脚本

功能：
- 自动识别日志格式（纯文本/JSON/Nginx/Apache/syslog）
- 统计日志级别分布
- 识别高频错误 Top N
- 时间范围分析与过滤
- 错误突增异常检测
- 关键词过滤
- 输出文本报告或 JSON

用法：
  python3 analyze_log.py --file app.log
  python3 analyze_log.py --file app.log --level ERROR,WARN
  python3 analyze_log.py --file app.log --from "2026-09-28 10:00" --to "2026-09-28 12:00"
  python3 analyze_log.py --file app.log --top 20
  python3 analyze_log.py --file app.log --grep "Timeout"
  python3 analyze_log.py --file app.log --format json
  cat app.log | python3 analyze_log.py
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# 日志级别
# ============================================================

LEVEL_PATTERNS = [
    ("FATAL", re.compile(r'\b(FATAL|CRITICAL|EMERGENCY|EMERG)\b', re.IGNORECASE)),
    ("ERROR", re.compile(r'\b(ERROR|ERR|EXCEPTION|FATAL)\b', re.IGNORECASE)),
    ("WARN", re.compile(r'\b(WARN|WARNING)\b', re.IGNORECASE)),
    ("INFO", re.compile(r'\b(INFO|NOTICE)\b', re.IGNORECASE)),
    ("DEBUG", re.compile(r'\b(DEBUG|TRACE|VERBOSE)\b', re.IGNORECASE)),
]

# 时间戳正则（常见格式）
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2026-09-28T14:23:45 or 2026-09-28 14:23:45
    (re.compile(r'(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})'), '%Y-%m-%d %H:%M:%S'),
    # 2026/09/28 14:23:45
    (re.compile(r'(\d{4}/\d{2}/\d{2})[ ](\d{2}:\d{2}:\d{2})'), '%Y/%m/%d %H:%M:%S'),
    # syslog: Sep 28 14:23:45
    (re.compile(r'([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})'), '%b %d %H:%M:%S'),
    # dd/MMM/yyyy:HH:mm:ss (Nginx)
    (re.compile(r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})'), '%d/%b/%Y:%H:%M:%S'),
]


# ============================================================
# 日志行解析
# ============================================================

class LogEntry:
    """单条日志记录"""
    def __init__(self, raw: str, level: str = "UNKNOWN",
                 timestamp: Optional[datetime] = None,
                 message: str = ""):
        self.raw = raw
        self.level = level
        self.timestamp = timestamp
        self.message = message


def detect_level(line: str) -> str:
    """检测日志级别"""
    for level, pattern in LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return "UNKNOWN"


def detect_timestamp(line: str) -> Optional[datetime]:
    """检测时间戳"""
    for pattern, fmt in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if match:
            ts_str = match.group(0).replace('T', ' ')
            try:
                if fmt == '%b %d %H:%M:%S':
                    # syslog 没有年份，假设当前年
                    dt = datetime.strptime(ts_str, fmt)
                    dt = dt.replace(year=datetime.now().year)
                    return dt
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue
    return None


def parse_json_log(line: str) -> Optional[Dict]:
    """尝试解析 JSON 日志行"""
    line = line.strip()
    if line.startswith('{') and line.endswith('}'):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None
    return None


def parse_line(line: str) -> LogEntry:
    """解析单行日志"""
    raw = line.rstrip('\n')
    if not raw.strip():
        return LogEntry(raw, "UNKNOWN", None, "")

    # 尝试 JSON
    json_data = parse_json_log(raw)
    if json_data:
        level = str(json_data.get('level', json_data.get('severity', 'UNKNOWN'))).upper()
        if level not in ('FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG'):
            level = detect_level(raw)
        ts_str = json_data.get('timestamp', json_data.get('time', json_data.get('@timestamp', '')))
        ts = None
        if ts_str:
            ts = detect_timestamp(str(ts_str))
        message = str(json_data.get('message', json_data.get('msg', raw)))
        return LogEntry(raw, level, ts, message)

    # 纯文本
    level = detect_level(raw)
    ts = detect_timestamp(raw)
    return LogEntry(raw, level, ts, raw)


# ============================================================
# 错误消息归一化（用于统计高频错误）
# ============================================================

def normalize_error_message(line: str) -> str:
    """归一化错误消息，去除变量部分以便统计"""
    msg = line.strip()

    # 去除时间戳
    for pattern, _ in TIMESTAMP_PATTERNS:
        msg = pattern.sub('', msg)

    # 去除常见前缀（级别、线程名等）
    msg = re.sub(r'^\s*\[?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.,\d]*\]?\s*', '', msg)
    msg = re.sub(r'^\s*\[[A-Z]+\]\s*', '', msg)
    msg = re.sub(r'^\s*[A-Z]+\s+', '', msg)

    # 去除数字（IP、端口、行号、ID 等）
    msg = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', msg)
    msg = re.sub(r'\b0x[0-9a-fA-F]+\b', '<HEX>', msg)
    msg = re.sub(r'\b\d+\b', '<N>', msg)

    # 去除 UUID
    msg = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', msg, flags=re.IGNORECASE)

    # 去除引号中的路径和值
    msg = re.sub(r"'[^']*'", "'<VAL>'", msg)
    msg = re.sub(r'"[^"]*"', '"<VAL>"', msg)

    # 截断过长消息
    if len(msg) > 200:
        msg = msg[:200] + '...'

    return msg.strip()


# ============================================================
# 分析器
# ============================================================

class LogAnalyzer:
    """日志分析器"""

    def __init__(self):
        self.entries: List[LogEntry] = []
        self.level_counts: Counter = Counter()
        self.error_messages: Counter = Counter()
        self.hourly_counts: Dict[str, Counter] = defaultdict(Counter)
        self.total_lines = 0
        self.parse_failures = 0
        self.earliest_ts: Optional[datetime] = None
        self.latest_ts: Optional[datetime] = None

    def add_line(self, line: str):
        """添加一行日志"""
        self.total_lines += 1
        entry = parse_line(line)
        if entry.level == "UNKNOWN" and not entry.raw.strip():
            self.parse_failures += 1
            return

        self.entries.append(entry)
        self.level_counts[entry.level] += 1

        # 时间统计
        if entry.timestamp:
            if self.earliest_ts is None or entry.timestamp < self.earliest_ts:
                self.earliest_ts = entry.timestamp
            if self.latest_ts is None or entry.timestamp > self.latest_ts:
                self.latest_ts = entry.timestamp
            hour_key = entry.timestamp.strftime('%Y-%m-%d %H:00')
            self.hourly_counts[hour_key][entry.level] += 1

        # 错误消息统计
        if entry.level in ('ERROR', 'FATAL'):
            normalized = normalize_error_message(entry.message or entry.raw)
            if normalized:
                self.error_messages[normalized] += 1

    def analyze(self, top_n: int = 10,
                level_filter: Optional[List[str]] = None,
                from_time: Optional[datetime] = None,
                to_time: Optional[datetime] = None,
                keyword: Optional[str] = None) -> Dict[str, Any]:
        """执行分析"""
        # 过滤
        filtered = self.entries
        if level_filter:
            filtered = [e for e in filtered if e.level in level_filter]
        if from_time:
            filtered = [e for e in filtered if e.timestamp and e.timestamp >= from_time]
        if to_time:
            filtered = [e for e in filtered if e.timestamp and e.timestamp <= to_time]
        if keyword:
            kw = keyword.lower()
            filtered = [e for e in filtered if kw in e.raw.lower()]

        # 重新统计过滤后的数据
        level_counts = Counter(e.level for e in filtered)
        error_messages = Counter()
        hourly_counts = defaultdict(Counter)
        earliest = None
        latest = None

        for e in filtered:
            if e.timestamp:
                if earliest is None or e.timestamp < earliest:
                    earliest = e.timestamp
                if latest is None or e.timestamp > latest:
                    latest = e.timestamp
                hour_key = e.timestamp.strftime('%Y-%m-%d %H:00')
                hourly_counts[hour_key][e.level] += 1
            if e.level in ('ERROR', 'FATAL'):
                normalized = normalize_error_message(e.message or e.raw)
                if normalized:
                    error_messages[normalized] += 1

        # 异常检测：找出错误突增的小时
        anomalies = []
        if hourly_counts:
            error_rates = []
            for hour, counts in sorted(hourly_counts.items()):
                total = sum(counts.values())
                errors = counts.get('ERROR', 0) + counts.get('FATAL', 0)
                rate = errors / total if total > 0 else 0
                error_rates.append((hour, errors, total, rate))

            if error_rates:
                avg_errors = sum(e[1] for e in error_rates) / len(error_rates)
                for hour, errors, total, rate in error_rates:
                    if avg_errors > 0 and errors > avg_errors * 3 and errors >= 5:
                        anomalies.append({
                            "hour": hour,
                            "errors": errors,
                            "total": total,
                            "rate": round(rate * 100, 1),
                            "ratio": round(errors / avg_errors, 1),
                        })

        return {
            "total_lines": self.total_lines,
            "filtered_lines": len(filtered),
            "parse_failures": self.parse_failures,
            "time_range": {
                "earliest": earliest.strftime('%Y-%m-%d %H:%M:%S') if earliest else None,
                "latest": latest.strftime('%Y-%m-%d %H:%M:%S') if latest else None,
            },
            "level_counts": dict(level_counts),
            "top_errors": error_messages.most_common(top_n),
            "hourly_stats": {h: dict(c) for h, c in sorted(hourly_counts.items())},
            "anomalies": anomalies,
        }


# ============================================================
# 报告格式化
# ============================================================

LEVEL_ICONS = {
    "FATAL": "🔴",
    "ERROR": "🔴",
    "WARN": "🟡",
    "INFO": "⚪",
    "DEBUG": "🔵",
    "UNKNOWN": "⚫",
}


def format_report(result: Dict[str, Any], filepath: str) -> str:
    """格式化分析报告"""
    lines = []
    lines.append("📊 日志分析报告")
    lines.append("=" * 50)
    lines.append(f"文件：{os.path.basename(filepath) if filepath else '（stdin）'}")
    lines.append(f"总行数：{result['total_lines']:,}")
    if result['filtered_lines'] != result['total_lines']:
        lines.append(f"过滤后：{result['filtered_lines']:,} 行")
    if result['parse_failures'] > 0:
        pct = result['parse_failures'] / result['total_lines'] * 100
        lines.append(f"解析失败：{result['parse_failures']} 行（{pct:.2f}%）")

    tr = result['time_range']
    if tr['earliest']:
        lines.append(f"时间范围：{tr['earliest']} ~ {tr['latest']}")
    lines.append("")

    # 级别分布
    lines.append("📈 级别分布：")
    total = sum(result['level_counts'].values())
    level_order = ['FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'UNKNOWN']
    for level in level_order:
        count = result['level_counts'].get(level, 0)
        if count > 0:
            pct = count / total * 100 if total > 0 else 0
            icon = LEVEL_ICONS.get(level, "⚫")
            lines.append(f"  {icon} {level:6s}: {count:>8,} ({pct:5.2f}%)")
    lines.append("")

    # 高频错误
    if result['top_errors']:
        lines.append(f"🔴 高频错误 Top {len(result['top_errors'])}：")
        for i, (msg, count) in enumerate(result['top_errors'], 1):
            display = msg[:100] + '...' if len(msg) > 100 else msg
            lines.append(f"  {i}. [{count}次] {display}")
        lines.append("")

    # 异常检测
    if result['anomalies']:
        lines.append("⚠️ 异常检测：")
        for a in result['anomalies']:
            lines.append(f"  - {a['hour']} 错误量突增（{a['errors']}次，为平均值的{a['ratio']}倍，错误率{a['rate']}%）")
        lines.append("")

    # 排查建议
    suggestions = []
    lc = result['level_counts']
    if lc.get('FATAL', 0) > 0:
        suggestions.append(f"存在 {lc['FATAL']} 条 FATAL 级错误，建议立即排查")
    if lc.get('ERROR', 0) > 100:
        suggestions.append(f"错误量较大（{lc['ERROR']}条），建议优先处理高频错误")
    if result['anomalies']:
        suggestions.append(f"发现 {len(result['anomalies'])} 个错误突增时段，建议检查对应时段的部署或变更")
    if result['top_errors']:
        top_err = result['top_errors'][0][0][:60]
        suggestions.append(f"最高频错误：{top_err}")

    if suggestions:
        lines.append("💡 排查建议：")
        for i, s in enumerate(suggestions, 1):
            lines.append(f"  {i}. {s}")
        lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)


# ============================================================
# 时间解析
# ============================================================

def parse_time_arg(s: str) -> Optional[datetime]:
    """解析时间参数"""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="日志分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", help="日志文件路径")
    parser.add_argument("--level", "-l", help="过滤级别，逗号分隔（如 ERROR,WARN）")
    parser.add_argument("--from", dest="from_time", help="起始时间（如 2026-09-28 10:00）")
    parser.add_argument("--to", dest="to_time", help="结束时间（如 2026-09-28 12:00）")
    parser.add_argument("--grep", "-g", help="关键词过滤")
    parser.add_argument("--top", "-n", type=int, default=10, help="高频错误 Top N（默认10）")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    # 获取日志内容
    if args.file:
        with open(args.file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    elif not sys.stdin.isatty():
        lines = sys.stdin.readlines()
        args.file = None
    else:
        print("错误：请提供文件（--file）或通过 stdin 传入", file=sys.stderr)
        sys.exit(1)

    # 解析参数
    level_filter = None
    if args.level:
        level_filter = [l.strip().upper() for l in args.level.split(',')]

    from_time = parse_time_arg(args.from_time) if args.from_time else None
    to_time = parse_time_arg(args.to_time) if args.to_time else None

    if args.from_time and from_time is None:
        print(f"警告：无法解析起始时间 '{args.from_time}'，将忽略时间过滤", file=sys.stderr)
    if args.to_time and to_time is None:
        print(f"警告：无法解析结束时间 '{args.to_time}'，将忽略时间过滤", file=sys.stderr)

    # 分析
    analyzer = LogAnalyzer()
    for line in lines:
        analyzer.add_line(line)

    result = analyzer.analyze(
        top_n=args.top,
        level_filter=level_filter,
        from_time=from_time,
        to_time=to_time,
        keyword=args.grep,
    )

    # 输出
    if args.format == "json":
        # JSON 输出时转换元组为列表
        result['top_errors'] = [{"message": m, "count": c} for m, c in result['top_errors']]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result, args.file or ""))


if __name__ == "__main__":
    main()
