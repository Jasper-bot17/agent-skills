---
name: color-palette-generator
description: '配色方案生成助手。输入一个基础颜色（HEX/RGB/HSL），自动生成多种配色方案（互补色、类比色、三角色、四角色、分裂互补、单色渐变），支持颜色格式互转（HEX/RGB/HSL/HSV），计算 WCAG 对比度比率并检查无障碍合规性（AA/AAA 标准），生成 CSS 变量和 Tailwind 配置，终端可视化预览配色效果。适用于网页设计、UI 设计、品牌配色、数据可视化配色等场景。'
---

# 配色方案生成助手

## 一、技能定位

本技能用于**生成和分析配色方案**。核心价值：

- 从一个基础颜色自动生成 6 种专业配色方案
- 颜色格式互转（HEX / RGB / HSL / HSV）
- WCAG 对比度计算与无障碍合规检查
- 生成 CSS 变量和 Tailwind 配置
- 终端可视化预览配色效果
- 保存和加载配色方案

## 二、触发场景

当用户出现以下需求时使用本技能：

1. 用户说「帮我生成一个配色方案」「选个配色」
2. 用户说「这个颜色的互补色是什么」「生成类比色」
3. 用户说「检查一下这两个颜色的对比度」「是否符合无障碍标准」
4. 用户说「把这个颜色转成 RGB/HSL」「颜色格式转换」
5. 用户说「生成 CSS 变量」「生成 Tailwind 配色配置」
6. 用户说「帮我设计一个网站配色」「品牌配色方案」
7. 用户说「数据可视化用什么颜色好」「图表配色」

## 三、支持的配色方案

### 3.1 互补色（Complementary）
基础色与色轮上对面 180° 的颜色组合，对比强烈，适合需要突出重点的场景。

### 3.2 类比色（Analogous）
色轮上相邻的 3-5 个颜色，和谐统一，适合背景和大面积使用。

### 3.3 三角色（Triadic）
色轮上等距 120° 的三个颜色，平衡且富有活力，适合需要多种主色的设计。

### 3.4 四角色（Tetradic / Square）
色轮上等距 90° 的四个颜色，丰富多变，适合复杂的多色设计。

### 3.5 分裂互补（Split Complementary）
基础色 + 互补色两侧的颜色，比互补色更柔和，对比仍然明显。

### 3.6 单色渐变（Monochromatic）
同一色相的不同明度和饱和度变化，简约高级，适合极简风格。

## 四、颜色格式

| 格式 | 示例 | 说明 |
|---|---|---|
| HEX | `#3498DB` | 十六进制，网页最常用 |
| RGB | `rgb(52, 152, 219)` | 红绿蓝，0-255 |
| HSL | `hsl(204, 70%, 53%)` | 色相/饱和度/明度 |
| HSV | `hsv(204, 76%, 86%)` | 色相/饱和度/明度（不同算法） |

## 五、WCAG 无障碍标准

### 5.1 对比度等级

| 等级 | 普通文本 | 大文本（18pt+ 或 14pt+粗体） |
|---|---|---|
| AA（最低标准） | ≥ 4.5:1 | ≥ 3:1 |
| AAA（最高标准） | ≥ 7:1 | ≥ 4.5:1 |

### 5.2 对比度计算公式

```
L = 0.2126 × R + 0.7152 × G + 0.0722 × B
（其中 R/G/B 需先做 gamma 校正）
对比度 = (L1 + 0.05) / (L2 + 0.05)
（L1 为较亮颜色的相对亮度，L2 为较暗颜色）
```

## 六、操作步骤

### 步骤 1：确认需求

确认用户需要：
- 生成配色方案 / 颜色格式转换 / 对比度检查 / 生成配置文件
- 基础颜色（HEX/RGB/HSL 格式）
- 配色方案类型（默认全部生成）
- 输出格式

### 步骤 2：运行脚本

使用 `scripts/generate_palette.py`：

```bash
# 生成所有配色方案（输入 HEX 颜色）
python3 scripts/generate_palette.py --color "#3498DB"

# 输入 RGB 颜色
python3 scripts/generate_palette.py --color "rgb(52,152,219)"

# 输入 HSL 颜色
python3 scripts/generate_palette.py --color "hsl(204,70%,53%)"

# 只生成特定方案
python3 scripts/generate_palette.py --color "#3498DB" --scheme complementary,triadic

# 颜色格式转换
python3 scripts/generate_palette.py --color "#3498DB" --convert

# 对比度检查（前景色 vs 背景色）
python3 scripts/generate_palette.py --color "#FFFFFF" --contrast "#3498DB"

# 生成 CSS 变量
python3 scripts/generate_palette.py --color "#3498DB" --format css

# 生成 Tailwind 配置
python3 scripts/generate_palette.py --color "#3498DB" --format tailwind

# 保存配色方案到文件
python3 scripts/generate_palette.py --color "#3498DB" --save my-palette.json

# 从文件加载配色方案
python3 scripts/generate_palette.py --load my-palette.json

# JSON 格式输出
python3 scripts/generate_palette.py --color "#3498DB" --format json
```

### 步骤 3：解读结果

- **配色方案**：每种方案包含多个颜色，每个颜色显示 HEX/RGB/HSL
- **终端预览**：用 ANSI 颜色块直观展示配色效果
- **对比度报告**：显示对比度比率和 AA/AAA 合规性
- **CSS/Tailwind**：可直接复制使用的配置代码

### 步骤 4：安全提示

1. 本技能只做颜色计算和生成，不涉及网络请求
2. 配色方案仅供参考，最终效果需在实际设计中验证
3. 无障碍检查基于 WCAG 2.1 标准，实际可读性还受字体、大小等因素影响

## 七、输出规范

### 7.1 配色方案列表

```
🎨 配色方案生成
━━━━━━━━━━━━━━━━━━━━━━━━
基础颜色：#3498DB (RGB: 52,152,219 | HSL: 204°,70%,53%)

【互补色 Complementary】
  #3498DB  ████████  主色
  #DB7734  ████████  互补色

【类比色 Analogous】
  #34DBBF  ████████  类比色1
  #3498DB  ████████  主色
  #3451DB  ████████  类比色2

【三角色 Triadic】
  #3498DB  ████████  主色
  #98DB34  ████████  三角色1
  #DB3498  ████████  三角色2
...
```

### 7.2 对比度报告

```
📊 对比度检查
━━━━━━━━━━━━━━━━━━━━━━━━
前景色：#FFFFFF (白色)
背景色：#3498DB (蓝色)

对比度比率：4.34 : 1

无障碍合规性：
  ✅ AA 大文本：通过 (≥ 3:1)
  ❌ AA 普通文本：未通过 (需要 ≥ 4.5:1)
  ❌ AAA 大文本：未通过 (需要 ≥ 4.5:1)
  ❌ AAA 普通文本：未通过 (需要 ≥ 7:1)

建议：
  - 用于大文本或图形元素
  - 如需用于普通文本，建议加深背景色至 #2980B9 (对比度 5.12:1)
```

### 7.3 CSS 变量输出

```css
:root {
  /* 主色 */
  --color-primary: #3498DB;
  --color-primary-light: #5DADE2;
  --color-primary-dark: #2980B9;

  /* 互补色 */
  --color-complementary: #DB7734;

  /* 三角色 */
  --color-triadic-1: #98DB34;
  --color-triadic-2: #DB3498;

  /* 中性色 */
  --color-bg: #F8F9FA;
  --color-text: #2C3E50;
  --color-muted: #7F8C8D;
}
```

### 7.4 Tailwind 配置输出

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EBF5FB',
          100: '#D6EAF8',
          200: '#AED6F1',
          300: '#85C1E9',
          400: '#5DADE2',
          500: '#3498DB',
          600: '#2E86C1',
          700: '#2874A6',
          800: '#21618C',
          900: '#1B4F72',
        },
      },
    },
  },
}
```

## 八、常见场景处理

### 场景 1：网站主色配色
**用户**：「我选了 #3498DB 作为网站主色，帮我生成完整配色」
**处理**：生成所有配色方案 → 生成 CSS 变量 → 检查主色与白色/黑色的对比度 → 给出使用建议。

### 场景 2：无障碍检查
**用户**：「这个文字颜色在这个背景上能看清吗」
**处理**：计算对比度比率 → 检查 AA/AAA 合规性 → 如不通过，给出调整建议（加深/变亮）。

### 场景 3：颜色格式转换
**用户**：「把 #FF5733 转成 RGB 和 HSL」
**处理**：解析 HEX → 转换为 RGB → 转换为 HSL/HSV → 输出所有格式。

### 场景 4：数据可视化配色
**用户**：「做图表需要 5 个区分度高的颜色」
**处理**：生成三角色/四角色方案 → 检查颜色间的区分度 → 给出 5 色方案。

### 场景 5：品牌配色
**用户**：「帮我设计一个科技感的品牌配色」
**处理**：以蓝色/紫色为基础 → 生成互补/类比方案 → 生成完整 CSS 配置 → 终端预览。

## 九、注意事项

1. **颜色输入格式**：支持 `#RRGGBB`、`#RGB`、`rgb(r,g,b)`、`hsl(h,s%,l%)` 四种格式。
2. **终端预览**：颜色块预览需要终端支持 24-bit 真彩色，不支持时会退化为 HEX 文本显示。
3. **对比度计算**：基于 WCAG 2.1 相对亮度公式，结果精确到小数点后两位。
4. **大文本定义**：WCAG 定义大文本为 18pt（约 24px）以上，或 14pt（约 18.66px）粗体以上。
5. **配色方案理论**：基于传统色轮理论（RYB），实际视觉效果可能因屏幕和色彩空间而异。
6. **单色渐变**：生成 5 个明度阶梯（100-900），类似 Tailwind 的色阶体系。
7. **保存格式**：配色方案保存为 JSON 文件，包含所有颜色的 HEX/RGB/HSL 信息。
8. **CSS 输出**：包含主色、浅色、深色变体，以及互补色和中性色，可直接使用。
9. **Tailwind 输出**：生成 50-900 共 10 个色阶，符合 Tailwind 配色规范。
10. **不修改文件**：本技能只读取输入和生成输出，不会修改任何已有文件。

## 十、文件结构

```
color-palette-generator/
├── SKILL.md                              # 本文件，技能定义与使用说明
├── templates/
│   └── color-theory-reference.md          # 色彩理论参考与配色指南
├── scripts/
│   └── generate_palette.py                # 配色方案生成脚本
└── examples/
    ├── sample-palette.json                # 示例配色方案（JSON）
    ├── sample-css-variables.css           # 示例 CSS 变量输出
    └── sample-contrast-report.md          # 示例对比度检查报告
```

## 十一、使用示例

### 示例 1：快速生成配色
**用户**：「用 #2ECC71 生成配色方案」
**AI**：运行 `--color "#2ECC71"` → 输出 6 种配色方案 + 终端预览。

### 示例 2：对比度检查
**用户**：「白色文字在 #E74C3C 背景上能看清吗」
**AI**：运行 `--color "#FFFFFF" --contrast "#E74C3C"` → 输出对比度比率和合规性。

### 示例 3：生成配置
**用户**：「生成 Tailwind 配色配置」
**AI**：运行 `--color "#9B59B6" --format tailwind` → 输出可直接复制的 Tailwind 配置。
