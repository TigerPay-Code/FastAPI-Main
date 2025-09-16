#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : __init__.py
# @Time      : 2025/9/15 17:47
# @IDE       : PyCharm
# @Function  : 接收支付通知 （global_pay_in_notify 代收通知，global_pay_out_notify 代付通知，global_refund_notify 退款通知）
import os

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field

from Data.base import Notify_In_Data
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

logger.debug("打印调试信息")
logger.info("打印日志信息")
logger.warn("打印警告信息")

logger.error("打印错误信息")
logger.exception("打印异常信息")

logger.critical("打印严重错误信息")

''''
sudo tail -f /data/FastAPI-Main/logs/ReceiveNotify.log
'''

notify = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")


class Notify_Out_Data(BaseModel):
    state: int
    sysOrderNo: str
    mchOrderNo: str
    amount: int
    sign: str


class Notify_Refund_Data(BaseModel):
    state: int
    sysOrderNo: str
    mchOrderNo: str
    amount: int
    sign: str


@notify.post("/global_pay_in_notify")
async def handle_global_pay_in_notify(notify_in_data: Notify_In_Data):
    logger.info(f"收到 【代收】 通知：数据：{notify_in_data}")
    if notify_in_data.state == 1:
        logger.info(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
    else:
        logger.error(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")
    return success


@notify.post("/global_pay_out_notify")
async def handle_global_pay_out_notify(notify_out_data: Notify_Out_Data):
    logger.info(f"收到 【代付】 通知：数据：{notify_out_data}")
    return success


@notify.post("/global_refund_notify")
async def handle_global_refund_notify(notify_refund_data: Notify_Refund_Data):
    logger.info(f"收到 【退款】 通知：数据：{notify_refund_data}")
    return success
