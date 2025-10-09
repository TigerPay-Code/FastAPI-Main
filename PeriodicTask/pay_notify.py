#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/10/09
# @IDE       : PyCharm
# @Function  : 定时任务调度与Telegram提醒（异步版，支持实时推送）

import asyncio
import os
from datetime import datetime, time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from Config.config_loader import public_config
from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

# ========== 日志初始化 ==========
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

scheduler: AsyncIOScheduler | None = None


# ============================================================
# 异步任务函数
# ============================================================

async def have_lunch():
    """提醒吃午饭"""
    logger.info("吃午饭时间到！")
    try:
        message = '🍱 吃午饭时间到，午饭开始啦！'
        logger.info(message)

        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.exception(f"定时任务[提醒吃午饭]执行出错: {e}")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"⚠️ 定时任务[提醒吃午饭]执行出错: {e}")


async def daily_reminder():
    """每日提醒"""
    logger.info("每日巴西支付报表提醒时间到！")
    try:
        message = '🕚 现在是上午11:05，每日巴西支付报表提醒！'
        logger.info(message)

        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.exception(f"定时任务[巴西支付报表]执行出错: {e}")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"⚠️ 定时任务[巴西支付报表]执行出错: {e}")


async def check_pending_payments():
    """检查未处理支付通知的异步任务"""
    logger.info(">>> check_pending_payments() 被调用 <<<")
    try:
        # 模拟实际逻辑（数据库查询）
        time_gap = public_config.get(key="task.interval", get_type=int, default=39)
        message = f'⏱ 每{time_gap}分钟检查一次未处理支付通知的任务执行了。'
        logger.info(message)

        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.exception(f"定时任务[检查未处理支付]执行出错: {e}")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            await send_telegram_message(f"⚠️ 定时任务[检查未处理支付]执行出错: {e}")


# ============================================================
# 工具函数
# ============================================================

def is_working_hours() -> bool:
    """判断是否工作时间（周一到周五 9:00~20:00）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return time(9, 0) <= now.time() <= time(20, 0)


# ============================================================
# 调度器启动/停止
# ============================================================

def start_check_balance_task():
    """启动定时任务调度器"""
    global scheduler

    logger.info("启动周期性任务调度器（异步版）...")
    scheduler = AsyncIOScheduler()

    # 从配置读取任务间隔
    interval_minutes = public_config.get(key="task.interval", get_type=int, default=39)

    # Job1：检查支付任务
    job1_trigger = AndTrigger([
        CronTrigger(day_of_week='mon-fri', hour='9-20'),
        IntervalTrigger(minutes=interval_minutes)
    ])
    scheduler.add_job(
        func=check_pending_payments,
        trigger=job1_trigger,
        id='payment_check_job'
    )
    logger.info(f"添加 Job1：周一到周五 9:00-20:00，每 {interval_minutes} 分钟执行一次")

    # Job2：午饭提醒 12:49
    scheduler.add_job(
        func=have_lunch,
        trigger='cron',
        day_of_week='mon-fri',
        hour=12,
        minute=49,
        id='lunch_reminder_job_49'
    )
    logger.info("添加 Job2：周一到周五 12:49 提醒吃午饭")

    # Job3：午饭提醒 12:50
    scheduler.add_job(
        func=have_lunch,
        trigger='cron',
        day_of_week='mon-fri',
        hour=12,
        minute=50,
        id='lunch_reminder_job_50'
    )
    logger.info("添加 Job3：周一到周五 12:50 提醒吃午饭")

    # Job4：每日巴西报表提醒 11:05
    scheduler.add_job(
        func=daily_reminder,
        trigger='cron',
        hour=11,
        minute=5,
        id='daily_reminder_job'
    )
    logger.info("添加 Job4：每天 11:05 发送报表提醒")

    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器已启动")

    # 启动后立即测试 Telegram 发送
    if public_config and public_config.get(key='telegram.enable', get_type=bool):
        asyncio.create_task(send_telegram_message(
            f"✅ 定时任务调度器已启动，共配置 {len(scheduler.get_jobs())} 个任务\n"
            f"支付检查任务：周一到周五 9:00~20:00，每 {interval_minutes} 分钟执行一次\n"
            f"每日提醒时间：每天 11:05\n"
            f"午餐提醒：周一至周五 12:49 与 12:50"
        ))
        asyncio.create_task(send_telegram_message("✅ 测试：调度器线程内 Telegram 实时消息发送成功"))


def start_periodic_task():
    """外部统一入口（兼容旧调用方式）"""
    start_check_balance_task()


def stop_periodic_task():
    """停止调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("定时任务调度器已停止")
        if public_config and public_config.get(key='telegram.enable', get_type=bool):
            asyncio.create_task(send_telegram_message("🛑 定时任务调度器已停止"))
        scheduler = None


# ============================================================
# 模块直接运行测试（非生产）
# ============================================================
#
# if __name__ == "__main__":
#     # 仅用于独立测试时运行
#     import asyncio
#
#     async def main():
#         start_periodic_task()
#         await asyncio.sleep(5)
#         print("等待调度器运行中...")
#
#     asyncio.run(main())
