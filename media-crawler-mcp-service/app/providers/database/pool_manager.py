#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接池管理模块
提供高效的数据库连接池管理，支持连接失败自动重连、连接复用和健康检查
"""

import asyncio
import asyncpg
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
import logging

from app.config.settings import global_settings

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """连接池配置"""
    max_size: int = 10
    min_size: int = 1
    command_timeout: float = 30.0
    max_inactive_connection_lifetime: float = 300.0
    keepalives_idle: int = 300
    keepalives_interval: int = 30
    keepalives_count: int = 3


class ConnectionPoolManager:
    """
    数据库连接池管理器
    
    提供：
    - 高效的连接池管理
    - 连接失败自动重连
    - 连接健康检查
    - 异步上下文管理器支持
    """
    
    _instance: Optional['ConnectionPoolManager'] = None
    _pool: Optional[asyncpg.Pool] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConnectionPoolManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化连接池管理器"""
        if not hasattr(self, '_initialized'):
            self._config = PoolConfig(
                max_size=global_settings.database.maxsize,
                min_size=global_settings.database.minsize,
                command_timeout=30.0,
                max_inactive_connection_lifetime=300.0,
                keepalives_idle=300,
                keepalives_interval=30,
                keepalives_count=3
            )
            self._last_health_check: Optional[datetime] = None
            self._pool_stats: Dict[str, Any] = {}
            self._initialized = True
    
    async def initialize(self) -> bool:
        """
        初始化连接池
        
        Returns:
            bool: 初始化是否成功
        """
        if self._pool is not None:
            logger.info("连接池已初始化，跳过重复初始化")
            return True
        
        try:
            db_config = global_settings.database
            
            self._pool = await asyncpg.create_pool(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
                max_size=self._config.max_size,
                min_size=self._config.min_size,
                command_timeout=self._config.command_timeout,
                max_inactive_connection_lifetime=self._config.max_inactive_connection_lifetime,
                server_settings={
                    'application_name': global_settings.app.name,
                    'tcp_keepalives_idle': str(self._config.keepalives_idle),
                    'tcp_keepalives_interval': str(self._config.keepalives_interval),
                    'tcp_keepalives_count': str(self._config.keepalives_count),
                }
            )
            
            await self._check_connection()
            logger.info(f"✅ 数据库连接池初始化成功: {db_config.host}:{db_config.port}/{db_config.database}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库连接池初始化失败: {e}")
            return False
    
    async def _check_connection(self) -> bool:
        """
        检查数据库连接健康状态
        
        Returns:
            bool: 连接是否健康
        """
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            self._last_health_check = datetime.now()
            return True
        except Exception as e:
            logger.error(f"数据库连接健康检查失败: {e}")
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            asyncpg.Connection: 数据库连接对象
        
        Example:
            async with pool_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")
        """
        if self._pool is None:
            await self.initialize()
        
        if self._pool is None:
            raise RuntimeError("数据库连接池未初始化")
        
        connection = None
        try:
            connection = await self._pool.acquire()
            yield connection
        finally:
            if connection is not None:
                await self._pool.release(connection)
    
    async def execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> asyncpg.Record:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            timeout: 超时时间(秒)
        
        Returns:
            asyncpg.Record: 查询结果
        
        Raises:
            Exception: 查询执行失败
        """
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def execute_many(
        self,
        query: str,
        args_list: List[tuple],
        timeout: Optional[float] = None
    ) -> None:
        """
        批量执行SQL查询
        
        Args:
            query: SQL查询语句
            args_list: 参数列表
            timeout: 超时时间(秒)
        """
        async with self.get_connection() as conn:
            await conn.executemany(query, args_list, timeout=timeout)
    
    async def fetch_all(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """
        获取所有查询结果
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            timeout: 超时时间(秒)
        
        Returns:
            List[asyncpg.Record]: 结果列表
        """
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetch_one(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> Optional[asyncpg.Record]:
        """
        获取单条查询结果
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            timeout: 超时时间(秒)
        
        Returns:
            Optional[asyncpg.Record]: 结果或None
        """
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def insert(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> int:
        """
        执行插入操作并返回插入的ID
        
        Args:
            query: SQL插入语句
            *args: 插入参数
            timeout: 超时时间(秒)
        
        Returns:
            int: 插入的记录ID
        """
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        获取连接池状态
        
        Returns:
            Dict: 连接池状态信息
        """
        if self._pool is None:
            return {
                "initialized": False,
                "message": "连接池未初始化"
            }
        
        return {
            "initialized": True,
            "max_size": self._config.max_size,
            "min_size": self._config.min_size,
            "size": self._pool.get_size() if hasattr(self._pool, 'get_size') else "unknown",
            "idle_size": self._pool.get_idle_size() if hasattr(self._pool, 'get_idle_size') else "unknown",
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
        }
    
    async def health_check(self) -> bool:
        """
        执行健康检查
        
        Returns:
            bool: 连接是否健康
        """
        return await self._check_connection()
    
    async def close(self) -> None:
        """
        关闭连接池
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("✅ 数据库连接池已关闭")
    
    async def reconnect(self) -> bool:
        """
        重新连接数据库
        
        Returns:
            bool: 重连是否成功
        """
        await self.close()
        return await self.initialize()


async def get_pool_manager() -> ConnectionPoolManager:
    """
    获取连接池管理器实例
    
    Returns:
        ConnectionPoolManager: 连接池管理器实例
    """
    manager = ConnectionPoolManager()
    if manager._pool is None:
        await manager.initialize()
    return manager


async def close_pool_manager() -> None:
    """
    关闭连接池管理器
    """
    manager = ConnectionPoolManager()
    await manager.close()
