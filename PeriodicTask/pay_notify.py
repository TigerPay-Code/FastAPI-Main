#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/10/09
# @IDE       : PyCharm
# @Function  : 异步定时任务调度器（修正版，支持 Telegram 实时提醒）

import asyncio
import os
from datetime import datetime, time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from Config.config_loader import public_config
from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

# ============================================================
# 日志初始化
# ============================================================
log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

scheduler: AsyncIOScheduler | None = None


# ============================================================
# 异步任务函数
# ============================================================

async def have_lunch():
    """提醒吃午饭"""
    try:
        message = "🍱 吃午饭时间到，午饭开始啦！"
        logger.info(message)
        if public_config.get(key="telegram.enable", get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.exception(f"定时任务[提醒吃午饭]出错: {e}")
        if public_config.get(key="telegram.enable", get_type=bool):
            await send_telegram_message(f"⚠️ 定时任务[提醒吃午饭]出错: {e}")


async def daily_reminder():
    """每日提醒"""
    try:
        message = "🕚 现在是上午11:05，每日巴西支付报表提醒！"
        logger.info(message)
        if public_config.get(key="telegram.enable", get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.exception(f"定时任务[每日提醒]出错: {e}")
        if public_config.get(key="telegram.enable", get_type=bool):
            await send_telegram_message(f"⚠️ 定时任务[每日提醒]出错: {e}")


async def check_pending_payments():
    """检查未处理支付通知"""
    try:
        time_gap = public_config.get(key="task.interval", get_type=int, default=1800)
        message = f"⏱ 每{time_gap}秒检查一次未处理支付通知的任务执行了。"
        logger.info(message)
        if public_config.get(key="telegram.enable", get_type=bool):
            await send_telegram_message(message)
    except Exception as e:
        logger.exception(f"定时任务[检查支付]出错: {e}")
        if public_config.get(key="telegram.enable", get_type=bool):
            await send_telegram_message(f"⚠️ 定时任务[检查支付]出错: {e}")


# ============================================================
# 工具函数
# ============================================================

def is_working_hours() -> bool:
    """判断当前时间是否在工作时间（周一至周五 9:00~20:00）"""
    now = datetime.now()
    if now.weekday() >= 5:  # 周六、周日
        return False
    return time(9, 0) <= now.time() <= time(20, 0)


async def run_all_tasks(task_id: str, task_name: str, message: str):
    """包装器：仅在工作时间执行检查"""

    logger.info(f"收到参数: {task_id}, {task_name}, {message}")

    if is_working_hours():
        await check_pending_payments()
    else:
        logger.info("当前非工作时间，跳过支付检查任务")


# ============================================================
# 调度器启动/停止
# ============================================================

def start_check_balance_task():
    """启动定时任务调度器"""
    global scheduler
    logger.info("启动周期性任务调度器（修正版）...")
    scheduler = AsyncIOScheduler()

    # ===============================
    # Job1: 支付检查
    # ===============================
    scheduler.add_job(
        id="check_job",
        name="定时检查未处理支付任务",
        func=run_all_tasks,
        args=['check_job', '定时检查未处理支付任务', '每隔半小时检查一次未处理支付任务'],
        trigger='cron',  # 改为 cron 触发器
        hour='9-20',  # 9点到20点
        day_of_week='mon-fri',  # 周一至周五
        minute='*/30',  # 每30分钟执行一次
        start_date='2024-01-01 00:00:00', # 开始时间
        end_date='2025-12-31 23:59:59', # 结束时间
        timezone='Asia/Shanghai'  # 时区
    )

    # ===============================
    # Job2: 午饭提醒（12:49）
    # ===============================
    scheduler.add_job(
        func=have_lunch,
        trigger=CronTrigger(day_of_week="mon-fri", hour=12, minute=49),
        id="lunch_reminder_1249",
        name="午饭提醒 12:49",
        start_date=datetime(2025, 1, 1, 0, 0, 0),  # 开始时间
        end_date=datetime(2025, 12, 31, 23, 59, 59)  # 结束时间
    )

    # ===============================
    # Job3: 午饭提醒（12:50）
    # ===============================
    scheduler.add_job(
        func=have_lunch,
        trigger=CronTrigger(day_of_week="mon-fri", hour=12, minute=50),
        id="lunch_reminder_1250",
        name="午饭提醒 12:50",
        start_date=datetime(2025, 1, 1, 0, 0, 0),  # 开始时间
        end_date=datetime(2025, 12, 31, 23, 59, 59)  # 结束时间
    )

    # ===============================
    # Job4: 每日巴西支付报表提醒（11:05）
    # ===============================
    scheduler.add_job(
        func=daily_reminder,
        trigger=CronTrigger(hour=11, minute=5),
        id="daily_reminder_1105",
        name="每日支付报表提醒",
        start_date=datetime(2025, 1, 1, 0, 0, 0),  # 开始时间
        end_date=datetime(2025, 12, 31, 23, 59, 59)  # 结束时间
    )

    # ===============================
    # 启动调度器
    # ===============================
    scheduler.start()
    logger.info(f"定时任务调度器已启动，共 {len(scheduler.get_jobs())} 个任务")

    # 启动后发送 Telegram 测试消息
    if public_config.get(key="telegram.enable", get_type=bool):
        asyncio.create_task(send_telegram_message(
            f"✅ 定时任务调度器已启动，共配置 {len(scheduler.get_jobs())} 个任务\n"
            f"支付检查任务：每 30 分钟执行一次（仅限工作时间）\n"
            f"每日提醒时间：每天 11:05\n"
            f"午餐提醒：周一至周五 12:49 与 12:50"
        ))
        asyncio.create_task(send_telegram_message("✅ 测试：调度器线程内 Telegram 实时消息发送成功"))


def start_periodic_task():
    """统一启动入口"""
    start_check_balance_task()


def stop_periodic_task():
    """停止定时任务调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("🛑 定时任务调度器已停止")
        if public_config.get(key="telegram.enable", get_type=bool):
            asyncio.create_task(send_telegram_message("🛑 定时任务调度器已停止"))
        scheduler = None


# ============================================================
# 独立调试入口
# ============================================================
if __name__ == "__main__":
    async def main():
        start_periodic_task()
        await asyncio.sleep(10)
        logger.info("✅ 调度器测试运行结束")

    asyncio.run(main())
