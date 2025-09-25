import redis.asyncio as redis
import os
import json
from typing import Optional, Any

from Config.config_loader import public_config
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

logger.debug("打印调试信息")
logger.info("打印日志信息")
logger.warn("打印警告信息")

logger.error("打印错误信息")
logger.exception("打印异常信息")

logger.critical("打印严重错误信息")

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=public_config.get(key="redis.host", get_type=str),
    port=public_config.get(key="redis.port", get_type=int),
    db=public_config.get(key="redis.db", get_type=int),
    password=public_config.get(key="redis.password", get_type=str),
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
    except Exception as err:
        logger.error(f"设置缓存失败，错误信息：{err}")
        return False

async def get_cache(key: str) -> Optional[Any]:
    """获取缓存"""
    try:
        redis_client = await get_redis()
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as err:
        logger.error(f"获取缓存失败，错误信息：{err}")
        return None

async def delete_cache(key: str) -> bool:
    """删除缓存"""
    try:
        redis_client = await get_redis()
        await redis_client.delete(key)
        return True
    except Exception as err:
        logger.error(f"删除缓存失败，错误信息：{err}")
        return False