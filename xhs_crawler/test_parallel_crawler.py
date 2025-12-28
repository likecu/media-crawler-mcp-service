#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行爬虫模块测试脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试并行爬虫模块导入")
    print("=" * 60)
    
    try:
        from xhs_crawler.crawlers.parallel_keyword_crawler import (
            ParallelKeywordCrawler,
            run_parallel_crawler,
            CrawlResult
        )
        print("✅ 所有模块导入成功")
        print(f"  - ParallelKeywordCrawler: {ParallelKeywordCrawler.__name__}")
        print(f"  - run_parallel_crawler: {run_parallel_crawler.__name__}")
        print(f"  - CrawlResult: {CrawlResult.__name__}")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crawler_instantiation():
    """测试爬虫实例化"""
    print("\n" + "=" * 60)
    print("测试爬虫实例化")
    print("=" * 60)
    
    try:
        from xhs_crawler.crawlers.parallel_keyword_crawler import ParallelKeywordCrawler
        
        crawler = ParallelKeywordCrawler(
            max_workers=3,
            detail_concurrency=5,
            timeout_per_keyword=120.0,
            timeout_per_detail=30.0
        )
        print("✅ ParallelKeywordCrawler 实例化成功")
        print(f"  - max_workers: {crawler.max_workers}")
        print(f"  - detail_concurrency: {crawler.detail_concurrency}")
        print(f"  - timeout_per_keyword: {crawler.timeout_per_keyword}")
        print(f"  - timeout_per_detail: {crawler.timeout_per_detail}")
        return True
    except Exception as e:
        print(f"❌ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crawl_result_dataclass():
    """测试CrawlResult数据类"""
    print("\n" + "=" * 60)
    print("测试CrawlResult数据类")
    print("=" * 60)
    
    try:
        from xhs_crawler.crawlers.parallel_keyword_crawler import CrawlResult
        
        result = CrawlResult(
            keyword="测试关键词",
            success=True,
            notes=[{"note_id": "123", "title": "测试笔记"}],
            duration=10.5,
            pages_crawled=3
        )
        print("✅ CrawlResult 数据类测试成功")
        print(f"  - keyword: {result.keyword}")
        print(f"  - success: {result.success}")
        print(f"  - notes count: {len(result.notes)}")
        print(f"  - duration: {result.duration}")
        print(f"  - pages_crawled: {result.pages_crawled}")
        return True
    except Exception as e:
        print(f"❌ 数据类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    results = []
    
    results.append(("模块导入测试", test_imports()))
    
    if results[-1][1]:
        results.append(("爬虫实例化测试", test_crawler_instantiation()))
    
    if results[-1][1]:
        results.append(("数据类测试", test_crawl_result_dataclass()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("💥 部分测试失败，请检查错误信息")
        sys.exit(1)
