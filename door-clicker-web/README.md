# Door Clicker Web Service

基于 Flask 的 Web 管理服务，提供远程开门控制和系统配置管理。

## 功能特性

- 🔓 **远程开门**：一键发送 MQTT 指令控制 ESP8266
- ⚙️ **配置管理**：通过 Web 界面修改 MQTT 连接配置
- 📋 **通信日志**：实时查看 MQTT 发送/接收日志
- 🔒 **管理员认证**：保护配置页面免受非法访问
- 📱 **移动端优化**：响应式设计，手机友好

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装与启动

```bash
# 进入目录
cd door-clicker-web

# 创建虚拟环境
python3 -m venv myenv
source myenv/bin/activate  # macOS/Linux
# myenv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
python3 app.py
```

服务启动后访问 `http://localhost:8080`

## 目录结构

```
door-clicker-web/
├── app.py                    # Flask 主应用，路由定义
├── auth.py                   # 认证模块（登录/登出/会话管理）
├── config_manager.py         # 配置管理（加载/保存/热加载）
├── mqtt_client_manager.py    # MQTT 客户端封装
├── log_manager.py            # 日志管理
├── config.json               # 配置文件
├── requirements.txt         # Python 依赖
├── templates/
│   ├── door.html             # 开门页面（极简）
│   ├── index.html            # 配置管理页面
│   └── login.html            # 登录页面
└── *_test.py                 # 单元测试
```

## 配置说明

### config.json

```json
{
  "mqttServer": "broker.example.com",
  "mqttPort": 1883,
  "mqttUsername": "user",
  "mqttPassword": "pass",
  "doorTopic": "door/00094E53",
  "adminUser": "admin",
  "adminPasswordHash": "",
  "topics": []
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `mqttServer` | string | MQTT Broker 地址 |
| `mqttPort` | int | MQTT Broker 端口 |
| `mqttUsername` | string | 认证用户名（选填） |
| `mqttPassword` | string | 认证密码（选填） |
| `doorTopic` | string | 开门指令 Topic |
| `adminUser` | string | 管理员用户名 |
| `adminPasswordHash` | string | SHA-256 加密后的密码 |

## API 接口

### 公开接口（无需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 开门页面 |
| GET | `/api/mqtt/status` | 获取 MQTT 连接状态 |
| POST | `/api/open/door` | 发送开门指令 |
| GET | `/api/health` | 健康检查 |

### 需登录接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/config` | 配置页面 |
| GET | `/api/config` | 获取配置（密码脱敏） |
| PUT | `/api/config` | 更新配置 |
| POST | `/api/mqtt/test` | 测试 MQTT 连接 |
| GET | `/api/logs` | 获取通信日志 |
| DELETE | `/api/logs` | 清空日志 |

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/login` | 登录页面 |
| POST | `/api/auth/login` | 登录验证 |
| POST | `/api/auth/logout` | 退出登录 |

## 请求/响应示例

### 开门指令

```bash
POST /api/open/door

# 成功响应
[
  {"angle": 90, "duration": 200},
  {"angle": 0, "duration": 200}
]

# 失败响应
{"error": "Not connected to MQTT broker"}
```

### 获取配置

```bash
GET /api/config

# 响应（MQTT 密码脱敏为 ***）
{
  "mqttServer": "broker.example.com",
  "mqttPort": 1883,
  "mqttUsername": "user",
  "mqttPassword": "***",
  "doorTopic": "door/00094E53",
  "adminUser": "admin",
  "topics": []
}
```

### 更新配置

```bash
PUT /api/config
Content-Type: application/json

{
  "mqttServer": "new-broker.example.com",
  "mqttPort": 1883
}

# 响应
{
  "config": { ... },
  "reload": {"success": true, "message": "Config reloaded and reconnected"}
}
```

### 修改管理员密码

```bash
PUT /api/config
Content-Type: application/json

{
  "adminPassword": "newpassword123"
}
```

## 安全特性

- **密码加密**：管理员密码使用 SHA-256 哈希存储，不存储明文
- **Session 超时**：登录后 Session 有效期 1 小时，超时自动退出
- **密码脱敏**：API 返回配置时 MQTT 密码显示为 `***`
- **路由保护**：配置相关路由必须登录才能访问
- **CORS**：仅同源请求允许

## 通信日志格式

日志条目结构：

```json
{
  "timestamp": "2024-08-15 14:30:00",
  "type": "send",
  "message": "开门命令发送成功",
  "topic": "door/00094E53",
  "payload": "[{\"angle\":90,\"duration\":200},...]"
}
```

| type 值 | 说明 |
|---------|------|
| `send` | 发送的消息 |
| `receive` | 接收的消息 |
| `info` | 系统信息 |
| `error` | 错误信息 |

## 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| flask | 3.0.3 | Web 框架 |
| paho-mqtt | 2.1.0 | MQTT 客户端 |
| flask_socketio | 5.3.6 | WebSocket 支持（备用） |
| websockets | 13.0.1 | WebSocket 库（备用） |

## 常见问题

### Q: 如何修改默认端口？
修改 `app.py` 最后一行：
```python
app.run(host="0.0.0.0", port=8080)  # 改为所需端口
```

### Q: 如何重置管理员密码？
删除 `config.json` 中的 `adminPasswordHash` 字段，重启后使用默认密码 `admin` 登录。

### Q: MQTT 连接失败怎么办？
1. 确认 MQTT Broker 地址和端口正确
2. 检查用户名密码是否正确
3. 在配置页面点击"测试连接"按钮验证
4. 查看日志界面的错误日志

### Q: 配置保存后需要重启吗？
不需要。保存配置后系统会自动断开旧连接并使用新配置重连 MQTT。

---

## Docker 部署

Door Clicker 提供完整的 Docker Compose 方案，支持**零环境依赖**一键启动（Web 面板 + Mosquitto MQTT Broker）。

### 环境要求

- Docker Engine ≥ 24
- Docker Compose v2（`docker compose` CLI，Docker Desktop 默认已启用）

### 三种运行模式对比

| 模式 | Web 端运行位置 | MQTT Broker 位置 | 启动命令 | 热重载 | IDE 断点 | 适用场景 |
|---|---|---|---|---|---|---|
| **混合开发（推荐默认）** | 本地 venv `python app.py` | Docker Mosquitto | 见下方 | ✅ | ✅ | 日常写代码 + 调试 |
| **全容器开发** | Docker web 容器（源码 bind mount）| Docker Mosquitto | `ENV=development docker compose up -d --build` | ✅（可能慢 1–3s）| 需 debugpy | 验证容器化行为、CI |
| **生产部署** | Docker web 容器（镜像内打包源码）| Docker Mosquitto | `docker compose up -d --build` | ❌ | ❌ | 服务器正式部署 |

### 快速开始（推荐：混合开发模式）

```bash
# 1. 只启动 MQTT Broker（后台常驻）
cd /path/to/door-clicker
docker compose up -d mosquitto

# 2. 本地 venv 跑 Flask（保留你最习惯的断点 + 秒级 reload）
cd door-clicker-web
python3 -m venv venv && source venv/bin/activate
python -m pip install -r requirements.txt
cd src
FLASK_ENV=development python app.py
```

浏览器访问 `http://localhost:5000`，MQTT 地址填 `127.0.0.1:1883`（默认匿名，开发模式零配置）。

### 快速开始（一键全栈）

```bash
cd /path/to/door-clicker

# 可选：自定义端口、模式
cp .env.example .env
#   编辑 .env，WEB_PORT / MQTT_PORT / ENV 按需改

# 生产模式（默认）— gunicorn + eventlet
docker compose up -d --build

# 或者：开发模式 — Flask dev server + 源码 bind mount 热重载
ENV=development docker compose up -d --build

# 查看状态 / 日志
docker compose ps
docker compose logs -f web
docker compose logs -f mosquitto

# 完全停止（持久化数据不会丢）
docker compose down
```

### 持久化目录一览

| 宿主机路径 / volume | 用途 | 销毁容器是否保留 |
|---|---|---|
| `door-clicker-web/data/`（bind mount） | `config.json` + `logs/` | ✅ 保留 |
| `mosquitto-data`（命名 volume） | Mosquitto 消息持久化 | ✅ 保留 |
| `mosquitto-log`（命名 volume） | Mosquitto 运行日志 | ✅ 保留 |

迁移现有配置：直接把旧的 `config.json` 拷到 `door-clicker-web/data/config.json`，JSON 格式完全兼容。

### 调试模式（容器内 debugpy attach）

1. 在 `docker-compose.yml` 里解开 `web` 服务 `5678:5678` 端口映射的注释。
2. 启动：`DEBUGPY=1 ENV=development docker compose up -d --build`。容器会 `--wait-for-client` 暂停，等待 IDE 连接。
3. VS Code 添加 launch.json 配置（type=python, request=attach, host=localhost, port=5678, pathMappings 映射 `/app/src` 到宿主机 `door-clicker-web/src`），按 F5 即可断点调试。

### 从现有 systemd 部署迁移 / 回滚

```bash
# 迁移
sudo systemctl stop door-clicker-web
sudo cp /opt/door-clicker/door-clicker-web/data/config.json ./door-clicker-web/data/
docker compose up -d --build

# 回滚
docker compose down
sudo systemctl start door-clicker-web
```

### 生产安全加固必读

- 编辑 `deploy/mosquitto/mosquitto.conf`：`allow_anonymous false`，取消 `password_file` 注释并用 `mosquitto_passwd -c` 生成用户。
- 如需暴露到公网，建议前面加一层 Nginx/Caddy 做 HTTPS；`docker-compose.yml` 默认暴露 5000 和 1883，按需绑定内网 IP 而不是 `0.0.0.0`。
