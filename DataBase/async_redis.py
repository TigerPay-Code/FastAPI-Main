#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : async_redis.py
# @Time      : 2025/9/17 15:13
# @IDE       : PyCharm
# @Function  :
import aioredis

class RedisPoolManager:
    def __init__(self):
        self.pool = None

    async def init_pool(self, url: str, max_connections: int = 50):
        if self.pool is None:
            self.pool = await aioredis.from_url(
                url,
                max_connections=max_connections,
                encoding="utf-8",
                decode_responses=True
            )
            print("✅ Redis pool initialized")

    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("🛑 Redis pool closed")

    def ensure_inited(self):
        if self.pool is None:
            raise RuntimeError("RedisPoolManager not initialized. Call init_pool first.")


redis_manager = RedisPoolManager()

# 依赖注入
async def get_redis():
    redis_manager.ensure_inited()
    yield redis_manager.pool
