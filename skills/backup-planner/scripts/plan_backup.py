#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
备份计划脚本

功能：
- 扫描目录，统计文件数量、总大小、类型分布
- 识别大文件和大目录
- 生成完整/增量备份方案
- 估算备份时间和压缩后大小
- 生成 tar/rsync 备份脚本
- 自动建议排除规则

用法：
  python3 plan_backup.py --dir /path/to/data
  python3 plan_backup.py --dir /path/to/data --top 20
  python3 plan_backup.py --dir /path/to/data --incremental 7
  python3 plan_backup.py --dir /path/to/data --script tar --output backup.sh
  python3 plan_backup.py --dir /path/to/data --script rsync --remote user@server:/backup/
  python3 plan_backup.py --dir /path/to/data --exclude "*.log,node_modules"
  python3 plan_backup.py --dir /path/to/data --speed 100
  python3 plan_backup.py --dir /path/to/data --format json
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


# ============================================================
# 文件类型分类
# ============================================================

FILE_CATEGORIES = {
    "文档": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt",
             ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".epub"],
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
             ".tiff", ".raw", ".ico", ".heic", ".psd", ".ai"],
    "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
             ".m4v", ".mpg", ".mpeg", ".3gp"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
             ".ape", ".opus"],
    "代码": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp",
             ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".sh", ".bash",
             ".html", ".css", ".scss", ".less", ".vue", ".jsx", ".tsx",
             ".sql", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
             ".cfg", ".conf", ".makefile", ".dockerfile"],
    "压缩包": [".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
               ".tgz", ".tbz2", ".zst"],
    "安装包": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".apk",
               ".ipa", ".appimage"],
    "字体": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "数据库": [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"],
    "其他": [],
}

# 默认排除目录
DEFAULT_EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".idea", ".vscode", ".vs", "vendor", "bower_components",
    ".next", ".nuxt", "dist", "build", "out", ".cache",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "target", ".gradle", ".maven", "Cargo",
}

# 默认排除文件模式
DEFAULT_EXCLUDE_FILES = [
    "*.log", "*.tmp", "*.temp", "*.swp", "*.swo", "*~",
    ".DS_Store", "Thumbs.db", "desktop.ini",
    "*.pyc", "*.pyo", "*.class",
    "*.bak", "*.old", "*.orig",
]

# 各类型压缩率估算（0-1，1表示完全压缩）
COMPRESSION_RATIOS = {
    "文档": 0.7,
    "图片": 0.05,
    "视频": 0.0,
    "音频": 0.1,
    "代码": 0.6,
    "压缩包": 0.0,
    "安装包": 0.0,
    "字体": 0.3,
    "数据库": 0.5,
    "其他": 0.3,
}


# ============================================================
# 工具函数
# ============================================================

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes < 1024 * 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 1:
        return "不到 1 秒"
    elif seconds < 60:
        return f"{seconds:.0f} 秒"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} 分钟"
    else:
        return f"{seconds / 3600:.1f} 小时"


def get_category(ext: str) -> str:
    """获取文件类型分类"""
    ext = ext.lower()
    for category, exts in FILE_CATEGORIES.items():
        if ext in exts:
            return category
    return "其他"


def should_exclude(name: str, exclude_patterns: List[str]) -> bool:
    """判断是否应排除"""
    import fnmatch
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


# ============================================================
# 目录扫描
# ============================================================

class ScanResult:
    """扫描结果"""
    def __init__(self):
        self.total_files = 0
        self.total_dirs = 0
        self.total_size = 0
        self.category_stats = defaultdict(lambda: {"count": 0, "size": 0})
        self.large_files = []  # (path, size)
        self.large_dirs = defaultdict(int)  # dir_path -> size
        self.skipped = 0
        self.scan_time = 0.0
        self.modified_recently = 0  # 最近 N 天修改的文件数
        self.modified_recently_size = 0


def scan_directory(dir_path: str, exclude_dirs: set,
                   exclude_files: List[str],
                   incremental_days: int = 0,
                   top_n: int = 10) -> ScanResult:
    """扫描目录"""
    result = ScanResult()
    start_time = time.time()

    cutoff_time = None
    if incremental_days > 0:
        cutoff_time = (datetime.now() - timedelta(days=incremental_days)).timestamp()

    abs_dir = os.path.abspath(dir_path)

    for root, dirs, files in os.walk(abs_dir, followlinks=False):
        # 过滤排除目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        result.total_dirs += len(dirs)

        for fname in files:
            if should_exclude(fname, exclude_files):
                result.skipped += 1
                continue

            fpath = os.path.join(root, fname)
            try:
                stat = os.lstat(fpath)
                if os.path.islink(fpath):
                    result.skipped += 1
                    continue

                size = stat.st_size
                result.total_files += 1
                result.total_size += size

                # 分类统计
                ext = os.path.splitext(fname)[1]
                cat = get_category(ext)
                result.category_stats[cat]["count"] += 1
                result.category_stats[cat]["size"] += size

                # 大文件
                result.large_files.append((fpath, size))

                # 大目录（直接父目录）
                parent = os.path.dirname(fpath)
                result.large_dirs[parent] += size

                # 增量备份过滤
                if cutoff_time and stat.st_mtime >= cutoff_time:
                    result.modified_recently += 1
                    result.modified_recently_size += size

            except (OSError, PermissionError):
                result.skipped += 1
                continue

    # 排序大文件
    result.large_files.sort(key=lambda x: x[1], reverse=True)
    result.large_files = result.large_files[:top_n]

    # 排序大目录
    result.large_dirs = sorted(result.large_dirs.items(),
                                key=lambda x: x[1], reverse=True)[:top_n]

    result.scan_time = time.time() - start_time
    return result


# ============================================================
# 备份方案生成
# ============================================================

def estimate_compressed_size(result: ScanResult) -> int:
    """估算压缩后大小"""
    compressed = 0
    for cat, stats in result.category_stats.items():
        ratio = COMPRESSION_RATIOS.get(cat, 0.3)
        compressed += int(stats["size"] * (1 - ratio))
    return compressed


def estimate_backup_time(total_size: int, speed_mbps: float,
                          compressed: bool = False) -> float:
    """估算备份时间（秒）"""
    if speed_mbps <= 0:
        speed_mbps = 100
    size_mb = total_size / (1024 * 1024)
    time_sec = size_mb / speed_mbps
    if compressed:
        time_sec *= 1.5  # 压缩需要额外时间
    return time_sec


# ============================================================
# 备份脚本生成
# ============================================================

def generate_tar_script(source: str, exclude_dirs: set,
                        exclude_files: List[str],
                        incremental_days: int = 0) -> str:
    """生成 tar 备份脚本"""
    abs_source = os.path.abspath(source)
    source_dir = os.path.dirname(abs_source)
    source_name = os.path.basename(abs_source)

    lines = [
        "#!/bin/bash",
        "# 自动生成的 tar 备份脚本",
        f"# 源目录：{abs_source}",
        f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f'SOURCE="{abs_source}"',
        'DEST="${DEST:-/backup}"',
        'TIMESTAMP=$(date +%Y%m%d_%H%M%S)',
        'BACKUP_NAME="backup_${TIMESTAMP}.tar.gz"',
        "",
        'echo "开始备份：${SOURCE}"',
        'echo "目标文件：${DEST}/${BACKUP_NAME}"',
        "",
        "tar -czf \"${DEST}/${BACKUP_NAME}\" \\",
    ]

    # 排除规则
    for d in sorted(exclude_dirs):
        lines.append(f'  --exclude="{d}" \\')
    for f in exclude_files:
        if not f.startswith("."):
            lines.append(f'  --exclude="{f}" \\')

    # 增量备份
    if incremental_days > 0:
        lines.append(f'  --newer-mtime="-{incremental_days} days" \\')

    lines.extend([
        f'  -C "{source_dir}" \\',
        f'  "{source_name}"',
        "",
        "if [ $? -eq 0 ]; then",
        '  echo "✅ 备份完成：${BACKUP_NAME}"',
        '  echo "文件大小：$(du -h "${DEST}/${BACKUP_NAME}" | cut -f1)"',
        "else",
        '  echo "❌ 备份失败"',
        "  exit 1",
        "fi",
    ])

    return "\n".join(lines)


def generate_rsync_script(source: str, exclude_dirs: set,
                          exclude_files: List[str],
                          remote: str = "",
                          incremental: bool = True) -> str:
    """生成 rsync 备份脚本"""
    abs_source = os.path.abspath(source)
    if not abs_source.endswith("/"):
        abs_source += "/"

    lines = [
        "#!/bin/bash",
        "# 自动生成的 rsync 备份脚本",
        f"# 源目录：{abs_source}",
        f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f'SOURCE="{abs_source}"',
    ]

    if remote:
        lines.append(f'DEST="{remote}"')
    else:
        lines.append('DEST="${DEST:-/backup/}"')

    lines.extend([
        "",
        'echo "开始同步：${SOURCE} -> ${DEST}"',
        "",
        "rsync -avz --progress \\",
        "  --delete \\",
    ])

    for d in sorted(exclude_dirs):
        lines.append(f'  --exclude="{d}/" \\')
    for f in exclude_files:
        lines.append(f'  --exclude="{f}" \\')

    lines.extend([
        '  "${SOURCE}" "${DEST}"',
        "",
        "if [ $? -eq 0 ]; then",
        '  echo "✅ 同步完成"',
        "else",
        '  echo "❌ 同步失败"',
        "  exit 1",
        "fi",
    ])

    return "\n".join(lines)


# ============================================================
# 输出格式化
# ============================================================

def format_scan_report(result: ScanResult, dir_path: str,
                       incremental_days: int = 0) -> str:
    """格式化扫描报告"""
    lines = []
    lines.append("📊 目录扫描报告")
    lines.append("━" * 40)
    lines.append(f"目录：{os.path.abspath(dir_path)}")
    lines.append(f"总大小：{format_size(result.total_size)}")
    lines.append(f"文件数：{result.total_files:,}")
    lines.append(f"目录数：{result.total_dirs:,}")
    if result.skipped > 0:
        lines.append(f"跳过：{result.skipped} 个（排除/无权限/符号链接）")
    lines.append(f"扫描用时：{result.scan_time:.2f} 秒")

    if incremental_days > 0:
        lines.append("")
        lines.append(f"📅 最近 {incremental_days} 天修改：")
        lines.append(f"  文件数：{result.modified_recently:,}")
        lines.append(f"  大小：{format_size(result.modified_recently_size)}")

    # 类型分布
    lines.append("")
    lines.append("📁 类型分布：")
    sorted_cats = sorted(result.category_stats.items(),
                         key=lambda x: x[1]["size"], reverse=True)
    for cat, stats in sorted_cats:
        if stats["count"] > 0:
            pct = stats["size"] / result.total_size * 100 if result.total_size > 0 else 0
            lines.append(f"  {cat}：{stats['count']:,} 个，{format_size(stats['size'])} ({pct:.1f}%)")

    # 大文件
    if result.large_files:
        lines.append("")
        lines.append(f"📈 大文件 Top {len(result.large_files)}：")
        for i, (fpath, size) in enumerate(result.large_files, 1):
            display = fpath
            if len(display) > 60:
                display = "..." + display[-57:]
            lines.append(f"  {i}. {display} — {format_size(size)}")

    # 大目录
    if result.large_dirs:
        lines.append("")
        lines.append(f"📂 大目录 Top {min(5, len(result.large_dirs))}：")
        for i, (dpath, size) in enumerate(result.large_dirs[:5], 1):
            display = dpath
            if len(display) > 60:
                display = "..." + display[-57:]
            lines.append(f"  {i}. {display} — {format_size(size)}")

    # 建议
    lines.append("")
    lines.append("💡 建议：")
    # 找出占比最大的类型
    if sorted_cats:
        top_cat = sorted_cats[0]
        lines.append(f"  - {top_cat[0]}文件占比最大（{top_cat[1]['size']/result.total_size*100:.0f}%），可考虑单独备份")
    lines.append("  - 建议排除 node_modules、.git 等依赖目录")
    compressed = estimate_compressed_size(result)
    lines.append(f"  - 压缩后预估大小：约 {format_size(compressed)}")
    lines.append("━" * 40)
    return "\n".join(lines)


def format_backup_plan(result: ScanResult, dir_path: str,
                       incremental_days: int = 0,
                       speed_mbps: float = 100) -> str:
    """格式化备份方案"""
    lines = []
    lines.append("💾 备份方案")
    lines.append("━" * 40)

    if incremental_days > 0:
        lines.append(f"备份类型：增量备份（最近 {incremental_days} 天）")
        backup_size = result.modified_recently_size
        backup_count = result.modified_recently
    else:
        lines.append("备份类型：完整备份")
        backup_size = result.total_size
        backup_count = result.total_files

    lines.append(f"源目录：{os.path.abspath(dir_path)}")
    lines.append("")
    lines.append("📦 备份范围：")
    lines.append(f"  文件数：{backup_count:,}")
    lines.append(f"  总大小：{format_size(backup_size)}")

    compressed = estimate_compressed_size(result)
    if incremental_days > 0:
        compressed = int(compressed * result.modified_recently_size / result.total_size) if result.total_size > 0 else 0
    lines.append(f"  压缩后预估：约 {format_size(compressed)}")

    lines.append("")
    lines.append("🚫 排除规则：")
    for d in sorted(DEFAULT_EXCLUDE_DIRS):
        lines.append(f"  - {d}/")
    for f in DEFAULT_EXCLUDE_FILES[:5]:
        lines.append(f"  - {f}")
    if len(DEFAULT_EXCLUDE_FILES) > 5:
        lines.append(f"  - ... 等 {len(DEFAULT_EXCLUDE_FILES)} 种文件模式")

    lines.append("")
    lines.append("⏱️  时间估算：")
    raw_time = estimate_backup_time(backup_size, speed_mbps, compressed=False)
    comp_time = estimate_backup_time(compressed, speed_mbps, compressed=True)
    lines.append(f"  未压缩：约 {format_duration(raw_time)}（按 {speed_mbps} MB/s）")
    lines.append(f"  压缩后：约 {format_duration(comp_time)}（含压缩时间）")

    lines.append("")
    lines.append("📋 建议：")
    if backup_size > 10 * 1024 * 1024 * 1024:  # > 10GB
        lines.append("  - 数据量较大，建议使用增量备份")
        lines.append("  - 备份频率：每周完整 + 每日增量")
    elif backup_size > 1 * 1024 * 1024 * 1024:  # > 1GB
        lines.append("  - 备份频率：每周一次完整备份")
    else:
        lines.append("  - 备份频率：每日一次完整备份")
    lines.append("  - 保留份数：至少 3 份（遵循 3-2-1 原则）")
    lines.append("  - 存储介质：外接硬盘 + 云存储")
    lines.append("  - 验证恢复：每月验证一次备份可恢复性")
    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="备份计划工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dir", "-d", required=True, help="要扫描的目录路径")
    parser.add_argument("--top", "-n", type=int, default=10, help="显示前 N 个大文件（默认 10）")
    parser.add_argument("--incremental", "-i", type=int, default=0, metavar="DAYS",
                        help="增量备份：仅包含最近 N 天修改的文件")
    parser.add_argument("--script", "-s", choices=["tar", "rsync"],
                        help="生成备份脚本类型")
    parser.add_argument("--remote", "-r", default="",
                        help="rsync 远程目标（如 user@server:/backup/）")
    parser.add_argument("--exclude", "-e", default="",
                        help="额外排除规则，逗号分隔（如 *.log,node_modules）")
    parser.add_argument("--speed", type=float, default=100,
                        help="假设传输速度 MB/s（默认 100）")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                        help="输出格式")
    parser.add_argument("--output", "-o", metavar="FILE", help="输出到文件")
    args = parser.parse_args()

    # 检查目录
    if not os.path.isdir(args.dir):
        print(f"错误：目录不存在：{args.dir}", file=sys.stderr)
        sys.exit(1)

    # 解析排除规则
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    exclude_files = list(DEFAULT_EXCLUDE_FILES)
    if args.exclude:
        for item in args.exclude.split(","):
            item = item.strip()
            if item:
                if "." in item or "*" in item:
                    exclude_files.append(item)
                else:
                    exclude_dirs.add(item)

    # 扫描
    print(f"正在扫描：{args.dir} ...", file=sys.stderr)
    result = scan_directory(args.dir, exclude_dirs, exclude_files,
                            incremental_days=args.incremental,
                            top_n=args.top)

    # 输出
    output = ""

    if args.script:
        if args.script == "tar":
            output = generate_tar_script(args.dir, exclude_dirs, exclude_files,
                                          incremental_days=args.incremental)
        else:
            output = generate_rsync_script(args.dir, exclude_dirs, exclude_files,
                                            remote=args.remote,
                                            incremental=(args.incremental > 0))
    elif args.format == "json":
        data = {
            "directory": os.path.abspath(args.dir),
            "total_files": result.total_files,
            "total_dirs": result.total_dirs,
            "total_size": result.total_size,
            "total_size_human": format_size(result.total_size),
            "skipped": result.skipped,
            "scan_time": round(result.scan_time, 2),
            "categories": {k: dict(v) for k, v in result.category_stats.items()},
            "large_files": [{"path": p, "size": s, "size_human": format_size(s)}
                            for p, s in result.large_files],
            "compressed_estimate": estimate_compressed_size(result),
            "incremental_days": args.incremental,
            "modified_recently": result.modified_recently,
            "modified_recently_size": result.modified_recently_size,
        }
        output = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        output = format_scan_report(result, args.dir, args.incremental)
        output += "\n\n"
        output += format_backup_plan(result, args.dir, args.incremental, args.speed)

    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output + "\n")
        print(f"\n已保存到：{args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
