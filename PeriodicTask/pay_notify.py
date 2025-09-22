#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import asyncio
import os

from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
import threading

from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

push_msg_thread = None


async def check_pending_payments():
    message = '每分钟检查一次未处理支付通知的任务执行了。'
    logger.info(message)
    await send_telegram_message(message)


def start_check_balance_task():
    check_balance = BlockingScheduler()
    check_balance.add_job(
        func=asyncio.run(check_pending_payments()),
        trigger='interval',
        minutes=1,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59'
    )  # 每1分钟执行一次
    check_balance.start()


def start_periodic_task():
    global push_msg_thread
    """
    启动周期性任务调度器。
    """
    push_msg_thread = threading.Thread(target=start_check_balance_task).start()


def stop_periodic_task():
    """
    停止周期性任务调度器。
    """
    global push_msg_thread
    if push_msg_thread:
        push_msg_thread.stop()
