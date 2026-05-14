import json
import re
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class EmotionRecognizer(BaseModel):
    sentiment: str = Field(description="识别到的主要情感")
    intensity: int = Field(description="情感强度评分，范围0-10")
    emotions: list = Field(description="具体情感标签列表")
    confidence: float = Field(description="置信度评分，范围0-1")
    reasoning: str = Field(description="简要分析原因")

def __init__(self):
    """初始化模型和内存"""
    self.sentiment_chain = None


def create_sentiment_chain(llm):
    """创建情感识别链"""
    sentiment_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个情感分析专家。请分析用户消息的情感，并返回JSON格式的结果。
            
分析要求：
1. 识别主要情感：positive（积极）, negative（消极）, neutral（中性）, mixed（混合）
2. 情感强度：0-10的分数，10表示最强烈
3. 具体情感标签：如高兴、愤怒、悲伤、恐惧、惊讶、厌恶等
4. 置信度：0-1的小数

请严格按照以下JSON格式返回，不要添加其他内容：
{{
    "sentiment": "主要情感",
    "intensity": 情感强度分数,
    "emotions": ["情感标签1", "情感标签2"],
    "confidence": 置信度,
    "reasoning": "简要分析原因"
}}"""),
        ("human", "用户消息：{user_input}")
    ])

    return sentiment_prompt | llm | StrOutputParser()

def _parse_sentiment_result( sentiment_result):
    """解析情感分析结果"""
    try:
        # 尝试直接解析JSON
        if isinstance(sentiment_result, str):
            # 提取JSON部分（处理可能的多余文本）
            json_match = re.search(r'\{.*}', sentiment_result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试直接解析整个字符串
                return json.loads(sentiment_result)
        else:
            return sentiment_result
    except json.JSONDecodeError:
        logger.warning(f"无法解析情感分析结果: {sentiment_result}")
        # 返回默认值
        return {
            "sentiment": "neutral",
            "intensity": 5,
            "emotions": ["neutral"],
            "confidence": 0.7,
            "reasoning": "自动解析失败"
        }
def analyze_sentiment(sentiment_chain,user_input):
    """分析用户情感"""
    try:
        sentiment_result = sentiment_chain.invoke({"user_input": user_input})
        # 解析JSON结果
        sentiment_data = _parse_sentiment_result(sentiment_result)
        logger.info(f"情感分析结果: {sentiment_data}")
        return sentiment_data
    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        return {
            "sentiment": "neutral",
            "intensity": 5,
            "emotions": ["neutral"],
            "confidence": 0.5,
            "reasoning": "情感分析暂时不可用"
        }

def create_emotional_response(sentiment_data):
    """根据情感创建个性化的系统提示，包含具体的咨询策略"""
    sentiment = sentiment_data.get("sentiment", "neutral")
    intensity = sentiment_data.get("intensity", 5)
    emotions = sentiment_data.get("emotions", [])

    # 咨询策略映射
    counseling_strategies = {
        # 积极情绪
        "positive": {
            "low": "用户心情不错，请保持积极的交流氛围，可以肯定用户的积极状态，强化积极情绪。",
            "medium": "用户心情良好，请与用户分享积极的互动，可以适当探讨如何保持这种积极状态。",
            "high": "用户非常开心，请热情回应，肯定用户的积极体验，并引导用户思考如何将这种积极情绪转化为长期的心理资源。"
        },
        # 消极情绪
        "negative": {
            "low": "用户情绪略显低落，请提供共情倾听，认可用户的感受，避免急于给出建议。",
            "medium": "用户情绪低落，请采用共情倾听和情绪支持策略，帮助用户表达和理解自己的情绪。可以适当提供一些简单的情绪调节技巧。",
            "high": "用户情绪非常低落，请优先采用共情倾听和情绪支持策略，避免提出解决方案。重点是让用户感受到被理解和接纳，同时温和地引导用户关注自身的资源和积极面。"
        },
        # 混合情绪
        "mixed": {
            "low": "用户情感复杂，请保持中立、客观的态度，帮助用户梳理不同的情绪体验。",
            "medium": "用户情感复杂，请采用认知重构策略，帮助用户从不同角度理解自己的情绪，找到情绪的平衡点。",
            "high": "用户情感强烈且复杂，请先提供情绪支持，帮助用户稳定情绪，然后采用认知重构和问题解决策略，帮助用户理清思路。"
        },
        # 中性情绪
        "neutral": {
            "low": "用户情绪平稳，请保持专业、友好的交流风格，可以采用问题解决策略，帮助用户明确需求。",
            "medium": "用户情绪平稳，请根据用户的具体问题选择合适的咨询策略，如认知重构、问题解决或心理健康知识普及。",
            "high": "用户情绪平静但可能有深层需求，请采用探索性提问，帮助用户更深入地了解自己的需求和感受。"
        }
    }

    # 根据情绪强度选择策略级别
    if intensity <= 3:
        level = "low"
    elif intensity <= 7:
        level = "medium"
    else:
        level = "high"

    # 获取对应的咨询策略
    strategy = counseling_strategies.get(sentiment, counseling_strategies["neutral"]).get(level, "")

    # 针对具体情绪的特殊处理
    specific_emotions = {
        "焦虑": "用户表现出焦虑情绪，请采用放松指导策略，如深呼吸、渐进式肌肉放松等技巧，并提供情绪调节的建议。",
        "抑郁": "用户表现出抑郁情绪，请采用共情倾听和情绪支持策略，避免评判，帮助用户看到积极的方面。",
        "愤怒": "用户表现出愤怒情绪，请保持冷静、中立的态度，采用共情倾听，帮助用户表达和理解自己的愤怒。",
        "恐惧": "用户表现出恐惧情绪，请采用情绪支持和认知重构策略，帮助用户评估现实风险，挑战非理性恐惧。",
        "悲伤": "用户表现出悲伤情绪，请采用共情倾听和情绪支持策略，认可用户的悲伤，提供情感支持。"
    }

    # 添加具体情绪的特殊处理
    emotion_specific = ""
    for emotion in emotions:
        if emotion in specific_emotions:
            emotion_specific = specific_emotions[emotion]
            break

    # 构建完整的情感提示
    emotional_prompt = f"情感感知：{strategy}"
    if emotion_specific:
        emotional_prompt += f"\n情绪特定策略：{emotion_specific}"

    return emotional_prompt