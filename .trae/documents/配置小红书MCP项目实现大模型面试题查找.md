# 配置小红书MCP项目实现大模型面试题查找

## 项目选择

选择 `media-crawler-mcp-service` 项目，原因：

* 基于Python技术栈，符合用户使用虚拟环境Python的要求

* 提供完善的MCP服务，可直接被AI调用

* 支持小红书搜索功能，适合查找面试题目

* 数据格式适合AI分析

* 安装和配置相对简单

## 配置步骤

### 1. 克隆项目到当前目录

```bash
git clone https://github.com/mcp-service/media-crawler-mcp-service.git
cd media-crawler-mcp-service
```

### 2. 使用虚拟环境安装依赖

```bash
# 确保使用用户提供的虚拟环境Python
/Volumes/600g/app1/okx-py/bin/python3 -m pip install poetry
poetry install
poetry run playwright install chromium
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 根据需要修改配置，主要是Redis连接和端口设置
```

### 4. 启动Redis服务

```bash
# 如果Redis未安装，先安装
brew install redis
# 启动Redis服务
redis-server --daemonize yes
```

### 5. 启动MCP服务

```bash
# 使用虚拟环境Python启动服务
/Volumes/600g/app1/okx-py/bin/python3 main.py
```

### 6. 测试小红书搜索功能

* 打开管理界面：<http://localhost:9090/admin>

* 进入"登录管理"，选择小红书平台进行登录

* 进入"工具调试"，使用`xhs_search`工具搜索"大模型面试"测试功能

### 7. 实现面试题查找和整理

* 使用AI助手连接MCP服务（SSE端点：<http://localhost:9090/mcp）>

* 调用`xhs_search`工具搜索"大模型面试"相关内容

* 对搜索结果进行筛选和整理

* 将每个相关帖子保存到独立文件，存放在指定文件夹

## 预期结果

* MCP服务成功启动，可正常访问管理界面

* 小红书登录状态持久化，可正常进行搜索

* 能够通过MCP服务查找到大模型面试相关帖子

* 所有相关帖子被整理成独立文件，存放在指定文件夹

## 注意事项

* 遵守小红书平台的使用条款，合理设置请求频率

* 定期检查登录状态，确保服务正常运行

* 注意数据备份，避免丢失重要信息

