#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
配色方案生成脚本

功能：
- 解析颜色输入（HEX/RGB/HSL）
- 颜色格式互转（HEX/RGB/HSL/HSV）
- 生成 6 种配色方案（互补/类比/三角色/四角色/分裂互补/单色渐变）
- WCAG 对比度计算与无障碍合规检查
- 生成 CSS 变量和 Tailwind 配置
- 终端可视化预览（ANSI 真彩色）
- 保存/加载配色方案（JSON）

用法：
  python3 generate_palette.py --color "#3498DB"
  python3 generate_palette.py --color "rgb(52,152,219)"
  python3 generate_palette.py --color "hsl(204,70%,53%)"
  python3 generate_palette.py --color "#3498DB" --scheme complementary,triadic
  python3 generate_palette.py --color "#3498DB" --convert
  python3 generate_palette.py --color "#FFFFFF" --contrast "#3498DB"
  python3 generate_palette.py --color "#3498DB" --format css
  python3 generate_palette.py --color "#3498DB" --format tailwind
  python3 generate_palette.py --color "#3498DB" --save palette.json
  python3 generate_palette.py --load palette.json
  python3 generate_palette.py --color "#3498DB" --format json
"""

import argparse
import json
import math
import os
import re
import sys
from typing import Dict, List, Optional, Tuple


# ============================================================
# 颜色解析
# ============================================================

def parse_color(color_str: str) -> Tuple[int, int, int]:
    """解析颜色字符串，返回 (R, G, B)"""
    s = color_str.strip()

    # HEX 格式: #RRGGBB 或 #RGB
    hex_match = re.match(r'^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', s)
    if hex_match:
        hex_val = hex_match.group(1)
        if len(hex_val) == 3:
            hex_val = ''.join(c * 2 for c in hex_val)
        return (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))

    # RGB 格式: rgb(r, g, b)
    rgb_match = re.match(r'^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', s, re.IGNORECASE)
    if rgb_match:
        r = max(0, min(255, int(rgb_match.group(1))))
        g = max(0, min(255, int(rgb_match.group(2))))
        b = max(0, min(255, int(rgb_match.group(3))))
        return (r, g, b)

    # HSL 格式: hsl(h, s%, l%)
    hsl_match = re.match(r'^hsla?\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*%?\s*,\s*(\d+(?:\.\d+)?)\s*%?', s, re.IGNORECASE)
    if hsl_match:
        h = float(hsl_match.group(1)) % 360
        s_pct = float(hsl_match.group(2)) / 100.0
        l_pct = float(hsl_match.group(3)) / 100.0
        return hsl_to_rgb(h, s_pct, l_pct)

    raise ValueError(f"无法解析颜色：{color_str}。支持格式：#RRGGBB, rgb(r,g,b), hsl(h,s%,l%)")


# ============================================================
# 颜色格式转换
# ============================================================

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB 转 HEX"""
    return f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """RGB 转 HSL，返回 (H[0-360], S[0-1], L[0-1])"""
    r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r_f, g_f, b_f)
    min_val = min(r_f, g_f, b_f)
    h, s, l = 0, 0, (max_val + min_val) / 2

    if max_val != min_val:
        d = max_val - min_val
        s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
        if max_val == r_f:
            h = (g_f - b_f) / d + (6 if g_f < b_f else 0)
        elif max_val == g_f:
            h = (b_f - r_f) / d + 2
        else:
            h = (r_f - g_f) / d + 4
        h /= 6

    return (h * 360, s, l)


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """HSL 转 RGB"""
    h = h % 360
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2

    if h < 60:
        r1, g1, b1 = c, x, 0
    elif h < 120:
        r1, g1, b1 = x, c, 0
    elif h < 180:
        r1, g1, b1 = 0, c, x
    elif h < 240:
        r1, g1, b1 = 0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x

    return (
        int(round((r1 + m) * 255)),
        int(round((g1 + m) * 255)),
        int(round((b1 + m) * 255)),
    )


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """RGB 转 HSV，返回 (H[0-360], S[0-1], V[0-1])"""
    r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r_f, g_f, b_f)
    min_val = min(r_f, g_f, b_f)
    d = max_val - min_val
    h = 0
    s = 0 if max_val == 0 else d / max_val
    v = max_val

    if d != 0:
        if max_val == r_f:
            h = ((g_f - b_f) / d) % 6
        elif max_val == g_f:
            h = (b_f - r_f) / d + 2
        else:
            h = (r_f - g_f) / d + 4
        h *= 60

    return (h, s, v)


def format_color_info(r: int, g: int, b: int) -> Dict:
    """格式化颜色信息"""
    h, s, l = rgb_to_hsl(r, g, b)
    hv, sv, vv = rgb_to_hsv(r, g, b)
    return {
        "hex": rgb_to_hex(r, g, b),
        "rgb": f"rgb({r},{g},{b})",
        "hsl": f"hsl({h:.0f},{s*100:.0f}%,{l*100:.0f}%)",
        "hsv": f"hsv({hv:.0f},{sv*100:.0f}%,{vv*100:.0f}%)",
        "r": r, "g": g, "b": b,
        "h": h, "s": s, "l": l,
    }


# ============================================================
# 配色方案生成
# ============================================================

def generate_complementary(r: int, g: int, b: int) -> List[Tuple[int, int, int]]:
    """互补色：基础色 + 180° 对面色"""
    h, s, l = rgb_to_hsl(r, g, b)
    h2 = (h + 180) % 360
    return [(r, g, b), hsl_to_rgb(h2, s, l)]


def generate_analogous(r: int, g: int, b: int) -> List[Tuple[int, int, int]]:
    """类比色：基础色 ± 30° 相邻色"""
    h, s, l = rgb_to_hsl(r, g, b)
    return [
        hsl_to_rgb((h - 30) % 360, s, l),
        (r, g, b),
        hsl_to_rgb((h + 30) % 360, s, l),
    ]


def generate_triadic(r: int, g: int, b: int) -> List[Tuple[int, int, int]]:
    """三角色：等距 120°"""
    h, s, l = rgb_to_hsl(r, g, b)
    return [
        (r, g, b),
        hsl_to_rgb((h + 120) % 360, s, l),
        hsl_to_rgb((h + 240) % 360, s, l),
    ]


def generate_tetradic(r: int, g: int, b: int) -> List[Tuple[int, int, int]]:
    """四角色：等距 90°"""
    h, s, l = rgb_to_hsl(r, g, b)
    return [
        (r, g, b),
        hsl_to_rgb((h + 90) % 360, s, l),
        hsl_to_rgb((h + 180) % 360, s, l),
        hsl_to_rgb((h + 270) % 360, s, l),
    ]


def generate_split_complementary(r: int, g: int, b: int) -> List[Tuple[int, int, int]]:
    """分裂互补：基础色 + 互补色 ± 30°"""
    h, s, l = rgb_to_hsl(r, g, b)
    return [
        (r, g, b),
        hsl_to_rgb((h + 150) % 360, s, l),
        hsl_to_rgb((h + 210) % 360, s, l),
    ]


def generate_monochromatic(r: int, g: int, b: int) -> List[Tuple[int, int, int]]:
    """单色渐变：同一色相的 5 个明度阶梯"""
    h, s, _ = rgb_to_hsl(r, g, b)
    lightnesses = [0.20, 0.35, 0.50, 0.65, 0.80]
    return [hsl_to_rgb(h, s, l) for l in lightnesses]


SCHEME_GENERATORS = {
    "complementary": ("互补色", generate_complementary),
    "analogous": ("类比色", generate_analogous),
    "triadic": ("三角色", generate_triadic),
    "tetradic": ("四角色", generate_tetradic),
    "split-complementary": ("分裂互补", generate_split_complementary),
    "monochromatic": ("单色渐变", generate_monochromatic),
}


# ============================================================
# WCAG 对比度计算
# ============================================================

def relative_luminance(r: int, g: int, b: int) -> float:
    """计算相对亮度（WCAG 2.1）"""
    def channel(c: int) -> float:
        c_srgb = c / 255.0
        return c_srgb / 12.92 if c_srgb <= 0.03928 else ((c_srgb + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """计算两个颜色的对比度比率"""
    l1 = relative_luminance(*color1)
    l2 = relative_luminance(*color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_accessibility(ratio: float) -> Dict[str, bool]:
    """检查无障碍合规性"""
    return {
        "aa_large": ratio >= 3.0,
        "aa_normal": ratio >= 4.5,
        "aaa_large": ratio >= 4.5,
        "aaa_normal": ratio >= 7.0,
    }


def suggest_improvement(fg: Tuple[int, int, int], bg: Tuple[int, int, int],
                         target: float = 4.5) -> Optional[Tuple[int, int, int]]:
    """建议调整背景色以达到目标对比度"""
    # 尝试加深或变亮背景色
    h, s, l = rgb_to_hsl(*bg)
    best = None
    best_ratio = contrast_ratio(fg, bg)

    # 尝试调整明度
    for delta in range(5, 50, 5):
        for direction in [-1, 1]:
            new_l = max(0.05, min(0.95, l + direction * delta / 100.0))
            new_bg = hsl_to_rgb(h, s, new_l)
            r = contrast_ratio(fg, new_bg)
            if r >= target and (best is None or abs(new_l - l) < abs(rgb_to_hsl(*best)[2] - l)):
                best = new_bg
                best_ratio = r

    return best


# ============================================================
# 输出生成
# ============================================================

def ansi_color_block(r: int, g: int, b: int, width: int = 8) -> str:
    """生成 ANSI 真彩色背景块"""
    return f"\033[48;2;{r};{g};{b}m{' ' * width}\033[0m"


def format_palette(r: int, g: int, b: int, schemes: Optional[List[str]] = None) -> str:
    """格式化配色方案输出"""
    lines = []
    info = format_color_info(r, g, b)

    lines.append("🎨 配色方案生成")
    lines.append("━" * 50)
    lines.append(f"基础颜色：{info['hex']}")
    lines.append(f"  RGB: {info['rgb']}")
    lines.append(f"  HSL: {info['hsl']}")
    lines.append(f"  HSV: {info['hsv']}")
    lines.append("")

    scheme_list = schemes if schemes else list(SCHEME_GENERATORS.keys())

    for scheme_key in scheme_list:
        if scheme_key not in SCHEME_GENERATORS:
            continue
        name, generator = SCHEME_GENERATORS[scheme_key]
        colors = generator(r, g, b)

        lines.append(f"【{name} {scheme_key.capitalize()}】")
        for i, (cr, cg, cb) in enumerate(colors):
            ci = format_color_info(cr, cg, cb)
            label = "主色" if i == 0 else f"{scheme_key}-{i}"
            block = ansi_color_block(cr, cg, cb)
            lines.append(f"  {ci['hex']}  {block}  {label}")
        lines.append("")

    lines.append("━" * 50)
    return "\n".join(lines)


def format_conversion(r: int, g: int, b: int) -> str:
    """格式化颜色转换输出"""
    info = format_color_info(r, g, b)
    lines = []
    lines.append("🔄 颜色格式转换")
    lines.append("━" * 50)
    lines.append(f"  HEX: {info['hex']}")
    lines.append(f"  RGB: {info['rgb']}")
    lines.append(f"  HSL: {info['hsl']}")
    lines.append(f"  HSV: {info['hsv']}")
    lines.append("")
    lines.append(f"  R = {info['r']}, G = {info['g']}, B = {info['b']}")
    lines.append(f"  H = {info['h']:.1f}°, S = {info['s']*100:.1f}%, L = {info['l']*100:.1f}%")
    lines.append("━" * 50)
    return "\n".join(lines)


def format_contrast(fg: Tuple[int, int, int], bg: Tuple[int, int, int]) -> str:
    """格式化对比度检查输出"""
    fg_info = format_color_info(*fg)
    bg_info = format_color_info(*bg)
    ratio = contrast_ratio(fg, bg)
    acc = check_accessibility(ratio)

    lines = []
    lines.append("📊 对比度检查")
    lines.append("━" * 50)
    lines.append(f"前景色：{fg_info['hex']} {ansi_color_block(*fg)}")
    lines.append(f"背景色：{bg_info['hex']} {ansi_color_block(*bg)}")
    lines.append("")
    lines.append(f"对比度比率：{ratio:.2f} : 1")
    lines.append("")
    lines.append("无障碍合规性（WCAG 2.1）：")
    lines.append(f"  {'✅' if acc['aa_large'] else '❌'} AA 大文本：{'通过' if acc['aa_large'] else '未通过'} (需要 ≥ 3:1)")
    lines.append(f"  {'✅' if acc['aa_normal'] else '❌'} AA 普通文本：{'通过' if acc['aa_normal'] else '未通过'} (需要 ≥ 4.5:1)")
    lines.append(f"  {'✅' if acc['aaa_large'] else '❌'} AAA 大文本：{'通过' if acc['aaa_large'] else '未通过'} (需要 ≥ 4.5:1)")
    lines.append(f"  {'✅' if acc['aaa_normal'] else '❌'} AAA 普通文本：{'通过' if acc['aaa_normal'] else '未通过'} (需要 ≥ 7:1)")
    lines.append("")

    if not acc['aa_normal']:
        suggestion = suggest_improvement(fg, bg, 4.5)
        if suggestion:
            si = format_color_info(*suggestion)
            new_ratio = contrast_ratio(fg, suggestion)
            lines.append("💡 改进建议：")
            lines.append(f"  将背景色调整为 {si['hex']} {ansi_color_block(*suggestion)}")
            lines.append(f"  新对比度：{new_ratio:.2f} : 1（通过 AA 普通文本）")
            lines.append("")

    lines.append("━" * 50)
    return "\n".join(lines)


def generate_css(r: int, g: int, b: int) -> str:
    """生成 CSS 变量"""
    info = format_color_info(r, g, b)
    h, s, l = rgb_to_hsl(r, g, b)
    comp = generate_complementary(r, g, b)[1]
    comp_info = format_color_info(*comp)
    light = hsl_to_rgb(h, s, min(0.85, l + 0.15))
    dark = hsl_to_rgb(h, s, max(0.15, l - 0.15))
    light_info = format_color_info(*light)
    dark_info = format_color_info(*dark)

    return f""":root {{
  /* 主色 */
  --color-primary: {info['hex']};
  --color-primary-light: {light_info['hex']};
  --color-primary-dark: {dark_info['hex']};

  /* 互补色 */
  --color-complementary: {comp_info['hex']};

  /* 中性色 */
  --color-bg: #F8F9FA;
  --color-surface: #FFFFFF;
  --color-text: #2C3E50;
  --color-text-muted: #7F8C8D;
  --color-border: #E9ECEF;

  /* 语义色 */
  --color-success: #28A745;
  --color-warning: #FFC107;
  --color-danger: #DC3545;
  --color-info: {info['hex']};
}}"""


def generate_tailwind(r: int, g: int, b: int) -> str:
    """生成 Tailwind 配色配置（50-900 色阶）"""
    h, s, _ = rgb_to_hsl(r, g, b)
    shades = [
        (50, 0.95), (100, 0.88), (200, 0.78), (300, 0.68),
        (400, 0.58), (500, 0.50), (600, 0.42), (700, 0.34),
        (800, 0.26), (900, 0.18),
    ]

    lines = ["module.exports = {", "  theme: {", "    extend: {", "      colors: {", "        primary: {"]
    for level, lightness in shades:
        color = hsl_to_rgb(h, s, lightness)
        hex_val = rgb_to_hex(*color)
        lines.append(f"          {level}: '{hex_val}',")
    lines.append("        },")
    lines.append("      },")
    lines.append("    },")
    lines.append("  },")
    lines.append("}")
    return "\n".join(lines)


def palette_to_dict(r: int, g: int, b: int) -> Dict:
    """将配色方案转为字典"""
    result = {"base": format_color_info(r, g, b), "schemes": {}}
    for key, (name, generator) in SCHEME_GENERATORS.items():
        colors = generator(r, g, b)
        result["schemes"][key] = {
            "name": name,
            "colors": [format_color_info(*c) for c in colors],
        }
    return result


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="配色方案生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--color", "-c", help="基础颜色（HEX/RGB/HSL 格式）")
    parser.add_argument("--scheme", "-s", default="",
                        help="配色方案类型（逗号分隔）：complementary,analogous,triadic,tetradic,split-complementary,monochromatic")
    parser.add_argument("--convert", action="store_true", help="颜色格式转换")
    parser.add_argument("--contrast", metavar="BG_COLOR", help="对比度检查（背景色）")
    parser.add_argument("--format", "-f", choices=["text", "css", "tailwind", "json"],
                        default="text", help="输出格式")
    parser.add_argument("--save", metavar="FILE", help="保存配色方案到 JSON 文件")
    parser.add_argument("--load", metavar="FILE", help="从 JSON 文件加载配色方案")
    args = parser.parse_args()

    # 加载模式
    if args.load:
        if not os.path.exists(args.load):
            print(f"错误：文件不存在：{args.load}", file=sys.stderr)
            sys.exit(1)
        with open(args.load, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if not args.color:
        print("错误：请使用 --color 指定基础颜色", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # 解析颜色
    try:
        r, g, b = parse_color(args.color)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    # 对比度检查
    if args.contrast:
        try:
            bg_r, bg_g, bg_b = parse_color(args.contrast)
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
        output = format_contrast((r, g, b), (bg_r, bg_g, bg_b))
        print(output)
        return

    # 颜色格式转换
    if args.convert:
        print(format_conversion(r, g, b))
        return

    # 解析方案类型
    schemes = None
    if args.scheme:
        schemes = [s.strip() for s in args.scheme.split(",") if s.strip()]

    # 输出格式
    if args.format == "css":
        print(generate_css(r, g, b))
    elif args.format == "tailwind":
        print(generate_tailwind(r, g, b))
    elif args.format == "json":
        print(json.dumps(palette_to_dict(r, g, b), ensure_ascii=False, indent=2))
    else:
        print(format_palette(r, g, b, schemes))

    # 保存
    if args.save:
        data = palette_to_dict(r, g, b)
        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n已保存到：{args.save}", file=sys.stderr)


if __name__ == "__main__":
    main()
