#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
JWT 解码器与生成器

支持 JWT 解码、过期状态判断、声明释义、HS256 生成、批量解码、JSON 输出。
基于 Python 标准库实现。

用法：
  python3 jwt_tool.py <token>
  python3 jwt_tool.py <token1> <token2>
  python3 jwt_tool.py --file token.txt
  python3 jwt_tool.py <token> --json
  python3 jwt_tool.py --generate --secret mysecret --sub 123 --exp 3600
"""

import argparse
import base64
import hashlib
import hmac
import json
import sys
import time


# ============================================================
# 标准声明中文释义
# ============================================================

CLAIM_DESCRIPTIONS = {
    "iss": "签发者（Issuer）：Token 的签发方",
    "sub": "主题（Subject）：Token 所属用户标识",
    "aud": "受众（Audience）：Token 的接收方（哪些应用可用）",
    "exp": "过期时间（Expiration Time）：Unix 时间戳，过期后 Token 无效",
    "nbf": "生效时间（Not Before）：Unix 时间戳，此前 Token 不可用",
    "iat": "签发时间（Issued At）：Unix 时间戳，Token 何时签发",
    "jti": "唯一 ID（JWT ID）：Token 的唯一标识，用于防重放",
    "typ": "类型（Type）：通常为 JWT",
    "alg": "算法（Algorithm）：签名算法（HS256/RS256 等）",
}


# ============================================================
# Base64Url 编解码
# ============================================================

def b64url_decode(data):
    """Base64Url 解码（自动补 padding）"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def b64url_encode(data):
    """Base64Url 编码（去除 padding）"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


# ============================================================
# JWT 解码
# ============================================================

def decode_jwt(token):
    """解码 JWT，返回结果字典"""
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None, f"JWT 格式错误：应有 3 段（Header.Payload.Signature），实际 {len(parts)} 段"

    header_b64, payload_b64, signature_b64 = parts

    # 解码 Header
    try:
        header_raw = b64url_decode(header_b64)
        header = json.loads(header_raw)
    except Exception as e:
        return None, f"Header 解码失败：{e}"

    # 解码 Payload
    try:
        payload_raw = b64url_decode(payload_b64)
        payload = json.loads(payload_raw)
    except Exception as e:
        return None, f"Payload 解码失败：{e}"

    # 时间判断
    now = time.time()
    status = "有效"
    status_detail = ""

    exp = payload.get("exp")
    nbf = payload.get("nbf")
    iat = payload.get("iat")

    if nbf and now < nbf:
        status = "未生效"
        remaining = nbf - now
        status_detail = f"将在 {format_timestamp(nbf)} 生效（{format_duration(remaining)} 后）"
    elif exp and now > exp:
        status = "已过期"
        expired = now - exp
        status_detail = f"已于 {format_timestamp(exp)} 过期（{format_duration(expired)} 前）"
    elif exp:
        remaining = exp - now
        status_detail = f"将在 {format_timestamp(exp)} 过期（剩余 {format_duration(remaining)}）"

    return {
        "header": header,
        "payload": payload,
        "signature_b64": signature_b64,
        "signature_length": len(b64url_decode(signature_b64)) if signature_b64 else 0,
        "alg": header.get("alg", "未知"),
        "status": status,
        "status_detail": status_detail,
        "now": int(now),
        "is_expired": bool(exp and now > exp),
        "is_not_yet_valid": bool(nbf and now < nbf),
    }, None


# ============================================================
# JWT 生成（HS256）
# ============================================================

def generate_jwt(claims, secret, expires_in=None, issued_at=None):
    """生成 HS256 JWT"""
    if issued_at is None:
        issued_at = int(time.time())

    header = {"alg": "HS256", "typ": "JWT"}

    payload = dict(claims)
    payload["iat"] = issued_at
    if expires_in is not None:
        payload["exp"] = issued_at + int(expires_in)

    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())

    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(
        secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature_b64 = b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


# ============================================================
# 格式化辅助
# ============================================================

def format_timestamp(ts):
    """Unix 时间戳转可读时间"""
    if ts is None:
        return "N/A"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def format_duration(seconds):
    """秒数转可读时长"""
    seconds = int(abs(seconds))
    if seconds < 60:
        return f"{seconds} 秒"
    elif seconds < 3600:
        return f"{seconds // 60} 分 {seconds % 60} 秒"
    elif seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h} 时 {m} 分"
    else:
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        return f"{d} 天 {h} 时"


def print_decode(result, as_json=False):
    """打印解码结果"""
    if as_json:
        # JSON 输出时不包含动态状态（每次调用时间不同）
        output = {
            "header": result["header"],
            "payload": result["payload"],
            "alg": result["alg"],
            "status": result["status"],
            "signature_b64": result["signature_b64"],
            "is_expired": result["is_expired"],
            "is_not_yet_valid": result["is_not_yet_valid"],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"{'='*60}")
    print(f"  JWT 解码结果")
    print(f"{'='*60}")

    # 状态
    status_icon = {"有效": "✅", "已过期": "❌", "未生效": "⏳"}.get(result["status"], "❓")
    print(f"  状态: {status_icon} {result['status']}")
    if result["status_detail"]:
        print(f"        {result['status_detail']}")
    print()

    # Header
    print(f"  ── Header（头部）──")
    for k, v in result["header"].items():
        desc = CLAIM_DESCRIPTIONS.get(k, "")
        print(f"    {k}: {v}" + (f"  // {desc}" if desc else ""))
    print()

    # Payload
    print(f"  ── Payload（载荷）──")
    for k, v in result["payload"].items():
        desc = CLAIM_DESCRIPTIONS.get(k, "")
        # 时间戳格式化
        if k in ("exp", "nbf", "iat") and isinstance(v, (int, float)):
            v_str = f"{v} ({format_timestamp(v)})"
        else:
            v_str = str(v)
        print(f"    {k}: {v_str}" + (f"  // {desc}" if desc else ""))
    print()

    # Signature
    print(f"  ── Signature（签名）──")
    print(f"    算法: {result['alg']}")
    print(f"    签名长度: {result['signature_length']} 字节")
    print(f"    签名片段: {result['signature_b64'][:40]}...")
    print(f"    提示: 解码工具不验证签名，需密钥才能验证")
    print()


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="JWT 解码器与生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  %(prog)s --file token.txt
  %(prog)s <token1> <token2>
  %(prog)s <token> --json
  %(prog)s --generate --secret mysecret --sub 123 --name Alice --exp 3600
        """,
    )

    parser.add_argument("tokens", nargs="*", help="JWT Token（可多个）")
    parser.add_argument("--file", help="从文件读取 JWT Token")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--generate", action="store_true", help="生成测试 JWT")
    parser.add_argument("--secret", default="changeme", help="生成 JWT 时的签名密钥（默认 changeme）")
    parser.add_argument("--exp", type=int, help="生成 JWT 时的过期时间（秒）")
    parser.add_argument("--sub", help="生成 JWT 时的 subject")
    parser.add_argument("--iss", help="生成 JWT 时的 issuer")
    parser.add_argument("--aud", help="生成 JWT 时的 audience")
    parser.add_argument("--role", help="生成 JWT 时的 role 声明")
    parser.add_argument("--name", help="生成 JWT 时的 name 声明")

    args = parser.parse_args()

    # 生成模式
    if args.generate:
        claims = {}
        if args.sub:
            claims["sub"] = args.sub
        if args.iss:
            claims["iss"] = args.iss
        if args.aud:
            claims["aud"] = args.aud
        if args.role:
            claims["role"] = args.role
        if args.name:
            claims["name"] = args.name

        token = generate_jwt(claims, secret=args.secret, expires_in=args.exp)
        print(f"生成的 JWT（HS256，密钥: {args.secret}）：")
        print()
        print(token)
        print()
        # 自动解码展示
        result, err = decode_jwt(token)
        if result:
            print_decode(result, as_json=args.json)
        return

    # 收集 tokens
    tokens = list(args.tokens)
    if args.file:
        try:
            with open(args.file, "r") as f:
                content = f.read().strip()
            tokens.append(content)
        except IOError as e:
            print(f"❌ 读取文件失败: {e}", file=sys.stderr)
            sys.exit(1)

    if not tokens:
        parser.print_help()
        sys.exit(1)

    # 解码
    for i, token in enumerate(tokens):
        if i > 0:
            print()
        result, err = decode_jwt(token)
        if err:
            print(f"❌ 解码失败: {err}", file=sys.stderr)
            continue
        print_decode(result, as_json=args.json)


if __name__ == "__main__":
    main()
