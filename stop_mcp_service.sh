#!/bin/bash

echo "=== 停止 Media Crawler MCP 服务 ==="
echo "工作目录: /Volumes/600g/app1/小红书/media-crawler-mcp-service"
echo ""

# 进入项目目录
cd /Volumes/600g/app1/小红书/media-crawler-mcp-service || {
    echo "❌ 无法进入项目目录"
    exit 1
}

# 停止 Docker Compose 服务
echo "🛑 正在停止 Docker Compose 服务..."
docker compose down

# 检查停止状态
echo ""
echo "🔍 检查服务状态..."
sleep 2
docker ps --filter name=media-crawler-mcp-service

echo ""
echo "✅ 服务已停止！"