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
from telebot.types import BotCommand

# 引入配置文件
from Config.config_loader import public_config

# 引用数据库异步操作模块
from DataBase.async_mysql import mysql_manager
from DataBase.async_redis import redis_manager
import aiomysql

# 引用日志模块
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)

try:
    bot = telebot.TeleBot(token=public_config.get(key='telegram.token', get_type=str), parse_mode=None)
except Exception as e:
    logger.error(f"初始化Telegram机器人失败: {e}")
    bot = None


@bot.message_handler(commands=['id'])
def gei_chat_id(message):
    bot.reply_to(message, f"{message.chat.id}")


# 启动Telegram机器人
async def start_telegram_bot():
    global bot

    if bot:
        bot.delete_my_commands(scope=None, language_code=None)

        commands_list = [
            ("id", "查询聊天ID")
        ]

        com_set = []
        for com, desc in commands_list:
            try:
                com_set.append(BotCommand(command=com, description=desc))
            except Exception as e:
                logger.error(f"添加命令 {com} 时发生错误: {e}")

        bot.set_my_commands(commands=com_set)

        try:
            bot.infinity_polling(
                skip_pending=True,  # 跳过未处理的消息
                interval=1,  # 降低轮询间隔到 1 秒，提高响应速度
                timeout=20,  # 减少单次轮询超时时间，提高响应效率
                long_polling_timeout=20,  # 减少长轮询超时时间
                allowed_updates=[  # 明确指定需要处理的更新类型
                    "message",
                    "callback_query"
                    # "edited_message",
                    # "my_chat_member",  # 添加成员状态更新，用于检测机器人被添加/删除
                    # "chat_member"  # 添加群组成员变动监控
                ],
                none_stop=True,  # 发生错误时继续运行
                restart_on_change=True
            )
        except KeyboardInterrupt:
            logger.error("收到终止信号，正在优雅关闭机器人...")
        except telebot.apihelper.ApiException as api_error:
            logger.error(f"Telegram API 错误: {api_error}")
        except Exception as e:
            logger.error(f"机器人运行时发生错误: {str(e)}")
        finally:
            logger.error("机器人已停止运行")
    else:
        logger.error("Telegram机器人未初始化，无法启动")


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
        try:
            # 直接从管理器获取连接和客户端
            conn = await mysql_manager.acquire()
            redis = redis_manager.client

            cache_key = "send_telegram_message_to_admin"
            cached_data = await redis.get(cache_key)

            admin_chat_id = None

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
