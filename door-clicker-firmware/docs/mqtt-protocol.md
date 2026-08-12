# Door Clicker MQTT 协议文档

## 主题 (Topic) 设计

| 主题 | 方向 | 说明 |
|------|------|------|
| `door/{device_id}` | 订阅 ↓ | 接收所有指令 |
| `door/{device_id}/status` | 发布 ↑ | 设备上报状态 |

> `{device_id}` 为设备唯一标识，由 `mqttClientId` 决定

---

## 1. 初始化舵机 (init)

**主题**: `door/device001`
**Payload**:
```json
{
  "type": "init",
  "pin": 2,
  "minAngle": 0,
  "maxAngle": 180,
  "initialAngle": 0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✓ | 固定 `"init"` |
| `pin` | int | ✓ | ESP8266 舵机引脚号 |
| `minAngle` | int | 推荐 | 最小角度，默认 0 |
| `maxAngle` | int | 推荐 | 最大角度，默认 180 |
| `initialAngle` | int | 推荐 | 初始化停留角度，默认 0 |

**触发上报**: 设备向 `door/device001/status` 推送 `{"event":"init", ...}`

---

## 2. 旋转舵机 (rotate)

**主题**: `door/device001`
**Payload**:
```json
{
  "type": "rotate",
  "actions": [
    {"angle": 90, "speed": 50, "delay": 100},
    {"angle": 0, "speed": 50, "delay": 500}
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | ✓ | 固定 `"rotate"` |
| `actions` | array | ✓ | 动作序列，按顺序执行 |
| `actions[].angle` | int | ✓ | 目标角度（自动 clamp 到 minAngle~maxAngle） |
| `actions[].speed` | int | 推荐 | 旋转速度 1-100，默认 50 |
| `actions[].delay` | int | 推荐 | 到达目标后停留毫秒数 |

**触发上报**: 完成后推送 `{"event":"rotate_done", ...}`

---

## 3. 状态上报 (status)

**主题**: `door/device001/status`
**Payload**:
```json
{
  "event": "rotate_done",
  "pin": 2,
  "angle": 0,
  "initialized": true,
  "clientId": "ESP8266Client"
}
```

| event 值 | 触发时机 |
|----------|---------|
| `connected` | MQTT 连接成功 |
| `init` | 舵机初始化完成 |
| `rotate_done` | 旋转动作序列完成 |

---

## 字段速查表

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `pin` | uint8 | 0-16 | ESP8266 GPIO 引脚 |
| `minAngle` | int | 0-180 | 最小角度限制 |
| `maxAngle` | int | 0-180 | 最大角度限制 |
| `angle` | int | minAngle-maxAngle | 目标/当前角度 |
| `speed` | int | 1-100 | 旋转速度（数值越大越快） |
| `delay` | int | ≥0 | 停留延时 (ms) |
