#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
环境变量管理脚本

功能：
- 解析 .env 文件（支持注释、引号、export 前缀）
- 多环境对比（差异检测）
- 配置审计（空值、重复、格式校验、密钥检测）
- 生成 .env.example 模板
- 多格式导出（shell/json/docker/yaml）
- 密钥脱敏显示

用法：
  python3 manage_env.py --file .env
  python3 manage_env.py --file .env --compare .env.prod
  python3 manage_env.py --file .env --template
  python3 manage_env.py --file .env --validate
  python3 manage_env.py --file .env --audit
  python3 manage_env.py --file .env --export json
  python3 manage_env.py --file .env --export docker
  python3 manage_env.py --file .env --no-mask
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple


# ============================================================
# 密钥关键词
# ============================================================

SECRET_KEYWORDS = [
    "secret", "password", "passwd", "token", "api_key", "apikey",
    "private_key", "access_key", "auth", "credential", "credentials",
    "db_pass", "database_url", "connection_string", "jwt", "signing_key",
    "encryption_key", "aws_secret", "azure_key", "gcp_key",
]

# 值中包含密码的模式（如 user:pass@host）
PASSWORD_IN_VALUE = re.compile(r'://[^:]+:([^@]+)@')


# ============================================================
# .env 解析
# ============================================================

class EnvEntry:
    """单个环境变量条目"""
    def __init__(self, key: str, value: str, line_num: int,
                 raw_line: str, comment: str = "", is_export: bool = False):
        self.key = key
        self.value = value
        self.line_num = line_num
        self.raw_line = raw_line
        self.comment = comment
        self.is_export = is_export


def parse_env_file(filepath: str) -> Tuple[List[EnvEntry], List[str]]:
    """
    解析 .env 文件
    返回 (条目列表, 原始行列表)
    """
    entries = []
    raw_lines = []

    if not os.path.exists(filepath):
        print(f"错误：文件不存在：{filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_comment = ""
    for i, line in enumerate(lines, 1):
        raw_lines.append(line.rstrip('\n'))
        stripped = line.strip()

        # 空行
        if not stripped:
            current_comment = ""
            continue

        # 注释行
        if stripped.startswith('#'):
            current_comment = stripped.lstrip('#').strip()
            continue

        # export 前缀
        is_export = False
        if stripped.startswith('export '):
            is_export = True
            stripped = stripped[7:].strip()

        # 解析 KEY=VALUE
        if '=' not in stripped:
            continue

        key, _, value = stripped.partition('=')
        key = key.strip()

        # 移除行内注释（值中 # 前有空格才算注释）
        comment = ""
        if ' #' in value:
            value, comment = value.split(' #', 1)
            value = value.strip()
            comment = comment.strip()

        # 去除引号
        value = value.strip()
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

        if not key or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
            continue

        entries.append(EnvEntry(
            key=key,
            value=value,
            line_num=i,
            raw_line=line.rstrip('\n'),
            comment=comment or current_comment,
            is_export=is_export,
        ))
        current_comment = ""

    return entries, raw_lines


def entries_to_dict(entries: List[EnvEntry]) -> Dict[str, str]:
    """转换为字典（后值覆盖前值）"""
    result = {}
    for e in entries:
        result[e.key] = e.value
    return result


# ============================================================
# 密钥检测与脱敏
# ============================================================

def is_secret_key(key: str) -> bool:
    """判断变量名是否可能是密钥"""
    key_lower = key.lower()
    return any(kw in key_lower for kw in SECRET_KEYWORDS)


def mask_value(key: str, value: str) -> str:
    """脱敏处理"""
    if not value:
        return "(空)"

    # URL 中的密码
    url_match = PASSWORD_IN_VALUE.search(value)
    if url_match:
        password = url_match.group(1)
        return value.replace(password, '***')

    # 密钥变量
    if is_secret_key(key):
        if len(value) <= 8:
            return '***'
        return value[:4] + '***' + value[-4:]

    return value


# ============================================================
# 格式校验
# ============================================================

def validate_entry(entry: EnvEntry) -> List[str]:
    """校验单个变量，返回问题列表"""
    issues = []
    key = entry.key
    value = entry.value
    key_lower = key.lower()

    # 空值
    if not value:
        issues.append("值为空")
        return issues

    # 端口校验
    if 'port' in key_lower:
        try:
            port = int(value)
            if port < 1 or port > 65535:
                issues.append(f"端口超出范围（1-65535）：{port}")
        except ValueError:
            issues.append(f"端口不是有效整数：{value}")

    # URL 校验
    if any(kw in key_lower for kw in ['url', 'uri', 'endpoint', 'host']):
        if not re.match(r'^https?://', value) and not re.match(r'^[a-zA-Z0-9.-]+:\d+$', value):
            if '://' not in value and not value.startswith('/'):
                issues.append(f"可能不是有效的 URL：{value[:50]}")

    # 邮箱校验
    if 'email' in key_lower or 'mail' in key_lower:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
            issues.append(f"可能不是有效的邮箱：{value[:50]}")

    # 布尔值校验
    if any(kw in key_lower for kw in ['enable', 'disable', 'debug', 'ssl', 'tls', 'cache']):
        if value.lower() not in ('true', 'false', 'yes', 'no', '1', '0', 'on', 'off'):
            if len(value) < 20:  # 短值才提示
                issues.append(f"可能不是有效的布尔值：{value}")

    # 路径校验
    if any(kw in key_lower for kw in ['path', 'dir', 'file', 'cert', 'key_file']):
        if value.startswith('/') or value.startswith('./') or value.startswith('../'):
            if not os.path.exists(value):
                issues.append(f"路径不存在：{value}")

    return issues


# ============================================================
# 审计
# ============================================================

def audit_env(entries: List[EnvEntry]) -> Dict:
    """审计 .env 文件"""
    result = {
        "total": len(entries),
        "empty": [],
        "duplicates": {},
        "format_issues": [],
        "secrets": [],
        "passed": [],
    }

    # 检测重复
    key_counts = {}
    for e in entries:
        key_counts.setdefault(e.key, []).append(e.line_num)

    for key, lines in key_counts.items():
        if len(lines) > 1:
            result["duplicates"][key] = lines

    # 逐项检查
    seen_keys = set()
    for e in entries:
        # 空值
        if not e.value:
            result["empty"].append({"key": e.key, "line": e.line_num})
            continue

        # 格式校验
        issues = validate_entry(e)
        if issues:
            result["format_issues"].append({
                "key": e.key,
                "line": e.line_num,
                "value": e.value[:60],
                "issues": issues,
            })

        # 密钥检测
        if is_secret_key(e.key) or PASSWORD_IN_VALUE.search(e.value):
            result["secrets"].append({
                "key": e.key,
                "line": e.line_num,
                "masked": mask_value(e.key, e.value),
            })

        if e.key not in seen_keys and e.value:
            result["passed"].append(e.key)
            seen_keys.add(e.key)

    return result


# ============================================================
# 对比
# ============================================================

def compare_env(entries_a: List[EnvEntry], entries_b: List[EnvEntry]) -> Dict:
    """对比两个 .env 文件"""
    dict_a = entries_to_dict(entries_a)
    dict_b = entries_to_dict(entries_b)

    keys_a = set(dict_a.keys())
    keys_b = set(dict_b.keys())

    only_a = sorted(keys_a - keys_b)
    only_b = sorted(keys_b - keys_a)
    common = sorted(keys_a & keys_b)

    different = []
    same = []
    for key in common:
        if dict_a[key] != dict_b[key]:
            different.append({
                "key": key,
                "value_a": mask_value(key, dict_a[key]),
                "value_b": mask_value(key, dict_b[key]),
            })
        else:
            same.append(key)

    return {
        "only_a": only_a,
        "only_b": only_b,
        "different": different,
        "same": same,
        "count_a": len(dict_a),
        "count_b": len(dict_b),
    }


# ============================================================
# 模板生成
# ============================================================

def generate_template(entries: List[EnvEntry], raw_lines: List[str]) -> str:
    """生成 .env.example"""
    lines = []
    lines.append("# 环境变量模板")
    lines.append("# 复制此文件为 .env 并填写实际值")
    lines.append("# 请勿将包含真实密钥的 .env 文件提交到版本控制")
    lines.append("")

    for e in entries:
        # 保留注释
        if e.comment:
            lines.append(f"# {e.comment}")

        if is_secret_key(e.key) or PASSWORD_IN_VALUE.search(e.value):
            # 密钥变量：清空值，给提示
            lines.append(f"{e.key}=")
        else:
            # 普通变量：保留示例值
            lines.append(f"{e.key}={e.value}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# 导出
# ============================================================

def export_shell(entries: List[EnvEntry]) -> str:
    """导出为 shell 格式"""
    lines = ["#!/bin/bash", "# 环境变量导出", ""]
    for e in entries:
        value = e.value.replace("'", "'\\''")
        lines.append(f"export {e.key}='{value}'")
    return "\n".join(lines)


def export_json(entries: List[EnvEntry]) -> str:
    """导出为 JSON"""
    data = entries_to_dict(entries)
    return json.dumps(data, ensure_ascii=False, indent=2)


def export_docker(entries: List[EnvEntry]) -> str:
    """导出为 Docker Compose 格式"""
    lines = ["environment:"]
    for e in entries:
        lines.append(f"  - {e.key}={e.value}")
    return "\n".join(lines)


def export_yaml(entries: List[EnvEntry]) -> str:
    """导出为 YAML"""
    lines = ["env:"]
    for e in entries:
        lines.append(f"  {e.key}: \"{e.value}\"")
    return "\n".join(lines)


# ============================================================
# 输出格式化
# ============================================================

def format_parse(entries: List[EnvEntry], mask: bool = True) -> str:
    """格式化解析结果"""
    lines = []
    lines.append("📋 环境变量解析结果")
    lines.append("━" * 40)
    lines.append(f"变量数：{len(entries)}")

    secrets = []
    normal = []
    for e in entries:
        if is_secret_key(e.key) or PASSWORD_IN_VALUE.search(e.value):
            secrets.append(e)
        else:
            normal.append(e)

    if secrets:
        lines.append("")
        lines.append(f"🔐 敏感变量（{len(secrets)} 个，已脱敏）：")
        for e in secrets:
            val = mask_value(e.key, e.value) if mask else e.value
            lines.append(f"  {e.key}={val}")

    if normal:
        lines.append("")
        lines.append(f"📝 普通变量（{len(normal)} 个）：")
        for e in normal:
            val = e.value
            if len(val) > 60:
                val = val[:57] + "..."
            lines.append(f"  {e.key}={val}")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


def format_compare(result: Dict, name_a: str, name_b: str) -> str:
    """格式化对比结果"""
    lines = []
    lines.append("🔍 环境对比报告")
    lines.append("━" * 40)
    lines.append(f"文件 A：{name_a}（{result['count_a']} 个变量）")
    lines.append(f"文件 B：{name_b}（{result['count_b']} 个变量）")

    if result["only_a"]:
        lines.append("")
        lines.append(f"⚠️  仅在 A 中存在（{len(result['only_a'])} 个）：")
        for k in result["only_a"]:
            lines.append(f"  - {k}")

    if result["only_b"]:
        lines.append("")
        lines.append(f"⚠️  仅在 B 中存在（{len(result['only_b'])} 个）：")
        for k in result["only_b"]:
            lines.append(f"  - {k}")

    if result["different"]:
        lines.append("")
        lines.append(f"❌ 值不同（{len(result['different'])} 个）：")
        for d in result["different"]:
            lines.append(f"  - {d['key']}: A={d['value_a']}, B={d['value_b']}")

    lines.append("")
    lines.append(f"✅ 相同（{len(result['same'])} 个）")
    lines.append("━" * 40)
    return "\n".join(lines)


def format_audit(result: Dict) -> str:
    """格式化审计结果"""
    lines = []
    lines.append("🔒 配置审计报告")
    lines.append("━" * 40)
    lines.append(f"总变量数：{result['total']}")

    has_issues = False

    if result["empty"]:
        has_issues = True
        lines.append("")
        lines.append(f"❌ 空值变量（{len(result['empty'])} 个）：")
        for e in result["empty"]:
            lines.append(f"  - {e['key']}=（第 {e['line']} 行，未填写）")

    if result["duplicates"]:
        has_issues = True
        lines.append("")
        lines.append(f"❌ 重复定义（{len(result['duplicates'])} 个）：")
        for key, lines_list in result["duplicates"].items():
            lines.append(f"  - {key}：定义于第 {', '.join(map(str, lines_list))} 行")

    if result["format_issues"]:
        has_issues = True
        lines.append("")
        lines.append(f"❌ 格式问题（{len(result['format_issues'])} 个）：")
        for fi in result["format_issues"]:
            lines.append(f"  - {fi['key']}（第 {fi['line']} 行）：")
            for issue in fi["issues"]:
                lines.append(f"    · {issue}")

    if result["secrets"]:
        lines.append("")
        lines.append(f"🔐 疑似密钥（{len(result['secrets'])} 个）：")
        for s in result["secrets"]:
            lines.append(f"  - {s['key']}（第 {s['line']} 行）：{s['masked']}")

    if not has_issues:
        lines.append("")
        lines.append("✅ 未发现问题")

    lines.append("")
    lines.append(f"✅ 校验通过：{len(result['passed'])} 个变量")
    lines.append("")
    lines.append("💡 建议：")
    lines.append("  - 确保 .env 已加入 .gitignore")
    lines.append("  - 空值变量请尽快填写")
    lines.append("  - 生产环境密钥建议使用密钥管理服务")
    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="环境变量管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", required=True, help=".env 文件路径")
    parser.add_argument("--compare", "-c", metavar="FILE", help="对比另一个 .env 文件")
    parser.add_argument("--template", "-t", action="store_true", help="生成 .env.example")
    parser.add_argument("--validate", "-v", action="store_true", help="格式校验")
    parser.add_argument("--audit", "-a", action="store_true", help="完整审计")
    parser.add_argument("--export", "-e", choices=["shell", "json", "docker", "yaml"],
                        help="导出格式")
    parser.add_argument("--no-mask", action="store_true", help="不脱敏显示（谨慎使用）")
    parser.add_argument("--output", "-o", metavar="FILE", help="输出到文件")
    args = parser.parse_args()

    # 解析文件
    entries, raw_lines = parse_env_file(args.file)

    output = ""

    # 对比模式
    if args.compare:
        entries_b, _ = parse_env_file(args.compare)
        result = compare_env(entries, entries_b)
        output = format_compare(result, os.path.basename(args.file),
                                os.path.basename(args.compare))

    # 模板模式
    elif args.template:
        output = generate_template(entries, raw_lines)

    # 审计模式
    elif args.audit:
        result = audit_env(entries)
        output = format_audit(result)

    # 校验模式
    elif args.validate:
        result = audit_env(entries)
        # 只显示格式问题
        issues = result["format_issues"]
        if issues:
            output = f"📋 格式校验：发现 {len(issues)} 个问题\n"
            output += "━" * 40 + "\n"
            for fi in issues:
                output += f"  - {fi['key']}（第 {fi['line']} 行）：\n"
                for issue in fi["issues"]:
                    output += f"    · {issue}\n"
        else:
            output = "✅ 格式校验通过，未发现问题"

    # 导出模式
    elif args.export:
        if args.export == "shell":
            output = export_shell(entries)
        elif args.export == "json":
            output = export_json(entries)
        elif args.export == "docker":
            output = export_docker(entries)
        elif args.export == "yaml":
            output = export_yaml(entries)

    # 默认：解析显示
    else:
        output = format_parse(entries, mask=not args.no_mask)

    # 输出
    print(output)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output + "\n")
        print(f"\n已保存到：{args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
