#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务测试脚本
演示如何连接和使用MediaCrawler MCP服务
"""

import requests
import json

def test_mcp_service():
    """
    测试MCP服务的基本功能
    
    Returns:
        bool: 服务是否正常运行
    """
    base_url = "http://localhost:9091"
    
    print("=== 测试MCP服务 ===")
    print(f"服务地址: {base_url}")
    print()
    
    try:
        # 1. 获取MCP工具列表
        print("1. 获取MCP工具列表...")
        response = requests.get(f"{base_url}/api/mcp/data")
        response.raise_for_status()
        data = response.json()
        
        print(f"   成功获取工具列表")
        print(f"   可用工具数: {len(data['tools']['tools'])}")
        print(f"   可用提示数: {len(data['prompts']['prompts'])}")
        print(f"   可用资源数: {len(data['resources']['resources'])}")
        print()
        
        # 2. 显示可用工具
        print("2. 可用工具列表:")
        for tool in data['tools']['tools']:
            print(f"   - {tool['platform']}_{tool['name']}: {tool['description']}")
        print()
        
        # 3. 显示管理界面地址
        print("3. 访问地址:")
        print(f"   管理界面: {base_url}/admin")
        print(f"   工具调试: {base_url}/admin/inspector")
        print(f"   MCP端点: {base_url}/mcp")
        print()
        
        # 4. 测试服务健康状态
        print("4. 测试服务健康状态...")
        # 尝试访问一个简单的端点
        response = requests.get(f"{base_url}/inspector")
        if response.status_code == 200:
            print("   ✅ 服务健康状态: 正常")
        else:
            print(f"   ❌ 服务健康状态: 异常 (状态码: {response.status_code})")
        print()
        
        print("=== 测试完成 ===")
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 无法连接到服务: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def example_xhs_search():
    """
    演示小红书搜索工具的使用示例
    """
    print("\n=== 小红书搜索工具使用示例 ===")
    print("使用方法:")
    print("1. 通过MCP客户端连接到服务")
    print("2. 调用工具: xhs_search")
    print("3. 参数示例:")
    example_params = {
        "keywords": "咖啡",
        "page_num": 1,
        "page_size": 10
    }
    print(json.dumps(example_params, indent=2, ensure_ascii=False))
    print()
    print("4. 响应示例:")
    print("   返回结构化的小红书笔记列表，包含标题、作者、互动数据等")

if __name__ == "__main__":
    success = test_mcp_service()
    if success:
        example_xhs_search()
    else:
        print("服务未正常运行，请检查Docker容器状态")
