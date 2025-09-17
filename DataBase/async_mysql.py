"""
connection_manager.py

FastAPI-friendly high-performance connection pool manager for MySQL (aiomysql) and Redis (aioredis).
"""
import os
import aiomysql
from aiomysql import Pool as MySQLPool
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)


class MySQLPoolManager:
    def __init__(self) -> None:
        self.pool: MySQLPool | None = None

    async def init_pool(self, **kwargs) -> None:
        """初始化 MySQL 连接池"""
        if self.pool is None:
            # 默认参数
            config = {
                "minsize": 2,
                "maxsize": 20,
                "autocommit": True,
            }
            # 用户配置覆盖默认
            config.update(kwargs)

            self.pool = await aiomysql.create_pool(**config)
            # 测试连接
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")

    async def close(self) -> None:
        """关闭连接池"""
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    def ensure_inited(self) -> None:
        """确认连接池已初始化"""
        if self.pool is None:
            raise RuntimeError("MySQLPoolManager not initialized. Call init_pool first.")

    async def acquire(self):
        """获取一个连接"""
        self.ensure_inited()
        assert self.pool is not None
        return await self.pool.acquire()

    async def release(self, conn) -> None:
        """释放连接"""
        if self.pool is not None:
            self.pool.release(conn)


mysql_manager = MySQLPoolManager()


# FastAPI 依赖
async def get_mysql_conn():
    conn = await mysql_manager.acquire()
    try:
        yield conn
    finally:
        await mysql_manager.release(conn)
