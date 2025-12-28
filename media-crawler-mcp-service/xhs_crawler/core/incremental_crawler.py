#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量爬取与智能去重模块
实现内容指纹生成、相似度检测、增量爬取控制
"""

import os
import sys
import hashlib
import json
import time
import re
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from xhs_crawler.core.local_database import LocalPostgreSQLDatabase


@dataclass
class ContentFingerprint:
    """内容指纹"""
    note_id: str
    content_hash: str
    title_hash: str
    combined_hash: str
    title: str
    content_preview: str
    created_at: datetime = field(default_factory=datetime.now)
    is_duplicate: bool = False
    similar_to: List[str] = field(default_factory=list)


@dataclass
class DuplicateCheckResult:
    """去重检测结果"""
    is_duplicate: bool
    duplicate_type: str  # exact, similar, new
    duplicate_note_ids: List[str]
    similarity_score: Optional[float]
    fingerprint: ContentFingerprint


class IncrementalCrawler:
    """
    增量爬取控制器
    管理爬取状态，实现增量更新和智能去重
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化增量爬取控制器"""
        if self._initialized:
            return
        
        self.db = None
        self.content_fingerprints: Dict[str, ContentFingerprint] = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words=None,
            max_features=1000,
            ngram_range=(1, 2)
        )
        self.content_vectors = None
        self.similarity_threshold = 0.85
        self._initialized = True
        self._lock = threading.Lock()
    
    def _get_database(self) -> LocalPostgreSQLDatabase:
        """获取数据库连接"""
        if self.db is None:
            self.db = LocalPostgreSQLDatabase()
        return self.db
    
    def _generate_content_hash(self, content: str) -> str:
        """
        生成内容哈希
        
        Args:
            content: 原始内容
            
        Returns:
            内容哈希值（MD5）
        """
        normalized = re.sub(r'\s+', ' ', content.strip())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _generate_title_hash(self, title: str) -> str:
        """
        生成标题哈希
        
        Args:
            title: 标题
            
        Returns:
            标题哈希值（MD5）
        """
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', title.strip())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _generate_combined_hash(self, title: str, content: str) -> str:
        """
        生成标题+内容组合哈希
        
        Args:
            title: 标题
            content: 内容
            
        Returns:
            组合哈希值（MD5）
        """
        combined = f"{title[:100]}|{content[:500]}".encode('utf-8')
        return hashlib.md5(combined).hexdigest()
    
    def _create_fingerprint(
        self,
        note_id: str,
        title: str,
        content: str
    ) -> ContentFingerprint:
        """
        创建内容指纹
        
        Args:
            note_id: 笔记ID
            title: 标题
            content: 内容
            
        Returns:
            内容指纹
        """
        return ContentFingerprint(
            note_id=note_id,
            content_hash=self._generate_content_hash(content),
            title_hash=self._generate_title_hash(title),
            combined_hash=self._generate_combined_hash(title, content),
            title=title[:100],
            content_preview=content[:200] if content else ""
        )
    
    def check_duplicate(
        self,
        note_id: str,
        title: str,
        content: str,
        check_exact: bool = True,
        check_similar: bool = True
    ) -> DuplicateCheckResult:
        """
        检测内容是否重复
        
        Args:
            note_id: 笔记ID
            title: 标题
            content: 内容
            check_exact: 是否检测完全重复
            check_similar: 是否检测相似内容
            
        Returns:
            去重检测结果
        """
        with self._lock:
            new_fingerprint = self._create_fingerprint(note_id, title, content)
            duplicate_note_ids = []
            similarity_score = None
            
            if check_exact:
                for fp in self.content_fingerprints.values():
                    if fp.combined_hash == new_fingerprint.combined_hash:
                        duplicate_note_ids.append(fp.note_id)
                        new_fingerprint.is_duplicate = True
                        return DuplicateCheckResult(
                            is_duplicate=True,
                            duplicate_type="exact",
                            duplicate_note_ids=duplicate_note_ids,
                            similarity_score=1.0,
                            fingerprint=new_fingerprint
                        )
                
                for fp in self.content_fingerprints.values():
                    if fp.content_hash == new_fingerprint.content_hash:
                        duplicate_note_ids.append(fp.note_id)
                        new_fingerprint.is_duplicate = True
                        return DuplicateCheckResult(
                            is_duplicate=True,
                            duplicate_type="exact",
                            duplicate_note_ids=duplicate_note_ids,
                            similarity_score=1.0,
                            fingerprint=new_fingerprint
                        )
            
            if check_similar and self.content_vectors is not None:
                new_vector = self.tfidf_vectorizer.transform([title + " " + content])
                similarities = cosine_similarity(new_vector, self.content_vectors)[0]
                max_similarity = float(np.max(similarities))
                most_similar_idx = int(np.argmax(similarities))
                
                if max_similarity >= self.similarity_threshold:
                    similar_note_ids = [
                        list(self.content_fingerprints.keys())[i]
                        for i in range(len(similarities))
                        if similarities[i] >= self.similarity_threshold
                    ]
                    duplicate_note_ids.extend(similar_note_ids)
                    new_fingerprint.is_duplicate = True
                    new_fingerprint.similar_to = similar_note_ids
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        duplicate_type="similar",
                        duplicate_note_ids=list(set(duplicate_note_ids)),
                        similarity_score=max_similarity,
                        fingerprint=new_fingerprint
                    )
                
                similarity_score = max_similarity
            
            return DuplicateCheckResult(
                is_duplicate=False,
                duplicate_type="new",
                duplicate_note_ids=duplicate_note_ids,
                similarity_score=similarity_score,
                fingerprint=new_fingerprint
            )
    
    def add_content(
        self,
        note_id: str,
        title: str,
        content: str
    ) -> ContentFingerprint:
        """
        添加新内容到指纹库
        
        Args:
            note_id: 笔记ID
            title: 标题
            content: 内容
            
        Returns:
            创建的内容指纹
        """
        with self._lock:
            fingerprint = self._create_fingerprint(note_id, title, content)
            self.content_fingerprints[note_id] = fingerprint
            return fingerprint
    
    def load_existing_fingerprints(
        self,
        source: str = None,
        days: int = 30
    ) -> int:
        """
        从数据库加载现有内容指纹
        
        Args:
            source: 数据来源（可选）
            days: 加载最近几天的数据
            
        Returns:
            加载的指纹数量
        """
        try:
            db = self._get_database()
            
            query = """
            SELECT note_id, title, content, created_at
            FROM leetcode_practice
            WHERE created_at >= %s
            """
            cutoff_date = datetime.now() - timedelta(days=days)
            params = [cutoff_date]
            
            if source:
                query += " AND source = %s"
                params.append(source)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            for row in rows:
                note_id, title, content, created_at = row
                fingerprint = self._create_fingerprint(note_id, title, content or "")
                fingerprint.created_at = created_at
                self.content_fingerprints[note_id] = fingerprint
            
            self._rebuild_tfidf_vectors()
            
            print(f"✅ 加载了 {len(self.content_fingerprints)} 个内容指纹")
            return len(self.content_fingerprints)
            
        except Exception as e:
            print(f"❌ 加载内容指纹失败: {e}")
            return 0
    
    def save_fingerprint(
        self,
        fingerprint: ContentFingerprint,
        source: str = "default"
    ) -> bool:
        """
        保存内容指纹到数据库
        
        Args:
            fingerprint: 内容指纹对象
            source: 数据来源标识
            
        Returns:
            是否保存成功
        """
        try:
            db = self._get_database()
            
            query = """
            INSERT INTO content_fingerprints 
            (note_id, title, content_hash, title_hash, combined_hash, 
             title_preview, content_preview, source, created_at, is_duplicate, similar_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (note_id) DO UPDATE SET
                title = EXCLUDED.title,
                content_hash = EXCLUDED.content_hash,
                title_hash = EXCLUDED.title_hash,
                combined_hash = EXCLUDED.combined_hash,
                title_preview = EXCLUDED.title_preview,
                content_preview = EXCLUDED.content_preview,
                source = EXCLUDED.source,
                created_at = EXCLUDED.created_at,
                is_duplicate = EXCLUDED.is_duplicate,
                similar_to = EXCLUDED.similar_to,
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = [
                fingerprint.note_id,
                fingerprint.title,
                fingerprint.content_hash,
                fingerprint.title_hash,
                fingerprint.combined_hash,
                fingerprint.title[:200] if fingerprint.title else "",
                fingerprint.content_preview,
                source,
                fingerprint.created_at,
                fingerprint.is_duplicate,
                json.dumps(fingerprint.similar_to) if fingerprint.similar_to else None
            ]
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ 保存内容指纹失败: {e}")
            return False
    
    def save_fingerprints_batch(
        self,
        fingerprints: List[ContentFingerprint],
        source: str = "default"
    ) -> int:
        """
        批量保存内容指纹到数据库
        
        Args:
            fingerprints: 内容指纹列表
            source: 数据来源标识
            
        Returns:
            成功保存的数量
        """
        if not fingerprints:
            return 0
        
        try:
            db = self._get_database()
            
            query = """
            INSERT INTO content_fingerprints 
            (note_id, title, content_hash, title_hash, combined_hash, 
             title_preview, content_preview, source, created_at, is_duplicate, similar_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (note_id) DO UPDATE SET
                title = EXCLUDED.title,
                content_hash = EXCLUDED.content_hash,
                title_hash = EXCLUDED.title_hash,
                combined_hash = EXCLUDED.combined_hash,
                title_preview = EXCLUDED.title_preview,
                content_preview = EXCLUDED.content_preview,
                source = EXCLUDED.source,
                is_duplicate = EXCLUDED.is_duplicate,
                similar_to = EXCLUDED.similar_to,
                updated_at = CURRENT_TIMESTAMP
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                for fingerprint in fingerprints:
                    params = [
                        fingerprint.note_id,
                        fingerprint.title,
                        fingerprint.content_hash,
                        fingerprint.title_hash,
                        fingerprint.combined_hash,
                        fingerprint.title[:200] if fingerprint.title else "",
                        fingerprint.content_preview,
                        source,
                        fingerprint.created_at,
                        fingerprint.is_duplicate,
                        json.dumps(fingerprint.similar_to) if fingerprint.similar_to else None
                    ]
                    cursor.execute(query, params)
                conn.commit()
            
            saved_count = len(fingerprints)
            print(f"✅ 批量保存了 {saved_count} 个内容指纹")
            return saved_count
            
        except Exception as e:
            print(f"❌ 批量保存内容指纹失败: {e}")
            try:
                with db.get_connection() as conn:
                    conn.rollback()
            except:
                pass
            return 0
    
    def mark_duplicate_in_db(
        self,
        note_id: str,
        duplicate_of: List[str],
        duplicate_type: str = "similar"
    ) -> bool:
        """
        在数据库中标记内容为重复
        
        Args:
            note_id: 笔记ID
            duplicate_of: 重复内容的ID列表
            duplicate_type: 重复类型
            
        Returns:
            是否标记成功
        """
        try:
            db = self._get_database()
            
            query = """
            UPDATE content_fingerprints 
            SET is_duplicate = TRUE, 
                duplicate_type = %s,
                similar_to = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE note_id = %s
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (duplicate_type, json.dumps(duplicate_of), note_id))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ 标记重复内容失败: {e}")
            return False
    
    def get_duplicate_stats(self, source: str = None) -> Dict[str, Any]:
        """
        获取数据库中的重复统计信息
        
        Args:
            source: 数据来源（可选）
            
        Returns:
            统计信息字典
        """
        try:
            db = self._get_database()
            
            query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) as duplicates,
                COUNT(DISTINCT source) as source_count
            FROM content_fingerprints
            """
            params = []
            
            if source:
                query += " WHERE source = %s"
                params.append(source)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                row = cursor.fetchone()
            
            return {
                "total_fingerprints": row[0] or 0,
                "duplicate_count": row[1] or 0,
                "unique_count": (row[0] or 0) - (row[1] or 0),
                "source_count": row[2] or 0
            }
            
        except Exception as e:
            print(f"❌ 获取重复统计信息失败: {e}")
            return {"total_fingerprints": 0, "duplicate_count": 0, "unique_count": 0, "source_count": 0}
    
    def cleanup_old_fingerprints(self, days: int = 90) -> int:
        """
        清理过期内容指纹
        
        Args:
            days: 保留最近多少天的数据
            
        Returns:
            删除的指纹数量
        """
        try:
            db = self._get_database()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
            DELETE FROM content_fingerprints 
            WHERE created_at < %s AND is_duplicate = TRUE
            """
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, [cutoff_date])
                deleted_count = cursor.rowcount
                conn.commit()
            
            print(f"🗑️ 清理了 {deleted_count} 个过期指纹")
            return deleted_count
            
        except Exception as e:
            print(f"❌ 清理过期指纹失败: {e}")
            return 0
    
    def _rebuild_tfidf_vectors(self):
        """重建TF-IDF向量"""
        if len(self.content_fingerprints) == 0:
            self.content_vectors = None
            return
        
        texts = [
            fp.title + " " + fp.content_preview
            for fp in self.content_fingerprints.values()
        ]
        
        if texts:
            self.content_vectors = self.tfidf_vectorizer.fit_transform(texts)
            print(f"✅ 重建TF-IDF向量，完成 {len(texts)} 个文本")
    
    def set_similarity_threshold(self, threshold: float):
        """
        设置相似度阈值
        
        Args:
            threshold: 相似度阈值（0-1）
        """
        self.similarity_threshold = max(0.0, min(1.0, threshold))
        print(f"📊 相似度阈值设置为: {self.similarity_threshold}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取去重统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.content_fingerprints)
        duplicates = sum(1 for fp in self.content_fingerprints.values() if fp.is_duplicate)
        
        return {
            "total_fingerprints": total,
            "duplicate_count": duplicates,
            "unique_count": total - duplicates,
            "similarity_threshold": self.similarity_threshold,
            "vector_dimensions": self.content_vectors.shape[1] if self.content_vectors is not None else 0
        }
    
    def get_source_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        获取按来源分组的统计信息
        
        Returns:
            来源统计字典 {source: {"total": x, "duplicates": y}}
        """
        source_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "duplicates": 0})
        
        for fp in self.content_fingerprints.values():
            source = getattr(fp, 'source', 'unknown') if hasattr(fp, 'source') else 'unknown'
            source_stats[source]["total"] += 1
            if fp.is_duplicate:
                source_stats[source]["duplicates"] += 1
        
        return dict(source_stats)
    
    def get_duplicate_rate(self) -> float:
        """
        计算重复率
        
        Returns:
            重复率（0-1）
        """
        total = len(self.content_fingerprints)
        if total == 0:
            return 0.0
        duplicates = sum(1 for fp in self.content_fingerprints.values() if fp.is_duplicate)
        return duplicates / total
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成去重统计报告
        
        Returns:
            报告字典
        """
        stats = self.get_statistics()
        source_stats = self.get_source_statistics()
        
        db_stats = self.get_duplicate_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "memory_stats": stats,
            "database_stats": db_stats,
            "source_statistics": source_stats,
            "duplicate_rate": self.get_duplicate_rate(),
            "similarity_threshold": self.similarity_threshold
        }
    
    def print_report(self):
        """打印去重统计报告"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("📊 增量爬取去重统计报告")
        print("="*60)
        print(f"生成时间: {report['timestamp']}")
        print(f"相似度阈值: {report['similarity_threshold']}")
        print("-"*60)
        print("内存中的指纹统计:")
        print(f"  总数量: {report['memory_stats']['total_fingerprints']}")
        print(f"  重复数: {report['memory_stats']['duplicate_count']}")
        print(f"  唯一数: {report['memory_stats']['unique_count']}")
        print(f"  重复率: {report['duplicate_rate']:.2%}")
        print("-"*60)
        print("数据库中的指纹统计:")
        print(f"  总数量: {report['database_stats']['total_fingerprints']}")
        print(f"  重复数: {report['database_stats']['duplicate_count']}")
        print(f"  唯一数: {report['database_stats']['unique_count']}")
        print(f"  来源数: {report['database_stats']['source_count']}")
        print("-"*60)
        print("按来源统计:")
        for source, s_stats in report['source_statistics'].items():
            rate = s_stats["duplicates"] / s_stats["total"] if s_stats["total"] > 0 else 0
            print(f"  {source}: {s_stats['total']} 条, {s_stats['duplicates']} 重复 ({rate:.2%})")
        print("="*60 + "\n")
    
    def clear_fingerprints(self):
        """清空所有指纹数据"""
        with self._lock:
            self.content_fingerprints.clear()
            self.content_vectors = None
            print("🗑️ 已清空所有内容指纹")


def get_incremental_crawler() -> IncrementalCrawler:
    """
    获取增量爬取控制器实例
    
    Returns:
        IncrementalCrawler 实例
    """
    return IncrementalCrawler()


class DuplicateChecker:
    """
    批量内容去重检查器
    支持批量检测和并行处理
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        max_workers: int = 4
    ):
        """
        初始化批量去重检查器
        
        Args:
            similarity_threshold: 相似度阈值
            max_workers: 最大并发数
        """
        self.incremental_crawler = get_incremental_crawler()
        self.similarity_threshold = similarity_threshold
        self.max_workers = max_workers
        self.incremental_crawler.set_similarity_threshold(similarity_threshold)
    
    def check_batch(
        self,
        items: List[Dict[str, str]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量检测内容重复
        
        Args:
            items: 内容列表，每个元素包含 note_id, title, content
            
        Returns:
            (新内容列表, 重复内容列表)
        """
        new_items = []
        duplicate_items = []
        
        for item in items:
            note_id = item.get("note_id", "")
            title = item.get("title", "")
            content = item.get("content", "")
            
            result = self.incremental_crawler.check_duplicate(
                note_id=note_id,
                title=title,
                content=content,
                check_exact=True,
                check_similar=True
            )
            
            item_result = {
                **item,
                "duplicate_type": result.duplicate_type,
                "similarity_score": result.similarity_score,
                "duplicate_note_ids": result.duplicate_note_ids
            }
            
            if result.is_duplicate:
                duplicate_items.append(item_result)
            else:
                new_items.append(item_result)
                self.incremental_crawler.add_content(note_id, title, content)
        
        return new_items, duplicate_items
    
    def filter_new_items(
        self,
        items: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        过滤出新增内容（去重）
        
        Args:
            items: 原始内容列表
            
        Returns:
            仅包含新增内容的列表
        """
        new_items, _ = self.check_batch(items)
        return new_items


def filter_duplicate_posts(
    posts: List[Dict[str, Any]],
    threshold: float = 0.85
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    过滤重复帖子
    
    Args:
        posts: 帖子列表
        threshold: 相似度阈值
        
    Returns:
        (新帖子列表, 重复帖子列表)
    """
    checker = DuplicateChecker(similarity_threshold=threshold)
    
    items = [
        {
            "note_id": post.get("note_id", post.get("id", "")),
            "title": post.get("title", "") or post.get("basic_info", {}).get("title", ""),
            "content": post.get("content", "") or post.get("detail", {}).get("desc", "")
        }
        for post in posts
    ]
    
    new_items, duplicate_items = checker.check_batch(items)
    
    new_posts = [
        post for post in posts
        if post.get("note_id", post.get("id", "")) in [i["note_id"] for i in new_items]
    ]
    
    duplicate_posts = [
        post for post in posts
        if post.get("note_id", post.get("id", "")) in [i["note_id"] for i in duplicate_items]
    ]
    
    return new_posts, duplicate_posts
