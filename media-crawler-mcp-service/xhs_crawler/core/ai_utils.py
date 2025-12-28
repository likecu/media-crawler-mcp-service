#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI/ML工具模块，提供增强的内容分析和推荐功能
优化版本：支持异步推理、批量处理、结果缓存
"""

import os
import sys
import json
import re
import time
import hashlib
import asyncio
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from xhs_crawler.core.mcp_utils import MCPUtils
from xhs_crawler.core.database import get_neon_database

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from xhs_crawler.core.config import get_output_dir, get_detail_dir, OCR_CONFIG

OCR_TOOL = OCR_CONFIG["tool_path"]


@dataclass
class InferenceResult:
    """推理结果数据类"""
    content: str
    summary: str = ""
    sentiment: str = "中性"
    key_points: List[str] = field(default_factory=list)
    category: str = "未分类"
    difficulty: str = "中级"
    confidence: float = 0.0
    tokens_used: int = 0
    inference_time: float = 0.0
    cached: bool = False


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, capacity: int = 1000, ttl: int = 3600):
        """
        初始化LRU缓存
        
        Args:
            capacity: 最大缓存数量
            ttl: 缓存过期时间（秒）
        """
        self.capacity = capacity
        self.ttl = ttl
        self.cache = {}
        self.access_order = {}
        self.lock = threading.Lock()
        self._counter = 0
    
    def _generate_key(self, content: str) -> str:
        """生成缓存键"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, content: str) -> Optional[InferenceResult]:
        """
        获取缓存结果
        
        Args:
            content: 输入内容
            
        Returns:
            缓存的推理结果，如果未命中返回None
        """
        with self.lock:
            key = self._generate_key(content)
            
            if key not in self.cache:
                return None
            
            result, timestamp = self.cache[key]
            if datetime.now() - timestamp > timedelta(seconds=self.ttl):
                del self.cache[key]
                del self.access_order[key]
                return None
            
            self._counter += 1
            self.access_order[key] = self._counter
            return result
    
    def set(self, content: str, result: InferenceResult):
        """
        设置缓存结果
        
        Args:
            content: 输入内容
            result: 推理结果
        """
        with self.lock:
            key = self._generate_key(content)
            self._counter += 1
            
            if key in self.cache:
                del self.cache[key]
                del self.access_order[key]
            
            if len(self.cache) >= self.capacity:
                oldest_key = min(self.access_order.keys(), key=lambda k: self.access_order[k])
                del self.cache[oldest_key]
                del self.access_order[oldest_key]
            
            self.cache[key] = (result, datetime.now())
            self.access_order[key] = self._counter
    
    def clear_expired(self):
        """清除过期缓存"""
        with self.lock:
            now = datetime.now()
            expired_keys = [
                k for k, (v, t) in self.cache.items()
                if now - t > timedelta(seconds=self.ttl)
            ]
            for k in expired_keys:
                del self.cache[k]
                del self.access_order[k]


class BatchProcessor:
    """批量处理器，支持并发批量推理"""
    
    def __init__(self, max_concurrent: int = 5, batch_size: int = 10):
        """
        初始化批量处理器
        
        Args:
            max_concurrent: 最大并发数
            batch_size: 批处理大小
        """
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    async def process_batch(
        self,
        items: List[Dict[str, Any]],
        process_func: callable,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量处理项目
        
        Args:
            items: 项目列表
            process_func: 处理函数
            kwargs: 处理函数参数
            
        Returns:
            处理结果列表
        """
        results = []
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        for batch in batches:
            tasks = [
                self._process_with_semaphore(process_func, item, **kwargs)
                for item in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    async def _process_with_semaphore(
        self,
        process_func: callable,
        item: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用信号量限制并发处理单个项目
        
        Args:
            process_func: 处理函数
            item: 项目
            kwargs: 处理函数参数
            
        Returns:
            处理结果
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                lambda: process_func(item, **kwargs)
            )


class AIUtils:
    """
    AI/ML工具类，提供增强的内容分析和推荐功能
    优化版本：支持异步推理、批量处理、结果缓存
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
        """初始化AI工具"""
        if self._initialized:
            return
        
        self.mcp_utils = MCPUtils()
        self.tfidf_vectorizer = TfidfVectorizer(stop_words=None)
        self.post_vectors = None
        self.posts = None
        self.cache = LRUCache(capacity=500, ttl=1800)
        self.batch_processor = BatchProcessor(max_concurrent=3, batch_size=5)
        self._initialized = True
    
    def summarize_content_enhanced(
        self,
        content: str,
        title: str,
        images: List[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        增强的内容总结功能，包括内容总结、情感分析和关键信息提取
        
        Args:
            content: 帖子内容
            title: 帖子标题
            images: 图片列表
            use_cache: 是否使用缓存
            
        Returns:
            包含总结、情感分析和关键信息的字典
        """
        print(f"🔍 开始增强内容总结: '{title[:30]}...'")
        print(f"📝 内容长度: {len(content)} 字符")
        
        try:
            cache_key = f"{title[:50]}|{content[:100]}"
            
            if use_cache:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    print(f"✅ 使用缓存结果")
                    return {
                        "summary": cached_result.summary,
                        "sentiment": cached_result.sentiment,
                        "key_points": cached_result.key_points,
                        "category": cached_result.category,
                        "difficulty": cached_result.difficulty,
                        "confidence": cached_result.confidence,
                        "cached": True
                    }
            
            full_content = content
            if images and len(images) > 0:
                print(f"📸 包含 {len(images)} 张图片")
            
            start_time = time.time()
            
            question = f'''请对这篇内容进行增强总结，输出格式为JSON，包含以下字段：
            - summary: 主要内容总结（200字以内）
            - sentiment: 情感倾向（积极/中性/消极）
            - key_points: 关键信息列表（5-10个要点）
            - category: 内容类别
            - difficulty: 难度级别（初级/中级/高级）
            
            内容：
            标题：{title}
            正文：{full_content}
            '''
            
            result = self._call_llm_tool(question)
            inference_time = time.time() - start_time
            
            if result:
                try:
                    summary_data = json.loads(result)
                    
                    inference_result = InferenceResult(
                        content=cache_key,
                        summary=summary_data.get("summary", ""),
                        sentiment=summary_data.get("sentiment", "中性"),
                        key_points=summary_data.get("key_points", []),
                        category=summary_data.get("category", "未分类"),
                        difficulty=summary_data.get("difficulty", "中级"),
                        confidence=0.85,
                        inference_time=inference_time
                    )
                    
                    if use_cache:
                        self.cache.set(cache_key, inference_result)
                    
                    return {
                        **summary_data,
                        "confidence": inference_result.confidence,
                        "inference_time": inference_time,
                        "cached": False
                    }
                    
                except json.JSONDecodeError:
                    return self._extract_summary_info(result, title, inference_time)
            
            return {"inference_time": inference_time, "cached": False}
            
        except Exception as e:
            print(f"❌ 增强总结异常: {type(e).__name__}: {e}")
            return {}
    
    def _call_llm_tool(self, question: str, timeout: int = 60) -> str:
        """
        调用LLM工具
        
        Args:
            question: 问题内容
            timeout: 超时时间（秒）
            
        Returns:
            LLM回答
        """
        try:
            args = [
                OCR_CONFIG["python_path"],
                OCR_TOOL,
                "--question",
                question
            ]
            
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout
            )
            
            if result.returncode != 0:
                print(f"❌ LLM工具调用失败，返回码: {result.returncode}")
                print(f"💬 错误输出: {result.stderr}")
                return ""
            
            output = result.stdout.strip()
            if "=== 处理结果 ===" in output:
                result_part = output.split("=== 处理结果 ===")[1]
                if "回答: " in result_part:
                    return result_part.split("回答: ")[1].strip()
            
            return output
            
        except subprocess.TimeoutExpired:
            print(f"❌ LLM工具调用超时（{timeout}秒）")
            return ""
        except Exception as e:
            print(f"❌ 调用LLM工具异常: {type(e).__name__}: {e}")
            return ""
    
    def _extract_summary_info(
        self,
        text: str,
        title: str,
        inference_time: float
    ) -> Dict[str, Any]:
        """
        从非JSON格式的文本中提取总结信息
        
        Args:
            text: 原始文本
            title: 帖子标题
            inference_time: 推理时间
            
        Returns:
            提取的总结信息
        """
        return {
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "sentiment": "中性",
            "key_points": [text[:100] + "..."] if text else [],
            "category": "未分类",
            "difficulty": "中级",
            "confidence": 0.6,
            "inference_time": inference_time,
            "cached": False
        }
    
    def batch_summarize(
        self,
        posts: List[Dict[str, Any]],
        use_cache: bool = True,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        批量总结帖子内容
        
        Args:
            posts: 帖子列表，每个帖子包含title和content
            use_cache: 是否使用缓存
            max_concurrent: 最大并发数
            
        Returns:
            总结结果列表
        """
        print(f"🔧 开始批量总结，共 {len(posts)} 篇帖子")
        start_time = time.time()
        
        results = []
        
        def process_single(post: Dict[str, Any]) -> Dict[str, Any]:
            title = post.get("title", "") or post.get("basic_info", {}).get("title", "")
            content = post.get("content", "") or post.get("detail", {}).get("desc", "")
            note_id = post.get("note_id", "")
            
            summary = self.summarize_content_enhanced(
                content=content,
                title=title,
                use_cache=use_cache
            )
            
            return {
                "note_id": note_id,
                "title": title,
                "summary": summary,
                "processing_time": time.time()
            }
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [
                executor.submit(process_single, post)
                for post in posts
            ]
            
            for future in futures:
                try:
                    result = future.result(timeout=120)
                    results.append(result)
                    print(f"✅ 完成帖子总结: {result['title'][:30]}...")
                except Exception as e:
                    print(f"❌ 批量总结异常: {e}")
        
        total_time = time.time() - start_time
        print(f"✅ 批量总结完成，{len(results)} 篇帖子耗时 {total_time:.2f} 秒")
        
        return results
    
    def analyze_image_content(self, image_url: str) -> Dict[str, Any]:
        """
        分析图像内容，包括图像分类和标签提取
        
        Args:
            image_url: 图像URL
            
        Returns:
            包含图像分析结果的字典
        """
        print(f"🔍 开始图像内容分析: {image_url[:50]}...")
        
        try:
            temp_dir = "/tmp/xhs_image_analysis"
            os.makedirs(temp_dir, exist_ok=True)
            img_save_path = os.path.join(temp_dir, f"image_{int(time.time())}.jpg")
            
            import requests
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            with open(img_save_path, 'wb') as f:
                f.write(response.content)
            
            question = "请分析这张图片的内容，包括：1. 图像主要内容；2. 相关标签（5-10个）；3. 图像类别；4. 关键元素描述"
            
            args = [
                OCR_CONFIG["python_path"],
                OCR_TOOL,
                img_save_path,
                "--question",
                question
            ]
            
            start_time = time.time()
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120
            )
            inference_time = time.time() - start_time
            
            if result.returncode != 0:
                print(f"❌ 图像分析失败，返回码: {result.returncode}")
                return {"error": result.stderr}
            
            output = result.stdout.strip()
            if "=== 处理结果 ===" in output:
                result_part = output.split("=== 处理结果 ===")[1]
                if "回答: " in result_part:
                    analysis_text = result_part.split("回答: ")[1].strip()
                    return {
                        "content": analysis_text,
                        "tags": [analysis_text[:20] for _ in range(5)],
                        "category": "未分类",
                        "elements": [analysis_text[:50]],
                        "inference_time": inference_time
                    }
            
            return {
                "content": output,
                "tags": [],
                "category": "未分类",
                "elements": [],
                "inference_time": inference_time
            }
            
        except Exception as e:
            print(f"❌ 图像内容分析异常: {type(e).__name__}: {e}")
            return {"error": str(e)}
    
    def build_content_index(self, posts: List[Dict[str, Any]]):
        """
        构建内容索引，用于相似度搜索
        
        Args:
            posts: 帖子列表
        """
        print(f"🔧 开始构建内容索引，共 {len(posts)} 篇帖子")
        
        self.posts = posts
        
        post_contents = []
        for post in posts:
            content = ""
            if "basic_info" in post:
                title = post["basic_info"].get("title", "")
                content += title + " "
            if "detail" in post:
                desc = post["detail"].get("desc", "")
                content += desc
            post_contents.append(content)
        
        self.post_vectors = self.tfidf_vectorizer.fit_transform(post_contents)
        print(f"✅ 内容索引构建完成")
    
    def search_similar_posts(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        基于内容相似度搜索帖子
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            相似度排序的帖子列表
        """
        if self.post_vectors is None or self.posts is None:
            print("❌ 内容索引未构建，请先调用build_content_index")
            return []
        
        print(f"🔍 开始相似度搜索: '{query}'")
        
        query_vector = self.tfidf_vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.post_vectors).flatten()
        
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                post = self.posts[idx].copy()
                post["similarity"] = float(similarities[idx])
                results.append(post)
        
        print(f"✅ 找到 {len(results)} 篇相关帖子")
        return results
    
    def recommend_posts(self, post_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        基于内容相似度推荐帖子
        
        Args:
            post_id: 参考帖子ID
            top_k: 返回结果数量
            
        Returns:
            推荐帖子列表
        """
        if self.post_vectors is None or self.posts is None:
            print("❌ 内容索引未构建，请先调用build_content_index")
            return []
        
        print(f"🔍 开始推荐帖子，参考ID: {post_id}")
        
        ref_idx = -1
        for i, post in enumerate(self.posts):
            if post.get("note_id") == post_id:
                ref_idx = i
                break
        
        if ref_idx == -1:
            print(f"❌ 未找到参考帖子: {post_id}")
            return []
        
        ref_vector = self.post_vectors[ref_idx]
        similarities = cosine_similarity(ref_vector, self.post_vectors).flatten()
        
        top_indices = similarities.argsort()[::-1][1:top_k+1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                post = self.posts[idx].copy()
                post["similarity"] = float(similarities[idx])
                results.append(post)
        
        print(f"✅ 生成 {len(results)} 篇推荐帖子")
        return results
    
    def analyze_trends(
        self,
        posts: List[Dict[str, Any]],
        time_window: str = "month"
    ) -> Dict[str, Any]:
        """
        分析内容趋势
        
        Args:
            posts: 帖子列表
            time_window: 时间窗口（day/week/month）
            
        Returns:
            趋势分析结果
        """
        print(f"📊 开始趋势分析，共 {len(posts)} 篇帖子，时间窗口: {time_window}")
        
        category_counts = {}
        for post in posts:
            category = post.get("category", "未分类")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        all_content = " "
        for post in posts:
            if "title" in post:
                all_content += post["title"] + " "
            if "content" in post:
                all_content += post["content"] + " "
        
        words = re.findall(r'\b\w{2,}\b', all_content)
        word_counts = {}
        stop_words = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        for word in words:
            if word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "category_distribution": category_counts,
            "top_keywords": sorted_words,
            "total_posts": len(posts),
            "time_window": time_window
        }
    
    def clear_cache(self, expired_only: bool = False):
        """
        清除缓存
        
        Args:
            expired_only: 只清除过期缓存
        """
        if expired_only:
            self.cache.clear_expired()
            print("✅ 已清除过期缓存")
        else:
            self.cache = LRUCache(capacity=500, ttl=1800)
            print("✅ 已清除所有缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return {
            "cache_size": len(self.cache.cache),
            "capacity": self.cache.capacity,
            "ttl": self.cache.ttl
        }


def get_ai_utils() -> AIUtils:
    """
    获取AI工具实例
    
    Returns:
        AIUtils实例
    """
    return AIUtils()


if __name__ == "__main__":
    ai_utils = AIUtils()
    
    print("测试增强内容总结...")
    result = ai_utils.summarize_content_enhanced(
        content="这是一篇关于机器学习的面试经验分享...",
        title="机器学习面试经验总结"
    )
    print(f"总结结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    print("\n测试缓存功能...")
    result2 = ai_utils.summarize_content_enhanced(
        content="这是一篇关于机器学习的面试经验分享...",
        title="机器学习面试经验总结"
    )
    print(f"是否使用缓存: {result2.get('cached', False)}")
    
    print("\n测试趋势分析...")
    trends = ai_utils.analyze_trends([
        {"title": "测试1", "content": "机器学习内容"},
        {"title": "测试2", "content": "深度学习内容"},
        {"title": "测试3", "content": "机器学习内容"}
    ])
    print(f"趋势分析: {json.dumps(trends, ensure_ascii=False, indent=2)}")
    
    print("\n测试批量总结...")
    posts = [
        {"title": f"测试帖子{i}", "content": f"这是第{i}篇测试内容..."}
        for i in range(5)
    ]
    batch_results = ai_utils.batch_summarize(posts)
    print(f"批量总结完成，共 {len(batch_results)} 篇")
