#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : base.py
# @Time      : 2025/9/16 11:18
# @IDE       : PyCharm
# @Function  :
import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)


# 接收Pay-RX支付通知数据模型
class Pay_RX_Notify_In_Data(BaseModel):
    state: int = Field(title="代收状态", description="0-订单生成,1-支付中,2-支付成功,3-支付失败", default=0, ge=0, le=3)
    sysOrderNo: str = Field(title="平台订单号", description="系统订单号", min_length=4, max_length=36)
    mchOrderNo: str = Field(title="下游订单号", description="商户订单号", min_length=4, max_length=36)
    amount: int = Field(title="金额", description="单位分", ge=1000, le=1000000)
    extraField: Optional[str] = Field(title="扩展字段", description="可选字段", min_length=0, max_length=32, default=None)
    sign: str = Field(title="签名", description="签名值大写的MD5值", min_length=32, max_length=32)


class Pay_RX_Notify_Out_Data(BaseModel):
    state: int = Field(title="支付状态", description="0-订单生成,1-支付中,2-支付成功,3-支付失败", default=0)
    sysOrderNo: str = Field(title="平台订单号", description="系统订单号", min_length=4, max_length=36)
    mchOrderNo: str = Field(title="下游订单号", description="商户订单号", min_length=4, max_length=36)
    amount: int = Field(title="金额", description="单位分", ge=1, le=1000000)
    sign: str = Field(title="签名", description="签名值大写的MD5值", min_length=32, max_length=32)


class Pay_RX_Notify_Refund_Data(BaseModel):
    state: int = Field(title="退款状态", description="0-订单生成,1-退款中,2-退款成功,3-退款失败", default=0)
    sysOrderNo: str = Field(title="平台订单号", description="系统订单号", min_length=4, max_length=36)
    mchOrderNo: str = Field(title="下游订单号", description="商户订单号", min_length=4, max_length=36)
    amount: int = Field(title="金额", description="单位分", ge=1, le=1000000)
    sign: str = Field(title="签名", description="签名值大写的MD5值", min_length=32, max_length=32)

# try:
#     data = Pay_RX_Notify_In_Data(
#         state=3,  # 无效值
#         sysOrderNo="ORD123456",
#         mchOrderNo="MCH987654",
#         amount=5000,
#         sign="F0A7708FEB4B6C9C197A37AAA22FE3F4"
#     )
# except ValidationError as e:
#     print(e.errors())
