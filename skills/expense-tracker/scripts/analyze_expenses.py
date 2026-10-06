#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人记账与消费分析助手 - 消费记录分析脚本

解析消费记录（CSV/文本），自动分类，生成统计报告。

用法：
    python3 analyze_expenses.py --input expenses.csv --month 2026-09 --format report
    python3 analyze_expenses.py --input expenses.csv --format json
    python3 analyze_expenses.py --input expenses.csv --budget 8000
    cat expenses.txt | python3 analyze_expenses.py --format report

CSV 格式（表头可选）：
    date,amount,category,description,payment_method
    2026-09-01,35.00,餐饮,午餐,微信

纯文本格式（每行一笔）：
    2026-09-01 午餐 35
    9/1 地铁 6
    9月2日 超市购物 156.5
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import List, Optional, Dict, Tuple


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Expense:
    """单笔消费记录"""
    date: str
    amount: float
    type: str  # 支出 / 收入
    category: str  # 一级类别
    subcategory: str  # 二级类别
    description: str
    payment_method: str = ""
    raw_text: str = ""


@dataclass
class CategoryStat:
    """类别统计"""
    name: str
    total: float = 0.0
    count: int = 0
    daily_avg: float = 0.0
    percentage: float = 0.0
    max_single: float = 0.0
    expenses: List[Expense] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """完整分析结果"""
    period: str = ""
    total_income: float = 0.0
    total_expense: float = 0.0
    balance: float = 0.0
    expense_count: int = 0
    income_count: int = 0
    days_in_period: int = 0
    daily_avg: float = 0.0
    max_expense: Optional[Expense] = None
    categories: Dict[str, CategoryStat] = field(default_factory=dict)
    daily_expenses: Dict[str, float] = field(default_factory=dict)
    top_expenses: List[Expense] = field(default_factory=list)
    budget: Optional[float] = None
    budget_remaining: Optional[float] = None
    budget_usage_pct: Optional[float] = None
    uncategorized: List[Expense] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================
# 消费类别关键词映射
# ============================================================

CATEGORY_KEYWORDS = {
    "餐饮": {
        "icon": "🍜",
        "subcategories": {
            "早餐": ["早餐", "早饭", "包子", "豆浆", "油条", "煎饼", "面包", "牛奶", "breakfast"],
            "午餐": ["午餐", "午饭", "中饭", "快餐", "黄焖鸡", "拉面", "外卖", "lunch"],
            "晚餐": ["晚餐", "晚饭", "夜宵", "烧烤", "火锅", "dinner"],
            "零食饮料": ["奶茶", "咖啡", "星巴克", "瑞幸", "零食", "饮料", "可乐", "冰淇淋", "甜品", "蛋糕", "coffee", "milk tea"],
            "水果": ["水果", "苹果", "香蕉", "葡萄", "西瓜", "fruit"],
            "食材": ["超市", "菜场", "买菜", "食材", "肉", "蔬菜", "grocery"],
        }
    },
    "交通": {
        "icon": "🚇",
        "subcategories": {
            "地铁公交": ["地铁", "公交", "公交通", "metro", "bus", "subway"],
            "打车": ["打车", "滴滴", "出租车", "网约车", "uber", "taxi", "ride"],
            "加油": ["加油", "油费", "gas", "fuel"],
            "停车": ["停车", "停车费", "parking"],
            "过路费": ["过路费", "高速费", "toll"],
            "火车票": ["火车", "高铁", "动车", "12306", "train", "railway"],
            "机票": ["机票", "飞机", "航班", "flight", "airline"],
            "共享单车": ["共享单车", "哈啰", "美团单车", "青桔", "bike"],
        }
    },
    "购物": {
        "icon": "🛒",
        "subcategories": {
            "服饰鞋包": ["衣服", "裤子", "鞋子", "包包", "外套", "T恤", "裙子", "内衣", "袜子", "clothes", "shoes", "bag"],
            "美妆护肤": ["口红", "面膜", "护肤品", "化妆品", "香水", "洗面奶", "美妆", "skincare", "cosmetics"],
            "日用品": ["日用品", "纸巾", "洗衣液", "洗发水", "沐浴露", "牙膏", "牙刷", "household", "daily necessities"],
            "数码产品": ["手机", "电脑", "耳机", "键盘", "鼠标", "充电器", "数据线", "平板", "相机", "electronics", "gadget"],
            "家居用品": ["家具", "家电", "床单", "被子", "枕头", "灯具", "收纳", "home", "furniture"],
            "书籍文具": ["书", "书籍", "笔记本", "笔", "文具", "book", "stationery"],
        }
    },
    "住房": {
        "icon": "🏠",
        "subcategories": {
            "房租房贷": ["房租", "租金", "房贷", "rent", "mortgage"],
            "水电燃气": ["水费", "电费", "燃气", "煤气", "utility", "electricity", "water", "gas"],
            "物业费": ["物业", "物业费", "property"],
            "宽带": ["宽带", "网费", "wifi", "internet"],
            "维修": ["维修", "修理", "repair", "fix"],
        }
    },
    "娱乐": {
        "icon": "🎮",
        "subcategories": {
            "电影演出": ["电影", "票", "演出", "演唱会", "话剧", "cinema", "movie", "concert"],
            "游戏充值": ["游戏", "充值", "steam", "皮肤", "点券", "game"],
            "会员订阅": ["会员", "订阅", "vip", "netflix", "spotify", "爱奇艺", "腾讯视频", "优酷", "b站", "bilibili"],
            "旅游": ["旅游", "旅行", "酒店", "住宿", "门票", "景点", "travel", "hotel", "ticket"],
            "运动健身": ["健身", "健身房", "瑜伽", "跑步", "球赛", "fitness", "gym", "yoga"],
            "聚会社交": ["聚会", "聚餐", "ktv", "酒吧", "朋友", "party", "ktv"],
        }
    },
    "医疗": {
        "icon": "💊",
        "subcategories": {
            "门诊挂号": ["挂号", "门诊", "看病", "医院", "clinic", "hospital"],
            "药品": ["药", "药品", "药店", "药房", "medicine", "drug", "pharmacy"],
            "体检": ["体检", "检查", "体检报告", "checkup", "physical"],
            "保健品": ["保健品", "维生素", "钙片", "supplement", "vitamin"],
            "牙科": ["牙科", "牙医", "洗牙", "补牙", "dentist", "dental"],
            "眼科": ["眼科", "眼镜", "验光", "eye", "glasses", "optic"],
        }
    },
    "教育": {
        "icon": "📚",
        "subcategories": {
            "课程培训": ["课程", "培训", "网课", "在线课程", "辅导班", "course", "training", "class"],
            "考试报名": ["考试", "报名费", "考证", "exam", "certification"],
            "书籍": ["教材", "参考书", "课本", "textbook"],
            "学习工具": ["学习", "知识付费", "得到", "极客时间", "learning", "tool"],
        }
    },
    "人情": {
        "icon": "🧧",
        "subcategories": {
            "红包": ["红包", "red packet", "red envelope"],
            "礼物": ["礼物", "礼品", "gift", "present"],
            "请客": ["请客", "treat"],
            "捐赠": ["捐赠", "捐款", "慈善", "donation", "charity"],
            "份子钱": ["份子", "随礼", "wedding gift"],
        }
    },
    "通讯": {
        "icon": "📱",
        "subcategories": {
            "手机话费": ["话费", "充值", "手机费", "phone bill", "mobile"],
            "流量包": ["流量", "data plan"],
            "网络服务": ["网络", "宽带费", "network"],
        }
    },
    "金融": {
        "icon": "💰",
        "subcategories": {
            "保险": ["保险", "保费", "insurance", "premium"],
            "理财": ["理财", "基金", "股票", "investment", "fund", "stock"],
            "贷款还款": ["贷款", "还款", "月供", "loan", "repayment"],
            "手续费": ["手续费", "利息", "fee", "interest", "charge"],
        }
    },
    "宠物": {
        "icon": "🐾",
        "subcategories": {
            "宠物食品": ["猫粮", "狗粮", "宠物粮", "pet food"],
            "宠物医疗": ["宠物医院", "疫苗", "驱虫", "vet", "pet medical"],
            "宠物用品": ["猫砂", "狗窝", "宠物用品", "pet supplies"],
            "宠物美容": ["宠物美容", "洗澡", "grooming"],
        }
    },
    "育儿": {
        "icon": "🚼",
        "subcategories": {
            "奶粉尿布": ["奶粉", "尿布", "尿不湿", "milk powder", "diaper"],
            "玩具": ["玩具", "toy"],
            "童装": ["童装", "宝宝衣服", "baby clothes"],
            "早教": ["早教", "幼儿园", "daycare", "kindergarten"],
            "学费": ["学费", "school fee"],
        }
    },
}

# 商家名称映射（常见商家 -> 类别）
MERCHANT_CATEGORY = {
    "星巴克": ("餐饮", "零食饮料"), "瑞幸": ("餐饮", "零食饮料"),
    "麦当劳": ("餐饮", "午餐"), "肯德基": ("餐饮", "午餐"),
    "海底捞": ("餐饮", "晚餐"), "美团": ("餐饮", "外卖"),
    "饿了么": ("餐饮", "外卖"), "滴滴": ("交通", "打车"),
    "高德": ("交通", "打车"), "12306": ("交通", "火车票"),
    "携程": ("娱乐", "旅游"), "飞猪": ("娱乐", "旅游"),
    "淘宝": ("购物", "日用品"), "天猫": ("购物", "日用品"),
    "京东": ("购物", "数码产品"), "拼多多": ("购物", "日用品"),
    "网易云": ("娱乐", "会员订阅"), "qq音乐": ("娱乐", "会员订阅"),
    "b站": ("娱乐", "会员订阅"), "bilibili": ("娱乐", "会员订阅"),
    "爱奇艺": ("娱乐", "会员订阅"), "腾讯视频": ("娱乐", "会员订阅"),
    "steam": ("娱乐", "游戏充值"), "微信": ("其他", ""),
    "支付宝": ("其他", ""), "apple": ("购物", "数码产品"),
    "华为": ("购物", "数码产品"), "小米": ("购物", "数码产品"),
}

# 收入关键词
INCOME_KEYWORDS = ["工资", "薪水", "薪资", "奖金", "收入", "报销", "退款",
                   "红包收入", "理财收益", "利息", "salary", "income", "bonus",
                   "refund", "reimbursement", "dividend"]


# ============================================================
# 解析器
# ============================================================

class ExpenseParser:
    """解析消费记录"""

    def __init__(self):
        self.expenses: List[Expense] = []

    def parse_csv(self, filepath: str) -> List[Expense]:
        """解析 CSV 文件"""
        expenses = []
        with open(filepath, "r", encoding="utf-8-sig") as f:
            # 检测是否有表头
            first_line = f.readline().strip()
            f.seek(0)

            has_header = False
            if first_line:
                # 检查第一行是否包含常见表头关键词
                header_keywords = ["date", "日期", "amount", "金额", "category", "类别", "描述", "description"]
                if any(kw in first_line.lower() for kw in header_keywords):
                    has_header = True

            if has_header:
                reader = csv.DictReader(f)
                for row in reader:
                    expense = self._parse_csv_row(row)
                    if expense:
                        expenses.append(expense)
            else:
                # 无表头，按位置解析：date,amount,category,description,payment
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        expense = self._parse_plain_row(row)
                        if expense:
                            expenses.append(expense)

        return expenses

    def _parse_csv_row(self, row: dict) -> Optional[Expense]:
        """解析 CSV 行（DictReader）"""
        # 兼容不同的列名
        date_str = row.get("date") or row.get("日期") or row.get("time") or ""
        amount_str = row.get("amount") or row.get("金额") or row.get("money") or "0"
        category = row.get("category") or row.get("类别") or row.get("分类") or ""
        description = row.get("description") or row.get("描述") or row.get("备注") or row.get("item") or ""
        payment = row.get("payment") or row.get("支付方式") or row.get("method") or ""
        exp_type = row.get("type") or row.get("类型") or ""

        try:
            amount = float(amount_str)
        except (ValueError, TypeError):
            return None

        if amount == 0:
            return None

        date = self._normalize_date(date_str)
        if not date:
            date = date.today().strftime("%Y-%m-%d") if hasattr(date, 'today') else "2026-01-01"

        # 判断收入/支出
        if not exp_type:
            exp_type = self._detect_type(description, amount)

        # 自动分类
        if not category or category == "其他":
            category, subcategory = self._auto_categorize(description, amount)
        else:
            subcategory = row.get("subcategory") or row.get("子类别") or ""

        return Expense(
            date=date,
            amount=abs(amount),
            type=exp_type,
            category=category,
            subcategory=subcategory,
            description=description,
            payment_method=payment,
            raw_text=",".join(str(v) for v in row.values()),
        )

    def _parse_plain_row(self, row: list) -> Optional[Expense]:
        """解析无表头的 CSV 行"""
        if len(row) < 2:
            return None

        date_str = row[0].strip()
        amount_str = row[1].strip()
        category = row[2].strip() if len(row) > 2 else ""
        description = row[3].strip() if len(row) > 3 else ""
        payment = row[4].strip() if len(row) > 4 else ""

        try:
            amount = float(amount_str)
        except ValueError:
            return None

        date = self._normalize_date(date_str)
        exp_type = self._detect_type(description, amount)

        if not category:
            category, subcategory = self._auto_categorize(description, amount)
        else:
            subcategory = ""

        return Expense(
            date=date,
            amount=abs(amount),
            type=exp_type,
            category=category,
            subcategory=subcategory,
            description=description,
            payment_method=payment,
            raw_text=" ".join(row),
        )

    def parse_text(self, text: str) -> List[Expense]:
        """解析纯文本格式（每行一笔）"""
        expenses = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            expense = self._parse_text_line(line)
            if expense:
                expenses.append(expense)
        return expenses

    def _parse_text_line(self, line: str) -> Optional[Expense]:
        """解析单行文本记录"""
        # 匹配日期
        date_match = re.search(
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{1,2}[-/月]\d{1,2}日?|\d{1,2}/\d{1,2})',
            line
        )
        date_str = date_match.group(1) if date_match else ""
        rest = line[date_match.end():].strip() if date_match else line

        # 匹配金额
        amount_match = re.search(r'(\d+\.?\d*)\s*(?:元|块|rmb|￥|¥)?', rest, re.IGNORECASE)
        if not amount_match:
            return None

        amount = float(amount_match.group(1))
        # 描述是去掉日期和金额后的部分
        description = rest[:amount_match.start()].strip() + rest[amount_match.end():].strip()
        description = description.strip(" -—,，。.")

        date = self._normalize_date(date_str)
        exp_type = self._detect_type(description, amount)
        category, subcategory = self._auto_categorize(description, amount)

        return Expense(
            date=date,
            amount=amount,
            type=exp_type,
            category=category,
            subcategory=subcategory,
            description=description or line,
            raw_text=line,
        )

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """将各种日期格式统一为 YYYY-MM-DD"""
        if not date_str:
            return date.today().strftime("%Y-%m-%d")

        date_str = date_str.strip()

        # 2026-09-01 / 2026/09/01 / 2026年9月1日
        m = re.match(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', date_str)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

        # 09-01 / 9/1 / 9月1日
        m = re.match(r'(\d{1,2})[-/月](\d{1,2})', date_str)
        if m:
            month = int(m.group(1))
            day = int(m.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"2026-{month:02d}-{day:02d}"

        return date.today().strftime("%Y-%m-%d")

    @staticmethod
    def _detect_type(description: str, amount: float) -> str:
        """判断是收入还是支出"""
        desc_lower = description.lower()
        for kw in INCOME_KEYWORDS:
            if kw in desc_lower:
                return "收入"
        # 负数金额视为收入（退款等）
        if amount < 0:
            return "收入"
        return "支出"

    @staticmethod
    def _auto_categorize(description: str, amount: float) -> Tuple[str, str]:
        """根据描述自动分类"""
        if not description:
            return "其他", ""

        desc_lower = description.lower()

        # 先匹配商家
        for merchant, (cat, subcat) in MERCHANT_CATEGORY.items():
            if merchant in desc_lower:
                return cat, subcat

        # 再匹配关键词
        best_category = "其他"
        best_subcategory = ""
        best_score = 0

        for cat_name, cat_info in CATEGORY_KEYWORDS.items():
            for subcat_name, keywords in cat_info["subcategories"].items():
                for kw in keywords:
                    if kw in desc_lower:
                        score = len(kw)  # 更长的关键词匹配更精确
                        if score > best_score:
                            best_score = score
                            best_category = cat_name
                            best_subcategory = subcat_name

        return best_category, best_subcategory


# ============================================================
# 分析器
# ============================================================

class ExpenseAnalyzer:
    """消费记录分析器"""

    def __init__(self, expenses: List[Expense]):
        self.expenses = expenses
        self.result = AnalysisResult()

    def analyze(self, month: Optional[str] = None, week: Optional[str] = None,
                budget: Optional[float] = None) -> AnalysisResult:
        """执行分析"""
        # 过滤时间段
        filtered = self.expenses
        if month:
            filtered = [e for e in filtered if e.date.startswith(month)]
            self.result.period = f"{month} 月度"
        elif week:
            # 简化处理：按周过滤需要计算日期范围
            filtered = [e for e in filtered if e.date.startswith(week[:4])]
            self.result.period = f"{week} 周度"
        else:
            self.result.period = "全部数据"

        if not filtered:
            self.result.warnings.append("所选时间段内没有消费记录")
            return self.result

        # 统计收入支出
        expenses_only = [e for e in filtered if e.type == "支出"]
        income_only = [e for e in filtered if e.type == "收入"]

        self.result.total_expense = sum(e.amount for e in expenses_only)
        self.result.total_income = sum(e.amount for e in income_only)
        self.result.balance = self.result.total_income - self.result.total_expense
        self.result.expense_count = len(expenses_only)
        self.result.income_count = len(income_only)

        # 计算天数
        dates = sorted(set(e.date for e in filtered))
        if dates:
            first = datetime.strptime(dates[0], "%Y-%m-%d")
            last = datetime.strptime(dates[-1], "%Y-%m-%d")
            self.result.days_in_period = (last - first).days + 1
        else:
            self.result.days_in_period = 1

        if self.result.days_in_period > 0:
            self.result.daily_avg = self.result.total_expense / self.result.days_in_period

        # 最大单笔支出
        if expenses_only:
            self.result.max_expense = max(expenses_only, key=lambda e: e.amount)

        # 分类统计
        for e in expenses_only:
            if e.category not in self.result.categories:
                icon = CATEGORY_KEYWORDS.get(e.category, {}).get("icon", "📦")
                self.result.categories[e.category] = CategoryStat(name=f"{icon} {e.category}")
            cat = self.result.categories[e.category]
            cat.total += e.amount
            cat.count += 1
            cat.max_single = max(cat.max_single, e.amount)
            cat.expenses.append(e)
            if e.category == "其他":
                self.result.uncategorized.append(e)

        # 计算占比和日均
        for cat in self.result.categories.values():
            cat.percentage = (cat.total / self.result.total_expense * 100) if self.result.total_expense > 0 else 0
            cat.daily_avg = cat.total / self.result.days_in_period if self.result.days_in_period > 0 else 0

        # 每日支出
        daily = defaultdict(float)
        for e in expenses_only:
            daily[e.date] += e.amount
        self.result.daily_expenses = dict(sorted(daily.items()))

        # Top 5 支出
        self.result.top_expenses = sorted(expenses_only, key=lambda e: e.amount, reverse=True)[:5]

        # 预算分析
        if budget and budget > 0:
            self.result.budget = budget
            self.result.budget_remaining = budget - self.result.total_expense
            self.result.budget_usage_pct = (self.result.total_expense / budget * 100) if budget > 0 else 0

        # 异常检测
        self._detect_anomalies()

        return self.result

    def _detect_anomalies(self):
        """检测异常消费"""
        # 单笔超过总支出15%
        if self.result.max_expense and self.result.total_expense > 0:
            pct = self.result.max_expense.amount / self.result.total_expense * 100
            if pct > 15:
                self.result.warnings.append(
                    f"大额支出提醒：{self.result.max_expense.date} "
                    f"{self.result.max_expense.description} ¥{self.result.max_expense.amount:.2f}，"
                    f"占总支出 {pct:.1f}%"
                )

        # 某类别占比超过40%
        for cat in self.result.categories.values():
            if cat.percentage > 40:
                self.result.warnings.append(
                    f"类别集中：{cat.name} 占比 {cat.percentage:.1f}%，"
                    f"支出 ¥{cat.total:.2f}，建议关注"
                )

        # 未分类支出
        if self.result.uncategorized:
            self.result.warnings.append(
                f"有 {len(self.result.uncategorized)} 笔支出未明确分类（归入「其他」），"
                f"建议补充描述以便更精确分析"
            )


# ============================================================
# 报告格式化
# ============================================================

def format_report(result: AnalysisResult) -> str:
    """格式化为文本报告"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"消费分析报告 - {result.period}")
    lines.append("=" * 60)
    lines.append("")

    # 概览
    lines.append("【本月概览】")
    lines.append(f"  总收入: ¥{result.total_income:,.2f} ({result.income_count} 笔)")
    lines.append(f"  总支出: ¥{result.total_expense:,.2f} ({result.expense_count} 笔)")
    lines.append(f"  结余:   ¥{result.balance:,.2f}")
    lines.append(f"  日均支出: ¥{result.daily_avg:,.2f} (共 {result.days_in_period} 天)")
    if result.max_expense:
        lines.append(f"  最大单笔: ¥{result.max_expense.amount:,.2f} ({result.max_expense.description})")
    if result.budget is not None:
        status = "超支" if result.budget_remaining < 0 else "正常"
        lines.append(f"  预算执行: ¥{result.total_expense:,.2f} / ¥{result.budget:,.2f} "
                     f"({result.budget_usage_pct:.1f}%) - {status}")
        if result.budget_remaining is not None and result.budget_remaining >= 0:
            lines.append(f"  剩余预算: ¥{result.budget_remaining:,.2f}")
    lines.append("")

    # 分类统计
    lines.append("【分类支出】")
    sorted_cats = sorted(result.categories.values(), key=lambda c: c.total, reverse=True)
    for i, cat in enumerate(sorted_cats, 1):
        bar = "█" * int(cat.percentage / 2) + "░" * (25 - int(cat.percentage / 2))
        lines.append(f"  {i:2d}. {cat.name:<12} ¥{cat.total:>9,.2f}  "
                     f"{cat.percentage:>5.1f}%  {bar}  ({cat.count}笔)")
    lines.append("")

    # 每日趋势（只显示有支出的日期）
    lines.append("【每日支出趋势】")
    for d, amount in list(result.daily_expenses.items())[:10]:
        bar = "▓" * min(int(amount / result.daily_avg), 30) if result.daily_avg > 0 else ""
        lines.append(f"  {d}  ¥{amount:>8,.2f}  {bar}")
    if len(result.daily_expenses) > 10:
        lines.append(f"  ... 共 {len(result.daily_expenses)} 天有支出记录")
    lines.append("")

    # Top 5
    lines.append("【大额支出 Top 5】")
    for i, e in enumerate(result.top_expenses, 1):
        pct = e.amount / result.total_expense * 100 if result.total_expense > 0 else 0
        lines.append(f"  {i}. {e.date}  {e.category}>{e.subcategory or '—'}  "
                     f"¥{e.amount:>8,.2f}  ({pct:.1f}%)  {e.description}")
    lines.append("")

    # 异常提醒
    if result.warnings:
        lines.append("【⚠ 异常提醒】")
        for w in result.warnings:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    # 省钱建议（基于数据）
    lines.append("【消费洞察与建议】")
    suggestions = _generate_suggestions(result)
    for i, s in enumerate(suggestions, 1):
        lines.append(f"  {i}. {s}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("* 本报告由消费记录自动生成，省钱建议仅供参考，不构成投资建议。")
    lines.append("=" * 60)

    return "\n".join(lines)


def _generate_suggestions(result: AnalysisResult) -> List[str]:
    """基于数据生成省钱建议"""
    suggestions = []

    # 餐饮占比过高
    food = result.categories.get("🍜 餐饮") or result.categories.get("餐饮")
    if food and food.percentage > 30:
        suggestions.append(
            f"餐饮支出占比 {food.percentage:.1f}%（¥{food.total:,.2f}），"
            f"建议减少外卖频次，每周自己做饭 2-3 次，预计可省 ¥{food.total * 0.15:,.0f}/月"
        )

    # 购物占比过高
    shopping = result.categories.get("🛒 购物") or result.categories.get("购物")
    if shopping and shopping.percentage > 20:
        suggestions.append(
            f"购物支出占比 {shopping.percentage:.1f}%（¥{shopping.total:,.2f}），"
            f"建议购物前列清单，设置 24 小时冷静期，避免冲动消费"
        )

    # 娱乐占比过高
    ent = result.categories.get("🎮 娱乐") or result.categories.get("娱乐")
    if ent and ent.percentage > 15:
        suggestions.append(
            f"娱乐支出占比 {ent.percentage:.1f}%（¥{ent.total:,.2f}），"
            f"建议清理不常用的会员订阅，选择免费替代活动"
        )

    # 交通打车
    transport = result.categories.get("🚇 交通") or result.categories.get("交通")
    if transport:
        taxi_count = sum(1 for e in transport.expenses if e.subcategory == "打车")
        if taxi_count >= 5:
            suggestions.append(
                f"本月打车 {taxi_count} 次，建议短途改用公共交通或共享单车，"
                f"预计可省 ¥{taxi_count * 15:,.0f}/月"
            )

    # 通用建议
    if not suggestions:
        suggestions.append("本月消费结构较为均衡，继续保持记账习惯，定期复盘消费趋势")

    # 预算建议
    if result.budget and result.budget_remaining is not None and result.budget_remaining < 0:
        suggestions.append(
            f"⚠ 本月已超支 ¥{abs(result.budget_remaining):,.2f}，"
            f"建议下月压缩非必要支出，优先保障必要开支"
        )

    return suggestions


def format_json(result: AnalysisResult) -> str:
    """格式化为 JSON"""
    data = {
        "period": result.period,
        "summary": {
            "total_income": round(result.total_income, 2),
            "total_expense": round(result.total_expense, 2),
            "balance": round(result.balance, 2),
            "expense_count": result.expense_count,
            "income_count": result.income_count,
            "days_in_period": result.days_in_period,
            "daily_avg": round(result.daily_avg, 2),
        },
        "categories": {
            name: {
                "total": round(cat.total, 2),
                "count": cat.count,
                "percentage": round(cat.percentage, 2),
                "daily_avg": round(cat.daily_avg, 2),
                "max_single": round(cat.max_single, 2),
            }
            for name, cat in result.categories.items()
        },
        "daily_expenses": {d: round(a, 2) for d, a in result.daily_expenses.items()},
        "top_expenses": [
            {
                "date": e.date,
                "amount": round(e.amount, 2),
                "category": e.category,
                "subcategory": e.subcategory,
                "description": e.description,
            }
            for e in result.top_expenses
        ],
        "budget": {
            "total": result.budget,
            "spent": round(result.total_expense, 2),
            "remaining": round(result.budget_remaining, 2) if result.budget_remaining is not None else None,
            "usage_pct": round(result.budget_usage_pct, 2) if result.budget_usage_pct is not None else None,
        } if result.budget else None,
        "warnings": result.warnings,
        "uncategorized_count": len(result.uncategorized),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="个人记账与消费分析工具 - 解析消费记录并生成统计报告"
    )
    parser.add_argument("--input", "-i", help="输入文件路径（CSV 或文本，默认从 stdin 读取）")
    parser.add_argument("--month", "-m", help="过滤月份，格式 YYYY-MM（如 2026-09）")
    parser.add_argument("--week", "-w", help="过滤周，格式 YYYY-Www（如 2026-W37）")
    parser.add_argument("--budget", "-b", type=float, help="本月总预算（元）")
    parser.add_argument("--format", "-f", choices=["report", "json"], default="report",
                        help="输出格式（默认 report）")
    args = parser.parse_args()

    # 读取输入
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"错误：文件 '{args.input}' 不存在", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误：读取文件失败 - {e}", file=sys.stderr)
            sys.exit(1)

        # 根据扩展名判断格式
        if args.input.lower().endswith(".csv"):
            expense_parser = ExpenseParser()
            expenses = expense_parser.parse_csv(args.input)
        else:
            expense_parser = ExpenseParser()
            expenses = expense_parser.parse_text(content)
    else:
        content = sys.stdin.read()
        if not content.strip():
            print("错误：输入为空，请提供消费记录", file=sys.stderr)
            print("\n用法示例：", file=sys.stderr)
            print("  python3 analyze_expenses.py --input expenses.csv --month 2026-09", file=sys.stderr)
            print("  cat expenses.txt | python3 analyze_expenses.py --budget 8000", file=sys.stderr)
            sys.exit(1)
        expense_parser = ExpenseParser()
        expenses = expense_parser.parse_text(content)

    if not expenses:
        print("错误：未能解析出任何消费记录，请检查输入格式", file=sys.stderr)
        sys.exit(1)

    # 分析
    analyzer = ExpenseAnalyzer(expenses)
    result = analyzer.analyze(month=args.month, week=args.week, budget=args.budget)

    # 输出
    if args.format == "json":
        print(format_json(result))
    else:
        print(format_report(result))


if __name__ == "__main__":
    main()
