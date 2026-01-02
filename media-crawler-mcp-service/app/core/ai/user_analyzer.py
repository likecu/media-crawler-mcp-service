"""
用户分析AI服务

提供用户画像分析、决策树生成和对话功能
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from loguru import logger


class UserAnalyzerAIService:
    """
    用户分析AI服务类

    提供：
    1. 用户画像分析
    2. 决策树生成
    3. 话题树生成
    4. 带上下文的对话功能
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        初始化用户分析AI服务

        Args:
            gemini_api_key: Gemini API密钥
        """
        self.gemini_api_key = gemini_api_key
        self.conversation_store: Dict[str, Dict[str, Any]] = {}
        self._init_prompts()

    def _init_prompts(self):
        """初始化提示词模板"""
        self.persona_prompt = """
请分析小红书用户主页，生成详细的用户画像。需要从以下维度分析：

用户主页信息：{user_info}

请以JSON格式返回以下分析结果：

{{
    "basic": {{
        "age_range": "年龄段估计，如：20-25岁",
        "gender": "性别",
        "personality_type": "性格类型估计，如：外向型、内敛型",
        "interests": ["兴趣1", "兴趣2"],
        "lifestyle": "生活方式描述"
    }},
    "relationship": {{
        "relationship_type": "关系类型估计",
        "relationship_goal": "关系目标",
        "communication_style": "沟通风格",
        "openness_level": "low/medium/high",
        "attachment_style": "依恋类型"
    }},
    "short_term": {{
        "short_term_potential": "low/medium/high",
        "attraction_indicators": ["吸引指标1", "吸引指标2"],
        "opportunity_score": 0-100的数值,
        "timeline_recommendation": "时间线建议"
    }},
    "long_term": {{
        "long_term_compatibility": "low/medium/high",
        "core_value_match": "核心价值观匹配度",
        "life_goal_alignment": "人生目标一致性",
        "risk_factors": ["风险因素1", "风险因素2"]
    }},
    "icebreakers": [
        {{
            "icebreaker": "开场白内容",
            "category": "comment/compliment/question",
            "success_rate": 0-100,
            "risk_level": "low/medium/high"
        }}
    ],
    "topic_tree": [
        {{
            "id": "topic_1",
            "topic": "话题内容",
            "category": "话题类别",
            "priority": "low/medium/high",
            "follow_up_questions": ["跟进问题1", "跟进问题2"],
            "talking_points": ["谈话要点1", "谈话要点2"],
            "land_zone_indicators": ["拉升关系指标1", "拉升关系指标2"]
        }}
    ],
    "overall_assessment": "总体评估",
    "confidence_score": 0.0-1.0
}}

只返回JSON，不要其他内容。
"""

        self.decision_tree_prompt = """
基于以下用户画像分析结果，生成关系发展的决策树：

用户画像：{persona}

目标关系类型：{target_relationship}
预期时间线：{timeline}

请生成决策树，包含关键决策点和应对策略。以JSON格式返回：

{{
    "decision_tree": [
        {{
            "id": "decision_1",
            "decision_point": "决策点描述",
            "situation": "情境描述",
            "options": [
                {{
                    "option": "选项1描述",
                    "outcome": "可能结果",
                    "success_probability": 0-100
                }}
            ],
            "recommended_action": "推荐行动",
            "reasoning": "推荐理由",
            "next_steps": ["后续步骤1", "后续步骤2"]
        }}
    ],
    "key_decisions": ["关键决策点1", "关键决策点2"],
    "success_factors": ["成功因素1", "成功因素2"],
    "warning_signals": ["警示信号1", "警示信号2"],
    "action_plan": "行动计划概述",
    "overall_feasibility": "low/medium/high/excellent"
}}

只返回JSON，不要其他内容。
"""

        self.conversation_prompt = """
你是一个关系发展顾问，帮助用户分析约会对象并提供对话建议。

当前分析的用户主页：{user_url}
用户画像信息：{persona}
决策树上下文：{decision_tree}

对话历史：
{conversation_history}

当前用户消息：{user_message}

请基于以上信息，提供智能回复建议。你的回复应该：
1. 理解当前对话情境
2. 结合用户画像和决策树给出针对性建议
3. 保持自然、贴心的语气
4. 提供具体的对话策略

以JSON格式返回：

{{
    "assistant_response": "对用户问题的直接回答/建议",
    "analysis": "对当前情况的分析",
    "suggested_talk_points": ["建议话题1", "建议话题2"],
    "current_decision_stage": "当前决策阶段",
    "next_steps": ["建议后续行动1", "建议后续行动2"],
    "tips": ["对话技巧1", "对话技巧2"]
}}

只返回JSON，不要其他内容。
"""

    async def analyze_user_persona(self, user_info: str, analysis_depth: str = "medium") -> Dict[str, Any]:
        """
        分析用户画像

        Args:
            user_info: 用户主页信息
            analysis_depth: 分析深度

        Returns:
            用户画像分析结果
        """
        try:
            logger.info(f"开始分析用户画像，深度: {analysis_depth}")

            prompt = self.persona_prompt.format(
                user_info=user_info
            )

            response = await self._call_gemini(prompt)

            result = self._parse_json_response(response)

            logger.info(f"用户画像分析完成，置信度: {result.get('confidence_score', 0)}")

            return result

        except Exception as e:
            logger.error(f"用户画像分析失败: {str(e)}")
            return self._get_default_persona()

    async def generate_decision_tree(
        self,
        user_info: str,
        persona: Dict[str, Any],
        target_relationship: str = "romantic",
        timeline: str = "medium"
    ) -> Dict[str, Any]:
        """
        生成决策树

        Args:
            user_info: 用户主页信息
            persona: 用户画像
            target_relationship: 目标关系类型
            timeline: 预期时间线

        Returns:
            决策树结果
        """
        try:
            logger.info(f"生成决策树，目标关系: {target_relationship}, 时间线: {timeline}")

            prompt = self.decision_tree_prompt.format(
                persona=json.dumps(persona, ensure_ascii=False, indent=2),
                target_relationship=target_relationship,
                timeline=timeline
            )

            response = await self._call_gemini(prompt)

            result = self._parse_json_response(response)

            logger.info(f"决策树生成完成")

            return result

        except Exception as e:
            logger.error(f"决策树生成失败: {str(e)}")
            return self._get_default_decision_tree()

    async def conversation_with_context(
        self,
        user_url: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        persona: Optional[Dict[str, Any]] = None,
        decision_tree: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        带上下文的对话

        Args:
            user_url: 用户主页URL
            user_message: 当前用户消息
            conversation_history: 对话历史
            persona: 用户画像
            decision_tree: 决策树

        Returns:
            AI回复和建议
        """
        try:
            conversation_id = self._get_conversation_id(user_url)

            logger.info(f"处理对话请求，会话ID: {conversation_id}")

            history_text = self._format_conversation_history(conversation_history)

            prompt = self.conversation_prompt.format(
                user_url=user_url,
                persona=json.dumps(persona or {}, ensure_ascii=False, indent=2),
                decision_tree=json.dumps(decision_tree or {}, ensure_ascii=False, indent=2),
                conversation_history=history_text,
                user_message=user_message
            )

            response = await self._call_gemini(prompt)

            result = self._parse_json_response(response)

            self._save_conversation(conversation_id, user_url, conversation_history, user_message, result)

            return result

        except Exception as e:
            logger.error(f"对话处理失败: {str(e)}")
            return self._get_default_conversation_response()

    async def _call_gemini(self, prompt: str) -> str:
        """
        调用Gemini API

        Args:
            prompt: 提示词

        Returns:
            API响应
        """
        try:
            import os

            if not self.gemini_api_key:
                self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

            if self.gemini_api_key:
                return await self._call_gemini_api(prompt)
            else:
                return self._simulate_gemini_response(prompt)

        except Exception as e:
            logger.error(f"Gemini API调用失败: {str(e)}")
            return self._simulate_gemini_response(prompt)

    async def _call_gemini_api(self, prompt: str) -> str:
        """调用Gemini API（实际实现）"""
        import httpx

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=60.0
            )

            response.raise_for_status()

            data = response.json()

            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _simulate_gemini_response(self, prompt: str) -> str:
        """
        模拟Gemini响应（用于没有API key的情况）

        Args:
            prompt: 提示词

        Returns:
            模拟响应
        """
        import re

        if "persona" in prompt.lower():
            return self._get_simulated_persona_response()
        elif "decision" in prompt.lower():
            return self._get_simulated_decision_tree_response()
        else:
            return self._get_simulated_conversation_response()

    def _get_simulated_persona_response(self) -> str:
        """获取模拟的用户画像响应"""
        return json.dumps({
            "basic": {
                "age_range": "22-28岁",
                "gender": "female",
                "personality_type": "外向开朗型",
                "interests": ["美妆护肤", "旅行", "美食", "摄影"],
                "lifestyle": "热爱生活，喜欢分享美好事物的年轻女性"
            },
            "relationship": {
                "relationship_type": "potential_romantic",
                "relationship_goal": "寻找稳定的恋爱关系",
                "communication_style": "活泼热情，喜欢用表情包",
                "openness_level": "high",
                "attachment_style": "安全型"
            },
            "short_term": {
                "short_term_potential": "medium",
                "attraction_indicators": ["互动积极", "回复速度快"],
                "opportunity_score": 65,
                "timeline_recommendation": "建议2-3周内推进关系"
            },
            "long_term": {
                "long_term_compatibility": "medium",
                "core_value_match": "需要更多了解",
                "life_goal_alignment": "待评估",
                "risk_factors": ["了解不够深入", "可能有竞争者"]
            },
            "icebreakers": [
                {
                    "icebreaker": "看到你最近去了云南旅行，有什么推荐的吗？",
                    "category": "question",
                    "success_rate": 75,
                    "risk_level": "low"
                },
                {
                    "icebreaker": "你的照片都拍得好有质感，是用什么相机拍的呀？",
                    "category": "compliment",
                    "success_rate": 70,
                    "risk_level": "low"
                }
            ],
            "topic_tree": [
                {
                    "id": "topic_1",
                    "topic": "旅行经历分享",
                    "category": "lifestyle",
                    "priority": "high",
                    "follow_up_questions": ["下次想去哪里", "旅行中印象最深的事"],
                    "talking_points": ["云南旅行", "美食体验", "住宿选择"],
                    "land_zone_indicators": ["表达共同旅行意愿", "暗示想一起出行"]
                },
                {
                    "id": "topic_2",
                    "topic": "美食探店",
                    "category": "interest",
                    "priority": "medium",
                    "follow_up_questions": ["推荐餐厅", "厨艺如何"],
                    "talking_points": ["网红餐厅", "自己做饭", "美食喜好"],
                    "land_zone_indicators": ["表达一起吃饭的意愿"]
                }
            ],
            "overall_assessment": "用户整体开放度较高，有发展潜力。建议从旅行、美食等共同兴趣切入，保持积极互动。",
            "confidence_score": 0.75
        }, ensure_ascii=False)

    def _get_simulated_decision_tree_response(self) -> str:
        """获取模拟的决策树响应"""
        return json.dumps({
            "decision_tree": [
                {
                    "id": "decision_1",
                    "decision_point": "初次聊天破冰",
                    "situation": "刚添加好友，需要建立初步联系",
                    "options": [
                        {
                            "option": "直接使用开场白",
                            "outcome": "快速建立联系，但可能显得刻意",
                            "success_probability": 70
                        },
                        {
                            "option": "先观察对方朋友圈",
                            "outcome": "了解更多信息后再互动",
                            "success_probability": 80
                        }
                    ],
                    "recommended_action": "先浏览对方近期动态，找到共同话题后再发起对话",
                    "reasoning": "对方开放度高，但对过于明显的搭讪可能有防备",
                    "next_steps": ["翻阅对方3天内的朋友圈", "找到1-2个切入点", "发起自然对话"]
                },
                {
                    "id": "decision_2",
                    "decision_point": "话题深入时机",
                    "situation": "对话已进行几轮，需要判断是否深入",
                    "options": [
                        {
                            "option": "继续聊表面话题",
                            "outcome": "保持安全但关系进展慢",
                            "success_probability": 60
                        },
                        {
                            "option": "尝试深入话题",
                            "outcome": "可能加快关系进展或有风险",
                            "success_probability": 65
                        }
                    ],
                    "recommended_action": "在对方表达积极回应后，适时深入",
                    "reasoning": "对方开放度高但需要确认兴趣",
                    "next_steps": ["观察回复速度和语气", "在聊旅行时表达想看照片", "适时提出视频/语音"]
                }
            ],
            "key_decisions": [
                "何时发起对话",
                "话题深入时机",
                "何时邀约",
                "如何表达好感"
            ],
            "success_factors": [
                "找到共同话题",
                "保持适当热情",
                "尊重对方节奏",
                "适时表达好感"
            ],
            "warning_signals": [
                "回复变慢或变简短",
                "不主动发起话题",
                "避免深入交流"
            ],
            "action_plan": "第一周：建立联系，了解基本信息。第二周：深入交流，找共同话题。第三周：适时邀约，推进关系。",
            "overall_feasibility": "medium"
        }, ensure_ascii=False)

    def _get_simulated_conversation_response(self) -> str:
        """获取模拟的对话响应"""
        return json.dumps({
            "assistant_response": "听起来进展不错！她愿意分享自己的日常，说明对你有好感。建议可以顺着这个话题，问问她平时周末喜欢做什么，既能了解她的生活方式，又能为下次邀约做铺垫。",
            "analysis": "对方主动分享日常是好感信号，当前互动氛围良好",
            "suggested_talk_points": ["周末活动", "兴趣爱好", "最近想做的事"],
            "current_decision_stage": "关系建立期",
            "next_steps": ["继续积极回应", "适时分享自己的日常", "为邀约做铺垫"],
            "tips": ["保持话题轻松有趣", "适当表达认同和欣赏", "不要急于推进"]
        }, ensure_ascii=False)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        解析JSON响应

        Args:
            response: API响应

        Returns:
            解析后的JSON对象
        """
        try:
            text = response.strip()

            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()

            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}, 响应: {response[:200]}")
            raise ValueError(f"无法解析响应: {str(e)}")

    def _get_conversation_id(self, user_url: str) -> str:
        """
        获取对话ID

        Args:
            user_url: 用户主页URL

        Returns:
            对话ID
        """
        if user_url not in self.conversation_store:
            self.conversation_store[user_url] = {
                "conversation_id": str(uuid.uuid4()),
                "message_count": 0
            }

        return self.conversation_store[user_url]["conversation_id"]

    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """
        格式化对话历史

        Args:
            history: 对话历史

        Returns:
            格式化后的字符串
        """
        if not history:
            return "（暂无对话历史）"

        lines = []
        for msg in history[-10:]:
            role = "用户" if msg.get("role") == "user" else "助手"
            lines.append(f"{role}: {msg.get('content', '')}")

        return "\n".join(lines)

    def _save_conversation(
        self,
        conversation_id: str,
        user_url: str,
        history: List[Dict[str, str]],
        user_message: str,
        response: Dict[str, Any]
    ):
        """
        保存对话记录

        Args:
            conversation_id: 对话ID
            user_url: 用户主页URL
            history: 对话历史
            user_message: 用户消息
            response: AI响应
        """
        if user_url not in self.conversation_store:
            self.conversation_store[user_url] = {
                "conversation_id": conversation_id,
                "message_count": 0
            }

        self.conversation_store[user_url]["message_count"] += 1

    def _get_default_persona(self) -> Dict[str, Any]:
        """获取默认用户画像"""
        return {
            "basic": {
                "age_range": "未知",
                "gender": "female",
                "personality_type": "未知",
                "interests": [],
                "lifestyle": ""
            },
            "relationship": {
                "relationship_type": "unknown",
                "relationship_goal": "",
                "communication_style": "",
                "openness_level": "medium",
                "attachment_style": ""
            },
            "short_term": {
                "short_term_potential": "unknown",
                "attraction_indicators": [],
                "opportunity_score": 50,
                "timeline_recommendation": ""
            },
            "long_term": {
                "long_term_compatibility": "unknown",
                "core_value_match": "",
                "life_goal_alignment": "",
                "risk_factors": []
            },
            "icebreakers": [],
            "topic_tree": [],
            "overall_assessment": "分析失败，请重试",
            "confidence_score": 0.0
        }

    def _get_default_decision_tree(self) -> Dict[str, Any]:
        """获取默认决策树"""
        return {
            "decision_tree": [],
            "key_decisions": [],
            "success_factors": [],
            "warning_signals": [],
            "action_plan": "",
            "overall_feasibility": "unknown"
        }

    def _get_default_conversation_response(self) -> Dict[str, Any]:
        """获取默认对话响应"""
        return {
            "assistant_response": "抱歉，我现在无法处理你的请求。请稍后再试。",
            "analysis": "",
            "suggested_talk_points": [],
            "current_decision_stage": "",
            "next_steps": [],
            "tips": []
        }

    def reset_conversation(self, user_url: str) -> str:
        """
        重置对话

        Args:
            user_url: 用户主页URL

        Returns:
            新的对话ID
        """
        if user_url in self.conversation_store:
            del self.conversation_store[user_url]

        return self._get_conversation_id(user_url)
