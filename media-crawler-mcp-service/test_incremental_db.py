#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增量爬取数据库集成功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from xhs_crawler.core.incremental_crawler import (
    get_incremental_crawler,
    ContentFingerprint,
    filter_duplicate_posts
)


def test_database_integration():
    """测试数据库集成功能"""
    print("=" * 60)
    print("测试增量爬取数据库集成功能")
    print("=" * 60)
    
    crawler = get_incremental_crawler()
    
    print("\n1. 测试清空现有指纹...")
    crawler.clear_fingerprints()
    
    print("\n2. 测试保存内容指纹到数据库...")
    test_fingerprints = [
        ContentFingerprint(
            note_id="test_note_001",
            content_hash="abc123hash",
            title_hash="def456hash",
            combined_hash="combined789hash",
            title="Python算法教程",
            content_preview="本文介绍Python中的排序算法..."
        ),
        ContentFingerprint(
            note_id="test_note_002",
            content_hash="xyz789hash",
            title_hash="uvw012hash",
            combined_hash="combined345hash",
            title="机器学习入门",
            content_preview="机器学习是人工智能的一个重要分支..."
        )
    ]
    
    saved_count = crawler.save_fingerprints_batch(test_fingerprints, source="test")
    print(f"   保存指纹数量: {saved_count}")
    
    print("\n3. 测试从数据库加载现有指纹...")
    loaded_count = crawler.load_existing_fingerprints(source="test")
    print(f"   加载指纹数量: {loaded_count}")
    
    print("\n4. 测试重复检测...")
    result1 = crawler.check_duplicate(
        note_id="test_note_003",
        title="Python算法教程",
        content="本文介绍Python中的排序算法..."
    )
    print(f"   相似内容检测结果: duplicate_type={result1.duplicate_type}, is_duplicate={result1.is_duplicate}")
    
    result2 = crawler.check_duplicate(
        note_id="test_note_004",
        title="全新的算法文章",
        content="这是一篇关于数据结构的文章..."
    )
    print(f"   新内容检测结果: duplicate_type={result2.duplicate_type}, is_duplicate={result2.is_duplicate}")
    
    print("\n5. 测试获取重复统计信息...")
    stats = crawler.get_duplicate_stats(source="test")
    print(f"   统计信息: {stats}")
    
    print("\n6. 测试本地内存统计...")
    local_stats = crawler.get_statistics()
    print(f"   本地统计: {local_stats}")
    
    print("\n7. 测试批量保存新检测的内容...")
    new_fingerprints = []
    if result2.fingerprint:
        new_fingerprints.append(result2.fingerprint)
    
    if new_fingerprints:
        saved_count = crawler.save_fingerprints_batch(new_fingerprints, source="test")
        print(f"   保存新指纹数量: {saved_count}")
    
    print("\n8. 测试清理过期指纹...")
    deleted_count = crawler.cleanup_old_fingerprints(days=1)
    print(f"   清理过期指纹数量: {deleted_count}")
    
    print("\n" + "=" * 60)
    print("✅ 数据库集成测试完成")
    print("=" * 60)


def test_content_fingerprint_creation():
    """测试内容指纹创建"""
    print("\n" + "=" * 60)
    print("测试内容指纹创建功能")
    print("=" * 60)
    
    crawler = get_incremental_crawler()
    crawler.clear_fingerprints()
    
    test_cases = [
        {
            "note_id": "note_001",
            "title": "  Python  高级  特性  ",
            "content": "  这是一篇关于Python的文章，包含很多空格  "
        },
        {
            "note_id": "note_002",
            "title": "Python高级特性",
            "content": "这是一篇关于Python的文章，包含很多空格"
        }
    ]
    
    for case in test_cases:
        fingerprint = crawler._create_fingerprint(
            case["note_id"],
            case["title"],
            case["content"]
        )
        print(f"\n  笔记ID: {case['note_id']}")
        print(f"  标题哈希: {fingerprint.title_hash[:16]}...")
        print(f"  内容哈希: {fingerprint.content_hash[:16]}...")
        print(f"  组合哈希: {fingerprint.combined_hash[:16]}...")
    
    print("\n  测试两个相似内容的哈希是否不同（带空格归一化）:")
    print(f"    案例1标题哈希: {crawler.content_fingerprints['note_001'].title_hash}")
    print(f"    案例2标题哈希: {crawler.content_fingerprints['note_002'].title_hash}")
    print(f"    哈希是否相同: {crawler.content_fingerprints['note_001'].title_hash == crawler.content_fingerprints['note_002'].title_hash}")
    
    print("\n" + "=" * 60)
    print("✅ 内容指纹创建测试完成")
    print("=" * 60)


def test_similarity_detection():
    """测试相似度检测"""
    print("\n" + "=" * 60)
    print("测试相似度检测功能")
    print("=" * 60)
    
    crawler = get_incremental_crawler()
    crawler.clear_fingerprints()
    crawler.set_similarity_threshold(0.7)
    
    base_content = "Python是一门流行的编程语言，广泛用于Web开发、数据科学和机器学习领域。"
    
    similar_cases = [
        {"note_id": "base_001", "title": "Python编程语言介绍", "content": base_content},
        {"note_id": "similar_001", "title": "Python编程语言入门", "content": "Python是一门流行的编程语言，广泛用于Web开发、数据科学和机器学习领域。"},
        {"note_id": "different_001", "title": "JavaScript教程", "content": "JavaScript是一门用于Web前端开发的脚本语言。"},
    ]
    
    for case in similar_cases:
        result = crawler.check_duplicate(
            case["note_id"],
            case["title"],
            case["content"],
            check_exact=True,
            check_similar=True
        )
        print(f"\n  笔记ID: {case['note_id']}")
        print(f"  重复类型: {result.duplicate_type}")
        print(f"  相似度分数: {result.similarity_score}")
        print(f"  是否重复: {result.is_duplicate}")
        print(f"  重复ID列表: {result.duplicate_note_ids}")
    
    print("\n" + "=" * 60)
    print("✅ 相似度检测测试完成")
    print("=" * 60)


def test_batch_filter():
    """测试批量过滤功能"""
    print("\n" + "=" * 60)
    print("测试批量过滤功能")
    print("=" * 60)
    
    crawler = get_incremental_crawler()
    crawler.clear_fingerprints()
    
    posts = [
        {"note_id": "post_001", "title": "算法之美", "content": "本文探讨算法的优雅与效率。"},
        {"note_id": "post_002", "title": "数据结构的魅力", "content": "数据结构是程序设计的基石。"},
        {"note_id": "post_003", "title": "算法之美", "content": "本文探讨算法的优雅与效率。"},  # 重复
        {"note_id": "post_004", "title": "排序算法详解", "content": "介绍常见的排序算法及其实现。"},
        {"note_id": "post_005", "title": "算法之美", "content": "本文探讨算法的优雅与效率。"},  # 重复
    ]
    
    new_posts, duplicate_posts = filter_duplicate_posts(posts, threshold=0.85)
    
    print(f"\n  原始帖子数量: {len(posts)}")
    print(f"  新帖子数量: {len(new_posts)}")
    print(f"  重复帖子数量: {len(duplicate_posts)}")
    
    print("\n  新帖子列表:")
    for post in new_posts:
        print(f"    - {post['note_id']}: {post['title']}")
    
    print("\n  重复帖子列表:")
    for post in duplicate_posts:
        print(f"    - {post['note_id']}: {post['title']} (类型: {post['duplicate_type']})")
    
    print("\n" + "=" * 60)
    print("✅ 批量过滤测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_database_integration()
        test_content_fingerprint_creation()
        test_similarity_detection()
        test_batch_filter()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
