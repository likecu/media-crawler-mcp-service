#!/bin/bash

echo "=== 启动 Media Crawler MCP 服务 ==="
echo "工作目录: /Volumes/600g/app1/小红书/media-crawler-mcp-service"
echo ""

# 进入项目目录
cd /Volumes/600g/app1/小红书/media-crawler-mcp-service || {
    echo "❌ 无法进入项目目录"
    exit 1
}

# 启动 Docker Compose 服务
echo "🚀 正在启动 Docker Compose 服务..."
docker compose up -d

# 检查启动状态
echo ""
echo "🔍 检查服务状态..."
sleep 5
docker ps --filter name=media-crawler-mcp-service

echo ""
echo "✅ 服务启动完成！"
echo "管理界面: http://localhost:9091/admin"
echo "工具调试: http://localhost:9091/admin/inspector"
echo "MCP SSE 端点: http://localhost:9091/mcp"
echo ""
echo "使用 'docker compose logs -f' 查看日志"
echo "使用 'docker compose down' 停止服务"