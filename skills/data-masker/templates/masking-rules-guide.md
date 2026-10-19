# 数据脱敏规则配置指南

> data-masker 技能配套指南，帮助配置正确的脱敏规则。

---

## 一、脱敏方式选择决策树

```
需要保留数据格式用于展示？
├── 是 → mask（掩码）
│   ├── 需要保留部分可读？→ 指定 keep_start / keep_end
│   └── 完全隐藏？→ keep_start=0, keep_end=0
├── 否 → 需要用于关联/去重？
│   ├── 是 → hash（哈希，加盐）
│   └── 否 → 需要统计分析？
│       ├── 是 → generalize（泛化/区间化）
│       └── 否 → 完全不需要？
│           ├── 是 → nullify（置空）
│           └── 否 → replace（替换为固定值）
```

---

## 二、各字段推荐脱敏方式

| 字段 | 推荐方式 | 参数 | 效果示例 |
|---|---|---|---|
| 手机号 | mask | keep_start=3, keep_end=4 | `138****5678` |
| 身份证 | mask | keep_start=6, keep_end=4 | `110101********1234` |
| 邮箱 | mask | keep_start=1, keep_domain=true | `z***@example.com` |
| 银行卡 | mask | keep_start=0, keep_end=4 | `************1234` |
| 姓名 | mask | keep_start=1 | `张*`、`John***` |
| 地址 | truncate | keep_chars=9 | `北京市朝阳区***` |
| IP | mask | keep_start=2, separator=. | `192.168.***.***` |
| 密码 | nullify | - | ``（空） |
| 用户ID | hash | salt=xxx, length=16 | `a1b2c3d4e5f6...` |
| 薪资 | generalize | bins=[...] | `10000-20000` |
| 年龄 | generalize | bins=[...] | `20-30` |
| 出生日期 | generalize | keep_year=true | `1990-**-**` |

---

## 三、规则文件完整示例

```json
{
  "auto_detect": true,
  "rules": [
    {
      "field": "phone",
      "match": "name",
      "aliases": ["phone", "mobile", "手机"],
      "method": "mask",
      "params": {"keep_start": 3, "keep_end": 4}
    },
    {
      "field": "user_id",
      "match": "name",
      "aliases": ["user_id", "uid", "用户ID"],
      "method": "hash",
      "params": {"salt": "my-secret-salt-2024", "length": 16}
    },
    {
      "field": "salary",
      "match": "name",
      "aliases": ["salary", "工资", "月薪"],
      "method": "generalize",
      "params": {"bins": [0, 5000, 10000, 20000, 50000, 100000]}
    },
    {
      "field": "remark",
      "match": "regex",
      "pattern": "\\b1[3-9]\\d{9}\\b",
      "method": "mask",
      "params": {"keep_start": 3, "keep_end": 4}
    }
  ]
}
```

---

## 四、正则匹配规则

当字段名无法识别时（如自由文本、备注字段），使用正则匹配：

```json
{
  "field": "phone_in_text",
  "match": "regex",
  "pattern": "\\b1[3-9]\\d{9}\\b",
  "method": "mask",
  "params": {"keep_start": 3, "keep_end": 4}
}
```

**常用正则**：
- 手机号：`\b1[3-9]\d{9}\b`
- 身份证：`\b\d{17}[\dXx]\b`
- 邮箱：`\b[\w.+-]+@[\w-]+\.[\w.-]+\b`
- IPv4：`\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
- 银行卡：`\b\d{16,19}\b`

---

## 五、哈希加盐最佳实践

1. **必须加盐**：不加盐的哈希可被彩虹表破解
2. **盐值保密**：盐值相当于密钥，不要和脱敏数据放在一起
3. **固定盐值**：同一项目使用固定盐值，保证同一原始值哈希结果一致（可关联）
4. **不同项目不同盐**：跨项目使用不同盐值，防止跨库关联
5. **长度选择**：16 位足够唯一标识，32 位更安全

---

## 六、合规参考

| 法规 | 要求 | 对应脱敏方式 |
|---|---|---|
| 《个人信息保护法》 | 处理个人信息应采取加密、去标识化等安全措施 | mask / hash |
| 《数据安全法》 | 重要数据出境需脱敏 | 全部方式 |
| GDPR | 数据最小化、匿名化 | nullify / hash |
| 行业规范（金融） | 客户信息脱敏展示 | mask |

---

## 七、验证清单

脱敏完成后，逐项检查：

- [ ] 所有手机号已脱敏（无完整 11 位手机号）
- [ ] 所有身份证已脱敏（无完整 18 位身份证）
- [ ] 所有邮箱已脱敏（本地名部分隐藏）
- [ ] 密码字段已置空
- [ ] 地址已截断到区/县级
- [ ] 薪资已泛化到区间
- [ ] 非敏感字段未被误处理
- [ ] 数据格式未被破坏（CSV 列数一致、JSON 可解析、SQL 可执行）
- [ ] 脱敏后数据可正常用于测试/分析
- [ ] 原始数据已安全备份

---

*本指南由 data-masker 技能提供，配合 mask_data.py 脚本使用*
