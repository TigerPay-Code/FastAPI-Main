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

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

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
            safe_async_run(send_telegram_message, f"定时任务[提醒吃午饭]执行出错: {e}")


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
            safe_async_run(send_telegram_message, f"运行异步任务[提醒吃午饭]时出错: {e}")


async def daily_reminder():
    """每日提醒的异步任务"""
    logger.info("每日提醒时间到！")
    try:
        message = '现在是上午11点05分，每日提醒！'
        logger.info(message)

        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.error(f"定时任务[每日提醒]执行出错: {e}")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            safe_async_run(send_telegram_message, f"定时任务[每日提醒]执行出错: {e}")


def run_async_daily_reminder_task():
    """在单独的事件循环中运行异步的每日提醒任务"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(daily_reminder())
        loop.close()
    except Exception as e:
        logger.error(f"运行异步任务[每日提醒]时出错: {e}")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            safe_async_run(send_telegram_message, f"运行异步任务[每日提醒]时出错: {e}")


async def check_pending_payments():
    """检查未处理支付通知的异步任务"""
    logger.info(">>> check_pending_payments() 被调用 <<<")
    try:
        # 这里应该添加实际的支付检查逻辑
        # 例如：查询数据库中的待处理支付

        time_gap = public_config.get(key="task.interval", get_type=int, default=39)
        message = f'每{time_gap}分钟检查一次未处理支付通知的任务执行了。'
        logger.info(message)

        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            safe_async_run(send_telegram_message, f"定时任务执行出错: {e}")


def start_periodic_task():
    """
    启动周期性任务调度器。
    """
    logger.info('启动周期性任务调度器。')
    start_check_balance_task()
    logger.info('周期性任务调度器已启动。')


def run_async_task():
    """在单独的事件循环中运行异步任务"""
    logger.info(">>> run_async_task() 被调用 <<<")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_pending_payments())
        loop.close()
    except Exception as e:
        logger.error(f"运行异步任务时出错: {e}")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            safe_async_run(send_telegram_message, f"运行异步任务时出错: {e}")


def safe_async_run(async_func, *args, **kwargs):
    """安全运行异步函数"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # 创建协程对象并运行
        coro = async_func(*args, **kwargs)
        loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"执行异步任务出错: {e}")
    finally:
        loop.close()


def is_working_hours():
    """检查当前时间是否在工作时间内（周一到周五，9:00-20:00）"""
    now = datetime.now()

    # 检查是否是周一到周五
    if now.weekday() >= 5:  # 5=周六, 6=周日
        return False

    # 检查是否在9:00-20:00之间
    start_time = time(9, 0)
    end_time = time(20, 0)
    current_time = now.time()

    return start_time <= current_time <= end_time


def start_check_balance_task():
    """启动检查余额的定时任务"""
    global scheduler

    scheduler = BackgroundScheduler()

    # 获取配置中的时间间隔，默认为39分钟
    interval_minutes = public_config.get(key="task.interval", get_type=int, default=39)

    # 创建组合触发器：周一到周五 + 9:00-20:00 + 间隔
    job1_trigger = AndTrigger([
        CronTrigger(day_of_week='mon-fri', hour='9-20'),
        IntervalTrigger(minutes=interval_minutes)
    ])

    job1 = scheduler.add_job(
        func=run_async_task,
        trigger=job1_trigger,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59',
        id='payment_check_job'
    )
    logger.info(f"添加Job1: 周一到周五 9:00-20:00，每{interval_minutes}分钟触发一次")

    job2 = scheduler.add_job(
        func=run_async_have_lunch_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='12',
        minute='49',
        start_date='2025-01-01 00:00:00',  # 修复无效日期字符串
        end_date='2025-12-31 23:59:59',
        id='lunch_reminder_job_49'
    )
    logger.info(f"添加Job2: 周一到周五 12:49触发")

    job3 = scheduler.add_job(  # 修复方法名错误
        func=run_async_have_lunch_task,
        trigger='cron',
        day_of_week='mon-fri',
        hour='12',
        minute='50',
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59',
        id='lunch_reminder_job_50'
    )
    logger.info(f"添加Job3: 周一到周五 12:50触发")

    job4 = scheduler.add_job(
        func=run_async_daily_reminder_task,
        trigger='cron',
        hour='11',
        minute='05',
        id='daily_reminder_job'
    )
    logger.info(f"添加Job4: 每天 11:05触发")

    try:
        scheduler.start()
        logger.info(f"当前注册的任务：{scheduler.get_jobs()}")
        logger.info("定时任务调度器已启动")

        # 发送启动通知
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            safe_async_run(send_telegram_message,
                f"定时任务调度器已启动，配置了{len(scheduler.get_jobs())}个任务\n"
                f"支付检查任务执行时间：周一到周五 9:00-20:00，每{interval_minutes}分钟一次\n"
                f"每日提醒时间：每天 11:05"
            )

        logger.info("测试直接发送 Telegram 消息")
        safe_async_run(send_telegram_message, "✅ 测试：调度线程中直接发送 Telegram 成功")
    except Exception as e:
        logger.error(f"启动定时任务时出错: {e}")
        # 尝试发送错误通知
        try:
            if public_config and public_config.get(key='telegram.enable', get_type=bool):
                safe_async_run(send_telegram_message, f"启动定时任务时出错: {e}")
        except Exception as te:
            logger.error(f"发送Telegram错误消息失败: {te}")


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
            safe_async_run(send_telegram_message, "定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止定时任务时出错: {e}")
        # 确保Telegram已启用
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            safe_async_run(send_telegram_message, f"停止定时任务时出错: {e}")