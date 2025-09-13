#!/bin/bash
# 仓库路径
REPO_DIR="/data/FastAPI-Main"
cd "$REPO_DIR" || exit 1

# 拉取最新代码
git fetch origin
git pull origin main

# 获取最近一次更新的目录列表
changed_dirs=$(git diff --name-only HEAD~1 HEAD | cut -d'/' -f1 | sort -u)

for dir in $changed_dirs; do
    case $dir in
        ReceiveNotify)
            echo "ReceiveNotify 目录有更新，重启 notify.service"
            sudo systemctl stop receive-notify.service
            sudo systemctl start receive-notify.service
            ;;
        ProjectUpdate)
            echo "ProjectUpdate 目录有更新"
            chmod +x /data/FastAPI-Main/ProjectUpdate/FastAPI-Main-Update.sh
            ;;
        order)
            echo "order 目录有更新，重启 order.service"
            sudo systemctl stop order.service
            sudo systemctl start order.service
            ;;
        *)
            echo "目录 $dir 更新，但没有对应的服务，跳过"
            ;;
    esac
done