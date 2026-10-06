#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
代码片段管理脚本

功能：
- 扫描目录，提取带 @snippet 标记的代码片段
- 解析片段元数据（标题、描述、标签、语言）
- 按关键词/标签/语言搜索过滤
- 生成 Markdown 格式片段库
- 导出 VS Code 片段格式（JSON）
- 统计语言分布和标签频率

用法：
  python3 manage_snippets.py --dir /path/to/code
  python3 manage_snippets.py --dir /path/to/code --search "排序"
  python3 manage_snippets.py --dir /path/to/code --tag "算法"
  python3 manage_snippets.py --dir /path/to/code --language python
  python3 manage_snippets.py --dir /path/to/code --format markdown --output snippets.md
  python3 manage_snippets.py --dir /path/to/code --format vscode --output cpp.code-snippets
  python3 manage_snippets.py --dir /path/to/code --stats
  python3 manage_snippets.py --dir /path/to/code --format json
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ============================================================
# 语言扩展名映射
# ============================================================

LANGUAGE_EXTENSIONS = {
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".h": "C++", ".hpp": "C++",
    ".c": "C", ".h": "C",
    ".py": "Python", ".pyw": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".sh": "Shell", ".bash": "Shell",
    ".sql": "SQL",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "CSS", ".less": "CSS",
    ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML",
    ".md": "Markdown",
    ".lua": "Lua",
    ".r": "R", ".R": "R",
    ".scala": "Scala",
    ".dart": "Flutter/Dart",
    ".vue": "Vue",
    ".jsx": "React",
}

# 支持的代码文件扩展名
CODE_EXTENSIONS = set(LANGUAGE_EXTENSIONS.keys())

# 最大文件大小（1MB）
MAX_FILE_SIZE = 1024 * 1024


# ============================================================
# 片段数据结构
# ============================================================

class Snippet:
    """代码片段"""
    def __init__(self):
        self.title = ""
        self.description = ""
        self.tags = []
        self.language = ""
        self.category = ""
        self.code = ""
        self.file = ""
        self.line = 0
        self.end_line = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "language": self.language,
            "category": self.category,
            "code": self.code,
            "file": self.file,
            "line": self.line,
            "end_line": self.end_line,
        }


# ============================================================
# 元数据解析
# ============================================================

def parse_single_line_metadata(line: str) -> dict:
    """解析单行 @snippet(title="...", tags=[...]) 格式"""
    result = {}

    # 提取 @snippet(...) 中的内容
    match = re.search(r'@snippet\s*\((.+)\)', line)
    if not match:
        return result

    content = match.group(1)

    # 解析 title="..."
    title_match = re.search(r'title\s*=\s*["\']([^"\']+)["\']', content)
    if title_match:
        result["title"] = title_match.group(1)

    # 解析 desc="..."
    desc_match = re.search(r'desc(?:ription)?\s*=\s*["\']([^"\']+)["\']', content)
    if desc_match:
        result["description"] = desc_match.group(1)

    # 解析 tags=["a","b"]
    tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', content)
    if tags_match:
        tags_str = tags_match.group(1)
        tags = re.findall(r'["\']([^"\']+)["\']', tags_str)
        if not tags:
            # 尝试逗号分隔无引号
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        result["tags"] = tags

    # 解析 language="..."
    lang_match = re.search(r'language\s*=\s*["\']([^"\']+)["\']', content)
    if lang_match:
        result["language"] = lang_match.group(1)

    # 解析 category="..."
    cat_match = re.search(r'category\s*=\s*["\']([^"\']+)["\']', content)
    if cat_match:
        result["category"] = cat_match.group(1)

    return result


def parse_multi_line_metadata(lines: List[str]) -> dict:
    """解析多行 @snippet 后跟 key: value 格式"""
    result = {}
    for line in lines:
        line = line.strip()
        # 去除注释前缀
        line = re.sub(r'^[/*#\s]+', '', line)
        if not line or line.startswith('@'):
            continue

        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip().lower()
            value = value.strip()

            if key == 'title':
                result["title"] = value
            elif key in ('desc', 'description'):
                result["description"] = value
            elif key == 'tags':
                tags = [t.strip() for t in re.split(r'[,，]', value) if t.strip()]
                result["tags"] = tags
            elif key == 'language':
                result["language"] = value
            elif key == 'category':
                result["category"] = value

    return result


# ============================================================
# 片段提取
# ============================================================

def extract_snippets_from_file(filepath: str) -> List[Snippet]:
    """从单个文件提取片段"""
    snippets = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except (OSError, IOError):
        return snippets

    ext = os.path.splitext(filepath)[1].lower()
    inferred_language = LANGUAGE_EXTENSIONS.get(ext, "未知")

    i = 0
    while i < len(lines):
        line = lines[i]

        # 检测 @snippet 开始
        if '@snippet' in line and '@end-snippet' not in line:
            start_line = i + 1  # 1-based
            snippet = Snippet()
            snippet.file = filepath
            snippet.line = start_line
            snippet.language = inferred_language

            # 尝试单行元数据解析
            metadata = parse_single_line_metadata(line)

            # 如果单行没有 title，检查后续行是否有多行元数据
            if "title" not in metadata:
                meta_lines = []
                j = i + 1
                while j < len(lines) and j < i + 10:
                    if '@end-snippet' in lines[j]:
                        break
                    # 检查是否是元数据行（包含 key: value 格式且是注释）
                    if re.match(r'^\s*[/*#]+\s*\w+\s*:', lines[j]):
                        meta_lines.append(lines[j])
                        j += 1
                    else:
                        break
                if meta_lines:
                    multi_meta = parse_multi_line_metadata(meta_lines)
                    metadata.update(multi_meta)
                    i = j - 1  # 调整 i 到元数据最后一行

            # 应用元数据
            if "title" in metadata:
                snippet.title = metadata["title"]
            if "description" in metadata:
                snippet.description = metadata["description"]
            if "tags" in metadata:
                snippet.tags = metadata["tags"]
            if "language" in metadata:
                snippet.language = metadata["language"]
            if "category" in metadata:
                snippet.category = metadata["category"]

            # 如果没有标题，用文件名+行号
            if not snippet.title:
                snippet.title = f"{os.path.basename(filepath)}:{start_line}"

            # 提取代码内容（直到 @end-snippet）
            code_lines = []
            j = i + 1
            while j < len(lines):
                if '@end-snippet' in lines[j]:
                    snippet.end_line = j + 1
                    break
                code_lines.append(lines[j])
                j += 1

            # 去除代码首尾空行
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()

            snippet.code = "".join(code_lines).rstrip()
            snippets.append(snippet)

            i = j + 1
            continue

        i += 1

    return snippets


def scan_directory(dir_path: str, extensions: Optional[set] = None) -> List[Snippet]:
    """扫描目录提取所有片段"""
    all_snippets = []
    abs_dir = os.path.abspath(dir_path)

    for root, dirs, files in os.walk(abs_dir):
        # 跳过常见无关目录
        dirs[:] = [d for d in dirs if d not in (
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', 'out', 'target', '.cache', '.idea', '.vscode'
        )]

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if extensions and ext not in extensions:
                continue
            if ext not in CODE_EXTENSIONS:
                continue

            fpath = os.path.join(root, fname)
            try:
                if os.path.getsize(fpath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            snippets = extract_snippets_from_file(fpath)
            all_snippets.extend(snippets)

    return all_snippets


# ============================================================
# 搜索与过滤
# ============================================================

def filter_snippets(snippets: List[Snippet], search: str = "",
                    tag: str = "", language: str = "",
                    category: str = "") -> List[Snippet]:
    """过滤片段"""
    result = snippets

    if search:
        search_lower = search.lower()
        result = [s for s in result
                  if search_lower in s.title.lower()
                  or search_lower in s.description.lower()
                  or search_lower in s.code.lower()]

    if tag:
        tag_lower = tag.lower()
        result = [s for s in result
                  if any(tag_lower == t.lower() for t in s.tags)]

    if language:
        lang_lower = language.lower()
        result = [s for s in result
                  if lang_lower in s.language.lower()]

    if category:
        cat_lower = category.lower()
        result = [s for s in result
                  if cat_lower in s.category.lower()]

    return result


# ============================================================
# 输出生成
# ============================================================

def generate_markdown(snippets: List[Snippet]) -> str:
    """生成 Markdown 格式片段库"""
    lines = []
    lines.append("# 代码片段库")
    lines.append("")
    lines.append(f"> 共 {len(snippets)} 个代码片段")
    lines.append("")

    # 按语言分组
    by_language = defaultdict(list)
    for s in snippets:
        by_language[s.language].append(s)

    # 目录
    lines.append("## 目录")
    lines.append("")
    for lang in sorted(by_language.keys()):
        anchor = lang.lower().replace("+", "").replace(" ", "-")
        lines.append(f"- [{lang} 片段](#{anchor}-片段)（{len(by_language[lang])} 个）")
        for s in by_language[lang]:
            lines.append(f"  - [{s.title}](#{s.title.lower().replace(' ', '-')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 内容
    for lang in sorted(by_language.keys()):
        lines.append(f"## {lang} 片段")
        lines.append("")

        for s in by_language[lang]:
            lines.append(f"### {s.title}")
            lines.append("")

            if s.description:
                lines.append(f"**描述**：{s.description}")
                lines.append("")

            if s.tags:
                lines.append(f"**标签**：{'、'.join(s.tags)}")
                lines.append("")

            lines.append(f"**文件**：`{s.file}:{s.line}`")
            lines.append("")

            # 代码块
            lang_for_md = lang.lower().replace("++", "pp").replace("c#", "csharp")
            lines.append(f"```{lang_for_md}")
            lines.append(s.code)
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def generate_vscode(snippets: List[Snippet]) -> str:
    """生成 VS Code 片段格式"""
    result = {}

    for s in snippets:
        # 生成 prefix：标题转小写，空格转横杠，保留 Unicode 字符
        prefix = s.title.lower().strip().replace(' ', '-')
        # 去除文件系统不安全字符
        prefix = re.sub(r'[\\/:*?"<>|]', '', prefix)
        if not prefix:
            prefix = f"snippet-{len(result)}"

        # 确保 prefix 唯一
        original_prefix = prefix
        counter = 1
        while prefix in result:
            prefix = f"{original_prefix}-{counter}"
            counter += 1

        # 代码按行分割
        body = s.code.split('\n') if s.code else [""]

        # 描述包含标签
        desc = s.description
        if s.tags:
            tag_str = " [" + ", ".join(s.tags) + "]"
            desc = (desc + tag_str) if desc else tag_str.strip()

        result[s.title] = {
            "prefix": prefix,
            "body": body,
            "description": desc or s.title,
        }

    return json.dumps(result, ensure_ascii=False, indent=2)


def format_list(snippets: List[Snippet]) -> str:
    """格式化片段列表"""
    lines = []
    lines.append("📚 代码片段库")
    lines.append("━" * 40)
    lines.append(f"片段总数：{len(snippets)}")

    # 语言分布
    lang_counts = defaultdict(int)
    for s in snippets:
        lang_counts[s.language] += 1
    if lang_counts:
        dist = ", ".join(f"{lang} {count}个"
                         for lang, count in sorted(lang_counts.items(),
                                                    key=lambda x: x[1], reverse=True))
        lines.append(f"语言分布：{dist}")

    lines.append("")
    lines.append("📋 片段列表：")
    for i, s in enumerate(snippets, 1):
        tags_str = f" — 标签：{', '.join(s.tags)}" if s.tags else ""
        lines.append(f"  {i}. [{s.language}] {s.title}{tags_str}")
        lines.append(f"     文件：{s.file}:{s.line}")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


def format_search_results(snippets: List[Snippet], keyword: str = "") -> str:
    """格式化搜索结果"""
    lines = []
    if keyword:
        lines.append(f"🔍 搜索结果：关键词「{keyword}」")
    else:
        lines.append("🔍 搜索结果")
    lines.append("━" * 40)
    lines.append(f"找到 {len(snippets)} 个匹配片段")
    lines.append("")

    for i, s in enumerate(snippets, 1):
        tags_str = f" — 标签：{', '.join(s.tags)}" if s.tags else ""
        lines.append(f"  {i}. [{s.language}] {s.title}{tags_str}")
        lines.append(f"     文件：{s.file}:{s.line}")

        # 代码预览（前5行）
        code_preview = s.code.split('\n')[:5]
        if code_preview:
            lines.append("     ┌─ 代码预览 ──────────────")
            for cl in code_preview:
                display = cl.rstrip()
                if len(display) > 50:
                    display = display[:47] + "..."
                lines.append(f"     │ {display}")
            if len(s.code.split('\n')) > 5:
                lines.append("     │ ...")
            lines.append("     └──────────────────────────")
        lines.append("")

    lines.append("━" * 40)
    return "\n".join(lines)


def format_stats(snippets: List[Snippet]) -> str:
    """格式化统计信息"""
    lines = []
    lines.append("📊 代码片段统计")
    lines.append("━" * 40)
    lines.append(f"片段总数：{len(snippets)}")

    # 语言分布
    lang_counts = defaultdict(int)
    for s in snippets:
        lang_counts[s.language] += 1
    lines.append("")
    lines.append("📝 语言分布：")
    for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(snippets) * 100 if snippets else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        lines.append(f"  {lang:15s} {count:3d} 个 ({pct:5.1f}%) {bar}")

    # 标签频率
    tag_counts = defaultdict(int)
    for s in snippets:
        for t in s.tags:
            tag_counts[t] += 1
    if tag_counts:
        lines.append("")
        lines.append("🏷️  标签云（Top 15）：")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            lines.append(f"  {tag:20s} × {count}")

    # 片段大小
    if snippets:
        sizes = [len(s.code) for s in snippets]
        avg_size = sum(sizes) / len(sizes)
        lines.append("")
        lines.append("📏 代码量统计：")
        lines.append(f"  总代码行数：{sum(s.code.count(chr(10)) + 1 for s in snippets)} 行")
        lines.append(f"  平均片段大小：{avg_size:.0f} 字符")
        lines.append(f"  最大片段：{max(sizes)} 字符")
        lines.append(f"  最小片段：{min(sizes)} 字符")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="代码片段管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dir", "-d", required=True, help="要扫描的目录路径")
    parser.add_argument("--search", "-s", default="", help="搜索关键词")
    parser.add_argument("--tag", "-t", default="", help="按标签过滤")
    parser.add_argument("--language", "-l", default="", help="按编程语言过滤")
    parser.add_argument("--category", "-c", default="", help="按分类过滤")
    parser.add_argument("--ext", "-e", default="",
                        help="只扫描指定扩展名（逗号分隔，如 .cpp,.h,.py）")
    parser.add_argument("--format", "-f", choices=["list", "markdown", "vscode", "json"],
                        default="list", help="输出格式")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--output", "-o", metavar="FILE", help="输出到文件")
    args = parser.parse_args()

    # 检查目录
    if not os.path.isdir(args.dir):
        print(f"错误：目录不存在：{args.dir}", file=sys.stderr)
        sys.exit(1)

    # 解析扩展名过滤
    extensions = None
    if args.ext:
        extensions = set(e.strip().lower() for e in args.ext.split(",") if e.strip())

    # 扫描
    print(f"正在扫描：{args.dir} ...", file=sys.stderr)
    snippets = scan_directory(args.dir, extensions)
    print(f"找到 {len(snippets)} 个片段", file=sys.stderr)

    # 过滤
    filtered = filter_snippets(snippets, search=args.search, tag=args.tag,
                               language=args.language, category=args.category)

    # 输出
    if args.stats:
        output = format_stats(filtered)
    elif args.format == 'markdown':
        output = generate_markdown(filtered)
    elif args.format == 'vscode':
        output = generate_vscode(filtered)
    elif args.format == 'json':
        output = json.dumps([s.to_dict() for s in filtered],
                            ensure_ascii=False, indent=2)
    elif args.search or args.tag or args.language or args.category:
        output = format_search_results(filtered, keyword=args.search)
    else:
        output = format_list(filtered)

    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output + "\n")
        print(f"\n已保存到：{args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
