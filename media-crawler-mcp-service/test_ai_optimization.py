#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试优化后的AI模块功能"""

import sys
import os
sys.path.insert(0, '/app')

from xhs_crawler.core.ai_utils import get_ai_utils

def main():
    print('=' * 60)
    print('AI模块优化功能测试')
    print('=' * 60)
    print('Python版本:', sys.version)
    
    try:
        ai_utils = get_ai_utils()
        print('SUCCESS: AI工具实例化成功')
        print('-' * 40)
        
        # 测试缓存功能
        test_content = '这是一篇关于机器学习的测试文章，用于验证缓存功能是否正常工作。测试内容包括自然语言处理、深度学习模型训练等。'
        
        print('\n[测试1] 首次推理（无缓存）')
        result1 = ai_utils.summarize_content_enhanced(
            content=test_content, 
            title='缓存测试'
        )
        print('  推理结果:', result1.get('summary', '')[:50] + '...')
        print('  推理时间:', result1.get('inference_time', 0), '秒')
        print('  是否缓存:', result1.get('cached', False))
        
        print('\n[测试2] 第二次推理（期望命中缓存）')
        result2 = ai_utils.summarize_content_enhanced(
            content=test_content, 
            title='缓存测试'
        )
        print('  推理结果:', result2.get('summary', '')[:50] + '...')
        print('  推理时间:', result2.get('inference_time', 0), '秒')
        print('  是否缓存:', result2.get('cached', False))
        
        # 测试缓存统计
        print('\n[测试3] 缓存统计信息')
        cache_stats = ai_utils.get_cache_stats()
        print('  缓存条目数:', cache_stats.get('size', 0))
        print('  缓存命中率:', cache_stats.get('hit_rate', 0))
        
        # 测试批量处理
        print('\n[测试4] 批量处理功能')
        test_posts = []
        for i in range(5):
            test_posts.append({
                'title': '测试帖子' + str(i),
                'content': '这是第' + str(i) + '篇测试内容，用于验证批量处理功能的性能和并发处理能力。',
                'note_id': 'note_' + str(i)
            })
        
        batch_results = ai_utils.batch_summarize(test_posts)
        print('  批量处理完成，处理了', len(batch_results), '篇帖子')
        for i, res in enumerate(batch_results):
            print(f'    帖子{i+1}: {res.get("title", "")} -> {res.get("summary", "")[:30]}...')
        
        print('\n' + '=' * 60)
        print('所有测试完成！')
        print('=' * 60)
        
    except Exception as e:
        print('ERROR:', str(e))
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
