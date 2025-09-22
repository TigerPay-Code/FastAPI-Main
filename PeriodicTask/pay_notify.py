#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading

from Logger.logger_config import setup_logger
from Telegram.auto_bot import send_telegram_message

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

def start_check_balance():
    message = f"一分钟任务开始执行"
    logger.info(message)  # 添加日志记录
    send_telegram_message(message)

def start_check_balance_task():
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

def start_task():
    # 使用守护线程启动定时任务
    threading.Thread(target=start_check_balance_task, daemon=True).start()
    logger.info("定时任务线程已启动")