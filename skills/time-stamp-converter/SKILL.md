---
name: time-stamp-converter
description: "时间戳转换助手。Unix 时间戳（秒/毫秒）与人类可读日期互转，支持多时区（UTC/北京时间/纽约/伦敦/东京等）、批量转换、当前时间戳、多种日期格式解析（ISO 8601、中文日期、RFC 2822 等）、时间差计算、日期加减。纯 Python 标准库实现，无外部依赖。适用于日志时间戳解析、API 时间字段调试、跨时区协作、数据库时间字段转换等场景。"
---

# 时间戳转换助手

## 触发场景

当用户出现以下意图时使用本技能：

- "这个时间戳是多少" / "1700000000 是什么时间" / "时间戳转换"
- "现在的时间戳" / "当前 unix 时间"
- "北京时间转 UTC" / "纽约时间现在几点" / "时区转换"
- "日期转时间戳" / "2024-01-01 转时间戳"
- "批量转换时间戳" / "这些时间戳分别是多少"
- "两个时间差多少" / "距离某日期还有多久"
- "日志里的时间戳" / "1699999999999 毫秒转日期"

## 核心功能

| 功能 | 说明 |
|---|---|
| 时间戳→日期 | 秒/毫秒自动识别，输出多种格式 |
| 日期→时间戳 | 支持 ISO 8601、中文日期、RFC 2822 等 |
| 多时区 | UTC、北京时间、纽约、伦敦、东京、悉尼等 |
| 当前时间戳 | 秒/毫秒/微秒 |
| 批量转换 | 从文件或命令行批量处理 |
| 时间差计算 | 两个时间戳之间的天数/小时/分钟 |
| 日期加减 | N 天/小时/分钟前后的时间戳 |
| 纯标准库 | 无外部依赖 |

## 使用方法

### 命令行工具

```bash
# 时间戳转日期（自动识别秒/毫秒）
python3 scripts/convert_ts.py --ts 1700000000

# 指定毫秒
python3 scripts/convert_ts.py --ts 1700000000000 --unit ms

# 日期转时间戳
python3 scripts/convert_ts.py --date "2024-01-01 00:00:00"

# 中文日期
python3 scripts/convert_ts.py --date "2024年1月1日 12点30分"

# 指定时区输出
python3 scripts/convert_ts.py --ts 1700000000 --timezone Asia/Shanghai

# 当前时间戳
python3 scripts/convert_ts.py --now

# 批量转换（从文件，每行一个时间戳）
python3 scripts/convert_ts.py --batch timestamps.txt

# 时间差计算
python3 scripts/convert_ts.py --diff 1700000000 1700100000

# 日期加减（3天后的时间戳）
python3 scripts/convert_ts.py --date "2024-01-01" --add-days 3

# 输出所有常用时区
python3 scripts/convert_ts.py --ts 1700000000 --all-timezones
```

### 作为模块调用

```python
from convert_ts import ts_to_date, date_to_ts, get_current_ts, time_diff

# 时间戳转日期
result = ts_to_date(1700000000, timezone="Asia/Shanghai")
print(result["formatted"])  # 2023-11-15 06:13:20

# 日期转时间戳
ts = date_to_ts("2024-01-01 00:00:00", timezone="Asia/Shanghai")

# 当前时间戳
now = get_current_ts(unit="s")

# 时间差
diff = time_diff(1700000000, 1700100000)
print(f"{diff['days']}天 {diff['hours']}小时 {diff['minutes']}分钟")
```

## 操作步骤

1. **确定输入**：用户提供时间戳或日期字符串
2. **自动识别**：判断是秒还是毫秒（10位=秒，13位=毫秒）
3. **确定时区**：默认北京时间，可指定其他时区
4. **执行转换**：运行脚本，捕获输出
5. **报告结果**：展示转换结果，包含多种格式和时区

## 输出规范

- 时间戳转日期时同时输出：本地时间、UTC 时间、ISO 8601 格式、RFC 2822 格式
- 日期转时间戳时同时输出：秒、毫秒、微秒
- 时间差输出：天、小时、分钟、秒（人类可读）
- 时区使用 IANA 标准名称（Asia/Shanghai、America/New_York 等）

## 注意事项

- 纯 Python 标准库实现，使用 `datetime` 和 `time` 模块
- 时区支持通过 `zoneinfo`（Python 3.9+）实现
- 毫秒时间戳为 13 位数字，秒为 10 位，自动识别
- 中文日期格式支持："2024年1月1日"、"2024/1/1"、"2024-1-1" 等
- 不支持夏令时自动切换（使用 IANA 时区数据库，系统需安装 tzdata）
