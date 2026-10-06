# 示例：目录扫描报告

> 使用 `plan_backup.py --dir /path/to/data --top 10` 生成。

---

## 基本信息

| 项目 | 值 |
|---|---|
| 目录 | `/home/user/data/` |
| 总大小 | 12.34 GB |
| 文件数 | 8,456 |
| 目录数 | 342 |
| 跳过 | 23 个（排除/无权限） |
| 扫描用时 | 2.3 秒 |

---

## 类型分布

| 类型 | 文件数 | 大小 | 占比 |
|---|---|---|---|
| 视频 | 45 | 6.78 GB | 55.0% |
| 图片 | 1,234 | 2.34 GB | 19.0% |
| 文档 | 2,345 | 1.56 GB | 12.6% |
| 代码 | 3,456 | 890 MB | 7.2% |
| 压缩包 | 123 | 567 MB | 4.6% |
| 其他 | 1,253 | 200 MB | 1.6% |

---

## 大文件 Top 10

| # | 文件路径 | 大小 | 类型 |
|---|---|---|---|
| 1 | `/data/video/tutorial_01.mp4` | 1.23 GB | 视频 |
| 2 | `/data/video/tutorial_02.mp4` | 987 MB | 视频 |
| 3 | `/data/backup/old_system.tar.gz` | 756 MB | 压缩包 |
| 4 | `/data/video/tutorial_03.mp4` | 654 MB | 视频 |
| 5 | `/data/docs/design_source.psd` | 345 MB | 图片 |
| 6 | `/data/video/tutorial_04.mp4` | 234 MB | 视频 |
| 7 | `/data/data/dataset_large.csv` | 189 MB | 文档 |
| 8 | `/data/images/photo_raw_01.raw` | 156 MB | 图片 |
| 9 | `/data/video/tutorial_05.mp4` | 134 MB | 视频 |
| 10 | `/data/backup/database_dump.sql` | 98 MB | 文档 |

---

## 大目录 Top 5

| # | 目录路径 | 大小 |
|---|---|---|
| 1 | `/data/video/` | 6.78 GB |
| 2 | `/data/images/` | 2.34 GB |
| 3 | `/data/docs/` | 1.56 GB |
| 4 | `/data/backup/` | 854 MB |
| 5 | `/data/code/` | 890 MB |

---

## 备份建议

1. **视频文件占比最大（55%）**，建议单独备份或使用增量备份
2. `/data/backup/` 目录包含旧备份，建议排除或单独处理
3. 压缩后预估大小：约 8.5 GB（视频几乎不可压缩）
4. 建议使用外接硬盘 + 云存储的双备份策略
5. 备份频率：每周完整 + 每日增量

---

*报告由 backup-planner 技能生成*
