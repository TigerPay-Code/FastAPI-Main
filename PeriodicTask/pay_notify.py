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
# 工具函数
# ============================================================
async def run_all_tasks(task_id: str, task_name: str, message: str):
    """包装器：仅在工作时间执行检查"""
    logger.info(f"收到参数: {task_id}, {task_name}, {message}")
    if task_id == "check_job":
        await send_telegram_message(message)
    elif task_id == "lunch_one" or task_id == "lunch_two":
        await send_telegram_message(message)
    elif task_id == "report":
        await send_telegram_message(message)
    else:
        logger.warning(f"未知任务 ID: {task_id}")


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
        day_of_week='mon-fri',  # 周一至周五
        hour='9-20',  # 9点到20点
        minute='*/30',  # 每30分钟执行一次
        start_date='2024-01-01 00:00:00',  # 开始时间
        end_date='2025-12-31 23:59:59',  # 结束时间
        timezone='Asia/Shanghai'  # 时区
    )

    # ===============================
    # Job2: 午饭提醒（12:49）
    # ===============================
    scheduler.add_job(
        id="lunch_one",
        name="吃午饭提醒",
        func=run_all_tasks,
        args=['lunch_one', '吃午饭提醒', '12:49 提醒吃午饭'],
        trigger='cron',  # 改为 cron 触发器
        day_of_week='mon-fri',  # 周一至周五
        hour=12,
        minute=49,
        start_date='2024-01-01 00:00:00',  # 开始时间
        end_date='2025-12-31 23:59:59',  # 结束时间
        timezone='Asia/Shanghai'  # 时区
    )

    # ===============================
    # Job3: 午饭提醒（12:50）
    # ===============================
    scheduler.add_job(
        id="lunch_two",
        name="吃午饭提醒",
        func=run_all_tasks,
        args=['lunch_two', '吃午饭提醒', '12:50 提醒吃午饭'],
        trigger='cron',  # 改为 cron 触发器
        day_of_week='mon-fri',  # 周一至周五
        hour=12,
        minute=50,
        start_date='2024-01-01 00:00:00',  # 开始时间
        end_date='2025-12-31 23:59:59',  # 结束时间
        timezone='Asia/Shanghai'  # 时区
    )

    # ===============================
    # Job4: 每日巴西支付报表提醒（11:05）
    # ===============================
    scheduler.add_job(
        id="report",
        name="巴西支付日统计报表提醒",
        func=run_all_tasks,
        args=['report', '支付报表', '11:05 巴西支付日统计报表提醒'],
        trigger='cron',  # 改为 cron 触发器
        day_of_week='mon-fri',  # 周一至周五
        hour=11,
        minute=5,
        start_date='2024-01-01 00:00:00',  # 开始时间
        end_date='2025-12-31 23:59:59',  # 结束时间
        timezone='Asia/Shanghai'  # 时区
    )

    # ===============================
    # 启动调度器
    # ===============================
    scheduler.start()
    logger.info(f"定时任务调度器已启动，共 {len(scheduler.get_jobs())} 个任务")

    # 启动后发送 Telegram 测试消息
    if public_config.get(key="telegram.enable", get_type=bool):
        asyncio.create_task(send_telegram_message(f"定时任务调度器已启动，共 {len(scheduler.get_jobs())} 个任务"))


def start_periodic_task():
    """统一启动入口"""
    start_check_balance_task()


def stop_periodic_task():
    """停止定时任务调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("定时任务调度器已停止")
        if public_config.get(key="telegram.enable", get_type=bool):
            asyncio.create_task(send_telegram_message("定时任务调度器已停止"))
        scheduler = None
