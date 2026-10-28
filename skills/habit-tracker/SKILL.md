---
name: habit-tracker
description: "习惯追踪器。记录和追踪日常习惯，支持添加习惯、每日打卡、连续天数统计（streak）、完成率分析、周/月概览仪表盘。使用 JSON 文件持久化存储，纯 Python 标准库实现。适用于养成学习、运动、阅读、早起等好习惯，追踪打卡记录和坚持情况。"
---

# 习惯追踪器（habit-tracker）

## 触发场景

当用户出现以下意图时使用本技能：

- "帮我追踪习惯"
- "记录今天的打卡"
- "我这周坚持了几天"
- "养成习惯"
- "每天运动打卡"
- "连续学习天数"
- "习惯统计"
- "打卡记录"
- "完成率多少"

## 核心功能

| 功能 | 说明 |
|---|---|
| 添加习惯 | 创建新习惯（名称、分类、目标频率） |
| 每日打卡 | 标记今天完成了某个习惯 |
| 取消打卡 | 撤销今天的打卡 |
| 连续天数 | 计算当前连续 streak 和最长 streak |
| 完成率 | 统计某段时间内的完成百分比 |
| 周概览 | 本周各习惯打卡情况 |
| 月概览 | 本月完成率统计 |
| 仪表盘 | 文本仪表盘展示所有习惯状态 |
| 删除习惯 | 删除不再追踪的习惯 |

## 数据存储

- JSON 文件存储，默认路径 `~/.habit_tracker/habits.json`
- 每个习惯记录：名称、分类、创建日期、每日打卡记录（日期列表）
- 纯文本可读，可手动编辑备份

## 使用方法

### 命令行工具

```bash
# 添加习惯
python3 scripts/habit_tracker.py add "早起" --category "健康"
python3 scripts/habit_tracker.py add "阅读30分钟" --category "学习"

# 今日打卡
python3 scripts/habit_tracker.py check "早起"
python3 scripts/habit_tracker.py check "阅读30分钟"

# 取消今日打卡
python3 scripts/habit_tracker.py uncheck "早起"

# 查看仪表盘
python3 scripts/habit_tracker.py dashboard

# 查看本周概览
python3 scripts/habit_tracker.py week

# 查看本月概览
python3 scripts/habit_tracker.py month

# 列出所有习惯
python3 scripts/habit_tracker.py list

# 删除习惯
python3 scripts/habit_tracker.py remove "早起"
```

### 操作步骤

1. **添加习惯**：用户说出想追踪的习惯名称，添加到列表
2. **每日打卡**：用户完成习惯后标记
3. **查看进度**：展示连续天数、完成率、仪表盘
4. **分析总结**：周/月概览帮助用户了解坚持情况

## 输出规范

- 仪表盘：表格列出习惯名、分类、当前连续、最长连续、本周完成率
- 周概览：7天网格视图，✓/✗/·标记每天完成情况
- 月概览：每月完成率百分比和连续天数
- 彩色输出：绿色=完成，灰色=未完成，黄色=今天
