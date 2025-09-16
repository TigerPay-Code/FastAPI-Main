#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : mysql.py
# @Time      : 2025/9/16 12:09
# @IDE       : PyCharm
# @Function  :
import aiomysql
import redis.asyncio as aioredis
from typing import Optional, AsyncGenerator
from redis.asyncio.client import Redis
from aiomysql import Pool
from contextlib import asynccontextmanager

mysql_pool: Optional[Pool] = None
redis_client: Optional[Redis] = None


# 使用异步上下文管理器来管理连接池的生命周期
@asynccontextmanager
async def lifespan_manager():
    global mysql_pool, redis_client

    # --- 应用启动时执行 ---
    try:
        mysql_pool = await aiomysql.create_pool(
            host='localhost',
            user='root',
            password='123456',
            db='test',
            autocommit=False,
            loop=None,
            charset='utf8mb4',
            maxsize=10
        )
        print("MySQL pool initialized successfully.")
    except Exception as e:
        print(f"Error initializing MySQL pool: {e}")

    try:
        redis_client = aioredis.from_url(
            f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
            decode_responses=True
        )
        await redis_client.ping()
        print("Redis client connected successfully.")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")

    # 使用 `yield` 将控制权交给 FastAPI 应用程序
    yield

    # --- 应用关闭时执行 ---
    if mysql_pool:
        mysql_pool.close()
        await mysql_pool.wait_closed()
        print("MySQL pool closed.")
    if redis_client:
        await redis_client.close()
        print("Redis client closed.")
