from tortoise.models import Model
from tortoise import fields
from datetime import datetime


class PracticeRecord(Model):
    """刷题记录表，记录用户刷过的题目"""
    id = fields.IntField(primary_key=True, generated=True)
    question_id = fields.CharField(max_length=64, description="题目ID")
    question_content = fields.TextField(description="题目内容")
    question_answer = fields.TextField(description="题目答案")
    category = fields.CharField(max_length=64, description="分类")
    difficulty = fields.CharField(max_length=32, description="难度")
    question_type = fields.CharField(max_length=32, description="题目类型")
    is_correct = fields.BooleanField(null=True, description="是否回答正确")
    user_answer = fields.TextField(null=True, description="用户答案")
    time_spent = fields.IntField(default=0, description="答题耗时(秒)")
    source = fields.CharField(max_length=255, default="", description="题目来源")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "practice_records"
        ordering = ["-created_at"]


class ConsolidationQuestion(Model):
    """巩固题目表，保存AI生成的巩固题目"""
    id = fields.IntField(primary_key=True, generated=True)
    original_question_id = fields.CharField(max_length=64, null=True, description="原始题目ID")
    content = fields.TextField(description="巩固题内容")
    question_type = fields.CharField(max_length=32, description="题目类型")
    options = fields.JSONField(null=True, description="选项列表")
    answer = fields.TextField(description="正确答案")
    explanation = fields.TextField(null=True, description="解析")
    difficulty = fields.CharField(max_length=32, default="medium", description="难度")
    category = fields.CharField(max_length=64, description="分类")
    generated_by = fields.CharField(max_length=255, description="生成方式")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "consolidation_questions"
        ordering = ["-created_at"]


class PracticeSession(Model):
    """刷题会话表，记录每次刷题练习"""
    id = fields.IntField(primary_key=True, generated=True)
    session_type = fields.CharField(max_length=32, default="practice", description="会话类型")
    category = fields.CharField(max_length=64, null=True, description="分类")
    total_questions = fields.IntField(default=0, description="总题目数")
    correct_count = fields.IntField(default=0, description="正确数")
    wrong_count = fields.IntField(default=0, description="错误数")
    skipped_count = fields.IntField(default=0, description="跳过数")
    time_spent = fields.IntField(default=0, description="总耗时(秒)")
    score = fields.FloatField(default=0.0, description="得分率")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "practice_sessions"
        ordering = ["-created_at"]
