#!/bin/bash
cd /data/FastAPI-Main
sudo systemctl stop receive-notify.service
sudo rm -rf /data/FastAPI-Main/logs/*.log
git pull
chmod +x /data/FastAPI-Main/Bash/*.sh
sudo systemctl restart receive-notify.service
sleep 3
clear
sudo tail -f /data/FastAPI-Main/logs/ReceiveNotify.log
