import redis.asyncio as redis
import os
import json
from typing import Optional, Any

# Redis 连接配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
    max_connections=20
)

async def get_redis() -> redis.Redis:
    """获取 Redis 连接"""
    return redis.Redis(connection_pool=redis_pool)

async def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    """设置缓存"""
    try:
        redis_client = await get_redis()
        await redis_client.setex(key, expire, json.dumps(value))
        return True
    except Exception:
        return False

async def get_cache(key: str) -> Optional[Any]:
    """获取缓存"""
    try:
        redis_client = await get_redis()
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        return None

async def delete_cache(key: str) -> bool:
    """删除缓存"""
    try:
        redis_client = await get_redis()
        await redis_client.delete(key)
        return True
    except Exception:
        return False