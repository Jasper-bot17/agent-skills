#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
决策矩阵助手（加权评分法）

帮助在多个选项和多个评价标准之间做量化决策。

用法：
  python3 decision_matrix.py                          # 交互式输入
  python3 decision_matrix.py --config decision.json   # 从配置文件运行
  python3 decision_matrix.py --config d.json --sensitivity "薪资=15"
  python3 decision_matrix.py --config d.json --json
"""

import argparse
import json
import sys


# ============================================================
# 核心计算
# ============================================================

class DecisionMatrix:
    def __init__(self, criteria, options):
        """
        criteria: [(name, weight, direction), ...]  direction: positive/negative
        options:  [(name, {criterion_name: score}), ...]
        """
        self.criteria = criteria
        self.options = options
        # 归一化权重
        total_w = sum(c[1] for c in criteria)
        self.norm_weights = {c[0]: c[1] / total_w for c in criteria}

    def calculate(self):
        """计算每个选项的加权总分"""
        results = []
        for opt_name, scores in self.options:
            total = 0.0
            detail = {}
            for crit_name, weight, direction in self.criteria:
                raw_score = scores.get(crit_name, 0)
                # 逆向标准：得分 = 11 - 原始分
                if direction == "negative":
                    adjusted = 10 - raw_score + 1  # 1-10 反向
                else:
                    adjusted = raw_score
                weighted = adjusted * self.norm_weights[crit_name]
                total += weighted
                detail[crit_name] = {
                    "raw": raw_score,
                    "adjusted": adjusted,
                    "weighted": round(weighted, 2),
                }
            results.append({
                "name": opt_name,
                "total_score": round(total, 2),
                "detail": detail,
            })
        # 按总分降序
        results.sort(key=lambda x: x["total_score"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1
        return results

    def sensitivity(self, crit_name, new_weight):
        """敏感性分析：调整某个标准的权重后重新计算"""
        new_criteria = []
        for c_name, weight, direction in self.criteria:
            if c_name == crit_name:
                new_criteria.append((c_name, new_weight, direction))
            else:
                new_criteria.append((c_name, weight, direction))
        dm = DecisionMatrix(new_criteria, self.options)
        return dm.calculate()


# ============================================================
# 表格输出
# ============================================================

def print_table(results, criteria, title="决策矩阵结果"):
    """打印文本对比表格"""
    crit_names = [c[0] for c in criteria]

    # 表头
    header = f"{'选项':<12}"
    for cn in crit_names:
        header += f" {cn:>8}"
    header += f" {'总分':>8} {'排名':>4}"

    sep = "-" * len(header)

    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print()
    print(header)
    print(sep)

    for r in results:
        row = f"{r['name']:<12}"
        for cn in crit_names:
            d = r["detail"].get(cn, {})
            row += f" {d.get('raw', '-'):>8}"
        row += f" {r['total_score']:>8.1f} {r['rank']:>4}"
        print(row)

    print(sep)
    print()

    # 权重行
    wrow = f"{'权重':<12}"
    for c_name, weight, direction in criteria:
        arrow = "↓" if direction == "negative" else "↑"
        wrow += f" {str(weight)+arrow:>8}"
    print(wrow)
    print()

    # 推荐
    winner = results[0]
    runner_up = results[1] if len(results) > 1 else None
    print(f"  🏆 推荐选项: {winner['name']}（总分 {winner['total_score']:.1f}）")
    if runner_up:
        gap = winner['total_score'] - runner_up['total_score']
        margin = gap / winner['total_score'] * 100
        print(f"     第二名: {runner_up['name']}（{runner_up['total_score']:.1f}，领先 {gap:.1f} 分，差距 {margin:.1f}%）")
    print()


def print_sensitivity(original, modified, crit_name, old_weight, new_weight):
    """打印敏感性分析对比"""
    print(f"\n{'~'*60}")
    print(f"  敏感性分析：{crit_name} 权重 {old_weight} → {new_weight}")
    print(f"{'~'*60}")
    print()
    print(f"{'选项':<12} {'原排名':>6} {'新排名':>6} {'原总分':>8} {'新总分':>8} {'变化':>8}")
    print("-" * 60)

    orig_map = {r["name"]: r for r in original}
    for mr in modified:
        or_ = orig_map[mr["name"]]
        change = mr["total_score"] - or_["total_score"]
        arrow = "↑" if change > 0 else ("↓" if change < 0 else "→")
        change_str = f"{arrow} {abs(change):.1f}" if change != 0 else "→ 0.0"
        rank_change = or_["rank"] - mr["rank"]
        rank_str = f"{'↑' if rank_change>0 else '↓' if rank_change<0 else '→'}{abs(rank_change)}"
        print(f"{mr['name']:<12} {or_['rank']:>6} {mr['rank']:>6} {or_['total_score']:>8.1f} {mr['total_score']:>8.1f} {change_str:>8}")

    print()
    new_winner = modified[0]["name"]
    old_winner = original[0]["name"]
    if new_winner != old_winner:
        print(f"  ⚠️  排名发生变化！推荐选项从「{old_winner}」变为「{new_winner}」")
    else:
        print(f"  ✅ 排名未变，推荐选项仍为「{new_winner}」，结果稳健")
    print()


# ============================================================
# 交互式输入
# ============================================================

def interactive_input():
    """交互式收集决策数据"""
    print("\n" + "=" * 60)
    print("  决策矩阵助手（交互式输入）")
    print("=" * 60)
    print()

    title = input("决策问题（如：选择工作机会）: ").strip()
    if not title:
        title = "决策矩阵"

    # 标准
    print("\n--- 评价标准 ---")
    print("每个标准输入名称、权重(1-10)、方向(正向/逆向)")
    print("方向：正向=越大越好（如薪资），逆向=越小越好（如通勤时间）")
    print("输入空名称结束\n")

    criteria = []
    while True:
        name = input(f"标准 {len(criteria)+1} 名称（空=结束）: ").strip()
        if not name:
            break
        while True:
            try:
                weight = int(input(f"  {name} 权重(1-10): "))
                if 1 <= weight <= 10:
                    break
                print("  请输入 1-10")
            except ValueError:
                print("  请输入数字")
        direction = input(f"  {name} 方向(正/逆): ").strip()
        direction = "negative" if direction in ("逆", "n", "negative", "0") else "positive"
        criteria.append((name, weight, direction))

    if not criteria:
        print("至少需要一个标准", file=sys.stderr)
        sys.exit(1)

    # 选项
    print("\n--- 选项 ---")
    options = []
    while True:
        name = input(f"选项 {len(options)+1} 名称（空=结束）: ").strip()
        if not name:
            break
        scores = {}
        for c_name, weight, direction in criteria:
            while True:
                try:
                    s = int(input(f"  {name} - {c_name} 得分(1-10): "))
                    if 1 <= s <= 10:
                        break
                    print("    请输入 1-10")
                except ValueError:
                    print("    请输入数字")
            scores[c_name] = s
        options.append((name, scores))

    if len(options) < 2:
        print("至少需要两个选项", file=sys.stderr)
        sys.exit(1)

    return title, criteria, options


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="决策矩阵助手")
    parser.add_argument("--config", help="JSON 配置文件路径")
    parser.add_argument("--sensitivity", "-s", action="append",
                        help="敏感性分析，格式: 标准名=新权重，可多次")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"❌ 读取配置文件失败: {e}", file=sys.stderr)
            sys.exit(1)

        title = config.get("title", "决策矩阵")
        criteria = [
            (c["name"], c["weight"], c.get("direction", "positive"))
            for c in config["criteria"]
        ]
        options = [
            (o["name"], o["scores"])
            for o in config["options"]
        ]
    else:
        title, criteria, options = interactive_input()

    # 计算
    dm = DecisionMatrix(criteria, options)
    results = dm.calculate()

    if args.json:
        output = {
            "title": title,
            "criteria": [
                {"name": c[0], "weight": c[1], "direction": c[2]}
                for c in criteria
            ],
            "ranking": [
                {
                    "rank": r["rank"],
                    "name": r["name"],
                    "total_score": r["total_score"],
                    "detail": r["detail"],
                }
                for r in results
            ],
            "winner": results[0]["name"],
        }
        # 敏感性分析
        if args.sensitivity:
            sensitivities = []
            for s in args.sensitivity:
                if "=" not in s:
                    continue
                crit_name, new_w = s.split("=", 1)
                crit_name = crit_name.strip()
                try:
                    new_w = int(new_w.strip())
                except ValueError:
                    continue
                # 找原始权重
                old_w = None
                for c in criteria:
                    if c[0] == crit_name:
                        old_w = c[1]
                        break
                if old_w is None:
                    continue
                mod_results = dm.sensitivity(crit_name, new_w)
                sensitivities.append({
                    "criterion": crit_name,
                    "old_weight": old_w,
                    "new_weight": new_w,
                    "ranking": [
                        {"rank": r["rank"], "name": r["name"], "total_score": r["total_score"]}
                        for r in mod_results
                    ],
                })
            output["sensitivity"] = sensitivities
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 文本输出
        print_table(results, criteria, title)

        # 敏感性分析
        if args.sensitivity:
            for s in args.sensitivity:
                if "=" not in s:
                    continue
                crit_name, new_w = s.split("=", 1)
                crit_name = crit_name.strip()
                try:
                    new_w = int(new_w.strip())
                except ValueError:
                    continue
                old_w = None
                for c in criteria:
                    if c[0] == crit_name:
                        old_w = c[1]
                        break
                if old_w is None:
                    print(f"⚠️  未找到标准: {crit_name}")
                    continue
                mod_results = dm.sensitivity(crit_name, new_w)
                print_sensitivity(results, mod_results, crit_name, old_w, new_w)


if __name__ == "__main__":
    main()
