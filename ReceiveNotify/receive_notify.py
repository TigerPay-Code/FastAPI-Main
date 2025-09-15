import os

from fastapi import FastAPI, Response
from pydantic import BaseModel, Field

from Logger.logger_config import setup_logger

log_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
logger = setup_logger(log_name)
logger.debug("打印调试信息")
logger.info("打印日志信息")
logger.warn("打印警告信息")
logger.warning("打印警告信息")
logger.error("打印错误信息")
logger.critical("打印严重错误信息")
logger.exception("打印异常信息")
''''
sudo tail -f /data/FastAPI-Main/logS/ReceiveNotify.log
'''

notify = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")


class Notify_In_Data(BaseModel):
    state: int = Field(
        title="通知状态",
        description="1 表示成功",
        default=0
    )
    sysOrderNo: str = Field(..., min_length=4, max_length=36, title="平台订单号", description="系统订单号")
    mchOrderNo: str = Field(..., min_length=4, max_length=36, title="下游订单号", description="商户订单号")
    amount: int = Field(..., description="金额，单位分")
    sign: str = Field(..., min_length=32, max_length=32, title="签名", description="签名值大写的MD5值")


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
    logger.info(f"收到 【代付】 通知：数据：{notify_in_data}")
    if notify_in_data.state == 1:
        logger.info(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
    else:
        logger.error(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")
    return success


@notify.post("/global_pay_out_notify")
async def handle_global_pay_notify(notify_out_data: Notify_Out_Data):
    logger.info(f"收到 【代付】 通知：数据：{notify_out_data}")
    return success


@notify.post("/global_refund_notify")
async def handle_global_pay_notify(notify_refund_data: Notify_Refund_Data):
    logger.info(f"收到 【退款】 通知：数据：{notify_refund_data}")
    return success
