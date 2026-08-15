# 舵机配置持久化与协议简化 - Product Requirement Document

## Overview
- **Summary**: 将舵机控制器的初始化参数（引脚、角度范围、初始角度）持久化到 `config.json` 配置文件，并在固件 `setup()` 启动时自动初始化舵机，同时删除 MQTT Init 协议，只保留 Rotate 协议用于发送开门命令。
- **Purpose**: 解决 ESP8266 重启后舵机未初始化导致开门命令失效的问题。当前舵机配置仅存在于内存中，需要通过 MQTT Init 命令下发，一旦设备重启就会丢失。通过持久化配置，设备启动后即可立即响应开门命令。
- **Target Users**: 门控系统的终端用户，通过 Web 页面远程控制开门。

## Goals
- [ ] 舵机配置持久化到 `config.json`，设备断电重启后自动恢复
- [ ] 固件 `setup()` 启动时根据配置自动初始化舵机
- [ ] 删除 MQTT Init 命令类型，简化协议为纯 Rotate 模式
- [ ] Web 配置页面增加舵机配置表单（引脚、角度范围、初始角度）
- [ ] 简化 `ServoController`，移除不必要的内存缓存逻辑

## Non-Goals (Out of Scope)
- [ ] 不改变开门命令的执行逻辑（Rotate 协议的 payload 格式保持不变）
- [ ] 不修改设备状态监控（心跳）功能
- [ ] 不修改 Web 端登录认证逻辑

## Background & Context
- **当前架构**: 
  - 舵机参数通过 MQTT Init 命令下发到固件，固件在内存中保存
  - 开门命令通过 MQTT Rotate 命令发送，固件执行舵机动作
  - `config.json` 当前存储 WiFi、MQTT、管理员密码等配置
  - ESP8266 使用 LittleFS 存储配置文件
- **问题**: 
  - 设备重启后内存清零，舵机 `initialized_` 重置为 false
  - 开门命令只包含角度/时长信息，不包含舵机配置
  - 之前的修复方案是在内存中保存 `lastInit*_` 参数，但这仍然不持久化

## Functional Requirements
- **FR-1**: `config.json` 新增 `servoPin`、`servoMinAngle`、`servoMaxAngle`、`servoInitialAngle` 字段
- **FR-2**: `ConfigStore` 扩展以支持读取和保存舵机配置
- **FR-3**: `DoorClickerApp::setup()` 启动时从配置读取舵机参数并调用 `servoController_.init()`
- **FR-4**: 删除 `MqttCmdType::Init` 枚举值及相关处理逻辑
- **FR-5**: `parseDoorCommandMessage()` 不再解析 Init 命令，只处理 Rotate
- **FR-6**: `ServoController` 简化，移除 `lastInit*_` 成员变量
- **FR-7**: `execute()` 和 `testOpen()` 不再需要自动初始化逻辑（因为 setup 已完成）
- **FR-8**: Web 配置页面增加舵机配置表单
- **FR-9**: Web `ConfigManager` 增加舵机配置的默认值
- **FR-10**: Web API 的 `PUT /api/config` 支持保存舵机配置并通过 MQTT 通知设备重载

## Non-Functional Requirements
- **NFR-1**: 设备启动后 1 秒内完成舵机初始化
- **NFR-2**: 配置文件损坏或缺失时使用默认值（pin=5, range=0-180, angle=0）
- **NFR-3**: 保持与现有 MQTT Rotate 命令的向后兼容

## Constraints
- **Technical**: 
  - ESP8266 + Arduino 框架
  - LittleFS 文件系统（固件侧）
  - Flask + Python（Web 服务端）
- **Dependencies**: 
  - Arduino Servo 库
  - ArduinoJson 库

## Assumptions
- [ ] 舵机配置变更频率低，不需要实时热更新
- [ ] 每次修改舵机配置后需要设备重启才能生效（或通过 MQTT 通知重载）
- [ ] 引脚 5 是舵机的标准连接引脚
- [ ] 角度范围 0-180 适用于所有舵机型号

## Acceptance Criteria

### AC-1: 设备启动自动初始化舵机
- **Given**: 设备已正确配置 `servoPin=5, servoMinAngle=0, servoMaxAngle=180, servoInitialAngle=0`
- **When**: 设备上电启动
- **Then**: `setup()` 完成后舵机已初始化并归位到初始角度
- **Verification**: `programmatic`
- **Notes**: 通过串口日志确认 "Initialized, pin=5 range=0-180 angle=0" 输出

### AC-2: 重启后开门命令立即可用
- **Given**: 设备刚完成启动（已通过 AC-1 初始化）
- **When**: Web 端发送开门命令
- **Then**: 舵机立即执行开门动作，无需先发送 Init 命令
- **Verification**: `programmatic`

### AC-3: Init 协议已删除
- **Given**: 固件已编译新代码
- **When**: 收到 `{"type": "init", ...}` 格式的 MQTT 消息
- **Then**: 固件忽略该消息或返回 Unknown 状态，不执行任何舵机初始化
- **Verification**: `programmatic`

### AC-4: Rotate 协议正常工作
- **Given**: 设备已启动并初始化舵机
- **When**: 收到 `[{"angle": 90, "duration": 200}, {"angle": 0, "duration": 200}]` 格式的消息
- **Then**: 舵机按顺序执行旋转动作
- **Verification**: `programmatic`

### AC-5: 配置页面可编辑舵机参数
- **Given**: 用户已登录管理员账户
- **When**: 访问配置页面
- **Then**: 看到舵机配置表单（引脚、最小角度、最大角度、初始角度）
- **Verification**: `human-judgment`

### AC-6: 保存舵机配置到 config.json
- **Given**: 用户在配置页面修改了舵机参数
- **When**: 点击"保存配置"
- **Then**: `config.json` 文件中包含新的舵机参数
- **Verification**: `programmatic`

### AC-7: 默认配置值
- **Given**: `config.json` 不存在或损坏
- **When**: 设备启动
- **Then**: 使用默认值 `pin=5, minAngle=0, maxAngle=180, initialAngle=0`
- **Verification**: `programmatic`

## Open Questions
- [ ] 是否需要在 Web 端添加"手动触发舵机重载"按钮（通过 MQTT 发送命令让设备重新读取 config.json）？
- [ ] 舵机配置变更后，是否需要设备自动重启，还是可以通过 MQTT 热更新？
