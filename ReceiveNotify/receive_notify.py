#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : receive_notify.py
# @Time      : 2025/10/09
# @IDE       : PyCharm
# @Function  : 接收支付通知 + 启动异步调度任务 + Telegram 实时提醒

import os
import json
from datetime import datetime
from math import ceil
from fastapi import FastAPI, Request, Response, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import aiomysql

# ----------------- 模块导入 -----------------
from Config.config_loader import initialize_config, public_config
from Data.base import Pay_RX_Notify_In_Data, Pay_RX_Notify_Out_Data, Pay_RX_Notify_Refund_Data

# ----------------- FastAPI中间访问件模块导入 -----------------
# from MiddleWare.middleware import AccessMiddleware
# -------------------------------------------
from PeriodicTask.pay_notify import start_periodic_task, stop_periodic_task
from Telegram.auto_bot import send_telegram_message, start_bot, stop_bot
from DataBase.async_mysql import mysql_manager, get_mysql_conn
from DataBase.async_redis import redis_manager, get_redis

from Utils.handle_time import get_sec_int_timestamp

# ----------------- 日志配置 -----------------
from Logger.logger_config import setup_logger
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)
# -------------------------------------------

# ----------------- HTTP 返回 -----------------
success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")

# ----------------- MySQL 与 Redis 配置 -----------------
mysql_cfg = {
    "host": public_config.get(key="database.host", get_type=str),
    "port": public_config.get(key="database.port", get_type=int),
    "user": public_config.get(key="database.user", get_type=str),
    "password": public_config.get(key="database.password", get_type=str),
    "db": public_config.get(key="database.database", get_type=str),
    "charset": public_config.get(key="database.charset", get_type=str)
}

redis_url = (
    f"redis://{public_config.get(key='redis.host', get_type=str)}:"
    f"{public_config.get(key='redis.port', get_type=int)}/"
    f"{public_config.get(key='redis.db', get_type=int)}"
)
redis_cfg = {
    "url": redis_url,
    "max_connections": 50,
}


# ============================================================
# 应用生命周期管理
# ============================================================
@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    """FastAPI 生命周期事件"""
    try:
        logger.info("🔧 正在初始化配置文件...")
        initialize_config()
        logger.info(f"当前操作系统: {public_config.get(key='software.system', get_type=str)}")
        logger.info(f"服务名称: {app.openapi()['info']['title']}")

        # 初始化数据库连接池
        logger.info("🗄️ 启动 MySQL 连接池...")
        await mysql_manager.init_pool(**mysql_cfg)

        # 初始化 Redis 连接池
        logger.info("🧠 启动 Redis 连接池...")
        await redis_manager.init_pool(**redis_cfg)

        # 启动 Telegram 机器人
        if public_config.get(key='telegram.enable', get_type=bool):
            logger.info("🤖 启动 Telegram 机器人线程...")
            start_bot()
            await send_telegram_message("✅ Telegram 机器人已启动")
        else:
            logger.warning("⚠️ Telegram 功能未启用，请检查配置文件 telegram.enable")

        # 启动定时任务调度器（异步）
        logger.info("⏱ 启动异步定时任务调度器...")
        start_periodic_task()

        # 服务启动通知
        if public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"🚀 服务 [{app.openapi()['info']['title']}] 已启动")

        yield  # 👇 应用运行中

    except Exception as e:
        logger.exception(f"❌ 服务启动过程中出错: {e}")
        if public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"❌ 服务启动出错: {e}")

    finally:
        # 停止任务与清理
        logger.info("🛑 服务关闭中... 停止调度任务与机器人")

        stop_periodic_task()

        if public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"🧩 服务 [{app.openapi()['info']['title']}] 已关闭")
            stop_bot()

        await mysql_manager.close()
        await redis_manager.close()
        logger.info("✅ 所有资源已安全关闭")


# ============================================================
# FastAPI 应用实例
# ============================================================
notify = FastAPI(
    title=public_config.get(key='software.app_name', get_type=str),
    description="接收 Pay-RX 支付回调通知服务",
    version=public_config.get(key='software.version', get_type=str),
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan_manager,
)

notify.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
notify.templates = templates

# notify.add_middleware(
#     AccessMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# ============================================================
# 工具函数
# ============================================================
def datetime_serializer(obj):
    """datetime → str"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ============================================================
# 路由部分
# ============================================================
@notify.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@notify.get("/users", response_class=HTMLResponse)
async def get_users(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=5, le=100),
        conn=Depends(get_mysql_conn),
        redis=Depends(get_redis)
):
    offset = (page - 1) * per_page
    cache_key = f"users_list:page_{page}:per_page_{per_page}"

    cached_data = await redis.get(cache_key)
    if cached_data:
        users = json.loads(cached_data)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT COUNT(*) AS total FROM users")
            total_users = (await cur.fetchone())["total"]
    else:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT COUNT(*) AS total FROM users")
            total_users = (await cur.fetchone())["total"]

            await cur.execute(
                "SELECT id, username, email, created_at FROM users ORDER BY id DESC LIMIT %s OFFSET %s",
                (per_page, offset)
            )
            users = await cur.fetchall()

            await redis.set(cache_key, json.dumps(users, default=datetime_serializer), ex=60)

    total_pages = int(ceil(total_users / per_page))
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_users": total_users,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1 if page > 1 else 1,
        "next_page": page + 1 if page < total_pages else total_pages,
    }

    return request.app.templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "pagination": pagination}
    )


# ============================================================
# 支付通知接口
# ============================================================
@notify.post("/global_pay_in_notify")
async def handle_global_pay_in_notify(notify_in_data: Pay_RX_Notify_In_Data):
    """代收通知"""
    logger.info(f"收到【代收】通知: {notify_in_data}")
    re_data = {"code": 0, "msg": "success"}

    try:
        # 时间戳验证
        if notify_in_data.timestamp > get_sec_int_timestamp() + public_config.get(key="order.delay_seconds", get_type=int, default=30):
            logger.warning(f"订单号 {notify_in_data.mchOrderNo} 时间戳异常，拒绝处理")
            return {"code": 1, "msg": "timestamp error"}

        if notify_in_data.state not in [0, 1, 2, 3]:
            logger.warning(f"订单号 {notify_in_data.mchOrderNo} 状态异常")
            return {"code": 1, "msg": "state error"}

        if notify_in_data.amount < 500 or notify_in_data.amount > 1000000:
            logger.warning(f"订单号 {notify_in_data.mchOrderNo} 金额异常")
            return {"code": 1, "msg": "amount error"}

        msg = (
            f"💰 订单号 {notify_in_data.mchOrderNo} "
            f"{'支付成功' if notify_in_data.state == 2 else '支付失败'}，"
            f"金额：{notify_in_data.amount / 100:.2f} 元"
        )
        logger.info(msg)
        await send_telegram_message(msg)
        return re_data

    except Exception as e:
        logger.exception(f"处理代收通知出错: {e}")
        await send_telegram_message(f"❌ 处理代收通知出错: {e}")
        return {"code": 1, "msg": "internal error"}


@notify.post("/global_pay_out_notify")
async def handle_global_pay_out_notify(notify_out_data: Pay_RX_Notify_Out_Data):
    """代付通知"""
    logger.info(f"收到【代付】通知: {notify_out_data}")
    msg = (
        f"🏦 代付订单号 {notify_out_data.mchOrderNo} "
        f"{'代付成功' if notify_out_data.state == 2 else '代付失败'}，"
        f"金额：{notify_out_data.amount / 100:.2f} 元"
    )
    await send_telegram_message(msg)
    return {"code": 0, "msg": "success"}


@notify.post("/global_refund_notify")
async def handle_global_refund_notify(notify_refund_data: Pay_RX_Notify_Refund_Data):
    """退款通知"""
    logger.info(f"收到【退款】通知: {notify_refund_data}")
    msg = (
        f"🔁 退款订单号 {notify_refund_data.mchOrderNo} "
        f"{'退款成功' if notify_refund_data.state == 2 else '退款失败'}，"
        f"金额：{notify_refund_data.amount / 100:.2f} 元"
    )
    await send_telegram_message(msg)
    return {"code": 0, "msg": "success"}


@notify.get("/Pay-RX_Notify")
async def pay_rx_health():
    """健康检查"""
    logger.info("健康检查成功")
    return Response(content="health", media_type="text/plain")
