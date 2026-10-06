# {YYYY年MM月} 消费报告

> 报告生成时间：{YYYY-MM-DD} | 数据范围：{YYYY-MM-01} 至 {YYYY-MM-DD}

---

## 一、本月概览

| 指标 | 金额 | 说明 |
|---|---|---|
| 总收入 | ¥{income_total} | {收入笔数} 笔 |
| 总支出 | ¥{expense_total} | {支出笔数} 笔 |
| 结余 | ¥{balance} | 收入 - 支出 |
| 日均支出 | ¥{daily_avg} | 按 {days} 天计算 |
| 单笔最大支出 | ¥{max_expense} | {max_expense_desc} |
| 预算执行 | {budget_status} | 预算 ¥{budget} / 已支出 ¥{expense_total} |

---

## 二、分类支出占比

| 排名 | 类别 | 金额 | 占比 | 笔数 | 日均 |
|---|---|---|---|---|---|
| 1 | 🍜 餐饮 | ¥{food_amount} | {food_pct}% | {food_count} | ¥{food_daily} |
| 2 | 🚇 交通 | ¥{transport_amount} | {transport_pct}% | {transport_count} | ¥{transport_daily} |
| 3 | 🛒 购物 | ¥{shopping_amount} | {shopping_pct}% | {shopping_count} | ¥{shopping_daily} |
| 4 | 🏠 住房 | ¥{housing_amount} | {housing_pct}% | {housing_count} | ¥{housing_daily} |
| 5 | 🎮 娱乐 | ¥{entertainment_amount} | {entertainment_pct}% | {entertainment_count} | ¥{entertainment_daily} |
| 6 | 💊 医疗 | ¥{medical_amount} | {medical_pct}% | {medical_count} | ¥{medical_daily} |
| 7 | 📚 教育 | ¥{education_amount} | {education_pct}% | {education_count} | ¥{education_daily} |
| 8 | 🧧 人情 | ¥{social_amount} | {social_pct}% | {social_count} | ¥{social_daily} |
| 9 | 📱 通讯 | ¥{communication_amount} | {communication_pct}% | {communication_count} | ¥{communication_daily} |
| 10 | 其他 | ¥{other_amount} | {other_pct}% | {other_count} | ¥{other_daily} |

**支出结构说明**：{简要描述本月支出结构特点，如「餐饮占比最高，达35%，主要因为外卖频次较高」}

---

## 三、每日支出趋势

| 日期 | 支出金额 | 主要消费 |
|---|---|---|
| {MM-DD} | ¥{amount} | {主要消费类别} |
| ... | ... | ... |

**趋势分析**：
- 支出最高日：{MM-DD}，¥{max_day_amount}（{原因}）
- 支出最低日：{MM-DD}，¥{min_day_amount}
- 周末 vs 工作日：周末日均 ¥{weekend_avg}，工作日日均 ¥{weekday_avg}
- {其他趋势观察}

---

## 四、大额支出 Top 5

| 排名 | 日期 | 类别 | 描述 | 金额 | 占总支出 |
|---|---|---|---|---|---|
| 1 | {MM-DD} | {类别} | {描述} | ¥{amount} | {pct}% |
| 2 | {MM-DD} | {类别} | {描述} | ¥{amount} | {pct}% |
| 3 | {MM-DD} | {类别} | {描述} | ¥{amount} | {pct}% |
| 4 | {MM-DD} | {类别} | {描述} | ¥{amount} | {pct}% |
| 5 | {MM-DD} | {类别} | {描述} | ¥{amount} | {pct}% |

---

## 五、预算执行情况

> 本月总预算：¥{budget}

| 类别 | 预算 | 实际支出 | 剩余/超支 | 执行率 | 状态 |
|---|---|---|---|---|---|
| 🍜 餐饮 | ¥{food_budget} | ¥{food_actual} | ¥{food_diff} | {food_rate}% | {正常/超支/结余} |
| 🚇 交通 | ¥{transport_budget} | ¥{transport_actual} | ¥{transport_diff} | {transport_rate}% | {状态} |
| 🛒 购物 | ¥{shopping_budget} | ¥{shopping_actual} | ¥{shopping_diff} | {shopping_rate}% | {状态} |
| 🏠 住房 | ¥{housing_budget} | ¥{housing_actual} | ¥{housing_diff} | {housing_rate}% | {状态} |
| 🎮 娱乐 | ¥{entertainment_budget} | ¥{entertainment_actual} | ¥{entertainment_diff} | {entertainment_rate}% | {状态} |
| 其他 | ¥{other_budget} | ¥{other_actual} | ¥{other_diff} | {other_rate}% | {状态} |
| **合计** | **¥{budget}** | **¥{actual_total}** | **¥{total_diff}** | **{total_rate}%** | **{总状态}** |

**预算分析**：
- {超支类别说明及原因}
- {结余类别说明}
- {剩余天数日均可用额度：¥{remaining_daily}/天}

---

## 六、异常消费提醒

{如无异常，写「本月未发现明显异常消费。」}

- ⚠ {异常1：类别/金额/原因说明}
- ⚠ {异常2：某类别支出环比增长超过50%}
- ⚠ {异常3：单笔支出超过月收入10%}

---

## 七、消费洞察与省钱建议

### 本月消费特点
1. {特点1：如「餐饮支出占比35%，其中外卖占餐饮的60%」}
2. {特点2：如「周末支出是工作日的1.8倍，主要集中在娱乐和购物」}
3. {特点3：如「购物类有3笔超过500元的大额支出」}

### 可操作的省钱建议
1. **{建议1}**：{具体说明，如「减少外卖频次，每周自己做饭2-3次，预计可省¥300/月」}
2. **{建议2}**：{具体说明，如「购物前列清单，避免冲动消费，设置每月购物上限」}
3. **{建议3}**：{具体说明，如「使用公共交通替代打车，预计可省¥150/月」}
4. **{建议4}**：{具体说明，如「订阅服务定期清理，取消不常用的会员」}

### 预计节省金额
如采纳以上建议，预计每月可节省 ¥{estimated_savings}，占本月支出的 {savings_pct}%。

---

## 八、下月预算建议

基于本月消费数据，建议下月预算分配如下：

| 类别 | 本月实际 | 建议预算 | 调整说明 |
|---|---|---|---|
| 🍜 餐饮 | ¥{food_actual} | ¥{food_suggested} | {调整原因} |
| 🚇 交通 | ¥{transport_actual} | ¥{transport_suggested} | {调整原因} |
| 🛒 购物 | ¥{shopping_actual} | ¥{shopping_suggested} | {调整原因} |
| 🏠 住房 | ¥{housing_actual} | ¥{housing_suggested} | {调整原因} |
| 🎮 娱乐 | ¥{entertainment_actual} | ¥{entertainment_suggested} | {调整原因} |
| 其他 | ¥{other_actual} | ¥{other_suggested} | {调整原因} |
| **合计** | **¥{actual_total}** | **¥{suggested_total}** | |

---

## 附录：消费明细

> 完整明细见附件 CSV 文件。以下为按类别汇总的明细预览。

### 🍜 餐饮（{food_count}笔，¥{food_amount}）
| 日期 | 描述 | 金额 |
|---|---|---|
| ... | ... | ... |

### 🚇 交通（{transport_count}笔，¥{transport_amount}）
| 日期 | 描述 | 金额 |
|---|---|---|
| ... | ... | ... |

---

*本报告由消费记录自动生成，金额以原始记录为准。如有遗漏请补充记录。*
*省钱建议仅供参考，不构成任何金融或投资建议。*
