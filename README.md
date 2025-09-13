# python FastAPI 项目

## 1. 项目简介

目录说明

- Systemctl：systemd 服务配置文件
- Logrotate：日志轮转配置文件
- PayOrder：支付订单模块
- ReceiveNotify：接收支付通知模块
- Utils：工具模块
- app.py：项目入口文件
- config.py：项目配置文件
- requirements.txt：项目依赖文件
- README.md：项目说明文件

## 2. 项目结构

```
.
├── PayOrder
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   ├── models.py
│   ├── routers.py
│   └── utils.py
├── ReceiveNotify
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   ├── models.py
│   ├── routers.py
│   └── utils.py
├── Utils
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routers.py
│   └── utils.py
├── app.py
├── config.py
├── requirements.txt
└── README.md
```

## 3. 项目启动
1. 生成依赖
```bash
pip install pipreqs
pipreqs /path/to/project --encoding=utf8 --force
pip freeze > requirements.txt
```
2. 安装依赖
```bash

pip install -r requirements.txt
```