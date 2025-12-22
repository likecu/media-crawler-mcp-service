#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于用户提供的psycopg2示例，测试Neon数据库连接
"""

import os
import re
import psycopg2
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def extract_info_from_auth_url(auth_url):
    """
    从VITE_NEON_AUTH_URL提取信息（演示用）
    
    Args:
        auth_url: VITE_NEON_AUTH_URL字符串
        
    Returns:
        dict: 提取的信息，包含endpoint和region
    """
    print(f"📋 从VITE_NEON_AUTH_URL提取信息: {auth_url}")
    
    # 匹配VITE_NEON_AUTH_URL格式
    pattern = r"https://([a-z0-9-]+)\.neonauth\.([a-z0-9-.]+)\.aws\.neon\.tech/neondb/auth"
    match = re.match(pattern, auth_url)
    
    if match:
        endpoint = match.group(1)
        region = match.group(2)
        print(f"✅ 提取成功:")
        print(f"   - Endpoint: {endpoint}")
        print(f"   - Region: {region}")
        return {
            'endpoint': endpoint,
            'region': region
        }
    else:
        print("❌ 无法提取信息，URL格式不匹配")
        return None

def test_database_connection():
    """
    测试数据库连接
    """
    print("🚀 开始测试数据库连接...")
    
    # 从环境变量获取DATABASE_URL
    database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL或NEON_DATABASE_URL环境变量未设置")
        print("\n📝 请在.env文件中添加数据库连接URL:")
        print("例如:")
        print("DATABASE_URL=postgresql://<user>:<password>@<endpoint>.neon.tech:<port>/<database>?sslmode=require")
        print("或")
        print("NEON_DATABASE_URL=postgresql://<user>:<password>@<endpoint>.neon.tech:<port>/<database>?sslmode=require")
        return False
    
    print(f"📋 使用数据库URL: {database_url}")
    
    try:
        # 使用用户提供的示例代码连接数据库
        conn = psycopg2.connect(database_url)
        
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            print(f"✅ 数据库版本: {cur.fetchone()[0]}")
            
            # 执行简单查询，测试连接
            cur.execute("SELECT 1 + 1")
            print(f"✅ 查询测试: 1 + 1 = {cur.fetchone()[0]}")
        
        conn.close()
        print("✅ 数据库连接成功！")
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ 连接数据库失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("🎉 开始执行psycopg2数据库连接测试...")
    
    # 1. 测试从VITE_NEON_AUTH_URL提取信息
    auth_url = os.getenv('VITE_NEON_AUTH_URL')
    if auth_url:
        extract_info_from_auth_url(auth_url)
    else:
        print("⚠️ VITE_NEON_AUTH_URL环境变量未设置")
    
    print()
    
    # 2. 测试数据库连接
    test_database_connection()
    
    print("\n📚 说明:")
    print("1. VITE_NEON_AUTH_URL仅用于Neon Auth认证，不直接包含数据库连接信息")
    print("2. 数据库连接URL需要从Neon控制台获取")
    print("3. 登录Neon控制台(https://console.neon.tech)，选择项目和分支，在'Connection'部分获取完整的数据库连接URL")
    print("4. 将获取的URL添加到.env文件中，使用DATABASE_URL或NEON_DATABASE_URL环境变量")

if __name__ == "__main__":
    main()
