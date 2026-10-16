#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
简历生成脚本

功能：
- 从 JSON 数据文件读取简历信息
- 自动按时间倒序排列工作经历、教育背景、项目经验
- 支持 Markdown、纯文本、HTML 三种输出格式
- 支持中英文双语简历
- 支持 classic / concise / modern 三种模板风格
- 纯 Python 标准库，无外部依赖

用法：
  python3 generate_resume.py --input resume.json --format markdown
  python3 generate_resume.py --input resume.json --format html --lang en
  python3 generate_resume.py --input resume.json --format text --style concise --output resume.txt
"""

import argparse
import json
import sys
from datetime import datetime


# ============================================================
# 国际化文本
# ============================================================

I18N = {
    "zh": {
        "objective": "求职意向",
        "position": "目标职位",
        "summary": "个人简介",
        "experience": "工作经历",
        "education": "教育背景",
        "skills": "专业技能",
        "projects": "项目经验",
        "certifications": "证书资质",
        "languages": "语言能力",
        "present": "至今",
        "tbd": "待补充",
        "gpa": "GPA",
        "tech_stack": "技术栈",
        "role": "角色",
    },
    "en": {
        "objective": "Objective",
        "position": "Target Position",
        "summary": "Summary",
        "experience": "Work Experience",
        "education": "Education",
        "skills": "Skills",
        "projects": "Projects",
        "certifications": "Certifications",
        "languages": "Languages",
        "present": "Present",
        "tbd": "TBD",
        "gpa": "GPA",
        "tech_stack": "Tech Stack",
        "role": "Role",
    },
}


# ============================================================
# 工具函数
# ============================================================

def parse_date(date_str):
    """解析日期字符串为可比较的元组 (year, month)"""
    if not date_str:
        return (0, 0)
    date_str = str(date_str).strip()
    # 处理 "至今" / "Present"
    if date_str in ("至今", "Present", "present", "now", "Now"):
        return (9999, 12)
    # 尝试 YYYY-MM
    for fmt in ("%Y-%m", "%Y/%m", "%Y.%m"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return (dt.year, dt.month)
        except ValueError:
            pass
    # 尝试 YYYY年MM月
    try:
        cleaned = date_str.replace("年", "-").replace("月", "").replace(" ", "")
        dt = datetime.strptime(cleaned, "%Y-%m")
        return (dt.year, dt.month)
    except ValueError:
        pass
    # 尝试只有年份 YYYY
    try:
        year = int(date_str[:4])
        return (year, 0)
    except (ValueError, IndexError):
        pass
    return (0, 0)


def format_date(date_str, lang="zh"):
    """格式化日期显示"""
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    if date_str in ("至今", "Present", "present", "now", "Now"):
        return I18N[lang]["present"]
    return date_str


def sort_by_date(items, date_field="start_date"):
    """按日期倒序排列"""
    return sorted(items, key=lambda x: parse_date(x.get(date_field, "")), reverse=True)


def safe_get(data, key, default=""):
    """安全获取字典值"""
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def has_content(data, key):
    """检查字段是否有实际内容"""
    val = safe_get(data, key)
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, list):
        return len(val) > 0
    if isinstance(val, dict):
        return len(val) > 0
    return val is not None


# ============================================================
# Markdown 生成器
# ============================================================

class MarkdownGenerator:
    def __init__(self, data, lang="zh", style="classic"):
        self.data = data
        self.lang = lang
        self.style = style
        self.t = I18N[lang]

    def generate(self):
        lines = []
        personal = safe_get(self.data, "personal", {})

        # 标题：姓名
        name = safe_get(personal, "name", self.t["tbd"])
        title = safe_get(personal, "title", "")
        if self.style == "concise":
            lines.append(f"# {name}")
            if title:
                lines.append(f"**{title}**")
        else:
            lines.append(f"# {name}")
            if title:
                lines.append(f"## {title}")

        # 联系方式
        contact_parts = []
        for field, label in [("email", ""), ("phone", ""), ("location", ""),
                             ("website", ""), ("github", ""), ("linkedin", "")]:
            val = safe_get(personal, field)
            if val:
                contact_parts.append(val)
        if contact_parts:
            lines.append(" | ".join(contact_parts))

        lines.append("")

        # 求职意向
        objective = safe_get(self.data, "objective", {})
        if has_content(objective, "position") or has_content(objective, "summary"):
            lines.append(f"## {self.t['objective']}")
            lines.append("")
            if has_content(objective, "position"):
                lines.append(f"**{self.t['position']}：** {safe_get(objective, 'position')}")
                lines.append("")
            if has_content(objective, "summary"):
                lines.append(safe_get(objective, "summary"))
                lines.append("")

        # 工作经历
        experience = safe_get(self.data, "experience", [])
        if experience:
            lines.append(f"## {self.t['experience']}")
            lines.append("")
            for exp in sort_by_date(experience):
                company = safe_get(exp, "company", self.t["tbd"])
                position = safe_get(exp, "position", "")
                start = format_date(safe_get(exp, "start_date"), self.lang)
                end = format_date(safe_get(exp, "end_date"), self.lang)
                location = safe_get(exp, "location", "")
                date_range = f"{start} - {end}" if end else start

                if self.style == "concise":
                    header = f"**{company}** — {position}"
                    lines.append(f"### {header}")
                    lines.append(f"_{date_range}_" + (f" · {location}" if location else ""))
                else:
                    lines.append(f"### {company}")
                    lines.append(f"**{position}** | {date_range}" + (f" | {location}" if location else ""))

                desc = safe_get(exp, "description", [])
                if desc:
                    for d in desc:
                        if d.strip():
                            lines.append(f"- {d}")
                lines.append("")

        # 项目经验
        projects = safe_get(self.data, "projects", [])
        if projects:
            lines.append(f"## {self.t['projects']}")
            lines.append("")
            for proj in sort_by_date(projects):
                name = safe_get(proj, "name", self.t["tbd"])
                role = safe_get(proj, "role", "")
                start = format_date(safe_get(proj, "start_date"), self.lang)
                end = format_date(safe_get(proj, "end_date"), self.lang)
                date_range = f"{start} - {end}" if end else start
                link = safe_get(proj, "link", "")

                if self.style == "modern":
                    lines.append(f"### {name}")
                    meta_parts = []
                    if role:
                        meta_parts.append(f"{self.t['role']}: {role}")
                    if date_range:
                        meta_parts.append(date_range)
                    if link:
                        meta_parts.append(link)
                    if meta_parts:
                        lines.append(" | ".join(meta_parts))
                else:
                    header = f"**{name}**"
                    if role:
                        header += f" — {role}"
                    lines.append(f"### {header}")
                    if date_range:
                        lines.append(f"_{date_range}_")

                tech = safe_get(proj, "tech_stack", [])
                if tech:
                    lines.append(f"*{self.t['tech_stack']}: {'、'.join(tech)}*")

                desc = safe_get(proj, "description", [])
                if desc:
                    for d in desc:
                        if d.strip():
                            lines.append(f"- {d}")
                lines.append("")

        # 教育背景
        education = safe_get(self.data, "education", [])
        if education:
            lines.append(f"## {self.t['education']}")
            lines.append("")
            for edu in sort_by_date(education):
                school = safe_get(edu, "school", self.t["tbd"])
                degree = safe_get(edu, "degree", "")
                major = safe_get(edu, "major", "")
                start = format_date(safe_get(edu, "start_date"), self.lang)
                end = format_date(safe_get(edu, "end_date"), self.lang)
                gpa = safe_get(edu, "gpa", "")
                date_range = f"{start} - {end}" if end else start

                header = f"**{school}**"
                details = []
                if degree:
                    details.append(degree)
                if major:
                    details.append(major)
                if details:
                    header += f" — {' · '.join(details)}"
                lines.append(f"### {header}")
                meta = date_range
                if gpa:
                    meta += f" | {self.t['gpa']}: {gpa}"
                lines.append(meta)

                desc = safe_get(edu, "description", [])
                if desc:
                    for d in desc:
                        if d.strip():
                            lines.append(f"- {d}")
                lines.append("")

        # 技能
        skills = safe_get(self.data, "skills", [])
        if skills:
            lines.append(f"## {self.t['skills']}")
            lines.append("")
            for skill_group in skills:
                category = safe_get(skill_group, "category", "")
                items = safe_get(skill_group, "items", [])
                if self.style == "modern":
                    tags = " ".join(f"`{item}`" for item in items)
                    lines.append(f"**{category}**: {tags}")
                else:
                    lines.append(f"- **{category}**: {'、'.join(items)}")
            lines.append("")

        # 证书
        certs = safe_get(self.data, "certifications", [])
        if certs:
            lines.append(f"## {self.t['certifications']}")
            lines.append("")
            for cert in certs:
                if isinstance(cert, str):
                    lines.append(f"- {cert}")
                elif isinstance(cert, dict):
                    name = safe_get(cert, "name", "")
                    issuer = safe_get(cert, "issuer", "")
                    date = format_date(safe_get(cert, "date"), self.lang)
                    parts = [p for p in [name, issuer, date] if p]
                    lines.append(f"- {' | '.join(parts)}")
            lines.append("")

        # 语言能力
        languages = safe_get(self.data, "languages", [])
        if languages:
            lines.append(f"## {self.t['languages']}")
            lines.append("")
            for lang_item in languages:
                if isinstance(lang_item, str):
                    lines.append(f"- {lang_item}")
                elif isinstance(lang_item, dict):
                    lang_name = safe_get(lang_item, "language", "")
                    level = safe_get(lang_item, "level", "")
                    lines.append(f"- {lang_name}: {level}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


# ============================================================
# 纯文本生成器
# ============================================================

class TextGenerator:
    def __init__(self, data, lang="zh", style="classic"):
        self.data = data
        self.lang = lang
        self.style = style
        self.t = I18N[lang]

    def _section_header(self, title):
        if self.style == "concise":
            return f"【{title}】"
        return f"{'=' * 50}\n{title}\n{'=' * 50}"

    def generate(self):
        lines = []
        personal = safe_get(self.data, "personal", {})

        # 姓名和标题
        name = safe_get(personal, "name", self.t["tbd"])
        title = safe_get(personal, "title", "")
        lines.append(name)
        if title:
            lines.append(title)

        # 联系方式
        contact_parts = []
        for field in ["email", "phone", "location", "website", "github", "linkedin"]:
            val = safe_get(personal, field)
            if val:
                contact_parts.append(val)
        if contact_parts:
            lines.append(" | ".join(contact_parts))
        lines.append("")

        # 求职意向
        objective = safe_get(self.data, "objective", {})
        if has_content(objective, "position") or has_content(objective, "summary"):
            lines.append(self._section_header(self.t["objective"]))
            if has_content(objective, "position"):
                lines.append(f"{self.t['position']}: {safe_get(objective, 'position')}")
            if has_content(objective, "summary"):
                lines.append(safe_get(objective, "summary"))
            lines.append("")

        # 工作经历
        experience = safe_get(self.data, "experience", [])
        if experience:
            lines.append(self._section_header(self.t["experience"]))
            for exp in sort_by_date(experience):
                company = safe_get(exp, "company", self.t["tbd"])
                position = safe_get(exp, "position", "")
                start = format_date(safe_get(exp, "start_date"), self.lang)
                end = format_date(safe_get(exp, "end_date"), self.lang)
                location = safe_get(exp, "location", "")
                date_range = f"{start} - {end}" if end else start

                lines.append(f"\n{company}")
                meta = position
                if date_range:
                    meta += f"  ({date_range})"
                if location:
                    meta += f"  [{location}]"
                lines.append(meta)

                desc = safe_get(exp, "description", [])
                for d in desc:
                    if d.strip():
                        lines.append(f"  * {d}")
            lines.append("")

        # 项目经验
        projects = safe_get(self.data, "projects", [])
        if projects:
            lines.append(self._section_header(self.t["projects"]))
            for proj in sort_by_date(projects):
                name = safe_get(proj, "name", self.t["tbd"])
                role = safe_get(proj, "role", "")
                start = format_date(safe_get(proj, "start_date"), self.lang)
                end = format_date(safe_get(proj, "end_date"), self.lang)
                date_range = f"{start} - {end}" if end else start

                lines.append(f"\n{name}")
                meta = role
                if date_range:
                    meta += f"  ({date_range})"
                if meta.strip():
                    lines.append(meta)

                tech = safe_get(proj, "tech_stack", [])
                if tech:
                    lines.append(f"  {self.t['tech_stack']}: {'、'.join(tech)}")

                desc = safe_get(proj, "description", [])
                for d in desc:
                    if d.strip():
                        lines.append(f"  * {d}")
            lines.append("")

        # 教育背景
        education = safe_get(self.data, "education", [])
        if education:
            lines.append(self._section_header(self.t["education"]))
            for edu in sort_by_date(education):
                school = safe_get(edu, "school", self.t["tbd"])
                degree = safe_get(edu, "degree", "")
                major = safe_get(edu, "major", "")
                start = format_date(safe_get(edu, "start_date"), self.lang)
                end = format_date(safe_get(edu, "end_date"), self.lang)
                gpa = safe_get(edu, "gpa", "")
                date_range = f"{start} - {end}" if end else start

                lines.append(f"\n{school}")
                meta = " · ".join(p for p in [degree, major] if p)
                if date_range:
                    meta += f"  ({date_range})"
                if gpa:
                    meta += f"  {self.t['gpa']}: {gpa}"
                lines.append(meta)

                desc = safe_get(edu, "description", [])
                for d in desc:
                    if d.strip():
                        lines.append(f"  * {d}")
            lines.append("")

        # 技能
        skills = safe_get(self.data, "skills", [])
        if skills:
            lines.append(self._section_header(self.t["skills"]))
            for skill_group in skills:
                category = safe_get(skill_group, "category", "")
                items = safe_get(skill_group, "items", [])
                lines.append(f"  {category}: {'、'.join(items)}")
            lines.append("")

        # 证书
        certs = safe_get(self.data, "certifications", [])
        if certs:
            lines.append(self._section_header(self.t["certifications"]))
            for cert in certs:
                if isinstance(cert, str):
                    lines.append(f"  * {cert}")
                elif isinstance(cert, dict):
                    name = safe_get(cert, "name", "")
                    issuer = safe_get(cert, "issuer", "")
                    lines.append(f"  * {name}" + (f" ({issuer})" if issuer else ""))
            lines.append("")

        # 语言能力
        languages = safe_get(self.data, "languages", [])
        if languages:
            lines.append(self._section_header(self.t["languages"]))
            for lang_item in languages:
                if isinstance(lang_item, str):
                    lines.append(f"  * {lang_item}")
                elif isinstance(lang_item, dict):
                    lang_name = safe_get(lang_item, "language", "")
                    level = safe_get(lang_item, "level", "")
                    lines.append(f"  * {lang_name}: {level}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


# ============================================================
# HTML 生成器
# ============================================================

class HtmlGenerator:
    def __init__(self, data, lang="zh", style="classic"):
        self.data = data
        self.lang = lang
        self.style = style
        self.t = I18N[lang]

    def _esc(self, text):
        """HTML 转义"""
        if not text:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    def generate(self):
        personal = safe_get(self.data, "personal", {})
        name = self._esc(safe_get(personal, "name", self.t["tbd"]))
        title = self._esc(safe_get(personal, "title", ""))

        # 联系方式
        contact_items = []
        for field in ["email", "phone", "location", "website", "github", "linkedin"]:
            val = safe_get(personal, field)
            if val:
                contact_items.append(f'<span class="contact-item">{self._esc(val)}</span>')
        contact_html = " · ".join(contact_items)

        sections = []

        # 求职意向
        objective = safe_get(self.data, "objective", {})
        if has_content(objective, "position") or has_content(objective, "summary"):
            content = ""
            if has_content(objective, "position"):
                content += f'<p class="objective-position"><strong>{self.t["position"]}:</strong> {self._esc(safe_get(objective, "position"))}</p>'
            if has_content(objective, "summary"):
                content += f'<p class="objective-summary">{self._esc(safe_get(objective, "summary"))}</p>'
            sections.append(self._section(self.t["objective"], content))

        # 工作经历
        experience = safe_get(self.data, "experience", [])
        if experience:
            entries = ""
            for exp in sort_by_date(experience):
                company = self._esc(safe_get(exp, "company", self.t["tbd"]))
                position = self._esc(safe_get(exp, "position", ""))
                start = format_date(safe_get(exp, "start_date"), self.lang)
                end = format_date(safe_get(exp, "end_date"), self.lang)
                location = self._esc(safe_get(exp, "location", ""))
                date_range = f"{start} - {end}" if end else start

                desc_items = ""
                for d in safe_get(exp, "description", []):
                    if d.strip():
                        desc_items += f"<li>{self._esc(d)}</li>"

                entries += f'''
                <div class="entry">
                    <div class="entry-header">
                        <span class="entry-company">{company}</span>
                        <span class="entry-date">{self._esc(date_range)}</span>
                    </div>
                    <div class="entry-subheader">
                        <span class="entry-position">{position}</span>
                        {f'<span class="entry-location">{location}</span>' if location else ''}
                    </div>
                    {f'<ul class="entry-description">{desc_items}</ul>' if desc_items else ''}
                </div>'''
            sections.append(self._section(self.t["experience"], entries))

        # 项目经验
        projects = safe_get(self.data, "projects", [])
        if projects:
            entries = ""
            for proj in sort_by_date(projects):
                pname = self._esc(safe_get(proj, "name", self.t["tbd"]))
                role = self._esc(safe_get(proj, "role", ""))
                start = format_date(safe_get(proj, "start_date"), self.lang)
                end = format_date(safe_get(proj, "end_date"), self.lang)
                date_range = f"{start} - {end}" if end else start
                link = self._esc(safe_get(proj, "link", ""))

                tech = safe_get(proj, "tech_stack", [])
                tech_html = ""
                if tech:
                    tags = " ".join(f'<span class="tech-tag">{self._esc(t)}</span>' for t in tech)
                    tech_html = f'<div class="tech-stack"><span class="tech-label">{self.t["tech_stack"]}:</span> {tags}</div>'

                desc_items = ""
                for d in safe_get(proj, "description", []):
                    if d.strip():
                        desc_items += f"<li>{self._esc(d)}</li>"

                entries += f'''
                <div class="entry">
                    <div class="entry-header">
                        <span class="entry-company">{pname}</span>
                        <span class="entry-date">{self._esc(date_range)}</span>
                    </div>
                    <div class="entry-subheader">
                        {f'<span class="entry-position">{role}</span>' if role else ''}
                        {f'<a href="{link}" class="project-link">{link}</a>' if link else ''}
                    </div>
                    {tech_html}
                    {f'<ul class="entry-description">{desc_items}</ul>' if desc_items else ''}
                </div>'''
            sections.append(self._section(self.t["projects"], entries))

        # 教育背景
        education = safe_get(self.data, "education", [])
        if education:
            entries = ""
            for edu in sort_by_date(education):
                school = self._esc(safe_get(edu, "school", self.t["tbd"]))
                degree = self._esc(safe_get(edu, "degree", ""))
                major = self._esc(safe_get(edu, "major", ""))
                start = format_date(safe_get(edu, "start_date"), self.lang)
                end = format_date(safe_get(edu, "end_date"), self.lang)
                gpa = self._esc(safe_get(edu, "gpa", ""))
                date_range = f"{start} - {end}" if end else start

                details = " · ".join(p for p in [degree, major] if p)

                desc_items = ""
                for d in safe_get(edu, "description", []):
                    if d.strip():
                        desc_items += f"<li>{self._esc(d)}</li>"

                entries += f'''
                <div class="entry">
                    <div class="entry-header">
                        <span class="entry-company">{school}</span>
                        <span class="entry-date">{self._esc(date_range)}</span>
                    </div>
                    <div class="entry-subheader">
                        <span class="entry-position">{self._esc(details)}</span>
                        {f'<span class="entry-gpa">{self.t["gpa"]}: {gpa}</span>' if gpa else ''}
                    </div>
                    {f'<ul class="entry-description">{desc_items}</ul>' if desc_items else ''}
                </div>'''
            sections.append(self._section(self.t["education"], entries))

        # 技能
        skills = safe_get(self.data, "skills", [])
        if skills:
            skill_html = ""
            for skill_group in skills:
                category = self._esc(safe_get(skill_group, "category", ""))
                items = safe_get(skill_group, "items", [])
                tags = " ".join(f'<span class="skill-tag">{self._esc(item)}</span>' for item in items)
                skill_html += f'<div class="skill-group"><span class="skill-category">{category}:</span> {tags}</div>'
            sections.append(self._section(self.t["skills"], skill_html))

        # 证书
        certs = safe_get(self.data, "certifications", [])
        if certs:
            cert_items = ""
            for cert in certs:
                if isinstance(cert, str):
                    cert_items += f"<li>{self._esc(cert)}</li>"
                elif isinstance(cert, dict):
                    cname = self._esc(safe_get(cert, "name", ""))
                    issuer = self._esc(safe_get(cert, "issuer", ""))
                    cert_items += f"<li>{cname}" + (f" ({issuer})" if issuer else "") + "</li>"
            sections.append(self._section(self.t["certifications"], f"<ul>{cert_items}</ul>"))

        # 语言能力
        languages = safe_get(self.data, "languages", [])
        if languages:
            lang_items = ""
            for lang_item in languages:
                if isinstance(lang_item, str):
                    lang_items += f"<li>{self._esc(lang_item)}</li>"
                elif isinstance(lang_item, dict):
                    lname = self._esc(safe_get(lang_item, "language", ""))
                    level = self._esc(safe_get(lang_item, "level", ""))
                    lang_items += f"<li>{lname}: {level}</li>"
            sections.append(self._section(self.t["languages"], f"<ul>{lang_items}</ul>"))

        sections_html = "\n".join(sections)

        # 样式
        if self.style == "modern":
            css = self._modern_css()
        elif self.style == "concise":
            css = self._concise_css()
        else:
            css = self._classic_css()

        return f'''<!DOCTYPE html>
<html lang="{self.lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} - Resume</title>
<style>
{css}
</style>
</head>
<body>
<div class="resume-container">
    <header class="resume-header">
        <h1 class="resume-name">{name}</h1>
        {f'<p class="resume-title">{title}</p>' if title else ''}
        {f'<div class="resume-contact">{contact_html}</div>' if contact_html else ''}
    </header>
    {sections_html}
</div>
</body>
</html>'''

    def _section(self, title, content):
        return f'''
    <section class="resume-section">
        <h2 class="section-title">{title}</h2>
        <div class="section-content">{content}</div>
    </section>'''

    def _classic_css(self):
        return """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }
.resume-container { max-width: 800px; margin: 30px auto; padding: 40px 50px; background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.resume-header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #2c3e50; }
.resume-name { font-size: 28px; color: #2c3e50; margin-bottom: 5px; }
.resume-title { font-size: 16px; color: #7f8c8d; margin-bottom: 10px; }
.resume-contact { font-size: 13px; color: #555; }
.contact-item { margin: 0 3px; }
.resume-section { margin-bottom: 25px; }
.section-title { font-size: 18px; color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-bottom: 15px; }
.entry { margin-bottom: 18px; }
.entry-header { display: flex; justify-content: space-between; align-items: baseline; }
.entry-company { font-weight: bold; font-size: 15px; color: #2c3e50; }
.entry-date { font-size: 13px; color: #888; }
.entry-subheader { display: flex; justify-content: space-between; margin-top: 2px; }
.entry-position { font-size: 14px; color: #555; font-style: italic; }
.entry-location, .entry-gpa { font-size: 13px; color: #999; }
.entry-description { margin-top: 8px; padding-left: 20px; }
.entry-description li { font-size: 14px; margin-bottom: 3px; }
.skill-group { margin-bottom: 8px; font-size: 14px; }
.skill-category { font-weight: bold; color: #2c3e50; }
.skill-tag { display: inline-block; background: #ecf0f1; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin: 2px; color: #555; }
.tech-stack { margin: 5px 0; font-size: 13px; }
.tech-label { color: #888; }
.tech-tag { display: inline-block; background: #e8f4fd; color: #2980b9; padding: 1px 6px; border-radius: 3px; font-size: 12px; margin: 1px; }
.project-link { font-size: 12px; color: #3498db; text-decoration: none; }
.objective-position { font-size: 14px; margin-bottom: 5px; }
.objective-summary { font-size: 14px; color: #555; }
ul { padding-left: 20px; }
@media print { body { background: #fff; } .resume-container { box-shadow: none; margin: 0; padding: 20px; } }
"""

    def _concise_css(self):
        return """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; background: #fff; color: #333; line-height: 1.4; font-size: 13px; }
.resume-container { max-width: 750px; margin: 0 auto; padding: 25px 35px; }
.resume-header { text-align: center; margin-bottom: 15px; }
.resume-name { font-size: 24px; color: #222; }
.resume-title { font-size: 14px; color: #666; margin: 3px 0; }
.resume-contact { font-size: 12px; color: #777; }
.resume-section { margin-bottom: 15px; }
.section-title { font-size: 15px; color: #222; border-bottom: 1px solid #ccc; padding-bottom: 3px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
.entry { margin-bottom: 10px; }
.entry-header { display: flex; justify-content: space-between; }
.entry-company { font-weight: bold; font-size: 13px; }
.entry-date { font-size: 12px; color: #888; }
.entry-subheader { display: flex; justify-content: space-between; font-size: 12px; color: #666; }
.entry-description { margin-top: 4px; padding-left: 18px; }
.entry-description li { font-size: 12px; margin-bottom: 1px; }
.skill-group { font-size: 12px; margin-bottom: 4px; }
.skill-category { font-weight: bold; }
.skill-tag { display: inline-block; background: #f0f0f0; padding: 1px 5px; border-radius: 2px; font-size: 11px; margin: 1px; }
.tech-tag { display: inline-block; background: #e8f4fd; color: #2980b9; padding: 1px 4px; border-radius: 2px; font-size: 11px; }
ul { padding-left: 18px; }
@media print { .resume-container { padding: 15px; } }
"""

    def _modern_css(self):
        return """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; line-height: 1.7; min-height: 100vh; }
.resume-container { max-width: 820px; margin: 30px auto; padding: 45px 55px; background: #fff; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.resume-header { text-align: center; margin-bottom: 35px; padding-bottom: 25px; background: linear-gradient(135deg, #667eea15, #764ba215); border-radius: 8px; padding: 25px; }
.resume-name { font-size: 32px; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 5px; }
.resume-title { font-size: 17px; color: #666; margin-bottom: 12px; }
.resume-contact { font-size: 13px; color: #777; }
.contact-item { margin: 0 4px; }
.resume-section { margin-bottom: 28px; }
.section-title { font-size: 19px; color: #667eea; margin-bottom: 18px; padding-left: 12px; border-left: 4px solid #667eea; }
.entry { margin-bottom: 20px; padding: 15px; background: #fafbfc; border-radius: 8px; border-left: 3px solid #667eea; }
.entry-header { display: flex; justify-content: space-between; align-items: baseline; }
.entry-company { font-weight: bold; font-size: 16px; color: #333; }
.entry-date { font-size: 13px; color: #999; background: #f0f0f0; padding: 2px 10px; border-radius: 10px; }
.entry-subheader { display: flex; justify-content: space-between; margin-top: 4px; }
.entry-position { font-size: 14px; color: #667eea; font-weight: 500; }
.entry-location, .entry-gpa { font-size: 13px; color: #aaa; }
.entry-description { margin-top: 10px; padding-left: 18px; }
.entry-description li { font-size: 14px; margin-bottom: 4px; color: #555; }
.skill-group { margin-bottom: 10px; font-size: 14px; }
.skill-category { font-weight: bold; color: #667eea; display: inline-block; min-width: 100px; }
.skill-tag { display: inline-block; background: linear-gradient(135deg, #667eea15, #764ba215); color: #667eea; padding: 3px 10px; border-radius: 15px; font-size: 12px; margin: 2px; font-weight: 500; }
.tech-stack { margin: 8px 0; }
.tech-label { color: #999; font-size: 13px; }
.tech-tag { display: inline-block; background: #f0f4ff; color: #667eea; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin: 2px; }
.project-link { font-size: 12px; color: #667eea; text-decoration: none; }
.objective-position { font-size: 14px; margin-bottom: 8px; }
.objective-summary { font-size: 14px; color: #666; line-height: 1.8; }
ul { padding-left: 20px; }
@media print { body { background: #fff; } .resume-container { box-shadow: none; margin: 0; border-radius: 0; } }
"""


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="简历生成器（支持 Markdown/Text/HTML，中英文双语，三种风格）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --input resume.json --format markdown
  %(prog)s --input resume.json --format html --lang en --output resume.html
  %(prog)s --input resume.json --format text --style concise
        """,
    )

    parser.add_argument("--input", "-i", required=True, help="输入 JSON 数据文件路径")
    parser.add_argument("--format", "-f", choices=["markdown", "text", "html"],
                        default="markdown", help="输出格式（默认 markdown）")
    parser.add_argument("--lang", "-l", choices=["zh", "en"], default="zh",
                        help="语言（默认 zh 中文）")
    parser.add_argument("--style", "-s", choices=["classic", "concise", "modern"],
                        default="classic", help="模板风格（默认 classic）")
    parser.add_argument("--output", "-o", help="输出文件路径（不指定则输出到终端）")

    args = parser.parse_args()

    # 读取 JSON 数据
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{args.input}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败 - {e}", file=sys.stderr)
        sys.exit(1)

    # 生成简历
    if args.format == "markdown":
        generator = MarkdownGenerator(data, args.lang, args.style)
    elif args.format == "text":
        generator = TextGenerator(data, args.lang, args.style)
    elif args.format == "html":
        generator = HtmlGenerator(data, args.lang, args.style)
    else:
        generator = MarkdownGenerator(data, args.lang, args.style)

    output = generator.generate()

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ 简历已生成: {args.output}")
        print(f"   格式: {args.format.upper()}, 语言: {args.lang}, 风格: {args.style}")
    else:
        print(output)


if __name__ == "__main__":
    main()
