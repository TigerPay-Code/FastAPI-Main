#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import asyncio
import os

from apscheduler.schedulers.background import BackgroundScheduler
import threading

from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

scheduler = None
push_msg_thread = None


async def check_pending_payments():
    try:
        message = '每分钟检查一次未处理支付通知的任务执行了。'
        logger.info(message)
        await send_telegram_message(message)
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")


def run_async_task():
    """在单独的事件循环中运行异步任务"""
    asyncio.run(check_pending_payments())


def start_check_balance_task():
    global scheduler
    scheduler = BackgroundScheduler()

    # 全天24小时不停地每30分钟执行一次任务
    # scheduler.add_job(
    #     func=run_async_task,  # 直接传递函数引用，而不是调用结果
    #     trigger='interval',
    #     minutes=30,
    #     start_date='2025-01-01 00:00:00',
    #     end_date='2025-12-31 23:59:59'
    # )

    # 只在每天的上午9点到20点之间，每30分钟执行一次任务
    scheduler.add_job(
        func=run_async_task,
        trigger='cron',
        hour='9-20',  # 只在上午9点到下午8点（20点）之间运行
        minute='*/30',  # 每隔30分钟运行一次
        start_date='2025-01-01 00:00:00',  # 任务开始时间 2025-01-01 00:00:00
        end_date='2025-12-31 23:59:59'  # 任务结束时间 2025-12-31 23:59:59
    )

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
    global scheduler, push_msg_thread
    if scheduler:
        scheduler.shutdown()
        scheduler = None
    if push_msg_thread:
        push_msg_thread = None
    logger.info("定时任务调度器已停止")
