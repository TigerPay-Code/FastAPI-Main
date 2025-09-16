#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : base.py
# @Time      : 2025/9/16 11:18
# @IDE       : PyCharm
# @Function  :
from pydantic import BaseModel, Field


class Notify_In_Data(BaseModel):
    state: int = Field(
        title="代收状态",
        description="0-订单生成,1-支付中,2-支付成功,3-支付失败",
        default=0
    )
    sysOrderNo: str = Field(
        title="平台订单号",
        description="系统订单号",
        min_length=4,
        max_length=36
    )
    mchOrderNo: str = Field(
        title="下游订单号",
        description="商户订单号",
        min_length=4,
        max_length=36
    )

    amount: int = Field(
        title="金额",
        description="单位分",
        ge=1000,
        le=1000000000
    )
    sign: str = Field(
        title="签名",
        description="签名值大写的MD5值",
        min_length=32,
        max_length=32
    )


class Notify_Out_Data(BaseModel):
    state: int = Field(
        title="支付状态",
        description="0-订单生成,1-支付中,2-支付成功,3-支付失败",
        default=0
    )
    sysOrderNo: str = Field(
        title="平台订单号",
        description="系统订单号",
        min_length=4,
        max_length=36
    )
    mchOrderNo: str = Field(
        title="下游订单号",
        description="商户订单号",
        min_length=4,
        max_length=36
    )

    amount: int = Field(
        title="金额",
        description="单位分",
        ge=1,
        le=1000000000
    )
    sign: str = Field(
        title="签名",
        description="签名值大写的MD5值",
        min_length=32,
        max_length=32
    )

class Notify_Refund_Data(BaseModel):
    state: int = Field(
        title="支付状态",
        description="0-订单生成,1-支付中,2-支付成功,3-支付失败",
        default=0
    )
    sysOrderNo: str = Field(
        title="平台订单号",
        description="系统订单号",
        min_length=4,
        max_length=36
    )
    mchOrderNo: str = Field(
        title="下游订单号",
        description="商户订单号",
        min_length=4,
        max_length=36
    )

    amount: int = Field(
        title="金额",
        description="单位分",
        ge=1,
        le=1000000000
    )
    sign: str = Field(
        title="签名",
        description="签名值大写的MD5值",
        min_length=32,
        max_length=32
    )