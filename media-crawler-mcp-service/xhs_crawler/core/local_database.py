#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 PostgreSQL 数据库连接模块
用于连接 media-crawler-mcp-service 中的 PostgreSQL 容器
支持连接池管理和高效的数据库操作
"""

import os
import psycopg2
from psycopg2 import pool, sql
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class PoolConfig:
    """数据库连接池配置"""
    minconn: int = 1
    maxconn: int = 10
    host: str = "localhost"
    port: int = 5432
    database: str = "mcp_tools_db"
    user: str = "postgres"
    password: str = "password"
    connect_timeout: int = 10


class LocalPostgreSQLDatabase:
    """
    本地 PostgreSQL 数据库连接类
    使用连接池管理，支持连接失败自动重连
    """
    
    _instance = None
    _lock = threading.Lock()
    _pool: Optional[pool.ThreadedConnectionPool] = None
    
    def __new__(cls, config: Optional[PoolConfig] = None):
        """
        单例模式确保全局唯一数据库连接池
        
        Args:
            config: 连接池配置
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[PoolConfig] = None):
        """
        初始化数据库连接池
        
        Args:
            config: 连接池配置
        """
        if self._initialized:
            return
        
        if config is None:
            config = PoolConfig(
                host=os.getenv("DB__HOST", os.getenv("DB_HOST", "localhost")),
                port=int(os.getenv("DB__PORT", os.getenv("DB_PORT", "5432"))),
                database=os.getenv("DB__NAME", os.getenv("DB_NAME", "mcp_tools_db")),
                user=os.getenv("DB__USER", os.getenv("DB_USER", "postgres")),
                password=os.getenv("DB__PASSWORD", os.getenv("DB_PASSWORD", "password")),
                minconn=1,
                maxconn=10
            )
        
        self._config = config
        self._init_pool()
        self._create_tables()
        self._initialized = True
    
    def _init_pool(self):
        """
        初始化数据库连接池
        
        Raises:
            psycopg2.OperationalError: 连接数据库失败
        """
        try:
            if LocalPostgreSQLDatabase._pool is None:
                LocalPostgreSQLDatabase._pool = pool.ThreadedConnectionPool(
                    self._config.minconn,
                    self._config.maxconn,
                    host=self._config.host,
                    port=self._config.port,
                    database=self._config.database,
                    user=self._config.user,
                    password=self._config.password,
                    connect_timeout=self._config.connect_timeout
                )
            conn = self._pool.getconn()
            self.cursor = conn.cursor()
            self._pool.putconn(conn)
            print(f"✅ 数据库连接池初始化成功: {self._config.host}:{self._config.port}/{self._config.database}")
        except psycopg2.OperationalError as e:
            print(f"❌ 连接本地 PostgreSQL 数据库失败: {e}")
            raise
    
    def _get_connection(self) -> psycopg2.extensions.connection:
        """
        获取数据库连接
        
        Returns:
            psycopg2.extensions.connection: 数据库连接对象
        """
        if LocalPostgreSQLDatabase._pool is None:
            self._init_pool()
        return LocalPostgreSQLDatabase._pool.getconn()
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            psycopg2.extensions.connection: 数据库连接对象
        """
        conn = self._get_connection()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)
    
    def _create_tables(self):
        """
        创建所有需要的表
        """
        self._create_leetcode_practice_table()
        self._create_practice_records_table()
        self._create_interview_questions_table()
        self._create_content_fingerprints_table()
    
    def _create_content_fingerprints_table(self):
        """
        创建内容指纹表（如果不存在）
        
        Table: content_fingerprints
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS content_fingerprints (
                id SERIAL PRIMARY KEY,
                note_id VARCHAR(100) NOT NULL UNIQUE,
                title VARCHAR(500),
                content_hash VARCHAR(64) NOT NULL,
                title_hash VARCHAR(64) NOT NULL,
                combined_hash VARCHAR(64) NOT NULL,
                title_preview VARCHAR(500),
                content_preview TEXT,
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_duplicate BOOLEAN DEFAULT FALSE,
                duplicate_type VARCHAR(20),
                similar_to TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_content_hash ON content_fingerprints(content_hash);
            CREATE INDEX IF NOT EXISTS idx_combined_hash ON content_fingerprints(combined_hash);
            CREATE INDEX IF NOT EXISTS idx_created_at ON content_fingerprints(created_at);
            CREATE INDEX IF NOT EXISTS idx_is_duplicate ON content_fingerprints(is_duplicate);
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
            print("✅ 内容指纹表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建内容指纹表失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            raise
    
    def _create_leetcode_practice_table(self):
        """
        创建刷题记录表（如果不存在）
        
        Table: leetcode_practice
        
        Raises:
            Exception: 创建表失败
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS leetcode_practice (
                id SERIAL PRIMARY KEY,
                note_id VARCHAR(100) NOT NULL UNIQUE,
                title VARCHAR(500),
                content TEXT,
                difficulty VARCHAR(20),
                question_id VARCHAR(50),
                question_url VARCHAR(1000),
                category VARCHAR(100),
                tags TEXT,
                like_count INTEGER DEFAULT 0,
                collect_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                share_count INTEGER DEFAULT 0,
                author VARCHAR(200),
                author_id VARCHAR(100),
                image_urls TEXT,
                video_url VARCHAR(1000),
                source_url VARCHAR(1000),
                source VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
            print("✅ 练习记录表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建练习记录表失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            raise
    
    def _create_practice_records_table(self):
        """
        创建练习记录表（如果不存在）
        
        Table: practice_records
        
        Raises:
            Exception: 创建表失败
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS practice_records (
                id SERIAL PRIMARY KEY,
                note_id VARCHAR(100) NOT NULL,
                question_id VARCHAR(50) NOT NULL,
                question_name VARCHAR(200),
                difficulty VARCHAR(20),
                status VARCHAR(50),
                solution_content TEXT,
                time_complexity VARCHAR(100),
                space_complexity VARCHAR(100),
                language VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(note_id, question_id)
            );
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
            print("✅ 练习记录表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建练习记录表失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            raise
    
    def _create_interview_questions_table(self):
        """
        创建面试题库表（如果不存在）
        
        Table: interview_questions
        
        Raises:
            Exception: 创建表失败
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS interview_questions (
                id SERIAL PRIMARY KEY,
                question_id VARCHAR(50) NOT NULL UNIQUE,
                content TEXT NOT NULL,
                answer TEXT,
                category VARCHAR(100),
                difficulty VARCHAR(20),
                question_type VARCHAR(50),
                explanation TEXT,
                source VARCHAR(500),
                source_url VARCHAR(1000),
                note_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
            print("✅ 面试题库表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建面试题库表失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            raise
    
    def insert_leetcode_practice(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_id: Optional[str] = None,
        question_url: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        like_count: int = 0,
        collect_count: int = 0,
        comment_count: int = 0,
        share_count: int = 0,
        author: Optional[str] = None,
        author_id: Optional[str] = None,
        image_urls: Optional[str] = None,
        video_url: Optional[str] = None,
        source_url: Optional[str] = None,
        source: Optional[str] = None
    ) -> bool:
        """
        插入或更新刷题记录
        
        Args:
            note_id: 笔记ID
            title: 标题
            content: 内容
            difficulty: 难度
            question_id: 题目ID
            question_url: 题目链接
            category: 分类
            tags: 标签
            like_count: 点赞数
            collect_count: 收藏数
            comment_count: 评论数
            share_count: 分享数
            author: 作者
            author_id: 作者ID
            image_urls: 图片URL列表
            video_url: 视频链接
            source_url: 源链接
            source: 来源
            
        Returns:
            bool: 插入成功返回 True，失败返回 False
        """
        try:
            insert_sql = """
            INSERT INTO leetcode_practice (
                note_id, title, content, difficulty, question_id, question_url,
                category, tags, like_count, collect_count, comment_count, share_count,
                author, author_id, image_urls, video_url, source_url, source
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (note_id) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                difficulty = EXCLUDED.difficulty,
                question_id = EXCLUDED.question_id,
                question_url = EXCLUDED.question_url,
                category = EXCLUDED.category,
                tags = EXCLUDED.tags,
                like_count = EXCLUDED.like_count,
                collect_count = EXCLUDED.collect_count,
                comment_count = EXCLUDED.comment_count,
                share_count = EXCLUDED.share_count,
                author = EXCLUDED.author,
                author_id = EXCLUDED.author_id,
                image_urls = EXCLUDED.image_urls,
                video_url = EXCLUDED.video_url,
                source_url = EXCLUDED.source_url,
                source = EXCLUDED.source,
                updated_at = CURRENT_TIMESTAMP
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, (
                    note_id, title, content, difficulty, question_id, question_url,
                    category, tags, like_count, collect_count, comment_count, share_count,
                    author, author_id, image_urls, video_url, source_url, source
                ))
                conn.commit()
            print(f"✅ 刷题记录插入/更新成功: note_id={note_id}")
            return True
        except Exception as e:
            print(f"❌ 插入刷题记录失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            return False
    
    def insert_practice_record(
        self,
        note_id: str,
        question_id: str,
        question_name: Optional[str] = None,
        difficulty: Optional[str] = None,
        status: Optional[str] = None,
        solution_content: Optional[str] = None,
        time_complexity: Optional[str] = None,
        space_complexity: Optional[str] = None,
        language: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        插入或更新练习记录
        
        Args:
            note_id: 笔记ID
            question_id: 题目ID
            question_name: 题目名称
            difficulty: 难度
            status: 状态
            solution_content: 解题内容
            time_complexity: 时间复杂度
            space_complexity: 空间复杂度
            language: 编程语言
            notes: 备注
            
        Returns:
            bool: 插入成功返回 True，失败返回 False
        """
        try:
            insert_sql = """
            INSERT INTO practice_records (
                note_id, question_id, question_name, difficulty, status,
                solution_content, time_complexity, space_complexity, language, notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (note_id, question_id) DO UPDATE SET
                question_name = EXCLUDED.question_name,
                difficulty = EXCLUDED.difficulty,
                status = EXCLUDED.status,
                solution_content = EXCLUDED.solution_content,
                time_complexity = EXCLUDED.time_complexity,
                space_complexity = EXCLUDED.space_complexity,
                language = EXCLUDED.language,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, (
                    note_id, question_id, question_name, difficulty, status,
                    solution_content, time_complexity, space_complexity, language, notes
                ))
                conn.commit()
            print(f"✅ 练习记录插入/更新成功: note_id={note_id}, question_id={question_id}")
            return True
        except Exception as e:
            print(f"❌ 插入练习记录失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            return False
    
    def insert_interview_question(
        self,
        question_id: str,
        content: str,
        answer: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        explanation: Optional[str] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None,
        note_id: Optional[str] = None
    ) -> bool:
        """
        插入或更新面试题
        
        Args:
            question_id: 题目ID
            content: 题目内容
            answer: 答案
            category: 分类
            difficulty: 难度
            question_type: 题目类型
            explanation: 解析
            source: 来源
            source_url: 来源链接
            note_id: 笔记ID
            
        Returns:
            bool: 插入成功返回 True，失败返回 False
        """
        try:
            insert_sql = """
            INSERT INTO interview_questions (
                question_id, content, answer, category, difficulty,
                question_type, explanation, source, source_url, note_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (question_id) DO UPDATE SET
                content = EXCLUDED.content,
                answer = EXCLUDED.answer,
                category = EXCLUDED.category,
                difficulty = EXCLUDED.difficulty,
                question_type = EXCLUDED.question_type,
                explanation = EXCLUDED.explanation,
                source = EXCLUDED.source,
                source_url = EXCLUDED.source_url,
                note_id = EXCLUDED.note_id,
                updated_at = CURRENT_TIMESTAMP
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, (
                    question_id, content, answer, category, difficulty,
                    question_type, explanation, source, source_url, note_id
                ))
                conn.commit()
            print(f"✅ 面试题插入/更新成功: question_id={question_id}")
            return True
        except Exception as e:
            print(f"❌ 插入面试题失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            return False
    
    def query_leetcode_practice(
        self,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询刷题记录
        
        Args:
            difficulty: 难度筛选
            category: 分类筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[Dict]: 刷题记录列表
        """
        try:
            query_sql = """
            SELECT * FROM leetcode_practice
            WHERE (%s IS NULL OR difficulty = %s)
            AND (%s IS NULL OR category = %s)
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_sql, (difficulty, difficulty, category, category, limit, offset))
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            print(f"❌ 查询刷题记录失败: {e}")
            return []
    
    def query_interview_questions(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询面试题
        
        Args:
            category: 分类筛选
            difficulty: 难度筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[Dict]: 面试题列表
        """
        try:
            query_sql = """
            SELECT * FROM interview_questions
            WHERE (%s IS NULL OR category = %s)
            AND (%s IS NULL OR difficulty = %s)
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """
            self.cursor.execute(query_sql, (category, category, difficulty, difficulty, limit, offset))
            columns = [desc[0] for desc in self.cursor.description]
            results = []
            for row in self.cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            print(f"❌ 查询面试题失败: {e}")
            return []
    
    def delete_leetcode_practice(self, note_id: str) -> bool:
        """
        删除刷题记录
        
        Args:
            note_id: 笔记ID
            
        Returns:
            bool: 删除成功返回 True，失败返回 False
        """
        try:
            delete_sql = "DELETE FROM leetcode_practice WHERE note_id = %s"
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(delete_sql, (note_id,))
                conn.commit()
            print(f"✅ 刷题记录删除成功: note_id={note_id}")
            return True
        except Exception as e:
            print(f"❌ 删除刷题记录失败: {e}")
            with self.get_connection() as conn:
                conn.rollback()
            return False
    
    def close(self):
        """
        关闭数据库连接池
        """
        if LocalPostgreSQLDatabase._pool:
            LocalPostgreSQLDatabase._pool.closeall()
            LocalPostgreSQLDatabase._pool = None
        print("✅ 数据库连接池已关闭")
    
    def __enter__(self):
        """
        支持上下文管理器
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器时自动关闭连接
        """
        self.close()
        return False


def get_local_database(
    host: str = "localhost",
    port: int = 5432,
    database: str = "mcp_tools_db",
    user: str = "postgres",
    password: str = "password"
) -> LocalPostgreSQLDatabase:
    """
    获取本地 PostgreSQL 数据库连接实例
    
    Args:
        host: 数据库主机地址
        port: 数据库端口
        database: 数据库名称
        user: 数据库用户名
        password: 数据库密码
        
    Returns:
        LocalPostgreSQLDatabase: 数据库连接实例
    """
    return LocalPostgreSQLDatabase(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
