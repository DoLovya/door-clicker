# 设备在线状态监控 - Implementation Plan

## [x] Task 1: 固件添加 MQTT 心跳发布功能
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `door_clicker_app.cpp` 的 `loop()` 方法中添加心跳发布逻辑
  - 每 30 秒向 `door/{device_id}/status` topic 发布心跳消息
  - 心跳 payload: `{"event":"heartbeat","clientId":"door_XXXX","uptime":秒数}`
  - 在 `tryConnectMqtt()` 成功后立即发布一次上线状态消息 `{"event":"connected","clientId":"door_XXXX"}`
  - 使用 `millis()` 计算时间，避免阻塞主循环
  - 心跳发布失败仅记录日志，不影响主循环
- **Acceptance Criteria Addressed**: AC-1, AC-9
- **Test Requirements**:
  - `programmatic` TR-1.1: 固件 loop() 中每 30 秒发布一次心跳到 status topic
  - `programmatic` TR-1.2: MQTT 连接成功后立即发布 connected 事件
  - `programmatic` TR-1.3: 心跳发布失败不阻塞主循环
  - `programmatic` TR-1.4: 心跳消息 payload 格式符合 JSON 规范
- **Notes**: 使用 `PubSubClient.publish()` 发布，不需要等待；保持现有代码风格

## [x] Task 2: Web 端 MQTT 客户端添加设备状态追踪
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `mqtt_client_manager.py` 中添加设备状态追踪功能
  - 新增 `_device_online`、`_last_heartbeat`、`_status_topic` 属性
  - MQTT 连接成功后自动订阅 `{doorTopic}/status` topic
  - 在 `_on_message` 中解析心跳消息，更新 `_last_heartbeat` 时间戳
  - 新增 `is_device_online()` 方法，检查最后心跳时间是否在 90 秒内
  - 新增 `get_device_status()` 方法，返回完整设备状态信息
  - MQTT 断开时重置设备状态为未知
  - 状态变更（上线/离线）时记录日志
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-4, AC-7, AC-8
- **Test Requirements**:
  - `programmatic` TR-2.1: MQTT 连接成功后自动订阅 status topic
  - `programmatic` TR-2.2: 收到心跳后 `_last_heartbeat` 被更新
  - `programmatic` TR-2.3: 90 秒内有心跳 → `is_device_online()` 返回 True
  - `programmatic` TR-2.4: 超过 90 秒无心跳 → `is_device_online()` 返回 False
  - `programmatic` TR-2.5: MQTT 断开连接 → 设备状态重置为未知
  - `programmatic` TR-2.6: 状态变更事件记录日志

## [x] Task 3: Web 端添加设备状态 API
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 在 `app.py` 中新增 `GET /api/device/status` API
  - 返回 JSON: `{"deviceOnline": bool, "lastHeartbeat": ISO时间或null, "mqttConnected": bool, "status": "online"/"offline"/"unknown"}`
  - 新增 `POST /api/mqtt/reset-device-status` API（管理员权限），用于手动重置设备状态
  - 在 `init_mqtt()` 中设置 `on_message_callback` 处理心跳消息
- **Acceptance Criteria Addressed**: AC-5, AC-7
- **Test Requirements**:
  - `programmatic` TR-3.1: `GET /api/device/status` 返回正确的 JSON 格式
  - `programmatic` TR-3.2: 设备在线时 `deviceOnline` 为 true
  - `programmatic` TR-3.3: 设备离线时 `deviceOnline` 为 false
  - `programmatic` TR-3.4: MQTT 断开时 `status` 为 "unknown"
  - `programmatic` TR-3.5: 状态变更事件在日志中可查

## [x] Task 4: 开门页面前端更新设备状态展示
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - 修改 `door.html`，在状态栏显示两个独立状态：
    - MQTT 连接状态（保持原有显示）
    - 设备在线状态（新增，使用不同颜色或图标区分）
  - 页面加载时同时查询 MQTT 状态和设备状态
  - 定时刷新（每 5 秒更新设备状态）
  - 设备离线时，开门按钮下方显示警告文字
  - 保持移动端响应式设计
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `human-judgement` TR-4.1: 页面清晰展示 MQTT 状态和设备状态两个独立指示器
  - `human-judgement` TR-4.2: 设备离线时有明确的视觉警告
  - `human-judgement` TR-4.3: 移动端布局合理，状态指示器清晰可见
  - `programmatic` TR-4.4: 页面 JavaScript 正确调用 `/api/device/status` API

## [x] Task 5: 更新 MQTT 协议文档
- **Priority**: medium
- **Depends On**: Task 1
- **Description**:
  - 在 `mqtt-protocol.md` 中更新状态上报部分
  - 新增心跳消息 payload 格式说明
  - 说明心跳间隔和判定规则
  - 补充 `heartbeat` 事件类型到状态上报表
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `human-judgement` TR-5.1: 文档清晰描述心跳消息格式
  - `human-judgement` TR-5.2: 文档说明在线/离线判定规则

## [x] Task 6: 添加单元测试和集成测试
- **Priority**: high
- **Depends On**: Task 2, Task 3
- **Description**:
  - 在 `mqtt_client_manager_test.py` 中添加设备状态追踪相关测试
  - 在 `app_test.py` 中添加设备状态 API 测试
  - 在 `integration_test.py` 中添加设备状态集成测试
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-4, AC-5, AC-7
- **Test Requirements**:
  - `programmatic` TR-6.1: 测试 MQTT 连接后自动订阅 status topic
  - `programmatic` TR-6.2: 测试心跳消息处理和时间戳更新
  - `programmatic` TR-6.3: 测试在线/离线状态判定逻辑
  - `programmatic` TR-6.4: 测试 MQTT 断开时状态重置
  - `programmatic` TR-6.5: 测试 `/api/device/status` API 返回值
  - `programmatic` TR-6.6: 运行完整测试套件，所有测试通过
