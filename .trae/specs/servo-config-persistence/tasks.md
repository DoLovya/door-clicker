# 舵机配置持久化与协议简化 - Implementation Plan

## [x] Task 1: 扩展固件 ConfigStore 支持舵机配置
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `config_store.h` 的 `AppConfigData` 结构体中新增舵机配置字段
  - 在 `config_store.cpp` 的 `syncDocToStruct()` 中解析舵机配置
  - 默认值：`servoPin=5, servoMinAngle=0, servoMaxAngle=180, servoInitialAngle=0`
  - 保持向后兼容：如果 config.json 中没有舵机字段，使用默认值
- **Acceptance Criteria Addressed**: AC-6, AC-7
- **Test Requirements**:
  - `programmatic` TR-1.1: `AppConfigData` 结构体包含 4 个新字段
  - `programmatic` TR-1.2: `syncDocToStruct()` 正确解析舵机配置
  - `programmatic` TR-1.3: config.json 无舵机字段时使用默认值
- **Notes**: 这是整个功能的基础，其他任务依赖此扩展

## [x] Task 2: 在 setup() 中初始化舵机
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 修改 `door_clicker_app.cpp` 的 `setup()` 方法
  - 在 `setupWifi()` 之后、MQTT 初始化之前，添加舵机初始化逻辑
  - 从 `ConfigStore::instance().getConfig()` 读取舵机参数
  - 调用 `servoController_.init(pin, minAngle, maxAngle, initialAngle)`
  - 添加日志记录初始化过程
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: `setup()` 中调用 `servoController_.init()`
  - `programmatic` TR-2.2: 日志包含 "Initialized, pin=X range=Y-Z angle=W" 输出
  - `programmatic` TR-2.3: 初始化失败不阻塞后续 WiFi/MQTT 初始化
- **Notes**: 舵机初始化应尽早执行，确保开门命令可用

## [x] Task 3: 删除 Init 协议处理逻辑
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 从 `door_command.h` 中删除 `MqttCmdType::Init` 枚举值
  - 删除 `ServoInitConfig` 结构体
  - 从 `DoorCommandMessage` 中删除 `initConfig` 成员
  - 修改 `door_command.cpp` 的 `parseDoorCommandMessage()` 移除 Init 解析逻辑
  - 修改 `door_clicker_app.cpp` 的 `handleMqttMessage()` 移除 Init 处理分支
  - 简化 `door_command.h` 移除不再需要的类型定义
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: `MqttCmdType` 枚举不包含 `Init`
  - `programmatic` TR-3.2: `DoorCommandMessage` 结构体不包含 `initConfig`
  - `programmatic` TR-3.3: 收到 Init 格式消息时返回 Unknown 类型
  - `programmatic` TR-3.4: Rotate 命令仍可正常解析和执行

## [x] Task 4: 简化 ServoController
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - 从 `servo_controller.h` 删除 `lastInitPin_`、`lastInitMinAngle_`、`lastInitMaxAngle_`、`lastInitInitialAngle_` 成员变量
  - 从 `servo_controller.cpp` 删除 `init()` 中保存 `lastInit*_` 的代码
  - 从 `execute()` 中删除自动初始化逻辑（因为 setup 已完成）
  - 从 `testOpen()` 中删除自动初始化逻辑
  - `execute()` 中如果 `!initialized_` 则记录错误日志并跳过（理论上不会发生）
  - 保持 `execute()` 的错误处理：未初始化时记录警告并返回
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-4.1: `ServoController` 类无 `lastInit*_` 成员
  - `programmatic` TR-4.2: `execute()` 不调用 `init()`
  - `programmatic` TR-4.3: `testOpen()` 不调用 `init()`
  - `programmatic` TR-4.4: 未初始化时 `execute()` 返回日志警告

## [x] Task 5: Web 端支持舵机配置
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 在 `config_manager.py` 的 `_DEFAULT_CONFIG` 中增加舵机默认值
  - 修改 `config_manager.py` 支持保存舵机配置字段
  - 修改 `index.html` 配置页面，增加舵机配置表单区域
  - 表单字段：引脚（数字输入）、最小角度（数字输入）、最大角度（数字输入）、初始角度（数字输入）
  - `loadConfig()` 加载舵机配置到表单
  - `saveConfig()` 保存舵机配置到后端
  - 在 `app.py` 的 `api_update_config()` 中支持舵机配置字段
- **Acceptance Criteria Addressed**: AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-5.1: `_DEFAULT_CONFIG` 包含舵机字段
  - `programmatic` TR-5.2: 配置页面显示舵机配置表单
  - `programmatic` TR-5.3: 保存配置时包含舵机参数
  - `human-judgement` TR-5.4: 表单布局清晰，移动端友好

## [x] Task 6: 更新协议文档
- **Priority**: medium
- **Depends On**: Task 3
- **Description**:
  - 修改 `mqtt-protocol.md`，删除 Init 协议相关内容
  - 更新协议说明，明确只有 Rotate 一种命令类型
  - 说明舵机配置通过 config.json 持久化，不通过 MQTT 下发
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `human-judgement` TR-6.1: 文档准确描述 Rotate 协议格式
  - `human-judgement` TR-6.2: 文档说明舵机配置方式

## [x] Task 7: 单元测试与验证
- **Priority**: high
- **Depends On**: Task 1-6
- **Description**:
  - 运行固件编译验证无错误
  - 运行 Web 端现有测试套件确保无回归
  - 手动验证：设备重启后开门命令立即可用
  - 手动验证：Init 协议消息被正确忽略
  - 手动验证：配置页面可编辑和保存舵机参数
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7
- **Test Requirements**:
  - `programmatic` TR-7.1: 固件编译无错误
  - `programmatic` TR-7.2: Web 端 88 个测试全部通过
  - `human-judgement` TR-7.3: 手动测试设备重启后开门功能正常
  - `human-judgement` TR-7.4: 手动测试 Init 消息被忽略
