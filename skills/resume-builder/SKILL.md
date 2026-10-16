---
name: resume-builder
description: '简历生成助手。根据用户提供的个人信息（基本资料、求职意向、工作经历、教育背景、技能、项目经验、证书、语言能力等），自动生成格式规范、排版美观的简历。支持 Markdown、纯文本、HTML 三种输出格式，支持中英文双语简历，可自定义模板风格，自动按时间倒序排列经历，智能突出关键词。适用于求职、实习申请、跳槽、校招等场景。纯 Python 标准库，无外部依赖。'
---

# 简历生成助手

## 一、技能定位

本技能用于**根据结构化个人信息自动生成专业简历**。核心价值：

- **结构化输入**：通过 JSON 数据文件描述简历内容，清晰易维护
- **三种输出格式**：Markdown（便于编辑）、纯文本（便于复制粘贴）、HTML（便于打印和网页展示）
- **中英文双语**：支持中文简历和英文简历生成
- **自动排序**：工作经历、教育背景、项目经验自动按时间倒序排列
- **智能排版**：自动处理日期格式、列表缩进、分隔线、标题层级
- **多模板风格**：支持经典、简洁、现代三种排版风格
- **关键词高亮**：HTML 格式中自动高亮技能关键词
- **纯标准库**：无外部依赖，开箱即用

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我写简历」「生成简历」「做一份简历」
2. 用户说「简历优化」「简历排版」「简历格式化」
3. 用户说「求职简历」「实习简历」「校招简历」
4. 用户说「英文简历」「CV」「resume」
5. 用户说「把这些信息整理成简历」
6. 用户说「简历模板」「简历格式」
7. 用户说「跳槽简历」「转行简历」
8. 用户提供个人信息要求生成简历文档

## 三、简历数据结构

简历数据以 JSON 格式描述，支持以下字段：

### 基本信息（personal）
| 字段 | 类型 | 说明 | 示例 |
|---|---|---|---|
| `name` | string | 姓名 | 张三 |
| `title` | string | 职位/头衔 | 软件工程师 |
| `email` | string | 邮箱 | zhangsan@example.com |
| `phone` | string | 电话 | 138-0000-0000 |
| `location` | string | 所在地 | 北京 |
| `website` | string | 个人网站 | https://zhangsan.dev |
| `github` | string | GitHub | https://github.com/zhangsan |
| `linkedin` | string | LinkedIn | https://linkedin.com/in/zhangsan |
| `avatar` | string | 头像URL（可选） | - |

### 求职意向（objective）
| 字段 | 类型 | 说明 |
|---|---|---|
| `position` | string | 目标职位 |
| `summary` | string | 个人简介/自我评价 |

### 工作经历（experience）
数组，每项包含：
| 字段 | 类型 | 说明 |
|---|---|---|
| `company` | string | 公司名称 |
| `position` | string | 职位 |
| `start_date` | string | 开始时间（YYYY-MM 或 YYYY年MM月） |
| `end_date` | string | 结束时间（或 "至今"/"Present"） |
| `location` | string | 工作地点（可选） |
| `description` | string[] | 工作描述/成就列表 |

### 教育背景（education）
数组，每项包含：
| 字段 | 类型 | 说明 |
|---|---|---|
| `school` | string | 学校名称 |
| `degree` | string | 学位/学历 |
| `major` | string | 专业 |
| `start_date` | string | 开始时间 |
| `end_date` | string | 结束时间 |
| `gpa` | string | GPA（可选） |
| `description` | string[] | 补充说明（可选） |

### 技能（skills）
数组，每项包含：
| 字段 | 类型 | 说明 |
|---|---|---|
| `category` | string | 技能分类（如"编程语言"） |
| `items` | string[] | 具体技能列表 |

### 项目经验（projects）
数组，每项包含：
| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 项目名称 |
| `role` | string | 担任角色 |
| `start_date` | string | 开始时间 |
| `end_date` | string | 结束时间 |
| `description` | string[] | 项目描述/成果 |
| `tech_stack` | string[] | 技术栈（可选） |
| `link` | string | 项目链接（可选） |

### 证书（certifications）
字符串数组，如 `["AWS 认证解决方案架构师", "PMP 项目管理专业人士"]`

### 语言能力（languages）
数组，每项包含：
| 字段 | 类型 | 说明 |
|---|---|---|
| `language` | string | 语言 |
| `level` | string | 水平 |

## 四、操作步骤

### 步骤 1：收集简历信息

向用户确认以下信息（用户可提供全部或部分）：
- 基本信息：姓名、联系方式、所在地
- 求职意向：目标职位、个人简介
- 工作经历：公司、职位、时间、工作内容
- 教育背景：学校、专业、学历、时间
- 技能：编程语言、工具、框架等
- 项目经验：项目名称、角色、描述
- 证书和语言能力（可选）

如果用户信息不完整，使用合理的占位符并标注「待补充」。

### 步骤 2：生成 JSON 数据文件

将收集到的信息整理为 JSON 格式，保存为文件（如 `resume-data.json`）。

可参考 `examples/sample-resume-data.json` 的格式。

### 步骤 3：运行生成脚本

```bash
# 基本用法：生成 Markdown 简历
python3 scripts/generate_resume.py --input resume-data.json --format markdown

# 生成纯文本简历
python3 scripts/generate_resume.py --input resume-data.json --format text

# 生成 HTML 简历（可直接浏览器打开打印）
python3 scripts/generate_resume.py --input resume-data.json --format html

# 英文简历
python3 scripts/generate_resume.py --input resume-data.json --format markdown --lang en

# 指定输出文件
python3 scripts/generate_resume.py --input resume-data.json --format html --output my-resume.html

# 指定模板风格
python3 scripts/generate_resume.py --input resume-data.json --format markdown --style modern
```

### 步骤 4：验证和调整

- 检查生成的简历内容是否完整
- 确认时间排序是否正确（倒序）
- 如需要修改，编辑 JSON 数据文件后重新生成
- HTML 格式可在浏览器中预览，使用 Ctrl+P 打印为 PDF

### 步骤 5：输出交付

- Markdown 格式：可直接复制到支持 Markdown 的编辑器
- 纯文本格式：可直接粘贴到网申系统
- HTML 格式：可在浏览器中打开，打印为 PDF

## 五、命令行参数

| 参数 | 说明 | 默认值 |
|---|---|---|
| `--input` / `-i` | 输入 JSON 数据文件路径 | 必填 |
| `--format` / `-f` | 输出格式：markdown / text / html | markdown |
| `--lang` / `-l` | 语言：zh / en | zh |
| `--style` / `-s` | 模板风格：classic / concise / modern | classic |
| `--output` / `-o` | 输出文件路径（不指定则输出到终端） | - |
| `--template` / `-t` | 自定义模板文件路径（可选） | - |

## 六、模板风格说明

| 风格 | 特点 | 适用场景 |
|---|---|---|
| `classic`（经典） | 完整标题层级、分隔线、详细排版 | 正式求职、社招 |
| `concise`（简洁） | 紧凑布局、减少空行、突出重点 | 实习、校招、一页简历 |
| `modern`（现代） | 技能标签化、项目卡片式、时间线 | 互联网行业、创意岗位 |

## 七、常见场景处理

### 场景 1：应届生简历
**用户**：「我是应届生，帮我生成一份简历」
**处理**：重点突出教育背景、项目经验、技能，工作经历可填实习经历，使用 concise 风格。

### 场景 2：社招跳槽简历
**用户**：「我有 3 年工作经验，想换工作」
**处理**：重点突出工作经历和项目成果，使用 classic 风格，工作描述中量化成果。

### 场景 3：英文简历
**用户**：「帮我生成一份英文简历」
**处理**：使用 `--lang en`，日期格式改为 "Jan 2020 - Present"，职位和公司名用英文。

### 场景 4：快速生成
**用户**：「我只有基本信息，先帮我生成一个框架」
**处理**：基于已有信息生成，缺失部分标注「待补充」，用户可后续完善 JSON 后重新生成。

### 场景 5：HTML 打印 PDF
**用户**：「我要打印成 PDF」
**处理**：生成 HTML 格式，告知用户在浏览器中打开后 Ctrl+P 选择「另存为 PDF」。

## 八、注意事项

1. **数据驱动**：所有简历内容来自 JSON 数据文件，修改内容只需编辑 JSON
2. **时间排序**：工作经历、教育、项目自动按开始时间倒序排列
3. **占位符**：缺失信息标注「待补充」（中文）或「TBD」（英文），不编造内容
4. **一页原则**：建议简历控制在一页内，内容过多时使用 concise 风格
5. **量化成果**：工作描述建议包含数字（如"提升性能 30%"），脚本不会自动添加
6. **不包含照片**：默认不包含照片，如需照片在 HTML 中可通过 avatar 字段添加
7. **隐私保护**：简历包含个人信息，生成后提醒用户妥善保管
8. **纯标准库**：不需要安装任何第三方包

## 九、文件结构

```
resume-builder/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── resume-template-guide.md          # 简历写作指南与模板说明
├── scripts/
│   └── generate_resume.py                # 简历生成脚本
└── examples/
    ├── sample-resume-data.json           # 示例简历数据（中文）
    ├── sample-resume.md                  # 生成的 Markdown 简历示例
    └── sample-resume.html                # 生成的 HTML 简历示例
```

## 十、使用示例

### 示例 1：中文 Markdown 简历
**用户**：提供个人信息 JSON
**AI**：运行 `--input data.json --format markdown` → 输出格式规范的 Markdown 简历

### 示例 2：英文 HTML 简历
**用户**：「生成英文 HTML 简历」
**AI**：运行 `--input data.json --format html --lang en --output resume.html` → 生成可打印的 HTML 简历

### 示例 3：简洁风格
**用户**：「我要一页纸的简洁简历」
**AI**：运行 `--input data.json --format markdown --style concise` → 紧凑排版的简历
