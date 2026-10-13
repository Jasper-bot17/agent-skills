#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
参考文献引用生成脚本

功能：
- 支持四种引用格式：GB/T 7714-2015、APA 7th、MLA 9th、Chicago
- 支持八种文献类型：期刊文章、书籍、网页、学位论文、会议论文、报纸文章、报告、专利
- 自动生成文中引用（in-text citation）和文后参考文献（reference list）
- 支持命令行单条生成和 JSON 批量生成
- 自动处理作者姓名格式、页码、卷期、DOI、URL 等字段

用法：
  python3 generate_citation.py --format gbt7714 --type journal \
    --authors "张三,李四" --title "论文标题" --journal "期刊名" \
    --year 2024 --volume 10 --issue 2 --pages "1-10"

  python3 generate_citation.py --format apa --batch references.json
  python3 generate_citation.py --list
"""

import argparse
import json
import sys
from datetime import datetime


# ============================================================
# 作者姓名处理
# ============================================================

def parse_authors(authors_str):
    """解析作者字符串，返回作者列表

    分隔规则：
    - 包含分号时，按分号分隔（每个作者内部可含逗号，如"Smith, John;Johnson, Alice"）
    - 不包含分号时：
      - 若包含", "（逗号+空格）且只有一个逗号，视为单作者"姓, 名"格式（如"Smith, John"）
      - 否则按逗号分隔（适用于中文作者，如"张三,李四"）
    """
    if not authors_str:
        return []
    if ";" in authors_str:
        authors = [a.strip() for a in authors_str.split(";") if a.strip()]
    elif ", " in authors_str and authors_str.count(",") == 1:
        # 单作者 "姓, 名" 格式（如 "Smith, John"）
        authors = [authors_str.strip()]
    else:
        authors = [a.strip() for a in authors_str.split(",") if a.strip()]
    return authors


def format_authors_gbt7714(authors):
    """GB/T 7714 作者格式：姓 名，多位用逗号，3位以上加'等'"""
    if not authors:
        return ""
    if len(authors) <= 3:
        return ", ".join(authors)
    else:
        return ", ".join(authors[:3]) + ", 等"


def format_authors_apa(authors):
    """APA 作者格式：姓, 名缩写. & 姓, 名缩写.（最多20位）"""
    if not authors:
        return ""
    formatted = []
    for author in authors[:20]:
        # 已经是 "姓, 名" 格式
        if "," in author:
            parts = author.split(",", 1)
            last = parts[0].strip()
            first = parts[1].strip()
            # 缩写名字
            initials = "".join([w[0].upper() + "." for w in first.split() if w])
            formatted.append(f"{last}, {initials}")
        else:
            # 中文作者或单名
            formatted.append(author)
    if len(authors) > 20:
        formatted.append("...")
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    else:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def format_authors_mla(authors):
    """MLA 作者格式：姓, 名. 第2位起 名 姓，多位加 et al."""
    if not authors:
        return ""
    if len(authors) == 1:
        author = authors[0]
        if "," in author:
            parts = author.split(",", 1)
            return f"{parts[0].strip()}, {parts[1].strip()}."
        return f"{author}."
    else:
        # 第一位：姓, 名
        first = authors[0]
        if "," in first:
            parts = first.split(",", 1)
            first_formatted = f"{parts[0].strip()}, {parts[1].strip()}"
        else:
            first_formatted = first
        # 其余：名 姓
        others = []
        for author in authors[1:]:
            if "," in author:
                parts = author.split(",", 1)
                others.append(f"{parts[1].strip()} {parts[0].strip()}")
            else:
                others.append(author)
        if len(authors) > 2:
            return f"{first_formatted}, et al."
        else:
            return f"{first_formatted}, and {others[0]}."


def format_authors_chicago(authors):
    """Chicago 作者格式：姓, 名. 第2位起 名 姓"""
    if not authors:
        return ""
    if len(authors) == 1:
        author = authors[0]
        if "," in author:
            parts = author.split(",", 1)
            return f"{parts[0].strip()}, {parts[1].strip()}."
        return f"{author}."
    else:
        first = authors[0]
        if "," in first:
            parts = first.split(",", 1)
            first_formatted = f"{parts[0].strip()}, {parts[1].strip()}"
        else:
            first_formatted = first
        others = []
        for author in authors[1:]:
            if "," in author:
                parts = author.split(",", 1)
                others.append(f"{parts[1].strip()} {parts[0].strip()}")
            else:
                others.append(author)
        return f"{first_formatted}, and {', '.join(others)}."


def get_first_author_surname(authors):
    """获取第一作者的姓（用于文中引用）"""
    if not authors:
        return ""
    first = authors[0]
    if "," in first:
        return first.split(",")[0].strip()
    # 中文作者全名作为姓
    return first


# ============================================================
# 日期格式化
# ============================================================

def format_date_apa(date_str):
    """APA 日期格式：Year, Month Day"""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        return f"{dt.year}, {months[dt.month-1]} {dt.day}"
    except ValueError:
        return date_str


def format_date_mla(date_str):
    """MLA 日期格式：Day Month Year"""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        months = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June",
                  "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
        return f"{dt.day} {months[dt.month-1]} {dt.year}"
    except ValueError:
        return date_str


def format_date_chicago(date_str):
    """Chicago 日期格式：Month Day, Year"""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        return f"{months[dt.month-1]} {dt.day}, {dt.year}"
    except ValueError:
        return date_str


# ============================================================
# 各格式各类型引用生成
# ============================================================

def generate_journal(fmt, data):
    """期刊文章引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    journal = data.get("journal", "")
    year = data.get("year", "")
    volume = data.get("volume", "")
    issue = data.get("issue", "")
    pages = data.get("pages", "")
    doi = data.get("doi", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        vol_issue = f"{volume}({issue})" if volume and issue else (volume if volume else "")
        result = f"{author_str}. {title}[J]. {journal}, {year}"
        if vol_issue:
            result += f", {vol_issue}"
        if pages:
            result += f": {pages}"
        result += "."
        return result

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        result = f"{author_str} ({year}). {title}. {journal}"
        if volume:
            result += f", {volume}"
            if issue:
                result += f"({issue})"
        if pages:
            result += f", {pages.replace('-', '–')}"
        result += "."
        if doi:
            result += f" https://doi.org/{doi}"
        return result

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        result = f'{author_str} "{title}." {journal}'
        if volume:
            result += f", vol. {volume}"
        if issue:
            result += f", no. {issue}"
        if year:
            result += f", {year}"
        if pages:
            result += f", pp. {pages}"
        result += "."
        return result

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        result = f'{author_str} "{title}." {journal} {volume}'
        if issue:
            result += f", no. {issue}"
        result += f" ({year})"
        if pages:
            result += f": {pages}"
        result += "."
        return result


def generate_book(fmt, data):
    """书籍引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    publisher = data.get("publisher", "")
    year = data.get("year", "")
    edition = data.get("edition", "")
    city = data.get("city", "")
    pages = data.get("pages", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        result = f"{author_str}. {title}[M]"
        if edition:
            result += f". {edition}"
        result += f". {city}: {publisher}, {year}"
        if pages:
            result += f": {pages}"
        result += "."
        return result

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        result = f"{author_str} ({year}). {title}"
        if edition:
            result += f" ({edition} ed.)"
        result += f". {publisher}."
        return result

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        result = f"{author_str} {title}."
        if edition:
            result += f" {edition} ed.,"
        result += f" {publisher}, {year}."
        return result

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        result = f"{author_str} {title}."
        if edition:
            result += f" {edition} ed."
        result += f" {city}: {publisher}, {year}."
        return result


def generate_webpage(fmt, data):
    """网页引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    url = data.get("url", "")
    publish_date = data.get("publish_date", data.get("publish-date", ""))
    access_date = data.get("access_date", data.get("access-date", ""))
    site = data.get("site", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        result = f"{author_str}. {title}[EB/OL]"
        if publish_date:
            result += f". ({publish_date})"
        if access_date:
            result += f"[{access_date}]"
        result += f". {url}."
        return result

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        result = f"{author_str} ({format_date_apa(publish_date)}). {title}"
        if site:
            result += f". {site}"
        result += f". {url}"
        return result

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        result = f'{author_str} "{title}." {site}, {format_date_mla(publish_date)}, {url}.'
        if access_date:
            result = result.rstrip(".") + f" Accessed {format_date_mla(access_date)}."
        return result

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        result = f'{author_str} "{title}." {site}. {format_date_chicago(publish_date)}. {url}.'
        if access_date:
            result = result.rstrip(".") + f" (accessed {format_date_chicago(access_date)})."
        return result


def generate_thesis(fmt, data):
    """学位论文引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    degree = data.get("degree", "")
    institution = data.get("institution", "")
    year = data.get("year", "")
    city = data.get("city", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        return f"{author_str}. {title}[D]. {city}: {institution}, {year}."

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        degree_type = "Doctoral dissertation" if "博" in str(degree) else "Master's thesis"
        return f"{author_str} ({year}). {title} [{degree_type}, {institution}]. {institution}."

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        return f"{author_str} {title}. {degree} thesis, {institution}, {year}."

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        return f"{author_str} \"{title}.\" {degree} thesis, {institution}, {year}."


def generate_conference(fmt, data):
    """会议论文引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    conference = data.get("conference", "")
    location = data.get("location", "")
    year = data.get("year", "")
    pages = data.get("pages", "")
    publisher = data.get("publisher", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        result = f"{author_str}. {title}[C]//{conference}. {location}, {year}"
        if publisher:
            result += f". {publisher}"
        if pages:
            result += f": {pages}"
        result += "."
        return result

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        result = f"{author_str} ({year}). {title}. In {conference} (pp. {pages}). {publisher}."
        return result

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        result = f'{author_str} "{title}." {conference}, {location}, {year}, pp. {pages}.'
        return result

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        result = f'{author_str} "{title}." Paper presented at {conference}, {location}, {year}.'
        return result


def generate_newspaper(fmt, data):
    """报纸文章引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    newspaper = data.get("newspaper", "")
    date = data.get("date", "")
    edition = data.get("edition", "")
    pages = data.get("pages", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        result = f"{author_str}. {title}[N]. {newspaper}, {date}"
        if edition:
            result += f"({edition})"
        if pages:
            result += f": {pages}"
        result += "."
        return result

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        result = f"{author_str} ({format_date_apa(date)}). {title}. {newspaper}"
        if pages:
            result += f", pp. {pages}"
        result += "."
        return result

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        result = f'{author_str} "{title}." {newspaper}, {format_date_mla(date)}, pp. {pages}.'
        return result

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        result = f'{author_str} "{title}." {newspaper}, {format_date_chicago(date)}, sec. {edition}, {pages}.'
        return result


def generate_report(fmt, data):
    """报告引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    report_no = data.get("report_no", data.get("report-no", ""))
    institution = data.get("institution", "")
    year = data.get("year", "")
    city = data.get("city", "")
    url = data.get("url", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        result = f"{author_str}. {title}[R]"
        if report_no:
            result += f". {report_no}"
        result += f". {city}: {institution}, {year}."
        return result

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        result = f"{author_str} ({year}). {title} (Report No. {report_no}). {institution}."
        if url:
            result += f" {url}"
        return result

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        result = f"{author_str} {title}. No. {report_no}, {institution}, {year}."
        return result

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        result = f"{author_str} {title}. No. {report_no}. {city}: {institution}, {year}."
        return result


def generate_patent(fmt, data):
    """专利引用"""
    authors = parse_authors(data.get("authors", ""))
    title = data.get("title", "")
    country = data.get("country", "")
    patent_no = data.get("patent_no", data.get("patent-no", ""))
    date = data.get("date", "")

    if fmt == "gbt7714":
        author_str = format_authors_gbt7714(authors)
        return f"{author_str}. {title}[P]. {country}: {patent_no}, {date}."

    elif fmt == "apa":
        author_str = format_authors_apa(authors)
        return f"{author_str} ({format_date_apa(date)}). {title} (Patent No. {patent_no}). {country} Patent Office."

    elif fmt == "mla":
        author_str = format_authors_mla(authors)
        return f'{author_str} "{title}." {country} Patent {patent_no}, {format_date_mla(date)}.'

    elif fmt == "chicago":
        author_str = format_authors_chicago(authors)
        return f'{author_str} "{title}." {country} Patent No. {patent_no}, {format_date_chicago(date)}.'


# ============================================================
# 文中引用生成
# ============================================================

def generate_in_text(fmt, data):
    """生成文中引用"""
    authors = parse_authors(data.get("authors", ""))
    year = data.get("year", "")
    pages = data.get("pages", "")
    surname = get_first_author_surname(authors)

    if not authors:
        return "(无作者)"

    if fmt == "gbt7714":
        # GB/T 7714 顺序编码制，文中引用为 [序号]
        return "[序号]"

    elif fmt == "apa":
        if len(authors) == 1:
            return f"({surname}, {year})"
        elif len(authors) == 2:
            surname2 = get_first_author_surname([authors[1]])
            return f"({surname} & {surname2}, {year})"
        else:
            return f"({surname} et al., {year})"

    elif fmt == "mla":
        if len(authors) == 1:
            if pages:
                return f"({surname} {pages})"
            return f"({surname})"
        else:
            if pages:
                return f"({surname} et al. {pages})"
            return f"({surname} et al.)"

    elif fmt == "chicago":
        if len(authors) == 1:
            return f"({surname}, {year})"
        elif len(authors) == 2:
            surname2 = get_first_author_surname([authors[1]])
            return f"({surname} and {surname2}, {year})"
        else:
            return f"({surname} et al., {year})"


# ============================================================
# 类型分发
# ============================================================

GENERATORS = {
    "journal": generate_journal,
    "book": generate_book,
    "webpage": generate_webpage,
    "thesis": generate_thesis,
    "conference": generate_conference,
    "newspaper": generate_newspaper,
    "report": generate_report,
    "patent": generate_patent,
}

TYPE_LABELS = {
    "journal": "期刊文章",
    "book": "书籍",
    "webpage": "网页",
    "thesis": "学位论文",
    "conference": "会议论文",
    "newspaper": "报纸文章",
    "report": "报告",
    "patent": "专利",
}

FORMAT_LABELS = {
    "gbt7714": "GB/T 7714-2015",
    "apa": "APA 7th",
    "mla": "MLA 9th",
    "chicago": "Chicago",
}


def generate_citation(fmt, ctype, data):
    """生成单条引用"""
    if ctype not in GENERATORS:
        raise ValueError(f"不支持的文献类型: {ctype}，支持: {', '.join(GENERATORS.keys())}")
    return GENERATORS[ctype](fmt, data)


# ============================================================
# 输出函数
# ============================================================

def print_single(fmt, ctype, data, in_text=False):
    """输出单条引用"""
    print("📚 参考文献引用生成")
    print("=" * 70)
    print(f"  引用格式: {FORMAT_LABELS.get(fmt, fmt)}")
    print(f"  文献类型: {TYPE_LABELS.get(ctype, ctype)}")
    print("-" * 70)

    try:
        citation = generate_citation(fmt, ctype, data)
        print(f"  文后参考文献:")
        print(f"  {citation}")
    except Exception as e:
        print(f"  ❌ 生成失败: {e}", file=sys.stderr)

    if in_text:
        print()
        print(f"  文中引用:")
        print(f"  {generate_in_text(fmt, data)}")

    print("=" * 70)


def print_batch(fmt, references):
    """批量输出引用"""
    print(f"📚 批量参考文献引用生成（{FORMAT_LABELS.get(fmt, fmt)}）")
    print("=" * 70)
    print(f"  共 {len(references)} 条文献")
    print("-" * 70)

    for i, ref in enumerate(references, 1):
        ctype = ref.get("type", "journal")
        try:
            citation = generate_citation(fmt, ctype, ref)
            if fmt == "gbt7714":
                print(f"  [{i}] {citation}")
            else:
                print(f"  {i}. {citation}")
        except Exception as e:
            print(f"  [{i}] ❌ 生成失败 ({TYPE_LABELS.get(ctype, ctype)}): {e}")

    print("=" * 70)


def print_list():
    """列出支持的格式和类型"""
    print("📋 支持的引用格式")
    print("=" * 50)
    for fmt, label in FORMAT_LABELS.items():
        print(f"  {fmt:<12} {label}")
    print()
    print("📋 支持的文献类型")
    print("=" * 50)
    for ctype, label in TYPE_LABELS.items():
        print(f"  {ctype:<12} {label}")
    print("=" * 50)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="参考文献引用生成器（GB/T 7714 / APA / MLA / Chicago）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --format gbt7714 --type journal --authors "张三,李四" \\
    --title "论文标题" --journal "期刊名" --year 2024 --volume 10 --issue 2 --pages "1-10"
  %(prog)s --format apa --batch references.json
  %(prog)s --list
        """,
    )

    # 基本参数
    parser.add_argument("--format", "-f", choices=["gbt7714", "apa", "mla", "chicago"],
                        help="引用格式")
    parser.add_argument("--type", "-t", choices=list(GENERATORS.keys()),
                        help="文献类型")
    parser.add_argument("--batch", "-b", help="批量生成（JSON 文件路径）")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出支持的格式和类型")
    parser.add_argument("--in-text", action="store_true",
                        help="同时生成文中引用")

    # 文献字段
    parser.add_argument("--authors", "-a", help="作者（逗号分隔，英文用'姓, 名'格式）")
    parser.add_argument("--title", help="题名")
    parser.add_argument("--journal", help="刊名（期刊文章）")
    parser.add_argument("--publisher", help="出版者（书籍）")
    parser.add_argument("--url", help="URL（网页）")
    parser.add_argument("--publish-date", help="发布日期（网页，YYYY-MM-DD）")
    parser.add_argument("--access-date", help="引用日期（网页，YYYY-MM-DD）")
    parser.add_argument("--site", help="网站名称（网页）")
    parser.add_argument("--degree", help="学位类型（学位论文）")
    parser.add_argument("--institution", help="学校/机构（学位论文/报告）")
    parser.add_argument("--conference", help="会议名称（会议论文）")
    parser.add_argument("--location", help="会议地点（会议论文）")
    parser.add_argument("--newspaper", help="报纸名（报纸文章）")
    parser.add_argument("--date", help="日期（报纸/专利，YYYY-MM-DD）")
    parser.add_argument("--edition", help="版次（书籍/报纸）")
    parser.add_argument("--report-no", help="报告编号（报告）")
    parser.add_argument("--country", help="专利国别（专利）")
    parser.add_argument("--patent-no", help="专利号（专利）")
    parser.add_argument("--year", "-y", help="年份")
    parser.add_argument("--volume", "-v", help="卷号")
    parser.add_argument("--issue", "-i", help="期号")
    parser.add_argument("--pages", "-p", help="页码")
    parser.add_argument("--city", help="出版地")
    parser.add_argument("--doi", help="DOI")

    args = parser.parse_args()

    # 列出支持的格式和类型
    if args.list:
        print_list()
        return

    # 必须指定格式
    if not args.format:
        parser.print_help()
        print("\n错误：请使用 --format 指定引用格式，或使用 --list 查看支持的格式",
              file=sys.stderr)
        sys.exit(1)

    fmt = args.format

    # 批量模式
    if args.batch:
        try:
            with open(args.batch, "r", encoding="utf-8") as f:
                references = json.load(f)
        except FileNotFoundError:
            print(f"错误：文件不存在: {args.batch}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"错误：JSON 解析失败: {e}", file=sys.stderr)
            sys.exit(1)

        if not isinstance(references, list):
            print("错误：JSON 文件必须是数组", file=sys.stderr)
            sys.exit(1)

        print()
        print_batch(fmt, references)
        return

    # 单条模式：必须指定类型
    if not args.type:
        parser.print_help()
        print("\n错误：请使用 --type 指定文献类型，或使用 --list 查看支持的类型",
              file=sys.stderr)
        sys.exit(1)

    # 构建文献数据
    data = {
        "authors": args.authors or "",
        "title": args.title or "",
        "journal": args.journal or "",
        "publisher": args.publisher or "",
        "url": args.url or "",
        "publish_date": args.publish_date or "",
        "access_date": args.access_date or "",
        "site": args.site or "",
        "degree": args.degree or "",
        "institution": args.institution or "",
        "conference": args.conference or "",
        "location": args.location or "",
        "newspaper": args.newspaper or "",
        "date": args.date or "",
        "edition": args.edition or "",
        "report_no": args.report_no or "",
        "country": args.country or "",
        "patent_no": args.patent_no or "",
        "year": args.year or "",
        "volume": args.volume or "",
        "issue": args.issue or "",
        "pages": args.pages or "",
        "city": args.city or "",
        "doi": args.doi or "",
    }

    print()
    print_single(fmt, args.type, data, args.in_text)


if __name__ == "__main__":
    main()
