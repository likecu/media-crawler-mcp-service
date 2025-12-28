#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试增量爬取与智能去重模块"""

import sys
import os
sys.path.insert(0, '/app')

from xhs_crawler.core.incremental_crawler import (
    IncrementalCrawler,
    DuplicateChecker,
    filter_duplicate_posts,
    get_incremental_crawler
)


def test_incremental_crawler():
    """测试增量爬取控制器"""
    print('=' * 60)
    print('增量爬取控制器测试')
    print('=' * 60)
    
    crawler = get_incremental_crawler()
    
    # 测试1: 添加内容
    print('\n[测试1] 添加内容指纹')
    crawler.add_content(
        note_id='note_001',
        title='如何学习机器学习',
        content='机器学习是人工智能的一个分支，通过算法从数据中学习模式。'
    )
    crawler.add_content(
        note_id='note_002',
        title='深度学习入门指南',
        content='深度学习是机器学习的一个子领域，使用神经网络模拟人脑工作机制。'
    )
    print('  已添加2个内容指纹')
    
    # 测试2: 检测精确重复
    print('\n[测试2] 检测精确重复')
    result = crawler.check_duplicate(
        note_id='note_003',
        title='如何学习机器学习',
        content='机器学习是人工智能的一个分支，通过算法从数据中学习模式。'
    )
    print(f'  重复类型: {result.duplicate_type}')
    print(f'  是否重复: {result.is_duplicate}')
    print(f'  相似度: {result.similarity_score}')
    
    # 测试3: 检测相似内容
    print('\n[测试3] 检测相似内容')
    result = crawler.check_duplicate(
        note_id='note_004',
        title='机器学习技术入门',
        content='机器学习是人工智能的重要技术，通过算法从数据中学习规律。'
    )
    print(f'  重复类型: {result.duplicate_type}')
    print(f'  是否重复: {result.is_duplicate}')
    print(f'  相似度: {result.similarity_score:.4f}')
    
    # 测试4: 新内容
    print('\n[测试4] 新内容检测')
    result = crawler.check_duplicate(
        note_id='note_005',
        title='Python编程技巧',
        content='Python是一种高级编程语言，适合初学者入门。'
    )
    print(f'  重复类型: {result.duplicate_type}')
    print(f'  是否重复: {result.is_duplicate}')
    print(f'  相似度: {result.similarity_score}')
    
    # 测试5: 统计信息
    print('\n[测试5] 统计信息')
    stats = crawler.get_statistics()
    print(f'  总指纹数: {stats["total_fingerprints"]}')
    print(f'  重复数: {stats["duplicate_count"]}')
    print(f'  唯一数: {stats["unique_count"]}')
    print(f'  相似度阈值: {stats["similarity_threshold"]}')
    
    print('\n' + '=' * 60)
    print('增量爬取控制器测试完成！')
    print('=' * 60)


def test_duplicate_checker():
    """测试批量去重检查器"""
    print('\n' + '=' * 60)
    print('批量去重检查器测试')
    print('=' * 60)
    
    checker = DuplicateChecker(similarity_threshold=0.8)
    
    items = [
        {"note_id": "post_001", "title": "AI面试经验分享", "content": "今天分享一些AI面试的技巧。"},
        {"note_id": "post_002", "title": "AI面试准备攻略", "content": "准备AI面试需要掌握这些要点。"},
        {"note_id": "post_003", "title": "机器学习入门", "content": "机器学习入门需要掌握基础数学知识。"},
        {"note_id": "post_004", "title": "AI面试经验分享", "content": "今天分享一些AI面试的技巧。"},
        {"note_id": "post_005", "title": "Java开发技巧", "content": "Java是一种流行的编程语言。"},
    ]
    
    new_items, duplicate_items = checker.check_batch(items)
    
    print(f'\n原始数量: {len(items)}')
    print(f'新内容数量: {len(new_items)}')
    print(f'重复内容数量: {len(duplicate_items)}')
    
    print('\n新内容:')
    for item in new_items:
        print(f'  - {item["title"]} ({item["note_id"]})')
    
    print('\n重复内容:')
    for item in duplicate_items:
        print(f'  - {item["title"]} ({item["note_id"]}) - {item["duplicate_type"]}')
    
    print('\n' + '=' * 60)
    print('批量去重检查器测试完成！')
    print('=' * 60)


def test_filter_duplicate_posts():
    """测试过滤重复帖子"""
    print('\n' + '=' * 60)
    print('过滤重复帖子测试')
    print('=' * 60)
    
    posts = [
        {"note_id": "001", "title": "刷题技巧", "content": "分享一些LeetCode刷题技巧。"},
        {"note_id": "002", "title": "算法面试", "content": "算法面试是技术面试的重要组成部分。"},
        {"note_id": "003", "title": "刷题技巧分享", "content": "分享一些LeetCode刷题技巧和经验。"},
        {"note_id": "004", "title": "数据结构", "content": "学习数据结构对编程很重要。"},
        {"note_id": "005", "title": "刷题技巧", "content": "分享一些LeetCode刷题技巧。"},
    ]
    
    new_posts, duplicate_posts = filter_duplicate_posts(posts, threshold=0.75)
    
    print(f'\n原始帖子数: {len(posts)}')
    print(f'新帖子数: {len(new_posts)}')
    print(f'重复帖子数: {len(duplicate_posts)}')
    
    print('\n新帖子:')
    for post in new_posts:
        print(f'  - {post["title"]} ({post["note_id"]})')
    
    print('\n重复帖子:')
    for post in duplicate_posts:
        print(f'  - {post["title"]} ({post["note_id"]})')
    
    print('\n' + '=' * 60)
    print('过滤重复帖子测试完成！')
    print('=' * 60)


def main():
    """主测试函数"""
    try:
        test_incremental_crawler()
        test_duplicate_checker()
        test_filter_duplicate_posts()
        print('\n✅ 所有测试完成！')
    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
