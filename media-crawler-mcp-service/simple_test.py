#!/usr/bin/env python
import sys
sys.path.insert(0, '/app')

print("开始测试...")
try:
    from xhs_crawler.core.incremental_crawler import IncrementalCrawler
    print("导入成功")
    
    crawler = IncrementalCrawler()
    print("实例化成功")
    
    crawler.add_content('001', '标题1', '内容1')
    print("添加成功")
    
    result = crawler.check_duplicate('002', '标题1', '内容1')
    print(f"重复检测: {result.is_duplicate}, 类型: {result.duplicate_type}")
    
    print("测试完成")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
