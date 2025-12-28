import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.providers.models.question_bank import PracticeRecord, ConsolidationQuestion, PracticeSession
from app.providers.logger import logger


class PracticeService:
    """刷题记录服务类"""

    @staticmethod
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
    ) -> PracticeRecord:
        """
        保存刷题记录

        Args:
            question_id: 题目ID
            question_content: 题目内容
            question_answer: 题目答案
            category: 分类
            difficulty: 难度
            question_type: 题目类型
            is_correct: 是否回答正确
            user_answer: 用户答案
            time_spent: 答题耗时(秒)
            source: 题目来源

        Returns:
            PracticeRecord: 保存的刷题记录
        """
        record = await PracticeRecord.create(
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
        logger.info(f"保存刷题记录: question_id={question_id}, is_correct={is_correct}")
        return record

    @staticmethod
    async def get_practice_history(
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PracticeRecord]:
        """
        获取刷题历史记录

        Args:
            category: 按分类筛选
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            List[PracticeRecord]: 刷题记录列表
        """
        query = PracticeRecord.all()

        if category:
            query = query.filter(category=category)

        if start_date:
            query = query.filter(created_at__gte=start_date)

        if end_date:
            query = query.filter(created_at__lte=end_date)

        records = await query.order_by("-created_at").limit(limit)
        return records

    @staticmethod
    async def get_practice_statistics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取刷题统计信息

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict: 统计信息
        """
        query = PracticeRecord.all()

        if start_date:
            query = query.filter(created_at__gte=start_date)

        if end_date:
            query = query.filter(created_at__lte=end_date)

        records = await query.all()

        total = len(records)
        correct = sum(1 for r in records if r.is_correct is True)
        wrong = sum(1 for r in records if r.is_correct is False)
        skipped = sum(1 for r in records if r.is_correct is None)

        total_time = sum(r.time_spent for r in records)

        by_category = {}
        by_difficulty = {}

        for r in records:
            by_category[r.category] = by_category.get(r.category, 0) + 1
            by_difficulty[r.difficulty] = by_difficulty.get(r.difficulty, 0) + 1

        return {
            "total_count": total,
            "correct_count": correct,
            "wrong_count": wrong,
            "skipped_count": skipped,
            "accuracy": round(correct / total * 100, 2) if total > 0 else 0,
            "total_time": total_time,
            "by_category": by_category,
            "by_difficulty": by_difficulty
        }

    @staticmethod
    async def create_session(
        session_type: str = "practice",
        category: Optional[str] = None
    ) -> PracticeSession:
        """
        创建刷题会话

        Args:
            session_type: 会话类型
            category: 分类

        Returns:
            PracticeSession: 创建的会话
        """
        session = await PracticeSession.create(
            session_type=session_type,
            category=category
        )
        return session

    @staticmethod
    async def update_session(
        session_id: int,
        total_questions: int,
        correct_count: int,
        wrong_count: int,
        skipped_count: int,
        time_spent: int
    ) -> PracticeSession:
        """
        更新刷题会话

        Args:
            session_id: 会话ID
            total_questions: 总题目数
            correct_count: 正确数
            wrong_count: 错误数
            skipped_count: 跳过数
            time_spent: 总耗时(秒)

        Returns:
            PracticeSession: 更新后的会话
        """
        session = await PracticeSession.get(id=session_id)
        session.total_questions = total_questions
        session.correct_count = correct_count
        session.wrong_count = wrong_count
        session.skipped_count = skipped_count
        session.time_spent = time_spent
        session.score = round(correct_count / total_questions * 100, 2) if total_questions > 0 else 0
        await session.save()
        return session

    @staticmethod
    async def get_sessions(
        limit: int = 20
    ) -> List[PracticeSession]:
        """
        获取刷题会话列表

        Args:
            limit: 返回数量限制

        Returns:
            List[PracticeSession]: 会话列表
        """
        sessions = await PracticeSession.all().order_by("-created_at").limit(limit)
        return sessions
