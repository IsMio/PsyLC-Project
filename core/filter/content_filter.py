from typing import Any, Dict, Optional

from core.filter.output_filter import DEFAULT_REPLACEMENTS, OutputFilterService, build_llm_moderator


REASON_TO_RISK_TYPE = {
    'self_harm_risk': '自残/自杀倾向',
    'violence_risk': '暴力/伤害他人',
    'hate_speech': '仇恨言论/歧视',
    'medical_diagnosis': '医疗诊断与处方',
    'medication_advice': '医疗诊断与处方',
    'style_absolute_claim': '绝对化表达',
    'llm_review': '需谨慎审查',
}


class ContentFilter:
    def __init__(self, llm: Optional[Any] = None, policy: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.policy = policy or {}
        self.output_filter = OutputFilterService(
            llm_moderator=build_llm_moderator(True),
            policy=self.policy,
        )

    def check_content(self, user_input: str) -> Dict[str, Any]:
        result = self.output_filter.filter_response(user_input=user_input, response_text=user_input)
        if not result['filtered']:
            return {
                'is_safe': True,
                'risk_type': 'none',
                'fallback_response': '',
            }

        reason = str(result.get('reason') or 'llm_review')
        return {
            'is_safe': False,
            'risk_type': REASON_TO_RISK_TYPE.get(reason, reason),
            'fallback_response': result.get('content') or DEFAULT_REPLACEMENTS['llm_review'],
        }
