#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : test.py
# @Time      : 2025/9/19 10:18
# @IDE       : PyCharm
# @Function  :
import re

import telebot  # pip3 install --upgrade pyTelegramBotAPI
from telebot import types
from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

from fastapi import FastAPI
import threading

# 引用生命期管理器模块
from contextlib import asynccontextmanager

# 引入配置文件
# from Config.config_loader import public_config

# 引用数据库异步操作模块
# from DataBase.async_mysql import mysql_manager
# from DataBase.async_redis import redis_manager
# import aiomysql

# 引用日志模块
# import os
# from Logger.logger_config import setup_logger
#
# log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
# logger = setup_logger(log_name)

Cancel_Button = InlineKeyboardButton(text="取消", callback_data="Cancel")

bot = None

try:
    bot = telebot.TeleBot(token='8263751942:AAH5rvEopgKEERvUa9peWZ-TnctU230rHUU')
except Exception as e:
    print(f"初始化 Telegram Bot 失败: {e}")


def start_handler(message):
    bot.send_message(message.chat.id, "Hello! 我是你的 FastAPI Telegram Bot 🤖")


def get_chat_id_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"你的聊天ID是: {chat_id}")


def get_me_handler(message):
    chat_id = message.chat.id
    bot.get_me()
    bot.send_message(chat_id, f"你的聊天ID是: {bot.get_me()}")


def handle_bot_click(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()

    # 第一行：三个按钮
    markup.row(
        InlineKeyboardButton(text='选项1', callback_data='Option1'),
        InlineKeyboardButton(text='选项2', callback_data='Option2'),
        InlineKeyboardButton(text='选项3', callback_data='Option3')
    )

    # 第二行：两个按钮
    markup.row(
        InlineKeyboardButton(text='选项4', callback_data='Option4'),
        InlineKeyboardButton(text='选项5', callback_data='Option5')
    )

    # 第三行：一个按钮（查看）
    markup.row(InlineKeyboardButton(text='查看', callback_data='View'))

    # 第四行：一个按钮（取消）
    markup.row(InlineKeyboardButton(text='取消', callback_data='Cancel'))

    bot.send_message(chat_id, "请选择一个需要查看的商户：", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == "View":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="你点击了查看按钮")
    elif call.data == "Cancel":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="你取消了操作")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.answer_callback_query(callback_query_id=call.id, text="未知操作")


def run_bot():
    bot.infinity_polling(
        allowed_updates=[  # 明确指定需要处理的更新类型
            "message",  # 处理消息
            "callback_query",  # 处理回调查询（按钮点击）
            "inline_query",  # 处理内联查询（搜索框）
            "chosen_inline_result",  # 处理选择的内联结果
            "shipping_query",  # 处理货运查询
            "pre_checkout_query",  # 处理预结账查询
            "poll",  # 处理投票
            "poll_answer",  # 处理投票答案
            "my_chat_member",  # 添加成员状态更新，用于检测机器人被添加/删除
            "chat_member",  # 添加群组成员变动监控
            "edited_message",  # 处理编辑过的消息
            "channel_post",  # 处理频道帖子
            "edited_channel_post"  # 处理编辑过的频道帖子
        ]
    )


def stop_bot():
    bot.stop_polling()


def start_bot():
    threading.Thread(target=run_bot, daemon=True).start()

    # 删除旧命令
    bot.delete_my_commands(scope=None, language_code=None)

    # 注册命令处理器
    bot.register_message_handler(start_handler, commands=["start"])
    bot.register_message_handler(get_chat_id_handler, commands=["id"])
    bot.register_message_handler(get_me_handler, commands=["me"])
    bot.register_message_handler(handle_bot_click, commands=["test"])

    commands_list = [
        ("id", "查询聊天ID"),
        ("me", "查询自己的信息"),
        ("test", "测试 InlineKeyboardMarkup")
    ]

    com_set = []
    for com, desc in commands_list:
        try:
            com_set.append(BotCommand(command=com, description=desc))
        except Exception as err:
            print(f"添加命令 {com} 时发生错误: {err}")

    bot.set_my_commands(commands=com_set)


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    start_bot()
    # 应用生命周期结束时执行
    yield
    # 应用关闭时执行
    stop_bot()


app = FastAPI(title="FastAPI + Telegram Bot", lifespan=lifespan_manager)


def get_custom_title_safe(member) -> str | None:
    """
    安全获取自定义头衔
    返回: 头衔字符串（可能为空）或 None（如果不是管理员）
    """
    # 1. 检查管理员状态
    if getattr(member, 'status', None) != "administrator":
        return None

    # 2. 安全获取属性
    title = getattr(member, 'custom_title', None)

    # 3. 处理不同情况
    if title is None:
        # 属性不存在（旧版API）
        return None
    if isinstance(title, str):
        # 清理头衔
        return re.sub(r'[\n\r\t]', '', title).strip()

    return None


def format_title_display(title: str) -> str:
    """格式化头衔显示"""
    if title is None:
        return "管理员"
    if title == "":
        return "管理员"
    return title


# 处理成员变动
@bot.chat_member_handler()
def handle_member_changes(update: types.ChatMemberUpdated):
    try:
        old = update.old_chat_member
        new = update.new_chat_member
        chat = update.chat

        # 新成员加入
        if old.status in ["left", "kicked", None] and new.status == "member":
            # 排除机器人自己
            if new.user.is_bot:
                print(f"检测到机器人加入，跳过欢迎: {new.user.first_name}")
                return

            print(f"检测到新成员加入: {new.user.first_name} 在群组 {chat.id}")

            welcome_msg = f"欢迎 {new.user.first_name} 加入群组！🎉"
            bot.send_message(chat.id, welcome_msg)


        # 成员离开
        elif old.status == "member" and new.status in ["left", "kicked"]:
            # 排除机器人自己
            if new.user.is_bot:
                print(f"检测到机器人离开，跳过告别: {new.user.first_name}")
                return

            print(f"检测到成员离开: {new.user.first_name} 从群组 {chat.id}")

            farewell_msg = f"{new.user.first_name} 已离开群组。👋"
            bot.send_message(chat.id, farewell_msg)

        # 获取头衔
        old_title = get_custom_title_safe(old)
        new_title = get_custom_title_safe(new)

        # 状态变化：成为管理员
        if old.status != "administrator" and new.status == "administrator":
            display = format_title_display(new_title)
            msg = f"🎖️ {new.user.first_name} 成为{display}"
            bot.send_message(update.chat.id, msg)

        # 管理员权限变更
        elif old.status == "administrator" and new.status == "administrator":
            if old_title != new_title:
                old_display = format_title_display(old_title)
                new_display = format_title_display(new_title)

                operator = update.from_user.first_name
                msg = f"📛 {operator} 更新了头衔: {old_display} → {new_display}"
                bot.send_message(update.chat.id, msg)

    except Exception as err:
        print(f"处理管理员变更出错: {err}")


@app.get("/")
async def root():
    return {"message": "FastAPI is running with Telegram Bot"}


@app.get("/send/{text}")
async def send_message(text: str):
    bot.send_message(chat_id=5312177749, text=text)
    return {"status": "sent", "message": text}
