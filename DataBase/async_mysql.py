"""
connection_manager.py

FastAPI-friendly high-performance connection pool manager for MySQL (aiomysql) and Redis (aioredis).
"""
import os
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

import aiomysql


class MySQLPoolManager:
    def __init__(self):
        self.pool = None

    async def init_pool(self, **kwargs):
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                minsize=kwargs.get("minsize", 2),
                maxsize=kwargs.get("maxsize", 20),
                **kwargs
            )
            print("✅ MySQL pool initialized")

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            print("🛑 MySQL pool closed")

    def ensure_inited(self):
        if self.pool is None:
            raise RuntimeError("MySQLPoolManager not initialized. Call init_pool first.")

    async def acquire(self):
        self.ensure_inited()
        return await self.pool.acquire()

    async def release(self, conn):
        self.ensure_inited()
        self.pool.release(conn)


mysql_manager = MySQLPoolManager()


# 依赖注入
async def get_mysql_conn():
    conn = await mysql_manager.acquire()
    try:
        yield conn
    finally:
        await mysql_manager.release(conn)
