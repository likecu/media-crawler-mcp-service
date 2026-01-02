# media-crawler-mcp-service 目录

MCP（Model Context Protocol）服务模块，提供爬虫API服务、数据库管理等功能。

## 文件说明

### app/
- `main.py` - FastAPI主应用入口
- `simple_test.py` - 简单测试脚本
- `test_ai_optimization.py` - AI优化测试
- `test_db_connection.py` - 数据库连接测试
- `test_db_pool.py` - 数据库连接池测试
- `test_incremental_crawler.py` - 增量爬虫测试
- `test_incremental_db.py` - 增量数据库测试
- `test_remote_api.py` - 远程API测试

### app/providers/services/
- `practice_service.py` - 练习服务模块
- `consolidation_service.py` - 数据整合服务

### xhs_crawler/ (核心爬虫模块)
- `cleaners/` - 数据清洗工具
  - `clean_json_files.py` - JSON文件清洗
- `core/` - 核心功能
  - `ai_utils.py` - AI工具函数
  - `base_crawler.py` - 爬虫基类
  - `config.py` - 配置管理
  - `database.py` - 数据库操作
  - `incremental_crawler.py` - 增量爬虫
  - `local_database.py` - 本地数据库
  - `mcp_utils.py` - MCP工具
  - `question_bank.py` - 题库管理
- `crawlers/` - 爬虫实现
  - `leetcode_crawler.py` - LeetCode爬虫
  - `multi_keyword_crawler.py` - 多关键词爬虫
  - `parallel_keyword_crawler.py` - 并行关键词爬虫
  - `simple_xhs_crawler.py` - 简易爬虫
  - `xhs_interview_crawler.py` - 面试帖子爬虫
- `generators/` - 生成器
  - `generate_complete_html.py` - 完整HTML生成
  - `generate_html_from_existing.py` - 从现有数据生成HTML
  - `html_generator.py` - HTML生成器
- `summarizers/` - 总结器
  - `hot_keywords.py` - 热门关键词
  - `summarize_posts.py` - 帖子总结

### 其他目录
- `MediaCrawler/` - 媒体爬虫核心库
- `browser_data/` - 浏览器数据（登录状态等）
- `data/` - 应用数据存储
- `docs/` - 文档目录
- `logs/` - 日志文件
- `migrations/` - 数据库迁移文件

## 配置说明
- `Dockerfile` - Docker构建配置
- `docker-compose.yml` - Docker Compose编排
- `mcp-config.json` - MCP服务配置
- `.env` - 环境变量配置
