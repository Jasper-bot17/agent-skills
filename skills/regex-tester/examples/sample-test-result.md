# 示例：正则测试结果

> 本示例展示使用 `test_regex.py` 对 `sample-text.txt` 进行正则测试的典型输出。
> 示例文本包含联系人信息、日期、IP、URL、订单等多种可提取内容。

---

## 测试 1：提取手机号

**命令**：
```bash
python3 scripts/test_regex.py --pattern '1[3-9]\d{9}' --file examples/sample-text.txt
```

**结果**：
```
匹配数量：3

匹配 1：13812345678（张三）
匹配 2：13987654321（李四）
匹配 3：13611112222（王五）
```

---

## 测试 2：提取邮箱（带分组）

**命令**：
```bash
python3 scripts/test_regex.py --pattern '([\w.-]+)@([\w.-]+\.\w+)' --file examples/sample-text.txt
```

**结果**：
```
匹配数量：3

匹配 1：zhangsan@example.com
  分组 1：zhangsan（用户名）
  分组 2：example.com（域名）

匹配 2：lisi_test@company.cn
  分组 1：lisi_test
  分组 2：company.cn

匹配 3：wang.wu@test.org
  分组 1：wang.wu
  分组 2：test.org
```

---

## 测试 3：提取 URL

**命令**：
```bash
python3 scripts/test_regex.py --pattern 'https?://[\w.-]+(?::\d+)?(?:/[^\s]*)?' --file examples/sample-text.txt
```

**结果**：
```
匹配数量：2

匹配 1：https://www.example.com/docs
匹配 2：http://status.example.com:8080
```

---

## 测试 4：提取日期

**命令**：
```bash
python3 scripts/test_regex.py --pattern '\d{4}-\d{2}-\d{2}' --file examples/sample-text.txt
```

**结果**：
```
匹配数量：4

匹配 1：2024-03-15（会议时间）
匹配 2：2024-03-15（订单ORD...001）
匹配 3：2024-03-15（订单ORD...002）
匹配 4：2024-03-16（订单ORD...003）
```

---

## 测试 5：提取 IP 地址

**命令**：
```bash
python3 scripts/test_regex.py --pattern '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' --file examples/sample-text.txt
```

**结果**：
```
匹配数量：2

匹配 1：192.168.1.100（主服务器）
匹配 2：10.0.0.1（备用服务器）
```

---

## 测试 6：正则解释

**命令**：
```bash
python3 scripts/test_regex.py --pattern '(\d{4})-(\d{2})-(\d{2})' --explain
```

**结果**：
```
逐部分拆解：
  `(\d{4})`   捕获分组：4位数字（年）
  `-`         字面量：连字符
  `(\d{2})`   捕获分组：2位数字（月）
  `-`         字面量：连字符
  `(\d{2})`   捕获分组：2位数字（日）

整体含义：匹配 YYYY-MM-DD 格式的日期，并分别捕获年、月、日
```

---

## 测试 7：替换预览

**命令**：
```bash
python3 scripts/test_regex.py --pattern '\d{4}-\d{2}-\d{2}' --text "会议时间：2024-03-15" --replace '【\g<0>】'
```

**结果**：
```
原文本：会议时间：2024-03-15
替换后：会议时间：【2024-03-15】
```
