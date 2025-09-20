#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : test.py
# @Time      : 2025/9/19 10:18
# @IDE       : PyCharm
# @Function  :
import telebot
from typing import Optional, Callable
from fastapi import FastAPI
import threading
from telebot.types import BotCommand
# 引用生命期管理器模块
from contextlib import asynccontextmanager


class TelegramBot:
    def __init__(self, token: str, parse_mode: str = "HTML"):
        """
        初始化 Telegram Bot
        :param token: 你的 Bot Token
        :param parse_mode: 消息解析模式 (HTML / Markdown)
        """
        self.bot = telebot.TeleBot(token, parse_mode=parse_mode)

    def send_message(self, chat_id: int | str, text: str, reply_to_message_id: Optional[int] = None):
        """
        发送消息
        :param chat_id: 接收方 chat_id
        :param text: 消息内容
        :param reply_to_message_id: 可选，回复的消息 ID
        """
        return self.bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)

    def register_message_handler(self, func: Callable, commands: Optional[list[str]] = None,
                                 regexp: Optional[str] = None):
        """
        注册消息处理器
        :param func: 回调函数，必须接受一个 Message 参数
        :param commands: 指令列表，例如 ["/start", "/help"]
        :param regexp: 正则匹配规则
        """
        self.bot.register_message_handler(func, commands=commands, regexp=regexp)

    def infinity_polling(self, interval: int = 0, timeout: int = 20, allowed_updates=None):
        """
        持续轮询
        """
        self.bot.infinity_polling(interval=interval, timeout=timeout)

    def polling(self, none_stop: bool = True, interval: int = 0, timeout: int = 20):
        """
        开启轮询
        """
        print("Telegram Bot started polling...")
        self.bot.polling(none_stop=none_stop, interval=interval, timeout=timeout)

    def stop_polling(self):
        """
        停止轮询
        """
        self.bot.stop_polling()

    def get_me(self):
        """
        获取 Bot 信息
        """
        return self.bot.get_me()

    def delete_my_commands(self, scope=None, language_code=None):
        self.bot.delete_my_commands(scope=scope, language_code=language_code)

    def set_my_commands(self, commands, scope=None, language_code=None):
        self.bot.set_my_commands(commands, scope=scope, language_code=language_code)


BOT_TOKEN = '8263751942:AAH5rvEopgKEERvUa9peWZ-TnctU230rHUU'
CHAT_ID = 5312177749


telegram_bot = TelegramBot(token=BOT_TOKEN)


def start_handler(message):
    telegram_bot.send_message(message.chat.id, "Hello! 我是你的 FastAPI Telegram Bot 🤖")


def get_chat_id_handler(message):
    chat_id = message.chat.id
    telegram_bot.send_message(chat_id, f"你的聊天ID是: {chat_id}")


def get_me_handler(message):
    chat_id = message.chat.id
    telegram_bot.get_me()
    telegram_bot.send_message(chat_id, f"你的聊天ID是: {telegram_bot.get_me()}")


telegram_bot.register_message_handler(start_handler, commands=["start"])
telegram_bot.register_message_handler(get_chat_id_handler, commands=["id"])
telegram_bot.register_message_handler(get_me_handler, commands=["me"])


def run_bot():
    telegram_bot.infinity_polling(
        allowed_updates=[  # 明确指定需要处理的更新类型
            "message",
            "callback_query"
            # "edited_message",
            # "my_chat_member",  # 添加成员状态更新，用于检测机器人被添加/删除
            # "chat_member"  # 添加群组成员变动监控
        ]
    )


def stop_bot():
    telegram_bot.stop_polling()


def start_bot():
    threading.Thread(target=run_bot, daemon=True).start()
    telegram_bot.delete_my_commands(scope=None, language_code=None)

commands_list = [
    ("id", "查询聊天ID"),
    ("me", "查询自己的信息")
]

com_set = []
for com, desc in commands_list:
    try:
        com_set.append(BotCommand(command=com, description=desc))
    except Exception as e:
        print(f"添加命令 {com} 时发生错误: {e}")

telegram_bot.set_my_commands(commands=com_set)


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    start_bot()

    # 应用生命周期结束时执行
    yield
    # 应用关闭时执行
    stop_bot()


app = FastAPI(title="FastAPI + Telegram Bot", lifespan=lifespan_manager)

@app.get("/")
async def root():
    return {"message": "FastAPI is running with Telegram Bot"}


@app.get("/send/{text}")
async def send_message(text: str):
    telegram_bot.send_message(CHAT_ID, text)
    return {"status": "sent", "message": text}
