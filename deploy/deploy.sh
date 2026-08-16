#!/bin/bash
set -e

echo "===== Door Clicker 部署脚本 ====="
echo "时间: $(date)"

# 配置
APP_DIR="/opt/door-clicker"
WEB_DIR="$APP_DIR/door-clicker-web"
SERVICE_NAME="door-clicker-web"
SERVICE_FILE="$APP_DIR/deploy/door-clicker-web.service"

# 1. 设置代理
if curl -s --connect-timeout 3 http://127.0.0.1:7890 > /dev/null 2>&1; then
    echo "[代理] 检测到本地代理，启用"
    export http_proxy=http://127.0.0.1:7890
    export https_proxy=http://127.0.0.1:7890
else
    echo "[代理] 未检测到本地代理，直连模式"
fi
export no_proxy=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8

# 2. 拉取代码
if [ ! -d "$APP_DIR/.git" ]; then
    echo "[代码] 初始化仓库..."
    cd /opt/
    rm -rf door-clicker
    git clone https://github.com/DoLovya/door-clicker.git
else
    echo "[代码] 更新..."
    cd "$APP_DIR"
    git fetch origin
    git reset --hard origin/main
    git clean -fd
fi

cd "$WEB_DIR"

# 3. 查找或安装 Python
PYTHON=""
for cmd in python3.11 python3.10 python3.9 python3.8 python3; do
    if command -v $cmd &>/dev/null; then
        PYTHON=$(command -v $cmd)
        echo "[Python] 找到 $cmd: $($PYTHON --version 2>&1)"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[Python] 未找到 Python，安装..."
    if command -v yum &>/dev/null; then
        yum install -y python3 python3-pip python3-venv
    elif command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    else
        echo "ERROR: 不支持的包管理器"
        exit 1
    fi
    PYTHON=$(command -v python3)
    echo "[Python] 安装完成: $($PYTHON --version)"
fi

# 4. 创建虚拟环境
echo "[虚拟环境] 创建..."
rm -rf venv
$PYTHON -m venv venv
source venv/bin/activate

# 5. 安装依赖
echo "[依赖] 安装..."
pip install --upgrade pip -i https://pypi.org/simple/ -q
pip install -r requirements.txt -i https://pypi.org/simple/

# 6. 创建目录
mkdir -p data/logs

# 7. 配置服务
echo "[服务] 配置..."
if [ -f "$SERVICE_FILE" ]; then
    cp "$SERVICE_FILE" /etc/systemd/system/
fi
systemctl daemon-reload
chmod -R 755 data

# 8. 重启服务
echo "[服务] 重启..."
systemctl restart "$SERVICE_NAME"
sleep 3

# 9. 检查状态
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "===== 部署成功 ====="
else
    echo "ERROR: 服务启动失败"
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi
