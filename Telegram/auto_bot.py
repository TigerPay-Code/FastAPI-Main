#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : auto_bot.py
# @Time      : 2025/9/18 11:58
# @IDE       : PyCharm
# @Function  :
import json
import os

import telebot  # pip3 install --upgrade pyTelegramBotAPI

# 引入配置文件
from Config.config_loader import public_config

# 引用数据库异步操作模块
from DataBase.async_mysql import mysql_manager, get_mysql_conn
from DataBase.async_redis import redis_manager, get_redis
import aiomysql
from fastapi import Depends

# 引用日志模块
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

try:
    bot = telebot.TeleBot(token=public_config.get(key='telegram.token', get_type=str), parse_mode=None)
except Exception as e:
    logger.error(f"初始化Telegram机器人失败: {e}")
    bot = None


# 启动Telegram机器人
def start_telegram_bot():
    global bot

    if bot:
        bot.delete_my_commands(scope=None, language_code=None)

    commands_list = [
        ("bxs", "查询半小时 代收、代付"),
        ("yxs", "查询一小时 代收、代付"),
        ("wdf", "查询所有未代付的订单"),
        ("td", "设置通道开关"),
        ("sh", "查看商户信息"),
        ("ctc", "查询充值、提现统计"),
        ("usdt", "发送USDT充值地址和图片")
    ]


if public_config and public_config.get(key='software.system', get_type=str) == 'windows':
    # 初始化Telegram机器人
    start_telegram_bot()
    logger.info("初始化Telegram机器人成功")
else:
    # 初始化Telegram机器人
    start_telegram_bot()
    logger.info("初始化Telegram机器人成功")


async def send_telegram_message(message: str):
    global bot

    if bot:
        conn = None
        redis = None
        try:
            # 直接从管理器获取连接和客户端
            conn = await mysql_manager.acquire()
            redis = redis_manager.client

            cache_key = "send_telegram_message_to_admin"
            cached_data = await redis.get(cache_key)

            if cached_data:
                admin_chat_id = json.loads(cached_data)
            else:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT `chat_id` FROM `telegram_users` order by `chat_id`")
                    admin_chat_id = await cur.fetchall()
                    await redis.set(cache_key, json.dumps(admin_chat_id), ex=3600)

            for chat_id in admin_chat_id:
                if chat_id['chat_id']:
                    bot.send_message(chat_id=chat_id['chat_id'], text=message)
            logger.info(f"发送Telegram消息成功, 消息内容: {message}")
        except Exception as aa:
            logger.error(f"发送Telegram消息失败: 错误信息: {aa}")
        finally:
            if conn:
                await mysql_manager.release(conn)
    else:
        logger.error("Telegram机器人未初始化，无法发送消息")