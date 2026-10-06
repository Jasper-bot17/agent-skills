#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 数据清洗脚本

读取 CSV/TSV 文件，检测数据质量问题并执行清洗。
支持三种模式：analyze（仅检测）、dry-run（预览）、execute（执行）。

用法：
  python3 clean_csv.py --input data.csv --mode analyze
  python3 clean_csv.py --input data.csv --mode dry-run
  python3 clean_csv.py --input data.csv --mode execute --output cleaned.csv
  python3 clean_csv.py --input data.csv --mode execute --missing-strategy fill_na
  python3 clean_csv.py --input data.csv --mode execute --remove-duplicates --trim-whitespace
"""

import argparse
import csv
import io
import os
import re
import sys
from collections import Counter
from datetime import datetime
from statistics import mean, median, stdev
from typing import Dict, List, Optional, Tuple


# ============================================================
# 工具函数
# ============================================================

# 缺失值标记
MISSING_TOKENS = {"", " ", "na", "n/a", "n.a", "null", "none", "nil",
                  "nan", "undefined", "-", "--", "未知", "无", "不适用"}

# 日期格式模式
DATE_PATTERNS = [
    (r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$', '%Y-%m-%d', ['-', '/']),
    (r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', None, ['-', '/']),  # 月/日/年 or 日/月/年
    (r'^\d{4}年\d{1,2}月\d{1,2}日$', None, None),
    (r'^\d{4}\d{2}\d{2}$', '%Y%m%d', None),
]


def is_missing(value: str) -> bool:
    """判断值是否为缺失"""
    return value.strip().lower() in MISSING_TOKENS


def try_numeric(value: str) -> Optional[float]:
    """尝试将值转换为数值，失败返回 None"""
    if is_missing(value):
        return None
    # 去除千分位逗号和货币符号
    cleaned = re.sub(r'[¥$€£,，\s]', '', value)
    try:
        return float(cleaned)
    except ValueError:
        return None


def try_date(value: str) -> Optional[str]:
    """尝试将值解析为日期，返回标准化的 YYYY-MM-DD 或 None"""
    if is_missing(value):
        return None
    value = value.strip()

    # 尝试常见格式
    formats = [
        '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
        '%m/%d/%Y', '%d/%m/%Y',
        '%Y年%m月%d日',
        '%Y%m%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def detect_delimiter(filepath: str) -> str:
    """自动检测 CSV 分隔符"""
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        sample = f.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        return dialect.delimiter
    except csv.Error:
        # 默认逗号
        return ','


def detect_encoding(filepath: str) -> str:
    """自动检测文件编码"""
    encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                f.read(8192)
            return enc
        except (UnicodeDecodeError, UnicodeError):
            continue
    return 'utf-8'


# ============================================================
# 列类型推断
# ============================================================

def infer_column_types(rows: List[List[str]], sample_size: int = 100) -> List[str]:
    """推断每列的类型：numeric / date / text / boolean"""
    if not rows:
        return []

    ncols = len(rows[0])
    types = []
    sample = rows[:sample_size]

    for col_idx in range(ncols):
        col_values = [r[col_idx] for r in sample if col_idx < len(r) and not is_missing(r[col_idx])]
        if not col_values:
            types.append("text")
            continue

        numeric_count = sum(1 for v in col_values if try_numeric(v) is not None)
        date_count = sum(1 for v in col_values if try_date(v) is not None)
        boolean_count = sum(1 for v in col_values if v.strip().lower() in
                           {"true", "false", "yes", "no", "是", "否", "1", "0"})

        if numeric_count / len(col_values) > 0.8:
            types.append("numeric")
        elif date_count / len(col_values) > 0.8:
            types.append("date")
        elif boolean_count / len(col_values) > 0.8:
            types.append("boolean")
        else:
            types.append("text")

    return types


# ============================================================
# CSV 分析器
# ============================================================

class CSVCleaner:
    """CSV 数据清洗器"""

    def __init__(self, filepath: str, missing_strategy: str = "fill_na",
                 remove_duplicates: bool = True, trim_whitespace: bool = True):
        self.filepath = filepath
        self.missing_strategy = missing_strategy
        self.remove_duplicates = remove_duplicates
        self.trim_whitespace = trim_whitespace

        self.encoding = detect_encoding(filepath)
        self.delimiter = detect_delimiter(filepath)

        self.header: List[str] = []
        self.rows: List[List[str]] = []
        self.column_types: List[str] = []

        self.issues: List[dict] = []
        self.actions: List[dict] = []
        self.original_row_count = 0
        self.cleaned_row_count = 0

    def load(self):
        """读取 CSV 文件"""
        with open(self.filepath, 'r', encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            all_rows = list(reader)

        if not all_rows:
            print("错误：文件为空", file=sys.stderr)
            sys.exit(1)

        # 处理 BOM
        self.header = [h.strip().lstrip('\ufeff') for h in all_rows[0]]
        self.rows = all_rows[1:]
        self.original_row_count = len(self.rows)

        # 推断列类型
        self.column_types = infer_column_types(self.rows)

    def analyze(self) -> dict:
        """分析数据质量问题"""
        self._detect_empty_rows()
        self._detect_duplicates()
        self._detect_missing_values()
        self._detect_whitespace()
        self._detect_type_mismatches()
        self._detect_outliers()
        return {
            "issues": self.issues,
            "header": self.header,
            "column_types": self.column_types,
            "row_count": self.original_row_count,
            "col_count": len(self.header),
        }

    def clean(self) -> List[List[str]]:
        """执行清洗，返回清洗后的行数据"""
        cleaned_rows = []
        seen = set()

        for row in self.rows:
            # 跳过空行
            if all(is_missing(v) for v in row):
                self.actions.append({"action": "删除空行", "detail": f"行: {row[:3]}"})
                continue

            # 跳过列数不一致的行
            if len(row) != len(self.header):
                self.issues.append({
                    "severity": "high",
                    "type": "列数不一致",
                    "detail": f"行有{len(row)}列，应为{len(self.header)}列",
                })
                continue

            # 去除首尾空格
            if self.trim_whitespace:
                row = [v.strip() if isinstance(v, str) else v for v in row]

            # 去重
            if self.remove_duplicates:
                row_key = tuple(row)
                if row_key in seen:
                    self.actions.append({"action": "删除重复行", "detail": str(row[:3])})
                    continue
                seen.add(row_key)

            cleaned_rows.append(row)

        # 处理缺失值
        cleaned_rows = self._handle_missing_values(cleaned_rows)

        self.cleaned_row_count = len(cleaned_rows)
        return cleaned_rows

    def _detect_empty_rows(self):
        """检测空行"""
        empty_count = sum(1 for row in self.rows if all(is_missing(v) for v in row))
        if empty_count > 0:
            self.issues.append({
                "severity": "low",
                "type": "空行",
                "detail": f"{empty_count} 个完全为空的行",
            })

    def _detect_duplicates(self):
        """检测重复行"""
        seen = set()
        dup_count = 0
        for row in self.rows:
            key = tuple(row)
            if key in seen:
                dup_count += 1
            else:
                seen.add(key)
        if dup_count > 0:
            self.issues.append({
                "severity": "high",
                "type": "完全重复行",
                "detail": f"{dup_count} 行与其他行完全相同",
            })

    def _detect_missing_values(self):
        """检测缺失值"""
        for col_idx, col_name in enumerate(self.header):
            missing_count = 0
            total = len(self.rows)
            for row in self.rows:
                if col_idx < len(row) and is_missing(row[col_idx]):
                    missing_count += 1
            if missing_count > 0:
                pct = missing_count / total * 100 if total > 0 else 0
                severity = "high" if pct > 30 else ("medium" if pct > 5 else "low")
                self.issues.append({
                    "severity": severity,
                    "type": "缺失值",
                    "detail": f"'{col_name}'列有 {missing_count} 个缺失值（{pct:.1f}%）",
                })

    def _detect_whitespace(self):
        """检测首尾空格"""
        count = 0
        examples = []
        for row in self.rows[:200]:  # 采样前200行
            for v in row:
                if isinstance(v, str) and v != v.strip() and v.strip():
                    count += 1
                    if len(examples) < 3:
                        examples.append(f"'{v}' → '{v.strip()}'")
        if count > 0:
            self.issues.append({
                "severity": "medium",
                "type": "首尾空格",
                "detail": f"采样中发现 {count} 个带首尾空格的值（如: {'; '.join(examples)}）",
            })

    def _detect_type_mismatches(self):
        """检测类型不匹配"""
        for col_idx, col_name in enumerate(self.header):
            col_type = self.column_types[col_idx] if col_idx < len(self.column_types) else "text"
            if col_type == "numeric":
                non_numeric = 0
                examples = []
                for row in self.rows[:200]:
                    if col_idx < len(row) and not is_missing(row[col_idx]):
                        if try_numeric(row[col_idx]) is None:
                            non_numeric += 1
                            if len(examples) < 3:
                                examples.append(row[col_idx])
                if non_numeric > 0:
                    self.issues.append({
                        "severity": "medium",
                        "type": "数值列类型不匹配",
                        "detail": f"'{col_name}'列（数值型）有 {non_numeric} 个非数值值（如: {examples}）",
                    })

    def _detect_outliers(self):
        """检测数值列异常值"""
        for col_idx, col_name in enumerate(self.header):
            if col_idx >= len(self.column_types):
                continue
            if self.column_types[col_idx] != "numeric":
                continue
            values = []
            for row in self.rows:
                if col_idx < len(row):
                    v = try_numeric(row[col_idx])
                    if v is not None:
                        values.append(v)
            if len(values) < 10:
                continue
            avg = mean(values)
            std = stdev(values) if len(values) > 1 else 0
            if std == 0:
                continue
            threshold = 3 * std
            outliers = [v for v in values if abs(v - avg) > threshold]
            if outliers:
                self.issues.append({
                    "severity": "low",
                    "type": "数值异常值",
                    "detail": f"'{col_name}'列有 {len(outliers)} 个异常值（均值{avg:.1f}，超出±3σ），如: {outliers[:3]}",
                })

    def _handle_missing_values(self, rows: List[List[str]]) -> List[List[str]]:
        """处理缺失值"""
        if self.missing_strategy == "ignore":
            return rows

        for col_idx, col_name in enumerate(self.header):
            if col_idx >= len(self.column_types):
                continue
            col_type = self.column_types[col_idx]

            # 收集该列的有效值
            valid_values = []
            for row in rows:
                if col_idx < len(row) and not is_missing(row[col_idx]):
                    if col_type == "numeric":
                        v = try_numeric(row[col_idx])
                        if v is not None:
                            valid_values.append(v)
                    else:
                        valid_values.append(row[col_idx])

            if not valid_values:
                continue

            # 根据策略填充
            fill_value = None
            if self.missing_strategy == "fill_na":
                fill_value = "N/A" if col_type == "text" else ""
            elif self.missing_strategy == "fill_mean" and col_type == "numeric":
                fill_value = str(mean(valid_values))
            elif self.missing_strategy == "fill_median" and col_type == "numeric":
                fill_value = str(median(valid_values))
            elif self.missing_strategy == "forward":
                # 前向填充
                last_valid = ""
                for row in rows:
                    if col_idx < len(row):
                        if is_missing(row[col_idx]):
                            row[col_idx] = last_valid
                        else:
                            last_valid = row[col_idx]
                continue
            elif self.missing_strategy == "drop":
                # 删除含缺失值的行
                rows = [r for r in rows if col_idx >= len(r) or not is_missing(r[col_idx])]
                continue

            if fill_value is not None:
                filled = 0
                for row in rows:
                    if col_idx < len(row) and is_missing(row[col_idx]):
                        row[col_idx] = fill_value
                        filled += 1
                if filled > 0:
                    self.actions.append({
                        "action": f"缺失值填充({self.missing_strategy})",
                        "detail": f"'{col_name}'列填充 {filled} 个值为: {fill_value}",
                    })

        return rows


# ============================================================
# 报告格式化
# ============================================================

def format_analyze_report(result: dict) -> str:
    """格式化为分析报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 CSV 数据检测报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"行数: {result['row_count']} | 列数: {result['col_count']}")
    lines.append("")

    # 列信息
    lines.append("📋 列信息:")
    lines.append(f"  {'列名':<20} {'类型':<8}")
    lines.append("  " + "-" * 30)
    for name, ctype in zip(result["header"], result["column_types"]):
        lines.append(f"  {name:<20} {ctype:<8}")
    lines.append("")

    # 问题列表
    if result["issues"]:
        lines.append(f"⚠ 发现 {len(result['issues'])} 个问题:")
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for i, issue in enumerate(result["issues"], 1):
            icon = severity_icon.get(issue["severity"], "⚪")
            lines.append(f"  {i}. {icon} [{issue['type']}] {issue['detail']}")
    else:
        lines.append("✅ 未发现明显数据质量问题。")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_clean_report(cleaner: CSVCleaner, cleaned_rows: List[List[str]]) -> str:
    """格式化为清洗报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("✅ CSV 数据清洗报告")
    lines.append("=" * 60)
    lines.append("")

    lines.append("📈 清洗前后对比:")
    lines.append(f"  {'指标':<15} {'清洗前':>10} {'清洗后':>10}")
    lines.append("  " + "-" * 40)
    lines.append(f"  {'行数':<15} {cleaner.original_row_count:>10} {cleaner.cleaned_row_count:>10}")
    lines.append(f"  {'列数':<15} {len(cleaner.header):>10} {len(cleaner.header):>10}")
    lines.append("")

    if cleaner.actions:
        lines.append(f"🔧 执行的操作 ({len(cleaner.actions)} 项):")
        for action in cleaner.actions:
            lines.append(f"  ✅ {action['action']}: {action['detail']}")
    else:
        lines.append("ℹ 未执行清洗操作。")
    lines.append("")

    if cleaner.issues:
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        lines.append(f"📋 检测到的问题 ({len(cleaner.issues)} 项):")
        for issue in cleaner.issues:
            icon = severity_icon.get(issue["severity"], "⚪")
            lines.append(f"  {icon} [{issue['type']}] {issue['detail']}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="CSV 数据清洗工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", required=True, help="输入 CSV 文件路径")
    parser.add_argument("--output", "-o", help="输出清洗后 CSV 文件路径")
    parser.add_argument("--mode", "-m", choices=["analyze", "dry-run", "execute"],
                        default="analyze", help="运行模式（默认 analyze）")
    parser.add_argument("--missing-strategy", choices=[
                        "fill_na", "fill_mean", "fill_median",
                        "forward", "drop", "ignore"],
                        default="fill_na", help="缺失值处理策略（默认 fill_na）")
    parser.add_argument("--remove-duplicates", action="store_true", default=True,
                        help="删除完全重复行（默认开启）")
    parser.add_argument("--keep-duplicates", action="store_true",
                        help="保留重复行")
    parser.add_argument("--trim-whitespace", action="store_true", default=True,
                        help="去除首尾空格（默认开启）")
    parser.add_argument("--output-report", "-r", help="将清洗报告写入文件")
    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误：文件不存在 - {args.input}", file=sys.stderr)
        sys.exit(1)

    # 处理参数
    remove_dups = not args.keep_duplicates
    trim_ws = args.trim_whitespace

    # 创建清洗器
    cleaner = CSVCleaner(
        args.input,
        missing_strategy=args.missing_strategy,
        remove_duplicates=remove_dups,
        trim_whitespace=trim_ws,
    )

    # 读取数据
    print(f"读取文件: {args.input}", file=sys.stderr)
    print(f"编码: {cleaner.encoding} | 分隔符: '{cleaner.delimiter}'", file=sys.stderr)
    cleaner.load()
    print(f"读取完成: {cleaner.original_row_count} 行, {len(cleaner.header)} 列", file=sys.stderr)

    # 分析
    result = cleaner.analyze()

    if args.mode == "analyze":
        report = format_analyze_report(result)
        print(report)
        return

    # 清洗
    cleaned_rows = cleaner.clean()

    if args.mode == "dry-run":
        print("🔍 Dry-run 模式（预览，不写文件）", file=sys.stderr)
        report = format_clean_report(cleaner, cleaned_rows)
        print(report)
        print("")
        print("清洗后前5行预览:")
        for row in cleaned_rows[:5]:
            print("  | " + " | ".join(str(v)[:20] for v in row))
        return

    if args.mode == "execute":
        if not args.output:
            # 默认输出文件名
            base, ext = os.path.splitext(args.input)
            args.output = f"{base}_cleaned{ext or '.csv'}"

        # 写入清洗后文件
        with open(args.output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=cleaner.delimiter)
            writer.writerow(cleaner.header)
            writer.writerows(cleaned_rows)

        report = format_clean_report(cleaner, cleaned_rows)
        print(report)
        print(f"\n清洗后文件已保存: {args.output}", file=sys.stderr)

        if args.output_report:
            with open(args.output_report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"清洗报告已保存: {args.output_report}", file=sys.stderr)


if __name__ == "__main__":
    main()
