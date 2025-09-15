from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from Logger.logger_config import logger

"""
https://notify.king-sms.com/global_pay_in_notify

sudo vim /etc/nginx/sites-available/fastapi-main.conf
-----------------------------------------------------------------------------------------------------------------
# HTTP 监听，不做重定向
server {
    listen 80;
    listen [::]:80;

    server_name	king-sms.com www.king-sms.com;

    root /srv/FastAPI/templates;       # 静态文件根目录
    index index.html;

    location / {
        try_files $uri $uri.html  $uri/ =404;
    }

    location /static/ {
        alias /srv/FastAPI/static/;
    }
}

# HTTPS 监听，提供 SSL 证书
server {
    listen 443;
    listen [::]:443;

    server_name king-sms.com www.king-sms.com;

    ssl_protocols	TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    root /srv/FastAPI/templates;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /static/ {
        alias /srv/FastAPI/static/;
    }
}

server {
    listen 80;

    server_name	api.king-sms.com;

    ssl_protocols	TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:8960;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}

server {
    listen 80;

    server_name notify.king-sms.com;

    ssl_protocols	TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:4911;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}

server {
    listen 80;

    server_name	pay-order.king-sms.com;

    ssl_protocols	TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:7517;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}
-----------------------------------------------------------------------------------------------------------------
sudo unlink /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/conf.d/default.conf
sudo ln -s /etc/nginx/sites-available/fastapi-main.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart nginx
sudo systemctl enable nginx


sudo vim /etc/systemd/system/receive-notify.service
-----------------------------------------------------------------------------------------------------------------
[Unit]
Description=Pay Receive Notify
After=network.target

[Service]
User=root
WorkingDirectory=/data/notify
Environment="PATH=/usr/local/bin"

# 方案 A：直接使用 Uvicorn --workers CPU核心数 * 2 + 1
ExecStart=/usr/local/bin/uvicorn ReceiveNotify:notify --host 127.0.0.1 --port 4911 --workers 1 --loop uvloop

# 方案 B：Gunicorn + Uvicorn Worker（注释掉方案 A 并取消下行注释） pip install gunicorn "uvicorn[standard]"
#ExecStart=/data/notify/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 5 app.ReceiveNotify:app --bind 127.0.0.1:4911

StandardOutput=file:/data/notify/log/notify.log
StandardError=file:/data/notify/log/notify-error.log

Restart=on-failure

[Install]
WantedBy=multi-user.target
-----------------------------------------------------------------------------------------------------------------
sudo systemctl daemon-reload
sudo systemctl enable receive-notify.service
sudo systemctl restart receive-notify.service
sudo systemctl start receive-notify.service
sudo systemctl stop receive-notify.service
sudo systemctl status receive-notify.service
sudo tail -f /data/FastAPI-Main/ReceiveNotify/log/notify.log

日志管理 2个月删除
sudo vim /etc/logrotate.d/fastapi-main
-----------------------------------------------------------------------------------------------------------------
/data/FastAPI-Main/ReceiveNotify/log/*.log {
    daily
    rotate 60
    compress
    dateext
    missingok
    notifempty
    sharedscripts
    postrotate
        # 针对 receive_notify 服务
        /usr/bin/systemctl reload receive_notify.service
    endscript
}
-----------------------------------------------------------------------------------------------------------------
验证日志管理
sudo logrotate -d /etc/logrotate.d/fastapi-main
sudo logrotate -vf /etc/logrotate.d/fastapi-main
"""

notify = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

success = Response(content="success", media_type="text/plain")
ok = Response(content="ok", media_type="text/plain")


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
    logger.info(f"收到 【代付】 通知：数据：{notify_in_data}")
    if notify_in_data.state == 1:
        logger.info(f"订单号: {notify_in_data.sysOrderNo} 已成功支付，金额: {notify_in_data.amount}")
    else:
        logger.error(f"订单号: {notify_in_data.sysOrderNo} 支付失败，金额: {notify_in_data.amount}")

    return success


@notify.post("/global_pay_out_notify")
async def handle_global_pay_notify(notify_out_data: Notify_Out_Data):
    print(f"收到 【代付】 通知：数据：{notify_out_data}")
    return success


@notify.post("/global_refund_notify")
async def handle_global_pay_notify(notify_refund_data: Notify_Refund_Data):
    print(f"收到 【退款】 通知：数据：{notify_refund_data}")
    return success
