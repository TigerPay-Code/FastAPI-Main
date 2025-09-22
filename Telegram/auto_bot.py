#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : auto_bot.py
# @Time      : 2025/9/18 11:58
# @IDE       : PyCharm
# @Function  :
import json
import os

import re
import telebot  # pip3 install --upgrade pyTelegramBotAPI
from telebot import types
from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
import threading

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

bot = None
bot_initialized = False  # 添加初始化状态标志

try:
    token = public_config.get("telegram", "token", get_type=str, default='')
    if token and isinstance(token, str) and token.strip():
        # 初始化 Telegram Bot
        bot = telebot.TeleBot(token=token)
        bot_initialized = True
        logger.info("Telegram Bot 初始化成功")
    else:
        logger.error("获取 Telegram token 失败或 token 为空")
except Exception as err:
    bot_initialized = False
    logger.info(f"初始化 Telegram Bot 失败: {err}")


def get_chat_id_handler(message):
    if not bot_initialized:
        logger.error("Bot 未初始化，无法处理消息")
        return

    chat_id = message.chat.id
    bot.send_message(chat_id, f"你的聊天ID是: {chat_id}")


def handle_bot_click(message):
    if not bot_initialized:
        logger.error("Bot 未初始化，无法处理消息")
        return

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


# 处理按钮点击事件
if bot_initialized:
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
    if not bot_initialized:
        logger.error("Bot 未初始化，无法启动轮询")
        return

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


def start_bot():
    if not bot_initialized:
        logger.error("Bot 未初始化，无法启动")
        return

    # 启动轮询线程
    threading.Thread(target=run_bot, daemon=True).start()

    # 删除旧命令
    bot.delete_my_commands(scope=None, language_code=None)

    # 注册命令处理器
    bot.register_message_handler(get_chat_id_handler, commands=["id"])
    bot.register_message_handler(handle_bot_click, commands=["test"])

    commands_list = [
        ("id", "查询聊天ID"),
        ("test", "测试 InlineKeyboardMarkup")
    ]

    com_set = []
    for com, desc in commands_list:
        try:
            com_set.append(BotCommand(command=com, description=desc))
        except Exception as err:
            print(f"添加命令 {com} 时发生错误: {err}")

    bot.set_my_commands(commands=com_set)


def stop_bot():
    if bot_initialized:
        bot.stop_polling()


@bot.message_handler(commands=['id'])
@bot.message_handler(commands=['id'])
def gei_chat_id(message):
    if not bot_initialized:
        logger.error("Bot 未初始化，无法处理消息")
        return
    bot.reply_to(message, f"{message.chat.id}")


async def send_telegram_message(message: str):
    if not bot_initialized:
        logger.error("Telegram机器人未初始化，无法发送消息")
        return

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
if bot_initialized:
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
