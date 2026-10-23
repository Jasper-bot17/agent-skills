#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
IP 子网计算器

支持 CIDR 解析、子网拆分、超网聚合、IP 分类、批量计算、JSON 输出。
基于 Python 标准库 ipaddress 模块实现。

用法：
  python3 calc_subnet.py 192.168.1.0/24
  python3 calc_subnet.py 10.0.5.100/22
  python3 calc_subnet.py 192.168.1.0/24 --split 26
  python3 calc_subnet.py 192.168.1.0/24 --split-count 4
  python3 calc_subnet.py --supernet 192.168.0.0/24 192.168.1.0/24
  python3 calc_subnet.py 10.0.0.0/8 172.16.0.0/12 --json
"""

import argparse
import ipaddress
import json
import sys


# ============================================================
# 核心计算函数
# ============================================================

def parse_cidr(cidr_str):
    """解析 CIDR，返回详细信息字典"""
    try:
        net = ipaddress.IPv4Network(cidr_str, strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as e:
        return None, str(e)

    info = {
        "cidr": str(net),
        "network_address": str(net.network_address),
        "broadcast_address": str(net.broadcast_address),
        "netmask": str(net.netmask),
        "wildcard_mask": str(net.hostmask),
        "prefixlen": net.prefixlen,
        "num_addresses": net.num_addresses,
        "is_private": net.is_private,
        "is_global": net.is_global,
        "is_loopback": net.is_loopback,
        "is_link_local": net.is_link_local,
        "is_multicast": net.is_multicast,
        "is_reserved": net.is_reserved,
        "is_unspecified": net.is_unspecified,
    }

    # 计算可用主机范围（/31 和 /32 特殊处理）
    if net.prefixlen == 32:
        info["host_min"] = str(net.network_address)
        info["host_max"] = str(net.network_address)
        info["usable_hosts"] = 1
    elif net.prefixlen == 31:
        # 点对点链路：两个地址都可用
        info["host_min"] = str(net.network_address)
        info["host_max"] = str(net.broadcast_address)
        info["usable_hosts"] = 2
    else:
        info["host_min"] = str(net.network_address + 1)
        info["host_max"] = str(net.broadcast_address - 1)
        info["usable_hosts"] = net.num_addresses - 2

    # IP 分类（A/B/C/D/E）
    info["ip_class"] = _classify_network(net)

    # 用途标签
    info["usage"] = _usage_label(net)

    return info, None


def _classify_network(net):
    """判断 IP 分类（A/B/C/D/E）"""
    first_octet = int(str(net.network_address).split(".")[0])
    if first_octet >= 224:
        return "D（组播）" if first_octet < 240 else "E（保留）"
    elif first_octet >= 192:
        return "C"
    elif first_octet >= 128:
        return "B"
    elif first_octet >= 1:
        return "A"
    else:
        return "特殊"


def _usage_label(net):
    """返回用途标签"""
    labels = []
    if net.is_loopback:
        labels.append("环回")
    if net.is_link_local:
        labels.append("链路本地")
    if net.is_multicast:
        labels.append("组播")
    if net.is_reserved:
        labels.append("保留")
    if net.is_unspecified:
        labels.append("未指定")
    if net.is_private and not net.is_loopback and not net.is_link_local:
        labels.append("私网")
    if net.is_global and not net.is_private:
        labels.append("公网")
    return "、".join(labels) if labels else "普通"


def split_subnet(cidr_str, new_prefix=None, count=None):
    """拆分子网"""
    try:
        net = ipaddress.IPv4Network(cidr_str, strict=False)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as e:
        return None, str(e)

    if new_prefix is not None:
        if new_prefix <= net.prefixlen:
            return None, f"新前缀 /{new_prefix} 必须大于原前缀 /{net.prefixlen}"
        subnets = list(net.subnets(new_prefix=new_prefix))
    elif count is not None:
        # 计算需要的新前缀
        import math
        needed_bits = math.ceil(math.log2(count))
        new_prefix = net.prefixlen + needed_bits
        if new_prefix > 32:
            return None, f"无法拆分 {count} 个子网（最多 {2 ** (32 - net.prefixlen)} 个）"
        subnets = list(net.subnets(new_prefix=new_prefix))[:count]
    else:
        return None, "必须指定 new_prefix 或 count"

    results = []
    for i, sub in enumerate(subnets):
        info, _ = parse_cidr(str(sub))
        info["index"] = i
        results.append(info)

    return {
        "parent": str(net),
        "new_prefix": new_prefix,
        "subnet_count": len(subnets),
        "subnets": results,
    }, None


def supernet(cidr_list):
    """聚合多个 CIDR 为最小超网"""
    networks = []
    for c in cidr_list:
        try:
            networks.append(ipaddress.IPv4Network(c, strict=False))
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as e:
            return None, f"无效 CIDR {c}: {e}"

    if not networks:
        return None, "未提供有效网络"

    # 使用 collapse_addresses 聚合所有网络，取结果中最小的那个
    collapsed = list(ipaddress.collapse_addresses(networks))
    if len(collapsed) == 1:
        result = collapsed[0]
    else:
        # 如果无法聚合成一个网络，取最大范围的那个
        result = collapsed[0]
        for net in collapsed[1:]:
            if net.num_addresses > result.num_addresses:
                result = net

    info, _ = parse_cidr(str(result))
    info["original_networks"] = [str(n) for n in networks]
    info["aggregated_count"] = len(networks)
    info["collapsed_count"] = len(collapsed)
    return info, None


# ============================================================
# 输出格式化
# ============================================================

def print_info(info, as_json=False):
    """打印单个 CIDR 解析结果"""
    if as_json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print(f"{'='*60}")
    print(f"  {info['cidr']}")
    print(f"{'='*60}")
    print(f"  网络地址:     {info['network_address']}")
    print(f"  广播地址:     {info['broadcast_address']}")
    print(f"  子网掩码:     {info['netmask']}  (/{info['prefixlen']})")
    print(f"  通配符掩码:   {info['wildcard_mask']}")
    print(f"  可用主机范围: {info['host_min']} ~ {info['host_max']}")
    print(f"  可用主机数:   {info['usable_hosts']}  (总地址 {info['num_addresses']})")
    print(f"  IP 分类:      {info['ip_class']}")
    print(f"  地址用途:     {info['usage']}")
    print()


def print_split(result, as_json=False):
    """打印子网拆分结果"""
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"{'='*70}")
    print(f"  拆分 {result['parent']} → /{result['new_prefix']}（共 {result['subnet_count']} 个子网）")
    print(f"{'='*70}")
    print(f"{'#':<4} {'CIDR':<20} {'网络地址':<16} {'广播地址':<16} {'可用主机范围':<32} {'主机数'}")
    print("-" * 70)
    for s in result["subnets"]:
        host_range = f"{s['host_min']} ~ {s['host_max']}"
        print(f"{s['index']:<4} {s['cidr']:<20} {s['network_address']:<16} "
              f"{s['broadcast_address']:<16} {host_range:<32} {s['usable_hosts']}")
    print()


def print_supernet(info, as_json=False):
    """打印超网聚合结果"""
    if as_json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    print(f"{'='*60}")
    print(f"  超网聚合结果")
    print(f"{'='*60}")
    print(f"  原始网络 ({info['aggregated_count']} 个):")
    for n in info["original_networks"]:
        print(f"    • {n}")
    print(f"\n  最小超网: {info['cidr']}")
    print(f"  网络地址: {info['network_address']}")
    print(f"  广播地址: {info['broadcast_address']}")
    print(f"  子网掩码: {info['netmask']}  (/{info['prefixlen']})")
    print(f"  总地址数: {info['num_addresses']}")
    print()


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="IP 子网计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s 192.168.1.0/24
  %(prog)s 10.0.5.100/22
  %(prog)s 192.168.1.0/24 --split 26
  %(prog)s 192.168.1.0/24 --split-count 4
  %(prog)s --supernet 192.168.0.0/24 192.168.1.0/24
  %(prog)s 10.0.0.0/8 172.16.0.0/12 --json
        """,
    )

    parser.add_argument("cidrs", nargs="*", help="CIDR 地址（可多个）")
    parser.add_argument("--split", type=int, metavar="PREFIX",
                        help="拆分到新前缀（如 26 表示拆成 /26）")
    parser.add_argument("--split-count", type=int, metavar="N",
                        help="拆分为 N 个子网（自动计算前缀）")
    parser.add_argument("--supernet", nargs="+", metavar="CIDR",
                        help="聚合多个 CIDR 为超网")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    # 超网聚合
    if args.supernet:
        info, err = supernet(args.supernet)
        if err:
            print(f"❌ {err}", file=sys.stderr)
            sys.exit(1)
        print_supernet(info, as_json=args.json)
        return

    # 子网拆分
    if args.split is not None or args.split_count is not None:
        if not args.cidrs:
            print("❌ 拆分需要指定父网络", file=sys.stderr)
            sys.exit(1)
        if len(args.cidrs) > 1:
            print("❌ 拆分时请只指定一个父网络", file=sys.stderr)
            sys.exit(1)
        result, err = split_subnet(args.cidrs[0],
                                   new_prefix=args.split,
                                   count=args.split_count)
        if err:
            print(f"❌ {err}", file=sys.stderr)
            sys.exit(1)
        print_split(result, as_json=args.json)
        return

    # 批量解析
    if args.cidrs:
        for cidr in args.cidrs:
            info, err = parse_cidr(cidr)
            if err:
                print(f"❌ 无效 CIDR '{cidr}': {err}", file=sys.stderr)
                continue
            print_info(info, as_json=args.json)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
