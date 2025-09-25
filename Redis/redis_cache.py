from datetime import datetime, date
import decimal

import redis.asyncio as redis
import os
import json
from typing import Optional, Any

from Config.config_loader import public_config
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

# logger.debug("打印调试信息")
# logger.info("打印日志信息")
# logger.warn("打印警告信息")
#
# logger.error("打印错误信息")
# logger.exception("打印异常信息")
#
# logger.critical("打印严重错误信息")

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=public_config.get(key="redis.host", get_type=str),
    port=public_config.get(key="redis.port", get_type=int),
    db=public_config.get(key="redis.db", get_type=int),
    password=public_config.get(key="redis.password", get_type=str),
    decode_responses=True,
    max_connections=20
)


# 自定义 JSON 编码器，处理 Decimal 和其他非标准类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # 将 Decimal 转换为 float 或字符串
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            # 将日期时间对象转换为 ISO 格式字符串
            return obj.isoformat()
        # 让基类处理其他类型
        return super().default(obj)


async def get_redis() -> redis.Redis:
    """获取 Redis 连接"""
    return redis.Redis(connection_pool=redis_pool)

async def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    """设置缓存"""
    try:
        redis_client = await get_redis()
        # 使用自定义编码器序列化数据
        serialized_value = json.dumps(value, cls=CustomJSONEncoder)
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