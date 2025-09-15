# python FastAPI 项目

## 1. 项目简介

目录说明
- Config：配置模块
- Database：数据库模块
- Loggers：日志模块
- Logrotate：日志轮转配置文件
- Nginx：Nginx 配置文件
- ProjectUpdate：项目更新脚本
- ReceiveNotify：接收支付通知模块
- Redis：Redis 模块
- Routers：路由模块
- static：静态文件
- Systemctl：systemd 服务配置文件
- Templates：模板文件
- requirements.txt：项目依赖文件
- README.md：项目说明文件

## 2. 项目结构

```
├── Config
│   ├── __init__.py
│   ├── config.ini------------------# 配置文件
│   ├── config-initialize.py--------# 配置初始化脚本
│   └── mconfig_loader.py-----------# 配置加载器
├── Database
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   ├── models.py
│   ├── routers.py
│   └── utils.py
├── ReceiveNotify
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