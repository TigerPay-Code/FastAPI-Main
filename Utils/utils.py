#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : utils.py
# @Time      : 2025/9/16 14:33
# @IDE       : PyCharm
# @Function  :
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# 假设你已经定义了 SECRET_KEY 和 ALGORITHM
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    生成 JWT Token
    :param data: 载荷数据，通常包含用户ID
    :param expires_delta: Token 有效期
    :return: JWT 字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """
    解码 JWT Token
    :param token: JWT 字符串
    :return: 解码后的载荷或 None（如果 Token 无效）
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


print(create_access_token)
