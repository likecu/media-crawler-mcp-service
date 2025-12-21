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
    Neon 数据库连接类，用于连接 Neon PostgreSQL 并上传文件
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
        
        Raises:
            psycopg2.OperationalError: 连接数据库失败
        """
        try:
            # 从环境变量获取数据库连接信息
            database_url = os.getenv('NEON_DATABASE_URL')
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filename)
            );
            """
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ 文件表创建成功或已存在")
        except Exception as e:
            print(f"❌ 创建文件表失败: {e}")
            self.connection.rollback()
    
    def upload_file(self, file_path: str) -> bool:
        """
        上传文件到数据库
        
        Args:
            file_path: 文件路径
            
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
            
            # 插入或更新文件
            upsert_sql = """
            INSERT INTO files (filename, file_type, file_content, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (filename) DO UPDATE
            SET file_content = EXCLUDED.file_content,
                file_type = EXCLUDED.file_type,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            self.cursor.execute(upsert_sql, (filename, file_type, file_content))
            self.connection.commit()
            print(f"✅ 文件 '{filename}' 成功上传到 Neon 数据库")
            return True
        except Exception as e:
            print(f"❌ 上传文件 '{file_path}' 失败: {e}")
            self.connection.rollback()
            return False
    
    def upload_files_in_directory(self, directory_path: str, extensions: list = None) -> int:
        """
        上传目录中的所有指定扩展名的文件到数据库
        
        Args:
            directory_path: 目录路径
            extensions: 允许的文件扩展名列表，如 ["txt", "html"]
            
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
                if self.upload_file(file_path):
                    success_count += 1
        
        print(f"📊 成功上传 {success_count} 个文件到 Neon 数据库")
        return success_count
    
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
