#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接池功能
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.database.pool_manager import (
    get_pool_manager, 
    close_pool_manager,
    ConnectionPoolManager
)


async def test_connection_pool():
    """
    测试数据库连接池功能
    
    Returns:
        bool: 测试是否成功
    """
    print("=" * 60)
    print("🧪 开始测试数据库连接池...")
    print("=" * 60)
    
    try:
        # 1. 测试连接池初始化
        print("\n📋 测试 1: 连接池初始化")
        pool_manager = await get_pool_manager()
        print("✅ 连接池管理器获取成功")
        
        # 2. 测试连接池状态
        print("\n📋 测试 2: 获取连接池状态")
        status = await pool_manager.get_pool_status()
        print(f"✅ 连接池状态: {status}")
        
        # 3. 测试数据库连接健康检查
        print("\n📋 测试 3: 健康检查")
        is_healthy = await pool_manager.health_check()
        print(f"✅ 健康检查结果: {is_healthy}")
        
        # 4. 测试简单查询
        print("\n📋 测试 4: 执行简单查询")
        async with pool_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT 1 + 1")
            print(f"✅ 简单查询结果: 1 + 1 = {result}")
        
        # 5. 测试获取多条记录
        print("\n📋 测试 5: 执行批量查询")
        async with pool_manager.get_connection() as conn:
            records = await conn.fetch("SELECT NOW() as current_time, version() as version")
            if records:
                print(f"✅ 批量查询成功，时间: {records[0]['current_time']}")
        
        # 6. 测试并发连接
        print("\n📋 测试 6: 并发连接测试")
        async def concurrent_query(task_id: int):
            async with pool_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                return f"任务 {task_id} 完成"
        
        tasks = [concurrent_query(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        print(f"✅ 并发测试完成: {len(results)} 个任务全部成功")
        
        # 7. 测试连接池统计
        print("\n📋 测试 7: 连接池统计")
        final_status = await pool_manager.get_pool_status()
        print(f"✅ 最终状态: {final_status}")
        
        print("\n" + "=" * 60)
        print("🎉 所有连接池测试通过!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n📋 清理连接池...")
        await close_pool_manager()
        print("✅ 连接池已关闭")


async def test_connection_retry():
    """
    测试连接重试机制
    
    Returns:
        bool: 测试是否成功
    """
    print("\n" + "=" * 60)
    print("🧪 测试连接重试机制...")
    print("=" * 60)
    
    try:
        pool_manager = ConnectionPoolManager()
        
        # 首次初始化
        success1 = await pool_manager.initialize()
        print(f"✅ 首次连接: {success1}")
        
        # 模拟断开后重连
        await pool_manager.close()
        success2 = await pool_manager.reconnect()
        print(f"✅ 重连测试: {success2}")
        
        await pool_manager.close()
        
        print("✅ 连接重试测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 重试测试失败: {e}")
        return False


async def main():
    """
    主测试函数
    """
    print("\n🚀 数据库连接池测试开始\n")
    
    # 运行所有测试
    test1_passed = await test_connection_pool()
    test2_passed = await test_connection_retry()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"连接池功能测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"连接重试测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    all_passed = test1_passed and test2_passed
    print(f"\n总体结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
