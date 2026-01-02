# media-crawler-mcp-service/app 目录

MCP服务的应用模块，包含FastAPI服务入口和业务逻辑。

## 文件说明
- `main.py` - FastAPI主应用入口
- `simple_test.py` - 简单功能测试脚本
- `test_ai_optimization.py` - AI优化功能测试
- `test_db_connection.py` - 数据库连接测试
- `test_db_pool.py` - 数据库连接池测试
- `test_incremental_crawler.py` - 增量爬虫功能测试
- `test_incremental_db.py` - 增量数据库功能测试
- `test_remote_api.py` - 远程API测试

## 子目录
- `providers/services/` - 业务服务层
  - `practice_service.py` - 练习服务，处理刷题相关业务
  - `consolidation_service.py` - 数据整合服务，处理数据汇总和清洗
