# AI Agent 技能合集网站 - 部署指南

## 快速部署（推荐：GitHub Pages，免费永久）

### 方法一：GitHub Pages（推荐，免费且永久）

1. **创建 GitHub 仓库**
   - 登录 https://github.com
   - 点击 "New repository"
   - 仓库名建议：`ai-agent-skills`
   - 选择 Public，勾选 "Add a README file"
   - 点击 Create repository

2. **上传网站文件**
   - 在仓库页面点击 "Add file" → "Upload files"
   - 上传 `index.html`
   - 点击 "Commit changes"

3. **启用 GitHub Pages**
   - 进入仓库 Settings → Pages
   - Source 选择 "Deploy from a branch"
   - Branch 选择 `main`，文件夹选择 `/ (root)`
   - 点击 Save
   - 等待 1-2 分钟，网站地址为：`https://<你的用户名>.github.io/ai-agent-skills/`

### 方法二：Netlify（免费，无需 GitHub）

1. 访问 https://app.netlify.com/drop
2. 将 `index.html` 拖放到页面上
3. 网站立即上线（地址类似 `https://random-name.netlify.app`）
4. 注册免费账号可永久保留并自定义域名

### 方法三：Vercel（免费，适合开发者）

1. 安装 CLI：`npm i -g vercel`
2. 在网站目录运行：`vercel`
3. 按提示登录（可用 GitHub 账号）
4. 部署完成，获得 `*.vercel.app` 域名

### 方法四：本地使用（无需部署）

直接双击 `index.html` 在浏览器中打开即可，所有功能（浏览、下载）完全可用。

---

## 更新网站

当有新技能添加后，重新运行构建脚本：

```bash
python3 build_site.py
```

然后将新生成的 `index.html` 重新上传到你的托管平台即可。

如果使用 GitHub Pages，可以设置 GitHub Actions 自动部署（可选）。

---

## 网站功能

- 📋 浏览所有技能（卡片式展示）
- 🔍 按分类筛选和关键词搜索
- 📖 查看技能详情（SKILL.md 完整内容渲染）
- 📥 下载单个技能（ZIP 包）
- 📦 一键下载全部技能（ZIP 包）
- 📋 复制 SKILL.md 到剪贴板
- 📊 技能统计（数量、分类、文件数、代码行数）

---

## 文件说明

| 文件 | 说明 |
|---|---|
| `index.html` | 完整网站（单文件，自包含） |
| `build_site.py` | 网站构建脚本，从技能目录重新生成网站 |
| `DEPLOY.md` | 本部署指南 |
