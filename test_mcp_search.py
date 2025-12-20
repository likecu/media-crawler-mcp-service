#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MCP服务的搜索功能
"""

import json
import requests

# MCP服务的WebSocket端点
MCP_URL = "http://localhost:9091/mcp"

# 尝试使用不同的端点
ENDPOINTS = [
    "http://localhost:9091/mcp",
    "http://localhost:9091/mcp/",
    "http://localhost:9091/api/mcp/data",
    "http://localhost:9091/api/admin/inspector/execute"
]

def test_mcp_endpoints():
    """测试不同的MCP端点"""
    print("测试不同的MCP端点...")
    
    for endpoint in ENDPOINTS:
        print(f"\n🔍 测试端点: {endpoint}")
        
        try:
            # 构建请求数据
            if "inspector" in endpoint:
                # 调试工具端点
                data = {
                    "tool": "xhs_search",
                    "params": {
                        "keywords": "大模型面试",
                        "page_num": 1,
                        "page_size": 5
                    }
                }
            else:
                # MCP协议端点
                data = {
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "call",
                    "params": {
                        "tool": "xhs_search",
                        "params": {
                            "keywords": "大模型面试",
                            "page_num": 1,
                            "page_size": 5
                        }
                    }
                }
            
            # 发送请求
            response = requests.post(
                endpoint,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📊 状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text[:500]}...")
            
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_mcp_endpoints()
