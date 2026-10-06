#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Markdown 格式化与质量检查脚本

功能：
- 分析 Markdown 文档（统计 + 语法检查）
- 格式化（表格对齐、标题标准化）
- 生成目录（TOC）
- 检查本地链接

用法：
  python3 format_markdown.py --file doc.md --mode analyze
  python3 format_markdown.py --file doc.md --mode format
  python3 format_markdown.py --file doc.md --mode format --output out.md
  python3 format_markdown.py --file doc.md --toc
  python3 format_markdown.py --file doc.md --check-links
  cat doc.md | python3 format_markdown.py --mode analyze
"""

import argparse
import os
import re
import sys
from typing import List, Tuple, Optional


# ============================================================
# 数据结构
# ============================================================

class MarkdownIssue:
    """文档问题"""
    def __init__(self, severity: str, line: int, message: str):
        self.severity = severity  # high/medium/low
        self.line = line
        self.message = message


class MarkdownStats:
    """文档统计"""
    def __init__(self):
        self.total_chars = 0
        self.chinese_chars = 0
        self.english_words = 0
        self.headings = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        self.paragraphs = 0
        self.code_blocks = 0
        self.tables = 0
        self.links = 0
        self.images = 0
        self.list_items = 0
        self.total_lines = 0


# ============================================================
# 解析器
# ============================================================

def parse_markdown(lines: List[str]) -> Tuple[MarkdownStats, List[MarkdownIssue], List[dict]]:
    """解析 Markdown，返回统计、问题和标题列表"""
    stats = MarkdownStats()
    issues = []
    headings = []  # {level, text, line}

    in_code_block = False
    code_block_start = 0
    in_table = False
    table_header_cols = 0
    table_start_line = 0
    prev_heading_level = 0
    heading_texts = {}  # text -> line

    stats.total_lines = len(lines)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 代码块检测
        if stripped.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_start = i
                stats.code_blocks += 1
                # 检查是否指定了语言
                if len(stripped) == 3:
                    issues.append(MarkdownIssue("low", i, "代码块未指定语言"))
            else:
                in_code_block = False
            continue

        if in_code_block:
            continue

        # 标题检测
        heading_match = re.match(r'^(#{1,6})\s+(.*)', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()

            if not text:
                issues.append(MarkdownIssue("medium", i, "空标题"))
            else:
                headings.append({"level": level, "text": text, "line": i})
                stats.headings[level] = stats.headings.get(level, 0) + 1

                # 标题层级跳跃检测
                if prev_heading_level > 0 and level > prev_heading_level + 1:
                    issues.append(MarkdownIssue("medium", i,
                        f"标题层级跳跃（H{prev_heading_level} → H{level}）"))
                prev_heading_level = level

                # 重复标题检测
                key = f"H{level}:{text}"
                if key in heading_texts:
                    issues.append(MarkdownIssue("low", i,
                        f"重复标题「{text}」（首次出现在第{heading_texts[key]}行）"))
                else:
                    heading_texts[key] = i
            continue

        # 表格检测
        if '|' in stripped and stripped.startswith('|'):
            if not in_table:
                in_table = True
                table_start_line = i
                table_header_cols = stripped.count('|') - 1
            else:
                # 检查是否是分隔行
                if re.match(r'^\|[\s\-:|]+\|$', stripped):
                    # 分隔行列数应与表头一致
                    sep_cols = stripped.count('|') - 1
                    if sep_cols != table_header_cols:
                        issues.append(MarkdownIssue("high", i,
                            f"表格分隔行列数不一致（表头{table_header_cols}列，分隔行{sep_cols}列）"))
                else:
                    # 数据行列数检查
                    data_cols = stripped.count('|') - 1
                    if data_cols != table_header_cols:
                        issues.append(MarkdownIssue("high", i,
                            f"表格列数不一致（表头{table_header_cols}列，本行{data_cols}列）"))
            continue
        else:
            if in_table:
                in_table = False
                stats.tables += 1

        # 链接检测
        links = re.findall(r'\[([^\]]*)\]\(([^)]*)\)', stripped)
        for link_text, url in links:
            stats.links += 1
            if not url.strip():
                issues.append(MarkdownIssue("medium", i, f"空链接「{link_text}」"))

        # 图片检测
        images = re.findall(r'!\[([^\]]*)\]\(([^)]*)\)', stripped)
        stats.images += len(images)

        # 列表项检测
        if re.match(r'^[\-\*\+]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            stats.list_items += 1

        # 段落检测（非空、非标题、非列表、非表格、非引用）
        if stripped and not heading_match and not stripped.startswith(('|', '- ', '* ', '+ ', '>', '```')):
            if not re.match(r'^\d+\.\s+', stripped):
                stats.paragraphs += 1

        # 字数统计
        stats.chinese_chars += len(re.findall(r'[\u4e00-\u9fa5]', line))
        stats.english_words += len(re.findall(r'[a-zA-Z]+', line))

    # 检查未闭合的代码块
    if in_code_block:
        issues.append(MarkdownIssue("high", code_block_start,
            f"未闭合的代码块（从第{code_block_start}行开始）"))

    # 如果最后一行是表格，计入统计
    if in_table:
        stats.tables += 1

    stats.total_chars = stats.chinese_chars + stats.english_words

    return stats, issues, headings


# ============================================================
# 表格格式化
# ============================================================

def get_display_width(text: str) -> int:
    """计算显示宽度（中文字符占2，英文占1）"""
    width = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef':
            width += 2
        else:
            width += 1
    return width


def pad_display(text: str, width: int) -> str:
    """按显示宽度填充空格"""
    current = get_display_width(text)
    return text + ' ' * max(0, width - current)


def format_table(lines: List[str], start: int) -> Tuple[List[str], int]:
    """格式化一个表格，返回格式化后的行和结束行索引"""
    # 收集表格行
    table_lines = []
    i = start
    while i < len(lines) and lines[i].strip().startswith('|'):
        table_lines.append(lines[i].strip())
        i += 1

    if len(table_lines) < 2:
        return lines[start:i], i

    # 解析单元格
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.split('|')[1:-1]]
        rows.append(cells)

    # 计算每列最大宽度
    num_cols = max(len(r) for r in rows)
    col_widths = [0] * num_cols
    for row in rows:
        for j, cell in enumerate(row):
            if j < num_cols:
                col_widths[j] = max(col_widths[j], get_display_width(cell))

    # 第二行是分隔行，特殊处理
    formatted = []
    for idx, row in enumerate(rows):
        if idx == 1 and all(re.match(r'^:?-+:?$', c) for c in row if c):
            # 分隔行
            sep_cells = []
            for j in range(num_cols):
                w = col_widths[j]
                sep_cells.append('-' * max(w, 3))
            formatted.append('| ' + ' | '.join(sep_cells) + ' |')
        else:
            cells = []
            for j in range(num_cols):
                cell = row[j] if j < len(row) else ''
                cells.append(pad_display(cell, col_widths[j]))
            formatted.append('| ' + ' | '.join(cells) + ' |')

    return formatted, i


# ============================================================
# 格式化整个文档
# ============================================================

def format_document(lines: List[str]) -> List[str]:
    """格式化整个 Markdown 文档"""
    result = []
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 代码块保持原样
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            i += 1
            continue

        if in_code_block:
            result.append(line)
            i += 1
            continue

        # 表格格式化
        if stripped.startswith('|') and '|' in stripped:
            formatted_table, end = format_table(lines, i)
            result.extend(formatted_table)
            i = end
            continue

        # 标题标准化（确保 # 后有空格）
        heading_match = re.match(r'^(#{1,6})(\S)', line)
        if heading_match:
            line = heading_match.group(1) + ' ' + line[len(heading_match.group(1)):]

        result.append(line)
        i += 1

    return result


# ============================================================
# 目录生成
# ============================================================

def generate_toc(headings: List[dict]) -> str:
    """根据标题生成目录"""
    if not headings:
        return "（文档中没有标题）"

    lines = ["## 目录", ""]
    for h in headings:
        level = h["level"]
        text = h["text"]
        # 生成 GitHub 风格锚点
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = anchor.replace(' ', '-')
        indent = "  " * (level - 1)
        lines.append(f"{indent}- [{text}](#{anchor})")

    return "\n".join(lines)


# ============================================================
# 链接检查
# ============================================================

def check_links(lines: List[str], filepath: str) -> List[MarkdownIssue]:
    """检查本地文件链接是否存在"""
    issues = []
    base_dir = os.path.dirname(os.path.abspath(filepath)) if filepath else os.getcwd()

    for i, line in enumerate(lines, 1):
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', line)
        for link_text, url in links:
            url = url.strip()
            # 跳过远程链接和锚点
            if url.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            # 移除锚点部分
            url_path = url.split('#')[0]
            if not url_path:
                continue
            full_path = os.path.join(base_dir, url_path)
            if not os.path.exists(full_path):
                issues.append(MarkdownIssue("medium", i,
                    f"断链「{link_text}」→ {url}（文件不存在）"))

    return issues


# ============================================================
# 报告格式化
# ============================================================

SEVERITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def format_analysis_report(stats: MarkdownStats, issues: List[MarkdownIssue],
                           filepath: str) -> str:
    """格式化分析报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 Markdown 文档分析报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"文件：{os.path.basename(filepath) if filepath else '（stdin）'}")
    lines.append(f"总行数：{stats.total_lines}")
    lines.append("")

    # 统计信息
    lines.append("📈 统计信息：")
    lines.append(f"  总字数：{stats.total_chars}（中文{stats.chinese_chars} + 英文{stats.english_words}词）")
    heading_str = ", ".join(f"H{k}:{v}" for k, v in stats.headings.items() if v > 0)
    total_headings = sum(stats.headings.values())
    lines.append(f"  标题数：{total_headings}（{heading_str}）")
    lines.append(f"  段落数：{stats.paragraphs}")
    lines.append(f"  代码块数：{stats.code_blocks}")
    lines.append(f"  表格数：{stats.tables}")
    lines.append(f"  链接数：{stats.links}")
    lines.append(f"  图片数：{stats.images}")
    lines.append(f"  列表项数：{stats.list_items}")
    lines.append("")

    # 问题
    if issues:
        lines.append(f"⚠ 发现的问题（{len(issues)}项）：")
        for i, issue in enumerate(issues, 1):
            icon = SEVERITY_ICON.get(issue.severity, "⚪")
            lines.append(f"  {i}. {icon} [{'高' if issue.severity=='high' else '中' if issue.severity=='medium' else '低'}] 第{issue.line}行：{issue.message}")
        lines.append("")
    else:
        lines.append("✅ 未发现语法问题。")
        lines.append("")

    # 建议
    high_count = sum(1 for i in issues if i.severity == "high")
    medium_count = sum(1 for i in issues if i.severity == "medium")
    if high_count > 0:
        lines.append("✅ 建议：")
        lines.append("  - 优先修复高严重度问题（表格列数不一致、未闭合代码块等）")
        if medium_count > 0:
            lines.append("  - 其次修复中严重度问题（标题跳跃、空链接等）")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Markdown 格式化与质量检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", help="Markdown 文件路径")
    parser.add_argument("--mode", "-m", choices=["analyze", "format"], default="analyze",
                        help="运行模式（默认 analyze）")
    parser.add_argument("--output", "-o", help="格式化输出文件路径")
    parser.add_argument("--toc", action="store_true", help="生成目录")
    parser.add_argument("--check-links", action="store_true", help="检查本地链接")
    args = parser.parse_args()

    # 获取文本
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
        args.file = None
    else:
        print("错误：请提供文件（--file）或通过 stdin 传入", file=sys.stderr)
        sys.exit(1)

    lines = content.split('\n')

    # 解析
    stats, issues, headings = parse_markdown(lines)

    # 链接检查
    if args.check_links and args.file:
        link_issues = check_links(lines, args.file)
        issues.extend(link_issues)

    # 目录生成
    if args.toc:
        print(generate_toc(headings))
        return

    # 模式
    if args.mode == "analyze":
        print(format_analysis_report(stats, issues, args.file or ""))
    elif args.mode == "format":
        formatted = format_document(lines)
        output = "\n".join(formatted)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ 格式化完成，已保存到：{args.output}", file=sys.stderr)
            # 同时输出分析报告
            print(format_analysis_report(stats, issues, args.file or ""))
        else:
            print(output)


if __name__ == "__main__":
    main()
