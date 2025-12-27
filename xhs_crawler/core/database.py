#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接模块，用于连接 Neon PostgreSQL 并上传文件
"""

import os
import psycopg2
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# 加载 .env 文件中的配置
load_dotenv()

class NeonDatabase:
    """
    Neon 数据库连接类，用于连接 Neon PostgreSQL 并上传/下载文件
    支持从 VITE_NEON_AUTH_URL 提取数据库连接信息
    """
    
    def __init__(self):
        """
        初始化数据库连接
        """
        self.connection = None
        self.cursor = None
        self._connect()
        self._create_table_if_not_exists()
    
    def _connect(self):
        """
        建立数据库连接
        支持从 VITE_NEON_AUTH_URL 提取数据库连接信息
        
        Raises:
            psycopg2.OperationalError: 连接数据库失败
        """
        try:
            # 从环境变量获取数据库连接信息
            database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
            
            # 如果没有直接的 DATABASE_URL，尝试从 VITE_NEON_AUTH_URL 提取信息
            if not database_url:
                auth_url = os.getenv('VITE_NEON_AUTH_URL')
                if auth_url:
                    print(f"📋 从 VITE_NEON_AUTH_URL 提取数据库连接信息: {auth_url}")
                    # VITE_NEON_AUTH_URL 格式: https://<endpoint>.neonauth.<region>.aws.neon.tech/neondb/auth
                    # 提取 endpoint 和 region 信息，用于构建数据库连接
                    # 注意: 这只是演示如何从 auth url 提取信息，实际连接可能需要不同的格式
                    
            if database_url:
                # 使用 DATABASE_URL 格式连接
                self.connection = psycopg2.connect(database_url)
            else:
                # 使用单独的配置项连接
                self.connection = psycopg2.connect(
                    host=os.getenv('NEON_HOST'),
                    port=int(os.getenv('NEON_PORT', 5432)),
                    user=os.getenv('NEON_USERNAME'),
                    password=os.getenv('NEON_PASSWORD'),
                    database=os.getenv('NEON_DATABASE')
                )
            
            self.cursor = self.connection.cursor()
            print("✅ 成功连接到 Neon 数据库")
        except psycopg2.OperationalError as e:
            print(f"❌ 连接 Neon 数据库失败: {e}")
            raise
    
    def _create_table_if_not_exists(self):
        """
        创建文件表（如果不存在）
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法创建表")
            return
        
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_content BYTEA NOT NULL,
                hashid VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename),
                UNIQUE(hashid)
            );
            """
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ 文件表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建文件表失败: {e}")
            self.connection.rollback()
            
            try:
                print("🔧 尝试更新表结构，添加hashid字段...")
                self.cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'files' AND column_name = 'hashid'")
                if not self.cursor.fetchone():
                    self.cursor.execute("ALTER TABLE files ADD COLUMN hashid VARCHAR(255) NOT NULL DEFAULT 'default_hashid'")
                    self.cursor.execute("ALTER TABLE files ADD CONSTRAINT files_hashid_key UNIQUE (hashid)")
                    self.connection.commit()
                    print("✅ 成功添加hashid字段和唯一约束")
                else:
                    print("✅ hashid字段已存在")
            except Exception as alter_e:
                print(f"❌ 更新表结构失败: {alter_e}")
                self.connection.rollback()
        
        self._create_practice_table()
        self._create_question_table()
        self._create_leetcode_table()
    
    def _create_leetcode_table(self):
        """
        创建LeetCode刷题记录表（如果不存在）
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS leetcode_practice (
                id SERIAL PRIMARY KEY,
                problem_id INTEGER NOT NULL,
                problem_name VARCHAR(500) NOT NULL,
                problem_url VARCHAR(1000),
                difficulty VARCHAR(20),
                status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(problem_id)
            );
            """
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ LeetCode刷题记录表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建LeetCode刷题记录表失败: {e}")
            self.connection.rollback()
    
    def _create_practice_table(self):
        """
        创建刷题记录表（如果不存在）
        """
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS practice_records (
                id SERIAL PRIMARY KEY,
                keyword VARCHAR(200) NOT NULL,
                platform VARCHAR(50),
                note_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ 刷题记录表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建刷题记录表失败: {e}")
            self.connection.rollback()
    
    def _create_question_table(self):
        """
        创建面试题库表（如果不存在）
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
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ 面试题库表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建面试题库表失败: {e}")
            self.connection.rollback()
    
    def upload_file(self, file_path: str, hashid: str = None) -> bool:
        """
        上传文件到数据库

        Args:
            file_path: 文件路径
            hashid: 文件对应的hashid

        Returns:
            是否上传成功
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法上传文件")
            return False

        try:
            # 获取文件名和文件类型
            filename = os.path.basename(file_path)
            file_type = os.path.splitext(filename)[1][1:].lower()  # 去除点号

            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # 如果没有提供hashid，使用文件名作为默认hashid
            if not hashid:
                hashid = filename

            # 插入或更新文件
            upsert_sql = """
            INSERT INTO files (filename, file_type, file_content, hashid, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (filename) DO UPDATE
            SET file_content = EXCLUDED.file_content,
                file_type = EXCLUDED.file_type,
                hashid = EXCLUDED.hashid,
                updated_at = CURRENT_TIMESTAMP;
            """

            self.cursor.execute(upsert_sql, (filename, file_type, file_content, hashid))
            self.connection.commit()
            print(f"✅ 文件 '{filename}' 成功上传到 Neon 数据库")
            return True
        except Exception as e:
            print(f"❌ 上传文件 '{file_path}' 失败: {e}")
            self.connection.rollback()
            return False
    
    def upload_content(self, filename: str, content: str, file_type: str = "html", hashid: str = None) -> bool:
        """
        直接上传内容到数据库，无需先保存到文件
        
        Args:
            filename: 文件名
            content: 文件内容
            file_type: 文件类型
            hashid: 文件对应的hashid
            
        Returns:
            是否上传成功
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法上传内容")
            return False
        
        try:
            # 如果没有提供hashid，使用文件名作为默认hashid
            if not hashid:
                hashid = filename
            
            # 将内容转换为字节
            file_content = content.encode('utf-8')
            
            # 插入或更新文件
            upsert_sql = """
            INSERT INTO files (filename, file_type, file_content, hashid, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (filename) DO UPDATE
            SET file_content = EXCLUDED.file_content,
                file_type = EXCLUDED.file_type,
                hashid = EXCLUDED.hashid,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            self.cursor.execute(upsert_sql, (filename, file_type, file_content, hashid))
            self.connection.commit()
            print(f"✅ 内容 '{filename}' 成功上传到 Neon 数据库")
            return True
        except Exception as e:
            print(f"❌ 上传内容 '{filename}' 失败: {e}")
            self.connection.rollback()
            return False
    
    def upload_files_in_directory(self, directory_path: str, extensions: list = None, hashid_prefix: str = None) -> int:
        """
        上传目录中的所有指定扩展名的文件到数据库
        
        Args:
            directory_path: 目录路径
            extensions: 允许的文件扩展名列表，如 ["txt", "html"]
            hashid_prefix: hashid前缀，用于生成文件对应的hashid
            
        Returns:
            成功上传的文件数量
        """
        if not os.path.exists(directory_path):
            print(f"❌ 目录不存在: {directory_path}")
            return 0
        
        success_count = 0
        
        # 遍历目录中的所有文件
        for root, _, files in os.walk(directory_path):
            for file in files:
                # 检查文件扩展名
                file_ext = os.path.splitext(file)[1][1:].lower()
                if extensions and file_ext not in extensions:
                    continue
                
                file_path = os.path.join(root, file)
                # 生成hashid
                hashid = f"{hashid_prefix}_{file}" if hashid_prefix else file
                if self.upload_file(file_path, hashid):
                    success_count += 1
        
        print(f"📊 成功上传 {success_count} 个文件到 Neon 数据库")
        return success_count
    
    def get_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取指定文件名的文件
        
        Args:
            filename: 要获取的文件名
            
        Returns:
            文件信息字典，包含filename, file_type, file_content, hashid, created_at, updated_at
            如果文件不存在则返回None
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法获取文件")
            return None
        
        try:
            # 查询文件
            select_sql = """
            SELECT filename, file_type, file_content, hashid, created_at, updated_at
            FROM files
            WHERE filename = %s;
            """
            
            self.cursor.execute(select_sql, (filename,))
            result = self.cursor.fetchone()
            
            if result:
                filename, file_type, file_content, hashid, created_at, updated_at = result
                print(f"✅ 成功获取文件 '{filename}'")
                return {
                    'filename': filename,
                    'file_type': file_type,
                    'file_content': file_content,
                    'hashid': hashid,
                    'created_at': created_at,
                    'updated_at': updated_at
                }
            else:
                print(f"⚠️  文件 '{filename}' 不存在")
                return None
        except Exception as e:
            print(f"❌ 获取文件 '{filename}' 失败: {e}")
            return None
    
    def get_file_by_hashid(self, hashid: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取指定hashid的文件
        
        Args:
            hashid: 要获取的文件的hashid
            
        Returns:
            文件信息字典，包含filename, file_type, file_content, hashid, created_at, updated_at
            如果文件不存在则返回None
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法获取文件")
            return None
        
        try:
            # 查询文件
            select_sql = """
            SELECT filename, file_type, file_content, hashid, created_at, updated_at
            FROM files
            WHERE hashid = %s;
            """
            
            self.cursor.execute(select_sql, (hashid,))
            result = self.cursor.fetchone()
            
            if result:
                filename, file_type, file_content, hashid, created_at, updated_at = result
                print(f"✅ 成功获取hashid为 '{hashid}' 的文件")
                return {
                    'filename': filename,
                    'file_type': file_type,
                    'file_content': file_content,
                    'hashid': hashid,
                    'created_at': created_at,
                    'updated_at': updated_at
                }
            else:
                print(f"⚠️  hashid为 '{hashid}' 的文件不存在")
                return None
        except Exception as e:
            print(f"❌ 获取hashid为 '{hashid}' 的文件失败: {e}")
            return None
    
    def get_all_files(self) -> list:
        """
        获取数据库中的所有文件信息
        
        Returns:
            文件信息列表，每个元素是包含filename, file_type, hashid, created_at, updated_at的字典
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法获取文件列表")
            return []
        
        try:
            # 查询所有文件信息
            select_sql = """
            SELECT filename, file_type, hashid, created_at, updated_at
            FROM files
            ORDER BY created_at DESC;
            """
            
            self.cursor.execute(select_sql)
            results = self.cursor.fetchall()
            
            files = []
            for result in results:
                filename, file_type, hashid, created_at, updated_at = result
                files.append({
                    'filename': filename,
                    'file_type': file_type,
                    'hashid': hashid,
                    'created_at': created_at,
                    'updated_at': updated_at
                })
            
            print(f"✅ 成功获取 {len(files)} 个文件信息")
            return files
        except Exception as e:
            print(f"❌ 获取文件列表失败: {e}")
            return []
    
    def download_file(self, filename: str, output_path: str) -> bool:
        """
        从数据库下载文件并保存到指定路径
        
        Args:
            filename: 要下载的文件名
            output_path: 输出路径（目录或完整文件路径）
            
        Returns:
            是否下载成功
        """
        file_info = self.get_file(filename)
        if not file_info:
            return False
        
        try:
            # 确定输出文件路径
            if os.path.isdir(output_path):
                # 如果是目录，使用文件名作为输出文件名
                output_file_path = os.path.join(output_path, filename)
            else:
                # 如果是文件路径，直接使用
                output_file_path = output_path
            
            # 写入文件
            with open(output_file_path, 'wb') as f:
                f.write(file_info['file_content'])
            
            print(f"✅ 文件 '{filename}' 成功下载到 '{output_file_path}'")
            return True
        except Exception as e:
            print(f"❌ 下载文件 '{filename}' 失败: {e}")
            return False
    
    def save_practice_record(self, keyword: str, platform: str = "小红书", note_count: int = 0) -> bool:
        """
        保存刷题记录
        
        Args:
            keyword: 搜索关键词
            platform: 平台名称
            note_count: 获取的笔记数量
            
        Returns:
            是否保存成功
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法保存刷题记录")
            return False
        
        try:
            upsert_sql = """
            INSERT INTO practice_records (keyword, platform, note_count, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (keyword) DO UPDATE
            SET note_count = EXCLUDED.note_count,
                platform = EXCLUDED.platform,
                updated_at = CURRENT_TIMESTAMP;
            """
            self.cursor.execute(upsert_sql, (keyword, platform, note_count))
            self.connection.commit()
            print(f"✅ 刷题记录 '{keyword}' 已保存到数据库")
            return True
        except Exception as e:
            print(f"❌ 保存刷题记录 '{keyword}' 失败: {e}")
            self.connection.rollback()
            return False
    
    def save_interview_question(self, question_data: Dict[str, Any]) -> bool:
        """
        保存面试题目到数据库
        
        Args:
            question_data: 题目数据字典，包含question_id, content, answer, category等字段
            
        Returns:
            是否保存成功
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法保存面试题目")
            return False
        
        try:
            upsert_sql = """
            INSERT INTO interview_questions (
                question_id, content, answer, category, difficulty, 
                question_type, explanation, source, source_url, note_id, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (question_id) DO UPDATE
            SET content = EXCLUDED.content,
                answer = EXCLUDED.answer,
                category = EXCLUDED.category,
                difficulty = EXCLUDED.difficulty,
                question_type = EXCLUDED.question_type,
                explanation = EXCLUDED.explanation,
                source = EXCLUDED.source,
                source_url = EXCLUDED.source_url,
                note_id = EXCLUDED.note_id,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            self.cursor.execute(upsert_sql, (
                question_data.get('question_id'),
                question_data.get('content'),
                question_data.get('answer'),
                question_data.get('category'),
                question_data.get('difficulty'),
                question_data.get('question_type'),
                question_data.get('explanation'),
                question_data.get('source'),
                question_data.get('source_url'),
                question_data.get('note_id')
            ))
            self.connection.commit()
            print(f"✅ 面试题 '{question_data.get('question_id')}' 已保存到数据库")
            return True
        except Exception as e:
            print(f"❌ 保存面试题 '{question_data.get('question_id')}' 失败: {e}")
            self.connection.rollback()
            return False
    
    def save_leetcode_problem(self, problem_id: int, problem_name: str, problem_url: str = None, 
                              difficulty: str = None, status: str = "pending", notes: str = None) -> bool:
        """
        保存LeetCode题目到刷题记录
        
        Args:
            problem_id: 题目编号
            problem_name: 题目名称
            problem_url: 题目链接
            difficulty: 难度
            status: 状态
            notes: 备注
            
        Returns:
            是否保存成功
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法保存LeetCode题目")
            return False
        
        try:
            upsert_sql = """
            INSERT INTO leetcode_practice (problem_id, problem_name, problem_url, difficulty, status, notes, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (problem_id) DO UPDATE
            SET problem_name = EXCLUDED.problem_name,
                problem_url = EXCLUDED.problem_url,
                difficulty = EXCLUDED.difficulty,
                status = EXCLUDED.status,
                notes = EXCLUDED.notes,
                updated_at = CURRENT_TIMESTAMP;
            """
            self.cursor.execute(upsert_sql, (problem_id, problem_name, problem_url, difficulty, status, notes))
            self.connection.commit()
            print(f"✅ LeetCode题目 #{problem_id} {problem_name} 已保存到数据库")
            return True
        except Exception as e:
            print(f"❌ 保存LeetCode题目 #{problem_id} 失败: {e}")
            self.connection.rollback()
            return False
    
    def get_practice_records(self) -> list:
        """
        获取所有刷题记录
        
        Returns:
            刷题记录列表
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法获取刷题记录")
            return []
        
        try:
            select_sql = """
            SELECT id, keyword, platform, note_count, created_at, updated_at
            FROM practice_records
            ORDER BY updated_at DESC;
            """
            self.cursor.execute(select_sql)
            results = self.cursor.fetchall()
            
            records = []
            for result in results:
                records.append({
                    'id': result[0],
                    'keyword': result[1],
                    'platform': result[2],
                    'note_count': result[3],
                    'created_at': result[4],
                    'updated_at': result[5]
                })
            
            print(f"✅ 成功获取 {len(records)} 条刷题记录")
            return records
        except Exception as e:
            print(f"❌ 获取刷题记录失败: {e}")
            return []
    
    def get_interview_questions(self, category: str = None, limit: int = 100) -> list:
        """
        获取面试题目
        
        Args:
            category: 分类筛选
            limit: 返回数量限制
            
        Returns:
            面试题目列表
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法获取面试题目")
            return []
        
        try:
            if category:
                select_sql = """
                SELECT id, question_id, content, answer, category, difficulty, question_type, 
                       explanation, source, source_url, note_id, created_at, updated_at
                FROM interview_questions
                WHERE category = %s
                ORDER BY created_at DESC
                LIMIT %s;
                """
                self.cursor.execute(select_sql, (category, limit))
            else:
                select_sql = """
                SELECT id, question_id, content, answer, category, difficulty, question_type, 
                       explanation, source, source_url, note_id, created_at, updated_at
                FROM interview_questions
                ORDER BY created_at DESC
                LIMIT %s;
                """
                self.cursor.execute(select_sql, (limit,))
            
            results = self.cursor.fetchall()
            
            questions = []
            for result in results:
                questions.append({
                    'id': result[0],
                    'question_id': result[1],
                    'content': result[2],
                    'answer': result[3],
                    'category': result[4],
                    'difficulty': result[5],
                    'question_type': result[6],
                    'explanation': result[7],
                    'source': result[8],
                    'source_url': result[9],
                    'note_id': result[10],
                    'created_at': result[11],
                    'updated_at': result[12]
                })
            
            print(f"✅ 成功获取 {len(questions)} 道面试题目")
            return questions
        except Exception as e:
            print(f"❌ 获取面试题目失败: {e}")
            return []
    
    def get_leetcode_practice(self, status: str = None) -> list:
        """
        获取LeetCode刷题记录
        
        Args:
            status: 状态筛选
            
        Returns:
            LeetCode刷题记录列表
        """
        if not self.connection or not self.cursor:
            print("❌ 数据库未连接，无法获取LeetCode刷题记录")
            return []
        
        try:
            if status:
                select_sql = """
                SELECT id, problem_id, problem_name, problem_url, difficulty, status, notes, created_at, updated_at
                FROM leetcode_practice
                WHERE status = %s
                ORDER BY problem_id ASC;
                """
                self.cursor.execute(select_sql, (status,))
            else:
                select_sql = """
                SELECT id, problem_id, problem_name, problem_url, difficulty, status, notes, created_at, updated_at
                FROM leetcode_practice
                ORDER BY problem_id ASC;
                """
                self.cursor.execute(select_sql)
            
            results = self.cursor.fetchall()
            
            problems = []
            for result in results:
                problems.append({
                    'id': result[0],
                    'problem_id': result[1],
                    'problem_name': result[2],
                    'problem_url': result[3],
                    'difficulty': result[4],
                    'status': result[5],
                    'notes': result[6],
                    'created_at': result[7],
                    'updated_at': result[8]
                })
            
            print(f"✅ 成功获取 {len(problems)} 条LeetCode刷题记录")
            return problems
        except Exception as e:
            print(f"❌ 获取LeetCode刷题记录失败: {e}")
            return []
    

    
    def close(self):
        """
        关闭数据库连接
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✅ 数据库连接已关闭")
    
    def __enter__(self):
        """
        上下文管理器进入方法
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器退出方法，自动关闭连接
        """
        self.close()


def get_neon_database() -> Optional[NeonDatabase]:
    """
    获取 Neon 数据库实例
    
    Returns:
        NeonDatabase 实例，如果连接失败则返回 None
    """
    try:
        return NeonDatabase()
    except Exception as e:
        print(f"⚠️  创建 Neon 数据库实例失败: {e}")
        return None
