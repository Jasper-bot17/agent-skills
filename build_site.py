#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能合集网站构建脚本
读取所有用户技能，生成一个自包含的单页 HTML 网站。
"""

import json
import os
import sys
from datetime import datetime

SKILLS_DIR = "/home/user/.doubao/agent_mode/workspace/.user_skills"
OUTPUT_DIR = "/home/user/Doubao/chats/38441283173235458/skill-collection-site"

# 技能分类映射
CATEGORY_MAP = {
    "meeting-notes-organizer": "办公效率",
    "git-commit-message-generator": "开发提效",
    "expense-tracker": "生活管理",
    "flashcard-generator": "学习辅助",
    "file-organizer": "效率工具",
    "text-readability-analyzer": "内容创作",
    "csv-data-cleaner": "数据处理",
    "regex-tester": "开发工具",
    "task-prioritizer": "时间管理",
    "date-extractor": "日程管理",
    "markdown-formatter": "文档工具",
    "json-formatter": "数据工具",
}

# 技能图标（emoji）
ICON_MAP = {
    "meeting-notes-organizer": "📝",
    "git-commit-message-generator": "🔧",
    "expense-tracker": "💰",
    "flashcard-generator": "🎴",
    "file-organizer": "📁",
    "text-readability-analyzer": "📖",
    "csv-data-cleaner": "🧹",
    "regex-tester": "🔍",
    "task-prioritizer": "📋",
    "date-extractor": "📅",
    "markdown-formatter": "📄",
    "json-formatter": "🔗",
}

CATEGORY_COLORS = {
    "办公效率": "#3b82f6",
    "开发提效": "#8b5cf6",
    "生活管理": "#10b981",
    "学习辅助": "#f59e0b",
    "效率工具": "#06b6d4",
    "内容创作": "#ec4899",
    "数据处理": "#14b8a6",
    "开发工具": "#6366f1",
    "时间管理": "#f97316",
    "日程管理": "#0ea5e9",
    "文档工具": "#84cc16",
    "数据工具": "#a855f7",
}


def parse_frontmatter(content):
    """解析 SKILL.md 的 frontmatter"""
    meta = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm = content[3:end]
            for line in fm.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip("'\"")
    return meta


def collect_skills():
    """收集所有技能信息和文件内容"""
    skills = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_path = os.path.join(SKILLS_DIR, name)
        if not os.path.isdir(skill_path):
            continue
        skill_md = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(skill_md):
            continue

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        meta = parse_frontmatter(content)
        category = CATEGORY_MAP.get(name, "其他")
        icon = ICON_MAP.get(name, "📦")

        # 收集所有文件
        files = {}
        for root, _, filenames in os.walk(skill_path):
            for fn in filenames:
                if fn == "__pycache__" or fn.endswith(".pyc"):
                    continue
                filepath = os.path.join(root, fn)
                relpath = os.path.relpath(filepath, skill_path)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        files[relpath] = f.read()
                except UnicodeDecodeError:
                    # 二进制文件跳过
                    continue

        # 统计文件数和脚本行数
        script_lines = 0
        for fpath, fcontent in files.items():
            if fpath.endswith(".py"):
                script_lines += len(fcontent.split("\n"))

        skills.append({
            "name": name,
            "title": meta.get("name", name),
            "description": meta.get("description", ""),
            "category": category,
            "icon": icon,
            "color": CATEGORY_COLORS.get(category, "#6b7280"),
            "skill_md": content,
            "files": files,
            "file_count": len(files),
            "script_lines": script_lines,
        })

    return skills


def generate_html(skills):
    """生成完整的 HTML 网站"""
    skills_json = json.dumps(skills, ensure_ascii=False)
    build_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agent 技能合集 | Skill Collection</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  min-height: 100vh;
}}
.hero {{
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 50%, #1e1b4b 100%);
  padding: 60px 20px 40px;
  text-align: center;
  border-bottom: 1px solid #334155;
}}
.hero h1 {{
  font-size: 2.5em;
  background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}}
.hero p {{ color: #94a3b8; font-size: 1.1em; margin-bottom: 24px; }}
.hero-stats {{
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}}
.stat {{ text-align: center; }}
.stat-num {{ font-size: 2em; font-weight: bold; color: #60a5fa; }}
.stat-label {{ color: #64748b; font-size: 0.9em; }}
.download-all-btn {{
  display: inline-block;
  margin-top: 24px;
  padding: 14px 32px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1em;
  cursor: pointer;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.download-all-btn:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
}}
.container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
.filters {{
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
  flex-wrap: wrap;
  align-items: center;
}}
.filter-btn {{
  padding: 8px 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 20px;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}}
.filter-btn:hover {{ border-color: #60a5fa; color: #e2e8f0; }}
.filter-btn.active {{
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}}
.search-box {{
  flex: 1;
  min-width: 200px;
  padding: 8px 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 20px;
  color: #e2e8f0;
  font-size: 0.9em;
  outline: none;
}}
.search-box:focus {{ border-color: #60a5fa; }}
.skill-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}}
.skill-card {{
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}}
.skill-card::before {{
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--card-color, #3b82f6);
}}
.skill-card:hover {{
  transform: translateY(-4px);
  border-color: #475569;
  box-shadow: 0 12px 30px rgba(0,0,0,0.3);
}}
.skill-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
.skill-icon {{ font-size: 2em; }}
.skill-name {{ font-size: 1.2em; font-weight: 600; color: #f1f5f9; }}
.skill-category {{
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.75em;
  color: white;
  background: var(--card-color, #3b82f6);
}}
.skill-desc {{
  color: #94a3b8;
  font-size: 0.9em;
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.skill-meta {{
  display: flex;
  gap: 16px;
  font-size: 0.8em;
  color: #64748b;
  margin-bottom: 16px;
}}
.skill-actions {{ display: flex; gap: 8px; }}
.btn {{
  padding: 8px 14px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 0.85em;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}}
.btn-primary {{ background: #3b82f6; color: white; }}
.btn-primary:hover {{ background: #2563eb; }}
.btn-secondary {{ background: #334155; color: #cbd5e1; }}
.btn-secondary:hover {{ background: #475569; }}
.modal {{
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7);
  z-index: 1000;
  overflow-y: auto;
}}
.modal.active {{ display: flex; justify-content: center; padding: 40px 20px; }}
.modal-content {{
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  max-width: 900px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  position: relative;
}}
.modal-header {{
  padding: 24px;
  border-bottom: 1px solid #334155;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}}
.modal-close {{
  background: none;
  border: none;
  color: #64748b;
  font-size: 1.5em;
  cursor: pointer;
}}
.modal-close:hover {{ color: #e2e8f0; }}
.modal-body {{ padding: 24px; }}
.modal-body h1, .modal-body h2, .modal-body h3 {{
  color: #f1f5f9;
  margin: 20px 0 10px;
}}
.modal-body h1 {{ font-size: 1.5em; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
.modal-body h2 {{ font-size: 1.25em; }}
.modal-body h3 {{ font-size: 1.1em; }}
.modal-body p {{ color: #cbd5e1; line-height: 1.8; margin: 8px 0; }}
.modal-body ul, .modal-body ol {{ color: #cbd5e1; padding-left: 24px; margin: 8px 0; }}
.modal-body li {{ margin: 4px 0; line-height: 1.7; }}
.modal-body code {{
  background: #0f172a;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
  color: #7dd3fc;
}}
.modal-body pre {{
  background: #0f172a;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}}
.modal-body pre code {{ background: none; padding: 0; }}
.modal-body table {{
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}}
.modal-body th, .modal-body td {{
  border: 1px solid #334155;
  padding: 8px 12px;
  text-align: left;
}}
.modal-body th {{ background: #0f172a; color: #f1f5f9; }}
.modal-body blockquote {{
  border-left: 3px solid #3b82f6;
  padding-left: 16px;
  color: #94a3b8;
  margin: 12px 0;
}}
.file-list {{
  margin-top: 20px;
  padding: 16px;
  background: #0f172a;
  border-radius: 8px;
}}
.file-list h4 {{ color: #f1f5f9; margin-bottom: 8px; }}
.file-item {{
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #1e293b;
  font-size: 0.85em;
}}
.file-item:last-child {{ border-bottom: none; }}
.file-name {{ color: #94a3b8; font-family: monospace; }}
.file-size {{ color: #64748b; }}
.footer {{
  text-align: center;
  padding: 40px 20px;
  color: #475569;
  font-size: 0.85em;
  border-top: 1px solid #1e293b;
}}
.toast {{
  position: fixed;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  background: #1e293b;
  border: 1px solid #3b82f6;
  color: #e2e8f0;
  padding: 12px 24px;
  border-radius: 8px;
  z-index: 2000;
  display: none;
}}
.toast.show {{ display: block; animation: fadeIn 0.3s; }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@media (max-width: 600px) {{
  .hero h1 {{ font-size: 1.8em; }}
  .skill-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<div class="hero">
  <h1>🤖 AI Agent 技能合集</h1>
  <p>实用、可复用的 Agent Skills — 浏览、下载、即刻使用</p>
  <div class="hero-stats">
    <div class="stat"><div class="stat-num" id="total-skills">0</div><div class="stat-label">技能数量</div></div>
    <div class="stat"><div class="stat-num" id="total-categories">0</div><div class="stat-label">覆盖场景</div></div>
    <div class="stat"><div class="stat-num" id="total-files">0</div><div class="stat-label">文件总数</div></div>
  </div>
  <button class="download-all-btn" onclick="downloadAll()">📦 下载全部技能 (ZIP)</button>
</div>

<div class="container">
  <div class="filters">
    <input type="text" class="search-box" id="search" placeholder="🔍 搜索技能名称或描述..." oninput="renderSkills()">
    <button class="filter-btn active" data-cat="all" onclick="setFilter('all', this)">全部</button>
  </div>
  <div class="skill-grid" id="skill-grid"></div>
</div>

<div class="modal" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal-content">
    <div class="modal-header">
      <div>
        <div class="skill-header">
          <span class="skill-icon" id="modal-icon"></span>
          <div>
            <div class="skill-name" id="modal-name"></div>
            <span class="skill-category" id="modal-category"></span>
          </div>
        </div>
      </div>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
    <div style="padding: 16px 24px; border-top: 1px solid #334155; display: flex; gap: 8px;">
      <button class="btn btn-primary" onclick="downloadSkill(currentSkill)">📥 下载此技能</button>
      <button class="btn btn-secondary" onclick="copySkillMd()">📋 复制 SKILL.md</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<div class="footer">
  <p>构建时间：{build_date} | 共 <span id="footer-count">0</span> 个技能 | 纯静态网站，可部署到任意托管平台</p>
</div>

<script>
const SKILLS = {skills_json};
let currentSkill = null;
let currentFilter = 'all';

// 初始化
function init() {{
  const categories = [...new Set(SKILLS.map(s => s.category))];
  const filterContainer = document.querySelector('.filters');
  categories.forEach(cat => {{
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.dataset.cat = cat;
    btn.textContent = cat;
    btn.onclick = () => setFilter(cat, btn);
    filterContainer.insertBefore(btn, filterContainer.querySelector('.search-box').nextSibling);
  }});

  document.getElementById('total-skills').textContent = SKILLS.length;
  document.getElementById('total-categories').textContent = categories.length;
  document.getElementById('total-files').textContent = SKILLS.reduce((a, s) => a + s.file_count, 0);
  document.getElementById('footer-count').textContent = SKILLS.length;

  renderSkills();
}}

function setFilter(cat, btn) {{
  currentFilter = cat;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderSkills();
}}

function renderSkills() {{
  const search = document.getElementById('search').value.toLowerCase();
  const grid = document.getElementById('skill-grid');
  const filtered = SKILLS.filter(s => {{
    const matchCat = currentFilter === 'all' || s.category === currentFilter;
    const matchSearch = !search || s.name.toLowerCase().includes(search) || s.description.toLowerCase().includes(search);
    return matchCat && matchSearch;
  }});

  grid.innerHTML = filtered.map(s => `
    <div class="skill-card" style="--card-color: ${{s.color}}" onclick="openModal('${{s.name}}')">
      <div class="skill-header">
        <span class="skill-icon">${{s.icon}}</span>
        <div>
          <div class="skill-name">${{s.name}}</div>
          <span class="skill-category" style="background: ${{s.color}}">${{s.category}}</span>
        </div>
      </div>
      <div class="skill-desc">${{s.description}}</div>
      <div class="skill-meta">
        <span>📄 ${{s.file_count}} 个文件</span>
        <span>📝 ${{s.script_lines}} 行代码</span>
      </div>
      <div class="skill-actions">
        <button class="btn btn-primary" onclick="event.stopPropagation();openModal('${{s.name}}')">查看详情</button>
        <button class="btn btn-secondary" onclick="event.stopPropagation();downloadSkillByName('${{s.name}}')">下载</button>
      </div>
    </div>
  `).join('');
}}

// 简单 Markdown 渲染
function renderMarkdown(text) {{
  // 移除 frontmatter
  text = text.replace(/^---\\n[\\s\\S]*?\\n---\\n/, '');
  let html = text;
  // 代码块
  html = html.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>');
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // 标题
  html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>');
  html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>');
  html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');
  // 粗体和斜体
  html = html.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  html = html.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
  // 引用
  html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>');
  // 表格
  html = html.replace(/\\|(.+)\\|\\n\\|[\\s\\-:|]+\\|\\n((?:\\|.+\\|\\n?)*)/g, (m, header, body) => {{
    const ths = header.split('|').filter(Boolean).map(h => `<th>${{h.trim()}}</th>`).join('');
    const trs = body.trim().split('\\n').map(row => {{
      const tds = row.split('|').filter(Boolean).map(d => `<td>${{d.trim()}}</td>`).join('');
      return `<tr>${{tds}}</tr>`;
    }}).join('');
    return `<table><thead><tr>${{ths}}</tr></thead><tbody>${{trs}}</tbody></table>`;
  }});
  // 列表
  html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\\/li>\\n?)+/g, m => `<ul>${{m}}</ul>`);
  html = html.replace(/^\\d+\\. (.*)$/gm, '<li>$1</li>');
  // 段落
  html = html.replace(/\\n\\n/g, '</p><p>');
  html = '<p>' + html + '</p>';
  // 清理空段落
  html = html.replace(/<p><\\/p>/g, '');
  return html;
}}

function openModal(name) {{
  const skill = SKILLS.find(s => s.name === name);
  if (!skill) return;
  currentSkill = skill;
  document.getElementById('modal-icon').textContent = skill.icon;
  document.getElementById('modal-name').textContent = skill.name;
  const catEl = document.getElementById('modal-category');
  catEl.textContent = skill.category;
  catEl.style.background = skill.color;

  let body = renderMarkdown(skill.skill_md);
  // 文件列表
  body += '<div class="file-list"><h4>📁 包含文件</h4>';
  for (const [fname, fcontent] of Object.entries(skill.files)) {{
    const size = new Blob([fcontent]).size;
    body += `<div class="file-item"><span class="file-name">${{fname}}</span><span class="file-size">${{size}} bytes</span></div>`;
  }}
  body += '</div>';
  document.getElementById('modal-body').innerHTML = body;
  document.getElementById('modal').classList.add('active');
}}

function closeModal() {{
  document.getElementById('modal').classList.remove('active');
}}

function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}}

async function downloadSkill(skill) {{
  const zip = new JSZip();
  const folder = zip.folder(skill.name);
  for (const [fname, fcontent] of Object.entries(skill.files)) {{
    folder.file(fname, fcontent);
  }}
  const blob = await zip.generateAsync({{type: 'blob'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = skill.name + '.zip';
  a.click();
  URL.revokeObjectURL(url);
  showToast('已下载 ' + skill.name + '.zip');
}}

function downloadSkillByName(name) {{
  const skill = SKILLS.find(s => s.name === name);
  if (skill) downloadSkill(skill);
}}

async function downloadAll() {{
  showToast('正在打包全部技能...');
  const zip = new JSZip();
  for (const skill of SKILLS) {{
    const folder = zip.folder(skill.name);
    for (const [fname, fcontent] of Object.entries(skill.files)) {{
      folder.file(fname, fcontent);
    }}
  }}
  // 添加 README
  zip.file('README.md', '# AI Agent 技能合集\\n\\n共 ' + SKILLS.length + ' 个技能。\\n\\n每个技能目录包含 SKILL.md（技能定义）、scripts/（可执行脚本）、templates/（模板）、examples/（示例）。\\n\\n使用方法：将技能目录放入 AI 的 skills 目录，或直接阅读 SKILL.md 按说明使用。');
  const blob = await zip.generateAsync({{type: 'blob'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ai-agent-skills-collection.zip';
  a.click();
  URL.revokeObjectURL(url);
  showToast('已下载全部技能合集');
}}

function copySkillMd() {{
  if (!currentSkill) return;
  navigator.clipboard.writeText(currentSkill.skill_md).then(() => {{
    showToast('SKILL.md 已复制到剪贴板');
  }});
}}

// ESC 关闭弹窗
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeModal();
}});

init();
</script>
</body>
</html>"""
    return html


def main():
    print("收集技能信息...")
    skills = collect_skills()
    print(f"找到 {len(skills)} 个技能")

    print("生成网站...")
    html = generate_html(skills)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(output_path)
    print(f"✅ 网站已生成：{output_path}")
    print(f"   文件大小：{size:,} 字节 ({size/1024:.1f} KB)")
    print(f"   技能数量：{len(skills)}")


if __name__ == "__main__":
    main()
