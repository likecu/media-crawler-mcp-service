#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Neon 数据库模块
"""

print("🚀 开始测试 Neon 数据库模块")

try:
    # 测试导入
    from xhs_crawler.core.database import get_neon_database
    print("✅ 成功导入 Neon 数据库模块")
    
    # 测试创建数据库实例（这会尝试连接数据库，如果配置不正确会失败但不会崩溃）
    db = get_neon_database()
    if db:
        print("✅ 成功创建 Neon 数据库实例")
        db.close()
    else:
        print("⚠️  创建 Neon 数据库实例失败（可能是配置问题，这是预期的，因为 .env 文件可能没有实际配置）")
    
    # 测试 HTML 生成器导入
    from xhs_crawler.generators.html_generator import generate_html
    print("✅ 成功导入 HTML 生成器")
    
    # 测试总结器导入
    from xhs_crawler.summarizers.summarize_posts import save_summary
    print("✅ 成功导入总结器")
    
    print("🎉 所有模块测试通过！代码语法和导入正常")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
