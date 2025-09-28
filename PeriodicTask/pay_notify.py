#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import asyncio
import os

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import threading

from Config.config_loader import public_config
from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

scheduler = None
push_msg_thread = None


async def check_pending_payments():
    """检查未处理支付通知的异步任务"""
    logger.info("检查未处理支付通知的异步任务")
    try:
        time_gap = public_config.get(key="task.interval", get_type=int, default=60)
        message = f'每{time_gap}秒钟检查一次未处理支付通知的任务执行了。'
        logger.info(message)
        await send_telegram_message(message)
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")


def run_async_task():
    """在单独的事件循环中运行异步任务"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_pending_payments())
        loop.close()
    except Exception as e:
        logger.error(f"运行异步任务时出错: {e}")


def start_check_balance_task():
    """启动检查余额的定时任务"""
    global scheduler

    beijing_tz = pytz.timezone('Asia/Shanghai')

    scheduler = BackgroundScheduler()

    job1 = scheduler.add_job(
        func=run_async_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='9-18',
        minute=f'*/{public_config.get(key="task.interval", get_type=int, default=60)/60}',
        timezone=beijing_tz
    )
    logger.info(f"添加Job1: 每30分钟触发")

    job2 = scheduler.add_job(
        func=run_async_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='12',
        minute='49',
        timezone=beijing_tz
    )
    logger.info(f"添加Job2: 12:49触发")

    job3 = scheduler.add_job(
        func=run_async_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='12',
        minute='50',
        timezone=beijing_tz
    )
    logger.info(f"添加Job3: 12:50触发")

    scheduler.start()
    logger.info("定时任务调度器已启动")


def start_periodic_task():
    global push_msg_thread
    """
    启动周期性任务调度器。
    """
    logger.info('启动周期性任务调度器。')
    if not push_msg_thread:
        push_msg_thread = threading.Thread(target=start_check_balance_task, daemon=True)
        push_msg_thread.start()
        logger.info('周期性任务调度器已启动。')


def stop_periodic_task():
    """
    停止周期性任务调度器。
    """
    """
        停止周期性任务调度器。
        """
    global scheduler, push_msg_thread

    try:
        if scheduler:
            scheduler.shutdown(wait=True)
            scheduler = None
        if push_msg_thread:
            push_msg_thread = None
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止定时任务时出错: {e}")