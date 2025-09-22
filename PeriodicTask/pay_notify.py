#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :
import threading

from apscheduler.schedulers.blocking import BlockingScheduler  # pip install apscheduler
from Telegram.auto_bot import send_telegram_message

# 引用数据库异步操作模块
from DataBase.async_mysql import mysql_manager, get_mysql_conn
from DataBase.async_redis import redis_manager, get_redis
import aiomysql

# 引用日志模块
import os
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)


def start_check_balance():
    message = f"一分钟任务开始执行"
    send_telegram_message(message)


def start_check_balance_task():
    check_balance = BlockingScheduler()
    check_balance.add_job(
        func=start_check_balance,
        trigger='interval',
        minutes=1,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59'
    )  # 每10分钟执行一次
    check_balance.start()



def start_task():
    threading.Thread(target=start_check_balance_task, daemon=True).start()

