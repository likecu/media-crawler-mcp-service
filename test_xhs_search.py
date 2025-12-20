#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书搜索功能，查找大模型面试相关内容
"""

import asyncio
import json
import os
from typing import Any, Dict, List

# 使用虚拟环境中的Python
import sys
print(f"当前Python解释器: {sys.executable}")

# 安装mcp库
os.system("/Volumes/600g/app1/okx-py/bin/python3 -m pip install fastmcp")

from fastmcp.client import FastMCPAsyncClient

async def test_xhs_search():
    """测试小红书搜索功能"""
    try:
        # 创建MCP客户端
        client = FastMCPAsyncClient(
            server_url="http://localhost:9091/mcp",
            timeout=30
        )
        
        # 连接到MCP服务
        await client.connect()
        print("✅ 成功连接到MCP服务")
        
        # 获取所有可用工具
        tools = await client.list_tools()
        print(f"\n📋 可用工具: {[tool.name for tool in tools]}")
        
        # 调用小红书搜索工具
        print("\n🔍 开始搜索 '大模型面试'...")
        result = await client.call_tool(
            tool_name="xhs_search",
            tool_params={
                "keywords": "大模型面试",
                "page_num": 1,
                "page_size": 10
            }
        )
        
        print(f"\n✅ 搜索结果: {result}")
        
        # 保存搜索结果到文件
        with open("xhs_search_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n📁 搜索结果已保存到 xhs_search_results.json")
        
        # 关闭连接
        await client.disconnect()
        print("\n🔌 已断开MCP服务连接")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_xhs_search())
