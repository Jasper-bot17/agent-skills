#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理助手 - 目录扫描、分类统计与文件整理脚本

支持三种模式：
  analyze  - 仅扫描分析，输出统计报告
  dry-run  - 预览整理方案，不实际移动文件
  execute  - 实际执行文件整理

支持两种策略：
  type - 按文件类型分类（文档/图片/视频/...）
  date - 按修改日期归档（YYYY-MM/）

用法：
  python3 organize_files.py --dir ~/Downloads --mode analyze
  python3 organize_files.py --dir ~/Downloads --mode dry-run --strategy type
  python3 organize_files.py --dir ~/Downloads --mode execute --strategy type
  python3 organize_files.py --dir ~/Photos --mode dry-run --strategy date
  python3 organize_files.py --dir ~/Downloads --mode analyze --large-threshold 100
  python3 organize_files.py --dir ~/Downloads --mode analyze --detect-duplicates
"""

import argparse
import hashlib
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================
# 文件分类定义
# ============================================================

FILE_CATEGORIES = {
    "文档": {
        "extensions": {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf",
                       ".txt", ".md", ".rtf", ".odt", ".ods", ".odp", ".csv", ".tsv",
                       ".wps", ".et", ".dps", ".pages", ".numbers", ".key"},
        "color": "\033[34m",
    },
    "图片": {
        "extensions": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
                       ".ico", ".tiff", ".tif", ".psd", ".ai", ".raw", ".heic",
                       ".heif", ".indd", ".eps", ".cr2", ".nef", ".arw", ".dng"},
        "color": "\033[35m",
    },
    "视频": {
        "extensions": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
                       ".m4v", ".mpg", ".mpeg", ".3gp", ".m2ts", ".ts", ".vob",
                       ".ogv", ".rm", ".rmvb", ".asf", ".f4v"},
        "color": "\033[31m",
    },
    "音频": {
        "extensions": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
                       ".ape", ".opus", ".mid", ".midi", ".aiff", ".alac", ".dsf"},
        "color": "\033[33m",
    },
    "压缩包": {
        "extensions": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
                       ".tgz", ".tbz2", ".iso", ".dmg", ".img", ".cab", ".lz",
                       ".zst", ".arj", ".lha"},
        "color": "\033[36m",
    },
    "代码": {
        "extensions": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp",
                       ".h", ".hpp", ".go", ".rs", ".rb", ".php", ".html", ".htm",
                       ".css", ".scss", ".less", ".json", ".xml", ".yaml", ".yml",
                       ".sh", ".bash", ".zsh", ".fish", ".sql", ".r", ".m", ".swift",
                       ".kt", ".dart", ".lua", ".pl", ".scala", ".clj", ".ex", ".exs",
                       ".vue", ".svelte", ".wasm", ".sol", ".toml", ".ini", ".cfg",
                       ".conf", ".env", ".lock", ".gradle", ".cmake", ".makefile"},
        "color": "\033[32m",
    },
    "可执行/安装包": {
        "extensions": {".exe", ".msi", ".app", ".pkg", ".deb", ".rpm", ".appimage",
                       ".apk", ".bat", ".cmd", ".com", ".scr", ".dll", ".so", ".dylib",
                       ".bin", ".run", ".sh", ".command"},
        "color": "\033[91m",
    },
    "电子书": {
        "extensions": {".epub", ".mobi", ".azw", ".azw3", ".cbz", ".cbr", ".djvu",
                       ".fb2", ".ibooks", ".lrf", ".lrx"},
        "color": "\033[94m",
    },
    "字体": {
        "extensions": {".ttf", ".otf", ".woff", ".woff2", ".eot", ".fon", ".fnt"},
        "color": "\033[95m",
    },
    "数据/数据库": {
        "extensions": {".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".parquet",
                       ".feather", ".h5", ".hdf5", ".mat", ".nc", ".grib", ".dbf"},
        "color": "\033[96m",
    },
    "系统/临时": {
        "extensions": {".tmp", ".temp", ".log", ".bak", ".old", ".swp", ".swo",
                       ".ds_store", ".thumbs.db", ".lock", ".part", ".crdownload",
                       ".download", ".cache", ".dat"},
        "color": "\033[90m",
    },
}

# 扩展名到分类的映射（构建一次）
_EXT_TO_CATEGORY: Dict[str, str] = {}
for cat, info in FILE_CATEGORIES.items():
    for ext in info["extensions"]:
        _EXT_TO_CATEGORY[ext] = cat

# 系统关键目录（禁止整理）
# 注意：不包含 /home 和 /tmp，用户主目录和临时目录允许整理
FORBIDDEN_DIRS = {
    "/", "/usr", "/etc", "/bin", "/sbin", "/lib", "/lib64",
    "/var", "/boot", "/dev", "/proc", "/sys", "/run",
    "/root", "/Applications", "/System", "/Library",
}


# ============================================================
# 工具函数
# ============================================================

def human_size(size_bytes: int) -> str:
    """将字节数转换为人类可读的大小"""
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} EB"


def get_category(filepath: str) -> str:
    """根据文件扩展名获取分类"""
    ext = Path(filepath).suffix.lower()
    return _EXT_TO_CATEGORY.get(ext, "其他")


def get_file_hash(filepath: str, chunk_size: int = 8192) -> Optional[str]:
    """计算文件 MD5 哈希（用于重复文件检测）"""
    try:
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def is_hidden(filepath: str) -> bool:
    """判断是否为隐藏文件（. 开头）"""
    return os.path.basename(filepath).startswith(".")


def is_forbidden_dir(target_dir: str) -> bool:
    """判断是否为禁止整理的系统目录"""
    resolved = os.path.realpath(target_dir)
    for forbidden in FORBIDDEN_DIRS:
        if resolved == forbidden or resolved.startswith(forbidden + "/"):
            return True
    return False


# ============================================================
# 目录扫描器
# ============================================================

class DirectoryScanner:
    """扫描目录，收集文件信息"""

    def __init__(self, target_dir: str, exclude_dirs: List[str] = None,
                 include_hidden: bool = False):
        self.target_dir = os.path.realpath(target_dir)
        self.exclude_dirs = set(exclude_dirs or [])
        self.include_hidden = include_hidden
        self.files: List[dict] = []
        self.total_size = 0
        self.errors: List[str] = []

    def scan(self) -> List[dict]:
        """执行扫描"""
        for root, dirs, filenames in os.walk(self.target_dir):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs
                       and not d.startswith(".")]
            # 跳过隐藏目录（除非包含）
            if not self.include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in filenames:
                if not self.include_hidden and filename.startswith("."):
                    continue
                filepath = os.path.join(root, filename)
                try:
                    stat = os.stat(filepath)
                    # 跳过符号链接
                    if os.path.islink(filepath):
                        continue
                    file_info = {
                        "path": filepath,
                        "name": filename,
                        "size": stat.st_size,
                        "ext": Path(filename).suffix.lower(),
                        "category": get_category(filepath),
                        "mtime": stat.st_mtime,
                        "atime": stat.st_atime,
                        "ctime": stat.st_ctime,
                    }
                    self.files.append(file_info)
                    self.total_size += stat.st_size
                except (OSError, PermissionError) as e:
                    self.errors.append(f"{filepath}: {e}")

        # 按大小降序排序
        self.files.sort(key=lambda x: x["size"], reverse=True)
        return self.files

    def get_category_stats(self) -> Dict[str, dict]:
        """按分类统计"""
        stats = defaultdict(lambda: {"count": 0, "size": 0})
        for f in self.files:
            cat = f["category"]
            stats[cat]["count"] += 1
            stats[cat]["size"] += f["size"]
        return dict(stats)

    def get_large_files(self, threshold_mb: int = 100) -> List[dict]:
        """获取大文件（超过阈值）"""
        threshold_bytes = threshold_mb * 1024 * 1024
        return [f for f in self.files if f["size"] >= threshold_bytes]

    def get_time_distribution(self) -> Dict[str, dict]:
        """按修改时间分布"""
        now = datetime.now().timestamp()
        dist = {
            "最近7天": {"count": 0, "size": 0},
            "7-30天": {"count": 0, "size": 0},
            "30-90天": {"count": 0, "size": 0},
            "90天以上": {"count": 0, "size": 0},
        }
        for f in self.files:
            age_days = (now - f["mtime"]) / 86400
            if age_days <= 7:
                key = "最近7天"
            elif age_days <= 30:
                key = "7-30天"
            elif age_days <= 90:
                key = "30-90天"
            else:
                key = "90天以上"
            dist[key]["count"] += 1
            dist[key]["size"] += f["size"]
        return dist

    def find_duplicates(self) -> Dict[str, List[dict]]:
        """检测重复文件（先按大小分组，再计算 MD5）"""
        # 按大小分组
        size_groups = defaultdict(list)
        for f in self.files:
            if f["size"] > 0:
                size_groups[f["size"]].append(f)

        # 只对大小相同的文件计算哈希
        duplicates = defaultdict(list)
        for size, group in size_groups.items():
            if len(group) < 2:
                continue
            hash_groups = defaultdict(list)
            for f in group:
                file_hash = get_file_hash(f["path"])
                if file_hash:
                    hash_groups[file_hash].append(f)
            for h, files in hash_groups.items():
                if len(files) > 1:
                    duplicates[h] = files

        return dict(duplicates)


# ============================================================
# 整理方案生成器
# ============================================================

class OrganizationPlanner:
    """生成文件整理方案"""

    def __init__(self, scanner: DirectoryScanner, strategy: str = "type"):
        self.scanner = scanner
        self.strategy = strategy
        self.plan: List[dict] = []  # 每个元素: {source, target, category, size}
        self.target_dirs: set = set()

    def generate(self) -> List[dict]:
        """生成整理方案"""
        for f in self.scanner.files:
            target_path = self._get_target_path(f)
            if target_path and target_path != f["path"]:
                self.plan.append({
                    "source": f["path"],
                    "target": target_path,
                    "category": f["category"],
                    "size": f["size"],
                    "name": f["name"],
                })
                self.target_dirs.add(os.path.dirname(target_path))
        return self.plan

    def _get_target_path(self, file_info: dict) -> Optional[str]:
        """根据策略计算目标路径"""
        base_dir = self.scanner.target_dir

        if self.strategy == "type":
            category = file_info["category"]
            target_dir = os.path.join(base_dir, category)
            target_path = os.path.join(target_dir, file_info["name"])
            # 处理同名冲突
            target_path = self._resolve_conflict(target_path)
            return target_path

        elif self.strategy == "date":
            mtime = datetime.fromtimestamp(file_info["mtime"])
            date_dir = mtime.strftime("%Y-%m")
            target_dir = os.path.join(base_dir, date_dir)
            target_path = os.path.join(target_dir, file_info["name"])
            target_path = self._resolve_conflict(target_path)
            return target_path

        elif self.strategy == "type-date":
            category = file_info["category"]
            mtime = datetime.fromtimestamp(file_info["mtime"])
            date_dir = mtime.strftime("%Y-%m")
            target_dir = os.path.join(base_dir, category, date_dir)
            target_path = os.path.join(target_dir, file_info["name"])
            target_path = self._resolve_conflict(target_path)
            return target_path

        return None

    def _resolve_conflict(self, target_path: str) -> str:
        """处理文件名冲突（自动重命名）"""
        if not os.path.exists(target_path):
            return target_path
        # 检查是否已经在 plan 中
        planned_targets = {p["target"] for p in self.plan}
        if target_path not in planned_targets and not os.path.exists(target_path):
            return target_path

        base, ext = os.path.splitext(target_path)
        counter = 1
        while True:
            new_path = f"{base} ({counter}){ext}"
            if not os.path.exists(new_path) and new_path not in planned_targets:
                return new_path
            counter += 1

    def get_summary(self) -> dict:
        """获取方案摘要"""
        category_stats = defaultdict(lambda: {"count": 0, "size": 0})
        for p in self.plan:
            cat = p["category"]
            category_stats[cat]["count"] += 1
            category_stats[cat]["size"] += p["size"]

        total_size = sum(p["size"] for p in self.plan)
        return {
            "total_files": len(self.plan),
            "total_size": total_size,
            "target_dirs": sorted(self.target_dirs),
            "category_stats": dict(category_stats),
        }


# ============================================================
# 整理执行器
# ============================================================

class OrganizationExecutor:
    """执行文件整理"""

    def __init__(self, plan: List[dict], target_dir: str):
        self.plan = plan
        self.target_dir = target_dir
        self.results = {"success": [], "failed": [], "skipped": []}
        self.undo_commands: List[str] = []

    def execute(self) -> dict:
        """执行整理方案"""
        backup_dir = os.path.join(self.target_dir, ".file-organizer-backup")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        undo_file = os.path.join(backup_dir, f"undo_{timestamp}.sh")

        for item in self.plan:
            source = item["source"]
            target = item["target"]
            try:
                # 创建目标目录
                os.makedirs(os.path.dirname(target), exist_ok=True)
                # 移动文件
                shutil.move(source, target)
                self.results["success"].append(item)
                # 记录 undo 命令
                self.undo_commands.append(
                    f'mv "{target}" "{source}"'
                )
            except (OSError, shutil.Error) as e:
                self.results["failed"].append({**item, "error": str(e)})

        # 写入 undo 脚本
        with open(undo_file, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write(f"# 文件整理回滚脚本 - 生成于 {timestamp}\n")
            f.write(f"# 整理目录: {self.target_dir}\n")
            f.write(f"# 共 {len(self.undo_commands)} 个操作\n\n")
            for cmd in reversed(self.undo_commands):
                f.write(cmd + "\n")
        os.chmod(undo_file, 0o755)

        self.results["undo_file"] = undo_file
        return self.results


# ============================================================
# 报告生成器
# ============================================================

class ReportGenerator:
    """生成整理报告"""

    @staticmethod
    def analyze_report(scanner: DirectoryScanner, large_threshold: int = 100,
                       duplicates: Dict = None) -> str:
        """生成分析报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("📂 目录分析报告")
        lines.append("=" * 60)
        lines.append(f"目录: {scanner.target_dir}")
        lines.append(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 总览
        lines.append("📊 总览")
        lines.append(f"  文件总数: {len(scanner.files)} 个")
        lines.append(f"  总大小: {human_size(scanner.total_size)}")
        if scanner.errors:
            lines.append(f"  扫描错误: {len(scanner.errors)} 个（权限不足等）")
        lines.append("")

        # 按类型分布
        lines.append("📁 按类型分布")
        cat_stats = scanner.get_category_stats()
        sorted_cats = sorted(cat_stats.items(), key=lambda x: x[1]["size"], reverse=True)
        lines.append(f"  {'类型':<12} {'数量':>6} {'大小':>10} {'占比':>8}")
        lines.append("  " + "-" * 40)
        for cat, info in sorted_cats:
            pct = (info["size"] / scanner.total_size * 100) if scanner.total_size > 0 else 0
            lines.append(f"  {cat:<12} {info['count']:>6} {human_size(info['size']):>10} {pct:>7.1f}%")
        lines.append("")

        # Top 10 大文件
        lines.append(f"🔝 Top 10 大文件")
        for i, f in enumerate(scanner.files[:10], 1):
            mtime = datetime.fromtimestamp(f["mtime"]).strftime("%Y-%m-%d")
            lines.append(f"  {i:2d}. {f['name']:<40} {human_size(f['size']):>10}  {f['category']:<8} {mtime}")
        lines.append("")

        # 大文件（超过阈值）
        large_files = scanner.get_large_files(large_threshold)
        if large_files:
            lines.append(f"⚠  大文件（>{large_threshold}MB）: {len(large_files)} 个，共 {human_size(sum(f['size'] for f in large_files))}")
            lines.append("")

        # 按时间分布
        lines.append("📅 按修改时间分布")
        time_dist = scanner.get_time_distribution()
        for period, info in time_dist.items():
            lines.append(f"  {period}: {info['count']} 个 ({human_size(info['size'])})")
        lines.append("")

        # 重复文件
        if duplicates:
            lines.append(f"🔄 重复文件: {len(duplicates)} 组")
            for i, (h, files) in enumerate(list(duplicates.items())[:5], 1):
                lines.append(f"  组 {i}: {len(files)} 个文件，每个 {human_size(files[0]['size'])}，浪费 {human_size(files[0]['size'] * (len(files)-1))}")
                for f in files[:3]:
                    lines.append(f"    - {f['path']}")
                if len(files) > 3:
                    lines.append(f"    ... 还有 {len(files)-3} 个")
            lines.append("")

        # 整理建议
        lines.append("💡 整理建议")
        if scanner.total_size > 0:
            # 找占比最大的类型
            top_cat = sorted_cats[0] if sorted_cats else None
            if top_cat:
                pct = top_cat[1]["size"] / scanner.total_size * 100
                if pct > 50:
                    lines.append(f"  - {top_cat[0]}占 {pct:.1f}% 空间，优先处理此类文件")
            # 长期未使用
            old_files = time_dist.get("90天以上", {"count": 0})
            if old_files["count"] > len(scanner.files) * 0.3:
                lines.append(f"  - {old_files['count']} 个文件超过90天未修改，可考虑归档")
            # 大文件
            if large_files:
                lines.append(f"  - {len(large_files)} 个大文件（>{large_threshold}MB），可移到外接存储或删除")
            # 重复
            if duplicates:
                wasted = sum(files[0]["size"] * (len(files) - 1) for files in duplicates.values())
                lines.append(f"  - 检测到 {len(duplicates)} 组重复文件，可释放 {human_size(wasted)} 空间")
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def dry_run_report(planner: OrganizationPlanner, scanner: DirectoryScanner) -> str:
        """生成预览报告"""
        lines = []
        summary = planner.get_summary()

        lines.append("=" * 60)
        lines.append("🔍 整理方案预览（dry-run，未实际执行）")
        lines.append("=" * 60)
        lines.append(f"目录: {scanner.target_dir}")
        lines.append(f"策略: {planner.strategy}")
        lines.append(f"预览时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("📋 方案摘要")
        lines.append(f"  将移动文件: {summary['total_files']} 个")
        lines.append(f"  总大小: {human_size(summary['total_size'])}")
        lines.append(f"  将创建目录: {len(summary['target_dirs'])} 个")
        skipped = len(scanner.files) - summary['total_files']
        if skipped > 0:
            lines.append(f"  跳过（已在目标位置）: {skipped} 个")
        lines.append("")

        lines.append("📂 目标目录结构")
        for d in summary["target_dirs"]:
            rel = os.path.relpath(d, scanner.target_dir)
            lines.append(f"  {rel}/")
        lines.append("")

        lines.append("📁 分类统计")
        for cat, info in sorted(summary["category_stats"].items(), key=lambda x: x[1]["size"], reverse=True):
            lines.append(f"  {cat}: {info['count']} 个 ({human_size(info['size'])})")
        lines.append("")

        # 移动示例（前 20 个）
        lines.append("📝 移动示例（前 20 个）")
        for i, p in enumerate(planner.plan[:20], 1):
            src_name = p["name"]
            dst_rel = os.path.relpath(p["target"], scanner.target_dir)
            lines.append(f"  {i:2d}. {src_name} → {dst_rel}")
        if len(planner.plan) > 20:
            lines.append(f"  ... 还有 {len(planner.plan) - 20} 个文件")
        lines.append("")

        lines.append("⚠  以上为预览，未实际移动任何文件。")
        lines.append("   确认执行后将实际移动文件。建议先备份重要文件。")
        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def execute_report(results: dict, scanner: DirectoryScanner, strategy: str) -> str:
        """生成执行报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("✅ 文件整理执行报告")
        lines.append("=" * 60)
        lines.append(f"目录: {scanner.target_dir}")
        lines.append(f"策略: {strategy}")
        lines.append(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("📊 执行结果")
        lines.append(f"  成功移动: {len(results['success'])} 个")
        lines.append(f"  失败: {len(results['failed'])} 个")
        lines.append(f"  跳过: {len(results['skipped'])} 个")
        success_size = sum(p["size"] for p in results["success"])
        lines.append(f"  成功移动总大小: {human_size(success_size)}")
        lines.append("")

        if results["failed"]:
            lines.append("⚠  失败文件")
            for f in results["failed"][:10]:
                lines.append(f"  - {f['name']}: {f.get('error', '未知错误')}")
            if len(results["failed"]) > 10:
                lines.append(f"  ... 还有 {len(results['failed']) - 10} 个")
            lines.append("")

        if "undo_file" in results:
            lines.append("🔄 回滚")
            lines.append(f"  如需撤销，运行: {results['undo_file']}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="文件整理助手 - 扫描、分类、整理文件目录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --dir ~/Downloads --mode analyze
  %(prog)s --dir ~/Downloads --mode dry-run --strategy type
  %(prog)s --dir ~/Downloads --mode execute --strategy type
  %(prog)s --dir ~/Photos --mode dry-run --strategy date
  %(prog)s --dir ~/Downloads --mode analyze --large-threshold 100
  %(prog)s --dir ~/Downloads --mode analyze --detect-duplicates
        """,
    )
    parser.add_argument("--dir", "-d", required=True, help="目标目录路径")
    parser.add_argument("--mode", "-m", choices=["analyze", "dry-run", "execute"],
                        default="analyze", help="运行模式（默认 analyze）")
    parser.add_argument("--strategy", "-s", choices=["type", "date", "type-date"],
                        default="type", help="整理策略（默认 type）")
    parser.add_argument("--exclude", "-e", nargs="*", default=[],
                        help="排除的子目录名（如 node_modules .git __pycache__）")
    parser.add_argument("--large-threshold", "-L", type=int, default=100,
                        help="大文件阈值（MB，默认 100）")
    parser.add_argument("--detect-duplicates", action="store_true",
                        help="检测重复文件（可能较慢）")
    parser.add_argument("--include-hidden", action="store_true",
                        help="包含隐藏文件（默认不包含）")
    parser.add_argument("--output", "-o", help="将报告写入文件")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="execute 模式下跳过确认（危险，慎用）")

    args = parser.parse_args()

    # 解析目录路径
    target_dir = os.path.expanduser(args.dir)
    if not os.path.exists(target_dir):
        print(f"错误：目录不存在 - {target_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(target_dir):
        print(f"错误：不是目录 - {target_dir}", file=sys.stderr)
        sys.exit(1)

    # 安全检查：禁止系统目录
    if is_forbidden_dir(target_dir):
        print(f"错误：禁止整理系统关键目录 - {target_dir}", file=sys.stderr)
        print("为安全起见，本工具不支持整理系统目录。", file=sys.stderr)
        sys.exit(1)

    # execute 模式确认
    if args.mode == "execute" and not args.yes:
        print(f"⚠  即将实际整理目录: {target_dir}")
        print(f"   策略: {args.strategy}")
        print("   此操作将移动文件，建议先备份。")
        confirm = input("   确认执行？(yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("已取消。")
            sys.exit(0)

    # 扫描目录
    print(f"正在扫描目录: {target_dir} ...", file=sys.stderr)
    scanner = DirectoryScanner(
        target_dir,
        exclude_dirs=args.exclude,
        include_hidden=args.include_hidden,
    )
    scanner.scan()
    print(f"扫描完成: {len(scanner.files)} 个文件，{human_size(scanner.total_size)}",
          file=sys.stderr)

    # 重复文件检测
    duplicates = None
    if args.detect_duplicates:
        print("正在检测重复文件（可能较慢）...", file=sys.stderr)
        duplicates = scanner.find_duplicates()
        print(f"检测完成: {len(duplicates)} 组重复文件", file=sys.stderr)

    # 根据模式生成报告
    if args.mode == "analyze":
        report = ReportGenerator.analyze_report(
            scanner, args.large_threshold, duplicates
        )
    elif args.mode == "dry-run":
        planner = OrganizationPlanner(scanner, args.strategy)
        planner.generate()
        report = ReportGenerator.dry_run_report(planner, scanner)
    elif args.mode == "execute":
        planner = OrganizationPlanner(scanner, args.strategy)
        planner.generate()
        print(f"正在执行整理: {len(planner.plan)} 个文件 ...", file=sys.stderr)
        executor = OrganizationExecutor(planner.plan, target_dir)
        results = executor.execute()
        report = ReportGenerator.execute_report(results, scanner, args.strategy)

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已写入: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
