#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : __init__.py
# @Time      : 2025/9/15 17:47
# @IDE       : PyCharm
# @Function  : 接收支付通知 （global_pay_in_notify 代收通知，global_pay_out_notify 代付通知，global_refund_notify 退款通知）

import os
import time
import json
from datetime import datetime

from fastapi import FastAPI, Request, Response, Depends, Query

from Config.config_loader import initialize_config, public_config
from Data.base import Pay_RX_Notify_In_Data, Pay_RX_Notify_Out_Data, Pay_RX_Notify_Refund_Data

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from math import ceil

# 引用生命期管理器模块
from contextlib import asynccontextmanager

from PeriodicTask.pay_notify import start_check_balance_task
# 引用发送Telegram消息模块
from Telegram.auto_bot import send_telegram_message, start_bot, stop_bot

# 引用数据库异步操作模块
from DataBase.async_mysql import mysql_manager, get_mysql_conn
from DataBase.async_redis import redis_manager, get_redis
import aiomysql

# 引用日志模块
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")

mysql_cfg = {
    "host": public_config.get(key="database.host", get_type=str),
    "port": public_config.get(key="database.port", get_type=int),
    "user": public_config.get(key="database.user", get_type=str),
    "password": public_config.get(key="database.password", get_type=str),
    "db": public_config.get(key="database.database", get_type=str),
    "charset": public_config.get(key="database.charset", get_type=str)
}
redis_url = (f"redis://{public_config.get(key='redis.host', get_type=str)}:"
             f"{public_config.get(key='redis.port', get_type=int)}/"
             f"{public_config.get(key='redis.db', get_type=int)}")

redis_cfg = {
    "url": redis_url,
    "max_connections": 50,
}


# 应用生命周期事件
@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    logger.info(f"当前操作系统：{public_config.get(key='software.system', get_type=str)}")

    logger.info(f"服务名称：{app.openapi()['info']['title']}")

    logger.info("正在初始化配置文件...")
    initialize_config()

    logger.info(f"正在启动数据库连接池...")
    await mysql_manager.init_pool(**mysql_cfg)

    logger.info(f"正在启动Redis连接池...")
    await redis_manager.init_pool(**redis_cfg)

    # 启动 Telegram 机器人（如果启用）
    if public_config and public_config.get(key='telegram.enable', get_type=bool):
        logger.info("正在启动 Telegram 机器人...")
        start_bot()
        logger.info("Telegram 机器人线程已启动")
    else:
        logger.info("启动 Telegram 机器人 失败！ (请检查配置文件中 telegram.enable 是否为 True)")

    # 启动定时检查余额任务
    start_check_balance_task()
    await send_telegram_message("启动定时检查余额任务")

    logger.info("接收Pay-RX通知服务开启")
    if public_config and public_config.get(key='telegram.enable', get_type=bool):
        await send_telegram_message(f"服务 {app.openapi()['info']['title']} 已启动")

    # 应用生命周期结束时执行
    yield

    logger.info("接收Pay-RX通知服务关闭")
    if public_config and public_config.get(key='telegram.enable', get_type=bool):
        await send_telegram_message(f"服务 {app.openapi()['info']['title']} 已关闭")

    logger.info(f"正在关闭数据库连接池...")
    await mysql_manager.close()
    logger.info(f"正在关闭Redis连接池...")
    await redis_manager.close()

    # 停止 Telegram 机器人
    stop_bot()


notify = FastAPI(
    title="FastAPI Receive Pay Notify Service",
    description="接收Pay-RX通知服务",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan_manager
)

notify.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
notify.templates = templates


def datetime_serializer(obj):
    """自定义序列化函数，处理datetime对象"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


@notify.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@notify.get("/mysql")
async def test_mysql(conn=Depends(get_mysql_conn)):
    async with conn.cursor() as cur:
        await cur.execute("SELECT NOW()")
        row = await cur.fetchone()
    return {"mysql_time": row[0].isoformat()}


@notify.get("/redis")
async def test_redis(redis=Depends(get_redis)):
    await redis.set("fastapi:test", "hello", ex=10)
    val = await redis.get("fastapi:test")
    return {"redis_value": val}


@notify.post("/user")
async def create_user(conn=Depends(get_mysql_conn)):
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO users (username, email) VALUES (%s, %s)",
            ("alice", "alice@example.com"),
        )
        await conn.commit()  # 提交事务
    return {"msg": "user created"}


# 查询数据 (查)
@notify.get("/user/{user_id}")
async def get_user(user_id: int, conn=Depends(get_mysql_conn)):
    start = time.perf_counter_ns()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT id, username, email, balance FROM users WHERE id=%s", (user_id,))
        row = await cur.fetchone()
    end = time.perf_counter_ns()
    elapsed_ms = (end - start) / 1_000_000
    logger.info(f"查询用户ID: {user_id} 耗时: {elapsed_ms:.6f} 毫秒")
    return {"user": row, "query_time_ns": f"查询用户ID: {user_id} 耗时: {elapsed_ms:.6f} 毫秒"}


# 查询数据 (查)
@notify.get("/username/{user_name}")
async def get_user(user_name: str, conn=Depends(get_mysql_conn)):
    start = time.perf_counter_ns()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT id, username, email, balance FROM users WHERE username=%s", (user_name,))
        row = await cur.fetchone()
    end = time.perf_counter_ns()
    elapsed_ms = (end - start) / 1_000_000
    logger.info(f"查询用户名: {user_name} 耗时: {elapsed_ms:.6f} 毫秒")
    return {"user": row, "query_time_ns": f"查询用户名: {user_name} 耗时: {elapsed_ms:.6f} 毫秒"}


# 更新数据 (改)
@notify.put("/user/{user_id}")
async def update_user(user_id: int, conn=Depends(get_mysql_conn)):
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE users SET email=%s WHERE id=%s",
            ("new_email@example.com", user_id),
        )
        await conn.commit()
    return {"msg": "user updated"}


# 删除数据 (删)
@notify.delete("/user/{user_id}")
async def delete_user(user_id: int, conn=Depends(get_mysql_conn)):
    async with conn.cursor() as cur:
        await cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        await conn.commit()
    return {"msg": "user deleted"}


@notify.post("/transfer")
async def transfer_money(conn=Depends(get_mysql_conn)):
    """
    模拟事务：从用户1扣钱，给用户2加钱
    """
    try:
        async with conn.cursor() as cur:
            await conn.begin()  # 开启事务

            # 扣钱
            await cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id=%s",
                (100, 1),
            )

            # 加钱
            await cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id=%s",
                (100, 2),
            )

            await conn.commit()  # 提交事务
        return {"msg": "transfer success"}
    except Exception as e:
        await conn.rollback()  # 回滚事务
        return {"error": str(e)}


@notify.get("/users", response_class=HTMLResponse)
async def get_users(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=5, le=100),
        conn=Depends(get_mysql_conn),
        redis=Depends(get_redis)
):
    # 计算偏移量
    offset = (page - 1) * per_page

    # 从缓存中获取数据
    cache_key = "all_users_list_cache"
    cached_data = await redis.get(cache_key)

    users = None

    if cached_data:
        # 如果缓存命中，则直接返回
        users = json.loads(cached_data)

        # 即使缓存命中，也需要获取总记录数用于分页
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT COUNT(*) AS total FROM users")
            total_result = await cur.fetchone()
            total_users = total_result['total']
    else:
        # 如果缓存未命中，则从数据库中获取数据
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 获取总记录数
            await cur.execute("SELECT COUNT(*) AS total FROM users")
            total_result = await cur.fetchone()
            total_users = total_result['total']

            # 获取当前页的用户数据
            await cur.execute(
                "SELECT id, username, email, created_at FROM users ORDER BY id DESC LIMIT %s OFFSET %s",
                (per_page, offset)
            )
            users = await cur.fetchall()

            await redis.set(cache_key, json.dumps(users, default=datetime_serializer), ex=60)

    # 计算总页数
    total_pages = ceil(total_users / per_page)

    # 分页信息
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_users": total_users,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1 if page > 1 else 1,
        "next_page": page + 1 if page < total_pages else total_pages
    }

    return request.app.templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": users,
            "pagination": pagination
        }
    )


@notify.get("/Pay-RX_Notify")  # 测试接口
async def pay_rx_notify():
    logger.info(f"健康检查，返回 health，服务运行正常")
    return Response(content="health", media_type="text/plain")


@notify.post("/global_pay_in_notify")
async def handle_global_pay_in_notify(notify_in_data: Pay_RX_Notify_In_Data):
    logger.info(f"收到 【代收】 通知：数据：{notify_in_data}")
    if notify_in_data.state == 2:
        logger.info(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
        await send_telegram_message(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
    else:
        logger.error(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")
        await send_telegram_message(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")
    return success


@notify.post("/global_pay_out_notify")
async def handle_global_pay_out_notify(notify_out_data: Pay_RX_Notify_Out_Data):



    logger.info(f"收到 【代付】 通知：数据：{notify_out_data}")
    if notify_out_data.state == 2:
        logger.info(f"代付订单号: {notify_out_data.sysOrderNo} 已成功代付，金额: {notify_out_data.amount}")
        await send_telegram_message(f"订单号: {notify_out_data.sysOrderNo} 已成功代付，金额: {notify_out_data.amount}")
    else:
        logger.error(f"代付订单号: {notify_out_data.sysOrderNo} 代付失败，金额: {notify_out_data.amount}")
        await send_telegram_message(f"订单号: {notify_out_data.sysOrderNo} 代付失败，金额: {notify_out_data.amount}")
    return success


@notify.post("/global_refund_notify")
async def handle_global_refund_notify(notify_refund_data: Pay_RX_Notify_Refund_Data):
    logger.info(f"收到 【退款】 通知：数据：{notify_refund_data}")
    if notify_refund_data.state == 2:
        logger.info(f"退款订单号: {notify_refund_data.sysOrderNo} 已成功退款，金额: {notify_refund_data.amount}")
        await send_telegram_message(f"退款订单号: {notify_refund_data.sysOrderNo} 已成功退款，金额: {notify_refund_data.amount}")
    else:
        logger.error(f"退款订单号: {notify_refund_data.sysOrderNo} 退款失败，金额: {notify_refund_data.amount}")
        await send_telegram_message(f"退款订单号: {notify_refund_data.sysOrderNo} 退款失败，金额: {notify_refund_data.amount}")
    return success
