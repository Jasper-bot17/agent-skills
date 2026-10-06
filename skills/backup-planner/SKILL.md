---
name: backup-planner
description: '备份计划助手。扫描指定目录，统计文件数量和总大小，识别大文件和大目录，分析文件类型分布，生成完整备份/增量备份方案，估算备份时间和存储空间，自动生成 tar/rsync 备份脚本，提供排除规则建议和备份频率推荐。适用于个人文件备份、项目代码备份、服务器数据备份、迁移前评估等场景。'
---

# 备份计划助手

## 一、技能定位

本技能用于**制定和生成数据备份方案**。核心价值：

- 扫描目录，统计文件数量、总大小、类型分布
- 识别大文件和大目录，找出备份重点
- 生成完整备份和增量备份方案
- 估算备份时间和所需存储空间
- 自动生成 tar / rsync 备份脚本
- 提供排除规则建议和备份频率推荐

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我看看这个目录有多大」「统计一下文件」
2. 用户说「帮我做个备份计划」「怎么备份这些文件」
3. 用户说「生成一个备份脚本」「写个 tar/rsync 备份命令」
4. 用户说「哪些文件最大」「找出大文件」
5. 用户说「迁移前评估一下」「看看要备份多少数据」
6. 用户说「增量备份怎么做」「哪些文件变化了」
7. 用户说「备份需要多长时间」「需要多大空间」

## 三、支持的功能

### 3.1 目录扫描

- 递归扫描指定目录
- 统计文件数量、总大小、目录数量
- 按文件类型分类统计（文档、图片、视频、音频、代码、压缩包等）
- 统计文件修改时间分布

### 3.2 大文件识别

- 找出 Top N 最大文件
- 找出 Top N 最大子目录
- 可自定义大小阈值
- 标记可压缩文件类型

### 3.3 备份方案生成

- **完整备份**：备份所有文件
- **增量备份**：仅备份最近 N 天修改的文件
- **差异备份**：仅备份与上次备份不同的文件
- 可自定义排除规则（排除 node_modules、.git、临时文件等）

### 3.4 时间与空间估算

- 基于文件大小估算备份时间（按假设传输速度）
- 计算压缩后预估大小（按类型压缩率估算）
- 计算保留多份备份所需总空间
- 支持自定义传输速度和压缩率

### 3.5 备份脚本生成

- 生成 tar 备份脚本（支持压缩、排除、时间戳命名）
- 生成 rsync 备份脚本（支持增量、远程同步、删除同步）
- 生成备份清单（manifest）
- 脚本可直接执行

### 3.6 排除规则建议

- 自动识别应排除的目录（node_modules、.git、__pycache__、vendor 等）
- 自动识别应排除的文件类型（.tmp、.log、.cache、.swp 等）
- 生成 .gitignore 风格的排除列表
- 可自定义排除模式

## 四、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 扫描目录 / 生成备份方案 / 生成备份脚本 / 大文件分析
- 目标目录路径
- 备份类型（完整/增量）
- 输出格式（报告/脚本）

### 步骤 2：运行脚本

使用 `scripts/plan_backup.py`：

```bash
# 扫描目录并生成报告
python3 scripts/plan_backup.py --dir /path/to/data

# 只显示前 20 个大文件
python3 scripts/plan_backup.py --dir /path/to/data --top 20

# 生成增量备份方案（最近 7 天）
python3 scripts/plan_backup.py --dir /path/to/data --incremental 7

# 生成 tar 备份脚本
python3 scripts/plan_backup.py --dir /path/to/data --script tar --output backup.sh

# 生成 rsync 备份脚本（远程目标）
python3 scripts/plan_backup.py --dir /path/to/data --script rsync --remote user@server:/backup/

# 自定义排除规则
python3 scripts/plan_backup.py --dir /path/to/data --exclude "*.log,node_modules,.git"

# 估算备份时间（假设 100MB/s 传输速度）
python3 scripts/plan_backup.py --dir /path/to/data --speed 100

# JSON 格式输出
python3 scripts/plan_backup.py --dir /path/to/data --format json
```

### 步骤 3：解读结果

- **扫描报告**：文件统计、类型分布、大文件列表
- **备份方案**：备份范围、预估大小、预估时间、排除规则
- **备份脚本**：可直接执行的 shell 脚本

### 步骤 4：安全提示

1. 备份前确认目标空间充足
2. 重要数据遵循 3-2-1 原则（3份副本、2种介质、1份异地）
3. 定期验证备份可恢复性
4. 敏感数据备份应加密
5. 不要将备份存储在同一物理设备上

## 五、输出规范

### 5.1 扫描报告

```
📊 目录扫描报告
━━━━━━━━━━━━━━━━━━━━━━━━
目录：/path/to/data
总大小：2.34 GB
文件数：1,234
目录数：89
扫描用时：0.3 秒

📁 类型分布：
  文档：234 个，456 MB (19.5%)
  图片：156 个，789 MB (33.7%)
  视频：12 个，678 MB (29.0%)
  代码：345 个，123 MB (5.3%)
  其他：487 个，294 MB (12.5%)

📈 大文件 Top 5：
  1. /path/to/data/video/intro.mp4 — 234 MB
  2. /path/to/data/backup.tar.gz — 156 MB
  3. /path/to/data/docs/manual.pdf — 89 MB
  4. /path/to/data/images/photo.raw — 67 MB
  5. /path/to/data/data/dataset.csv — 45 MB

💡 建议：
  - 视频文件占比最大（29%），可考虑单独备份
  - 建议排除 node_modules（123 MB）和 .git（45 MB）
  - 压缩后预估大小：约 1.8 GB
```

### 5.2 备份方案

```
💾 备份方案
━━━━━━━━━━━━━━━━━━━━━━━━
备份类型：完整备份
源目录：/path/to/data
目标位置：/backup/

📦 备份范围：
  文件数：1,234
  总大小：2.34 GB
  排除后大小：2.17 GB（排除 167 MB）

🚫 排除规则：
  - node_modules/
  - .git/
  - __pycache__/
  - *.log
  - *.tmp

⏱️  时间估算：
  未压缩：约 22 秒（按 100 MB/s）
  压缩后：约 1.8 GB，约 45 秒（含压缩时间）

📋 建议：
  - 备份频率：每周一次完整备份
  - 保留份数：至少 3 份
  - 存储介质：外接硬盘 + 云存储
  - 验证恢复：每月验证一次
```

### 5.3 备份脚本

```bash
#!/bin/bash
# 自动生成的备份脚本
# 源目录：/path/to/data
# 生成时间：2026-10-02

SOURCE="/path/to/data"
DEST="/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}.tar.gz"

echo "开始备份：${SOURCE}"
echo "目标文件：${DEST}/${BACKUP_NAME}"

tar -czf "${DEST}/${BACKUP_NAME}" \
  --exclude="node_modules" \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude="*.log" \
  --exclude="*.tmp" \
  -C "$(dirname "${SOURCE}")" \
  "$(basename "${SOURCE}")"

if [ $? -eq 0 ]; then
  echo "✅ 备份完成：${BACKUP_NAME}"
  echo "文件大小：$(du -h "${DEST}/${BACKUP_NAME}" | cut -f1)"
else
  echo "❌ 备份失败"
  exit 1
fi
```

## 六、常见场景处理

### 场景 1：个人文件备份
**用户**：「帮我看看 Documents 目录有多大，做个备份计划」
**处理**：扫描目录 → 生成报告 → 推荐每周完整备份 → 生成 tar 脚本。

### 场景 2：项目代码备份
**用户**：「这个项目怎么备份，要排除 node_modules」
**处理**：扫描目录 → 自动识别排除规则 → 生成 rsync 增量备份脚本。

### 场景 3：服务器数据迁移
**用户**：「迁移前评估一下服务器数据量」
**处理**：扫描目录 → 统计总大小和类型 → 估算传输时间 → 推荐分批迁移策略。

### 场景 4：大文件清理
**用户**：「找出最大的 10 个文件」
**处理**：扫描目录 → 输出 Top 10 大文件 → 标记可删除/可压缩项。

### 场景 5：增量备份
**用户**：「只备份最近 7 天修改的文件」
**处理**：扫描目录 → 按修改时间过滤 → 生成增量备份脚本 → 估算增量大小。

## 七、注意事项

1. **权限问题**：扫描需要读取权限，无权限的文件会被跳过并在报告中说明。
2. **符号链接**：默认不跟随符号链接，避免循环引用和重复备份。
3. **大目录扫描**：扫描数十万文件可能需要较长时间，建议先指定子目录。
4. **时间估算**：备份时间基于假设传输速度，实际时间受磁盘 IO、CPU、网络影响。
5. **压缩率估算**：不同文件类型压缩率差异大（文本 70%、图片 5%、视频 0%），估算仅供参考。
6. **排除规则**：默认排除常见开发依赖目录和临时文件，可通过 `--exclude` 自定义。
7. **脚本安全**：生成的脚本包含 `rm` 等危险命令时会加注释提醒，执行前请仔细检查。
8. **不执行备份**：本技能只生成方案和脚本，不实际执行备份操作。
9. **路径处理**：支持相对路径和绝对路径，脚本中会转换为绝对路径。
10. **跨平台**：生成的 tar/rsync 脚本适用于 Linux/macOS，Windows 用户需使用 WSL 或对应工具。

## 八、文件结构

```
backup-planner/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── backup-policy-template.md          # 备份策略模板
├── scripts/
│   └── plan_backup.py                    # 备份计划脚本
└── examples/
    ├── sample-scan-report.md              # 示例扫描报告
    └── sample-backup-script.sh            # 示例备份脚本
```

## 九、使用示例

### 示例 1：快速扫描
**用户**：「看看这个目录有多大」
**AI**：运行 `--dir /path/to/data` → 输出文件统计和大文件列表。

### 示例 2：生成备份脚本
**用户**：「生成一个备份脚本，排除 node_modules 和 .git」
**AI**：运行 `--script tar --exclude "node_modules,.git"` → 生成可执行脚本。

### 示例 3：增量备份
**用户**：「只备份最近 3 天的文件」
**AI**：运行 `--incremental 3` → 过滤近期文件 → 生成增量备份方案。
