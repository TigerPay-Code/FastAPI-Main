#!/bin/bash
# 仓库路径
REPO_DIR="/data/FastAPI-Main"
cd "$REPO_DIR" || exit 1

# 完全重置仓库到干净状态
echo "强制重置仓库状态..."
git reset --hard HEAD
git clean -f -d -x  # 删除所有未跟踪文件和目录（包括忽略的文件）
git checkout -- .   # 丢弃所有修改

# 强制获取最新代码
echo "强制拉取最新代码..."
git fetch origin
git reset --hard origin/main

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
        Nginx)
            echo "Nginx 目录有更新，重启 Nginx"

            if [ -f "$REPO_DIR/FastAPI-Main.conf" ]; then
                echo "正在复制 FastAPI-Main.conf 到 Nginx 配置目录..."

                # 复制配置文件
                sudo cp "$REPO_DIR/FastAPI-Main.conf" /etc/nginx/sites-available/FastAPI-Main.conf

                # 测试 Nginx 配置
                echo "测试 Nginx 配置..."
                if sudo nginx -t; then
                    echo "Nginx 配置测试成功，重新加载 Nginx..."

                    # 重新加载 Nginx
                    sudo systemctl reload nginx

                    # 重启 Nginx 以确保配置完全生效
                    sudo systemctl restart nginx

                    echo "Nginx 已成功重新加载并重启"
                else
                    echo "Nginx 配置测试失败，请检查配置文件"
                    exit 1
                fi
            else
                echo "错误：未找到 $REPO_DIR/FastAPI-Main.conf 文件"
                exit 1
            fi

            ;;
        *)
            echo "目录 $dir 更新，但没有对应的服务，跳过"
            ;;
    esac
done