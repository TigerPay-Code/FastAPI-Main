"""
connection_manager.py

FastAPI-friendly high-performance connection pool manager for MySQL (aiomysql) and Redis (aioredis).
"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Optional, Any, List, Tuple, Dict

import aiomysql
import aioredis

logger = logging.getLogger("connection_manager")
logger.setLevel(logging.INFO)


class RetryConfig:
    def __init__(self, attempts: int = 3, base_delay: float = 0.1, max_delay: float = 2.0):
        self.attempts = attempts
        self.base_delay = base_delay
        self.max_delay = max_delay


async def _retry(coro_fn, *args, retry_cfg: Optional[RetryConfig] = None, **kwargs):
    """简单的指数退避重试器"""
    if retry_cfg is None:
        retry_cfg = RetryConfig()
    attempt = 0
    while True:
        try:
            return await coro_fn(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if attempt >= retry_cfg.attempts:
                logger.exception("Retry exhausted")
                raise
            backoff = min(retry_cfg.base_delay * (2 ** (attempt - 1)), retry_cfg.max_delay)
            jitter = backoff * 0.3 * (0.5 - (time.time() % 1))  # small jitter
            sleep_for = max(0.0, backoff + jitter)
            logger.warning("Transient error, retrying %s/%s after %.3fs: %s", attempt, retry_cfg.attempts, sleep_for, e)
            await asyncio.sleep(sleep_for)


class MySQLPoolManager:
    _instance_lock = asyncio.Lock()

    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        self._inited = False

    async def init_pool(
            self,
            host: str,
            port: int,
            user: str,
            password: str,
            db: str,
            minsize: int = 1,
            maxsize: int = 10,
            autocommit: bool = True,
            connect_timeout: int = 10,
            charset: str = "utf8mb4",
    ):
        async with self._instance_lock:
            if self._inited:
                return
            logger.info("Initializing MySQL pool to %s:%s db=%s min=%s max=%s", host, port, db, minsize, maxsize)
            self.pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                db=db,
                minsize=minsize,
                maxsize=maxsize,
                autocommit=autocommit,
                connect_timeout=connect_timeout,
                charset=charset,
            )
            self._inited = True

    async def close(self):
        if self.pool:
            logger.info("Closing MySQL pool")
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            self._inited = False

    def ensure_inited(self):
        if not self._inited or self.pool is None:
            raise RuntimeError("MySQLPoolManager not initialized. Call init_pool first.")

    async def acquire(self):
        """Context manager style acquisition for raw connection"""
        self.ensure_inited()
        conn = await self.pool.acquire()
        try:
            yield_conn = conn
            return yield_conn
        finally:
            self.pool.release(conn)

    # Helper: execute sql (write)
    async def execute(self, sql: str, params: Optional[Tuple] = None, retry_cfg: Optional[RetryConfig] = None) -> int:
        self.ensure_inited()

        async def _do():
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, params or ())
                    # aiomysql returns affected rows via cur.rowcount
                    return cur.rowcount

        return await _retry(_do, retry_cfg=retry_cfg)

    # Helper: fetchone
    async def fetchone(self, sql: str, params: Optional[Tuple] = None, retry_cfg: Optional[RetryConfig] = None) -> \
    Optional[Tuple]:
        self.ensure_inited()

        async def _do():
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(sql, params or ())
                    return await cur.fetchone()

        return await _retry(_do, retry_cfg=retry_cfg)

    # Helper: fetchall
    async def fetchall(self, sql: str, params: Optional[Tuple] = None, retry_cfg: Optional[RetryConfig] = None) -> List[
        Dict]:
        self.ensure_inited()

        async def _do():
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(sql, params or ())
                    return await cur.fetchall()

        return await _retry(_do, retry_cfg=retry_cfg)

    # Helper: transaction context manager
    async def transaction(self):
        """Usage:
            async with mysql_pool.transaction() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(...)
        """
        self.ensure_inited()
        conn = await self.pool.acquire()
        try:
            await conn.begin()
            try:
                yield_conn = conn
                yield yield_conn
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
        finally:
            self.pool.release(conn)

    async def health_check(self) -> bool:
        try:
            row = await self.fetchone("SELECT 1 AS v", retry_cfg=RetryConfig(attempts=2))
            return bool(row and row.get("v") == 1)
        except Exception as e:
            logger.warning("MySQL health check failed: %s", e)
            return False


class RedisPoolManager:
    _instance_lock = asyncio.Lock()

    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
        self._inited = False

    async def init_pool(
            self,
            url: str,
            max_connections: int = 20,
            encoding: Optional[str] = "utf-8",
            decode_responses: bool = True,
            socket_keepalive: bool = True,
            **kwargs,
    ):
        async with self._instance_lock:
            if self._inited:
                return
            logger.info("Initializing Redis client to %s max_connections=%s", url, max_connections)
            # aioredis.from_url returns a redis client with an internal pool
            self.client = await aioredis.from_url(
                url,
                encoding=encoding,
                decode_responses=decode_responses,
                max_connections=max_connections,
                socket_keepalive=socket_keepalive,
                **kwargs,
            )
            # Optionally ping to verify
            try:
                await self.client.ping()
            except Exception:
                logger.exception("Redis ping failed during init")
                # still set inited to True to allow controlled retries later
            self._inited = True

    async def close(self):
        if self.client:
            logger.info("Closing Redis client")
            try:
                await self.client.close()
            except Exception:
                logger.exception("Error closing redis client")
            self.client = None
            self._inited = False

    def ensure_inited(self):
        if not self._inited or self.client is None:
            raise RuntimeError("RedisPoolManager not initialized. Call init_pool first.")

    # simple helpers
    async def get(self, key: str, retry_cfg: Optional[RetryConfig] = None) -> Any:
        self.ensure_inited()
        return await _retry(self.client.get, key, retry_cfg=retry_cfg)

    async def set(self, key: str, value: Any, ex: Optional[int] = None,
                  retry_cfg: Optional[RetryConfig] = None) -> bool:
        self.ensure_inited()
        return await _retry(self.client.set, key, value, ex=ex, retry_cfg=retry_cfg)

    async def delete(self, *keys: str, retry_cfg: Optional[RetryConfig] = None) -> int:
        self.ensure_inited()
        return await _retry(self.client.delete, *keys, retry_cfg=retry_cfg)

    async def health_check(self) -> bool:
        try:
            return await _retry(self.client.ping, retry_cfg=RetryConfig(attempts=2))
        except Exception as e:
            logger.warning("Redis health check failed: %s", e)
            return False


# Singletons
mysql_manager = MySQLPoolManager()
redis_manager = RedisPoolManager()


# FastAPI integration helpers
def register_lifespan_handlers(app, mysql_cfg: dict, redis_cfg: dict):
    """
    Register startup/shutdown events on given FastAPI app.
    mysql_cfg: dict for MySQLPoolManager.init_pool(...)
    redis_cfg: dict for RedisPoolManager.init_pool(...)
    """

    @app.on_event("startup")
    async def _startup():
        # initialize pools concurrently
        logger.info("Starting up connection pools")
        await asyncio.gather(
            mysql_manager.init_pool(**mysql_cfg),
            redis_manager.init_pool(**redis_cfg),
        )
        logger.info("Connection pools ready")

    @app.on_event("shutdown")
    async def _shutdown():
        logger.info("Shutting down connection pools")
        await asyncio.gather(
            mysql_manager.close(),
            redis_manager.close(),
        )
        logger.info("Connection pools closed")


# FastAPI dependency examples
async def get_mysql_conn() -> AsyncGenerator[aiomysql.Connection, None]:
    """
    Yields an aiomysql Connection from the pool.
    Usage in endpoint:
      async def endpoint(conn: aiomysql.Connection = Depends(get_mysql_conn)):
          async with conn.cursor() as cur:
              await cur.execute(...)
    """
    mysql_manager.ensure_inited()
    conn = await mysql_manager.pool.acquire()
    try:
        yield conn
    finally:
        mysql_manager.pool.release(conn)


async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Yields the redis client (has internal pool).
    """
    redis_manager.ensure_inited()
    yield redis_manager.client


# Example simple health-check endpoint helper
async def overall_health() -> Dict[str, bool]:
    mysql_ok = await mysql_manager.health_check()
    redis_ok = await redis_manager.health_check()
    return {"mysql": mysql_ok, "redis": redis_ok}
