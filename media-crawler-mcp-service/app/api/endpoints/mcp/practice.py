from typing import Optional, List, Dict, Any
from datetime import datetime
from app.api.endpoints import main_app
from app.providers.services.practice_service import PracticeService
from app.providers.services.consolidation_service import ConsolidationQuestionGenerator
from app.providers.logger import logger


@main_app.tool()
async def save_practice_record(
    question_id: str,
    question_content: str,
    question_answer: str,
    category: str,
    difficulty: str,
    question_type: str,
    is_correct: Optional[bool] = None,
    user_answer: Optional[str] = None,
    time_spent: int = 0,
    source: str = ""
) -> Dict[str, Any]:
    """
    保存刷题记录

    当用户完成一道题目后，调用此接口记录刷题结果。系统会记录用户是否答对、答题耗时等信息。

    Args:
        question_id: 题目ID（来自题库的题目编号）
        question_content: 题目内容（完整的题目描述）
        question_answer: 正确答案（标准答案）
        category: 题目分类（如：transformer、llm_fundamentals、rag等）
        difficulty: 难度级别（easy/medium/hard）
        question_type: 题目类型（single_choice/multiple_choice/discussion）
        is_correct: 用户是否回答正确
        user_answer: 用户填写的答案
        time_spent: 答题耗时（秒）
        source: 题目来源

    Returns:
        Dict: 包含保存结果的字典
    """
    try:
        record = await PracticeService.save_practice_record(
            question_id=question_id,
            question_content=question_content,
            question_answer=question_answer,
            category=category,
            difficulty=difficulty,
            question_type=question_type,
            is_correct=is_correct,
            user_answer=user_answer,
            time_spent=time_spent,
            source=source
        )
        return {
            "success": True,
            "message": "刷题记录保存成功",
            "data": {
                "record_id": record.id,
                "created_at": record.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"保存刷题记录失败: {e}")
        return {
            "success": False,
            "message": f"保存失败: {str(e)}"
        }


@main_app.tool()
async def get_practice_history(
    category: Optional[str] = None,
    days: int = 30,
    limit: int = 50
) -> Dict[str, Any]:
    """
    获取刷题历史记录

    查看用户过去的刷题记录，包括正确率、答题情况等统计信息。

    Args:
        category: 按分类筛选（如：transformer、llm_fundamentals等）
        days: 查看最近多少天的记录（默认30天）
        limit: 返回记录数量上限（默认50条）

    Returns:
        Dict: 包含刷题历史和统计信息的字典
    """
    try:
        start_date = datetime.now() if days > 0 else None

        records = await PracticeService.get_practice_history(
            category=category,
            start_date=start_date,
            limit=limit
        )

        record_list = []
        for r in records:
            record_list.append({
                "id": r.id,
                "question_id": r.question_id,
                "question_content": r.question_content[:100] + "..." if len(r.question_content) > 100 else r.question_content,
                "category": r.category,
                "difficulty": r.difficulty,
                "is_correct": r.is_correct,
                "time_spent": r.time_spent,
                "created_at": r.created_at.isoformat()
            })

        stats = await PracticeService.get_practice_statistics(
            start_date=start_date
        )

        return {
            "success": True,
            "data": {
                "records": record_list,
                "statistics": stats
            }
        }
    except Exception as e:
        logger.error(f"获取刷题历史失败: {e}")
        return {
            "success": False,
            "message": f"获取失败: {str(e)}"
        }


@main_app.tool()
async def get_practice_statistics(days: int = 30) -> Dict[str, Any]:
    """
    获取刷题统计信息

    获取用户的刷题统计数据，包括总题数、正确率、各分类的做题情况等。

    Args:
        days: 统计最近多少天的数据（默认30天）

    Returns:
        Dict: 包含详细统计信息的字典
    """
    try:
        start_date = datetime.now() if days > 0 else None

        stats = await PracticeService.get_practice_statistics(
            start_date=start_date
        )

        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取刷题统计失败: {e}")
        return {
            "success": False,
            "message": f"获取失败: {str(e)}"
        }


@main_app.tool()
async def generate_consolidation_questions(
    question_content: str,
    question_answer: str,
    category: str,
    question_type: str = "choice",
    count: int = 3,
    difficulty: str = "same",
    difficulty_level: Optional[str] = None
) -> Dict[str, Any]:
    """
    AI生成巩固练习题

    基于用户刚刚答错的题目，使用AI生成类似的巩固练习题，帮助用户加深理解和记忆。

    Args:
        question_content: 原始题目内容
        question_answer: 原始题目答案
        category: 题目分类
        question_type: 题目类型（choice-选择题，discussion-问答题）
        count: 生成题目数量（默认3道）
        difficulty: 难度设置（same-相同难度，harder-更难，easier-更简单）
        difficulty_level: 可选指定难度级别（easy/medium/hard）

    Returns:
        Dict: 包含生成的巩固题目的字典
    """
    try:
        generator = ConsolidationQuestionGenerator()

        original_question = {
            "content": question_content,
            "answer": question_answer,
            "category": category
        }

        effective_difficulty = difficulty if not difficulty_level else difficulty_level

        questions = await generator.generate_consolidation_questions(
            original_question=original_question,
            question_type=question_type,
            count=count,
            difficulty=effective_difficulty
        )

        if not questions:
            return {
                "success": False,
                "message": "AI生成题目失败，请稍后重试"
            }

        question_list = []
        for q in questions:
            question_list.append({
                "content": q.get("content", ""),
                "question_type": q.get("question_type", question_type),
                "options": q.get("options", []),
                "answer": q.get("answer", ""),
                "explanation": q.get("explanation", ""),
                "difficulty": q.get("difficulty", "medium")
            })

        return {
            "success": True,
            "message": f"成功生成 {len(questions)} 道巩固题目",
            "data": {
                "questions": question_list
            }
        }
    except Exception as e:
        logger.error(f"生成巩固题目失败: {e}")
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }


@main_app.tool()
async def start_practice_session(
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    开始一次刷题练习

    开始一个新的刷题会话，用于追踪单次练习的完整统计信息。

    Args:
        category: 练习分类（可选）

    Returns:
        Dict: 包含会话ID的字典
    """
    try:
        session = await PracticeService.create_session(
            session_type="practice",
            category=category
        )

        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "created_at": session.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"创建刷题会话失败: {e}")
        return {
            "success": False,
            "message": f"创建失败: {str(e)}"
        }


@main_app.tool()
async def end_practice_session(
    session_id: int,
    total_questions: int,
    correct_count: int,
    wrong_count: int,
    skipped_count: int,
    time_spent: int
) -> Dict[str, Any]:
    """
    结束刷题会话

    完成一次刷题练习后，调用此接口更新会话统计信息。

    Args:
        session_id: 会话ID（来自start_practice_session）
        total_questions: 总题目数
        correct_count: 正确题数
        wrong_count: 错误题数
        skipped_count: 跳过题数
        time_spent: 总耗时（秒）

    Returns:
        Dict: 包含会话统计结果的字典
    """
    try:
        session = await PracticeService.update_session(
            session_id=session_id,
            total_questions=total_questions,
            correct_count=correct_count,
            wrong_count=wrong_count,
            skipped_count=skipped_count,
            time_spent=time_spent
        )

        score = round(correct_count / total_questions * 100, 2) if total_questions > 0 else 0

        return {
            "success": True,
            "message": "刷题会话完成",
            "data": {
                "session_id": session.id,
                "total_questions": total_questions,
                "correct_count": correct_count,
                "wrong_count": wrong_count,
                "skipped_count": skipped_count,
                "score": score,
                "time_spent": time_spent
            }
        }
    except Exception as e:
        logger.error(f"更新刷题会话失败: {e}")
        return {
            "success": False,
            "message": f"更新失败: {str(e)}"
        }
