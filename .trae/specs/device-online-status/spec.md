# 设备在线状态监控 - Product Requirement Document

## Overview
- **Summary**: 为 Door Clicker 系统增加设备在线状态监控功能。ESP8266 固件通过 MQTT 定期向 `status` topic 上报心跳，Web 端订阅该 topic 并根据最后心跳时间实时显示设备在线/离线状态，替代当前仅展示 MQTT 连接状态的不足。
- **Purpose**: 当前开门页面仅显示 Web 服务与 MQTT Broker 的连接状态，无法反映实际硬件设备的在线情况。用户可能看到"已连接"但实际设备已离线，导致开门指令无效。此功能让用户能区分"MQTT Broker 连接正常"和"物理设备在线"两个独立状态。
- **Target Users**: 家庭用户，需要通过手机远程开门的屋主。

## Goals
- 固件通过 MQTT 定期发布心跳消息，证明设备在线
- Web 端订阅状态 topic，实时追踪设备最后心跳时间
- 提供 API 查询设备在线/离线状态
- 开门页面分别展示"MQTT 连接状态"和"设备在线状态"
- 设备离线时在开门页面给出明确提示

## Non-Goals (Out of Scope)
- 不实现多设备管理（当前仅支持单个 ESP8266 设备）
- 不实现门磁传感器集成（仅基于 MQTT 心跳判断在线状态）
- 不实现开门历史记录功能（独立功能，后续可扩展）
- 不实现消息推送/通知功能

## Background & Context
- ESP8266 固件已实现 WiFi 和 MQTT 自动重连机制
- MQTT 协议文档已定义 `door/{device_id}/status` topic 用于状态上报，但固件尚未实际使用
- Web 端 MQTT 客户端已支持订阅 topic 和接收消息回调
- 开门页面已有"连接中/已连接"状态显示，需要拆分为两个独立状态

## Functional Requirements

- **FR-1 (固件心跳)**: ESP8266 固件在 MQTT 连接成功后，每隔 30 秒向 `door/{device_id}/status` topic 发布心跳消息，payload 包含设备 ID、时间戳和运行状态。
- **FR-2 (Web 订阅状态)**: Web 端 MQTT 客户端在连接成功后，自动订阅设备状态 topic `{doorTopic}/status`（如 `door/00094E53/status`），并在收到消息时更新设备在线状态。
- **FR-3 (状态追踪)**: Web 端维护设备最后心跳时间戳，若 90 秒内未收到新心跳，则判定设备为离线。
- **FR-4 (状态 API)**: 提供 `GET /api/device/status` API，返回设备在线状态（online/offline）、最后心跳时间、MQTT 连接状态等信息。
- **FR-5 (前端展示)**: 开门页面展示两个状态指示器：MQTT 连接状态（绿/灰）和设备在线状态（绿/灰），设备离线时开门按钮显示警告提示。
- **FR-6 (状态重置)**: Web 端 MQTT 断开连接时，设备状态应重置为"未知"，避免误导用户。

## Non-Functional Requirements

- **NFR-1 (性能)**: 心跳检测的判定延迟不超过 90 秒（3 倍心跳间隔），前端状态刷新间隔不超过 5 秒。
- **NFR-2 (可靠性)**: 心跳消息发送失败不应影响固件主循环和开门功能。
- **NFR-3 (可观测性)**: 设备状态变更事件（上线/离线）应记录到日志中。
- **NFR-4 (兼容性)**: 固件心跳功能在 MQTT 未配置时不影响设备正常运行；Web 端在未收到任何心跳前默认设备状态为"未知"。

## Constraints

- **Technical**:
  - 固件使用 Arduino Framework + PubSubClient，MQTT 消息大小有限制（PubSubClient 默认 256 bytes，可配置到 512）
  - ESP8266 单线程，心跳发布不能阻塞主循环
  - Web 端使用 Python + Flask + paho-mqtt
- **Business**: 心跳间隔选择 30 秒，平衡实时性和网络流量
- **Dependencies**: 依赖现有 MQTT Broker 可用

## Assumptions

- ESP8266 设备已正确配置 WiFi 和 MQTT 参数
- MQTT Broker 支持消息传输
- `doorTopic` 配置项在 Web 端已正确设置（如 `door/00094E53`）
- 固件和 Web 端使用相同的 `doorTopic` 配置
- 用户理解"MQTT 已连接"和"设备在线"是两个不同概念

## Acceptance Criteria

### AC-1: 固件定期发送心跳
- **Given**: ESP8266 已连接 WiFi 和 MQTT Broker
- **When**: 固件运行中
- **Then**: 每 30 秒向 `door/{device_id}/status` 发布心跳消息，payload 包含 `{"event":"heartbeat","clientId":"door_XXXX","uptime":秒数}`
- **Verification**: `programmatic`
- **Notes**: 通过串口日志确认心跳发布；通过 MQTT 客户端工具（如 mosquitto_sub）订阅验证

### AC-2: Web 端订阅并接收心跳
- **Given**: Web 服务已启动且 MQTT 已连接
- **When**: Web 端 MQTT 连接成功
- **Then**: 自动订阅 `{doorTopic}/status` topic，收到心跳后记录时间戳
- **Verification**: `programmatic`

### AC-3: 设备在线状态判定
- **Given**: Web 服务运行中
- **When**: 收到心跳后 90 秒内再次收到心跳
- **Then**: 设备状态为 `online`
- **Verification**: `programmatic`

### AC-4: 设备离线状态判定
- **Given**: Web 服务运行中
- **When**: 距离最后一次收到心跳已超过 90 秒
- **Then**: 设备状态为 `offline`
- **Verification**: `programmatic`

### AC-5: 设备状态 API
- **Given**: Web 服务运行中
- **When**: 调用 `GET /api/device/status`
- **Then**: 返回 JSON `{"deviceOnline": true/false, "lastHeartbeat": "ISO时间或null", "mqttConnected": true/false, "status": "online"/"offline"/"unknown"}`
- **Verification**: `programmatic`

### AC-6: 前端状态展示
- **Given**: 用户访问开门页面
- **When**: 页面加载完成
- **Then**: 页面显示两个状态指示器（MQTT 连接 + 设备在线），设备离线时显示警告文字
- **Verification**: `human-judgment`

### AC-7: MQTT 断开时状态重置
- **Given**: Web 端 MQTT 连接已断开
- **When**: 调用设备状态 API
- **Then**: 返回 `{"mqttConnected": false, "deviceOnline": false, "status": "unknown"}`
- **Verification**: `programmatic`

### AC-8: 日志记录状态变更
- **Given**: 设备状态发生变化（上线/离线）
- **When**: 状态变更事件触发
- **Then**: 日志中记录状态变更信息
- **Verification**: `programmatic`

### AC-9: 固件心跳不影响开门
- **Given**: 固件正常运行中
- **When**: 心跳发布与开门命令同时发生
- **Then**: 开门命令正常执行，心跳消息可在下一个周期补发
- **Verification**: `programmatic`

## Open Questions
- [ ] 设备 ID 是否需要在配置页可查看/修改？（当前自动生成）
- [ ] 心跳间隔 30 秒是否合适？用户是否需要可配置？
- [ ] 是否需要支持心跳间隔的远程配置？
