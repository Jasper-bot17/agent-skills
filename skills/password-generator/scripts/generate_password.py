#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
密码生成与强度检测脚本

功能：
- 生成随机密码（可定制长度和字符集）
- 生成易记口令（Passphrase）
- 生成 PIN 码
- 评估密码强度（熵值、常见密码、模式检测）
- 检查密码策略合规
- 批量生成

用法：
  python3 generate_password.py
  python3 generate_password.py --length 20
  python3 generate_password.py --type passphrase --words 5
  python3 generate_password.py --type pin --length 6
  python3 generate_password.py --count 10
  python3 generate_password.py --check "MyP@ssw0rd!"
  python3 generate_password.py --check "abc123" --policy min-length=8,require-upper
  python3 generate_password.py --count 20 --output passwords.txt
"""

import argparse
import math
import re
import secrets
import string
import sys
from typing import Dict, List, Optional, Tuple


# ============================================================
# 字符集
# ============================================================

UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?"
AMBIGUOUS = "0O1lI5S2Z"  # 易混淆字符

# 易记口令单词库（精选常见英文单词，5-8 字母）
WORD_LIST = [
    "apple", "beach", "cloud", "dance", "eagle", "flame", "grape", "house",
    "ivory", "jolly", "knife", "lemon", "mango", "noble", "ocean", "piano",
    "queen", "river", "sugar", "tiger", "unity", "vivid", "water", "xenon",
    "yacht", "zebra", "amber", "brave", "candy", "dream", "earth", "frost",
    "green", "happy", "input", "joker", "karma", "light", "music", "night",
    "olive", "peach", "quick", "royal", "smile", "trust", "urban", "voice",
    "wheat", "youth", "zesty", "angel", "blaze", "crisp", "daisy", "ember",
    "fresh", "glide", "honey", "ivory", "jazzy", "kites", "lunar", "magic",
    "nectar", "orbit", "plush", "quill", "raven", "solar", "thunder", "ultra",
    "vapor", "witty", "yummy", "zephyr", "arrow", "bloom", "cider", "dusk",
    "echo", "fable", "glory", "haven", "iris", "jewel", "kitten", "lucky",
    "maple", "nova", "opal", "pixel", "quest", "ruby", "storm", "trail",
    "umbra", "violet", "willow", "xray", "yield", "zenith", "acorn", "breeze",
    "coral", "dolphin", "elm", "fern", "grove", "hearth", "ink", "jade",
    "kelp", "lotus", "meadow", "nebula", "onyx", "pine", "quartz", "rose",
    "sage", "tide", "umber", "vine", "wolf", "yucca", "zinc",
]


# ============================================================
# 常见弱密码列表
# ============================================================

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "12345678", "12345", "1234567",
    "1234567890", "qwerty", "abc123", "password1", "111111", "123123",
    "admin", "letmein", "welcome", "monkey", "dragon", "master", "login",
    "princess", "qwerty123", "solo", "passw0rd", "starwars", "iloveyou",
    "666666", "888888", "999999", "000000", "555555", "333333", "222222",
    "7777777", "444444", "123321", "654321", "123456a", "a123456",
    "123456b", "123456c", "123456d", "123456e", "123456f", "123456g",
    "123456h", "123456i", "123456j", "123456k", "123456l", "123456m",
    "123456n", "123456o", "123456p", "123456q", "123456r", "123456s",
    "123456t", "123456u", "123456v", "123456w", "123456x", "123456y",
    "123456z", "abcdef", "abcdefg", "abcdefgh", "abcdefghi", "abcdefghij",
    "qazwsx", "qazwsxedc", "asdfgh", "asdfghjkl", "zxcvbn", "zxcvbnm",
    "1q2w3e", "1q2w3e4r", "1q2w3e4r5t", "qwertyuiop", "asdf1234",
    "zxcv1234", "q1w2e3r4", "q1w2e3r4t5", "1qaz2wsx", "1qaz2wsx3edc",
    "zaq12wsx", "zaq12wsx", "password123", "password12", "password1234",
    "pass1234", "pass123", "p@ssw0rd", "p@ssword", "passw0rd123",
    "test", "test123", "test1234", "testing", "guest", "guest123",
    "root", "toor", "changeme", "default", "temp", "temp123",
    "hello", "hello123", "hello1234", "world", "world123",
    "football", "baseball", "soccer", "hockey", "basketball",
    "charlie", "thomas", "george", "jennifer", "jordan", "michael",
    "superman", "batman", "spiderman", "ironman", "hulk",
    "shadow", "sunshine", "summer", "winter", "spring", "autumn",
    "freedom", "whatever", "trustno1", "trustnoone", "access",
    "computer", "internet", "network", "server", "system",
    "microsoft", "google", "apple", "amazon", "facebook",
    "123qwe", "123qweasd", "qwe123", "qweasd", "qweasdzxc",
    "123asd", "123asdf", "asd123", "asdf123", "asdf1234",
    "zxc123", "zxcv123", "zxcv1234", "123zxc", "123zxcv",
    "qweasd123", "qweasdzxc123", "1234qwer", "qwer1234",
    "asdfzxcv", "zxcvasdf", "qazwsx123", "qazwsxedc123",
}


# ============================================================
# 密码生成
# ============================================================

def generate_random_password(length: int = 16,
                             use_upper: bool = True,
                             use_lower: bool = True,
                             use_digits: bool = True,
                             use_symbols: bool = True,
                             no_ambiguous: bool = False) -> str:
    """生成随机密码"""
    if length < 4:
        raise ValueError("密码长度至少为 4 位")

    charset = ""
    required = []

    if use_upper:
        chars = UPPERCASE
        if no_ambiguous:
            chars = ''.join(c for c in chars if c not in AMBIGUOUS)
        charset += chars
        required.append(secrets.choice(chars))

    if use_lower:
        chars = LOWERCASE
        if no_ambiguous:
            chars = ''.join(c for c in chars if c not in AMBIGUOUS)
        charset += chars
        required.append(secrets.choice(chars))

    if use_digits:
        chars = DIGITS
        if no_ambiguous:
            chars = ''.join(c for c in chars if c not in AMBIGUOUS)
        charset += chars
        required.append(secrets.choice(chars))

    if use_symbols:
        charset += SYMBOLS
        required.append(secrets.choice(SYMBOLS))

    if not charset:
        raise ValueError("至少需要选择一种字符类型")

    # 填充剩余字符
    remaining = length - len(required)
    if remaining < 0:
        remaining = 0
        required = required[:length]

    password_chars = required + [secrets.choice(charset) for _ in range(remaining)]

    # 打乱顺序
    secrets.SystemRandom().shuffle(password_chars)
    return ''.join(password_chars)


def generate_passphrase(words: int = 4, separator: str = "-",
                        capitalize: bool = True) -> str:
    """生成易记口令"""
    if words < 2:
        raise ValueError("口令至少需要 2 个单词")

    selected = [secrets.choice(WORD_LIST) for _ in range(words)]
    if capitalize:
        selected = [w.capitalize() for w in selected]

    return separator.join(selected)


def generate_pin(length: int = 6, allow_repeats: bool = True,
                 allow_sequences: bool = True) -> str:
    """生成 PIN 码"""
    if length < 4:
        raise ValueError("PIN 码长度至少为 4 位")
    if length > 12:
        raise ValueError("PIN 码长度不超过 12 位")

    for _ in range(100):  # 最多尝试 100 次
        pin = ''.join(secrets.choice(DIGITS) for _ in range(length))

        if not allow_repeats and len(set(pin)) < length:
            continue

        if not allow_sequences:
            has_seq = False
            for i in range(len(pin) - 2):
                a, b, c = int(pin[i]), int(pin[i+1]), int(pin[i+2])
                if (b - a == 1 and c - b == 1) or (a - b == 1 and b - c == 1):
                    has_seq = True
                    break
            if has_seq:
                continue

        return pin

    # 兜底：返回纯随机
    return ''.join(secrets.choice(DIGITS) for _ in range(length))


# ============================================================
# 强度评估
# ============================================================

def calculate_entropy(password: str) -> float:
    """计算密码熵值（bits）"""
    charset_size = 0
    if re.search(r'[a-z]', password):
        charset_size += 26
    if re.search(r'[A-Z]', password):
        charset_size += 26
    if re.search(r'[0-9]', password):
        charset_size += 10
    if re.search(r'[^a-zA-Z0-9]', password):
        charset_size += len(SYMBOLS)

    if charset_size == 0:
        return 0.0

    return len(password) * math.log2(charset_size)


def detect_patterns(password: str) -> List[str]:
    """检测密码中的弱模式"""
    patterns = []

    # 连续字符（abc, 123）
    for i in range(len(password) - 2):
        a, b, c = password[i], password[i+1], password[i+2]
        if (ord(b) - ord(a) == 1 and ord(c) - ord(b) == 1):
            patterns.append(f"包含连续递增序列: {a}{b}{c}")
            break
        if (ord(a) - ord(b) == 1 and ord(b) - ord(c) == 1):
            patterns.append(f"包含连续递减序列: {a}{b}{c}")
            break

    # 重复字符（aaa, 111）
    for i in range(len(password) - 2):
        if password[i] == password[i+1] == password[i+2]:
            patterns.append(f"包含重复字符: {password[i]}{password[i+1]}{password[i+2]}")
            break

    # 键盘序列（qwerty, asdf）
    keyboard_rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    lower_pwd = password.lower()
    for row in keyboard_rows:
        for i in range(len(row) - 3):
            seq = row[i:i+4]
            if seq in lower_pwd:
                patterns.append(f"包含键盘序列: {seq}")
                break

    # 全小写
    if password.islower():
        patterns.append("全部为小写字母")

    # 全大写
    if password.isupper():
        patterns.append("全部为大写字母")

    # 全数字
    if password.isdigit():
        patterns.append("全部为数字")

    # 全字母
    if password.isalpha():
        patterns.append("不包含数字和符号")

    return patterns


def evaluate_strength(password: str) -> Dict:
    """评估密码强度"""
    result = {
        "password": password,
        "length": len(password),
        "entropy": 0.0,
        "level": "",
        "level_icon": "",
        "has_upper": bool(re.search(r'[A-Z]', password)),
        "has_lower": bool(re.search(r'[a-z]', password)),
        "has_digits": bool(re.search(r'[0-9]', password)),
        "has_symbols": bool(re.search(r'[^a-zA-Z0-9]', password)),
        "is_common": False,
        "patterns": [],
        "suggestions": [],
    }

    # 常见密码检测
    if password.lower() in COMMON_PASSWORDS:
        result["is_common"] = True
        result["level"] = "极弱"
        result["level_icon"] = "🔴"
        result["suggestions"].append("这是一个常见弱密码，极易被破解，请立即更换")
        result["entropy"] = calculate_entropy(password)
        return result

    # 熵值计算
    entropy = calculate_entropy(password)
    result["entropy"] = entropy

    # 模式检测
    patterns = detect_patterns(password)
    result["patterns"] = patterns

    # 等级判定
    if entropy < 28:
        result["level"] = "极弱"
        result["level_icon"] = "🔴"
    elif entropy < 36:
        result["level"] = "弱"
        result["level_icon"] = "🟠"
    elif entropy < 60:
        result["level"] = "中等"
        result["level_icon"] = "🟡"
    elif entropy < 128:
        result["level"] = "强"
        result["level_icon"] = "🟢"
    else:
        result["level"] = "极强"
        result["level_icon"] = "🔵"

    # 模式会降低等级
    if patterns and result["level"] in ("强", "极强"):
        result["level"] = "中等"
        result["level_icon"] = "🟡"
        result["suggestions"].append("密码包含弱模式，实际安全性低于理论熵值")

    # 改进建议
    if len(password) < 12:
        result["suggestions"].append(f"长度偏短（{len(password)}位），建议至少 12 位")
    if not result["has_upper"]:
        result["suggestions"].append("建议添加大写字母")
    if not result["has_lower"]:
        result["suggestions"].append("建议添加小写字母")
    if not result["has_digits"]:
        result["suggestions"].append("建议添加数字")
    if not result["has_symbols"]:
        result["suggestions"].append("建议添加特殊符号（如 !@#$%）")

    if not result["suggestions"] and result["level"] in ("强", "极强"):
        result["suggestions"].append("密码强度良好，继续保持")

    return result


# ============================================================
# 策略合规检查
# ============================================================

def check_policy(password: str, policy: Dict) -> Dict:
    """检查密码是否符合策略"""
    result = {
        "password": password,
        "checks": [],
        "passed": True,
        "missing": [],
    }

    # 最小长度
    min_length = policy.get("min_length", 0)
    if min_length > 0:
        ok = len(password) >= min_length
        result["checks"].append({
            "item": f"最小长度 {min_length} 位",
            "actual": f"{len(password)} 位",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append(f"长度不足（需要 {min_length} 位，当前 {len(password)} 位）")

    # 最大长度
    max_length = policy.get("max_length", 0)
    if max_length > 0:
        ok = len(password) <= max_length
        result["checks"].append({
            "item": f"最大长度 {max_length} 位",
            "actual": f"{len(password)} 位",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append(f"长度超过限制（最大 {max_length} 位）")

    # 必须包含大写
    if policy.get("require_upper", False):
        ok = bool(re.search(r'[A-Z]', password))
        result["checks"].append({
            "item": "包含大写字母",
            "actual": "有" if ok else "无",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append("缺少大写字母")

    # 必须包含小写
    if policy.get("require_lower", False):
        ok = bool(re.search(r'[a-z]', password))
        result["checks"].append({
            "item": "包含小写字母",
            "actual": "有" if ok else "无",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append("缺少小写字母")

    # 必须包含数字
    if policy.get("require_digits", False):
        ok = bool(re.search(r'[0-9]', password))
        result["checks"].append({
            "item": "包含数字",
            "actual": "有" if ok else "无",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append("缺少数字")

    # 必须包含符号
    if policy.get("require_symbols", False):
        ok = bool(re.search(r'[^a-zA-Z0-9]', password))
        result["checks"].append({
            "item": "包含特殊符号",
            "actual": "有" if ok else "无",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append("缺少特殊符号")

    # 禁止常见密码
    if policy.get("forbid_common", False):
        ok = password.lower() not in COMMON_PASSWORDS
        result["checks"].append({
            "item": "非常见弱密码",
            "actual": "通过" if ok else "命中",
            "passed": ok,
        })
        if not ok:
            result["passed"] = False
            result["missing"].append("使用了常见弱密码")

    return result


def parse_policy(policy_str: str) -> Dict:
    """解析策略字符串"""
    policy = {}
    if not policy_str:
        return policy

    for item in policy_str.split(","):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "min-length":
                policy["min_length"] = int(value)
            elif key == "max-length":
                policy["max_length"] = int(value)
        else:
            key = item.lower()
            if key == "require-upper":
                policy["require_upper"] = True
            elif key == "require-lower":
                policy["require_lower"] = True
            elif key == "require-number" or key == "require-digits":
                policy["require_digits"] = True
            elif key == "require-symbol" or key == "require-symbols":
                policy["require_symbols"] = True
            elif key == "forbid-common":
                policy["forbid_common"] = True

    return policy


# ============================================================
# 输出格式化
# ============================================================

def format_generation(password: str, pwd_type: str, strength: Dict) -> str:
    """格式化生成结果"""
    lines = []
    lines.append("🔐 密码生成结果")
    lines.append("━" * 40)
    lines.append(f"密码：{password}")
    lines.append(f"类型：{pwd_type}")
    lines.append(f"长度：{strength['length']} 位")
    lines.append(f"熵值：{strength['entropy']:.1f} bits")
    lines.append(f"强度：{strength['level_icon']} {strength['level']}")

    charset_parts = []
    if strength["has_upper"]:
        charset_parts.append("大写")
    if strength["has_lower"]:
        charset_parts.append("小写")
    if strength["has_digits"]:
        charset_parts.append("数字")
    if strength["has_symbols"]:
        charset_parts.append("符号")
    lines.append(f"字符集：{'+'.join(charset_parts) if charset_parts else '无'}")

    if strength["patterns"]:
        lines.append("")
        lines.append("⚠️  检测到弱模式：")
        for p in strength["patterns"]:
            lines.append(f"  - {p}")

    lines.append("")
    lines.append("⚠️  安全提示：")
    lines.append("  - 请妥善保管，不要明文分享")
    lines.append("  - 建议使用密码管理器存储")
    lines.append("  - 不同账号使用不同密码")
    lines.append("━" * 40)
    return "\n".join(lines)


def format_strength(strength: Dict) -> str:
    """格式化强度评估"""
    lines = []
    lines.append("🔍 密码强度评估")
    lines.append("━" * 40)
    lines.append(f"密码：{'•' * min(len(strength['password']), 20)}（已隐藏）")
    lines.append(f"长度：{strength['length']} 位")
    lines.append(f"熵值：{strength['entropy']:.1f} bits")
    lines.append(f"强度：{strength['level_icon']} {strength['level']}")
    lines.append("")

    lines.append("📊 详细分析：")
    lines.append(f"  {'✅' if strength['has_upper'] else '❌'} 包含大写字母")
    lines.append(f"  {'✅' if strength['has_lower'] else '❌'} 包含小写字母")
    lines.append(f"  {'✅' if strength['has_digits'] else '❌'} 包含数字")
    lines.append(f"  {'✅' if strength['has_symbols'] else '❌'} 包含特殊符号")

    if strength["is_common"]:
        lines.append(f"  ❌ 常见弱密码（已命中）")

    if strength["patterns"]:
        lines.append("")
        lines.append("⚠️  弱模式：")
        for p in strength["patterns"]:
            lines.append(f"  - {p}")

    if strength["suggestions"]:
        lines.append("")
        lines.append("💡 改进建议：")
        for i, s in enumerate(strength["suggestions"], 1):
            lines.append(f"  {i}. {s}")

    lines.append("━" * 40)
    return "\n".join(lines)


def format_policy_check(result: Dict) -> str:
    """格式化策略检查结果"""
    lines = []
    lines.append("📋 策略合规检查")
    lines.append("━" * 40)
    lines.append(f"密码：{'•' * min(len(result['password']), 20)}（已隐藏）")
    lines.append("")

    lines.append("策略要求：")
    for check in result["checks"]:
        icon = "✅" if check["passed"] else "❌"
        lines.append(f"  {icon} {check['item']}（当前：{check['actual']}）")

    lines.append("")
    if result["passed"]:
        lines.append("✅ 结果：符合策略要求")
    else:
        lines.append("❌ 结果：不符合策略")
        lines.append("缺失项：")
        for m in result["missing"]:
            lines.append(f"  - {m}")

    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="密码生成与强度检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--type", choices=["random", "passphrase", "pin"],
                        default="random", help="密码类型（默认 random）")
    parser.add_argument("--length", "-l", type=int, default=16,
                        help="密码长度（默认 16，PIN 默认 6）")
    parser.add_argument("--words", "-w", type=int, default=4,
                        help="口令单词数量（默认 4，仅 passphrase 类型）")
    parser.add_argument("--separator", "-s", default="-",
                        help="口令分隔符（默认 -，仅 passphrase 类型）")
    parser.add_argument("--no-upper", action="store_true", help="不包含大写字母")
    parser.add_argument("--no-lower", action="store_true", help="不包含小写字母")
    parser.add_argument("--no-digits", action="store_true", help="不包含数字")
    parser.add_argument("--no-symbols", action="store_true", help="不包含特殊符号")
    parser.add_argument("--no-ambiguous", action="store_true", help="排除易混淆字符（0/O/1/l等）")
    parser.add_argument("--no-capitalize", action="store_true",
                        help="口令单词不大写（仅 passphrase 类型）")
    parser.add_argument("--no-repeats", action="store_true",
                        help="PIN 码不允许重复数字（仅 pin 类型）")
    parser.add_argument("--no-sequences", action="store_true",
                        help="PIN 码不允许连续数字（仅 pin 类型）")
    parser.add_argument("--count", "-n", type=int, default=1,
                        help="生成数量（默认 1）")
    parser.add_argument("--check", "-c", metavar="PASSWORD",
                        help="检查指定密码的强度")
    parser.add_argument("--policy", metavar="POLICY",
                        help="策略检查，如 min-length=12,require-upper,require-number")
    parser.add_argument("--output", "-o", metavar="FILE",
                        help="输出到文件")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="仅输出密码（批量生成时使用）")
    args = parser.parse_args()

    output_lines = []

    # 检查模式
    if args.check:
        strength = evaluate_strength(args.check)
        if args.policy:
            policy = parse_policy(args.policy)
            policy_result = check_policy(args.check, policy)
            output_lines.append(format_strength(strength))
            output_lines.append("")
            output_lines.append(format_policy_check(policy_result))
        else:
            output_lines.append(format_strength(strength))
    else:
        # 生成模式
        if args.count < 1:
            print("错误：生成数量至少为 1", file=sys.stderr)
            sys.exit(1)

        passwords = []
        for _ in range(args.count):
            if args.type == "random":
                pwd = generate_random_password(
                    length=args.length,
                    use_upper=not args.no_upper,
                    use_lower=not args.no_lower,
                    use_digits=not args.no_digits,
                    use_symbols=not args.no_symbols,
                    no_ambiguous=args.no_ambiguous,
                )
                pwd_type = "随机密码"
            elif args.type == "passphrase":
                pwd = generate_passphrase(
                    words=args.words,
                    separator=args.separator,
                    capitalize=not args.no_capitalize,
                )
                pwd_type = "易记口令"
            else:  # pin
                pin_length = args.length if args.length != 16 else 6
                pwd = generate_pin(
                    length=pin_length,
                    allow_repeats=not args.no_repeats,
                    allow_sequences=not args.no_sequences,
                )
                pwd_type = "PIN 码"

            passwords.append((pwd, pwd_type))

        if args.quiet or args.count > 1:
            # 批量模式：简洁输出
            for pwd, pwd_type in passwords:
                strength = evaluate_strength(pwd)
                output_lines.append(f"{pwd}  [{strength['level_icon']} {strength['level']}, {strength['entropy']:.0f}bits]")
        else:
            # 单个模式：详细输出
            pwd, pwd_type = passwords[0]
            strength = evaluate_strength(pwd)
            output_lines.append(format_generation(pwd, pwd_type, strength))

    # 输出
    result_text = "\n".join(output_lines)
    print(result_text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result_text + "\n")
        print(f"\n已保存到：{args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
