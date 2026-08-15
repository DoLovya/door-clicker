# Door Clicker Firmware

ESP8266 固件，实现 WiFi 连接、MQTT 通信和舵机控制。

## 硬件连接

### 引脚分配

| ESP8266 引脚 | GPIO | 功能 | 连接 |
|-------------|------|------|------|
| D1 | **GPIO5** | 舵机控制 | 舵机信号线 (PWM) |
| VCC | 3.3V | 电源 | 舵机 VCC (建议外部5V供电) |
| G | GND | 接地 | 舵机 GND |

### 接线图

```
ESP8266 (Huzzah)          舵机 (SG90)
─────────────────         ──────────
3.3V  ──────────────────  VCC  (或外部5V)
GND   ──────────────────  GND
D1    ──────────────────  SIGNAL
(GPIO5)
```

> ⚠️ **注意**：舵机启动电流较大，建议使用外部 5V 供电以避免 ESP8266 重启。

## 功能特性

- 📡 **WiFi 连接**：自动连接配置的 WiFi 网络
- 🔗 **MQTT 通信**：订阅设备专属 Topic，接收指令
- 🔄 **舵机控制**：支持角度控制、速度调整、延时执行
- 📊 **状态上报**：通过 MQTT 上报执行结果
- 🌐 **配置页面**：内置 HTTP 服务器，支持 WiFi 配置和舵机测试

## 开发环境

### 依赖

| 库 | 版本 | 用途 |
|----|------|------|
| PubSubClient | 2.8+ | MQTT 客户端 |
| ArduinoJson | 7.3+ | JSON 解析 |

### 构建工具

- [PlatformIO](https://platformio.org) v6.0+

## 编译与烧录

### 1. 修改配置

编辑 `platformio.ini`，设置正确的串口：

```ini
[env:huzzah]
platform = espressif8266
board = huzzah
framework = arduino
upload_port = /dev/cu.usbserial-210  ; 根据实际情况修改
monitor_port = /dev/cu.usbserial-210
monitor_speed = 19200
```

> 💡 **提示**：USB 重新插拔后端口号可能变化，使用 `ls /dev/cu.*` 查看当前端口。

### 2. 编译

```bash
pio run
```

### 3. 烧录

```bash
pio run --target upload
```

### 4. 查看串口日志

```bash
pio device monitor
```

## 使用说明

### 首次配网

1. 烧录固件后，ESP8266 会启动一个 WiFi 热点
2. 连接热点（默认 SSID: `DoorClicker-<芯片ID>`）
3. 浏览器访问 `http://192.168.4.1`
4. 在配置页面输入 WiFi 信息和 MQTT Broker 地址
5. 保存后设备会重启并连接到指定网络

### 舵机测试

在配置页面可以点击"测试舵机"按钮，舵机会执行 0° → 90° → 0° 的旋转测试。

## MQTT 协议

详细的 MQTT 协议说明请参考 [mqtt-protocol.md](docs/mqtt-protocol.md)。

### Topic 格式

```
door/{chip_id}
```

其中 `{chip_id}` 为 ESP8266 芯片 ID（十六进制，如 `3FF12345`）。

### 开门指令示例

```json
{
  "type": "rotate",
  "actions": [
    {"angle": 90, "duration": 200},
    {"angle": 0, "duration": 200}
  ]
}
```

## 目录结构

```
door-clicker-firmware/
├── include/
│   ├── config_store.h       # 配置存储
│   ├── door_clicker_app.h   # 主应用类
│   ├── door_command.h       # 指令解析
│   ├── http_config_service.h # HTTP 配置服务
│   ├── logger.h             # 日志
│   └── servo_controller.h   # 舵机控制
├── src/
│   ├── main.cpp             # 程序入口
│   ├── door_clicker_app.cpp # 主应用实现
│   ├── door_command.cpp     # 指令解析实现
│   ├── http_config_service.cpp # HTTP 服务实现
│   ├── config_store.cpp     # 配置存储实现
│   ├── servo_controller.cpp # 舵机控制实现
│   └── logger.cpp           # 日志实现
├── docs/
│   └── mqtt-protocol.md     # MQTT 协议文档
├── lib/                     # 自定义库
├── test/                    # 单元测试
└── platformio.ini           # PlatformIO 配置
```

## 状态流转

```
开机 → 连接WiFi → 连接MQTT → 订阅Topic → 等待指令
                                              ↓
                                    接收MQTT消息
                                              ↓
                                        解析指令
                                              ↓
                                        执行动作
                                              ↓
                                        上报状态
                                              ↓
                                        继续等待
```

## 故障排查

### ESP8266 不断重启

- 检查供电是否充足（舵机启动电流可达 500mA+）
- 舵机建议使用外部 5V 供电

### MQTT 连接失败

- 确认 MQTT Broker 地址和端口
- 检查 WiFi 连接是否正常
- 查看串口日志中的错误信息

### 舵机不动作

- 确认 GPIO5 接线正确
- 使用配置页面的测试功能验证
- 检查舵机是否已初始化（发送 init 指令）

## 技术参数

| 参数 | 值 |
|------|-----|
| MCU | ESP8266EX |
| WiFi | 802.11 b/g/n |
| 工作电压 | 3.3V |
| 舵机接口 | PWM (GPIO5) |
| MQTT Buffer | 256 bytes |
