# Door Clicker MQTT 协议文档

## 主题 (Topic) 设计

| 主题 | 方向 | 说明 |
|------|------|------|
| `door/{device_id}` | 订阅 ↓ | 接收所有指令 |
| `door/{device_id}/status` | 发布 ↑ | 设备上报状态（心跳、上线、执行结果） |

> `{device_id}` 由 ESP8266 Chip ID 自动生成，格式: `door_{HEX}`
> 例如: `door_3FF12345`

---

## 配置项

| 配置项 | 说明 |
|--------|------|
| `mqttServer` | MQTT 服务器地址（必填） |
| `mqttPort` | MQTT 服务器端口（默认 1883） |
| `device_id` | 自动生成，基于 Chip ID |
| `topic` | 自动生成，格式 `door/{device_id}` |

---

## 引脚配置

| ESP8266 引脚 | GPIO | 功能 | 备注 |
|-------------|------|------|------|
| D1 | **5** | 舵机信号线 (PWM) | 默认引脚 |
| VCC | 3.3V | 舵机电源 | 建议外部 5V 供电 |
| G | GND | 接地 | - |

> ⚠️ GPIO5 对应开发板 D1 引脚。舵机启动电流较大（可达 500mA+），建议使用外部电源供电。

---

### 舵机配置

舵机参数（引脚、角度范围、初始角度）通过 `config.json` 持久化存储，设备启动时自动初始化，无需通过 MQTT 下发。

config.json 中相关字段：
- `servoPin`: GPIO 引脚号（默认 2，即 D4）
- `servoMinAngle`: 最小角度（默认 0）
- `servoMaxAngle`: 最大角度（默认 180）
- `servoInitialAngle`: 初始角度（默认 0）

---

## 1. 开门命令 (Rotate)

**主题**: `door/{device_id}`

**Payload**:
```json
{
  "type": "rotate",
  "actions": [
    {"angle": 90, "duration": 200},
    {"angle": 0, "duration": 200}
  ]
}
```

或兼容旧格式：
```json
[{"angle": 90, "duration": 200}, {"angle": 0, "duration": 200}]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 固定 `"rotate"`（可选，兼容旧格式） |
| `actions` | array | 动作序列（可选，兼容旧格式） |
| `angle` | int | 目标角度（0-180） |
| `duration` | int | 动作持续时间（毫秒） |

---

## 2. 状态上报 (status)

**主题**: `door/{device_id}/status`

### 2.1 心跳消息

设备每 30 秒发布一次心跳消息，用于证明设备在线。

**Payload**:
```json
{
  "event": "heartbeat",
  "clientId": "door_3FF12345",
  "uptime": 3600
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | 固定 `"heartbeat"` |
| `clientId` | string | 设备 MQTT 客户端 ID |
| `uptime` | uint32 | 设备运行时间（秒） |

### 2.2 上线事件

MQTT 连接成功后立即发布。

**Payload**:
```json
{
  "event": "connected",
  "clientId": "door_3FF12345"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | string | 固定 `"connected"` |
| `clientId` | string | 设备 MQTT 客户端 ID |

### 2.3 执行结果

**Payload**:
```json
{
  "event": "rotate",
  "clientId": "door_3FF12345"
}
```

| event 值 | 触发时机 |
|----------|---------|
| `connected` | MQTT 连接成功 |
| `heartbeat` | 每 30 秒定期上报 |
| `rotate` | 接收开门命令 |

### 2.4 在线/离线判定规则

| 条件 | 判定结果 |
|------|---------|
| Web 端 90 秒内收到心跳 | 设备 **在线** |
| Web 端超过 90 秒未收到心跳 | 设备 **离线** |
| MQTT 连接断开 | 设备状态 **未知** |
| 从未收到过心跳 | 设备状态 **未知** |

> 心跳间隔 30 秒，超时判定使用 3 倍间隔（90 秒），容忍偶发网络抖动。

---

## 字段速查表

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `angle` | int | 0-180 | 目标角度 |
| `duration` | int | ≥0 | 每个动作的持续时间 (ms) |
| `uptime` | uint32 | ≥0 | 设备运行时间（秒），心跳消息中上报 |
