# db.py
import asyncio
import aiomysql
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional, List, Tuple, Dict
import logging
import backoff  # 可选：用于自动重试，若无则可移除并实现自定义重试

logger = logging.getLogger(__name__)

# 全局池变量（模块级）
_POOL: Optional[aiomysql.Pool] = None

class DBConfig:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        db: Optional[str] = None,
        minsize: int = 1,
        maxsize: int = 10,
        charset: str = "utf8mb4",
        autocommit: bool = False,
        connect_timeout: int = 10,
        **kwargs,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.minsize = minsize
        self.maxsize = maxsize
        self.charset = charset
        self.autocommit = autocommit
        self.connect_timeout = connect_timeout
        self.extra = kwargs

    def to_aiomysql_kwargs(self):
        kw = dict(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            minsize=self.minsize,
            maxsize=self.maxsize,
            charset=self.charset,
            autocommit=self.autocommit,
            connect_timeout=self.connect_timeout,
            cursorclass=aiomysql.DictCursor,
        )
        kw.update(self.extra)
        return kw

async def init_pool(config: DBConfig) -> aiomysql.Pool:
    """
    初始化全局连接池（在 FastAPI startup 时调用）
    """
    global _POOL
    if _POOL is not None:
        return _POOL

    kwargs = config.to_aiomysql_kwargs()
    _POOL = await aiomysql.create_pool(**kwargs)
    logger.info("MySQL pool created: %s:%s/%s (min=%s max=%s)",
                config.host, config.port, config.db, config.minsize, config.maxsize)
    return _POOL

async def close_pool() -> None:
    """
    关闭全局连接池（在 FastAPI shutdown 时调用）
    """
    global _POOL
    if _POOL is None:
        return
    _POOL.close()
    await _POOL.wait_closed()
    logger.info("MySQL pool closed")
    _POOL = None

def get_pool() -> aiomysql.Pool:
    """
    同步读取全局池引用（若在请求上下文需要直接拿到 pool）
    """
    if _POOL is None:
        raise RuntimeError("DB pool is not initialized. Call init_pool first.")
    return _POOL

# ----- 基础执行API -----
async def _acquire_conn():
    pool = get_pool()
    conn = await pool.acquire()
    return conn

async def execute(sql: str, params: Optional[Tuple[Any, ...]] = None) -> int:
    """
    执行 INSERT/UPDATE/DELETE，返回受影响行数
    """
    conn = await _acquire_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or ())
            affected = cur.rowcount
            # 如果连接设置了 autocommit=False，需要手动 commit
            if not conn.get_autocommit():
                await conn.commit()
            return affected
    finally:
        pool = get_pool()
        pool.release(conn)

async def fetchone(sql: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    conn = await _acquire_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or ())
            row = await cur.fetchone()
            return row
    finally:
        pool = get_pool()
        pool.release(conn)

async def fetchall(sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
    conn = await _acquire_conn()
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, params or ())
            rows = await cur.fetchall()
            return rows
    finally:
        pool = get_pool()
        pool.release(conn)

async def executemany(sql: str, seq_of_params: List[Tuple[Any, ...]]) -> int:
    """
    批量插入/更新（使用 executemany），返回最后 cursor.rowcount
    """
    conn = await _acquire_conn()
    try:
        async with conn.cursor() as cur:
            await cur.executemany(sql, seq_of_params)
            affected = cur.rowcount
            if not conn.get_autocommit():
                await conn.commit()
            return affected
    finally:
        pool = get_pool()
        pool.release(conn)

# ----- 事务上下文管理 -----
@asynccontextmanager
async def transaction() -> AsyncGenerator[aiomysql.Connection, None]:
    """
    事务上下文示例：
    async with transaction() as conn:
        async with conn.cursor() as cur:
            await cur.execute(...)
    """
    conn = await _acquire_conn()
    try:
        # 确保事务开始
        await conn.begin()
        yield conn
        # 如果没有异常则提交
        await conn.commit()
    except Exception:
        # 出错回滚
        try:
            await conn.rollback()
        finally:
            pool = get_pool()
            pool.release(conn)
        raise
    else:
        pool = get_pool()
        pool.release(conn)

# ----- 健康检查 -----
async def healthcheck() -> bool:
    """
    简单的健康检查：执行 SELECT 1
    """
    try:
        row = await fetchone("SELECT 1 as ok")
        return bool(row and row.get("ok") == 1)
    except Exception as e:
        logger.exception("DB healthcheck failed: %s", e)
        return False

# ----- 可选：带重试的执行（示例使用 backoff 库；若未安装请移除）
try:
    def _giveup_on_value_error(e):
        # 例如：对语法错误不重试，其他异常重试
        return isinstance(e, aiomysql.OperationalError)

    @backoff.on_exception(backoff.expo, Exception, max_tries=3, giveup=_giveup_on_value_error)
    async def execute_with_retry(sql: str, params: Optional[Tuple[Any, ...]] = None):
        return await execute(sql, params)
except Exception:
    # 如果没有安装 backoff，不影响核心功能
    pass
