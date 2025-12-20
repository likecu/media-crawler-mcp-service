#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试脚本：测试小红书搜索功能
"""

import json
import requests
import time
import os

# 调试工具端点
INSPECTOR_URL = "http://localhost:9091/api/admin/inspector/execute"

# 结果保存目录
OUTPUT_DIR = "大模型面试帖子"

def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✅ 创建输出目录: {OUTPUT_DIR}")

def test_xhs_search():
    """测试小红书搜索功能"""
    print("🔍 测试小红书搜索功能...")
    ensure_output_dir()
    
    # 构建请求数据
    data = {
        "tool": "xhs_search",
        "params": {
            "keywords": "大模型面试",
            "page_num": 1,
            "page_size": 10
        }
    }
    
    try:
        # 发送请求
        response = requests.post(
            INSPECTOR_URL,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        # 解析响应
        result = response.json()
        print(f"📝 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 保存原始响应
        with open(os.path.join(OUTPUT_DIR, "原始响应.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("✅ 保存原始响应到文件")
        
        # 检查结果
        if "result" in result:
            search_result = result["result"]
            print(f"\n📋 搜索结果: {search_result}")
            
            # 尝试获取笔记列表
            if isinstance(search_result, dict):
                if "data" in search_result and isinstance(search_result["data"], dict):
                    # 检查不同的结果结构
                    if "notes" in search_result["data"]:
                        notes = search_result["data"]["notes"]
                        print(f"✅ 找到 {len(notes)} 篇笔记")
                        
                        # 保存每篇笔记
                        for i, note in enumerate(notes, 1):
                            # 提取标题
                            title = note.get("title", f"帖子{i}")
                            # 清理文件名
                            clean_title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_')
                            filename = f"{i:03d}_{clean_title}.json"
                            file_path = os.path.join(OUTPUT_DIR, filename)
                            
                            with open(file_path, "w", encoding="utf-8") as f:
                                json.dump(note, f, ensure_ascii=False, indent=2)
                            print(f"✅ 保存帖子: {file_path}")
                    else:
                        print("❌ 搜索结果中没有找到笔记列表")
                elif "msg" in search_result:
                    print(f"❌ 搜索失败: {search_result['msg']}")
                else:
                    print("❌ 搜索结果结构不符合预期")
            else:
                print(f"❌ 搜索结果类型不符合预期: {type(search_result)}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 启动小红书搜索测试")
    
    # 尝试多次，直到成功或达到最大尝试次数
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\n📌 尝试 {attempt}/{max_attempts}")
        test_xhs_search()
        
        # 检查是否有结果文件生成
        if len(os.listdir(OUTPUT_DIR)) > 1:  # 至少有一个结果文件（除了原始响应）
            print("\n🎉 测试成功！")
            break
        
        if attempt < max_attempts:
            print(f"⏳ 等待 5 秒后重试...")
            time.sleep(5)
    
    print("\n📊 测试完成！")
    print(f"📁 结果保存目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"📄 目录内容: {os.listdir(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()
