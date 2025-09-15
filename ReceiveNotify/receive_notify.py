import os

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from Logger.logger_config import setup_logger

notify = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")

rn_log = setup_logger(os.path.basename(os.path.dirname(os.path.abspath(__file__))))

class Notify_In_Data(BaseModel):
    state: int = Field(
        title="通知状态",
        description="1 表示成功",
        default=0
    )
    sysOrderNo: str = Field(..., min_length=4, max_length=36, description="系统订单号")
    mchOrderNo: str = Field(..., min_length=4, max_length=36, description="商户订单号")
    amount: int = Field(..., description="金额，单位分")
    sign: str


class Notify_Out_Data(BaseModel):
    state: int
    sysOrderNo: str
    mchOrderNo: str
    amount: int
    sign: str


class Notify_Refund_Data(BaseModel):
    state: int
    sysOrderNo: str
    mchOrderNo: str
    amount: int
    sign: str


@notify.post("/global_pay_in_notify")
async def handle_global_pay_notify(notify_in_data: Notify_In_Data):
    rn_log.info(f"收到 【代付】 通知：数据：{notify_in_data}")
    if notify_in_data.state == 1:
        rn_log.info(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
    else:
        rn_log.error(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")

    return success


@notify.post("/global_pay_out_notify")
async def handle_global_pay_notify(notify_out_data: Notify_Out_Data):
    rn_log.info(f"收到 【代付】 通知：数据：{notify_out_data}")
    return success


@notify.post("/global_refund_notify")
async def handle_global_pay_notify(notify_refund_data: Notify_Refund_Data):
    rn_log.info(f"收到 【退款】 通知：数据：{notify_refund_data}")
    return success
