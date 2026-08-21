#!/bin/bash
set -e

SERVER_USER="door-clicker"
APP_DIR="/opt/door-clicker"
VENV_DIR="$APP_DIR/door-clicker-web/venv"

echo "========================================"
echo "  Door Clicker 服务器初始化脚本"
echo "========================================"
echo ""

# 进度提示函数
progress() {
    local step=$1
    local total=$2
    local msg=$3
    echo "[$step/$total] $msg ..."
}

# 检测系统发行版
if [ "$(uname)" != "Linux" ]; then
    echo "✗ 此脚本仅支持 Linux 服务器（Ubuntu/Debian/CentOS/RHEL 等）"
    echo " 请在云服务器上执行：ssh door-clicker@服务器IP 'cd /opt/door-clicker/deploy && sudo ./setup.sh'"
    exit 1
fi

# 尝试多种方式检测 OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL 旧版本
    OS=$(cat /etc/redhat-release | grep -oE 'CentOS|Red Hat Enterprise Linux|Rocky Linux|AlmaLinux|Fedora' | head -1 | tr '[:upper:]' '[:lower:]')
    OS_VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+' | head -1)
    [ -z "$OS" ] && OS="centos"
    [ -z "$OS_VERSION" ] && OS_VERSION="7"
elif [ -f /etc/centos-release ]; then
    OS="centos"
    OS_VERSION=$(cat /etc/centos-release | grep -oE '[0-9]+' | head -1)
    [ -z "$OS_VERSION" ] && OS_VERSION="7"
elif command -v lsb_release &> /dev/null; then
    OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
    OS_VERSION=$(lsb_release -sr)
else
    echo "✗ 无法检测 Linux 发行版"
    echo " 系统信息:"
    uname -a
    echo ""
    echo " 请手动指定 OS 类型:"
    echo "   export OS=centos OS_VERSION=7"
    echo "   然后重新运行脚本"
    exit 1
fi
echo "检测到系统: $OS $OS_VERSION"
TOTAL_STEPS=10

# 1. 创建用户
progress 1 $TOTAL_STEPS "检查用户"
if ! id "$SERVER_USER" &>/dev/null; then
    useradd -r -s /bin/false "$SERVER_USER"
    echo "  ✓ 创建用户: $SERVER_USER"
else
    echo "  ✓ 用户 $SERVER_USER 已存在"
fi

# 2. 安装系统依赖
progress 2 $TOTAL_STEPS "安装系统依赖 (Python, Git, Nginx, Mosquitto)"
case "$OS" in
    ubuntu|debian)
        apt update
        apt install -y python3 python3-venv python3-pip git nginx mosquitto mosquitto-clients
        ;;
    centos|rhel|fedora|rocky|almalinux|alinux|amzn)
        if command -v dnf &> /dev/null; then
            PKG_MGR="dnf"
        else
            PKG_MGR="yum"
        fi
        echo "    使用包管理器: $PKG_MGR"
        $PKG_MGR update -y
        $PKG_MGR install -y python3 python3-pip git nginx mosquitto
        # CentOS/RHEL 中 python3-venv 包名不同
        if ! python3 -m venv --help &>/dev/null; then
            echo "    安装 python3-virtualenv ..."
            $PKG_MGR install -y python3-virtualenv || pip3 install virtualenv
        fi
        ;;
    *)
        echo "✗ 不支持的操作系统: $OS"
        exit 1
esac
echo "  ✓ 系统依赖安装完成"

# 3. 创建目录结构
progress 3 $TOTAL_STEPS "创建目录结构"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/door-clicker-web"/{src,data,data/logs,tests,src/templates,src/static}
echo "  ✓ 目录结构创建完成"

# 4. 安装 MQTT Broker (Mosquitto)
progress 4 $TOTAL_STEPS "配置 MQTT Broker"
systemctl enable mosquitto
systemctl start mosquitto
echo "  ✓ MQTT Broker 已启动"

# 5. 创建虚拟环境
progress 5 $TOTAL_STEPS "创建 Python 虚拟环境"
cd "$APP_DIR/door-clicker-web"
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
echo "  ✓ Python 虚拟环境创建完成"

# 6. 配置 systemd
progress 6 $TOTAL_STEPS "配置 systemd 服务"
SERVICE_FILE=$(dirname "$0")/door-clicker-web.service
if [ -f "$SERVICE_FILE" ]; then
    cp "$SERVICE_FILE" /etc/systemd/system/
else
    cat > /etc/systemd/system/door-clicker-web.service << EOF
[Unit]
Description=Door Clicker Web Service
After=network.target mqtt.target

[Service]
Type=simple
User=$SERVER_USER
Group=$SERVER_USER
WorkingDirectory=$APP_DIR/door-clicker-web/src
ExecStart=$APP_DIR/door-clicker-web/venv/bin/python app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=FLASK_ENV=production
Environment=PYTHONUNBUFFERED=1

NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR/door-clicker-web/data $APP_DIR/door-clicker-web/data/logs

[Install]
WantedBy=multi-user.target
EOF
fi
systemctl daemon-reload
systemctl enable door-clicker-web
echo "  ✓ systemd 服务配置完成"

# 7. 设置目录权限
progress 7 $TOTAL_STEPS "设置目录权限"
chown -R "$SERVER_USER:$SERVER_USER" "$APP_DIR"
chmod 750 "$APP_DIR/door-clicker-web/data" "$APP_DIR/door-clicker-web/data/logs"
echo "  ✓ 目录权限设置完成"

# 8. 配置 Nginx
progress 8 $TOTAL_STEPS "配置 Nginx 反向代理"
if [ -d /etc/nginx/sites-available ]; then
    cat > /etc/nginx/sites-available/door-clicker << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINXEOF
    ln -sf /etc/nginx/sites-available/door-clicker /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
else
    cat > /etc/nginx/conf.d/door-clicker.conf << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINXEOF
    sed -i '/listen.*80/d' /etc/nginx/nginx.conf 2>/dev/null || true
fi

systemctl enable nginx
systemctl start nginx
nginx -t && systemctl reload nginx
echo "  ✓ Nginx 配置完成"

# 9. 创建默认配置文件
progress 9 $TOTAL_STEPS "创建默认配置"
cat > "$APP_DIR/door-clicker-web/data/config.json" << EOF
{
    "mqttServer": "127.0.0.1",
    "mqttPort": 1883,
    "mqttUsername": "",
    "mqttPassword": "",
    "doorTopic": "door/00094E53",
    "adminUser": "admin",
    "adminPasswordHash": "",
    "servoPin": 2
}
EOF
chown "$SERVER_USER:$SERVER_USER" "$APP_DIR/door-clicker-web/data/config.json"
echo "  ✓ 默认配置创建完成"

# 10. 初始化日志目录
progress 10 $TOTAL_STEPS "初始化日志目录"
mkdir -p "$APP_DIR/door-clicker-web/data/logs"
touch "$APP_DIR/door-clicker-web/data/logs/door_clicker.log"
chown "$SERVER_USER:$SERVER_USER" "$APP_DIR/door-clicker-web/data/logs/door_clicker.log"
echo "  ✓ 日志目录初始化完成"

echo ""
echo "========================================"
echo "  初始化完成！"
echo "========================================"
echo ""
echo "接下来的步骤："
echo "  1. git clone 你的仓库到 $APP_DIR"
echo "     git clone https://github.com/DoLovya/door-clicker.git $APP_DIR"
echo ""
echo "  2. 在 GitHub Settings → Secrets 添加以下密钥："
echo "     SSH_HOST = 你的服务器IP"
echo "     SSH_USER = $SERVER_USER"
echo "     SSH_KEY = 部署用的 SSH 私钥"
echo ""
echo "  3. 确保 SSH 公钥已添加到服务器："
echo "     ssh-copy-id -i ~/.ssh/door-clicker-deploy.pub $SERVER_USER@你的服务器IP"
echo ""
echo "  4. 推送代码到 GitHub 触发自动部署"
echo ""
