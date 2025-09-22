#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import os
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading

from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

# 全局调度器实例
scheduler = None


def start_check_balance():
    """定时任务执行函数"""
    message = f"一分钟任务开始执行 - 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    logger.info(message)
    send_telegram_message(message)


def init_scheduler():
    """初始化调度器"""
    global scheduler
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=start_check_balance,
            trigger=IntervalTrigger(minutes=1),
            id='minute_check_balance',
            replace_existing=True,
            start_date='2025-01-01 00:00:00',
            end_date='2025-12-31 23:59:59'
        )
        scheduler.start()
        logger.info("一分钟定时任务已启动")

        # 立即执行一次
        start_check_balance()

    except Exception as e:
        logger.error(f"启动定时任务失败: {e}")


def shutdown_scheduler():
    """关闭调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务已停止")
    scheduler = None


def get_scheduler():
    """获取调度器实例"""
    return scheduler
