#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : test.py
# @Time      : 2025/9/16 14:57
# @IDE       : PyCharm
# @Function  :
import uuid


print(f"生成的 UUID1 字符串: {str(uuid.uuid1())}")
print(f"生成的 UUID1 字符串: {str(uuid.uuid1())}")



# 生成一个 UUID 对象
uuid_obj = uuid.uuid4()

# 将其转换为字符串形式，这是最常见的用法
uuid_str = str(uuid_obj)
print(f"生成的 UUID4 字符串: {uuid_str}")
# 输出示例: 6b1d42a9-7c8a-4c2f-b413-d4d12a6f236e

# 获取32位的十六进制字符串（没有横杠）
uuid_hex = uuid_obj.hex
print(f"生成的32位十六进制字符串: {uuid_hex}")
# 输出示例: 6b1d42a97c8a4c2fb413d4d12a6f236e