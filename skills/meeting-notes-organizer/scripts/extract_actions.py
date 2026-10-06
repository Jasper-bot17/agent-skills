#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会议纪要整理助手 - 行动项初步提取脚本

基于关键词模式从会议原始文本中标记候选行动项，输出 JSON 格式供 AI 复核。

注意：本脚本仅做模式匹配，结果必须经过语义复核后才能写入最终纪要。
      脚本不会替代 AI 的理解能力，仅用于减少长文本中的遗漏。

用法：
    python3 extract_actions.py <input_file> [--output <output_file>]
    python3 extract_actions.py <input_file> --format text   # 纯文本输出
    cat notes.txt | python3 extract_actions.py -              # 从 stdin 读取
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional


# ============================================================
# 行动项触发关键词模式
# ============================================================

# 中文行动动词模式（出现在句子中，暗示需要执行某动作）
ACTION_VERBS_CN = [
    r"负责", r"跟进", r"推进", r"落实", r"执行", r"完成", r"提交",
    r"准备", r"整理", r"输出", r"提供", r"对接", r"协调", r"安排",
    r"确认", r"核实", r"调研", r"评估", r"分析", r"设计", r"开发",
    r"测试", r"上线", r"发布", r"优化", r"修复", r"解决", r"处理",
    r"联系", r"沟通", r"同步", r"汇报", r"review", r"评审",
    r"需要.{0,10}(做|完成|准备|提交|提供)",
    r"得(把|将|去).{0,20}(做|弄|搞|完成)",
    r"尽快", r"赶紧", r"马上", r"立刻",
]

# 英文行动动词模式
ACTION_VERBS_EN = [
    r"\bneed to\b", r"\bshould\b", r"\bmust\b", r"\bhave to\b",
    r"\baction item\b", r"\bfollow up\b", r"\bfollow-up\b",
    r"\bowner\b", r"\bresponsible\b", r"\bassigned to\b",
    r"\bdeadline\b", r"\bdue\b", r"\bby \w+ \d+\b",
    r"\blet's\b", r"\blet us\b", r"\bwe need\b",
    r"\bplease\b", r"\bmake sure\b", r"\bensure\b",
]

# 负责人标记模式
OWNER_PATTERNS = [
    r"([\u4e00-\u9fa5]{2,4})(?=负责|跟进|推进|落实|来做|来搞|来弄|去做)",
    r"由([\u4e00-\u9fa5]{2,4})(来|去|负责|跟进|推进)",
    r"([\u4e00-\u9fa5]{2,4})的话",
    r"@([\w\u4e00-\u9fa5]+)",  # @提及
    r"\bassigned to\s+([A-Za-z][A-Za-z\s]{1,30})\b",
    r"\bowner[:：]\s*([A-Za-z\u4e00-\u9fa5][\w\u4e00-\u9fa5\s]{1,30})\b",
]

# 截止日期标记模式
DEADLINE_PATTERNS = [
    # 中文日期
    r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)",
    r"(\d{1,2}月\d{1,2}日?)",
    r"(本周[一二三四五六日天])",
    r"(下周[一二三四五六日天])",
    r"(这周[一二三四五六日天])",
    r"(这周内|本周内|下周内)",
    r"(今天|明天|后天|大后天)",
    r"(月底|月初|月中|周末)",
    r"(季度末|年底|年末)",
    # 英文日期
    r"\b(by\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(st|nd|rd|th)?(,?\s+\d{4})?\b",
    r"\b(\d{1,2}/\d{1,2}(/\d{2,4})?)\b",
    r"\b(end of (this|next) (week|month|quarter|year))\b",
    r"\b(EOD|COB|EOW|EOM)\b",
    # 通用
    r"(截止|deadline|due)([:：]?\s*)([^，。,.\n]{1,30})",
]

# 决议标记模式
RESOLUTION_PATTERNS = [
    r"(决定|确定|确认|通过|同意|达成一致|就这么定|定下来|结论是)",
    r"\b(decided|agreed|resolved|conclusion|approved|confirmed)\b",
    r"(最终|最后).{0,10}(决定|确定|选择|用|采用)",
]

# 待决问题标记模式
OPEN_QUESTION_PATTERNS = [
    r"(待定|待确认|待讨论|待研究|待评估|未定|未确定|还没定)",
    r"(下次再说|下次讨论|回头再说|再议|从长计议)",
    r"(需要进一步|还需要|有待|尚需)",
    r"\b(TBD|TBC|open question|to be discussed|to be confirmed)\b",
    r"(有没有|是否|能不能|可不可以|要不要).{0,30}(\?|？)",
]


@dataclass
class ActionItem:
    """候选行动项数据结构"""
    id: str
    text: str                  # 原始句子
    task: str                  # 提取的任务描述（清洗后）
    owner: Optional[str]       # 负责人
    deadline: Optional[str]    # 截止日期
    priority: str              # 初步优先级（高/中/低/未知）
    confidence: float          # 匹配置信度 0-1
    source_line: int           # 原文行号
    matched_patterns: List[str]  # 命中的模式类型


def split_sentences(text: str) -> List[tuple]:
    """
    将文本按句子分割，返回 (句子内容, 起始行号) 列表。
    支持中英文标点断句。
    """
    # 先按行分割，记录行号
    lines = text.split('\n')
    sentences = []

    for line_idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        # 按中英文句末标点分割
        parts = re.split(r'(?<=[。！？!?；;])\s*', line)
        for part in parts:
            part = part.strip()
            if part and len(part) > 3:  # 过滤过短的碎片
                sentences.append((part, line_idx))

    return sentences


def detect_owner(sentence: str) -> Optional[str]:
    """从句子中尝试提取负责人"""
    for pattern in OWNER_PATTERNS:
        match = re.search(pattern, sentence)
        if match:
            owner = match.group(1).strip()
            # 过滤掉明显不是人名的匹配
            if len(owner) >= 2 and not re.match(r'^(我们|你们|他们|大家|团队|部门|公司|相关)$', owner):
                return owner
    return None


def detect_deadline(sentence: str) -> Optional[str]:
    """从句子中尝试提取截止日期"""
    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def detect_priority(sentence: str) -> str:
    """根据语境初步判断优先级"""
    high_patterns = [r'紧急| ASAP|立即|马上|立刻|今天|阻塞|卡住|关键|重要紧急',
                     r'\bASAP\b|\burgent\b|\bimmediately\b|\bcritical\b|\bblocker\b']
    low_patterns = [r'优化|改进|长期|后续|有空|顺便|可以考虑|未来',
                     r'\boptional\b|\bnice.to.have\b|\blater\b|\beventually\b']

    for p in high_patterns:
        if re.search(p, sentence, re.IGNORECASE):
            return "高"
    for p in low_patterns:
        if re.search(p, sentence, re.IGNORECASE):
            return "低"
    return "中"


def is_action_item(sentence: str) -> tuple:
    """
    判断句子是否包含行动项。
    返回 (是否行动项, 命中模式列表, 置信度)
    """
    matched = []
    score = 0.0

    # 检查中文行动动词
    for pattern in ACTION_VERBS_CN:
        if re.search(pattern, sentence):
            matched.append(f"cn_verb:{pattern}")
            score += 0.3
            break  # 同类只计一次

    # 检查英文行动动词
    for pattern in ACTION_VERBS_EN:
        if re.search(pattern, sentence, re.IGNORECASE):
            matched.append(f"en_verb:{pattern}")
            score += 0.3
            break

    # 有负责人加分
    if detect_owner(sentence):
        matched.append("has_owner")
        score += 0.2

    # 有截止日期加分
    if detect_deadline(sentence):
        matched.append("has_deadline")
        score += 0.2

    # 包含明确的任务交付物加分
    if re.search(r'(文档|报告|方案|设计|代码|PRD|PPT|邮件|会议纪要|清单|表格|数据|测试用例)', sentence):
        matched.append("has_deliverable")
        score += 0.1

    # 疑问句通常不是行动项（除非是反问/要求）
    if sentence.endswith(('?', '？')) and not re.search(r'(能不能|可不可以|要不要).{0,10}(负责|做|准备|提交)', sentence):
        score -= 0.3

    # 纯背景陈述减分
    if re.match(r'^(关于|对于|至于|说到|提到|之前|上次|最近|目前|现在)', sentence) and not re.search(r'|'.join(ACTION_VERBS_CN[:20]), sentence):
        score -= 0.2

    is_action = score >= 0.3
    confidence = min(score, 1.0)

    return is_action, matched, confidence


def clean_task_text(sentence: str) -> str:
    """清洗句子，提取更简洁的任务描述"""
    task = sentence
    # 去除开头的语气词和连接词
    task = re.sub(r'^(然后|接下来|另外|还有|就是|那个|这个|嗯|啊|哦|呃|so|well|and|but)\s*', '', task, flags=re.IGNORECASE)
    # 去除尾部的语气词
    task = re.sub(r'[，。！？、；：,.!?;:]+$', '', task)
    # 压缩多余空格
    task = re.sub(r'\s+', ' ', task).strip()
    return task


def extract_actions(text: str) -> List[ActionItem]:
    """主函数：从文本中提取所有候选行动项"""
    sentences = split_sentences(text)
    action_items = []
    counter = 1

    for sentence, line_num in sentences:
        is_action, matched, confidence = is_action_item(sentence)
        if is_action:
            item = ActionItem(
                id=f"A{counter:03d}",
                text=sentence,
                task=clean_task_text(sentence),
                owner=detect_owner(sentence),
                deadline=detect_deadline(sentence),
                priority=detect_priority(sentence),
                confidence=round(confidence, 2),
                source_line=line_num,
                matched_patterns=matched,
            )
            action_items.append(item)
            counter += 1

    return action_items


def extract_resolutions(text: str) -> List[dict]:
    """提取候选决议"""
    sentences = split_sentences(text)
    resolutions = []
    counter = 1

    for sentence, line_num in sentences:
        for pattern in RESOLUTION_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                resolutions.append({
                    "id": f"R{counter:03d}",
                    "text": sentence,
                    "matched_pattern": pattern,
                    "source_line": line_num,
                })
                counter += 1
                break

    return resolutions


def extract_open_questions(text: str) -> List[dict]:
    """提取候选待决问题"""
    sentences = split_sentences(text)
    questions = []
    counter = 1

    for sentence, line_num in sentences:
        for pattern in OPEN_QUESTION_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                questions.append({
                    "id": f"Q{counter:03d}",
                    "text": sentence,
                    "matched_pattern": pattern,
                    "source_line": line_num,
                })
                counter += 1
                break

    return questions


def format_text_output(actions: List[ActionItem], resolutions: List[dict],
                       questions: List[dict]) -> str:
    """格式化为纯文本输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("会议纪要整理助手 - 初步提取结果")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"【候选行动项】共 {len(actions)} 条")
    lines.append("-" * 40)
    for item in actions:
        lines.append(f"[{item.id}] (置信度: {item.confidence}, 行: {item.source_line})")
        lines.append(f"  任务: {item.task}")
        lines.append(f"  负责人: {item.owner or '未识别'}")
        lines.append(f"  截止: {item.deadline or '未识别'}")
        lines.append(f"  优先级: {item.priority}")
        lines.append("")

    lines.append(f"【候选决议】共 {len(resolutions)} 条")
    lines.append("-" * 40)
    for r in resolutions:
        lines.append(f"[{r['id']}] (行: {r['source_line']})")
        lines.append(f"  {r['text']}")
        lines.append("")

    lines.append(f"【候选待决问题】共 {len(questions)} 条")
    lines.append("-" * 40)
    for q in questions:
        lines.append(f"[{q['id']}] (行: {q['source_line']})")
        lines.append(f"  {q['text']}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("注意：以上为模式匹配初步结果，必须经过语义复核后才能写入最终纪要。")
    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="会议纪要整理助手 - 从会议文本中初步提取行动项、决议和待决问题"
    )
    parser.add_argument("input", help="输入文件路径，使用 - 表示从 stdin 读取")
    parser.add_argument("--output", "-o", help="输出文件路径（默认输出到 stdout）")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json",
                        help="输出格式（默认 json）")
    parser.add_argument("--min-confidence", "-c", type=float, default=0.0,
                        help="最低置信度过滤（0-1，默认 0 不过滤）")

    args = parser.parse_args()

    # 读取输入
    if args.input == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"错误：文件 '{args.input}' 不存在", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误：读取文件失败 - {e}", file=sys.stderr)
            sys.exit(1)

    if not text.strip():
        print("错误：输入文本为空", file=sys.stderr)
        sys.exit(1)

    # 执行提取
    actions = extract_actions(text)
    resolutions = extract_resolutions(text)
    questions = extract_open_questions(text)

    # 置信度过滤
    if args.min_confidence > 0:
        actions = [a for a in actions if a.confidence >= args.min_confidence]

    # 格式化输出
    if args.format == "json":
        result = {
            "summary": {
                "total_action_items": len(actions),
                "total_resolutions": len(resolutions),
                "total_open_questions": len(questions),
                "input_length": len(text),
            },
            "action_items": [asdict(a) for a in actions],
            "resolutions": resolutions,
            "open_questions": questions,
            "note": "以上为模式匹配初步结果，必须经过语义复核后才能写入最终纪要。",
        }
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_text_output(actions, resolutions, questions)

    # 输出
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"结果已写入: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"错误：写入文件失败 - {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)


if __name__ == "__main__":
    main()
