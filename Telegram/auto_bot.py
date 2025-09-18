#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : auto_bot.py
# @Time      : 2025/9/18 11:58
# @IDE       : PyCharm
# @Function  :
import os

import telebot  # pip3 install --upgrade pyTelegramBotAPI

# 引入配置文件
from Config.config_loader import public_config

# 引用日志模块
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

try:
    bot = telebot.TeleBot(token=public_config.get(key='telegram.token', get_type=str), parse_mode=None)
except Exception as e:
    logger.error(f"init telegram bot error: {e}")
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
    os.system('title 自动交易机器人')
    # 初始化Telegram机器人
    start_telegram_bot()
    logger.info("Telegram bot started successfully.")
else:
    # 初始化Telegram机器人
    start_telegram_bot()
    logger.info("Telegram bot started successfully.")


def send_telegram_message(message: str):
    global bot

    try:
        bot.send_message(chat_id=public_config.get(key='telegram.chat_id', get_type=str), text=message)
    except Exception as aa:
        logger.error(f"send_telegram_message error: {aa}")


if __name__ == "__main__":
    send_telegram_message("hello world")
