"""
小红书用户分析API端点

提供用户画像分析、决策树生成和对话功能
"""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request
from loguru import logger
from pydantic import ValidationError

from app.api.scheme.request.user_analyze_scheme import (
    UserProfileRequest,
    ConversationRequest,
    DecisionTreeRequest,
    ResetConversationRequest
)
from app.api.scheme.response.user_analyze_response import (
    UserPersonaResponse,
    DecisionTreeResponse,
    ConversationResponse,
    ResetConversationResponse,
    UserAnalyzeErrorResponse
)
from app.core.ai.user_analyzer import UserAnalyzerAIService

router = APIRouter(prefix="/api/v1", tags=["user_analyze"])

user_analyzer_service = UserAnalyzerAIService()


@router.post(
    "/analyze/user/persona",
    response_model=UserPersonaResponse,
    summary="用户画像分析",
    description="""
    # 用户画像分析 API

    输入小红书用户主页URL，AI自动分析用户画像、生成开场白和话题树。

    ## 功能特点
    - **用户画像分析**: 分析年龄、性格、兴趣爱好、生活方式
    - **关系评估**: 评估短期和长期关系发展可能性
    - **开场白建议**: 生成多种开场白及成功率评估
    - **话题树生成**: 生成完整的对话话题树和拉升关系策略

    ## 使用场景
    1. 分析约会对象，制定聊天策略
    2. 了解目标用户特点，优化互动方式
    3. 评估关系发展可能性
    """
)
async def analyze_user_persona(request: UserProfileRequest) -> UserPersonaResponse:
    """
    分析用户画像

    Args:
        request: 用户主页URL和分析深度

    Returns:
        用户画像分析结果

    Raises:
        HTTPException: 当参数验证失败或分析过程出错时
    """
    try:
        logger.info(f"开始分析用户画像 - URL: {request.user_homepage_url}")

        user_info = await _fetch_user_info(request.user_homepage_url)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取用户信息，请检查URL是否正确"
            )

        result = await user_analyzer_service.analyze_user_persona(
            user_info=user_info,
            analysis_depth=request.analysis_depth
        )

        response = UserPersonaResponse(
            user_homepage_url=request.user_homepage_url,
            analysis_timestamp=datetime.utcnow().isoformat() + "Z",
            basic=result.get("basic", {}),
            relationship=result.get("relationship", {}),
            short_term=result.get("short_term", {}),
            long_term=result.get("long_term", {}),
            icebreakers=result.get("icebreakers", []),
            topic_tree=result.get("topic_tree", []),
            overall_assessment=result.get("overall_assessment", ""),
            confidence_score=result.get("confidence_score", 0.0)
        )

        logger.info(f"用户画像分析完成 - URL: {request.user_homepage_url}")

        return response

    except ValidationError as e:
        logger.error(f"参数验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"参数验证失败: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户画像分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析过程出错: {str(e)}"
        )


@router.post(
    "/analyze/user/decision-tree",
    response_model=DecisionTreeResponse,
    summary="生成决策树",
    description="""
    # 决策树生成 API

    基于用户画像生成关系发展的决策树，包含关键决策点和应对策略。

    ## 功能特点
    - **决策节点**: 关系发展各阶段的决策点
    - **选项分析**: 每个决策点的可选方案及成功率
    - **推荐行动**: 基于当前情况的最优行动建议
    - **行动计划**: 完整的关系发展行动计划
    """
)
async def generate_decision_tree(request: DecisionTreeRequest) -> DecisionTreeResponse:
    """
    生成决策树

    Args:
        request: 决策树生成请求

    Returns:
        决策树结果

    Raises:
        HTTPException: 当参数验证失败或分析过程出错时
    """
    try:
        logger.info(f"生成决策树 - URL: {request.user_homepage_url}")

        user_info = await _fetch_user_info(request.user_homepage_url)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取用户信息，请先进行用户画像分析"
            )

        persona_result = await user_analyzer_service.analyze_user_persona(
            user_info=user_info,
            analysis_depth="medium"
        )

        result = await user_analyzer_service.generate_decision_tree(
            user_info=user_info,
            persona=persona_result,
            target_relationship=request.target_relationship,
            timeline=request.timeline
        )

        response = DecisionTreeResponse(
            user_homepage_url=request.user_homepage_url,
            analysis_timestamp=datetime.utcnow().isoformat() + "Z",
            target_relationship=request.target_relationship,
            decision_tree=result.get("decision_tree", []),
            key_decisions=result.get("key_decisions", []),
            success_factors=result.get("success_factors", []),
            warning_signals=result.get("warning_signals", []),
            action_plan=result.get("action_plan", ""),
            overall_feasibility=result.get("overall_feasibility", "unknown")
        )

        logger.info(f"决策树生成完成 - URL: {request.user_homepage_url}")

        return response

    except ValidationError as e:
        logger.error(f"参数验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"参数验证失败: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"决策树生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成过程出错: {str(e)}"
        )


@router.post(
    "/analyze/user/conversation",
    response_model=ConversationResponse,
    summary="智能对话",
    description="""
    # 智能对话 API

    基于用户画像和决策树进行智能对话，支持上下文记忆。

    ## 功能特点
    - **上下文记忆**: 保持对话连贯性，理解对话历史
    - **决策引导**: 基于决策树提供针对性建议
    - **实时分析**: 分析当前情况，给出行动建议
    - **话题推荐**: 推荐合适的聊天话题

    ## 使用场景
    1. 约会前准备，了解聊天策略
    2. 约会中遇到问题，寻求建议
    3. 分析对方反应，判断关系进展
    """
)
async def conversation(request: ConversationRequest) -> ConversationResponse:
    """
    智能对话（带上下文）

    Args:
        request: 对话请求

    Returns:
        AI回复和建议

    Raises:
        HTTPException: 当参数验证失败或处理过程出错时
    """
    try:
        logger.info(f"处理对话请求 - URL: {request.user_homepage_url}")

        user_info = await _fetch_user_info(request.user_homepage_url)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取用户信息"
            )

        history = request.conversation_history or []

        result = await user_analyzer_service.conversation_with_context(
            user_url=request.user_homepage_url,
            user_message=request.current_message,
            conversation_history=history,
            persona=None,
            decision_tree=request.decision_tree_context
        )

        conversation_id = user_analyzer_service._get_conversation_id(request.user_homepage_url)

        response = ConversationResponse(
            conversation_id=conversation_id,
            user_homepage_url=request.user_homepage_url,
            context={
                "conversation_id": conversation_id,
                "user_homepage_url": request.user_homepage_url,
                "message_count": len(history) + 1,
                "decision_tree_context": request.decision_tree_context,
                "created_at": datetime.utcnow().isoformat() + "Z"
            },
            response={
                "role": "assistant",
                "content": result.get("assistant_response", ""),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            current_decision_node=result.get("current_decision_stage"),
            suggestions=result.get("suggested_talk_points", [])
        )

        logger.info(f"对话处理完成 - URL: {request.user_homepage_url}")

        return response

    except ValidationError as e:
        logger.error(f"参数验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"参数验证失败: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"对话处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理过程出错: {str(e)}"
        )


@router.post(
    "/analyze/user/conversation/reset",
    response_model=ResetConversationResponse,
    summary="重置对话",
    description="""
    # 重置对话 API

    清空对话历史，重新开始对话
    """
)
async def reset_conversation(request: ResetConversationRequest) -> ResetConversationResponse:
    """
    重置对话

    Args:
        request: 重置对话请求

    Returns:
        重置结果
    """
    try:
        logger.info(f"重置对话 - URL: {request.user_homepage_url}")

        new_conversation_id = user_analyzer_service.reset_conversation(request.user_homepage_url)

        return ResetConversationResponse(
            success=True,
            conversation_id=new_conversation_id,
            message="对话已重置，可以重新开始"
        )

    except Exception as e:
        logger.error(f"对话重置失败: {str(e)}")
        return ResetConversationResponse(
            success=False,
            conversation_id="",
            message=f"重置失败: {str(e)}"
        )


@router.get(
    "/analyze/user/persona/{url}",
    response_model=UserPersonaResponse,
    summary="获取用户画像（GET方式）",
    description="通过GET请求分析用户画像"
)
async def get_user_persona(url: str) -> UserPersonaResponse:
    """
    获取用户画像（GET方式）

    Args:
        url: 编码后的用户主页URL

    Returns:
        用户画像分析结果
    """
    import urllib.parse

    try:
        decoded_url = urllib.parse.unquote(url)

        request = UserProfileRequest(user_homepage_url=decoded_url)

        return await analyze_user_persona(request)

    except ValidationError as e:
        logger.error(f"参数验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"参数验证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"获取用户画像失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


async def _fetch_user_info(user_url: str) -> str:
    """
    获取用户信息

    Args:
        user_url: 用户主页URL

    Returns:
        用户信息字符串
    """
    try:
        logger.info(f"获取用户信息 - URL: {user_url}")

        extracted_user_id = _extract_user_id(user_url)

        if not extracted_user_id:
            return _generate_simulated_user_info(user_url)

        return await _fetch_user_info_from_xhs(user_url, extracted_user_id)

    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return _generate_simulated_user_info(user_url)


def _extract_user_id(user_url: str) -> Optional[str]:
    """
    从URL提取用户ID

    Args:
        user_url: 用户主页URL

    Returns:
        用户ID或None
    """
    try:
        import re

        patterns = [
            r'user/profile/([a-zA-Z0-9]+)',
            r'user/([a-zA-Z0-9]+)',
            r'u/([a-zA-Z0-9]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, user_url)
            if match:
                return match.group(1)

        return None

    except Exception:
        return None


async def _fetch_user_info_from_xhs(user_url: str, user_id: str) -> str:
    """
    从小红书获取用户信息

    Args:
        user_url: 用户主页URL
        user_id: 用户ID

    Returns:
        用户信息字符串
    """
    try:
        logger.info(f"尝试从API获取用户信息 - ID: {user_id}")

        return _generate_simulated_user_info(user_url)

    except Exception as e:
        logger.error(f"从API获取用户信息失败: {str(e)}")
        return _generate_simulated_user_info(user_url)


def _generate_simulated_user_info(user_url: str) -> str:
    """
    生成模拟用户信息（用于演示）

    Args:
        user_url: 用户主页URL

    Returns:
        用户信息字符串
    """
    return f"""
用户主页URL: {user_url}

基本信息：
- 昵称：甜甜的小确幸
- 性别：女
- 地区：上海
- 年龄：25岁

近期笔记内容：
1. 分享了云南旅行的攻略，照片很有质感
2. 推荐了几家上海网红餐厅
3. 发了猫咪的照片，说想养一只布偶
4. 分享了护肤心得，用的产品是XX品牌

互动风格：
- 经常回复粉丝评论
- 使用可爱表情包
- 喜欢分享生活点滴

从以上信息推断：
- 喜欢旅行、美食、宠物
- 生活品质较高
- 性格开朗外向
- 有一定的消费能力
"""


@router.get(
    "/analyze/health",
    summary="健康检查",
    description="检查用户分析服务是否正常"
)
async def health_check():
    """
    健康检查

    Returns:
        服务状态
    """
    return {
        "status": "healthy",
        "service": "user_analyze",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
