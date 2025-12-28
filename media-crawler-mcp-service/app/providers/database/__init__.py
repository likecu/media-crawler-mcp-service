#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接池管理模块
提供高效的数据库连接管理，支持连接池、自动重连和健康检查
"""

from app.providers.database.pool_manager import (
    ConnectionPoolManager,
    PoolConfig,
    get_pool_manager,
    close_pool_manager,
)

__all__ = [
    "ConnectionPoolManager",
    "PoolConfig", 
    "get_pool_manager",
    "close_pool_manager",
]
