"""
小红书用户分析API响应模型
用于用户画像分析、决策树生成和对话功能
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class UserPersonaBasic(BaseModel):
    """
    用户基础画像
    """

    age_range: Optional[str] = Field(default=None, description="年龄段估计")
    gender: str = Field(default="female", description="性别")
    personality_type: Optional[str] = Field(default=None, description="性格类型估计")
    interests: List[str] = Field(default_factory=list, description="兴趣爱好列表")
    lifestyle: Optional[str] = Field(default=None, description="生活方式描述")


class UserPersonaRelationship(BaseModel):
    """
    用户关系画像
    """

    relationship_type: str = Field(default="unknown", description="关系类型估计")
    relationship_goal: Optional[str] = Field(default=None, description="关系目标")
    communication_style: Optional[str] = Field(default=None, description="沟通风格")
    openness_level: str = Field(default="medium", description="开放程度：low/medium/high")
    attachment_style: Optional[str] = Field(default=None, description="依恋类型")


class UserPersonaShortTerm(BaseModel):
    """
    短期关系评估
    """

    short_term_potential: str = Field(default="unknown", description="短期可能性：low/medium/high")
    attraction_indicators: List[str] = Field(default_factory=list, description="吸引指标")
    opportunity_score: int = Field(default=50, ge=0, le=100, description="机会得分0-100")
    timeline_recommendation: Optional[str] = Field(default=None, description="时间线建议")


class UserPersonaLongTerm(BaseModel):
    """
    长期关系评估
    """

    long_term_compatibility: str = Field(default="unknown", description="长期兼容度：low/medium/high")
    core_value_match: Optional[str] = Field(default=None, description="核心价值观匹配度")
    life_goal_alignment: Optional[str] = Field(default=None, description="人生目标一致性")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")


class IcebreakerSuggestion(BaseModel):
    """
    开场白建议
    """

    icebreaker: str = Field(..., description="开场白内容")
    category: str = Field(default="comment", description="类型：comment/compliment/question")
    success_rate: int = Field(default=50, ge=0, le=100, description="预估成功率0-100")
    risk_level: str = Field(default="medium", description="风险等级：low/medium/high")


class TopicTreeNode(BaseModel):
    """
    话题树节点
    """

    id: str = Field(..., description="节点ID")
    topic: str = Field(..., description="话题内容")
    category: str = Field(default="general", description="话题类别")
    priority: str = Field(default="medium", description="优先级：low/medium/high")
    follow_up_questions: List[str] = Field(default_factory=list, description="跟进问题")
    talking_points: List[str] = Field(default_factory=list, description="谈话要点")
    land_zone_indicators: List[str] = Field(default_factory=list, description="拉升关系指标")


class UserPersonaResponse(BaseModel):
    """
    用户画像分析响应
    """

    user_homepage_url: str = Field(..., description="用户主页URL")
    analysis_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    basic: UserPersonaBasic = Field(default_factory=UserPersonaBasic)
    relationship: UserPersonaRelationship = Field(default_factory=UserPersonaRelationship)
    short_term: UserPersonaShortTerm = Field(default_factory=UserPersonaShortTerm)
    long_term: UserPersonaLongTerm = Field(default_factory=UserPersonaLongTerm)
    icebreakers: List[IcebreakerSuggestion] = Field(default_factory=list, description="开场白建议列表")
    topic_tree: List[TopicTreeNode] = Field(default_factory=list, description="话题树")
    overall_assessment: str = Field(default="", description="总体评估")
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="分析置信度")


class DecisionNode(BaseModel):
    """
    决策树节点
    """

    id: str = Field(..., description="节点ID")
    decision_point: str = Field(..., description="决策点描述")
    situation: str = Field(..., description="情境描述")
    options: List[Dict[str, Any]] = Field(default_factory=list, description="选项列表")
    recommended_action: str = Field(default="", description="推荐行动")
    reasoning: Optional[str] = Field(default=None, description="推荐理由")
    next_steps: List[str] = Field(default_factory=list, description="后续步骤")


class DecisionTreeResponse(BaseModel):
    """
    决策树响应
    """

    user_homepage_url: str = Field(..., description="用户主页URL")
    analysis_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    target_relationship: str = Field(default="romantic", description="目标关系类型")
    decision_tree: List[DecisionNode] = Field(default_factory=list, description="决策树节点列表")
    key_decisions: List[str] = Field(default_factory=list, description="关键决策点")
    success_factors: List[str] = Field(default_factory=list, description="成功因素")
    warning_signals: List[str] = Field(default_factory=list, description="警示信号")
    action_plan: str = Field(default="", description="行动计划")
    overall_feasibility: str = Field(default="unknown", description="总体可行性")


class ConversationContext(BaseModel):
    """
    对话上下文
    """

    conversation_id: str = Field(..., description="对话会话ID")
    user_homepage_url: str = Field(..., description="用户主页URL")
    message_count: int = Field(default=0, description="消息数量")
    decision_tree_context: Optional[Dict[str, Any]] = Field(default=None, description="决策树上下文")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ConversationMessageResponse(BaseModel):
    """
    对话消息响应
    """

    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ConversationResponse(BaseModel):
    """
    对话响应
    """

    conversation_id: str = Field(..., description="对话会话ID")
    user_homepage_url: str = Field(..., description="用户主页URL")
    context: ConversationContext = Field(default_factory=ConversationContext)
    response: ConversationMessageResponse = Field(default_factory=ConversationMessageResponse)
    current_decision_node: Optional[str] = Field(default=None, description="当前决策节点")
    suggestions: List[str] = Field(default_factory=list, description="后续建议")


class ResetConversationResponse(BaseModel):
    """
    重置对话响应
    """

    success: bool = Field(..., description="是否成功")
    conversation_id: str = Field(..., description="新的对话会话ID")
    message: str = Field(default="对话已重置")


class UserAnalyzeErrorResponse(BaseModel):
    """
    错误响应
    """

    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")
