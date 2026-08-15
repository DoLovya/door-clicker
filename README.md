# Door Clicker

基于 ESP8266 的智能门禁控制系统，通过 MQTT 协议实现远程开门。

## 项目结构

```
door-clicker/
├── door-clicker-firmware/    # ESP8266 固件
│   ├── include/              # 头文件
│   ├── src/                  # 源文件
│   ├── docs/                 # 文档
│   └── platformio.ini        # PlatformIO 配置
└── door-clicker-web/         # Web 管理服务
    ├── templates/            # HTML 模板
    ├── app.py                # Flask 主应用
    ├── config_manager.py     # 配置管理
    ├── mqtt_client_manager.py # MQTT 客户端
    └── requirements.txt      # Python 依赖
```

## 系统架构

```
┌─────────────┐   HTTP API    ┌──────────────┐   MQTT    ┌─────────────┐   MQTT    ┌─────────┐
│  Web 浏览器  │ ────────────► │  Web Server  │ ───────► │ MQTT Broker │ ───────► │  ESP8266 │
│  (phone/pc)  │ ◄──────────── │  (Flask)     │ ◄─────── │  (EMQX等)   │ ◄─────── │         │
└─────────────┘                └──────────────┘          └─────────────┘          └────┬────┘
                                                                                        │ GPIO5(D1)
                                                                                        ▼
                                                                                   ┌─────────┐
                                                                                   │  舵机    │
                                                                                   └─────────┘
```

**数据流说明：**
- Web 浏览器与 Web Server 之间通过 **HTTP API** 通信
- Web Server 作为 MQTT 客户端，通过 **MQTT 协议** 与 Broker 交互
- ESP8266 作为 MQTT 客户端，订阅设备专属 Topic
- MQTT Broker 实现"内网穿透"效果，让公网 Web 服务能控制内网设备

## 硬件要求

| 组件 | 型号 | 说明 |
|------|------|------|
| 主控 | ESP8266 (Huzzah) | WiFi 通信 + 舵机控制 |
| 舵机 | SG90/MG996R | 门锁驱动 |
| 服务器 | 任意 MQTT Broker | EMQX、Mosquitto 等 |

### 引脚分配

| ESP8266 引脚 | GPIO | 连接 |
|-------------|------|------|
| D1 | GPIO5 | 舵机信号线 |
| - | 3.3V | 舵机 VCC (或外部供电) |
| G | GND | 舵机 GND |

## 快速开始

### 1. ESP8266 固件烧录

```bash
cd door-clicker-firmware

# 安装 PlatformIO (首次使用)
# 参考 https://platformio.org/install

# 编译
pio run

# 烧录 (根据实际端口修改 upload_port)
pio run --target upload

# 查看串口日志
pio device monitor
```

### 2. Web 服务启动

```bash
cd door-clicker-web

# 创建虚拟环境 (首次使用)
python3 -m venv myenv
source myenv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python3 app.py
```

### 3. 访问地址

| 页面 | URL | 说明 |
|------|-----|------|
| 开门页 | `http://<host>:8080/` | 极简开门按钮，适合手机 |
| 配置页 | `http://<host>:8080/config` | MQTT 配置、日志查看 |
| 登录页 | `http://<host>:8080/login` | 管理员登录 |

### 4. 默认账号

- 用户名: `admin`
- 密码: `admin`

> ⚠️ 首次登录后请立即修改密码

## 详细文档

- [MQTT 协议文档](door-clicker-firmware/docs/mqtt-protocol.md)
- [Web 服务说明](door-clicker-web/README.md)
- [固件开发说明](door-clicker-firmware/README.md)

## 技术栈

### 固件
- PlatformIO
- Arduino Framework
- PubSubClient (MQTT)
- ArduinoJson

### Web 服务
- Python 3.12
- Flask (Web 框架)
- Paho-MQTT (MQTT 客户端)
- SHA-256 (密码加密)
