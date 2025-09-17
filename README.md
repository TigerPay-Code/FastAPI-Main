# python FastAPI 项目

## 1. 项目简介

目录说明
- Config：配置模块
- Database：数据库模块
- Logger：日志模块
- Middleware：中间件模块
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
## 3. 创建和管理虚拟环境

```cmd
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 更新虚拟环境的pip版本
python.exe -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```
以管理员身份打开 PowerShell，运行
```cmd
wsl --install
```

Windows终端上运行程序
```cmd
# 激活虚拟环境
venv\Scripts\activate

# 启动项目
uvicorn ReceiveNotify.receive_notify:notify --host 127.0.0.1 --port 4911 --workers 1

# 启动调试模式
uvicorn ReceiveNotify.receive_notify:notify --host 127.0.0.1 --port 4911 --workers 1 --reload

# 退出虚拟环境
deactivate
```

## 4. 项目启动
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