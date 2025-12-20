#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试小红书搜索功能，查找大模型面试相关内容
直接使用HTTP请求调用MCP服务API，避免版本兼容性问题
"""

import json
import os
import requests
from typing import Any, Dict, List

# 使用虚拟环境中的Python
import sys
print(f"当前Python解释器: {sys.executable}")

def test_xhs_search():
    """测试小红书搜索功能"""
    try:
        # MCP服务API地址
        mcp_url = "http://localhost:9091/mcp"
        
        # 构建MCP请求
        request_data = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "call",
            "params": {
                "tool": "xhs_search",
                "params": {
                    "keywords": "大模型面试",
                    "page_num": 1,
                    "page_size": 10
                }
            }
        }
        
        print("🔍 开始搜索 '大模型面试'...")
        
        # 发送HTTP POST请求
        response = requests.post(
            mcp_url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # 检查响应状态码
        if response.status_code != 200:
            print(f"❌ HTTP请求失败: 状态码 {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        # 解析响应
        result = response.json()
        print(f"\n✅ 搜索结果: {result}")
        
        # 保存搜索结果到文件
        with open("xhs_search_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("\n📁 搜索结果已保存到 xhs_search_results.json")
        
        # 整理搜索结果，将每个帖子保存到独立文件
        print("\n📋 整理搜索结果...")
        
        # 创建保存目录
        save_dir = "大模型面试帖子"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 检查结果结构
        if "result" in result:
            search_result = result["result"]
            if isinstance(search_result, dict) and "notes" in search_result:
                notes = search_result["notes"]
                for i, note in enumerate(notes, 1):
                    # 提取帖子标题作为文件名
                    title = note.get("title", f"帖子{i}")
                    # 清理文件名中的特殊字符
                    clean_title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_')
                    filename = f"{i:03d}_{clean_title}.json"
                    file_path = os.path.join(save_dir, filename)
                    
                    # 保存帖子详情
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(note, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ 保存帖子: {file_path}")
            else:
                print("❌ 搜索结果结构不符合预期")
        else:
            print("❌ 搜索结果中没有result字段")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_xhs_search()
