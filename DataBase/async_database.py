#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : async_database.py
# @Time      : 2025/10/9 11:14
# @IDE       : PyCharm
# @Function  :
# async_database.py
# 统一的异步数据库 + 缓存组件（aiomysql + redis.asyncio）
# 适用于 FastAPI 异步环境

import asyncio
import time
import json
from typing import Any, Optional, Callable, Iterable
import aiomysql
import aioredis
from redis.asyncio import Redis
from contextlib import asynccontextmanager


# ----------------- 日志配置 -----------------
import os
from Logger.logger_config import setup_logger
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)
# -------------------------------------------


# 如果你的项目有配置加载器，请改为从 config_loader 导入 public_config
try:
    from Config.config_loader import public_config
except ImportError:
    # fallback - 开发/测试时可以替换为硬编码
    logger.error("模块 Config.config_loader 未找到或 public_config 未定义，将 public_config 设置为 None")
    public_config = None

# ---------- 日志 ----------
import os
from Logger.logger_config import setup_logger
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)


# ---------- 异步 MySQL 管理 ----------
class AsyncMySQL:
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        self._init_lock = asyncio.Lock()

    async def init_pool(self, **kwargs):
        """初始化 MySQL 连接池（幂等）"""
        async with self._init_lock:
            if self.pool is not None:
                return
            config = {
                "minsize": 2,
                "maxsize": 20,
                "autocommit": True,
            }
            config.update(kwargs)
            logger.info("初始化 MySQL 连接池...")
            self.pool = await aiomysql.create_pool(**config)
            # 测试连接
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
            logger.info("MySQL 连接池就绪")

    async def close(self):
        if self.pool is not None:
            logger.info("关闭 MySQL 连接池...")
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("MySQL 连接池已关闭")

    def ensure_inited(self):
        if self.pool is None:
            raise RuntimeError("MySQL pool not initialized. Call init_pool first.")

    @asynccontextmanager
    async def acquire(self):
        """上下文方式获取连接"""
        self.ensure_inited()
        assert self.pool is not None
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            # release 回收连接
            self.pool.release(conn)

    # 便利方法
    async def fetchone(self, sql: str, args: Optional[Iterable] = None, dict_cursor: bool = True):
        async with self.acquire() as conn:
            cursor_factory = aiomysql.DictCursor if dict_cursor else None
            async with conn.cursor(cursor_factory) as cur:
                await cur.execute(sql, args or ())
                return await cur.fetchone()

    async def fetchall(self, sql: str, args: Optional[Iterable] = None, dict_cursor: bool = True):
        async with self.acquire() as conn:
            cursor_factory = aiomysql.DictCursor if dict_cursor else None
            async with conn.cursor(cursor_factory) as cur:
                await cur.execute(sql, args or ())
                return await cur.fetchall()

    async def execute(self, sql: str, args: Optional[Iterable] = None):
        """执行写操作（INSERT/UPDATE/DELETE）；返回受影响行数"""
        async with self.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, args or ())
                # 注意：如果 autocommit=False，你需要手动 commit
                return cur.rowcount

    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器：async with db.transaction():"""
        self.ensure_inited()
        assert self.pool is not None
        conn = await self.pool.acquire()
        try:
            await conn.begin()
            try:
                yield conn
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
        finally:
            self.pool.release(conn)


# ---------- 异步 Redis 管理 ----------
class AsyncRedis:
    def __init__(self):
        self.client: Optional[Redis] = None
        self._init_lock = asyncio.Lock()

    async def init_pool(self, url: Optional[str] = None, **kwargs):
        """初始化 Redis 客户端；支持 from_url 或 host/port/db 形式"""
        async with self._init_lock:
            if self.client is not None:
                return
            logger.info("初始化 Redis 客户端...")
            # 如果传入 url 则优先使用
            if url:
                self.client = aioredis.from_url(url, **kwargs)
            else:
                # 允许通过 host/port/db/password 等 kwargs 构建 url
                self.client = aioredis.from_url(**kwargs)
            # 测试连接
            try:
                await self.client.ping()
            except Exception as e:
                logger.exception("Redis ping 失败")
                raise RuntimeError("Redis connection failed") from e
            logger.info("Redis 客户端就绪")

    async def close(self):
        if self.client is not None:
            logger.info("关闭 Redis 客户端...")
            await self.client.close()
            self.client = None
            logger.info("Redis 客户端已关闭")

    def ensure_inited(self):
        if self.client is None:
            raise RuntimeError("Redis client not initialized. Call init_pool first.")

    # 简单封装
    async def get(self, key: str):
        self.ensure_inited()
        return await self.client.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        self.ensure_inited()
        # 自动将 dict/list/非 str 序列化为 json
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value, default=str, ensure_ascii=False)
        return await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        self.ensure_inited()
        return await self.client.delete(key)

    async def exists(self, key: str):
        self.ensure_inited()
        return await self.client.exists(key)

    # 分布式锁（简单实现）
    async def acquire_lock(self, lock_key: str, lock_ttl: int = 10) -> bool:
        """
        尝试获取锁（非阻塞）。返回 True/False。
        基于 SET NX EX。
        """
        self.ensure_inited()
        # redis-py 采用 set(name, value, nx=True, ex=lock_ttl)
        return await self.client.set(lock_key, "1", nx=True, ex=lock_ttl)

    async def release_lock(self, lock_key: str):
        self.ensure_inited()
        await self.client.delete(lock_key)


# ---------- 缓存装饰器：自动缓存查询结果（支持防穿透锁） ----------
def cached(key_builder: Callable[..., str], ttl: int = 60, null_ttl: int = 5, lock_ttl: int = 5):
    """
    使用方法示例：
    @cached(lambda user_id: f"user:{user_id}", ttl=60)
    async def load_user(user_id): ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存 key（允许 key_builder 使用 args/kwargs）
            try:
                cache_key = key_builder(*args, **kwargs)
            except Exception:
                # 如果 key 构建失败，直接调用函数
                return await func(*args, **kwargs)

            redis = ASYNC_DB.redis  # 访问单例（见下）
            # 1. 尝试取缓存
            raw = await redis.get(cache_key)
            if raw is not None:
                # 如果是 bytes -> decode
                if isinstance(raw, (bytes, bytearray)):
                    try:
                        raw = raw.decode()
                    except Exception:
                        pass
                # 尝试 json 反序列化
                try:
                    return json.loads(raw)
                except Exception:
                    return raw

            lock_key = cache_key + ":lock"
            # 2. 获取分布式锁，防止缓存击穿
            got = await redis.acquire_lock(lock_key, lock_ttl=lock_ttl)
            if not got:
                # 等待锁释放后再读取缓存（自旋 + 超时）
                wait_start = time.time()
                while time.time() - wait_start < (lock_ttl + 0.5):
                    await asyncio.sleep(0.05)
                    raw = await redis.get(cache_key)
                    if raw is not None:
                        try:
                            return json.loads(raw)
                        except Exception:
                            return raw
                # 超时仍无缓存，则回退调用函数
                return await func(*args, **kwargs)

            # 我们获取到锁 -> 调用函数并写回缓存
            try:
                result = await func(*args, **kwargs)
                if result is None:
                    # 防穿透短期缓存
                    await redis.set(cache_key, json.dumps(None), ex=null_ttl)
                else:
                    await redis.set(cache_key, result, ex=ttl)
                return result
            finally:
                await redis.release_lock(lock_key)

        return wrapper
    return decorator


# ---------- 统一入口单例 ----------
ASYNC_DB = type("ASyncDBHolder", (), {})()
ASYNC_DB.mysql = AsyncMySQL()
ASYNC_DB.redis = AsyncRedis()

# ---------- 便捷导出（方便在项目中 import 使用） ----------
mysql_manager = ASYNC_DB.mysql
redis_manager = ASYNC_DB.redis

# ---------- 从配置文件自动初始化（可选） ----------
def _maybe_auto_init():
    """
    如果程序在导入时已经有 public_config，尝试自动初始化。
    在生产中更建议在 FastAPI startup 事件中手动初始化（更可控）。
    """
    try:
        if public_config is None:
            return
        # mysql config
        mysql_cfg = {
            "host": public_config.get(key="database.host", get_type=str),
            "port": public_config.get(key="database.port", get_type=int),
            "user": public_config.get(key="database.user", get_type=str),
            "password": public_config.get(key="database.password", get_type=str),
            "db": public_config.get(key="database.database", get_type=str),
            "charset": public_config.get(key="database.charset", get_type=str)
        }
        # redis config -> 构建 url 或使用 host/port
        redis_host = public_config.get(key="redis.host", get_type=str)
        redis_port = public_config.get(key="redis.port", get_type=int)
        redis_db = public_config.get(key="redis.db", get_type=int)
        redis_password = public_config.get(key="redis.password", get_type=str, default=None)
        redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        # kick off init tasks but do not await here (最好在 startup 中 await)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果处于正在运行的事件循环（例如 uvicorn 已运行），需要用户在 startup 显式 await
            return
        loop.run_until_complete(ASYNC_DB.mysql.init_pool(**mysql_cfg))
        loop.run_until_complete(ASYNC_DB.redis.init_pool(url=redis_url, password=redis_password, db=redis_db))
    except Exception as e:
        logger.warning(f"自动初始化数据库/缓存失败（忽略）：{e}")

_maybe_auto_init()
