#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本可读性分析脚本

对中文/英文文本进行多维度可读性分析：
- 基础统计（字符数、字数、句数、段数、阅读时间）
- 句子质量（平均句长、长句检测、句长分布）
- 词汇分析（高频词、填充词、被动句、冗长表达）
- 段落分析（平均段长、最长段落）
- 可读性评分（0-100）

用法：
  python3 analyze_readability.py --input article.txt
  python3 analyze_readability.py --input article.txt --format json
  python3 analyze_readability.py --input article.txt --style academic
  python3 analyze_readability.py --input article.txt --issues-only
  cat article.txt | python3 analyze_readability.py
"""

import argparse
import json
import re
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple


# ============================================================
# 词汇库
# ============================================================

# 中文填充词/弱义词（出现过多说明表达不够精炼）
CHINESE_FILLER_WORDS = {
    "的": "结构助词，过多说明修饰语冗余",
    "了": "动态助词，过多说明啰嗦",
    "是": "判断动词，过多可精简",
    "在": "介词，过多可精简",
    "和": "连词，过多说明并列过多",
    "进行": "虚化动词，可替换为具体动词",
    "相关": "模糊词，应具体化",
    "通过": "介词，过多可精简",
    "对于": "介词，可精简",
    "关于": "介词，可精简",
    "以及": "连词，可替换为顿号",
    "等等": "列举词，应具体",
    "非常": "程度副词，可删或替换",
    "十分": "程度副词，可删或替换",
    "可以": "能愿动词，可精简",
    "能够": "能愿动词，可精简",
    "需要": "能愿动词，视情况精简",
    "应该": "能愿动词，视情况精简",
    "一些": "数量词，模糊，应具体化",
    "一定的": "模糊修饰，应具体化",
    "方面": "后缀词，可精简",
    "问题": "高频词，检查是否过度使用",
    "工作": "高频词，检查是否过度使用",
    "情况": "模糊词，应具体化",
}

# 中文被动句模式
CHINESE_PASSIVE_PATTERNS = [
    (r'被[\u4e00-\u9fff]{1,8}(?:所|地|地)?', "被字句"),
    (r'受[\u4e00-\u9fff]{1,6}(?:所|的)?', "受字句"),
    (r'为[\u4e00-\u9fff]{1,6}所[\u4e00-\u9fff]{1,8}', "为...所..."),
    (r'由[\u4e00-\u9fff]{1,8}(?:来|去)?(?:完成|执行|负责|进行|处理)', "由...来..."),
]

# 中文冗长表达模式
CHINESE_VERBOSE_PATTERNS = [
    (r'由于.{1,15}的原因', "由于...的原因（语义重复，可删'的原因'）"),
    (r'在.{1,15}方面', "在...方面（可精简为直接表述）"),
    (r'对于.{1,15}来说', "对于...来说（可精简）"),
    (r'为了.{1,15}的目的', "为了...的目的（语义重复）"),
    (r'进行了.{1,10}', "进行了...（可直接用动词）"),
    (r'作出了.{1,10}', "作出了...（可直接用动词）"),
    (r'予以.{1,8}', "予以...（公文套话，可精简）"),
    (r'加以.{1,8}', "加以...（公文套话，可精简）"),
    (r'相关的.{1,8}', "相关的...（模糊，应具体化）"),
    (r'一定程度上', "一定程度上（模糊，应具体说明程度）"),
    (r'在一定程度上', "在一定程度上（模糊）"),
    (r'从某种意义上说', "从某种意义上说（模糊套话）"),
    (r'众所周知', "众所周知（空泛，可删）"),
    (r'毋庸置疑', "毋庸置疑（空泛，可删）"),
]

# 英文填充词
ENGLISH_FILLER_WORDS = {
    "very": "程度副词，可删或替换",
    "really": "程度副词，可删",
    "quite": "程度副词，可删",
    "actually": "填充词，可删",
    "basically": "填充词，可删",
    "literally": "填充词，可删",
    "just": "填充词，可删",
    "maybe": "模糊词，应具体化",
    "perhaps": "模糊词，应具体化",
    "things": "模糊词，应具体化",
    "stuff": "模糊词，应具体化",
    "a lot of": "模糊量词，应具体化",
    "lots of": "模糊量词，应具体化",
    "kind of": "模糊词，应删",
    "sort of": "模糊词，应删",
    "in order to": "冗长，可用to",
    "due to the fact that": "冗长，可用because",
    "in spite of the fact that": "冗长，可用although",
}

# 英文句子结束标点
EN_SENTENCE_ENDERS = ".!?"

# 中文句子结束标点
ZH_SENTENCE_ENDERS = "。！？；"


# ============================================================
# 文本分析器
# ============================================================

class TextAnalyzer:
    """文本可读性分析器"""

    def __init__(self, text: str, style: str = "auto"):
        self.text = text.strip()
        self.style = style
        # 分析结果
        self.chars = 0
        self.words = 0
        self.sentences: List[str] = []
        self.paragraphs: List[str] = []
        self.zh_char_count = 0
        self.en_word_count = 0
        self.is_chinese_dominant = True

    def analyze(self) -> dict:
        """执行完整分析，返回结果字典"""
        self._basic_stats()
        self._sentence_analysis()
        self._paragraph_analysis()
        self._word_analysis()
        self._passive_detection()
        self._verbose_detection()
        score = self._calculate_score()
        issues = self._collect_issues()

        return {
            "basic_stats": {
                "chars": self.chars,
                "words": self.words,
                "sentences": len(self.sentences),
                "paragraphs": len(self.paragraphs),
                "reading_time_min": self._estimate_reading_time(),
            },
            "sentence_analysis": self._sentence_stats(),
            "paragraph_analysis": self._paragraph_stats(),
            "word_analysis": self._word_stats(),
            "passive_voice": self.passive_results,
            "verbose_expressions": self.verbose_results,
            "readability_score": score,
            "issues": issues,
        }

    def _basic_stats(self):
        """基础统计"""
        # 去除空白
        text_no_space = re.sub(r'\s+', '', self.text)
        self.chars = len(text_no_space)

        # 统计中文字符和英文单词
        self.zh_char_count = len(re.findall(r'[\u4e00-\u9fff]', self.text))
        en_words = re.findall(r'[a-zA-Z]+(?:[\'-][a-zA-Z]+)*', self.text)
        self.en_word_count = len(en_words)

        # 总字数：中文字符 + 英文单词
        self.words = self.zh_char_count + self.en_word_count

        # 判断是否以中文为主
        self.is_chinese_dominant = self.zh_char_count > self.en_word_count

        # 分段
        self.paragraphs = [p.strip() for p in self.text.split('\n') if p.strip()]

    def _split_sentences(self) -> List[str]:
        """将文本拆分为句子"""
        # 统一换行
        text = self.text.replace('\n', ' ')
        # 按中文句号、问号、叹号、分号分割
        # 保留分隔符
        sentences = re.split(r'(?<=[。！？；!?;])', text)
        # 清理
        result = []
        for s in sentences:
            s = s.strip()
            # 去除前后空白和标点
            s = re.sub(r'^[\s，,。！？；:：]+', '', s)
            s = re.sub(r'[\s]+$', '', s)
            if len(s) >= 2:  # 至少2个字才算句子
                result.append(s)
        return result

    def _sentence_analysis(self):
        """句子分析"""
        self.sentences = self._split_sentences()

    def _paragraph_analysis(self):
        """段落分析"""
        pass  # 在 _paragraph_stats 中计算

    def _get_sentence_length(self, sentence: str) -> int:
        """计算句子长度（中文字符+英文单词数）"""
        zh = len(re.findall(r'[\u4e00-\u9fff]', sentence))
        en = len(re.findall(r'[a-zA-Z]+(?:[\'-][a-zA-Z]+)*', sentence))
        return zh + en

    def _sentence_stats(self) -> dict:
        """句子统计"""
        if not self.sentences:
            return {"avg_length": 0, "long_sentences": [], "super_long": [], "distribution": {}}

        lengths = [self._get_sentence_length(s) for s in self.sentences]
        avg_len = sum(lengths) / len(lengths)

        # 标准差
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        cv = std_dev / avg_len if avg_len > 0 else 0

        # 长句阈值（中文：40字；英文按词数类似处理）
        long_threshold = 40 if self.is_chinese_dominant else 30
        super_long_threshold = 60 if self.is_chinese_dominant else 45

        long_sents = []
        super_long_sents = []
        for i, (sent, length) in enumerate(zip(self.sentences, lengths), 1):
            if length >= super_long_threshold:
                super_long_sents.append({"index": i, "length": length, "text": sent[:80]})
            elif length >= long_threshold:
                long_sents.append({"index": i, "length": length, "text": sent[:80]})

        # 分布
        short_count = sum(1 for l in lengths if l < 15)
        mid_count = sum(1 for l in lengths if 15 <= l < 30)
        long_count = sum(1 for l in lengths if l >= 30)
        total = len(lengths)

        return {
            "avg_length": round(avg_len, 1),
            "std_dev": round(std_dev, 1),
            "cv": round(cv, 2),
            "long_count": len(long_sents),
            "super_long_count": len(super_long_sents),
            "long_pct": round(len(long_sents) / total * 100, 1),
            "super_long_pct": round(len(super_long_sents) / total * 100, 1),
            "long_sentences": long_sents[:10],
            "super_long_sentences": super_long_sents[:10],
            "distribution": {
                "short_lt15": round(short_count / total * 100, 1),
                "mid_15to30": round(mid_count / total * 100, 1),
                "long_ge30": round(long_count / total * 100, 1),
            },
        }

    def _paragraph_stats(self) -> dict:
        """段落统计"""
        if not self.paragraphs:
            return {"avg_length": 0, "longest": 0, "shortest": 0, "long_paragraphs": []}

        lengths = [self._get_sentence_length(p) for p in self.paragraphs]
        avg_len = sum(lengths) / len(lengths)

        # 长段落阈值（中文：300字）
        long_threshold = 300 if self.is_chinese_dominant else 200
        long_paras = []
        for i, (para, length) in enumerate(zip(self.paragraphs, lengths), 1):
            if length >= long_threshold:
                long_paras.append({"index": i, "length": length, "preview": para[:60]})

        return {
            "count": len(self.paragraphs),
            "avg_length": round(avg_len, 1),
            "longest": max(lengths),
            "shortest": min(lengths),
            "long_paragraphs": long_paras[:5],
        }

    def _extract_chinese_words(self) -> List[str]:
        """简易中文分词：提取常见双字词和四字词"""
        words = []
        # 提取2-4字的中文词组（基于2-4字滑窗，保留有意义的）
        # 这里用简单的频率统计：提取所有2字词
        text = self.text
        # 提取所有2字组合
        two_grams = re.findall(r'[\u4e00-\u9fff]{2}', text)
        words.extend(two_grams)
        # 提取3字组合
        three_grams = re.findall(r'[\u4e00-\u9fff]{3}', text)
        words.extend(three_grams)
        return words

    def _word_analysis(self):
        """词汇分析"""
        self.filler_stats = {}
        self.hot_words = []

        if self.is_chinese_dominant:
            # 填充词统计
            for word, desc in CHINESE_FILLER_WORDS.items():
                count = self.text.count(word)
                if count > 0:
                    self.filler_stats[word] = {"count": count, "desc": desc}

            # 高频词（2字词）
            two_grams = re.findall(r'[\u4e00-\u9fff]{2}', self.text)
            # 过滤掉常见无意义组合
            stop_2grams = {"我们", "你们", "他们", "这个", "那个", "就是", "不是",
                          "可以", "因为", "所以", "但是", "而且", "或者", "如果",
                          "虽然", "然而", "同时", "其中", "以上", "以下", "目前",
                          "已经", "正在", "将要", "应该", "需要", "能够", "进行",
                          "相关", "通过", "对于", "关于", "由于", "为了", "根据",
                          "按照", "基于", "处于", "属于", "位于", "在于", "在于"}
            filtered = [w for w in two_grams if w not in stop_2grams]
            counter = Counter(filtered)
            self.hot_words = counter.most_common(20)
        else:
            # 英文填充词
            text_lower = self.text.lower()
            for phrase, desc in ENGLISH_FILLER_WORDS.items():
                count = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
                if count > 0:
                    self.filler_stats[phrase] = {"count": count, "desc": desc}

            # 高频英文词
            words = re.findall(r'[a-zA-Z]+', self.text.lower())
            stop_words = {"the", "a", "an", "is", "are", "was", "were", "be",
                         "been", "being", "have", "has", "had", "do", "does", "did",
                         "will", "would", "could", "should", "may", "might", "must",
                         "shall", "can", "need", "dare", "ought", "used", "to", "of",
                         "in", "for", "on", "with", "at", "by", "from", "as", "into",
                         "through", "during", "before", "after", "above", "below",
                         "and", "but", "or", "nor", "not", "so", "yet", "both",
                         "either", "neither", "each", "every", "all", "any", "few",
                         "more", "most", "other", "some", "such", "no", "only",
                         "own", "same", "than", "too", "very", "just", "because",
                         "if", "when", "where", "how", "what", "which", "who", "whom",
                         "this", "that", "these", "those", "i", "me", "my", "we",
                         "our", "you", "your", "he", "him", "his", "she", "her",
                         "it", "its", "they", "them", "their"}
            filtered = [w for w in words if w not in stop_words and len(w) > 2]
            counter = Counter(filtered)
            self.hot_words = counter.most_common(20)

    def _word_stats(self) -> dict:
        """词汇统计"""
        # 填充词总数
        total_filler = sum(v["count"] for v in self.filler_stats.values())
        # 主要问题填充词（出现>=5次）
        problem_fillers = {k: v for k, v in self.filler_stats.items() if v["count"] >= 3}

        return {
            "hot_words": self.hot_words[:15],
            "filler_total": total_filler,
            "filler_ratio": round(total_filler / max(self.words, 1) * 100, 1),
            "problem_fillers": problem_fillers,
        }

    def _passive_detection(self):
        """被动句检测"""
        self.passive_results = []
        if not self.is_chinese_dominant:
            return

        for pattern, label in CHINESE_PASSIVE_PATTERNS:
            matches = re.finditer(pattern, self.text)
            for m in matches:
                context_start = max(0, m.start() - 10)
                context_end = min(len(self.text), m.end() + 10)
                self.passive_results.append({
                    "pattern": label,
                    "match": m.group(),
                    "context": self.text[context_start:context_end],
                })

    def _verbose_detection(self):
        """冗长表达检测"""
        self.verbose_results = []
        if not self.is_chinese_dominant:
            return

        for pattern, description in CHINESE_VERBOSE_PATTERNS:
            matches = re.finditer(pattern, self.text)
            for m in matches:
                self.verbose_results.append({
                    "description": description,
                    "match": m.group(),
                })

    def _estimate_reading_time(self) -> float:
        """估算阅读时间（分钟）"""
        if self.is_chinese_dominant:
            # 中文约 300 字/分钟
            minutes = self.words / 300.0
        else:
            # 英文约 200 词/分钟
            minutes = self.words / 200.0
        return round(minutes, 1)

    def _calculate_score(self) -> dict:
        """计算可读性评分"""
        scores = {}

        # 1. 句子长度合理性 (30分)
        s = self._sentence_stats()
        avg = s["avg_length"]
        if self.is_chinese_dominant:
            # 理想平均句长 15-30 字
            if 15 <= avg <= 30:
                len_score = 30
            elif 12 <= avg < 15 or 30 < avg <= 40:
                len_score = 22
            elif 10 <= avg < 12 or 40 < avg <= 50:
                len_score = 15
            else:
                len_score = 8
        else:
            if 12 <= avg <= 20:
                len_score = 30
            elif 8 <= avg < 12 or 20 < avg <= 28:
                len_score = 22
            elif 6 <= avg < 8 or 28 < avg <= 35:
                len_score = 15
            else:
                len_score = 8
        # 长句扣分
        long_penalty = s["long_pct"] * 0.3 + s["super_long_pct"] * 0.5
        len_score = max(0, len_score - long_penalty)
        scores["sentence_length"] = round(len_score)

        # 2. 句子变化性 (15分)
        cv = s["cv"]
        if cv >= 0.6:
            var_score = 15
        elif cv >= 0.4:
            var_score = 12
        elif cv >= 0.25:
            var_score = 8
        else:
            var_score = 4
        scores["sentence_variety"] = round(var_score)

        # 3. 段落结构 (15分)
        p = self._paragraph_stats()
        if p["count"] == 0:
            para_score = 7
        else:
            avg_para = p["avg_length"]
            if self.is_chinese_dominant:
                if 80 <= avg_para <= 250:
                    para_score = 15
                elif 50 <= avg_para < 80 or 250 < avg_para <= 400:
                    para_score = 11
                else:
                    para_score = 6
            else:
                if 60 <= avg_para <= 180:
                    para_score = 15
                elif 40 <= avg_para < 60 or 180 < avg_para <= 300:
                    para_score = 11
                else:
                    para_score = 6
            # 长段落扣分
            if len(p["long_paragraphs"]) > 0:
                para_score = max(0, para_score - len(p["long_paragraphs"]) * 2)
        scores["paragraph_structure"] = round(para_score)

        # 4. 词汇丰富度 (20分)
        w = self._word_stats()
        # 填充词比例扣分
        filler_ratio = w["filler_ratio"]
        if filler_ratio <= 5:
            vocab_score = 20
        elif filler_ratio <= 10:
            vocab_score = 15
        elif filler_ratio <= 15:
            vocab_score = 10
        else:
            vocab_score = 5
        scores["vocabulary"] = round(vocab_score)

        # 5. 表达简洁度 (20分)
        brevity_score = 20
        # 被动句扣分
        brevity_score -= len(self.passive_results) * 1.5
        # 冗长表达扣分
        brevity_score -= len(self.verbose_results) * 2
        brevity_score = max(0, brevity_score)
        scores["brevity"] = round(brevity_score)

        total = sum(scores.values())
        if total >= 90:
            grade = "A"
        elif total >= 75:
            grade = "B"
        elif total >= 60:
            grade = "C"
        elif total >= 40:
            grade = "D"
        else:
            grade = "E"

        return {
            "total": total,
            "grade": grade,
            "breakdown": scores,
        }

    def _collect_issues(self) -> List[dict]:
        """收集所有问题"""
        issues = []

        s = self._sentence_stats()
        p = self._paragraph_stats()
        w = self._word_stats()

        # 长句问题
        if s["super_long_count"] > 0:
            issues.append({
                "type": "超长句",
                "severity": "high",
                "message": f"有 {s['super_long_count']} 个超长句（>60字），最长 {s['super_long_sentences'][0]['length'] if s['super_long_sentences'] else 0} 字",
                "suggestion": "将超长句拆分为2-3个短句，每句只表达一个意思",
            })
        if s["long_pct"] > 20:
            issues.append({
                "type": "长句过多",
                "severity": "medium",
                "message": f"长句占比 {s['long_pct']}%，超过 20% 的建议线",
                "suggestion": "适当拆分长句，增加短句，改善阅读节奏",
            })

        # 句长单一
        if s["cv"] < 0.3:
            issues.append({
                "type": "句长单一",
                "severity": "low",
                "message": f"句长变异系数 {s['cv']}，句式节奏较单一",
                "suggestion": "穿插使用长短句，增加阅读节奏感",
            })

        # 长段落
        if p.get("long_paragraphs"):
            issues.append({
                "type": "段落过长",
                "severity": "medium",
                "message": f"有 {len(p['long_paragraphs'])} 个段落超过 300 字",
                "suggestion": "将长段落拆分为多个短段落，每段一个主题",
            })

        # 填充词
        problem_fillers = w["problem_fillers"]
        if problem_fillers:
            top_filler = max(problem_fillers.items(), key=lambda x: x[1]["count"])
            issues.append({
                "type": "填充词过多",
                "severity": "medium",
                "message": f"'{top_filler[0]}' 出现 {top_filler[1]['count']} 次（{top_filler[1]['desc']}）",
                "suggestion": f"减少'{top_filler[0]}'的使用，替换为更具体的表达",
            })

        # 被动句
        if len(self.passive_results) >= 3:
            issues.append({
                "type": "被动句过多",
                "severity": "low",
                "message": f"检测到 {len(self.passive_results)} 处被动句",
                "suggestion": "适当改为主动语态，使表达更直接有力",
            })

        # 冗长表达
        if self.verbose_results:
            issues.append({
                "type": "冗长表达",
                "severity": "medium",
                "message": f"检测到 {len(self.verbose_results)} 处冗长表达（如'{self.verbose_results[0]['match']}'）",
                "suggestion": "精简冗余表达，如'由于...的原因'改为'由于...'",
            })

        # 平均句长过高
        if self.is_chinese_dominant and s["avg_length"] > 35:
            issues.append({
                "type": "平均句长偏长",
                "severity": "medium",
                "message": f"平均句长 {s['avg_length']} 字，偏长",
                "suggestion": "将平均句长控制在 15-30 字，每句表达一个要点",
            })

        return issues


# ============================================================
# 报告格式化
# ============================================================

def format_report(result: dict) -> str:
    """格式化为文本报告"""
    lines = []
    b = result["basic_stats"]
    sc = result["sentence_analysis"]
    pa = result["paragraph_analysis"]
    wa = result["word_analysis"]
    score = result["readability_score"]
    issues = result["issues"]

    lines.append("=" * 60)
    lines.append("📊 文本可读性分析报告")
    lines.append("=" * 60)
    lines.append("")

    # 基本信息
    lines.append("【基本信息】")
    lines.append(f"  总字符数：{b['chars']:,}")
    lines.append(f"  总字数：{b['words']:,}")
    lines.append(f"  句子数：{b['sentences']}")
    lines.append(f"  段落数：{b['paragraphs']}")
    lines.append(f"  预计阅读时间：约 {b['reading_time_min']} 分钟")
    lines.append("")

    # 评分
    lines.append("【可读性评分】")
    lines.append(f"  总分：{score['total']}/100（{score['grade']}级）")
    lines.append("")
    lines.append("  分项评分：")
    names = {
        "sentence_length": "句子长度合理性",
        "sentence_variety": "句子变化性",
        "paragraph_structure": "段落结构",
        "vocabulary": "词汇丰富度",
        "brevity": "表达简洁度",
    }
    max_scores = {"sentence_length": 30, "sentence_variety": 15,
                  "paragraph_structure": 15, "vocabulary": 20, "brevity": 20}
    for key, name in names.items():
        val = score["breakdown"].get(key, 0)
        mx = max_scores[key]
        bar_filled = int(val / mx * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        lines.append(f"  {name:<16} {bar} {val}/{mx}")
    lines.append("")

    # 句子分析
    lines.append("【句子分析】")
    lines.append(f"  平均句长：{sc['avg_length']} 字")
    lines.append(f"  句长标准差：{sc['std_dev']}（变异系数 {sc['cv']}）")
    lines.append(f"  长句（>40字）：{sc['long_count']} 句（{sc['long_pct']}%）")
    lines.append(f"  超长句（>60字）：{sc['super_long_count']} 句（{sc['super_long_pct']}%）")
    lines.append(f"  句长分布：短(<15字) {sc['distribution']['short_lt15']}% | 中(15-30字) {sc['distribution']['mid_15to30']}% | 长(>30字) {sc['distribution']['long_ge30']}%")
    if sc["super_long_sentences"]:
        lines.append("")
        lines.append("  超长句示例：")
        for s in sc["super_long_sentences"][:3]:
            lines.append(f"    第{s['index']}句（{s['length']}字）：{s['text']}...")
    lines.append("")

    # 段落分析
    lines.append("【段落分析】")
    lines.append(f"  段落数：{pa['count']}")
    lines.append(f"  平均段长：{pa['avg_length']} 字")
    lines.append(f"  最长段落：{pa['longest']} 字")
    if pa.get("long_paragraphs"):
        lines.append("  过长段落：")
        for p in pa["long_paragraphs"][:3]:
            lines.append(f"    第{p['index']}段（{p['length']}字）：{p['preview']}...")
    lines.append("")

    # 词汇分析
    lines.append("【词汇分析】")
    lines.append(f"  填充词总计：{wa['filler_total']} 个（占 {wa['filler_ratio']}%）")
    if wa["problem_fillers"]:
        lines.append("  主要填充词：")
        for word, info in sorted(wa["problem_fillers"].items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
            lines.append(f"    '{word}'：{info['count']} 次（{info['desc']}）")
    if wa["hot_words"]:
        lines.append("  高频词 Top 10：")
        for word, count in wa["hot_words"][:10]:
            lines.append(f"    {word}：{count} 次")
    lines.append("")

    # 被动句和冗长表达
    if result["passive_voice"]:
        lines.append("【被动句】")
        for p in result["passive_voice"][:5]:
            lines.append(f"  [{p['pattern']}] ...{p['context']}...")
        lines.append("")

    if result["verbose_expressions"]:
        lines.append("【冗长表达】")
        for v in result["verbose_expressions"][:5]:
            lines.append(f"  '{v['match']}'：{v['description']}")
        lines.append("")

    # 问题和建议
    lines.append("=" * 60)
    lines.append(f"⚠  发现的问题（共 {len(issues)} 项）")
    lines.append("=" * 60)
    if issues:
        for i, issue in enumerate(issues, 1):
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
            lines.append(f"  {i}. {severity_icon} [{issue['type']}] {issue['message']}")
            lines.append(f"     → 建议：{issue['suggestion']}")
    else:
        lines.append("  未发现明显问题，文本质量良好！")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_issues_only(result: dict) -> str:
    """仅输出问题列表"""
    issues = result["issues"]
    lines = []
    lines.append(f"⚠ 文本问题列表（共 {len(issues)} 项）")
    lines.append("")
    for i, issue in enumerate(issues, 1):
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
        lines.append(f"{i}. {severity_icon} [{issue['type']}]")
        lines.append(f"   {issue['message']}")
        lines.append(f"   → {issue['suggestion']}")
        lines.append("")
    if not issues:
        lines.append("未发现明显问题。")
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="文本可读性分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --input article.txt
  %(prog)s --input article.txt --format json
  %(prog)s --input article.txt --style academic
  %(prog)s --input article.txt --issues-only
  cat article.txt | %(prog)s
        """,
    )
    parser.add_argument("--input", "-i", help="输入文本文件路径（默认从 stdin 读取）")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                        help="输出格式（默认 text）")
    parser.add_argument("--style", "-s",
                        choices=["auto", "general", "academic", "business", "casual", "technical"],
                        default="auto", help="文体类型（默认 auto）")
    parser.add_argument("--issues-only", action="store_true",
                        help="仅输出问题列表")
    parser.add_argument("--output", "-o", help="将报告写入文件")
    args = parser.parse_args()

    # 读取输入
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"错误：文件不存在 - {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("错误：输入为空", file=sys.stderr)
        print("用法：", file=sys.stderr)
        print("  python3 analyze_readability.py --input article.txt", file=sys.stderr)
        print("  cat article.txt | python3 analyze_readability.py", file=sys.stderr)
        sys.exit(1)

    # 分析
    analyzer = TextAnalyzer(text, style=args.style)
    result = analyzer.analyze()

    # 输出
    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    elif args.issues_only:
        output = format_issues_only(result)
    else:
        output = format_report(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"报告已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
