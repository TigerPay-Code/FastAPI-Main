#!/bin/bash
echo "正在更新代码..."
cd /data/FastAPI-Main
echo "停止服务..."
sudo systemctl stop receive-notify.service
echo "清理日志..."
sudo rm -rf /data/FastAPI-Main/logs/*.log
echo "更新代码..."
git pull
sleep 3
echo "赋予脚本执行权限..."
chmod +x /data/FastAPI-Main/Bash/*.sh
echo "重启服务..."
sudo systemctl restart receive-notify.service
sleep 3
clear
echo "查看日志..."
sudo tail -f /data/FastAPI-Main/logs/ReceiveNotify.log
