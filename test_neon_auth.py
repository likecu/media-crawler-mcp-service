#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试VITE_NEON_AUTH_URL的可访问性和文件上传下载功能
"""

import os
import requests
from dotenv import load_dotenv
from xhs_crawler.core.database import get_neon_database

# 加载.env文件
load_dotenv()

def test_vite_neon_auth_url():
    """
    测试VITE_NEON_AUTH_URL的可访问性
    
    Returns:
        bool: URL是否可访问
    """
    print("🚀 开始测试VITE_NEON_AUTH_URL...")
    
    # 从环境变量获取URL
    auth_url = os.getenv('VITE_NEON_AUTH_URL')
    if not auth_url:
        print("❌ VITE_NEON_AUTH_URL环境变量未设置")
        return False
    
    print(f"📋 测试URL: {auth_url}")
    
    try:
        # 发送GET请求测试URL可访问性
        response = requests.get(auth_url, timeout=5)
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 500:
            # 2xx: 成功访问
            # 4xx: 客户端错误，但URL本身是可访问的
            print("✅ VITE_NEON_AUTH_URL可访问")
            return True
        else:
            print(f"⚠️ VITE_NEON_AUTH_URL返回意外状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法访问VITE_NEON_AUTH_URL: {e}")
        return False

def create_sample_html_file():
    """
    创建示例HTML文件用于测试
    
    Returns:
        str: 示例HTML文件路径
    """
    print("\n📄 创建示例HTML文件...")
    
    # 创建示例HTML内容
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试页面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>测试页面</h1>
        <p>这是一个用于测试Neon数据库文件上传下载功能的示例HTML文件。</p>
        <p>文件创建时间: 2025-12-22</p>
    </div>
</body>
</html>
    """
    
    # 写入文件
    sample_file_path = "sample_test.html"
    with open(sample_file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ 示例HTML文件已创建: {sample_file_path}")
    return sample_file_path

def test_file_upload_download():
    """
    测试文件上传下载功能
    
    Returns:
        bool: 测试是否成功
    """
    print("\n📤📥 开始测试文件上传下载功能...")
    
    # 获取数据库实例
    db = get_neon_database()
    if not db:
        print("⚠️  无法创建数据库实例，跳过文件上传下载测试")
        return False
    
    try:
        # 创建示例HTML文件
        sample_file = create_sample_html_file()
        
        # 测试内容直接上传
        print(f"\n📤 直接上传HTML内容...")
        # 读取文件内容
        with open(sample_file, 'r', encoding='utf-8') as f:
            sample_content = f.read()
        upload_success = db.upload_content("sample_test.html", sample_content, "html", "test_hashid")
        if not upload_success:
            print("❌ 内容上传失败")
            return False
        
        # 测试获取文件列表
        print("\n📋 获取文件列表:")
        files = db.get_all_files()
        for file in files:
            print(f"   - {file['filename']} ({file['file_type']})")
        
        # 测试文件下载
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        download_path = os.path.join(download_dir, sample_file)
        
        print(f"\n📥 下载文件到: {download_path}")
        download_success = db.download_file(sample_file, download_path)
        if not download_success:
            print("❌ 文件下载失败")
            return False
        
        # 验证文件内容一致性
        print("\n🔍 验证文件内容一致性...")
        with open(sample_file, 'r', encoding='utf-8') as f1, open(download_path, 'r', encoding='utf-8') as f2:
            original_content = f1.read()
            downloaded_content = f2.read()
            
        if original_content == downloaded_content:
            print("✅ 文件内容一致")
        else:
            print("❌ 文件内容不一致")
            return False
        
        # 清理测试文件
        os.remove(sample_file)
        os.remove(download_path)
        os.rmdir(download_dir)
        
        print("✅ 文件上传下载测试通过")
        return True
    finally:
        # 关闭数据库连接
        db.close()

def main():
    """
    主测试函数
    """
    print("🎉 开始完整测试...")
    
    # 测试VITE_NEON_AUTH_URL
    auth_url_test = test_vite_neon_auth_url()
    
    # 测试文件上传下载
    file_test = test_file_upload_download()
    
    print("\n📊 测试结果汇总:")
    print(f"   VITE_NEON_AUTH_URL可访问性: {'✅ 成功' if auth_url_test else '❌ 失败'}")
    print(f"   文件上传下载功能: {'✅ 成功' if file_test else '❌ 失败'}")
    
    if auth_url_test and file_test:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    main()
