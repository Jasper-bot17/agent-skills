# 示例：日志分析报告

> 本示例展示使用 `analyze_log.py` 对 `sample-app.log` 进行分析的输出。
> 示例日志为一个 Web 应用一天的运行日志，包含数据库连接故障和内存溢出。

---

## 基本信息

| 项目 | 值 |
|---|---|
| 文件 | sample-app.log |
| 总行数 | 259 |
| 时间范围 | 2026-09-28 08:00:01 ~ 2026-09-28 23:59:58 |

---

## 级别分布

| 级别 | 数量 | 占比 |
|---|---|---|
| 🔴 FATAL | 2 | 0.77% |
| 🔴 ERROR | 223 | 86.10% |
| 🟡 WARN | 5 | 1.93% |
| ⚪ INFO | 28 | 10.81% |
| 🔵 DEBUG | 1 | 0.39% |

---

## 高频错误 Top 5

| 排名 | 错误消息 | 次数 |
|---|---|---|
| 1 | Connection refused (127.0.0.1:5432) - retrying in 5s | 217 |
| 2 | Connection refused (127.0.0.1:5432) - retrying in 10s | 1 |
| 3 | Connection refused (127.0.0.1:5432) - retrying in 15s | 1 |
| 4 | NullPointerException at UserService.java:42 | 1 |
| 5 | TimeoutException after 30000ms calling payment-service | 1 |

---

## 异常检测

| 时段 | 错误数 | 错误率 | 异常倍数 |
|---|---|---|---|
| 2026-09-28 14:00 | 218 | 98.2% | 15.5x |

**异常分析**：14:00 部署 version 2.5.0 后，数据库连接立即开始被拒绝，持续约 23 分钟，最终导致 JVM 内存溢出（OutOfMemoryError），应用在 14:23 自动重启。

---

## 排查建议

1. **立即排查**：存在 2 条 FATAL 级错误（OutOfMemoryError），应用曾崩溃重启
2. **根因推测**：14:00 部署后数据库连接被拒绝 217 次，可能是新版本配置错误或数据库未启动
3. **优先处理**：Connection refused 占全部错误的 97%，修复数据库连接可消除绝大多数错误
4. **次要问题**：NullPointerException at UserService.java:42 需检查空值处理

---

## 时间过滤示例

过滤 14:00-14:30 时段：

```bash
python3 analyze_log.py --file app.log --from "2026-09-28 14:00" --to "2026-09-28 14:30"
```

结果：222 行，其中 ERROR 216 条、FATAL 2 条、INFO 4 条。

---

*报告由 log-analyzer 技能生成*
