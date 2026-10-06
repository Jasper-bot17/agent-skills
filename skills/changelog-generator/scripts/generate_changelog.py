#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
变更日志生成脚本

功能：
- 解析 Git 提交历史
- 按 Conventional Commits 规范分类（feat/fix/docs/style/refactor/perf/test/chore/build/ci/revert）
- 按版本标签或日期范围分组
- 生成 Keep a Changelog 格式的 Markdown 变更日志
- 提交统计（按类型、按作者）
- 未发布变更管理
- JSON 格式输出

用法：
  python3 generate_changelog.py --repo /path/to/repo
  python3 generate_changelog.py --repo /path/to/repo --unreleased
  python3 generate_changelog.py --repo /path/to/repo --from v1.0.0 --to v2.0.0
  python3 generate_changelog.py --repo /path/to/repo --since 2024-01-01 --until 2024-06-30
  python3 generate_changelog.py --repo /path/to/repo --version 1.2.0
  python3 generate_changelog.py --repo /path/to/repo --stats
  python3 generate_changelog.py --repo /path/to/repo --format json
  python3 generate_changelog.py --repo /path/to/repo --output CHANGELOG.md
  python3 generate_changelog.py --log-file sample-git-log.txt
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ============================================================
# Conventional Commits 类型定义
# ============================================================

COMMIT_TYPES = {
    "feat":     {"emoji": "✨", "label": "新增功能", "section": "✨ 新增功能"},
    "fix":      {"emoji": "🐛", "label": "问题修复", "section": "🐛 问题修复"},
    "docs":     {"emoji": "📝", "label": "文档更新", "section": "📝 文档更新"},
    "style":    {"emoji": "💄", "label": "样式调整", "section": "💄 样式调整"},
    "refactor": {"emoji": "♻️", "label": "代码重构", "section": "♻️ 代码重构"},
    "perf":     {"emoji": "⚡", "label": "性能提升", "section": "⚡ 性能提升"},
    "test":     {"emoji": "✅", "label": "测试更新", "section": "✅ 测试更新"},
    "build":    {"emoji": "📦", "label": "构建变更", "section": "📦 构建变更"},
    "ci":       {"emoji": "🔧", "label": "CI/CD", "section": "🔧 CI/CD"},
    "chore":    {"emoji": "🔨", "label": "杂项", "section": "🔨 杂项"},
    "revert":   {"emoji": "⏪️", "label": "回退", "section": "⏪️ 回退"},
    "other":    {"emoji": "📌", "label": "其他变更", "section": "📌 其他变更"},
}

# 变更日志中显示的类型顺序
DISPLAY_ORDER = ["feat", "fix", "perf", "refactor", "docs", "test",
                  "style", "build", "ci", "chore", "revert", "other"]


# ============================================================
# 提交数据结构
# ============================================================

class Commit:
    """Git 提交"""
    def __init__(self, hash_str: str, date: str, author: str, subject: str, body: str = ""):
        self.hash = hash_str
        self.date = date  # YYYY-MM-DD
        self.author = author
        self.subject = subject
        self.body = body
        self.type = "other"
        self.scope = ""
        self.description = subject
        self.breaking = False
        self._parse_conventional()

    def _parse_conventional(self):
        """解析 Conventional Commits 格式"""
        # 匹配 type(scope)!: subject 或 type!: subject 或 type: subject
        pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$'
        match = re.match(pattern, self.subject)
        if match:
            commit_type = match.group(1).lower()
            if commit_type in COMMIT_TYPES:
                self.type = commit_type
            else:
                self.type = "other"
            self.scope = match.group(2) or ""
            self.breaking = match.group(3) == "!"
            self.description = match.group(4).strip()
        else:
            self.type = "other"
            self.description = self.subject

        # 检查 body 中的 BREAKING CHANGE
        if "BREAKING CHANGE" in self.body or "BREAKING-CHANGE" in self.body:
            self.breaking = True

    def short_hash(self) -> str:
        return self.hash[:7]

    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "short_hash": self.short_hash(),
            "date": self.date,
            "author": self.author,
            "type": self.type,
            "scope": self.scope,
            "description": self.description,
            "subject": self.subject,
            "breaking": self.breaking,
        }


# ============================================================
# Git 操作
# ============================================================

def run_git(repo: str, args: List[str]) -> str:
    """运行 Git 命令"""
    cmd = ["git", "-C", repo] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=30)
        return result.stdout
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"Git 命令执行失败: {' '.join(cmd)}\n{e}", file=sys.stderr)
        return ""


def get_tags(repo: str) -> List[Tuple[str, str]]:
    """获取所有标签及对应日期，按日期排序（旧→新）"""
    output = run_git(repo, ["tag", "--sort=creatordate", "--format=%(creatordate:short)|%(refname:short)"])
    tags = []
    for line in output.strip().split("\n"):
        if "|" in line:
            date, name = line.split("|", 1)
            tags.append((name.strip(), date.strip()))
    return tags


def get_commits(repo: str, revision_range: str = "",
                 since: str = "", until: str = "",
                 no_merges: bool = False) -> List[Commit]:
    """获取提交列表"""
    args = ["log", "--pretty=format:%H|%ad|%ae|%s%n%b---END---",
            "--date=format:%Y-%m-%d"]

    if no_merges:
        args.append("--no-merges")

    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")

    if revision_range:
        args.append(revision_range)

    output = run_git(repo, args)
    commits = []

    # 解析输出
    blocks = output.split("---END---")
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")
        if not lines:
            continue

        # 第一行包含 hash|date|author|subject
        first_line = lines[0]
        parts = first_line.split("|", 3)
        if len(parts) < 4:
            continue

        hash_str, date, author, subject = parts[0], parts[1], parts[2], parts[3]
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        commit = Commit(hash_str, date, author, subject, body)
        commits.append(commit)

    return commits


def get_latest_tag(repo: str) -> Optional[str]:
    """获取最新标签"""
    tags = get_tags(repo)
    return tags[-1][0] if tags else None


# ============================================================
# 变更日志生成
# ============================================================

def group_commits_by_type(commits: List[Commit]) -> Dict[str, List[Commit]]:
    """按类型分组提交"""
    groups = defaultdict(list)
    for commit in commits:
        groups[commit.type].append(commit)
    return dict(groups)


def format_commit_line(commit: Commit, show_author: bool = True) -> str:
    """格式化单行提交信息"""
    scope_str = f"({commit.scope})" if commit.scope else ""
    breaking_str = " **[BREAKING]**" if commit.breaking else ""
    author_str = f" (@{commit.author.split('@')[0]})" if show_author else ""
    return f"- {commit.type}{scope_str}: {commit.description}{breaking_str}{author_str}"


def generate_version_section(version: str, date: str,
                             commits: List[Commit]) -> str:
    """生成单个版本的变更日志段落"""
    lines = []

    if version == "未发布":
        lines.append(f"## [未发布]")
    else:
        lines.append(f"## [{version}] - {date}")

    lines.append("")

    groups = group_commits_by_type(commits)

    # 按显示顺序输出
    has_content = False
    for commit_type in DISPLAY_ORDER:
        if commit_type not in groups:
            continue
        type_commits = groups[commit_type]
        if not type_commits:
            continue

        info = COMMIT_TYPES[commit_type]
        lines.append(f"### {info['section']}")
        lines.append("")
        for commit in type_commits:
            lines.append(format_commit_line(commit))
        lines.append("")
        has_content = True

    if not has_content:
        lines.append("_此版本无显著变更_")
        lines.append("")

    return "\n".join(lines)


def generate_changelog(repo: str, unreleased_only: bool = False,
                       from_tag: str = "", to_tag: str = "",
                       since: str = "", until: str = "",
                       version: str = "", show_stats: bool = False) -> str:
    """生成完整变更日志"""
    lines = []
    lines.append("# 更新日志")
    lines.append("")
    lines.append("所有显著变更都记录在此文件中。")
    lines.append("")
    lines.append("格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，")
    lines.append("本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。")
    lines.append("")

    all_commits = []

    # 模式 1：指定版本范围
    if from_tag or to_tag:
        revision = f"{from_tag}..{to_tag}" if from_tag and to_tag else (to_tag or from_tag)
        commits = get_commits(repo, revision_range=revision)
        version_name = version or to_tag or "指定范围"
        version_date = commits[0].date if commits else datetime.now().strftime("%Y-%m-%d")
        lines.append(generate_version_section(version_name, version_date, commits))
        all_commits = commits

    # 模式 2：只显示未发布
    elif unreleased_only:
        latest = get_latest_tag(repo)
        revision = f"{latest}..HEAD" if latest else "HEAD"
        commits = get_commits(repo, revision_range=revision)
        version_name = version or "未发布"
        lines.append(generate_version_section(version_name, "", commits))
        all_commits = commits

    # 模式 3：日期范围
    elif since or until:
        commits = get_commits(repo, since=since, until=until)
        version_name = version or f"{since or '开始'} ~ {until or '至今'}"
        version_date = until or datetime.now().strftime("%Y-%m-%d")
        lines.append(generate_version_section(version_name, version_date, commits))
        all_commits = commits

    # 模式 4：完整变更日志（按标签分组）
    else:
        tags = get_tags(repo)

        # 未发布部分
        latest_tag = tags[-1][0] if tags else None
        if latest_tag:
            unreleased = get_commits(repo, revision_range=f"{latest_tag}..HEAD")
        else:
            unreleased = get_commits(repo)

        if unreleased:
            lines.append(generate_version_section("未发布", "", unreleased))
            all_commits.extend(unreleased)

        # 按标签分组
        for i in range(len(tags) - 1, -1, -1):
            tag_name, tag_date = tags[i]
            if i > 0:
                prev_tag = tags[i - 1][0]
                revision = f"{prev_tag}..{tag_name}"
            else:
                revision = tag_name

            commits = get_commits(repo, revision_range=revision)
            if commits:
                lines.append(generate_version_section(tag_name, tag_date, commits))
                all_commits.extend(commits)

    # 统计信息
    if show_stats and all_commits:
        lines.append("---")
        lines.append("")
        lines.append(generate_stats(all_commits))

    return "\n".join(lines)


def generate_stats(commits: List[Commit]) -> str:
    """生成提交统计"""
    lines = []
    lines.append("📊 提交统计")
    lines.append("━" * 40)
    lines.append(f"总提交数：{len(commits)}")
    lines.append("")

    # 按类型统计
    type_counts = defaultdict(int)
    for commit in commits:
        type_counts[commit.type] += 1

    lines.append("按类型分布：")
    max_count = max(type_counts.values()) if type_counts else 1
    for commit_type in DISPLAY_ORDER:
        if commit_type not in type_counts:
            continue
        count = type_counts[commit_type]
        pct = count / len(commits) * 100
        bar_len = int(count / max_count * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        info = COMMIT_TYPES[commit_type]
        lines.append(f"  {info['emoji']} {commit_type:10s}: {count:4d}  {pct:5.1f}%  {bar}")

    # 按作者统计
    author_counts = defaultdict(int)
    for commit in commits:
        author_counts[commit.author] += 1

    lines.append("")
    lines.append("作者贡献：")
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (author, count) in enumerate(sorted_authors[:10], 1):
        pct = count / len(commits) * 100
        lines.append(f"  {i:2d}. {author:30s} {count:4d}  {pct:5.1f}%")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 从日志文件解析（用于测试/示例）
# ============================================================

def parse_log_file(filepath: str) -> List[Commit]:
    """从 git log 文本文件解析提交（格式：hash|date|author|subject）"""
    commits = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    commit = Commit(parts[0], parts[1], parts[2], parts[3])
                    commits.append(commit)
    except (OSError, IOError) as e:
        print(f"读取日志文件失败: {e}", file=sys.stderr)
    return commits


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="变更日志生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", "-r", default=".", help="Git 仓库路径（默认当前目录）")
    parser.add_argument("--unreleased", action="store_true", help="只显示未发布的变更")
    parser.add_argument("--from", dest="from_tag", default="", help="起始版本标签")
    parser.add_argument("--to", dest="to_tag", default="", help="结束版本标签")
    parser.add_argument("--since", default="", help="起始日期（YYYY-MM-DD）")
    parser.add_argument("--until", default="", help="结束日期（YYYY-MM-DD）")
    parser.add_argument("--version", "-v", default="", help="版本号（用于标题）")
    parser.add_argument("--stats", action="store_true", help="显示提交统计")
    parser.add_argument("--no-merges", action="store_true", help="排除合并提交")
    parser.add_argument("--format", "-f", choices=["markdown", "json"],
                        default="markdown", help="输出格式")
    parser.add_argument("--output", "-o", metavar="FILE", help="输出到文件")
    parser.add_argument("--log-file", default="", help="从日志文件读取（用于测试）")
    args = parser.parse_args()

    # 从日志文件读取（测试模式）
    if args.log_file:
        commits = parse_log_file(args.log_file)
        if args.format == "json":
            result = {
                "total": len(commits),
                "commits": [c.to_dict() for c in commits],
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(generate_version_section(args.version or "示例版本",
                                            commits[0].date if commits else "", commits))
            if args.stats:
                print("")
                print(generate_stats(commits))
        return

    # 检查是否为 Git 仓库
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"错误：{repo} 不是 Git 仓库（未找到 .git 目录）", file=sys.stderr)
        sys.exit(1)

    # JSON 格式
    if args.format == "json":
        if args.unreleased:
            latest = get_latest_tag(repo)
            revision = f"{latest}..HEAD" if latest else "HEAD"
            commits = get_commits(repo, revision_range=revision, no_merges=args.no_merges)
        elif args.from_tag or args.to_tag:
            revision = f"{args.from_tag}..{args.to_tag}" if args.from_tag and args.to_tag else (args.to_tag or args.from_tag)
            commits = get_commits(repo, revision_range=revision, no_merges=args.no_merges)
        elif args.since or args.until:
            commits = get_commits(repo, since=args.since, until=args.until, no_merges=args.no_merges)
        else:
            commits = get_commits(repo, no_merges=args.no_merges)

        result = {
            "total": len(commits),
            "commits": [c.to_dict() for c in commits],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Markdown 格式
    output = generate_changelog(
        repo,
        unreleased_only=args.unreleased,
        from_tag=args.from_tag,
        to_tag=args.to_tag,
        since=args.since,
        until=args.until,
        version=args.version,
        show_stats=args.stats,
    )

    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output + "\n")
        print(f"\n已保存到：{args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
