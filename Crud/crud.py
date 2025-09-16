#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : crud.py
# @Time      : 2025/9/16 13:39
# @IDE       : PyCharm
# @Function  :
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import redis.asyncio as redis
import json
from typing import List, Optional


# 缓存键前缀
PRODUCT_CACHE_KEY_PREFIX = "product:id:"
PRODUCT_LIST_CACHE_KEY = "product:list:all"
CACHE_EXPIRATION = 3600  # 缓存过期时间


# --- 增：创建产品 ---
async def create_product(db: AsyncSession, product: ProductCreate) -> Product:
    new_product = Product(**product.dict())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    # 异步清理缓存
    await clear_product_cache(redis_client)
    return new_product


# --- 查：根据 ID 获取单个产品（带缓存）---
async def get_product_by_id(db: AsyncSession, redis_client: redis.Redis, product_id: int) -> Optional[Product]:
    # 1. 尝试从 Redis 缓存中获取
    cache_key = f"{PRODUCT_CACHE_KEY_PREFIX}{product_id}"
    cached_product_json = await redis_client.get(cache_key)
    if cached_product_json:
        return Product(**json.loads(cached_product_json))

    # 2. 缓存未命中，查询数据库
    stmt = select(Product).where(Product.id == product_id, Product.status == 1)
    result = await db.execute(stmt)
    db_product = result.scalars().first()

    # 3. 如果找到，存入缓存
    if db_product:
        await redis_client.set(cache_key, json.dumps(db_product.__dict__), ex=CACHE_EXPIRATION)

    return db_product


# --- 查：获取所有产品列表（带缓存）---
async def get_all_products(db: AsyncSession, redis_client: redis.Redis) -> List[Product]:
    # 1. 尝试从 Redis 缓存中获取
    cached_list_json = await redis_client.get(PRODUCT_LIST_CACHE_KEY)
    if cached_list_json:
        return [Product(**item) for item in json.loads(cached_list_json)]

    # 2. 缓存未命中，查询数据库
    stmt = select(Product).where(Product.status == 1).order_by(Product.id)
    result = await db.execute(stmt)
    db_products = result.scalars().all()

    # 3. 如果找到，存入缓存
    if db_products:
        # 将 ORM 对象转换为字典列表进行序列化
        product_dicts = [item.__dict__ for item in db_products]
        await redis_client.set(PRODUCT_LIST_CACHE_KEY, json.dumps(product_dicts), ex=CACHE_EXPIRATION)

    return db_products


# --- 改：更新产品 ---
async def update_product(db: AsyncSession, redis_client: redis.Redis, product_id: int, product_data: ProductUpdate) -> \
Optional[Product]:
    # 1. 检查产品是否存在
    existing_product = await get_product_by_id(db, redis_client, product_id)
    if not existing_product:
        return None

    # 2. 更新数据库
    update_data = product_data.dict(exclude_unset=True)
    stmt = update(Product).where(Product.id == product_id).values(**update_data)
    await db.execute(stmt)
    await db.commit()
    await db.refresh(existing_product)

    # 3. 清理缓存，保证数据一致性
    await clear_product_cache(redis_client, product_id)

    return existing_product


# --- 删：逻辑删除产品 ---
async def delete_product(db: AsyncSession, redis_client: redis.Redis, product_id: int) -> bool:
    # 1. 检查产品是否存在
    existing_product = await get_product_by_id(db, redis_client, product_id)
    if not existing_product:
        return False

    # 2. 逻辑删除，更新 status 字段
    stmt = update(Product).where(Product.id == product_id).values(status=0)
    await db.execute(stmt)
    await db.commit()

    # 3. 清理缓存
    await clear_product_cache(redis_client, product_id)

    return True


# --- 事务示例：扣减库存 ---
async def decrease_stock_transaction(db: AsyncSession, redis_client: redis.Redis, product_id: int, amount: int) -> bool:
    try:
        # 使用 with 语句开启事务
        async with db.begin():
            # 悲观锁：select ... for update，在事务提交前锁定该行，防止并发冲突
            # 注意：`for_update=True` 在 SQLAlchemy 2.0+ 中推荐使用 `with_for_update()`
            stmt = select(Product).where(Product.id == product_id).with_for_update()
            result = await db.execute(stmt)
            product = result.scalars().first()

            if not product or product.stock < amount:
                # 抛出异常会回滚事务
                raise ValueError("库存不足或产品不存在")

            # 更新库存
            product.stock -= amount
            await db.commit()  # 提交事务

            # 事务成功后，清理缓存
            await clear_product_cache(redis_client, product_id)
            return True

    except Exception as e:
        await db.rollback()  # 发生异常时回滚
        print(f"事务失败: {e}")
        return False


# --- 缓存管理函数 ---
async def clear_product_cache(redis_client: redis.Redis, product_id: Optional[int] = None):
    # 清理单个产品缓存
    if product_id:
        await redis_client.delete(f"{PRODUCT_CACHE_KEY_PREFIX}{product_id}")
    # 清理产品列表缓存
    await redis_client.delete(PRODUCT_LIST_CACHE_KEY)