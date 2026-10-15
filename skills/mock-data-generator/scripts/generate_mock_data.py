#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
模拟数据生成脚本

功能：
- 支持 30+ 种数据字段（姓名、邮箱、手机号、身份证号、地址、日期、数字等）
- 支持中英文双语数据风格
- 支持 CSV、JSON、SQL INSERT 三种输出格式
- 支持 8 种预设模板（user/customer/employee/order/product/article/log/student）
- 支持自定义字段组合、数据量、随机种子、输出文件
- 纯 Python 标准库，无外部依赖

用法：
  python3 generate_mock_data.py --template user --count 10
  python3 generate_mock_data.py --fields id,name,email --count 50 --format json
  python3 generate_mock_data.py --template order --count 20 --format sql --table orders
  python3 generate_mock_data.py --list
"""

import argparse
import csv
import io
import json
import random
import sys
import uuid
from datetime import datetime, timedelta


# ============================================================
# 数据词库
# ============================================================

# 中文姓氏
ZH_SURNAMES = [
    "王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
    "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
]

# 中文名字（男）
ZH_MALE_NAMES = [
    "伟", "强", "磊", "军", "洋", "勇", "艳", "杰", "涛", "明",
    "超", "辉", "鹏", "华", "飞", "鑫", "波", "斌", "宇", "浩",
    "凯", "健", "俊", "帆", "博", "威", "龙", "刚", "建国", "建华",
]

# 中文名字（女）
ZH_FEMALE_NAMES = [
    "芳", "娜", "敏", "静", "丽", "艳", "娟", "霞", "秀英", "燕",
    "玲", "桂英", "玉兰", "萍", "慧", "红", "婷", "雪", "倩", "琳",
    "颖", "佳", "悦", "璐", "瑶", "薇", "欣", "怡", "雯", "菲菲",
]

# 英文名字（男）
EN_MALE_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard",
    "Joseph", "Thomas", "Charles", "Christopher", "Daniel", "Matthew",
    "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua",
    "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward",
    "Jason", "Jeffrey", "Ryan",
]

# 英文名字（女）
EN_FEMALE_NAMES = [
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan",
    "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Margaret", "Betty",
    "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna", "Michelle",
    "Carol", "Amanda", "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon",
    "Laura", "Cynthia",
]

# 英文姓氏
EN_SURNAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson",
]

# 中国城市
ZH_CITIES = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉",
    "西安", "重庆", "天津", "苏州", "长沙", "郑州", "青岛", "大连",
    "宁波", "厦门", "福州", "济南", "哈尔滨", "沈阳", "长春", "石家庄",
    "太原", "合肥", "南昌", "昆明", "贵阳", "南宁",
]

# 中国省份
ZH_PROVINCES = [
    "北京市", "上海市", "广东省", "浙江省", "江苏省", "四川省", "湖北省",
    "陕西省", "重庆市", "天津市", "山东省", "湖南省", "河南省", "辽宁省",
    "福建省", "黑龙江省", "吉林省", "河北省", "山西省", "安徽省",
]

# 中国区县/路名前缀
ZH_DISTRICTS = [
    "朝阳区", "海淀区", "西城区", "东城区", "丰台区", "浦东新区", "黄浦区",
    "静安区", "徐汇区", "天河区", "越秀区", "南山区", "福田区", "西湖区",
    "鼓楼区", "武侯区", "锦江区", "洪山区", "雁塔区", "渝中区",
]

ZH_STREETS = [
    "中山路", "人民路", "解放路", "建设路", "和平路", "光明路", "文化路",
    "科技路", "创业路", "学府路", "长安街", "南京路", "北京路", "上海路",
    "广州大道", "深南大道", "天府大道", "光谷大道",
]

# 美国城市
EN_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
    "Seattle", "Denver", "Washington", "Boston", "Nashville", "Portland",
    "Las Vegas", "Detroit",
]

# 美国州
EN_STATES = [
    "California", "Texas", "Florida", "New York", "Pennsylvania", "Illinois",
    "Ohio", "Georgia", "North Carolina", "Michigan", "New Jersey", "Virginia",
    "Washington", "Arizona", "Massachusetts", "Tennessee", "Indiana", "Missouri",
    "Maryland", "Wisconsin", "Colorado", "Minnesota", "South Carolina",
    "Alabama", "Louisiana",
]

EN_STREETS = [
    "Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Pine Rd", "Elm St",
    "Washington Blvd", "Park Ave", "Lake Dr", "Hill St", "River Rd",
    "Sunset Blvd", "Highland Ave", "Forest Ln", "Meadow Dr", "Spring St",
    "Court St", "Church St", "Mill Rd", "Union St",
]

# 邮箱域名
EMAIL_DOMAINS = [
    "example.com", "test.com", "sample.org", "demo.net", "mock.io",
    "mail.com", "email.com", "inbox.com", "post.com", "message.com",
]

# 公司名前缀
ZH_COMPANY_PREFIXES = [
    "华", "中", "大", "新", "金", "银", "宝", "瑞", "盛", "恒",
    "泰", "昌", "茂", "丰", "鑫", "源", "通", "达", "信", "和",
]

ZH_COMPANY_SUFFIXES = [
    "科技有限公司", "信息技术有限公司", "网络科技有限公司", "电子商务有限公司",
    "数据科技有限公司", "智能科技有限公司", "软件开发有限公司", "咨询有限公司",
    "贸易有限公司", "实业有限公司", "集团有限公司", "控股有限公司",
]

EN_COMPANY_PREFIXES = [
    "Acme", "Global", "Prime", "Elite", "Apex", "Summit", "Vanguard",
    "Pioneer", "Quantum", "Nexus", "Vertex", "Horizon", "Zenith", "Atlas",
    "Catalyst", "Synergy", "Dynamic", "Innovative", "Strategic", "United",
]

EN_COMPANY_SUFFIXES = [
    "Inc", "LLC", "Corp", "Ltd", "Group", "Technologies", "Solutions",
    "Systems", "Labs", "Ventures", "Partners", "Holdings", "Industries",
    "Enterprises", "Associates",
]

# 职位
ZH_JOBS = [
    "软件工程师", "高级软件工程师", "前端开发工程师", "后端开发工程师",
    "全栈开发工程师", "测试工程师", "产品经理", "项目经理", "UI设计师",
    "数据分析师", "数据科学家", "算法工程师", "运维工程师", "架构师",
    "技术总监", "CTO", "CEO", "市场经理", "销售经理", "人力资源专员",
    "财务专员", "行政助理", "运营专员", "客服专员", "法务专员",
]

EN_JOBS = [
    "Software Engineer", "Senior Software Engineer", "Frontend Developer",
    "Backend Developer", "Full Stack Developer", "QA Engineer", "Product Manager",
    "Project Manager", "UI Designer", "Data Analyst", "Data Scientist",
    "Algorithm Engineer", "DevOps Engineer", "Architect", "CTO", "CEO",
    "Marketing Manager", "Sales Manager", "HR Specialist", "Accountant",
    "Administrative Assistant", "Operations Specialist", "Customer Support",
    "Legal Counsel",
]

# 部门
ZH_DEPARTMENTS = [
    "技术部", "产品部", "设计部", "市场部", "销售部", "人力资源部",
    "财务部", "行政部", "运营部", "客服部", "法务部", "数据部",
]

EN_DEPARTMENTS = [
    "Engineering", "Product", "Design", "Marketing", "Sales", "Human Resources",
    "Finance", "Administration", "Operations", "Customer Support", "Legal",
    "Data",
]

# 产品分类
ZH_CATEGORIES = [
    "电子产品", "服装鞋帽", "食品饮料", "家居用品", "美妆护肤", "图书文具",
    "运动户外", "母婴用品", "汽车用品", "数码配件", "家用电器", "珠宝首饰",
]

EN_CATEGORIES = [
    "Electronics", "Clothing", "Food & Beverage", "Home & Garden", "Beauty",
    "Books", "Sports & Outdoors", "Baby", "Automotive", "Accessories",
    "Appliances", "Jewelry",
]

# 订单状态
ZH_ORDER_STATUSES = ["待付款", "待发货", "已发货", "已完成", "已取消", "退款中"]
EN_ORDER_STATUSES = ["pending", "processing", "shipped", "completed", "cancelled", "refunded"]

# 文章分类
ZH_ARTICLE_CATEGORIES = ["科技", "财经", "体育", "娱乐", "教育", "健康", "旅游", "美食"]
EN_ARTICLE_CATEGORIES = ["Tech", "Finance", "Sports", "Entertainment", "Education", "Health", "Travel", "Food"]

# 颜色
ZH_COLORS = ["红色", "橙色", "黄色", "绿色", "蓝色", "紫色", "黑色", "白色", "灰色", "粉色"]
EN_COLORS = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Black", "White", "Gray", "Pink"]

# 中文随机词
ZH_WORDS = [
    "科技", "创新", "发展", "未来", "智能", "数据", "网络", "数字", "信息", "系统",
    "平台", "服务", "产品", "用户", "体验", "设计", "开发", "测试", "运营", "管理",
    "市场", "品牌", "营销", "销售", "客户", "团队", "合作", "项目", "目标", "计划",
]

# 英文随机词
EN_WORDS = [
    "technology", "innovation", "development", "future", "intelligent", "data",
    "network", "digital", "information", "system", "platform", "service",
    "product", "user", "experience", "design", "development", "testing",
    "operations", "management", "market", "brand", "marketing", "sales",
    "customer", "team", "collaboration", "project", "goal", "plan",
]

# HTTP 方法
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# HTTP 状态码
HTTP_STATUSES = [200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503]

# URL 路径
URL_PATHS = [
    "/api/users", "/api/products", "/api/orders", "/api/auth/login",
    "/api/auth/register", "/api/search", "/api/upload", "/api/download",
    "/api/profile", "/api/settings", "/api/notifications", "/api/messages",
    "/home", "/about", "/contact", "/dashboard", "/admin", "/login",
]

# 专业
ZH_MAJORS = [
    "计算机科学与技术", "软件工程", "电子信息工程", "自动化", "机械工程",
    "土木工程", "建筑学", "数学与应用数学", "物理学", "化学", "生物学",
    "经济学", "金融学", "管理学", "市场营销", "会计学", "法学", "英语",
    "汉语言文学", "新闻传播学",
]

EN_MAJORS = [
    "Computer Science", "Software Engineering", "Electrical Engineering",
    "Mechanical Engineering", "Civil Engineering", "Architecture", "Mathematics",
    "Physics", "Chemistry", "Biology", "Economics", "Finance", "Management",
    "Marketing", "Accounting", "Law", "English", "History", "Psychology",
    "Sociology",
]

# 学校
ZH_SCHOOLS = [
    "清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学", "南京大学",
    "中国科学技术大学", "哈尔滨工业大学", "西安交通大学", "华中科技大学",
    "武汉大学", "中山大学", "四川大学", "吉林大学", "山东大学",
]

EN_SCHOOLS = [
    "MIT", "Stanford University", "Harvard University", "Caltech",
    "University of Chicago", "Princeton University", "Yale University",
    "Columbia University", "UC Berkeley", "Cornell University",
    "University of Michigan", "Carnegie Mellon University",
]

# Lorem Ipsum 句子（英文）
LOREM_SENTENCES = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum.",
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia.",
    "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit.",
    "Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet.",
    "Consectetur, adipisci velit, sed quia non numquam eius modi tempora.",
    "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis.",
    "Praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias.",
]

# 中文句子
ZH_SENTENCES = [
    "这是一段用于测试的模拟文本内容。",
    "科技的发展正在深刻改变人们的生活方式。",
    "数据分析已经成为企业决策的重要依据。",
    "人工智能技术在各个领域得到了广泛应用。",
    "团队协作是项目成功的关键因素之一。",
    "用户体验设计需要关注每一个细节。",
    "持续学习是保持竞争力的重要途径。",
    "创新是推动社会进步的核心动力。",
    "优质的产品和服务是企业生存的根本。",
    "高效的沟通能够显著提升工作效率。",
]


# ============================================================
# 数据生成器
# ============================================================

class MockDataGenerator:
    """模拟数据生成器"""

    def __init__(self, lang="zh", seed=None):
        self.lang = lang
        self.rng = random.Random(seed)
        self._id_counter = 0

    def _next_id(self):
        self._id_counter += 1
        return self._id_counter

    def gen_id(self):
        return self._next_id()

    def gen_uuid(self):
        return str(uuid.UUID(int=self.rng.getrandbits(128), version=4))

    def gen_name(self):
        if self.lang == "zh":
            surname = self.rng.choice(ZH_SURNAMES)
            gender = self.rng.choice(["male", "female"])
            given = self.rng.choice(ZH_MALE_NAMES if gender == "male" else ZH_FEMALE_NAMES)
            return surname + given
        else:
            gender = self.rng.choice(["male", "female"])
            first = self.rng.choice(EN_MALE_NAMES if gender == "male" else EN_FEMALE_NAMES)
            last = self.rng.choice(EN_SURNAMES)
            return f"{first} {last}"

    def gen_gender(self):
        if self.lang == "zh":
            return self.rng.choice(["男", "女"])
        return self.rng.choice(["Male", "Female"])

    def gen_email(self, name=None):
        if name is None:
            name = self.gen_name()
        if self.lang == "zh":
            # 中文名字转拼音首字母（简化处理，用随机字符串）
            local = ''.join(self.rng.choices('abcdefghijklmnopqrstuvwxyz', k=self.rng.randint(5, 10)))
        else:
            parts = name.lower().replace(" ", ".")
            local = parts + str(self.rng.randint(1, 999))
        domain = self.rng.choice(EMAIL_DOMAINS)
        return f"{local}@{domain}"

    def gen_phone(self):
        if self.lang == "zh":
            prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                        "150", "151", "152", "153", "155", "156", "157", "158", "159",
                        "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
            return self.rng.choice(prefixes) + ''.join(self.rng.choices('0123456789', k=8))
        else:
            return f"+1-{self.rng.randint(200, 999)}-{self.rng.randint(200, 999)}-{self.rng.randint(1000, 9999)}"

    def gen_id_card(self):
        if self.lang != "zh":
            return ""
        # 前6位地区码（简化为北京等）
        area_codes = ["110101", "110105", "310101", "310104", "440101", "440301",
                      "330101", "320101", "510101", "420101"]
        area = self.rng.choice(area_codes)
        # 出生日期
        birth = self.gen_date()
        birth_compact = birth.replace("-", "")
        # 顺序码
        seq = str(self.rng.randint(1, 999)).zfill(3)
        # 校验码（简化计算）
        body = area + birth_compact + seq
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = "10X98765432"
        total = sum(int(body[i]) * weights[i] for i in range(17))
        check = check_codes[total % 11]
        return body + check

    def gen_address(self):
        if self.lang == "zh":
            city = self.rng.choice(ZH_CITIES)
            district = self.rng.choice(ZH_DISTRICTS)
            street = self.rng.choice(ZH_STREETS)
            number = self.rng.randint(1, 999)
            return f"{city}{district}{street}{number}号"
        else:
            number = self.rng.randint(1, 9999)
            street = self.rng.choice(EN_STREETS)
            city = self.rng.choice(EN_CITIES)
            state = self.rng.choice(EN_STATES)
            zip_code = self.rng.randint(10000, 99999)
            return f"{number} {street}, {city}, {state} {zip_code}"

    def gen_city(self):
        return self.rng.choice(ZH_CITIES if self.lang == "zh" else EN_CITIES)

    def gen_province(self):
        return self.rng.choice(ZH_PROVINCES if self.lang == "zh" else EN_STATES)

    def gen_country(self):
        return "中国" if self.lang == "zh" else "United States"

    def gen_zip_code(self):
        if self.lang == "zh":
            return str(self.rng.randint(100000, 999999))
        return str(self.rng.randint(10000, 99999))

    def gen_date(self):
        start = datetime.now() - timedelta(days=365 * 5)
        end = datetime.now()
        delta = end - start
        random_days = self.rng.randint(0, delta.days)
        return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

    def gen_datetime(self):
        start = datetime.now() - timedelta(days=365 * 5)
        end = datetime.now()
        delta = end - start
        random_seconds = self.rng.randint(0, int(delta.total_seconds()))
        return (start + timedelta(seconds=random_seconds)).strftime("%Y-%m-%d %H:%M:%S")

    def gen_timestamp(self):
        start = datetime(2020, 1, 1)
        end = datetime.now()
        delta = end - start
        return int((start + timedelta(seconds=self.rng.randint(0, int(delta.total_seconds())))).timestamp())

    def gen_age(self):
        return self.rng.randint(18, 80)

    def gen_company(self):
        if self.lang == "zh":
            prefix = self.rng.choice(ZH_COMPANY_PREFIXES)
            suffix = self.rng.choice(ZH_COMPANY_SUFFIXES)
            middle = self.rng.choice(["", "科技", "信息", "网络", "数据", "智能"])
            return f"{prefix}{middle}{suffix}"
        else:
            prefix = self.rng.choice(EN_COMPANY_PREFIXES)
            suffix = self.rng.choice(EN_COMPANY_SUFFIXES)
            return f"{prefix} {suffix}"

    def gen_job_title(self):
        return self.rng.choice(ZH_JOBS if self.lang == "zh" else EN_JOBS)

    def gen_department(self):
        return self.rng.choice(ZH_DEPARTMENTS if self.lang == "zh" else EN_DEPARTMENTS)

    def gen_salary(self):
        if self.lang == "zh":
            return self.rng.randint(5000, 50000)
        return self.rng.randint(30000, 150000)

    def gen_price(self):
        return round(self.rng.uniform(1, 10000), 2)

    def gen_quantity(self):
        return self.rng.randint(1, 100)

    def gen_boolean(self):
        return self.rng.choice([True, False])

    def gen_ip(self):
        return f"{self.rng.randint(1, 255)}.{self.rng.randint(0, 255)}.{self.rng.randint(0, 255)}.{self.rng.randint(1, 255)}"

    def gen_url(self):
        domain = self.rng.choice(EMAIL_DOMAINS)
        path = self.rng.choice(URL_PATHS)
        return f"https://www.{domain}{path}"

    def gen_color(self):
        return self.rng.choice(ZH_COLORS if self.lang == "zh" else EN_COLORS)

    def gen_hex_color(self):
        return "#{:06X}".format(self.rng.randint(0, 0xFFFFFF))

    def gen_word(self):
        return self.rng.choice(ZH_WORDS if self.lang == "zh" else EN_WORDS)

    def gen_sentence(self):
        if self.lang == "zh":
            return self.rng.choice(ZH_SENTENCES)
        return self.rng.choice(LOREM_SENTENCES)

    def gen_paragraph(self):
        num_sentences = self.rng.randint(3, 6)
        if self.lang == "zh":
            return ''.join(self.rng.choices(ZH_SENTENCES, k=num_sentences))
        return ' '.join(self.rng.choices(LOREM_SENTENCES, k=num_sentences))

    def gen_text(self):
        return self.gen_paragraph()

    # 模板专用字段
    def gen_user_id(self):
        return self.rng.randint(1, 10000)

    def gen_product_name(self):
        if self.lang == "zh":
            adj = self.rng.choice(["高端", "智能", "专业", "便携", "时尚", "经典", "新款", "限量"])
            noun = self.rng.choice(["手机", "电脑", "耳机", "手表", "相机", "键盘", "鼠标", "显示器"])
            return f"{adj}{noun}"
        else:
            adj = self.rng.choice(["Premium", "Smart", "Pro", "Portable", "Stylish", "Classic", "New", "Limited"])
            noun = self.rng.choice(["Phone", "Laptop", "Headphones", "Watch", "Camera", "Keyboard", "Mouse", "Monitor"])
            return f"{adj} {noun}"

    def gen_category(self):
        return self.rng.choice(ZH_CATEGORIES if self.lang == "zh" else EN_CATEGORIES)

    def gen_order_status(self):
        return self.rng.choice(ZH_ORDER_STATUSES if self.lang == "zh" else EN_ORDER_STATUSES)

    def gen_article_title(self):
        if self.lang == "zh":
            return f"{self.rng.choice(ZH_WORDS)}与{self.rng.choice(ZH_WORDS)}的{self.rng.choice(['研究', '分析', '应用', '探索', '实践'])}"
        return f"{self.rng.choice(EN_WORDS).title()} and {self.rng.choice(EN_WORDS).title()}: A {self.rng.choice(['Study', 'Analysis', 'Application', 'Exploration', 'Review'])}"

    def gen_sku(self):
        return ''.join(self.rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))

    def gen_grade(self):
        if self.lang == "zh":
            return self.rng.choice(["大一", "大二", "大三", "大四", "研一", "研二", "研三"])
        return self.rng.choice(["Freshman", "Sophomore", "Junior", "Senior", "Graduate"])

    def gen_major(self):
        return self.rng.choice(ZH_MAJORS if self.lang == "zh" else EN_MAJORS)

    def gen_school(self):
        return self.rng.choice(ZH_SCHOOLS if self.lang == "zh" else EN_SCHOOLS)

    def gen_hire_date(self):
        return self.gen_date()

    def gen_enrollment_date(self):
        return self.gen_date()

    def gen_views(self):
        return self.rng.randint(0, 100000)

    def gen_stock(self):
        return self.rng.randint(0, 1000)

    def gen_total(self, quantity=None, price=None):
        if quantity is None:
            quantity = self.gen_quantity()
        if price is None:
            price = self.gen_price()
        return round(quantity * price, 2)

    def gen_method(self):
        return self.rng.choice(HTTP_METHODS)

    def gen_status(self):
        return self.rng.choice(HTTP_STATUSES)

    def gen_response_time(self):
        return self.rng.randint(1, 5000)

    def gen_path(self):
        return self.rng.choice(URL_PATHS)


# ============================================================
# 字段映射
# ============================================================

FIELD_GENERATORS = {
    "id": lambda g: g.gen_id(),
    "uuid": lambda g: g.gen_uuid(),
    "name": lambda g: g.gen_name(),
    "email": lambda g: g.gen_email(),
    "phone": lambda g: g.gen_phone(),
    "id_card": lambda g: g.gen_id_card(),
    "address": lambda g: g.gen_address(),
    "city": lambda g: g.gen_city(),
    "province": lambda g: g.gen_province(),
    "country": lambda g: g.gen_country(),
    "zip_code": lambda g: g.gen_zip_code(),
    "date": lambda g: g.gen_date(),
    "datetime": lambda g: g.gen_datetime(),
    "timestamp": lambda g: g.gen_timestamp(),
    "age": lambda g: g.gen_age(),
    "gender": lambda g: g.gen_gender(),
    "company": lambda g: g.gen_company(),
    "job_title": lambda g: g.gen_job_title(),
    "department": lambda g: g.gen_department(),
    "salary": lambda g: g.gen_salary(),
    "price": lambda g: g.gen_price(),
    "quantity": lambda g: g.gen_quantity(),
    "boolean": lambda g: g.gen_boolean(),
    "ip": lambda g: g.gen_ip(),
    "url": lambda g: g.gen_url(),
    "color": lambda g: g.gen_color(),
    "hex_color": lambda g: g.gen_hex_color(),
    "text": lambda g: g.gen_text(),
    "word": lambda g: g.gen_word(),
    "sentence": lambda g: g.gen_sentence(),
    "paragraph": lambda g: g.gen_paragraph(),
    "user_id": lambda g: g.gen_user_id(),
    "product_name": lambda g: g.gen_product_name(),
    "category": lambda g: g.gen_category(),
    "order_status": lambda g: g.gen_order_status(),
    "article_title": lambda g: g.gen_article_title(),
    "sku": lambda g: g.gen_sku(),
    "grade": lambda g: g.gen_grade(),
    "major": lambda g: g.gen_major(),
    "school": lambda g: g.gen_school(),
    "hire_date": lambda g: g.gen_hire_date(),
    "enrollment_date": lambda g: g.gen_enrollment_date(),
    "views": lambda g: g.gen_views(),
    "stock": lambda g: g.gen_stock(),
    "total": lambda g: g.gen_total(),
    "method": lambda g: g.gen_method(),
    "status": lambda g: g.gen_status(),
    "response_time": lambda g: g.gen_response_time(),
    "path": lambda g: g.gen_path(),
    "publish_date": lambda g: g.gen_date(),
    "order_date": lambda g: g.gen_date(),
    "author": lambda g: g.gen_name(),
    "content": lambda g: g.gen_paragraph(),
    "description": lambda g: g.gen_sentence(),
}

# 预设模板
TEMPLATES = {
    "user": ["id", "name", "email", "phone", "gender", "age", "address", "city", "country"],
    "customer": ["id", "name", "email", "phone", "company", "job_title", "address", "city"],
    "employee": ["id", "name", "email", "phone", "job_title", "department", "salary", "hire_date"],
    "order": ["id", "user_id", "product_name", "quantity", "price", "total", "order_date", "order_status"],
    "product": ["id", "product_name", "category", "price", "stock", "description", "sku"],
    "article": ["id", "article_title", "author", "content", "publish_date", "category", "views"],
    "log": ["id", "timestamp", "ip", "method", "path", "status", "response_time"],
    "student": ["id", "name", "gender", "age", "grade", "major", "school", "enrollment_date"],
}


# ============================================================
# 输出格式化
# ============================================================

def format_csv(rows, fields):
    """格式化为 CSV"""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def format_json(rows):
    """格式化为 JSON"""
    return json.dumps(rows, ensure_ascii=False, indent=2)


def format_sql(rows, fields, table_name):
    """格式化为 SQL INSERT"""
    lines = []
    col_names = ", ".join(fields)
    for row in rows:
        values = []
        for f in fields:
            val = row[f]
            if isinstance(val, bool):
                values.append("TRUE" if val else "FALSE")
            elif isinstance(val, (int, float)):
                values.append(str(val))
            else:
                escaped = str(val).replace("'", "''")
                values.append(f"'{escaped}'")
        lines.append(f"INSERT INTO {table_name} ({col_names}) VALUES ({', '.join(values)});")
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="模拟数据生成器（支持 CSV/JSON/SQL，中英文双语）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --template user --count 10
  %(prog)s --fields id,name,email --count 50 --format json
  %(prog)s --template order --count 20 --format sql --table orders
  %(prog)s --list
        """,
    )

    parser.add_argument("--template", "-t", choices=list(TEMPLATES.keys()),
                        help="使用预设模板")
    parser.add_argument("--fields", "-f", help="自定义字段（逗号分隔）")
    parser.add_argument("--count", "-n", type=int, default=10,
                        help="生成数据量（默认 10）")
    parser.add_argument("--format", choices=["csv", "json", "sql"], default="csv",
                        help="输出格式（默认 csv）")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh",
                        help="数据语言（默认 zh 中文）")
    parser.add_argument("--seed", type=int, help="随机种子（用于复现）")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--table", default="mock_data",
                        help="SQL 表名（默认 mock_data）")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出所有可用字段和模板")

    args = parser.parse_args()

    # 列出可用字段和模板
    if args.list:
        print("=" * 60)
        print("可用字段（30+ 种）：")
        print("=" * 60)
        for field in sorted(FIELD_GENERATORS.keys()):
            print(f"  {field}")
        print()
        print("=" * 60)
        print("预设模板：")
        print("=" * 60)
        for name, fields in TEMPLATES.items():
            print(f"  {name:<12} {', '.join(fields)}")
        print("=" * 60)
        return

    # 确定字段
    if args.fields:
        fields = [f.strip() for f in args.fields.split(",") if f.strip()]
        invalid = [f for f in fields if f not in FIELD_GENERATORS]
        if invalid:
            print(f"错误：不支持的字段: {', '.join(invalid)}", file=sys.stderr)
            print(f"使用 --list 查看所有可用字段", file=sys.stderr)
            sys.exit(1)
    elif args.template:
        fields = TEMPLATES[args.template]
    else:
        parser.print_help()
        print("\n错误：请使用 --template 指定模板，或使用 --fields 指定字段", file=sys.stderr)
        sys.exit(1)

    # 生成数据
    generator = MockDataGenerator(lang=args.lang, seed=args.seed)
    rows = []
    for _ in range(args.count):
        row = {}
        for field in fields:
            row[field] = FIELD_GENERATORS[field](generator)
        rows.append(row)

    # 格式化输出
    if args.format == "csv":
        output = format_csv(rows, fields)
    elif args.format == "json":
        output = format_json(rows)
    elif args.format == "sql":
        output = format_sql(rows, fields, args.table)
    else:
        output = format_csv(rows, fields)

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ 已生成 {args.count} 条数据，保存到: {args.output}")
        print(f"   格式: {args.format.upper()}, 字段: {', '.join(fields)}")
    else:
        print(output)


if __name__ == "__main__":
    main()
