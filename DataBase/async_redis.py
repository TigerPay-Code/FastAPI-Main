#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : async_redis.py
# @Time      : 2025/9/17 15:13
# @IDE       : PyCharm
# @Function  :
import aioredis
from redis.asyncio import Redis


class RedisPoolManager:
    def __init__(self) -> None:
        self.client: Redis | None = None

    async def init_pool(self, **kwargs) -> None:
        """初始化 Redis 连接池"""
        if self.client is None:
            # 默认参数
            config = {
                "max_connections": 50,
                "encoding": "utf-8",
                "decode_responses": True,
            }
            # 用户配置覆盖默认
            config.update(kwargs)

            self.client = aioredis.from_url(**config)
            # 测试连接
            try:
                await self.client.ping()
            except Exception:
                raise RuntimeError("Redis connection test failed")

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self.client is not None:
            await self.client.close()
            self.client = None

    def ensure_inited(self) -> None:
        if self.client is None:
            raise RuntimeError("RedisManager not initialized. Call init_pool first.")


redis_manager = RedisPoolManager()


# FastAPI 依赖
async def get_redis():
    redis_manager.ensure_inited()
    yield redis_manager.client