#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试远程数据库连接脚本
"""

import sys
sys.path.insert(0, '/home/milk/media-crawler-mcp-service')

from xhs_crawler.core.local_database import LocalPostgreSQLDatabase

def test_database_connection():
    """
    测试数据库连接和表创建
    """
    print("🔄 正在测试数据库连接...")
    
    try:
        db = LocalPostgreSQLDatabase(
            host="localhost",
            port=5432,
            database="mcp_tools_db",
            user="postgres",
            password="password"
        )
        
        print("✅ 数据库连接成功！")
        
        print("\n📊 测试插入数据...")
        
        test_note_id = f"test_{int(__import__('time').time())}"
        
        result = db.insert_leetcode_practice(
            note_id=test_note_id,
            title="测试刷题记录",
            content="这是测试内容",
            difficulty="medium",
            question_id="999",
            category="test"
        )
        
        if result:
            print("✅ 刷题记录插入成功！")
        else:
            print("❌ 刷题记录插入失败！")
            return False
        
        print("\n🔍 测试查询数据...")
        records = db.query_leetcode_practice(limit=10)
        print(f"✅ 查询成功，共找到 {len(records)} 条记录")
        
        print("\n📝 测试插入面试题...")
        test_question_id = f"test_q_{int(__import__('time').time())}"
        result = db.insert_interview_question(
            question_id=test_question_id,
            content="测试题目内容",
            answer="测试答案",
            category="test",
            difficulty="easy"
        )
        
        if result:
            print("✅ 面试题插入成功！")
        else:
            print("❌ 面试题插入失败！")
            return False
        
        print("\n🧹 清理测试数据...")
        db.delete_leetcode_practice(test_note_id)
        print("✅ 测试数据清理完成")
        
        db.close()
        print("\n🎉 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
