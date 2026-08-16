# Door Clicker 自动化部署

本文档介绍如何使用 GitHub Actions + SSH + systemd 实现自动化部署。

## 架构说明

```
开发者 Push → GitHub Actions → SSH → 云服务器 → systemd → 应用服务
```

## 前置条件

- [ ] 一台 Linux 服务器（Ubuntu 20.04+ 推荐）
- [ ] GitHub 仓库有推送权限
- [ ] 服务器已安装 Python 3.8+、Git、Nginx、Mosquitto

## 服务器初始化

首次部署需要在服务器上执行初始化脚本：

```bash
# 1. 克隆项目（如果还没有）
cd /opt/
git clone https://github.com/DoLovya/door-clicker.git

# 2. 执行初始化脚本
cd door-clicker/deploy
chmod +x setup.sh
sudo ./setup.sh
```

脚本会自动完成：
- 创建运行用户 `door-clicker`
- 安装 Python、Nginx、Mosquitto 等依赖
- 创建虚拟环境
- 配置 systemd 服务
- 配置 Nginx 反向代理
- 创建默认配置文件

## SSH 密钥配置

### 1. 生成部署密钥对

在本地电脑执行：

```bash
ssh-keygen -t ed25519 -C "door-clicker-deploy" -f ~/.ssh/door-clicker-deploy
```

### 2. 将公钥添加到服务器

```bash
ssh-copy-id -i ~/.ssh/door-clicker-deploy.pub door-clicker@你的服务器IP
```

### 3. 测试连接

```bash
ssh -i ~/.ssh/door-clicker-deploy door-clicker@你的服务器IP
```

## GitHub Secrets 配置

在 GitHub 仓库 `Settings → Secrets and variables → Actions` 添加：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `SSH_HOST` | 服务器 IP 或域名 | `47.94.208.227` |
| `SSH_USER` | SSH 用户名 | `door-clicker` |
| `SSH_KEY` | SSH 私钥内容（完整） | `cat ~/.ssh/door-clicker-deploy` |
| `SSH_PORT` | SSH 端口（可选） | `22` |
| `APP_PORT` | 应用端口（可选） | `5000` |
| `DEPLOY_URL` | 部署后访问 URL（可选） | `https://door-clicker.example.com` |

## 触发部署

### 自动部署

推送到 `main` 分支会自动触发部署：

```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

### 手动部署

在 GitHub Actions 页面点击 `Run workflow` 手动触发。

### 服务器手动部署

```bash
ssh door-clicker@服务器IP
cd /opt/door-clicker/deploy
./deploy.sh
```

## 服务管理

```bash
# 查看服务状态
sudo systemctl status door-clicker-web

# 查看日志
sudo journalctl -u door-clicker-web -f

# 重启服务
sudo systemctl restart door-clicker-web

# 停止服务
sudo systemctl stop door-clicker-web

# 启动服务
sudo systemctl start door-clicker-web
```

## 配置说明

### 修改 MQTT 配置

编辑 `/opt/door-clicker/door-clicker-web/data/config.json`：

```json
{
    "mqttServer": "MQTT服务器地址",
    "mqttPort": 1883,
    "mqttUsername": "用户名",
    "mqttPassword": "密码",
    "doorTopic": "door/00094E53",
    "adminUser": "admin",
    "adminPasswordHash": "",
    "servoPin": 2
}
```

修改后重启服务：

```bash
sudo systemctl restart door-clicker-web
```

## 常见问题

### Q: GitHub Actions 连接失败？

检查：
1. `SSH_HOST` 是否正确
2. `SSH_KEY` 是否为完整私钥内容（包括头尾标记）
3. 服务器防火墙是否开放 SSH 端口
4. 服务器 `~/.ssh/authorized_keys` 是否包含公钥

### Q: 服务启动失败？

查看日志：
```bash
sudo journalctl -u door-clicker-web -n 50 --no-pager
```

### Q: 配置文件被覆盖？

部署脚本不会覆盖 `data/config.json`，但建议备份：
```bash
cp /opt/door-clicker/door-clicker-web/data/config.json ~/config.json.backup
```

## 安全建议

- 使用专用的 SSH 密钥对做部署，不要复用个人密钥
- 定期更换 SSH 密钥
- 服务器防火墙仅开放必要端口（22, 80, 1883）
- 配置 HTTPS（可使用 Let's Encrypt）
- 定期检查 `data/config.json` 中的密码是否暴露

## 目录结构

```
door-clicker/
├── .github/
│   └── workflows/
│       └── deploy.yaml          # GitHub Actions 工作流
├── deploy/
│   ├── door-clicker-web.service  # systemd 服务配置
│   ├── setup.sh                  # 服务器初始化脚本
│   ├── deploy.sh                 # 部署脚本（服务器端执行）
│   └── README.md                 # 本文档
├── door-clicker-web/
│   ├── src/
│   ├── data/
│   │   └── config.json           # 运行时配置（不提交）
│   ├── logs/
│   │   └── door_clicker.log      # 运行时日志（不提交）
│   ├── tests/
│   └── requirements.txt
└── README.md
```
