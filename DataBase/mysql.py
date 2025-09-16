from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
import redis.asyncio as redis


# MySQL 配置
DATABASE_URL = f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Redis 配置
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True # 自动解码 UTF-8
)

async def get_db_session():
    """依赖注入，获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis_client():
    """依赖注入，获取 Redis 客户端"""
    async with redis.Redis(connection_pool=redis_pool) as r:
        yield r