#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author    : 贺鉴龙
# @File      : base.py
# @Time      : 2025/9/16 11:18
# @IDE       : PyCharm
# @Function  :
import os
import re
import urllib
import hashlib
import urllib.parse
from typing import Dict, List, Any, Optional
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

    # ========== 字段验证器 ==========
    @field_validator('state')
    @classmethod
    def validate_state(cls, v: int) -> int:
        """验证状态值是否有效"""
        if v not in [0, 1, 2, 3]:
            logger.error(f'状态码验证失败: 传入值{v}，无效状态码。'
                         '允许值: 0(订单生成), 1(支付中), 2(支付成功), 3(支付失败)')
            raise ValueError(
                f'无效状态码: {v}。'
                '允许值: 0(订单生成), 1(支付中), 2(支付成功), 3(支付失败)')
        return v

    @field_validator('sysOrderNo', 'mchOrderNo')
    @classmethod
    def validate_order_no_format(cls, v: str) -> str:
        """验证订单号格式"""
        if not re.match(r'^[a-zA-Z0-9_-]{4,36}$', v):
            logger.error(f'订单号验证失败: 传入值{v}，订单号只能包含字母、数字、下划线和连字符')
            raise ValueError('订单号只能包含字母、数字、下划线和连字符')
        return v

    @field_validator('sign')
    @classmethod
    def validate_sign_format(cls, v: str) -> str:
        """验证签名格式"""
        if not re.match(r'^[A-Z0-9]{32}$', v):
            logger.error(f'签名验证失败: 传入值{v}，签名必须是32位大写MD5值')
            raise ValueError('签名必须是32位大写MD5值')
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount_range(cls, v: int) -> int:
        """验证金额范围"""
        if not (1000 <= v <= 1000000):
            logger.error(f'金额验证失败: 传入值{v}分，金额必须在1000到1000000分之间')
            raise ValueError('金额必须在1000到1000000分之间')
        return v

    # @field_validator('mchOrderNo')
    # @classmethod
    # def validate_mch_order_no_prefix(cls, v: str) -> str:
    #     """商户订单号前缀验证（示例）"""
    #     if not v.startswith('MCH_'):
    #         raise ValueError('商户订单号必须以MCH_开头')
    #     return v
    #
    # @field_validator('sysOrderNo')
    # @classmethod
    # def validate_sys_order_no_prefix(cls, v: str) -> str:
    #     """系统订单号前缀验证（示例）"""
    #     if not v.startswith('SYS_'):
    #         raise ValueError('系统订单号必须以SYS_开头')
    #     return v

    # ========== 模型验证器 ==========
    @model_validator(mode='after')
    def validate_signature(self) -> 'Pay_RX_Notify_In_Data':
        """
        签名验证流程：
        1. 获取参与签名的字段：state, sysOrderNo, mchOrderNo, amount
        2. 按参数名ASCII码从小到大排序
        3. 格式化为 key=value 字符串，用 & 连接
        4. 计算MD5并转为大写
        5. 与传入的sign比较
        """
        # 步骤1：准备签名数据
        sign_data = {
            "amount": self.amount,
            "mchOrderNo": self.mchOrderNo,
            "state": self.state,  # 使用枚举值（整数）
            "sysOrderNo": self.sysOrderNo
        }

        # 步骤2：按参数名ASCII码从小到大排序
        sorted_items = self._sort_params(sign_data)

        # 步骤3：构建签名字符串
        sign_str = self._build_sign_string(sorted_items)

        # 步骤4：计算签名
        calculated_sign = self._calculate_md5(sign_str)

        # 步骤5：验证签名
        if not self._safe_compare_sign(calculated_sign, self.sign):
            logger.error(f'签名验证失败: 计算签名={calculated_sign}, 传入签名={self.sign}')
            raise ValueError(f'签名验证失败:传入签名={self.sign}')
        return self

    def _sort_params(self, params: Dict[str, Any]) -> List[tuple]:
        """按参数名ASCII码从小到大排序"""
        return sorted(params.items(), key=lambda x: x[0])

    def _build_sign_string(self, sorted_items: List[tuple]) -> str:
        """构建签名字符串：key1=value1&key2=value2"""
        return '&'.join(
            f"{key}={self._format_value(value)}"
            for key, value in sorted_items
        )

    def _format_value(self, value: Any) -> str:
        """特殊值处理（根据业务需求）"""
        # 金额保持整数形式
        if isinstance(value, int):
            return str(value)
        # 字符串进行URL编码（根据业务需求决定是否需要）
        return urllib.parse.quote_plus(str(value))

    def _calculate_md5(self, sign_str: str) -> str:
        """计算MD5并转为大写"""
        # 注意：有些系统需要添加密钥，如：sign_str += "&key=YOUR_SECRET_KEY"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _safe_compare_sign(self, sign1: str, sign2: str) -> bool:
        """安全比较签名（防止时序攻击）"""
        # 使用secrets.compare_digest进行恒定时间比较
        import secrets
        return secrets.compare_digest(sign1, sign2)

    @model_validator(mode='after')
    def validate_amount_with_state(self) -> 'Pay_RX_Notify_In_Data':
        """状态与金额的关联验证"""
        if self.state == 2 and self.amount <= 0:
            raise ValueError('支付成功时金额必须大于0')
        return self

    @model_validator(mode='after')
    def validate_order_no_unique(self) -> 'Pay_RX_Notify_In_Data':
        """系统订单号和商户订单号不能相同"""
        if self.sysOrderNo == self.mchOrderNo:
            raise ValueError('系统订单号和商户订单号不能相同')
        return self


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
