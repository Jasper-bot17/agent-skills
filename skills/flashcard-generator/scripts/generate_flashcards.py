#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆卡片生成助手 - 知识点提取与卡片初步生成脚本

从学习文本中提取核心知识点，生成问答式记忆卡片。
支持文本、Anki CSV、JSON 三种输出格式。

用法：
    python3 generate_flashcards.py --input notes.txt --format text
    python3 generate_flashcards.py --input notes.txt --format anki
    python3 generate_flashcards.py --input notes.txt --format json
    python3 generate_flashcards.py --input notes.txt --max-cards 30 --tags "生物学,细胞"
    cat notes.txt | python3 generate_flashcards.py --format text
"""

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Flashcard:
    """一张记忆卡片"""
    id: int
    card_type: str  # concept, causal, comparison, formula, process, list, timeline, cloze
    front: str
    back: str
    tags: List[str] = field(default_factory=list)
    difficulty: str = "basic"  # basic, advanced, high_frequency
    source: str = ""
    confidence: float = 0.0  # 提取置信度 0-1


@dataclass
class KnowledgePoint:
    """提取的知识点"""
    text: str
    kp_type: str  # definition, list, comparison, formula, process, timeline
    source_line: int
    context: str = ""


# ============================================================
# 知识点提取模式
# ============================================================

# 定义模式
DEFINITION_PATTERNS = [
    r'(.{2,50}?)\s*(?:是指|定义为|称为|是指|就是指|系指)\s*(.{10,200})',
    r'所谓\s*(.{2,30}?)\s*[，,]\s*(.{10,200})',
    r'(.{2,30}?)\s*(?:的定义|的概念)\s*[是：:]\s*(.{10,200})',
]

# 列表/特征模式
LIST_PATTERNS = [
    r'(.{2,30}?)\s*(?:的特征|的特点|的分类|的类型|的种类|包括|分为|有以下|主要有)\s*[：:]\s*(.{10,300})',
    r'(.{2,30}?)\s*(?:的优点|的缺点|的优势|的局限|的不足)\s*[：:]\s*(.{10,200})',
]

# 对比模式
COMPARISON_PATTERNS = [
    r'(.{2,20}?)\s*(?:和|与|跟)\s*(.{2,20}?)\s*(?:的区别|的不同|的异同|的比较)\s*[：:，,]?\s*(.{10,300})',
    r'(.{2,20}?)\s*(?:不同于|区别于)\s*(.{2,20}?)\s*[，,。]\s*(.{10,200})',
]

# 因果/机制模式
CAUSAL_PATTERNS = [
    r'(.{2,30}?)\s*(?:的原因|的机理|的机制|的原理|的过程)\s*[：:]\s*(.{10,300})',
    r'因为\s*(.{10,100}?)\s*[，,]\s*(?:所以|因此|导致|因而)\s*(.{10,100})',
]

# 公式/定理模式
FORMULA_PATTERNS = [
    r'(.{2,30}?)\s*(?:公式|定理|定律|法则|方程)\s*[：:]\s*(.{5,100})',
    r'(.{2,30}?)\s*(?:公式|定理|定律)\s*(?:为|是)\s*[：:]?\s*(.{5,100})',
]

# 步骤/流程模式
PROCESS_PATTERNS = [
    r'(.{2,30}?)\s*(?:的步骤|的过程|的流程|的阶段)\s*[：:]\s*(.{10,300})',
    r'(?:第一步|首先|第一阶段)\s*[：:，,]?\s*(.{5,100})',
]

# 时间线模式
TIMELINE_PATTERNS = [
    r'(\d{4}年)\s*(.{2,50}?)\s*(?:提出|发现|建立|发表|创立|发明)\s*(.{0,50})',
    r'(\d{4}年)\s*[，,]\s*(.{2,30}?)\s*(?:提出|发现|建立)\s*(.{0,50})',
]


# ============================================================
# 文本解析器
# ============================================================

class TextParser:
    """解析学习文本，提取知识点"""

    def __init__(self, text: str):
        self.text = text
        self.lines = text.split('\n')
        self.knowledge_points: List[KnowledgePoint] = []

    def parse(self) -> List[KnowledgePoint]:
        """执行知识点提取"""
        # 合并段落（按空行分割）
        paragraphs = self._split_paragraphs()

        for para_text, start_line in paragraphs:
            # 跳过过短的段落
            if len(para_text) < 15:
                continue

            # 尝试各种模式匹配
            self._extract_definitions(para_text, start_line)
            self._extract_lists(para_text, start_line)
            self._extract_comparisons(para_text, start_line)
            self._extract_causal(para_text, start_line)
            self._extract_formulas(para_text, start_line)
            self._extract_processes(para_text, start_line)
            self._extract_timelines(para_text, start_line)

        return self.knowledge_points

    def _split_paragraphs(self) -> List[Tuple[str, int]]:
        """将文本按空行分割为段落，返回 (段落文本, 起始行号)"""
        paragraphs = []
        current_para = []
        start_line = 0

        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped:
                if not current_para:
                    start_line = i + 1
                current_para.append(stripped)
            else:
                if current_para:
                    paragraphs.append((' '.join(current_para), start_line))
                    current_para = []

        if current_para:
            paragraphs.append((' '.join(current_para), start_line))

        return paragraphs

    def _add_kp(self, text: str, kp_type: str, line: int, context: str = ""):
        """添加知识点（去重）"""
        # 简单去重：文本相似度高的跳过
        text_clean = re.sub(r'\s+', ' ', text).strip()
        for existing in self.knowledge_points:
            if existing.text[:30] == text_clean[:30] and len(text_clean) > 20:
                return
        self.knowledge_points.append(KnowledgePoint(
            text=text_clean,
            kp_type=kp_type,
            source_line=line,
            context=context,
        ))

    def _extract_definitions(self, text: str, line: int):
        """提取定义"""
        for pattern in DEFINITION_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    term = match[0].strip()
                    definition = match[1].strip()
                    # 过滤掉太短或明显不是定义的
                    if len(term) >= 2 and len(definition) >= 10:
                        self._add_kp(
                            f"{term}：{definition}",
                            "definition",
                            line,
                            f"术语：{term}"
                        )

    def _extract_lists(self, text: str, line: int):
        """提取列表/特征"""
        for pattern in LIST_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    topic = match[0].strip()
                    content = match[1].strip()
                    if len(topic) >= 2 and len(content) >= 10:
                        self._add_kp(
                            f"{topic}：{content}",
                            "list",
                            line,
                            f"主题：{topic}"
                        )

    def _extract_comparisons(self, text: str, line: int):
        """提取对比"""
        for pattern in COMPARISON_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    a = match[0].strip()
                    b = match[1].strip() if len(match) > 1 else ""
                    content = match[2] if len(match) > 2 else ""
                    if len(a) >= 2 and len(b) >= 2:
                        self._add_kp(
                            f"{a}与{b}的区别：{content}",
                            "comparison",
                            line,
                            f"对比：{a} vs {b}"
                        )

    def _extract_causal(self, text: str, line: int):
        """提取因果/机制"""
        for pattern in CAUSAL_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    topic = match[0].strip()
                    content = match[1].strip()
                    if len(topic) >= 2 and len(content) >= 10:
                        self._add_kp(
                            f"{topic}的原因/机制：{content}",
                            "causal",
                            line,
                            f"主题：{topic}"
                        )

    def _extract_formulas(self, text: str, line: int):
        """提取公式/定理"""
        for pattern in FORMULA_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    name = match[0].strip()
                    formula = match[1].strip()
                    if len(name) >= 2 and len(formula) >= 3:
                        self._add_kp(
                            f"{name}：{formula}",
                            "formula",
                            line,
                            f"名称：{name}"
                        )

    def _extract_processes(self, text: str, line: int):
        """提取步骤/流程"""
        for pattern in PROCESS_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    topic = match[0].strip()
                    content = match[1].strip()
                    if len(topic) >= 2 and len(content) >= 10:
                        self._add_kp(
                            f"{topic}的步骤：{content}",
                            "process",
                            line,
                            f"主题：{topic}"
                        )

    def _extract_timelines(self, text: str, line: int):
        """提取时间线"""
        for pattern in TIMELINE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    year = match[0].strip()
                    person = match[1].strip()
                    achievement = match[2] if len(match) > 2 else ""
                    if year and person:
                        self._add_kp(
                            f"{year} {person}：{achievement}",
                            "timeline",
                            line,
                            f"时间：{year}"
                        )


# ============================================================
# 卡片生成器
# ============================================================

class FlashcardGenerator:
    """将知识点转化为记忆卡片"""

    # 知识点类型到卡片类型的映射
    TYPE_MAP = {
        "definition": "concept",
        "list": "list",
        "comparison": "comparison",
        "causal": "causal",
        "formula": "formula",
        "process": "process",
        "timeline": "timeline",
    }

    # 卡片类型中文名
    TYPE_NAMES = {
        "concept": "概念定义",
        "causal": "因果关系",
        "comparison": "对比辨析",
        "formula": "公式定理",
        "process": "步骤流程",
        "list": "列举",
        "timeline": "时间线",
        "cloze": "填空",
    }

    def __init__(self, knowledge_points: List[KnowledgePoint], tags: List[str] = None,
                 max_cards: int = 50):
        self.kps = knowledge_points
        self.tags = tags or []
        self.max_cards = max_cards
        self.cards: List[Flashcard] = []

    def generate(self) -> List[Flashcard]:
        """生成卡片"""
        for i, kp in enumerate(self.kps[:self.max_cards]):
            card = self._generate_card(kp, i + 1)
            if card:
                self.cards.append(card)
        return self.cards

    def _generate_card(self, kp: KnowledgePoint, card_id: int) -> Optional[Flashcard]:
        """根据知识点生成单张卡片"""
        card_type = self.TYPE_MAP.get(kp.kp_type, "concept")

        # 根据类型生成不同的正面问题和背面答案
        if kp.kp_type == "definition":
            front, back = self._gen_definition_card(kp)
        elif kp.kp_type == "list":
            front, back = self._gen_list_card(kp)
        elif kp.kp_type == "comparison":
            front, back = self._gen_comparison_card(kp)
        elif kp.kp_type == "causal":
            front, back = self._gen_causal_card(kp)
        elif kp.kp_type == "formula":
            front, back = self._gen_formula_card(kp)
        elif kp.kp_type == "process":
            front, back = self._gen_process_card(kp)
        elif kp.kp_type == "timeline":
            front, back = self._gen_timeline_card(kp)
        else:
            front = f"关于以下内容，你能回忆起什么？\n{kp.text[:50]}..."
            back = kp.text

        if not front or not back:
            return None

        # 推断难度
        difficulty = self._infer_difficulty(kp)

        return Flashcard(
            id=card_id,
            card_type=card_type,
            front=front,
            back=back,
            tags=self.tags + [card_type, difficulty],
            difficulty=difficulty,
            source=f"第{kp.source_line}行",
            confidence=0.6,  # 模式匹配的基础置信度
        )

    def _gen_definition_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成定义型卡片"""
        # 从 text 中提取术语和定义
        match = re.match(r'(.{2,50}?)[：:]\s*(.+)', kp.text)
        if match:
            term = match.group(1).strip()
            definition = match.group(2).strip()
            front = f"什么是{term}？"
            back = f"**{term}**：{definition}\n\n*出自原文第{kp.source_line}行*"
            return front, back
        return f"以下内容的定义是什么？\n{kp.text[:80]}", kp.text

    def _gen_list_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成列举型卡片"""
        match = re.match(r'(.{2,50}?)[：:]\s*(.+)', kp.text)
        if match:
            topic = match.group(1).strip()
            content = match.group(2).strip()
            front = f"{topic}有哪些？"
            # 将内容分点
            items = re.split(r'[；;。\n]', content)
            items = [f"- {item.strip()}" for item in items if item.strip()]
            back = f"**{topic}**：\n\n" + "\n".join(items) if items else content
            return front, back
        return f"以下内容包括哪些要点？", kp.text

    def _gen_comparison_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成对比型卡片"""
        match = re.match(r'(.{2,30}?)与(.{2,30}?)的区别[：:]\s*(.+)', kp.text)
        if match:
            a = match.group(1).strip()
            b = match.group(2).strip()
            content = match.group(3).strip()
            front = f"{a}和{b}的区别是什么？"
            back = f"**{a} vs {b}**：\n\n{content}"
            return front, back
        return f"以下两者的区别是什么？\n{kp.text[:80]}", kp.text

    def _gen_causal_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成因果型卡片"""
        match = re.match(r'(.{2,50}?)的原因[/／]机制[：:]\s*(.+)', kp.text)
        if match:
            topic = match.group(1).strip()
            content = match.group(2).strip()
            front = f"{topic}的原因/机制是什么？"
            back = f"**{topic}的原因/机制**：\n\n{content}"
            return front, back
        return f"以下内容的原因是什么？", kp.text

    def _gen_formula_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成公式型卡片"""
        match = re.match(r'(.{2,50}?)[：:]\s*(.+)', kp.text)
        if match:
            name = match.group(1).strip()
            formula = match.group(2).strip()
            front = f"{name}的公式/内容是什么？"
            back = f"**{name}**：\n\n`{formula}`"
            return front, back
        return f"以下公式是什么？", kp.text

    def _gen_process_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成步骤型卡片"""
        match = re.match(r'(.{2,50}?)的步骤[：:]\s*(.+)', kp.text)
        if match:
            topic = match.group(1).strip()
            content = match.group(2).strip()
            front = f"{topic}的步骤/过程是什么？"
            back = f"**{topic}的步骤**：\n\n{content}"
            return front, back
        return f"以下内容的步骤是什么？", kp.text

    def _gen_timeline_card(self, kp: KnowledgePoint) -> Tuple[str, str]:
        """生成时间线卡片"""
        front = f"以下事件发生在什么时间？涉及谁？\n{kp.text[:60]}..."
        back = kp.text
        return front, back

    @staticmethod
    def _infer_difficulty(kp: KnowledgePoint) -> str:
        """推断知识点难度"""
        text = kp.text
        # 包含"区别""对比""机制"等词的通常较难
        if any(kw in text for kw in ["区别", "对比", "机制", "机理", "推导", "证明", "综合"]):
            return "advanced"
        # 包含"高频""考点""重点"的标记为高频
        if any(kw in text for kw in ["高频", "考点", "重点", "必考", "常考"]):
            return "high_frequency"
        return "basic"


# ============================================================
# 输出格式化
# ============================================================

def format_text(cards: List[Flashcard], stats: dict) -> str:
    """格式化为文本输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("记忆卡片生成结果")
    lines.append("=" * 60)
    lines.append("")

    for card in cards:
        type_name = FlashcardGenerator.TYPE_NAMES.get(card.card_type, card.card_type)
        lines.append(f"### 卡片 {card.id}：[{type_name}]")
        lines.append("")
        lines.append("【正面（问题）】")
        lines.append(f"  {card.front}")
        lines.append("")
        lines.append("【背面（答案）】")
        for back_line in card.back.split('\n'):
            lines.append(f"  {back_line}")
        lines.append("")
        lines.append(f"【标签】{' '.join(card.tags)}")
        lines.append(f"【难度】{card.difficulty} | 【来源】{card.source} | 【置信度】{card.confidence}")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")

    # 统计
    lines.append("📊 卡片统计")
    lines.append(f"  总卡片数：{stats['total']}")
    lines.append(f"  类型分布：{', '.join(f'{k} {v}' for k, v in stats['type_dist'].items())}")
    lines.append(f"  难度分布：{', '.join(f'{k} {v}' for k, v in stats['difficulty_dist'].items())}")
    lines.append("")
    lines.append("⚠ 注意：以上为模式匹配初步生成的卡片，需经 AI 语义审核和优化后使用。")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_anki_csv(cards: List[Flashcard]) -> str:
    """格式化为 Anki 兼容 CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["正面", "背面", "标签"])

    for card in cards:
        # 将背面的换行转为 HTML <br>
        back_html = card.back.replace('\n', '<br>')
        # 加粗转换
        back_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', back_html)
        # 标签用 :: 分隔（Anki 层级标签）
        tags = '::'.join(card.tags) if card.tags else ''
        writer.writerow([card.front, back_html, tags])

    return output.getvalue()


def format_json(cards: List[Flashcard], stats: dict) -> str:
    """格式化为 JSON"""
    data = {
        "stats": stats,
        "cards": [
            {
                "id": c.id,
                "type": c.card_type,
                "type_name": FlashcardGenerator.TYPE_NAMES.get(c.card_type, c.card_type),
                "front": c.front,
                "back": c.back,
                "tags": c.tags,
                "difficulty": c.difficulty,
                "source": c.source,
                "confidence": c.confidence,
            }
            for c in cards
        ],
        "note": "以上为模式匹配初步生成的卡片，需经 AI 语义审核和优化后使用。",
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def compute_stats(cards: List[Flashcard]) -> dict:
    """计算卡片统计"""
    type_dist = defaultdict(int)
    difficulty_dist = defaultdict(int)
    for c in cards:
        type_name = FlashcardGenerator.TYPE_NAMES.get(c.card_type, c.card_type)
        type_dist[type_name] += 1
        difficulty_dist[c.difficulty] += 1
    return {
        "total": len(cards),
        "type_dist": dict(type_dist),
        "difficulty_dist": dict(difficulty_dist),
    }


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="记忆卡片生成工具 - 从学习文本中提取知识点并生成记忆卡片"
    )
    parser.add_argument("--input", "-i", help="输入文本文件路径（默认从 stdin 读取）")
    parser.add_argument("--format", "-f", choices=["text", "anki", "json"], default="text",
                        help="输出格式（默认 text）")
    parser.add_argument("--max-cards", "-m", type=int, default=50,
                        help="最大卡片数量（默认 50）")
    parser.add_argument("--tags", "-t", help="卡片标签，用逗号分隔（如：生物学,细胞,基础）")
    parser.add_argument("--output", "-o", help="输出文件路径（默认输出到 stdout）")
    args = parser.parse_args()

    # 读取输入
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"错误：文件 '{args.input}' 不存在", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误：读取文件失败 - {e}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("错误：输入为空，请提供学习文本", file=sys.stderr)
        print("\n用法示例：", file=sys.stderr)
        print("  python3 generate_flashcards.py --input notes.txt --format anki", file=sys.stderr)
        print("  cat notes.txt | python3 generate_flashcards.py --max-cards 30", file=sys.stderr)
        sys.exit(1)

    # 解析标签
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else []

    # 提取知识点
    text_parser = TextParser(text)
    knowledge_points = text_parser.parse()

    if not knowledge_points:
        print("提示：未能从文本中自动提取到知识点。", file=sys.stderr)
        print("建议：提供包含明确定义、列表、对比等结构的学习文本，或由 AI 手动生成卡片。", file=sys.stderr)
        sys.exit(0)

    # 生成卡片
    generator = FlashcardGenerator(knowledge_points, tags=tags, max_cards=args.max_cards)
    cards = generator.generate()

    if not cards:
        print("错误：未能生成卡片", file=sys.stderr)
        sys.exit(1)

    # 统计
    stats = compute_stats(cards)

    # 输出
    if args.format == "anki":
        output = format_anki_csv(cards)
    elif args.format == "json":
        output = format_json(cards, stats)
    else:
        output = format_text(cards, stats)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"结果已写入: {args.output}（{len(cards)} 张卡片）", file=sys.stderr)
        except Exception as e:
            print(f"错误：写入文件失败 - {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)


if __name__ == "__main__":
    main()
