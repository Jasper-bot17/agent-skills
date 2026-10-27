#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
文本对比工具

比较两段文本或两个文件的差异。

用法：
  python3 text_diff.py file1.txt file2.txt
  python3 text_diff.py --str1 "文本1" --str2 "文本2"
  python3 text_diff.py old.txt new.txt --side-by-side
  python3 text_diff.py old.txt new.txt --ignore-whitespace --ignore-case
  python3 text_diff.py old.txt new.txt --json
"""

import argparse
import difflib
import re
import sys


# ============================================================
# 核心对比类
# ============================================================

class TextDiffer:
    def __init__(self, ignore_whitespace=False, ignore_case=False):
        self.ignore_whitespace = ignore_whitespace
        self.ignore_case = ignore_case

    def _normalize_line(self, line):
        """根据选项预处理行"""
        if self.ignore_whitespace:
            # 去除首尾空白，并将内部连续空白合并为单个空格
            line = re.sub(r"\s+", " ", line.strip())
        if self.ignore_case:
            line = line.lower()
        return line

    def compare(self, text1, text2):
        """比较两段文本，返回结果字典"""
        lines1 = text1.splitlines(keepends=False)
        lines2 = text2.splitlines(keepends=False)

        norm1 = [self._normalize_line(l) for l in lines1]
        norm2 = [self._normalize_line(l) for l in lines2]

        # 用 difflib 计算 opcodes
        sm = difflib.SequenceMatcher(a=norm1, b=norm2, autojunk=False)
        opcodes = sm.get_opcodes()

        # 统计
        added = 0
        removed = 0
        modified = 0
        diff_lines = []

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for k in range(i1, i2):
                    diff_lines.append(("equal", lines1[k], None))
            elif tag == "delete":
                for k in range(i1, i2):
                    removed += 1
                    diff_lines.append(("removed", lines1[k], None))
            elif tag == "insert":
                for k in range(j1, j2):
                    added += 1
                    diff_lines.append(("added", None, lines2[k]))
            elif tag == "replace":
                # 删除的旧行和新增的新行配对
                del_count = i2 - i1
                ins_count = j2 - j1
                pair_count = min(del_count, ins_count)
                for k in range(pair_count):
                    modified += 1
                    diff_lines.append(("modified", lines1[i1 + k], lines2[j1 + k]))
                # 多余的删除行
                for k in range(pair_count, del_count):
                    removed += 1
                    diff_lines.append(("removed", lines1[i1 + k], None))
                # 多余的新增行
                for k in range(pair_count, ins_count):
                    added += 1
                    diff_lines.append(("added", None, lines2[j1 + k]))

        # 相似度
        similarity = sm.ratio() * 100

        return {
            "opcodes": opcodes,
            "diff_lines": diff_lines,
            "added": added,
            "removed": removed,
            "modified": modified,
            "similarity": round(similarity, 1),
            "total_lines1": len(lines1),
            "total_lines2": len(lines2),
        }

    def unified_diff(self, text1, text2, fromfile="旧版本", tofile="新版本"):
        """生成统一 diff 格式"""
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        norm1 = [self._normalize_line(l.rstrip("\n")) for l in lines1]
        norm2 = [self._normalize_line(l.rstrip("\n")) for l in lines2]

        diff = difflib.unified_diff(
            norm1, norm2,
            fromfile=fromfile, tofile=tofile,
            lineterm="",
        )
        return "\n".join(diff)

    def side_by_side(self, text1, text2, width=40):
        """生成并排对比文本"""
        result = self.compare(text1, text2)
        lines = []
        header = f"{'旧版本':<{width}}  |  {'新版本':<{width}}"
        sep = "-" * (width * 2 + 5)
        lines.append(header)
        lines.append(sep)

        for change, old, new in result["diff_lines"]:
            old_str = old if old is not None else ""
            new_str = new if new is not None else ""
            # 截断过长的行
            if len(old_str) > width:
                old_str = old_str[:width - 3] + "..."
            if len(new_str) > width:
                new_str = new_str[:width - 3] + "..."

            if change == "equal":
                tag = "  "
            elif change == "added":
                tag = "+ "
            elif change == "removed":
                tag = "- "
            elif change == "modified":
                tag = "~ "
            else:
                tag = "  "

            lines.append(f"{tag}{old_str:<{width}}  |  {tag}{new_str:<{width}}")

        return "\n".join(lines)

    def compare_files(self, path1, path2):
        """比较两个文件"""
        try:
            with open(path1, "r", encoding="utf-8") as f:
                text1 = f.read()
        except IOError as e:
            return None, f"无法读取文件 {path1}: {e}"
        try:
            with open(path2, "r", encoding="utf-8") as f:
                text2 = f.read()
        except IOError as e:
            return None, f"无法读取文件 {path2}: {e}"
        result = self.compare(text1, text2)
        result["_unified"] = self.unified_diff(text1, text2, path1, path2)
        result["_side"] = self.side_by_side(text1, text2)
        return result, None


# ============================================================
# 彩色输出
# ============================================================

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_colored_diff(result):
    """彩色打印差异"""
    for change, old, new in result["diff_lines"]:
        if change == "equal":
            print(f"  {old}")
        elif change == "added":
            print(f"{Colors.GREEN}+ {new}{Colors.RESET}")
        elif change == "removed":
            print(f"{Colors.RED}- {old}{Colors.RESET}")
        elif change == "modified":
            print(f"{Colors.RED}- {old}{Colors.RESET}")
            print(f"{Colors.GREEN}+ {new}{Colors.RESET}")


def print_stats(result):
    """打印统计摘要"""
    print()
    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"{Colors.BOLD}  对比统计{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*50}{Colors.RESET}")
    print(f"  旧文本行数: {result['total_lines1']}")
    print(f"  新文本行数: {result['total_lines2']}")
    print(f"  {Colors.GREEN}新增行: {result['added']}{Colors.RESET}")
    print(f"  {Colors.RED}删除行: {result['removed']}{Colors.RESET}")
    print(f"  {Colors.YELLOW}修改行: {result['modified']}{Colors.RESET}")
    print(f"  {Colors.CYAN}相似度: {result['similarity']}%{Colors.RESET}")
    print()

    if result['similarity'] == 100:
        print("  ✅ 两段文本完全相同")
    elif result['similarity'] >= 90:
        print("  📝 文本高度相似，仅有少量差异")
    elif result['similarity'] >= 70:
        print("  📄 文本有一定差异")
    else:
        print("  📂 文本差异较大")
    print()


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="文本对比工具")
    parser.add_argument("files", nargs="*", help="两个文件路径")
    parser.add_argument("--str1", help="第一段文本")
    parser.add_argument("--str2", help="第二段文本")
    parser.add_argument("--side-by-side", "-s", action="store_true", help="并排对比模式")
    parser.add_argument("--unified", "-u", action="store_true", help="统一 diff 格式")
    parser.add_argument("--ignore-whitespace", "-w", action="store_true", help="忽略空白差异")
    parser.add_argument("--ignore-case", "-i", action="store_true", help="忽略大小写")
    parser.add_argument("--stats-only", action="store_true", help="只显示统计摘要")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--no-color", action="store_true", help="禁用彩色输出")
    args = parser.parse_args()

    if args.no_color:
        Colors.GREEN = Colors.RED = Colors.YELLOW = Colors.CYAN = Colors.RESET = Colors.BOLD = ""

    differ = TextDiffer(
        ignore_whitespace=args.ignore_whitespace,
        ignore_case=args.ignore_case,
    )

    # 获取文本
    if args.str1 is not None and args.str2 is not None:
        text1 = args.str1
        text2 = args.str2
        fromfile = "文本1"
        tofile = "文本2"
    elif len(args.files) == 2:
        try:
            with open(args.files[0], "r", encoding="utf-8") as f:
                text1 = f.read()
            with open(args.files[1], "r", encoding="utf-8") as f:
                text2 = f.read()
            fromfile = args.files[0]
            tofile = args.files[1]
        except IOError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    result = differ.compare(text1, text2)

    if args.json:
        import json
        output = {
            "from": fromfile,
            "to": tofile,
            "added": result["added"],
            "removed": result["removed"],
            "modified": result["modified"],
            "similarity": result["similarity"],
            "total_lines_old": result["total_lines1"],
            "total_lines_new": result["total_lines2"],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if args.stats_only:
        print_stats(result)
        return

    # 输出差异内容
    print(f"{Colors.BOLD}对比: {fromfile} → {tofile}{Colors.RESET}")
    print()

    if args.side_by_side:
        print(differ.side_by_side(text1, text2))
    elif args.unified:
        print(differ.unified_diff(text1, text2, fromfile, tofile))
    else:
        print_colored_diff(result)

    print_stats(result)


if __name__ == "__main__":
    main()
