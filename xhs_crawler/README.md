# xhs_crawler 目录

小红书爬虫核心模块，提供笔记爬取、数据清洗、HTML生成等功能。

## 文件说明

### cleaners/
- `clean_json_files.py` - JSON数据清洗工具，处理爬取的原始数据

### core/
- `ai_utils.py` - AI工具函数，集成大模型能力
- `base_crawler.py` - 爬虫基类，定义通用爬取接口
- `config.py` - 配置文件管理
- `database.py` - 数据库操作模块
- `local_database.py` - 本地数据库操作
- `mcp_utils.py` - MCP工具函数
- `question_bank.py` - 题库管理模块

### crawlers/
- `leetcode_crawler.py` - LeetCode题目爬取
- `multi_keyword_crawler.py` - 多关键词爬取
- `parallel_keyword_crawler.py` - 并行关键词爬取
- `simple_xhs_crawler.py` - 简易小红书爬虫
- `xhs_interview_crawler.py` - 小红书面试帖子爬虫

### generators/
- `generate_complete_html.py` - 生成完整HTML报告
- `generate_html_from_existing.py` - 从现有数据生成HTML
- `html_generator.py` - HTML生成器

### summarizers/
- `hot_keywords.py` - 热门关键词分析
- `summarize_posts.py` - 帖子总结生成

### 其他
- `test_parallel_crawler.py` - 并行爬虫测试
