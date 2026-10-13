---
name: citation-generator
description: '参考文献引用生成器。根据文献信息自动生成标准格式的参考文献引用，支持四种引用格式：GB/T 7714-2015（中国国标）、APA 7th、MLA 9th、Chicago。支持八种文献类型：期刊文章、书籍、网页、学位论文、会议论文、报纸文章、报告、专利。自动生成文中引用（in-text citation）和文后参考文献（reference list），支持批量从 JSON 文件读取生成，内置各格式规范说明。适用于学生写论文/作业、学术写作、报告撰写等场景。'
---

# 参考文献引用生成器

## 一、技能定位

本技能用于**根据文献信息自动生成标准格式的参考文献引用**。核心价值：

- 四种引用格式：GB/T 7714-2015（中国国标）、APA 7th、MLA 9th、Chicago
- 八种文献类型：期刊文章、书籍、网页、学位论文、会议论文、报纸文章、报告、专利
- 自动生成文中引用（in-text citation）和文后参考文献（reference list）
- 支持命令行单条生成和 JSON 批量生成
- 自动处理作者姓名格式（姓在前名在后、缩写、et al.）
- 自动处理页码、卷期、DOI、URL、访问日期等字段
- 内置各格式规范说明和示例

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「生成参考文献」「引用格式」「GB/T 7714」
2. 用户说「APA 格式引用」「MLA 格式」「Chicago 格式」
3. 用户说「这篇论文怎么引用」「期刊文章引用格式」
4. 用户说「网页引用」「书籍引用」「学位论文引用」
5. 用户说「批量生成参考文献」「从 JSON 生成引用」
6. 用户说「文中引用怎么写」「in-text citation」
7. 用户说「论文参考文献格式不对」「引用格式报错」
8. 用户写论文/作业需要整理参考文献

## 三、支持的引用格式

### 3.1 GB/T 7714-2015（中国国家标准）

中国学术写作最常用的格式，顺序编码制。

**期刊文章**：
```
[1] 作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.
```

**书籍**：
```
[2] 作者. 书名[M]. 版本. 出版地: 出版者, 出版年: 起止页码.
```

**网页**：
```
[3] 作者. 题名[EB/OL]. (发布日期)[引用日期]. URL.
```

### 3.2 APA 7th（美国心理学会）

社会科学常用格式，作者-年份制。

**期刊文章**：
```
作者, A. A. (年). 题名. 刊名, 卷(期), 起止页码. https://doi.org/xxx
```

**书籍**：
```
作者, A. A. (年). 书名 (版次). 出版社.
```

**文中引用**：`(作者, 年)` 或 `作者 (年)`

### 3.3 MLA 9th（现代语言协会）

人文学科常用格式，作者-页码制。

**期刊文章**：
```
作者. "题名." 刊名, vol. 卷, no. 期, 年, pp. 起止页码.
```

**书籍**：
```
作者. 书名. 版次, 出版社, 年.
```

**文中引用**：`(作者 页码)`

### 3.4 Chicago（芝加哥）

历史、艺术等人文学科常用，有注释-书目制和作者-年份制两种。本技能支持注释-书目制。

**期刊文章**：
```
作者. "题名." 刊名 卷, no. 期 (年): 起止页码.
```

**书籍**：
```
作者. 书名. 版次. 出版地: 出版社, 年.
```

## 四、支持的文献类型

| 类型标识 | 文献类型 | GB/T 7714 标识 | 必需字段 |
|---|---|---|---|
| `journal` | 期刊文章 | [J] | 作者、题名、刊名、年、卷(期)、页码 |
| `book` | 书籍 | [M] | 作者、书名、出版地、出版者、出版年 |
| `webpage` | 网页 | [EB/OL] | 作者、题名、URL、发布日期、引用日期 |
| `thesis` | 学位论文 | [D] | 作者、题名、学位类型、学校、年 |
| `conference` | 会议论文 | [C] | 作者、题名、会议名、会议地点、年、页码 |
| `newspaper` | 报纸文章 | [N] | 作者、题名、报纸名、出版日期、版次 |
| `report` | 报告 | [R] | 作者、题名、报告编号、机构、年 |
| `patent` | 专利 | [P] | 发明者、专利题名、专利国别、专利号、发布日期 |

## 五、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 引用格式（gbt7714 / apa / mla / chicago）
- 文献类型（journal / book / webpage / thesis / conference / newspaper / report / patent）
- 文献信息（作者、题名、刊名/书名、年、卷期、页码等）

### 步骤 2：运行脚本

使用 `scripts/generate_citation.py`：

```bash
# 基本用法：生成单条引用
python3 scripts/generate_citation.py --format gbt7714 --type journal \
  --authors "张三,李四" --title "论文标题" --journal "期刊名" \
  --year 2024 --volume 10 --issue 2 --pages "1-10"

# APA 格式期刊文章
python3 scripts/generate_citation.py --format apa --type journal \
  --authors "Zhang, San" --title "Paper Title" --journal "Journal Name" \
  --year 2024 --volume 10 --issue 2 --pages "1-10" --doi "10.1234/abc"

# MLA 格式书籍
python3 scripts/generate_citation.py --format mla --type book \
  --authors "Smith, John" --title "Book Title" --publisher "Publisher" \
  --year 2024 --edition "2nd"

# 网页引用
python3 scripts/generate_citation.py --format gbt7714 --type webpage \
  --authors "王五" --title "网页标题" --url "https://example.com" \
  --publish-date "2024-01-15" --access-date "2024-06-01"

# 学位论文
python3 scripts/generate_citation.py --format gbt7714 --type thesis \
  --authors "赵六" --title "论文题目" --degree "硕士" \
  --institution "某某大学" --year 2024

# 批量生成（从 JSON 文件）
python3 scripts/generate_citation.py --format apa --batch references.json

# 生成文中引用
python3 scripts/generate_citation.py --format apa --type journal \
  --authors "Zhang, San" --year 2024 --in-text

# 列出所有支持的格式和类型
python3 scripts/generate_citation.py --list
```

### 步骤 3：批量 JSON 格式

批量生成时，JSON 文件格式如下：

```json
[
  {
    "type": "journal",
    "authors": ["张三", "李四"],
    "title": "论文标题",
    "journal": "期刊名",
    "year": 2024,
    "volume": 10,
    "issue": 2,
    "pages": "1-10",
    "doi": "10.1234/abc"
  },
  {
    "type": "book",
    "authors": ["Smith, John"],
    "title": "Book Title",
    "publisher": "Publisher",
    "year": 2024,
    "edition": "2nd",
    "city": "New York"
  }
]
```

### 步骤 4：安全提示

1. 本技能只生成引用文本，不修改任何文件
2. 生成的引用需要用户核对文献信息的准确性
3. 不同学校/期刊可能有细微格式差异，建议以目标要求为准
4. DOI 和 URL 建议直接复制，避免手动输入错误
5. 作者姓名格式：中文用全名，英文用"姓, 名缩写"格式
6. 引用日期格式：GB/T 7714 用 YYYY-MM-DD，APA/MLA/Chicago 用 Month DD, YYYY

## 六、常见场景处理

### 场景 1：中文期刊论文（GB/T 7714）
**用户**：「帮我生成这篇中文期刊的参考文献」
**处理**：使用 `--format gbt7714 --type journal`，输入中文作者、题名、刊名、年卷期页码。

### 场景 2：英文期刊论文（APA）
**用户**：「这篇英文论文 APA 格式怎么引用？」
**处理**：使用 `--format apa --type journal`，作者用"姓, 名缩写"，包含 DOI。

### 场景 3：引用网页
**用户**：「网页的参考文献怎么写？」
**处理**：使用 `--type webpage`，必须包含 URL、发布日期和引用日期。

### 场景 4：学位论文
**用户**：「硕士论文的引用格式」
**处理**：使用 `--type thesis`，包含学位类型（硕士/博士）、学校、年份。

### 场景 5：批量生成
**用户**：「我有 20 篇文献，帮我批量生成参考文献」
**处理**：整理为 JSON 文件，使用 `--batch` 批量生成。

### 场景 6：文中引用
**用户**：「文中引用怎么标注？」
**处理**：使用 `--in-text` 生成文中引用格式（APA: (作者, 年)；MLA: (作者 页码)）。

### 场景 7：书籍引用
**用户**：「这本书怎么引用？」
**处理**：使用 `--type book`，包含作者、书名、出版社、年份、版次（可选）。

### 场景 8：会议论文
**用户**：「会议论文的引用格式」
**处理**：使用 `--type conference`，包含会议名、会议地点、年份、页码。

## 七、注意事项

1. **作者格式**：中文作者用全名（如"张三"）；英文作者用"姓, 名缩写"（如"Smith, J."）。多位作者用逗号分隔。
2. **三位以上作者**：GB/T 7714 列出前3位后加"等"；APA 列出前20位；MLA 列出第1位后加"et al."。
3. **页码格式**：GB/T 7714 用"1-10"；APA 用"1–10"（en dash）；MLA 用"1-10"。
4. **卷期格式**：GB/T 7714 用"卷(期)"；APA 用"卷(期)"；MLA 用"vol. 卷, no. 期"。
5. **DOI**：优先使用 DOI，格式为 `https://doi.org/10.xxxx/xxxx`。
6. **网页引用**：必须包含引用日期（access date），因为网页内容可能变化。
7. **出版地**：GB/T 7714 和 Chicago 需要出版地；APA 7th 已不再要求出版地。
8. **格式差异**：不同学校/期刊可能有自定义要求，最终以目标要求为准。
9. **不修改文件**：本技能只输出引用文本，不创建或修改任何文件。
10. **信息核对**：生成后请核对作者、题名、年份、页码等关键信息的准确性。

## 八、文件结构

```
citation-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── citation-style-guide.md           # 四种引用格式规范指南
├── scripts/
│   └── generate_citation.py               # 引用生成脚本
└── examples/
    ├── sample-references.json             # 示例批量输入（8种文献类型）
    ├── sample-gbt7714-output.txt          # 示例 GB/T 7714 输出
    └── sample-apa-output.txt              # 示例 APA 输出
```

## 九、使用示例

### 示例 1：中文期刊
**用户**：「生成 GB/T 7714 格式的期刊引用」
**AI**：运行 `--format gbt7714 --type journal --authors "张三,李四" --title "深度学习研究" --journal "计算机学报" --year 2024 --volume 47 --issue 3 --pages "100-110"` → `[1] 张三, 李四. 深度学习研究[J]. 计算机学报, 2024, 47(3): 100-110.`

### 示例 2：英文期刊 APA
**用户**：「APA 格式引用这篇论文」
**AI**：运行 `--format apa --type journal --authors "Smith, J.,Johnson, A." --title "AI Research" --journal "Journal of AI" --year 2024 --volume 10 --issue 2 --pages "1-10" --doi "10.1234/ai"` → `Smith, J., & Johnson, A. (2024). AI research. Journal of AI, 10(2), 1–10. https://doi.org/10.1234/ai`
