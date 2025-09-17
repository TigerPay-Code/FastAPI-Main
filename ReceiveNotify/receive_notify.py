#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : __init__.py
# @Time      : 2025/9/15 17:47
# @IDE       : PyCharm
# @Function  : 接收支付通知 （global_pay_in_notify 代收通知，global_pay_out_notify 代付通知，global_refund_notify 退款通知）
import os
from fastapi import FastAPI, Response
from contextlib import asynccontextmanager
from Config.config_loader import initialize_config, public_config
from Data.base import Pay_RX_Notify_In_Data, Pay_RX_Notify_Out_Data, Pay_RX_Notify_Refund_Data
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")

notify = FastAPI(
    title="FastAPI Receive Pay Notify Service",
    description="接收Pay-RX通知服务",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("接收Pay-RX通知服务启动")
    initialize_config()
    logger.info(f"当前操作系统：{public_config.get('software.system')}")
    yield
    logger.info("接收Pay-RX通知服务关闭")


notify.router.lifespan_context = lifespan


@notify.get("/Pay-RX_Notify")  # 测试接口
async def pay_rx_notify():
    logger.info(f"健康检查，返回 health，服务运行正常")
    return Response(content="health", media_type="text/plain")


@notify.post("/global_pay_in_notify")
async def handle_global_pay_in_notify(notify_in_data: Pay_RX_Notify_In_Data):
    logger.info(f"收到 【代收】 通知：数据：{notify_in_data}")
    if notify_in_data.state == 2:
        logger.info(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
    else:
        logger.error(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")
    return success


@notify.post("/global_pay_out_notify")
async def handle_global_pay_out_notify(notify_out_data: Pay_RX_Notify_Out_Data):
    logger.info(f"收到 【代付】 通知：数据：{notify_out_data}")
    return success


@notify.post("/global_refund_notify")
async def handle_global_refund_notify(notify_refund_data: Pay_RX_Notify_Refund_Data):
    logger.info(f"收到 【退款】 通知：数据：{notify_refund_data}")
    return success
