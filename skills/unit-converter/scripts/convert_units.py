#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
单位换算脚本

功能：
- 支持 12 大类单位换算：长度、重量、温度、面积、体积、速度、时间、数据大小、能量、压力、功率、力
- 支持任意单位间直接换算
- 支持批量换算到该类别所有单位
- 支持精度控制（小数位数）
- 支持科学计数法显示
- 支持列出所有类别和单位
- 支持常用换算速查表

用法：
  python3 convert_units.py --value 1 --from m --to ft
  python3 convert_units.py --value 1 --from m
  python3 convert_units.py --list length
  python3 convert_units.py --categories
  python3 convert_units.py --value 100 --from C --to F --precision 2
  python3 convert_units.py --value 1 --from eV --to J --scientific
  python3 convert_units.py --cheatsheet
"""

import argparse
import sys


# ============================================================
# 单位定义：每个单位映射到基准单位的换算因子
# 温度特殊处理（非线性）
# ============================================================

UNITS = {
    "length": {
        "name": "长度",
        "base": "m",
        "units": {
            "m": {"name": "米", "factor": 1.0},
            "km": {"name": "千米", "factor": 1000.0},
            "cm": {"name": "厘米", "factor": 0.01},
            "mm": {"name": "毫米", "factor": 0.001},
            "um": {"name": "微米", "factor": 1e-6},
            "nm": {"name": "纳米", "factor": 1e-9},
            "in": {"name": "英寸", "factor": 0.0254},
            "ft": {"name": "英尺", "factor": 0.3048},
            "yd": {"name": "码", "factor": 0.9144},
            "mi": {"name": "英里", "factor": 1609.344},
            "nmi": {"name": "海里", "factor": 1852.0},
            "li": {"name": "里", "factor": 500.0},
            "zhang": {"name": "丈", "factor": 10.0 / 3.0},
            "chi": {"name": "尺", "factor": 1.0 / 3.0},
        },
    },
    "weight": {
        "name": "重量",
        "base": "kg",
        "units": {
            "kg": {"name": "千克", "factor": 1.0},
            "g": {"name": "克", "factor": 0.001},
            "mg": {"name": "毫克", "factor": 1e-6},
            "t": {"name": "吨", "factor": 1000.0},
            "lb": {"name": "磅", "factor": 0.45359237},
            "oz": {"name": "盎司", "factor": 0.028349523125},
            "ct": {"name": "克拉", "factor": 0.0002},
            "jin": {"name": "斤", "factor": 0.5},
            "liang": {"name": "两", "factor": 0.05},
        },
    },
    "temperature": {
        "name": "温度",
        "base": "C",
        "units": {
            "C": {"name": "摄氏度"},
            "F": {"name": "华氏度"},
            "K": {"name": "开尔文"},
            "R": {"name": "兰金度"},
            "Re": {"name": "列氏度"},
        },
    },
    "area": {
        "name": "面积",
        "base": "m2",
        "units": {
            "m2": {"name": "平方米", "factor": 1.0},
            "km2": {"name": "平方千米", "factor": 1e6},
            "ha": {"name": "公顷", "factor": 10000.0},
            "mu": {"name": "亩", "factor": 2000.0 / 3.0},
            "ft2": {"name": "平方英尺", "factor": 0.09290304},
            "in2": {"name": "平方英寸", "factor": 0.00064516},
            "mi2": {"name": "平方英里", "factor": 2589988.110336},
            "acre": {"name": "英亩", "factor": 4046.8564224},
        },
    },
    "volume": {
        "name": "体积",
        "base": "m3",
        "units": {
            "m3": {"name": "立方米", "factor": 1.0},
            "L": {"name": "升", "factor": 0.001},
            "mL": {"name": "毫升", "factor": 1e-6},
            "gal": {"name": "加仑(美)", "factor": 0.003785411784},
            "qt": {"name": "夸脱(美)", "factor": 0.000946352946},
            "pt": {"name": "品脱(美)", "factor": 0.000473176473},
            "ft3": {"name": "立方英尺", "factor": 0.028316846592},
            "in3": {"name": "立方英寸", "factor": 1.6387064e-5},
        },
    },
    "speed": {
        "name": "速度",
        "base": "m/s",
        "units": {
            "m/s": {"name": "米每秒", "factor": 1.0},
            "km/h": {"name": "千米每小时", "factor": 1.0 / 3.6},
            "mph": {"name": "英里每小时", "factor": 0.44704},
            "kn": {"name": "节", "factor": 1852.0 / 3600.0},
            "Ma": {"name": "马赫", "factor": 340.3},
            "ft/s": {"name": "英尺每秒", "factor": 0.3048},
        },
    },
    "time": {
        "name": "时间",
        "base": "s",
        "units": {
            "s": {"name": "秒", "factor": 1.0},
            "ms": {"name": "毫秒", "factor": 0.001},
            "us": {"name": "微秒", "factor": 1e-6},
            "ns": {"name": "纳秒", "factor": 1e-9},
            "min": {"name": "分钟", "factor": 60.0},
            "h": {"name": "小时", "factor": 3600.0},
            "d": {"name": "天", "factor": 86400.0},
            "wk": {"name": "周", "factor": 604800.0},
            "mo": {"name": "月", "factor": 2592000.0},
            "yr": {"name": "年", "factor": 31536000.0},
        },
    },
    "data": {
        "name": "数据大小",
        "base": "B",
        "units": {
            "bit": {"name": "比特", "factor": 0.125},
            "B": {"name": "字节", "factor": 1.0},
            "KB": {"name": "千字节(十进制)", "factor": 1000.0},
            "MB": {"name": "兆字节(十进制)", "factor": 1e6},
            "GB": {"name": "吉字节(十进制)", "factor": 1e9},
            "TB": {"name": "太字节(十进制)", "factor": 1e12},
            "PB": {"name": "拍字节(十进制)", "factor": 1e15},
            "EB": {"name": "艾字节(十进制)", "factor": 1e18},
            "KiB": {"name": "千比字节(二进制)", "factor": 1024.0},
            "MiB": {"name": "兆比字节(二进制)", "factor": 1024.0 ** 2},
            "GiB": {"name": "吉比字节(二进制)", "factor": 1024.0 ** 3},
            "TiB": {"name": "太比字节(二进制)", "factor": 1024.0 ** 4},
        },
    },
    "energy": {
        "name": "能量",
        "base": "J",
        "units": {
            "J": {"name": "焦耳", "factor": 1.0},
            "kJ": {"name": "千焦", "factor": 1000.0},
            "cal": {"name": "卡路里", "factor": 4.184},
            "kcal": {"name": "千卡", "factor": 4184.0},
            "kWh": {"name": "千瓦时", "factor": 3600000.0},
            "eV": {"name": "电子伏特", "factor": 1.602176634e-19},
            "BTU": {"name": "英热单位", "factor": 1055.05585262},
        },
    },
    "pressure": {
        "name": "压力",
        "base": "Pa",
        "units": {
            "Pa": {"name": "帕斯卡", "factor": 1.0},
            "kPa": {"name": "千帕", "factor": 1000.0},
            "MPa": {"name": "兆帕", "factor": 1e6},
            "bar": {"name": "巴", "factor": 100000.0},
            "atm": {"name": "标准大气压", "factor": 101325.0},
            "mmHg": {"name": "毫米汞柱", "factor": 133.322368421},
            "psi": {"name": "磅每平方英寸", "factor": 6894.757293168},
            "Torr": {"name": "托", "factor": 133.322368421},
        },
    },
    "power": {
        "name": "功率",
        "base": "W",
        "units": {
            "W": {"name": "瓦", "factor": 1.0},
            "kW": {"name": "千瓦", "factor": 1000.0},
            "MW": {"name": "兆瓦", "factor": 1e6},
            "hp": {"name": "马力(公制)", "factor": 735.49875},
            "bhp": {"name": "英制马力", "factor": 745.69987158227022},
            "ft-lb/s": {"name": "英尺磅每秒", "factor": 1.3558179483314004},
            "kcal/h": {"name": "千卡每小时", "factor": 4184.0 / 3600.0},
        },
    },
    "force": {
        "name": "力",
        "base": "N",
        "units": {
            "N": {"name": "牛顿", "factor": 1.0},
            "kN": {"name": "千牛", "factor": 1000.0},
            "kgf": {"name": "千克力", "factor": 9.80665},
            "gf": {"name": "克力", "factor": 0.00980665},
            "lbf": {"name": "磅力", "factor": 4.4482216152605},
            "dyn": {"name": "达因", "factor": 1e-5},
        },
    },
}


# ============================================================
# 温度换算（非线性，需要特殊处理）
# ============================================================

def temp_to_celsius(value: float, unit: str) -> float:
    """将温度转换为摄氏度"""
    if unit == "C":
        return value
    elif unit == "F":
        return (value - 32) * 5.0 / 9.0
    elif unit == "K":
        return value - 273.15
    elif unit == "R":
        return (value - 491.67) * 5.0 / 9.0
    elif unit == "Re":
        return value * 5.0 / 4.0
    else:
        raise ValueError(f"未知温度单位: {unit}")


def celsius_to_temp(value: float, unit: str) -> float:
    """将摄氏度转换为目标温度单位"""
    if unit == "C":
        return value
    elif unit == "F":
        return value * 9.0 / 5.0 + 32
    elif unit == "K":
        return value + 273.15
    elif unit == "R":
        return (value + 273.15) * 9.0 / 5.0
    elif unit == "Re":
        return value * 4.0 / 5.0
    else:
        raise ValueError(f"未知温度单位: {unit}")


# ============================================================
# 通用换算函数
# ============================================================

def find_category(unit: str) -> str:
    """查找单位所属的类别"""
    for cat_key, cat_data in UNITS.items():
        if unit in cat_data["units"]:
            return cat_key
    return None


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """执行单位换算"""
    category = find_category(from_unit)
    if category is None:
        raise ValueError(f"未知源单位: {from_unit}")

    to_category = find_category(to_unit)
    if to_category is None:
        raise ValueError(f"未知目标单位: {to_unit}")

    if category != to_category:
        raise ValueError(f"单位类别不匹配: {from_unit} ({UNITS[category]['name']}) vs {to_unit} ({UNITS[to_category]['name']})")

    # 温度特殊处理
    if category == "temperature":
        celsius = temp_to_celsius(value, from_unit)
        return celsius_to_temp(celsius, to_unit)

    # 线性换算
    from_factor = UNITS[category]["units"][from_unit]["factor"]
    to_factor = UNITS[category]["units"][to_unit]["factor"]
    return value * from_factor / to_factor


def format_number(value: float, precision: int = 6, scientific: bool = False) -> str:
    """格式化数字输出"""
    if scientific:
        return f"{value:.{precision}e}"
    else:
        # 对于极大或极小值自动使用科学计数法
        if value != 0 and (abs(value) >= 1e15 or abs(value) < 1e-6):
            return f"{value:.{precision}e}"
        formatted = f"{value:.{precision}f}"
        # 去除末尾多余的零
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted


# ============================================================
# 输出函数
# ============================================================

def print_categories():
    """列出所有类别"""
    print("📋 支持的单位类别：")
    print("=" * 50)
    for cat_key, cat_data in UNITS.items():
        unit_count = len(cat_data["units"])
        print(f"  {cat_key:<15} {cat_data['name']:<8} ({unit_count} 种单位)")
    print("=" * 50)
    print(f"共 {len(UNITS)} 个类别")


def print_category_units(category: str):
    """列出指定类别的所有单位"""
    if category not in UNITS:
        print(f"错误：未知类别 '{category}'", file=sys.stderr)
        print("使用 --categories 查看所有类别", file=sys.stderr)
        sys.exit(1)

    cat_data = UNITS[category]
    print(f"📐 {cat_data['name']}（{category}）单位列表：")
    print("=" * 50)
    print(f"  {'符号':<12} {'名称':<15} {'基准换算因子'}")
    print("-" * 50)
    for unit_key, unit_data in cat_data["units"].items():
        if category == "temperature":
            factor_str = "非线性"
        else:
            factor = unit_data["factor"]
            if factor == 1.0:
                factor_str = "基准单位"
            elif factor >= 1e6 or factor < 1e-3:
                factor_str = f"{factor:.2e}"
            else:
                factor_str = f"{factor:.6g}"
        print(f"  {unit_key:<12} {unit_data['name']:<15} {factor_str}")
    print("=" * 50)


def print_single_conversion(value: float, from_unit: str, to_unit: str,
                             precision: int, scientific: bool):
    """输出单个换算结果"""
    result = convert(value, from_unit, to_unit)
    from_name = UNITS[find_category(from_unit)]["units"][from_unit]["name"]
    to_name = UNITS[find_category(to_unit)]["units"][to_unit]["name"]

    print("🔄 单位换算结果")
    print("=" * 50)
    print(f"  输入: {format_number(value, precision, scientific)} {from_unit} ({from_name})")
    print(f"  输出: {format_number(result, precision, scientific)} {to_unit} ({to_name})")
    print("=" * 50)


def print_batch_conversion(value: float, from_unit: str, precision: int, scientific: bool):
    """输出批量换算结果（到该类别所有单位）"""
    category = find_category(from_unit)
    cat_data = UNITS[category]
    from_name = cat_data["units"][from_unit]["name"]

    print(f"📊 批量换算：{format_number(value, precision, scientific)} {from_unit} ({from_name})")
    print("=" * 60)
    print(f"  {'单位':<12} {'名称':<15} {'换算结果'}")
    print("-" * 60)

    for unit_key, unit_data in cat_data["units"].items():
        if unit_key == from_unit:
            result_str = f"{format_number(value, precision, scientific)} (原值)"
        else:
            result = convert(value, from_unit, unit_key)
            result_str = format_number(result, precision, scientific)
        print(f"  {unit_key:<12} {unit_data['name']:<15} {result_str}")

    print("=" * 60)


def print_cheatsheet():
    """输出常用换算速查表"""
    print("📖 常用单位换算速查表")
    print("=" * 70)

    cheatsheet = [
        ("长度", [
            ("1 m", "3.28084 ft", "1 米 = 3.28 英尺"),
            ("1 km", "0.621371 mi", "1 公里 = 0.62 英里"),
            ("1 in", "2.54 cm", "1 英寸 = 2.54 厘米"),
            ("1 mi", "1.60934 km", "1 英里 = 1.61 公里"),
            ("1 nmi", "1.852 km", "1 海里 = 1.852 公里"),
        ]),
        ("重量", [
            ("1 kg", "2.20462 lb", "1 千克 = 2.20 磅"),
            ("1 lb", "0.453592 kg", "1 磅 = 0.45 千克"),
            ("1 jin", "0.5 kg", "1 斤 = 0.5 千克"),
            ("1 oz", "28.3495 g", "1 盎司 = 28.35 克"),
            ("1 ct", "0.2 g", "1 克拉 = 0.2 克"),
        ]),
        ("温度", [
            ("0°C", "32°F", "水的冰点"),
            ("100°C", "212°F", "水的沸点"),
            ("37°C", "98.6°F", "人体正常体温"),
            ("20°C", "68°F", "室温"),
            ("0 K", "-273.15°C", "绝对零度"),
        ]),
        ("数据大小", [
            ("1 GB", "1000 MB", "十进制（厂商）"),
            ("1 GiB", "1024 MiB", "二进制（系统）"),
            ("1 TB", "约 931 GiB", "1TB 硬盘实际容量"),
            ("1 MB", "1000 KB", "十进制"),
            ("1 MiB", "1024 KiB", "二进制"),
        ]),
        ("速度", [
            ("100 km/h", "62.1371 mph", "100 公里/小时 = 62 英里/小时"),
            ("1 Ma", "1225.08 km/h", "1 马赫 ≈ 1225 公里/小时"),
            ("1 kn", "1.852 km/h", "1 节 = 1.852 公里/小时"),
            ("60 mph", "96.5606 km/h", "60 英里/小时 = 96.6 公里/小时"),
        ]),
        ("能量", [
            ("1 kcal", "4184 J", "1 千卡 = 4184 焦耳"),
            ("1 kWh", "3.6e6 J", "1 千瓦时 = 360 万焦耳"),
            ("1 cal", "4.184 J", "1 卡路里 = 4.184 焦耳"),
            ("1 eV", "1.602e-19 J", "1 电子伏特 ≈ 1.602×10⁻¹⁹ 焦耳"),
        ]),
        ("压力", [
            ("1 atm", "101325 Pa", "1 标准大气压"),
            ("1 atm", "14.6959 psi", "1 大气压 = 14.7 psi"),
            ("1 bar", "100000 Pa", "1 巴 = 10 万帕"),
            ("1 mmHg", "133.322 Pa", "1 毫米汞柱"),
        ]),
        ("功率", [
            ("1 hp", "735.499 W", "1 公制马力 = 735.5 瓦"),
            ("1 bhp", "745.7 W", "1 英制马力 = 745.7 瓦"),
            ("1 kW", "1.35962 hp", "1 千瓦 = 1.36 马力"),
        ]),
    ]

    for cat_name, items in cheatsheet:
        print(f"\n【{cat_name}】")
        print("-" * 70)
        for from_val, to_val, desc in items:
            print(f"  {from_val:<12} = {to_val:<20} {desc}")

    print("\n" + "=" * 70)
    print("提示：使用 --value/--from/--to 进行精确换算，使用 --list 查看所有单位")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="单位换算工具 - 支持 12 大类 80+ 种单位",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --value 1 --from m --to ft          米转英尺
  %(prog)s --value 100 --from C --to F          摄氏度转华氏度
  %(prog)s --value 1 --from kg                  批量换算千克
  %(prog)s --list length                         列出长度单位
  %(prog)s --categories                          列出所有类别
  %(prog)s --cheatsheet                          常用换算速查表
        """,
    )
    parser.add_argument("--value", "-v", type=float, help="要换算的数值")
    parser.add_argument("--from", "-f", dest="from_unit", help="源单位")
    parser.add_argument("--to", "-t", dest="to_unit", help="目标单位（不指定则批量换算）")
    parser.add_argument("--list", "-l", dest="list_category", metavar="CATEGORY",
                        help="列出指定类别的所有单位")
    parser.add_argument("--categories", action="store_true",
                        help="列出所有支持的类别")
    parser.add_argument("--precision", "-p", type=int, default=6,
                        help="小数位数（默认 6）")
    parser.add_argument("--scientific", "-s", action="store_true",
                        help="使用科学计数法显示")
    parser.add_argument("--cheatsheet", "-c", action="store_true",
                        help="显示常用换算速查表")

    args = parser.parse_args()

    # 列出所有类别
    if args.categories:
        print_categories()
        return

    # 列出指定类别单位
    if args.list_category:
        print_category_units(args.list_category)
        return

    # 显示速查表
    if args.cheatsheet:
        print_cheatsheet()
        return

    # 执行换算
    if args.value is None or args.from_unit is None:
        parser.print_help()
        print("\n错误：换算需要 --value 和 --from 参数", file=sys.stderr)
        sys.exit(1)

    # 验证源单位
    category = find_category(args.from_unit)
    if category is None:
        print(f"错误：未知单位 '{args.from_unit}'", file=sys.stderr)
        print("使用 --categories 查看所有类别，使用 --list <类别> 查看该类别所有单位",
              file=sys.stderr)
        sys.exit(1)

    # 单个换算或批量换算
    if args.to_unit:
        print_single_conversion(args.value, args.from_unit, args.to_unit,
                                 args.precision, args.scientific)
    else:
        print_batch_conversion(args.value, args.from_unit,
                               args.precision, args.scientific)


if __name__ == "__main__":
    main()
