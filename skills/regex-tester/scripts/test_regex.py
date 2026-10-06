#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
正则表达式测试脚本

测试正则表达式在样本文本上的匹配结果，支持：
- 查找所有匹配项及位置
- 显示分组捕获内容
- 替换预览
- 正则模式中文解释
- 匹配统计

用法：
  python3 test_regex.py --pattern '\d+' --text "订单12345，金额99.5"
  python3 test_regex.py --pattern '[\w.-]+@[\w.-]+\.\w+' --file sample.txt
  python3 test_regex.py --pattern '(\d{4})-(\d{2})-(\d{2})' --text "2024-01-15"
  python3 test_regex.py --pattern '\d+' --text "2024年1月" --replace '[\d]'
  python3 test_regex.py --pattern '\d{3}-\d{4}-\d{4}' --explain
  echo "电话13812345678" | python3 test_regex.py --pattern '1[3-9]\d{9}'
"""

import argparse
import re
import sys
from typing import List, Optional, Tuple


# ============================================================
# 正则模式解释器
# ============================================================

# 正则语法元素及其中文说明
REGEX_EXPLANATIONS = [
    # 锚点
    (r'\\b', '单词边界（匹配单词与非单词字符之间的位置）'),
    (r'\\B', '非单词边界'),
    (r'\^', '行首/字符串开头锚点'),
    (r'\$', '行尾/字符串结尾锚点'),
    # 字符类
    (r'\\d', '数字（0-9）'),
    (r'\\D', '非数字字符'),
    (r'\\w', '单词字符（字母、数字、下划线）'),
    (r'\\W', '非单词字符'),
    (r'\\s', '空白字符（空格、制表符、换行等）'),
    (r'\\S', '非空白字符'),
    (r'\\n', '换行符'),
    (r'\\t', '制表符'),
    (r'\.', '任意字符（除换行符）'),
    # 量词
    (r'\*', '0次或多次（贪婪匹配）'),
    (r'\+', '1次或多次（贪婪匹配）'),
    (r'\?', '0次或1次（可选）'),
    (r'\{(\d+)\}', '恰好匹配 N 次'),
    (r'\{(\d+),\}', '至少匹配 N 次'),
    (r'\{(\d+),(\d+)\}', '匹配 N 到 M 次'),
    (r'\*\?', '0次或多次（惰性匹配）'),
    (r'\+\?', '1次或多次（惰性匹配）'),
    (r'\?\?', '0次或1次（惰性匹配）'),
    # 分组
    (r'\(\?P<(\w+)>', '命名分组（组名：\\1）'),
    (r'\(\?:', '非捕获分组（仅分组不捕获）'),
    (r'\(\?=', '正向先行断言（后面必须匹配）'),
    (r'\(\?!', '负向先行断言（后面不能匹配）'),
    (r'\(\?<=', '正向后行断言（前面必须匹配）'),
    (r'\(\?<!', '负向后行断言（前面不能匹配）'),
    (r'\(', '捕获分组开始'),
    (r'\)', '分组结束'),
    # 其他
    (r'\[', '字符类开始（匹配其中任一字符）'),
    (r'\]', '字符类结束'),
    (r'\[\^', '否定字符类开始（匹配其中以外的字符）'),
    (r'\|', '或（匹配左侧或右侧）'),
    (r'\\(\d+)', '反向引用第 N 个分组'),
    (r'\\/', '字面量：斜杠'),
]


def explain_pattern(pattern: str) -> List[Tuple[str, str]]:
    """将正则模式逐部分解释为中文"""
    explanations = []
    remaining = pattern
    i = 0

    while i < len(remaining):
        matched = False
        for regex, desc in REGEX_EXPLANATIONS:
            m = re.match(regex, remaining[i:])
            if m:
                token = m.group(0)
                if len(m.groups()) > 0:
                    # 有量词参数的，补充说明
                    if '{n}' in desc or 'N 次' in desc:
                        desc = desc.replace('N', m.group(1))
                    if 'M 次' in desc:
                        desc = desc.replace('N', m.group(1)).replace('M', m.group(2))
                explanations.append((token, desc))
                i += len(token)
                matched = True
                break

        if not matched:
            ch = remaining[i]
            if ch == '\\' and i + 1 < len(remaining):
                # 转义字符
                next_ch = remaining[i + 1]
                explanations.append((f'\\{next_ch}', f'转义字符：{next_ch}'))
                i += 2
            elif ch in '[]-':
                explanations.append((ch, '字符类相关符号'))
                i += 1
            else:
                # 普通字符
                explanations.append((ch, f'字面量：{ch}'))
                i += 1

    return explanations


# ============================================================
# 正则测试器
# ============================================================

def test_pattern(pattern: str, text: str, flags: int = 0) -> List[dict]:
    """测试正则，返回所有匹配"""
    matches = []
    try:
        for m in re.finditer(pattern, text, flags):
            match_info = {
                'start': m.start(),
                'end': m.end(),
                'group': m.group(),
                'groups': m.groups(),
                'groupdict': m.groupdict(),
            }
            matches.append(match_info)
        return matches
    except re.error as e:
        print(f"❌ 正则语法错误：{e}", file=sys.stderr)
        sys.exit(1)


def replace_pattern(pattern: str, text: str, replacement: str, flags: int = 0) -> str:
    """测试正则替换"""
    try:
        return re.sub(pattern, replacement, text, flags=flags)
    except re.error as e:
        print(f"❌ 正则语法错误：{e}", file=sys.stderr)
        sys.exit(1)


# ============================================================
# 报告格式化
# ============================================================

def format_test_result(pattern: str, text: str, matches: List[dict]) -> str:
    """格式化测试结果"""
    lines = []
    lines.append("=" * 60)
    lines.append("🔍 正则测试结果")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"模式：`{pattern}`")
    lines.append(f"文本：{text[:80]}{'...' if len(text) > 80 else ''}")
    lines.append("")

    if not matches:
        lines.append("⚠ 未找到任何匹配。")
        lines.append("")
        lines.append("可能原因：")
        lines.append("  - 正则模式与文本不匹配")
        lines.append("  - 转义字符问题（注意 \\d 在字符串中需要写为 \\\\d）")
        lines.append("  - 大小写敏感（可尝试 re.IGNORECASE）")
        lines.append("  - 多行模式（^ 和 $ 的行为）")
        return "\n".join(lines)

    lines.append(f"📊 匹配数量：{len(matches)}")
    lines.append("")

    for i, m in enumerate(matches[:20], 1):
        lines.append(f"匹配 {i}：")
        lines.append(f"  位置：{m['start']}-{m['end']}")
        lines.append(f"  完整匹配：`{m['group']}`")
        if m['groups']:
            for j, g in enumerate(m['groups'], 1):
                lines.append(f"  分组 {j}：`{g}`")
        if m['groupdict']:
            for name, g in m['groupdict'].items():
                lines.append(f"  分组 '{name}'：`{g}`")
        lines.append("")

    if len(matches) > 20:
        lines.append(f"... 还有 {len(matches) - 20} 个匹配未显示")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_explain_result(pattern: str) -> str:
    """格式化正则解释"""
    lines = []
    lines.append("=" * 60)
    lines.append("📖 正则模式解释")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"模式：`{pattern}`")
    lines.append("")
    lines.append("逐部分拆解：")
    lines.append("-" * 40)

    explanations = explain_pattern(pattern)
    for token, desc in explanations:
        lines.append(f"  `{token:<12}`  {desc}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_replace_result(pattern: str, text: str, replacement: str, result: str) -> str:
    """格式化替换结果"""
    lines = []
    lines.append("=" * 60)
    lines.append("🔄 正则替换预览")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"模式：`{pattern}`")
    lines.append(f"替换为：`{replacement}`")
    lines.append("")
    lines.append(f"原文本：{text[:80]}")
    lines.append(f"替换后：{result[:80]}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================
# 常用正则配方
# ============================================================

RECIPES = {
    "email": {
        "pattern": r'[\w.-]+@[\w.-]+\.\w+',
        "desc": "邮箱地址",
        "example": "test.user@example.com",
    },
    "phone": {
        "pattern": r'1[3-9]\d{9}',
        "desc": "中国手机号",
        "example": "13812345678",
    },
    "url": {
        "pattern": r'https?://[\w.-]+(?::\d+)?(?:/[^\s]*)?',
        "desc": "HTTP/HTTPS URL",
        "example": "https://www.example.com/path",
    },
    "ipv4": {
        "pattern": r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
        "desc": "IPv4 地址",
        "example": "192.168.1.1",
    },
    "date": {
        "pattern": r'\d{4}-\d{2}-\d{2}',
        "desc": "日期 YYYY-MM-DD",
        "example": "2024-01-15",
    },
    "idcard": {
        "pattern": r'\d{17}[\dXx]',
        "desc": "18位身份证号",
        "example": "110101199001011234",
    },
    "qq": {
        "pattern": r'[1-9]\d{4,11}',
        "desc": "QQ号（5-12位）",
        "example": "123456789",
    },
    "chinese": {
        "pattern": r'[\u4e00-\u9fa5]+',
        "desc": "中文字符",
        "example": "你好世界",
    },
    "color": {
        "pattern": r'#(?:[0-9a-fA-F]{3}){1,2}',
        "desc": "十六进制颜色",
        "example": "#FF5733",
    },
    "zipcode": {
        "pattern": r'[1-9]\d{5}',
        "desc": "邮政编码（6位）",
        "example": "100000",
    },
}


def show_recipes():
    """显示所有常用正则配方"""
    lines = []
    lines.append("=" * 60)
    lines.append("💡 常用正则配方")
    lines.append("=" * 60)
    lines.append("")
    for name, recipe in RECIPES.items():
        lines.append(f"【{recipe['desc']}】")
        lines.append(f"  正则：`{recipe['pattern']}`")
        lines.append(f"  示例：{recipe['example']}")
        lines.append("")
    lines.append("用法：python3 test_regex.py --pattern '<正则>' --text '<测试文本>'")
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="正则表达式测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pattern", "-p", help="正则表达式模式")
    parser.add_argument("--text", "-t", help="待匹配的文本")
    parser.add_argument("--file", "-f", help="从文件读取待匹配文本")
    parser.add_argument("--replace", "-r", help="替换为指定字符串")
    parser.add_argument("--explain", "-e", action="store_true",
                        help="解释正则模式各部分含义")
    parser.add_argument("--recipes", action="store_true",
                        help="显示常用正则配方")
    parser.add_argument("--ignore-case", "-i", action="store_true",
                        help="忽略大小写")
    parser.add_argument("--multiline", "-m", action="store_true",
                        help="多行模式（^ 和 $ 匹配每行首尾）")
    parser.add_argument("--dotall", "-s", action="store_true",
                        help=". 匹配换行符")
    args = parser.parse_args()

    # 显示配方
    if args.recipes:
        print(show_recipes())
        return

    if not args.pattern:
        print("错误：请提供正则模式（--pattern）", file=sys.stderr)
        print("用法：", file=sys.stderr)
        print("  python3 test_regex.py --pattern '\\d+' --text '订单12345'", file=sys.stderr)
        print("  python3 test_regex.py --recipes", file=sys.stderr)
        sys.exit(1)

    # 解释模式
    if args.explain:
        print(format_explain_result(args.pattern))
        return

    # 获取待匹配文本
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"错误：文件不存在 - {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("错误：待匹配文本为空", file=sys.stderr)
        sys.exit(1)

    # 构建 flags
    flags = 0
    if args.ignore_case:
        flags |= re.IGNORECASE
    if args.multiline:
        flags |= re.MULTILINE
    if args.dotall:
        flags |= re.DOTALL

    # 替换模式
    if args.replace:
        result = replace_pattern(args.pattern, text, args.replace, flags)
        print(format_replace_result(args.pattern, text, args.replace, result))
    else:
        # 测试匹配
        matches = test_pattern(args.pattern, text, flags)
        print(format_test_result(args.pattern, text, matches))


if __name__ == "__main__":
    main()
