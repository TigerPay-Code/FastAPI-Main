#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : test.py
# @Time      : 2025/9/19 10:18
# @IDE       : PyCharm
# @Function  :


import telebot
import threading
from typing import Optional, Callable


class TelegramBot:
    def __init__(self, token: str):
        """
        初始化 Telegram Bot
        :param token: 你的 Bot Token
        :param parse_mode: 消息解析模式 (HTML / Markdown)
        """
        self.bot = telebot.TeleBot(token)

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

    def polling(self, none_stop: bool = True, interval: int = 0, timeout: int = 20):
        """
        开启轮询
        """
        print("Telegram Bot started polling...")
        self.bot.polling(none_stop=none_stop, interval=interval, timeout=timeout)


# 注册一个简单的命令处理
def start_handler(message):
    telegram_bot.send_message(message.chat.id, "Hello! 我是你的 FastAPI Telegram Bot 🤖")


def run_bot():
    telegram_bot.polling()


def telegram_send_message(text: str,chat_id: int | str = 5312177749):
    telegram_bot.send_message(chat_id, text)


# 示例用法
if __name__ == "__main__":
    TOKEN = "8263751942:AAH5rvEopgKEERvUa9peWZ-TnctU230rHUU"
    telegram_bot = TelegramBot(token=TOKEN)

    telegram_bot.register_message_handler(start_handler, commands=["start"])

    threading.Thread(target=run_bot, daemon=True).start()

    telegram_bot.send_message(chat_id=5312177749, text="Hello! 我是你的 FastAPI Telegram Bot 🤖")
    telegram_send_message(text="Hello! 我是你的 FastAPI Telegram Bot 🤖")

    run_bot()