#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import asyncio
import os
from datetime import datetime, time

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import threading

from Config.config_loader import public_config
from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

scheduler = None
push_msg_thread = None


async def have_lunch():
    logger.info("吃午饭时间到！")
    try:
        message = '吃午饭时间到，午饭开始了！'
        logger.info(message)

        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.error(f"定时任务[提醒吃午饭]执行出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"定时任务[提醒吃午饭]执行出错: {e}")


def run_async_have_lunch_task():
    """在单独的事件循环中运行异步任务"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(have_lunch())
        loop.close()
    except Exception as e:
        logger.error(f"运行异步任务[提醒吃午饭]时出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            asyncio.run(send_telegram_message(f"运行异步任务[提醒吃午饭]时出错: {e}"))


async def check_pending_payments():
    """检查未处理支付通知的异步任务"""
    logger.info("检查未处理支付通知的异步任务")
    try:
        # 这里应该添加实际的支付检查逻辑
        # 例如：查询数据库中的待处理支付

        time_gap = public_config.get(key="task.interval", get_type=int, default=60)
        message = f'每{time_gap}秒钟检查一次未处理支付通知的任务执行了。'
        logger.info(message)

        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"定时任务执行出错: {e}")


def run_async_task():
    """在单独的事件循环中运行异步任务"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_pending_payments())
        loop.close()
    except Exception as e:
        logger.error(f"运行异步任务时出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            asyncio.run(send_telegram_message(f"运行异步任务时出错: {e}"))


def is_working_hours():
    """检查当前时间是否在工作时间内（周一到周五，9:00-19:00）"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)

    # 检查是否是周一到周五
    if now.weekday() >= 5:  # 5=周六, 6=周日
        return False

    # 检查是否在9:00-19:00之间
    start_time = time(9, 0)
    end_time = time(19, 0)
    current_time = now.time()

    return start_time <= current_time <= end_time


def start_check_balance_task():
    """启动检查余额的定时任务"""
    global scheduler

    beijing_tz = pytz.timezone('Asia/Shanghai')

    scheduler = BackgroundScheduler()

    # 获取配置中的时间间隔，默认为60秒
    interval_seconds = public_config.get(key="task.interval", get_type=int, default=60)
    interval_minutes = interval_seconds // 60

    # 创建组合触发器：周一到周五 + 9:00-19:00 + 间隔时间
    job1_trigger = AndTrigger([
        CronTrigger(day_of_week='mon-fri', hour='9-18', timezone=beijing_tz),
        IntervalTrigger(minutes=interval_minutes, timezone=beijing_tz)
    ])

    job1 = scheduler.add_job(
        func=run_async_task,
        trigger=job1_trigger,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59',
        id='payment_check_job'
    )
    logger.info(f"添加Job1: 周一到周五 9:00-19:00，每{interval_minutes}分钟触发一次")

    job2 = scheduler.add_job(
        func=run_async_have_lunch_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='12',
        minute='49',
        timezone=beijing_tz,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59',
        id='lunch_reminder_job_49'
    )
    logger.info(f"添加Job2: 周一到周五 12:49触发")

    job3 = scheduler.add_job(
        func=run_async_have_lunch_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='12',
        minute='50',
        timezone=beijing_tz,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59',
        id='lunch_reminder_job_50'
    )
    logger.info(f"添加Job3: 周一到周五 12:50触发")

    try:
        scheduler.start()
        logger.info("定时任务调度器已启动")

        # 立即执行一次任务，但只在工作时间内
        if is_working_hours():
            run_async_task()
            logger.info("立即执行了一次支付检查任务（在工作时间内）")
        else:
            logger.info("当前非工作时间，跳过立即执行支付检查任务")

        # 发送启动通知
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            asyncio.run(send_telegram_message(
                f"定时任务调度器已启动，配置了{len(scheduler.get_jobs())}个任务\n"
                f"支付检查任务执行时间：周一到周五 9:00-19:00，每{interval_minutes}分钟一次"
            ))
    except Exception as e:
        logger.error(f"启动定时任务时出错: {e}")
        # 尝试发送错误通知
        try:
            if public_config and public_config.get(key='telegram.enable', get_type=bool):
                asyncio.run(send_telegram_message(f"启动定时任务时出错: {e}"))
        except Exception as te:
            logger.error(f"发送Telegram错误消息失败: {te}")


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

    try:
        if scheduler:
            scheduler.shutdown(wait=True)
            scheduler = None
        if push_msg_thread:
            push_msg_thread = None
        logger.info("定时任务调度器已停止")

        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            asyncio.run(send_telegram_message("定时任务调度器已停止"))
    except Exception as e:
        logger.error(f"停止定时任务时出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            asyncio.run(send_telegram_message(f"停止定时任务时出错: {e}"))
