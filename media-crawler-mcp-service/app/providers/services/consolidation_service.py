import json
from typing import List, Dict, Any, Optional
from app.providers.models.question_bank import ConsolidationQuestion
from app.providers.logger import logger


class ConsolidationQuestionGenerator:
    """AI巩固题目生成器"""

    def __init__(self, api_key: str = None):
        """
        初始化生成器

        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"

    async def generate_consolidation_questions(
        self,
        original_question: Dict[str, Any],
        question_type: str = "choice",
        count: int = 3,
        difficulty: str = "same"
    ) -> List[Dict[str, Any]]:
        """
        基于原始题目生成巩固练习题

        Args:
            original_question: 原始题目信息
            question_type: 题目类型（choice-选择题, discussion-问答题）
            count: 生成数量
            difficulty: 难度（same-相同, harder-更难, easier-更简单）

        Returns:
            List[Dict]: 生成的巩固题目列表
        """
        content = original_question.get("content", "")
        answer = original_question.get("answer", "")
        category = original_question.get("category", "")

        difficulty_map = {
            "same": "保持与原题相同的难度",
            "harder": "比原题稍微更难一些",
            "easier": "比原题稍微更简单一些"
        }

        prompt = self._build_prompt(
            content=content,
            answer=answer,
            category=category,
            question_type=question_type,
            count=count,
            difficulty=difficulty_map[difficulty]
        )

        try:
            response = await self._call_ai_api(prompt)
            questions = self._parse_response(response, question_type)
            return questions
        except Exception as e:
            logger.error(f"生成巩固题目失败: {e}")
            return []

    def _build_prompt(
        self,
        content: str,
        answer: str,
        category: str,
        question_type: str,
        count: int,
        difficulty: str
    ) -> str:
        """
        构建AI提示词

        Args:
            content: 原始题目内容
            answer: 原始题目答案
            category: 分类
            question_type: 题目类型
            count: 生成数量
            difficulty: 难度要求

        Returns:
            str: 完整的提示词
        """
        if question_type == "choice":
            prompt = f"""你是一个专业的面试题出题专家。请基于以下面试题，生成{count}道巩固选择题。

原始题目分类：{category}
题目内容：{content}
参考答案：{answer}
难度要求：{difficulty}

请生成{count}道选择题，要求：
1. 考察知识点与原题相关但不完全相同
2. 每道题有4个选项，有且仅有一个正确答案
3. 选项要有一定的干扰性，但不能太明显
4. 答案需要包含解析

请以JSON数组格式返回，格式如下：
[
  {{
    "content": "题目内容",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "explanation": "答案解析",
    "difficulty": "medium"
  }}
]
"""
        else:
            prompt = f"""你是一个专业的面试题出题专家。请基于以下面试题，生成{count}道巩固问答题。

原始题目分类：{category}
题目内容：{content}
参考答案：{answer}
难度要求：{difficulty}

请生成{count}道问答题，要求：
1. 考察知识点与原题相关但不完全相同
2. 问题要有一定的深度和思考性
3. 答案要点要清晰明确
4. 适当添加解析说明

请以JSON数组格式返回，格式如下：
[
  {{
    "content": "题目内容",
    "answer": "答案要点",
    "explanation": "解析说明",
    "difficulty": "medium"
  }}
]
"""
        return prompt

    async def _call_ai_api(self, prompt: str) -> str:
        """
        调用AI API

        Args:
            prompt: 提示词

        Returns:
            str: API响应
        """
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的面试题出题专家，擅长生成高质量的面试题目。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _parse_response(
        self,
        response: str,
        question_type: str
    ) -> List[Dict[str, Any]]:
        """
        解析AI响应

        Args:
            response: AI响应内容
            question_type: 题目类型

        Returns:
            List[Dict]: 解析后的题目列表
        """
        try:
            start = response.find("[")
            end = response.rfind("]") + 1

            if start != -1 and end != 0:
                json_str = response[start:end]
                questions = json.loads(json_str)
            else:
                questions = []

            return questions
        except json.JSONDecodeError as e:
            logger.error(f"解析AI响应失败: {e}, response: {response}")
            return []

    async def save_consolidation_questions(
        self,
        questions: List[Dict[str, Any]],
        original_question_id: str = None,
        category: str = "other",
        generated_by: str = "deepseek"
    ) -> List[ConsolidationQuestion]:
        """
        保存生成的巩固题目到数据库

        Args:
            questions: 题目列表
            original_question_id: 原始题目ID
            category: 分类
            generated_by: 生成方式

        Returns:
            List[ConsolidationQuestion]: 保存的题目列表
        """
        saved_questions = []

        for q in questions:
            if q.get("question_type") == "choice" or "options" in q:
                question_type = "choice"
                options = q.get("options", [])
            else:
                question_type = "discussion"
                options = None

            saved = await ConsolidationQuestion.create(
                original_question_id=original_question_id,
                content=q.get("content", ""),
                question_type=question_type,
                options=options,
                answer=q.get("answer", ""),
                explanation=q.get("explanation", ""),
                difficulty=q.get("difficulty", "medium"),
                category=category,
                generated_by=generated_by
            )
            saved_questions.append(saved)
            logger.info(f"保存巩固题目: id={saved.id}")

        return saved_questions

    async def generate_and_save(
        self,
        original_question: Dict[str, Any],
        question_type: str = "choice",
        count: int = 3,
        difficulty: str = "same",
        generated_by: str = "deepseek"
    ) -> List[ConsolidationQuestion]:
        """
        生成并保存巩固题目

        Args:
            original_question: 原始题目
            question_type: 题目类型
            count: 生成数量
            difficulty: 难度
            generated_by: 生成方式

        Returns:
            List[ConsolidationQuestion]: 保存的巩固题目
        """
        questions = await self.generate_consolidation_questions(
            original_question=original_question,
            question_type=question_type,
            count=count,
            difficulty=difficulty
        )

        if not questions:
            return []

        saved = await self.save_consolidation_questions(
            questions=questions,
            original_question_id=original_question.get("id"),
            category=original_question.get("category", "other"),
            generated_by=generated_by
        )

        return saved

    @staticmethod
    async def get_consolidation_questions(
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[ConsolidationQuestion]:
        """
        获取巩固题目列表

        Args:
            category: 按分类筛选
            limit: 返回数量限制

        Returns:
            List[ConsolidationQuestion]: 题目列表
        """
        query = ConsolidationQuestion.all()

        if category:
            query = query.filter(category=category)

        questions = await query.order_by("-created_at").limit(limit)
        return questions

    @staticmethod
    async def get_question_by_id(question_id: int) -> Optional[ConsolidationQuestion]:
        """
        获取单个巩固题目

        Args:
            question_id: 题目ID

        Returns:
            ConsolidationQuestion or None: 题目或None
        """
        question = await ConsolidationQuestion.get_or_none(id=question_id)
        return question
