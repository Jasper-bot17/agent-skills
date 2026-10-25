#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Base64 编解码助手

支持文本编解码（标准/URL-safe）、文件编解码、批量模式、随机生成、JSON 输出。
基于 Python 标准库实现。

用法：
  python3 b64_tool.py encode "Hello World"
  python3 b64_tool.py decode "SGVsbG8="
  python3 b64_tool.py encode "text" --url-safe
  python3 b64_tool.py encode --file input.txt
  python3 b64_tool.py encode-file image.png
  python3 b64_tool.py decode-file <b64> --output out.png
  python3 b64_tool.py random 16
  python3 b64_tool.py encode "a" "b" "c"
"""

import argparse
import base64
import json
import os
import sys


# ============================================================
# 核心编解码函数
# ============================================================

def encode(text, url_safe=False):
    """文本编码为 Base64"""
    data = text.encode("utf-8")
    if url_safe:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    return base64.b64encode(data).decode("ascii")


def decode(b64_str, url_safe=False):
    """Base64 解码为文本"""
    b64_str = b64_str.strip()
    if url_safe:
        # 自动补 padding
        padding = 4 - len(b64_str) % 4
        if padding != 4:
            b64_str += "=" * padding
        data = base64.urlsafe_b64decode(b64_str)
    else:
        data = base64.b64decode(b64_str)
    return data.decode("utf-8")


def encode_file(filepath, url_safe=False):
    """文件编码为 Base64"""
    with open(filepath, "rb") as f:
        data = f.read()
    if url_safe:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    return base64.b64encode(data).decode("ascii")


def decode_file(b64_str, output_path, url_safe=False):
    """Base64 解码并保存为文件"""
    b64_str = b64_str.strip()
    if url_safe:
        padding = 4 - len(b64_str) % 4
        if padding != 4:
            b64_str += "=" * padding
        data = base64.urlsafe_b64decode(b64_str)
    else:
        data = base64.b64decode(b64_str)
    with open(output_path, "wb") as f:
        f.write(data)
    return len(data)


def random_b64(nbytes, url_safe=False):
    """生成 nbytes 随机字节的 Base64 字符串"""
    data = os.urandom(nbytes)
    if url_safe:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    return base64.b64encode(data).decode("ascii")


def analyze_padding(b64_str):
    """分析 Base64 字符串的 padding 状态"""
    b64_str = b64_str.strip()
    padding_count = b64_str.count("=")
    # 原始字节数 = (长度 - padding) * 6 / 8
    effective_len = len(b64_str) - padding_count
    byte_len = effective_len * 6 // 8
    has_url_safe = "-" in b64_str or "_" in b64_str
    return {
        "length": len(b64_str),
        "padding_count": padding_count,
        "has_padding": padding_count > 0,
        "is_url_safe": has_url_safe,
        "decoded_byte_length": byte_len,
    }


# ============================================================
# 输出格式化
# ============================================================

def print_result(label, value, detail=None, as_json=False):
    if as_json:
        output = {"result": value}
        if detail:
            output.update(detail)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  结果: {value}")
    if detail:
        for k, v in detail.items():
            print(f"  {k}: {v}")
    print()


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Base64 编解码助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s encode "Hello World"
  %(prog)s decode "SGVsbG8gV29ybGQ="
  %(prog)s encode "Hello" --url-safe
  %(prog)s encode --file input.txt
  %(prog)s encode-file image.png
  %(prog)s decode-file <b64> --output out.png
  %(prog)s random 16
  %(prog)s encode "a" "b" "c"
        """,
    )

    # 位置参数：操作 + 输入
    parser.add_argument("action", choices=[
        "encode", "decode", "encode-file", "decode-file",
        "random", "analyze",
    ], help="操作类型")
    parser.add_argument("inputs", nargs="*", help="输入字符串（可多个）")

    # 可选参数
    parser.add_argument("--file", help="从文件读取输入文本")
    parser.add_argument("--output", "-o", help="解码文件时的输出路径")
    parser.add_argument("--url-safe", action="store_true", help="使用 URL-safe Base64 变体")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--data-url", action="store_true", help="文件编码时生成 Data URL")

    args = parser.parse_args()

    # ---- 编码 ----
    if args.action == "encode":
        texts = list(args.inputs)
        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    texts.append(f.read())
            except IOError as e:
                print(f"❌ 读取文件失败: {e}", file=sys.stderr)
                sys.exit(1)

        if not texts:
            parser.print_help()
            sys.exit(1)

        for i, text in enumerate(texts):
            result = encode(text, url_safe=args.url_safe)
            detail = {
                "输入长度": f"{len(text)} 字符 / {len(text.encode('utf-8'))} 字节",
                "编码长度": f"{len(result)} 字符",
                "变体": "URL-safe" if args.url_safe else "标准",
            }
            print_result(f"编码结果 ({i+1}/{len(texts)})", result, detail, as_json=args.json)

    # ---- 解码 ----
    elif args.action == "decode":
        b64_strs = list(args.inputs)
        if args.file:
            try:
                with open(args.file, "r") as f:
                    b64_strs.append(f.read().strip())
            except IOError as e:
                print(f"❌ 读取文件失败: {e}", file=sys.stderr)
                sys.exit(1)

        if not b64_strs:
            parser.print_help()
            sys.exit(1)

        for i, b64_str in enumerate(b64_strs):
            try:
                result = decode(b64_str, url_safe=args.url_safe)
                detail = {
                    "输入长度": f"{len(b64_str)} 字符",
                    "输出长度": f"{len(result)} 字符 / {len(result.encode('utf-8'))} 字节",
                    "变体": "URL-safe" if args.url_safe else "标准",
                }
                print_result(f"解码结果 ({i+1}/{len(b64_strs)})", result, detail, as_json=args.json)
            except Exception as e:
                print(f"❌ 解码失败: {e}", file=sys.stderr)

    # ---- 文件编码 ----
    elif args.action == "encode-file":
        if not args.inputs:
            print("❌ 请指定文件路径", file=sys.stderr)
            sys.exit(1)

        filepath = args.inputs[0]
        if not os.path.isfile(filepath):
            print(f"❌ 文件不存在: {filepath}", file=sys.stderr)
            sys.exit(1)

        b64_result = encode_file(filepath, url_safe=args.url_safe)
        file_size = os.path.getsize(filepath)

        if args.data_url:
            # 推断 MIME 类型
            ext = os.path.splitext(filepath)[1].lower()
            mime_map = {
                ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
                ".pdf": "application/pdf", ".txt": "text/plain", ".json": "application/json",
                ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
            }
            mime = mime_map.get(ext, "application/octet-stream")
            result = f"data:{mime};base64,{b64_result}"
        else:
            result = b64_result

        detail = {
            "文件": filepath,
            "原始大小": f"{file_size} 字节 ({file_size/1024:.1f} KB)",
            "Base64 长度": f"{len(b64_result)} 字符 ({len(b64_result)/1024:.1f} KB)",
            "膨胀率": f"{len(b64_result)/file_size*100:.1f}%",
        }
        print_result("文件编码结果", result, detail, as_json=args.json)

    # ---- 文件解码 ----
    elif args.action == "decode-file":
        if not args.inputs:
            print("❌ 请提供 Base64 字符串", file=sys.stderr)
            sys.exit(1)
        if not args.output:
            print("❌ 请用 --output 指定输出路径", file=sys.stderr)
            sys.exit(1)

        b64_str = args.inputs[0]
        try:
            byte_len = decode_file(b64_str, args.output, url_safe=args.url_safe)
            detail = {
                "输出文件": args.output,
                "文件大小": f"{byte_len} 字节 ({byte_len/1024:.1f} KB)",
            }
            print_result("文件解码结果", f"已保存到 {args.output}", detail, as_json=args.json)
        except Exception as e:
            print(f"❌ 解码失败: {e}", file=sys.stderr)
            sys.exit(1)

    # ---- 随机生成 ----
    elif args.action == "random":
        if not args.inputs:
            print("❌ 请指定字节数，如: random 16", file=sys.stderr)
            sys.exit(1)

        try:
            nbytes = int(args.inputs[0])
        except ValueError:
            print(f"❌ 无效的字节数: {args.inputs[0]}", file=sys.stderr)
            sys.exit(1)

        if nbytes < 1 or nbytes > 1024:
            print("❌ 字节数应在 1~1024 之间", file=sys.stderr)
            sys.exit(1)

        result = random_b64(nbytes, url_safe=args.url_safe)
        detail = {
            "随机字节数": nbytes,
            "Base64 长度": f"{len(result)} 字符",
            "变体": "URL-safe" if args.url_safe else "标准",
        }
        print_result("随机 Base64", result, detail, as_json=args.json)

    # ---- Padding 分析 ----
    elif args.action == "analyze":
        if not args.inputs:
            print("❌ 请提供 Base64 字符串", file=sys.stderr)
            sys.exit(1)

        for i, b64_str in enumerate(args.inputs):
            info = analyze_padding(b64_str)
            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                print(f"{'='*60}")
                print(f"  Padding 分析 ({i+1}/{len(args.inputs)})")
                print(f"{'='*60}")
                print(f"  字符串: {b64_str[:60]}{'...' if len(b64_str)>60 else ''}")
                print(f"  总长度: {info['length']} 字符")
                print(f"  Padding: {'有' if info['has_padding'] else '无'} ({info['padding_count']} 个 =)")
                print(f"  变体: {'URL-safe' if info['is_url_safe'] else '标准'}")
                print(f"  解码后字节数: {info['decoded_byte_length']} 字节")
                print()


if __name__ == "__main__":
    main()
