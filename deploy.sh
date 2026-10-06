#!/bin/bash
# 一键构建并部署技能合集网站到 GitHub Pages
# 使用前需先完成一次性设置：
#   1. 在 GitHub 创建仓库（如 ai-agent-skills）
#   2. git clone 到本地
#   3. 将本脚本和 build_site.py 放入仓库目录
#   4. gh auth login 完成登录

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 正在构建网站..."
python3 build_site.py

echo ""
echo "📦 正在部署到 GitHub Pages..."

# 检查是否在 git 仓库中
if [ ! -d ".git" ]; then
    echo "❌ 当前目录不是 git 仓库"
    echo "请先执行：git init && git remote add origin <你的仓库地址>"
    exit 1
fi

git add index.html
git commit -m "更新技能合集网站 $(date '+%Y-%m-%d %H:%M')" || echo "无更新"
git push origin main

echo ""
echo "✅ 部署完成！"
echo "网站地址：https://<你的用户名>.github.io/<仓库名>/"
