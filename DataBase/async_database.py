#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : async_database.py
# @Time      : 2025/10/10 12:14
# @IDE       : PyCharm
# @Function  :
# async_database.py
# 统一的异步数据库 + 缓存组件（aiomysql + redis.asyncio）
# 适用于 FastAPI 异步环境
import asyncio
import time
import json
import logging
from typing import Any, Optional, Callable, Iterable, Coroutine
import aiomysql
# 推荐使用 redis.asyncio from `redis` 包
from aiomysql import Connection
import redis.asyncio as redis_asyncio
from redis.asyncio import Redis
from contextlib import asynccontextmanager

# ----------------- 日志配置 -----------------
import os
from Logger.logger_config import setup_logger
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

# 尝试从项目配置加载 public_config（可选）
try:
    from Config.config_loader import public_config
except Exception as err1:
    logger.error(
        f"模块 Config.config_loader 未找到或 public_config 未定义，将 public_config 设置为 None，错误信息：{err1}")
    public_config = None


# ---------- 异步 MySQL 管理 ----------
class AsyncMySQL:
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None
        self._init_lock = asyncio.Lock()

    async def init_pool(self, **kwargs):
        """
        初始化 MySQL 连接池（幂等）。
        常用参数：host, port, user, password, db, charset, minsize, maxsize, autocommit
        """
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
            # 创建连接池
            self.pool: aiomysql.Pool = await aiomysql.create_pool(**config)
            # 测试连接
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    await cur.fetchone()
            logger.info("MySQL 连接池就绪 (minsize=%s maxsize=%s)", config.get("minsize"), config.get("maxsize"))

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
        """上下文方式获取连接：async with mysql_manager.acquire() as conn: ..."""
        self.ensure_inited()
        assert self.pool is not None
        conn: Connection = await self.pool.acquire()
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
        """
        执行写操作（INSERT/UPDATE/DELETE）。
        返回 (rowcount, lastrowid)。如果不需要 lastrowid，可只使用 [0]。
        注意：如果初始化时 autocommit=False，需要外部 commit（transaction() 场景会自动 commit/rollback）。
        """
        async with self.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, args or ())
                # lastrowid 在某些驱动/语句下为 None
                lastrowid = getattr(cur, "lastrowid", None)
                return cur.rowcount, lastrowid

    @asynccontextmanager
    async def transaction(self):
        """
        事务上下文管理器：
        async with mysql_manager.transaction() as conn:
            async with conn.cursor() as cur:
                await cur.execute(...)
        commit/rollback 在此封装处理。
        """
        self.ensure_inited()
        assert self.pool is not None
        conn = await self.pool.acquire()  # type: ignore
        try:
            await conn.begin()
            try:
                yield conn
                await conn.commit()
            except Exception as err2:
                logger.exception(f"事务执行失败，回滚中...，错误信息：{err2}")
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
        """
        初始化 Redis 客户端；
        - 优先使用 url（比如 redis://:password@host:port/db）
        - 否则使用 host/port/db/password 等 kwargs 构建 URL
        """
        async with self._init_lock:
            if self.client is not None:
                return
            logger.info("初始化 Redis 客户端...")
            # 支持传入 redis URL 或 host/port/db/password
            try:
                if url:
                    # 直接使用传入的 url（并传递其他 redis 参数）
                    self.client = redis_asyncio.from_url(url, **{k: v for k, v in kwargs.items() if k != "password"})
                    # 有些版本需要单独传 password
                    if "password" in kwargs and kwargs["password"] is not None:
                        # redis.from_url 会根据 URL 解析密码，若需要可在 URL 中放入密码
                        pass
                else:
                    host = kwargs.get("host", "localhost")
                    port = kwargs.get("port", 6379)
                    db = kwargs.get("db", 0)
                    password = kwargs.get("password", None)
                    # 构建 redis url（如果有密码，采用 redis://:password@host:port/db）
                    if password:
                        redis_url = f"redis://:{password}@{host}:{port}/{db}"
                    else:
                        redis_url = f"redis://{host}:{port}/{db}"
                    self.client = redis_asyncio.from_url(redis_url)
                # 测试连接
                await self.client.ping()
            except Exception as e:
                logger.exception("Redis ping 失败")
                raise RuntimeError("Redis connection failed") from e
            logger.info("Redis 客户端就绪")

    async def close(self):
        if self.client is not None:
            logger.info("关闭 Redis 客户端...")
            try:
                await self.client.aclose()  # 取代 await self.client.close()
            except AttributeError:
                # 向后兼容旧版本 redis (<5.0)
                await self.client.close()
            self.client = None
            logger.info("Redis 客户端已关闭")

    def ensure_inited(self):
        if self.client is None:
            raise RuntimeError("Redis client not initialized. Call init_pool first.")

    # 基础操作（原始值：bytes / str）
    async def get(self, key: str):
        self.ensure_inited()
        return await self.client.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        """
        自动序列化：如果 value 不是 str/bytes，则 JSON 序列化存储。
        ex 为秒级过期时间。
        """
        self.ensure_inited()
        if not isinstance(value, (str, bytes, bytearray)):
            try:
                value = json.dumps(value, default=str, ensure_ascii=False)
            except Exception as err3:
                logger.exception(f"Redis 值 JSON 序列化失败，尝试转为 str 存储，错误信息：{err3}")
                # fallback: 转为 str
                value = str(value)
        return await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        self.ensure_inited()
        return await self.client.delete(key)

    async def exists(self, key: str):
        self.ensure_inited()
        return await self.client.exists(key)

    # 更友好的 JSON API
    async def get_json(self, key: str):
        """尝试从 redis 取值并 json.loads，失败时返回原始字符串/bytes"""
        self.ensure_inited()
        raw = await self.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            try:
                raw = raw.decode()
            except Exception as err4:
                logger.exception(f"Redis 值解码失败，返回原始值，错误信息：{err4}")
                pass
        try:
            return json.loads(raw)
        except Exception as err5:
            logger.exception(f"JSON 反序列化失败，返回原始值，错误信息：{err5}")
            return raw

    # 分布式锁（简单实现）
    async def acquire_lock(self, lock_key: str, lock_ttl: int = 10) -> bool:
        """
        尝试获取锁（非阻塞）。返回 True/False。
        基于 SET NX EX。
        """
        self.ensure_inited()
        # redis-py(set) 采用 set(name, value, nx=True, ex=lock_ttl)
        return await self.client.set(lock_key, "1", nx=True, ex=lock_ttl)

    async def release_lock(self, lock_key: str):
        self.ensure_inited()
        await self.client.delete(lock_key)


# ---------- 缓存装饰器：自动缓存查询结果（支持防穿透锁） ----------
def cached(key_builder: Callable[..., str], ttl: int = 60, null_ttl: int = 5, lock_ttl: int = 5):
    """
    使用方法示例：
    @cached(lambda user_id: f "user:{user_id}", ttl=60)
    async def load_user(user_id): ...
    """

    def decorator(func: Callable[..., Coroutine]):
        async def wrapper(*args, **kwargs):
            # 生成缓存 key（允许 key_builder 使用 args/kwargs）
            try:
                cache_key = key_builder(*args, **kwargs)
            except Exception as err6:
                # 如果 key 构建失败，直接调用函数
                logger.exception(f"缓存 key 构建失败，直接回退执行函数，错误信息：{err6}")
                return await func(*args, **kwargs)

            redis = ASYNC_DB.redis  # 访问单例（见下）
            # 如果 redis 尚未初始化，退回到函数执行
            try:
                if redis is None or redis.client is None:
                    logger.debug("Redis 未初始化，跳过缓存逻辑")
                    return await func(*args, **kwargs)
            except Exception as err7:
                # defensive
                logger.exception(f"Redis 检查失败，直接回退执行函数，错误信息：{err7}")
                return await func(*args, **kwargs)

            # 1. 尝试取缓存（使用 get_json 以便自动反序列化）
            raw = await redis.get_json(cache_key)
            if raw is not None:
                return raw

            lock_key = cache_key + ":lock"
            # 2. 获取分布式锁，防止缓存击穿
            got = await redis.acquire_lock(lock_key, lock_ttl=lock_ttl)
            if not got:
                # 等待锁释放后再读取缓存（自旋 + 超时）
                wait_start = time.time()
                while time.time() - wait_start < (lock_ttl + 0.5):
                    await asyncio.sleep(0.05)
                    raw = await redis.get_json(cache_key)
                    if raw is not None:
                        return raw
                # 超时仍无缓存，则回退调用函数
                return await func(*args, **kwargs)

            # 我们获取到锁 -> 调用函数并写回缓存
            try:
                result = await func(*args, **kwargs)
                if result is None:
                    # 防穿透短期缓存（保存 JSON null）
                    await redis.set(cache_key, json.dumps(None), ex=null_ttl)
                else:
                    # redis.set 会在内部把 dict/list JSON 序列化
                    await redis.set(cache_key, result, ex=ttl)
                return result
            finally:
                # 释放锁
                try:
                    await redis.release_lock(lock_key)
                except Exception as err8:
                    # defensive
                    logger.exception(f"释放锁失败 lock_key={lock_key}，错误信息：{err8}")

        return wrapper

    return decorator


# ---------- 统一入口单例 ----------
ASYNC_DB = type("ASyncDBHolder", (), {})()
ASYNC_DB.mysql = AsyncMySQL()
ASYNC_DB.redis = AsyncRedis()

# 便捷导出
mysql_manager = ASYNC_DB.mysql
redis_manager = ASYNC_DB.redis


# # ---------- 从配置文件自动初始化（可选） ----------
# def _maybe_auto_init():
#     """
#     如果项目有 public_config，可在导入时自动初始化（但在 uvicorn/fastapi 的运行事件循环中可能不适合直接 run_until_complete）。
#     推荐在 FastAPI startup 中手动 await mysql_manager.init_pool(...) 与 redis_manager.init_pool(...)
#     """
#     try:
#         if public_config is None:
#             return
#         loop = asyncio.get_event_loop()
#         if loop.is_running():
#             # 如果当前事件循环已在运行（例如 FastAPI/uvicorn）
#             logger.info("当前事件循环正在运行，跳过自动初始化（避免loop冲突）")
#             return
#
#         # mysql config
#         mysql_cfg = {
#             "host": public_config.get(key="database.host", get_type=str),
#             "port": public_config.get(key="database.port", get_type=int),
#             "user": public_config.get(key="database.user", get_type=str),
#             "password": public_config.get(key="database.password", get_type=str),
#             "db": public_config.get(key="database.database", get_type=str),
#             "charset": public_config.get(key="database.charset", get_type=str, default="utf8mb4")
#         }
#         # redis config
#         redis_host = public_config.get(key="redis.host", get_type=str)
#         redis_port = public_config.get(key="redis.port", get_type=int)
#         redis_db = public_config.get(key="redis.db", get_type=int)
#         redis_password = public_config.get(key="redis.password", get_type=str, default=None)
#         redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
#         loop = asyncio.get_event_loop()
#         if loop.is_running():
#             # 如果当前事件循环正在运行（例如在 uvicorn 中），建议在 startup 事件中手动 await 初始化
#             logger.info("当前事件循环正在运行，跳过模块导入时自动初始化，请在应用 startup 中手动初始化")
#             return
#         loop.run_until_complete(mysql_manager.init_pool(**mysql_cfg))
#         loop.run_until_complete(redis_manager.init_pool(url=redis_url, password=redis_password))
#         logger.info("自动初始化 MySQL/Redis 完成")
#     except Exception as err9:
#         logger.warning(f"自动初始化数据库/缓存失败（忽略）：{err9}")
#
#
# # _maybe_auto_init()
#
# # ---------- __main__ 演示（用于本地测试） ----------
# if __name__ == "__main__":
#     # 本地简单测试，修改为你自己的数据库/redis 配置再运行
#     async def demo():
#         try:
#             # 初始化 MySQL（utf8mb4 示例）
#             await mysql_manager.init_pool(
#                 host=public_config.get(key="database.host", get_type=str),
#                 port=public_config.get(key="database.port", get_type=int),
#                 user=public_config.get(key="database.user", get_type=str),
#                 password=public_config.get(key="database.password", get_type=str),
#                 db=public_config.get(key="database.database", get_type=str),
#                 charset=public_config.get(key="database.charset", get_type=str, default="utf8mb4")
#             )
#             # 初始化 Redis（无密码示例）
#             await redis_manager.init_pool(
#                 host=public_config.get(key="redis.host", get_type=str),
#                 port=public_config.get(key="redis.port", get_type=int),
#                 db=public_config.get(key="redis.db", get_type=int)
#             )
#
#             # MySQL 查询示例（fetchall）
#             try:
#                 rows = await mysql_manager.fetchall(
#                     "SELECT `ID`, `batch_id`, `phone_number`, `verification_code` FROM `sms_info`")
#                 print("mysql.fetchall ->", rows)
#             except Exception as err10:
#                 print("mysql fetch error:", err10)
#
#             # Redis set/get 示例
#             await redis_manager.set("demo:user:1", {"name": "Tom", "age": 18}, ex=30)
#             user = await redis_manager.get_json("demo:user:1")
#             print("redis.get_json ->", user)
#
#             cache_key = "sms_info:id:1"
#             cache_data = await redis_manager.get_json(cache_key)
#             if cache_data:
#                 print("缓存命中 ->", cache_data)
#             else:
#                 print("缓存未命中")
#                 cache_data = await mysql_manager.fetchone(
#                     "SELECT `ID`, `batch_id`, `phone_number`, `verification_code` FROM `sms_info` WHERE `ID`=1")
#                 if cache_data:
#                     await redis_manager.set(cache_key, cache_data, ex=15)
#                     print("缓存未命中，从数据库读取 ->", cache_data)
#                 else:
#                     print("缓存未命中，数据库也未查到 ->", cache_data)
#
#             # 分布式锁示例
#             lock_acquired = await redis_manager.acquire_lock("demo:lock:test", lock_ttl=10)  # 尝试获取锁
#             if lock_acquired:
#                 print("获取到锁，执行受保护操作...")
#                 await asyncio.sleep(2)  # 模拟操作
#                 await redis_manager.release_lock("demo:lock:test")
#                 print("操作完成，释放锁")
#             else:
#                 print("未能获取锁，跳过操作")
#
#             # 缓存穿透示例（缓存 null 值）
#             await redis_manager.set("demo:null:key", None, ex=10)
#             null_data = await redis_manager.get_json("demo:null:key")
#             print("缓存穿透示例 ->", null_data)
#
#             # cached 装饰器示例
#             @cached(lambda uid: f"demo:user:{uid}", ttl=15)
#             async def load_user(uid: int):
#                 print("load_user from DB for", uid)
#                 # 假装去数据库查
#                 return {"id": uid, "name": "demo"}
#
#             # 使用 cached 装饰器
#             print("load_user 1 ->", await load_user(1))
#             # 等待 15 秒后再次调用（会打印 load_user from DB）
#             await asyncio.sleep(15)
#             print("load_user 1 ->", await load_user(1))
#
#             # 第一次从函数取并缓存
#             print("load_user 1 ->", await load_user(1))
#             # 第二次从缓存读取（不会打印 load_user from DB）
#             print("load_user 1 ->", await load_user(1))
#         finally:
#             await mysql_manager.close()
#             await redis_manager.close()
#
#
#     asyncio.run(demo())
