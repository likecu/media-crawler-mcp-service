"""
小红书用户分析API请求模型
用于用户画像分析、决策树生成和对话功能
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum


class UserProfileRequest(BaseModel):
    """
    用户主页分析请求
    """

    user_homepage_url: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="小红书用户主页URL",
        examples=["https://www.xiaohongshu.com/user/profile/1234567890"]
    )

    analysis_depth: Optional[str] = Field(
        default="medium",
        description="分析深度：basic(基础)、medium(中等)、detailed(详细)",
        examples=["medium"]
    )


class ConversationMessage(BaseModel):
    """
    对话消息
    """

    role: str = Field(
        ...,
        description="消息角色：user或assistant",
        examples=["user"]
    )

    content: str = Field(
        ...,
        description="消息内容",
        examples=["我觉得她今天好像不太开心"]
    )


class ConversationRequest(BaseModel):
    """
    对话请求
    """

    user_homepage_url: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="小红书用户主页URL",
        examples=["https://www.xiaohongshu.com/user/profile/1234567890"]
    )

    conversation_history: Optional[List[ConversationMessage]] = Field(
        default=None,
        description="对话历史，用于保持上下文",
        examples=[
            [
                {"role": "user", "content": "帮我分析这个用户"},
                {"role": "assistant", "content": "分析结果..."}
            ]
        ]
    )

    current_message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="当前用户输入的消息",
        examples=["约会时应该聊什么话题？"]
    )

    decision_tree_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="决策树上下文，传入后可基于决策树进行对话"
    )


class TopicNode(BaseModel):
    """
    话题节点
    """

    id: str = Field(..., description="节点ID")
    topic: str = Field(..., description="话题内容")
    type: str = Field(default="question", description="节点类型：question/icebreaker/topic/landing")
    follow_up: Optional[List[str]] = Field(default=None, description="后续话题列表")
    tips: Optional[str] = Field(default=None, description="对话技巧提示")


class DecisionTreeRequest(BaseModel):
    """
    决策树生成请求
    """

    user_homepage_url: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="小红书用户主页URL"
    )

    target_relationship: Optional[str] = Field(
        default="romantic",
        description="目标关系类型：romantic(恋爱)、friendship(交友)、casual(随意)"
    )

    timeline: Optional[str] = Field(
        default="medium",
        description="预期时间线：short(短期)、medium(中期)、long(长期)"
    )


class ResetConversationRequest(BaseModel):
    """
    重置对话请求
    """

    user_homepage_url: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="小红书用户主页URL"
    )
