#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : pay_notify.py
# @Time      : 2025/9/22 13:45
# @IDE       : PyCharm
# @Function  :

from apscheduler.schedulers.blocking import BlockingScheduler
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
    # 连接数据库
    mysql_conn = get_mysql_conn()
    # 连接redis
    redis_conn = get_redis()
    # 查询数据库中所有用户的余额
    async def get_user_balance():
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT id, username, balance FROM user_info")
            user_balance_list = await cur.fetchall()
        return user_balance_list

    # 遍历用户余额，如果余额小于1000，则发送通知
    async def send_notify(user_balance_list):
        for user_balance in user_balance_list:
            if user_balance['balance'] < 0.70:
                user_id = user_balance['id']
                balance = user_balance['balance']
                # 发送通知
                message = f"用户{id}的余额为{balance}元，请及时充值！"
                await send_telegram_message(message)
                # 记录日志
                logger.info(f"用户{id}余额为{balance}元，已发送通知")


def start_check_balance_task():
    check_balance = BlockingScheduler()
    check_balance.add_job(
        func=start_check_balance,
        trigger='interval',
        minutes=10,
        start_date='2025-01-01 00:00:00',
        end_date='2025-12-31 23:59:59'
    )  # 每10分钟执行一次
    check_balance.start()