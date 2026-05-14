import re
from typing import Any, Callable, Dict, Optional


DEFAULT_REPLACEMENTS = {
    'medical_diagnosis': '我不能直接替代专业医生或心理治疗师做诊断，也不能据此给出确定性医疗结论。如果你已经持续感到明显痛苦、功能受影响，建议尽快联系专业精神科或心理咨询人员做正式评估。我也可以先陪你梳理最近的情绪、睡眠和压力变化。',
    'medication_advice': '我不能直接提供药物处方、剂量或替代正规医疗建议。如果你在考虑用药，请尽快咨询精神科医生或其他合格医疗专业人员。我可以先帮助你整理症状变化与就医时需要表达的重点。',
    'self_harm_risk': '如果你现在有伤害自己或他人的想法，并且觉得可能会付诸行动，请立即联系当地紧急救助电话、最近的急诊机构，或立刻联系你身边可信任的人陪伴你。你不需要一个人扛着。如果你愿意，也可以马上告诉我你当前是否处于紧急危险中。',
    'violence_risk': '我不能帮助策划、鼓励或优化伤害他人的行为。如果你现在情绪非常激动，建议先立刻离开可能造成伤害的场景、放下危险物品，并尽快联系可信任的人或当地紧急支持资源协助降温。我也可以先陪你把触发愤怒的情境梳理清楚。',
    'hate_speech': '我不能帮助强化针对特定群体的侮辱、歧视或伤害表达。如果你愿意，我可以陪你把当前的愤怒、委屈或冲突重新表述成更安全、具体的问题，再一起讨论应对办法。',
    'style_absolute_claim': '我不能保证结果，也不适合用绝对化方式下结论。不过我可以基于你现在描述的情况，陪你一起做更稳妥的分析，并给出更审慎的支持建议。',
    'llm_review': '为了避免给出可能不安全或过度确定的建议，我先不直接沿用刚才那种表达。我可以换一种更谨慎的方式，陪你一起梳理问题，并建议在需要时寻求专业支持。',
}


class OutputFilterService:
    def __init__(self, llm_moderator: Optional[Callable[[str, str], Dict[str, Any]]] = None, policy: Optional[Dict[str, Any]] = None):
        self.llm_moderator = llm_moderator
        self.policy = policy or {}
        self.rule_patterns = [
            ('self_harm_risk', [r'自杀(吧|去)', r'结束生命', r'最有效的自残', r'去死', r'一了百了', r'吃安眠药']),
            ('violence_risk', [r'砍死', r'杀了他', r'带把刀', r'报复他', r'弄死他']),
            ('hate_speech', [r'都该死', r'不配活着', r'都是垃圾', r'某某地域的人都是垃圾', r'低等民族']),
            ('medical_diagnosis', [r'你就是[^。！？\n]*抑郁症', r'你已经患上', r'可以确诊为', r'明确诊断']),
            ('medication_advice', [r'吃[\u4e00-\u9fa5A-Za-z0-9]+mg', r'处方', r'直接服用', r'按这个剂量']),
            ('style_absolute_claim', [r'我保证', r'一定会好', r'必须马上', r'彻底治好', r'百分之百']),
        ]

    def filter_response(self, *, user_input: str, response_text: str) -> Dict[str, Any]:
        normalized = (response_text or '').strip()
        if not normalized:
            return {'filtered': False, 'reason': None, 'content': response_text}

        rule_reason = self._match_rule(normalized)
        if rule_reason:
            return self._replacement(rule_reason)

        if self.llm_moderator:
            review = self.llm_moderator(user_input, normalized) or {}
            if review.get('blocked'):
                return self._replacement(str(review.get('reason') or 'llm_review'))

        return {'filtered': False, 'reason': None, 'content': response_text}

    def _match_rule(self, response_text: str) -> Optional[str]:
        custom_rules = self.policy.get('rules') or []
        for item in custom_rules:
            if not item.get('enabled', True):
                continue
            pattern = str(item.get('pattern') or '').strip()
            reason = str(item.get('reason') or '').strip()
            if pattern and reason and re.search(pattern, response_text, re.IGNORECASE):
                return reason

        for reason, patterns in self.rule_patterns:
            for pattern in patterns:
                if re.search(pattern, response_text, re.IGNORECASE):
                    return reason
        return None

    def _replacement(self, reason: str) -> Dict[str, Any]:
        custom_templates = self.policy.get('templates') or {}
        return {
            'filtered': True,
            'reason': reason,
            'content': custom_templates.get(reason, DEFAULT_REPLACEMENTS.get(reason, DEFAULT_REPLACEMENTS['llm_review'])),
        }


def build_llm_moderator(review_enabled: bool = True):
    if not review_enabled:
        return None

    def moderator(user_input: str, response_text: str) -> Dict[str, Any]:
        lower_text = response_text.lower()
        if any(flag in lower_text for flag in ['我保证', '保证你', '一定治好', '百分之百']):
            return {'blocked': True, 'reason': 'style_absolute_claim'}
        if '诊断' in response_text and any(flag in response_text for flag in ['明确', '就是', '确诊']):
            return {'blocked': True, 'reason': 'medical_diagnosis'}
        return {'blocked': False, 'reason': None}

    return moderator


def build_stream_replace_signal(content: str, reason: Optional[str]) -> Dict[str, Any]:
    return {
        'choices': [
            {
                'delta': {'content': content},
                'finish_reason': None,
            },
        ],
        'replace': True,
        'filtered': True,
        'filter_reason': reason,
    }
