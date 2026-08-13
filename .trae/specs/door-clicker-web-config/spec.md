# Door Clicker Web 配置管理 - Product Requirement Document

## Overview
- **Summary**: 将 door-clicker-web 项目从一个简单的"开门"按钮应用，升级为具备完整 MQTT 配置管理能力的 Web 控制台。用户可以通过前端界面配置 MQTT 服务器地址、端口、用户名、密码，以及管理设备 Topic 订阅等。
- **Purpose**: 当前 Web 端的 MQTT 连接参数（服务器地址、端口等）全部硬编码在 Python 源码中，每次修改都需要重新部署。将配置开放到前端界面后，用户可以动态调整配置，无需修改代码和重启服务。
- **Target Users**: Door Clicker 设备的最终用户和管理员，需要通过 Web 界面远程管理 MQTT 连接配置。

## Goals
- 提供 Web 界面用于配置 MQTT 服务器连接参数（地址、端口、用户名、密码）
- 支持配置持久化存储（使用配置文件）
- 支持测试 MQTT 连接功能，验证配置是否正确
- 支持设备 Topic 管理（添加/删除/查看已订阅的设备 Topic）
- 保持现有"开门"功能正常工作

## Non-Goals (Out of Scope)
- 不修改固件（door-clicker-firmware）的功能
- 不实现用户认证/权限管理
- 不实现 Web 端的设备固件 OTA 升级
- 不实现批量管理多个设备
- 不实现数据加密存储（本地配置文件为明文）

## Background & Context
- **技术栈**: Python + Flask 后端，原生 HTML/CSS/JavaScript 前端
- **现有架构**: 
  - `app.py` - Flask 主应用，路由处理
  - `mqtt_command_publisher.py` - MQTT 命令发布，连接参数硬编码
  - `mqtt_command_subscriber.py` - MQTT 消息订阅
  - `templates/index.html` - 前端页面，仅包含开门按钮
- **固件协议**: 设备通过 MQTT 通信，Topic 格式为 `door/{device_id}`，详见 `door-clicker-firmware/docs/mqtt-protocol.md`
- **配置来源**: 固件端已有完整配置系统（`config_store.h`），Web 端需要类似的配置管理能力

## Functional Requirements
- **FR-1**: 提供 MQTT 配置页面，支持查看和编辑 MQTT 服务器地址、端口、用户名、密码
- **FR-2**: 支持将 MQTT 配置保存到本地配置文件（JSON 格式）
- **FR-3**: 应用启动时自动从配置文件加载 MQTT 参数
- **FR-4**: 提供"测试连接"功能，验证当前配置是否能成功连接 MQTT Broker
- **FR-5**: 支持设备 Topic 管理，用户可以添加/删除/查看需要监听的设备 Topic
- **FR-6**: "开门"命令使用最新的 MQTT 配置参数发送

## Non-Functional Requirements
- **NFR-1**: 配置更改无需重启服务即可生效（热加载）
- **NFR-2**: MQTT 连接失败时应有明确的错误提示
- **NFR-3**: 前端页面响应式设计，兼容移动端浏览器
- **NFR-4**: 配置文件损坏或不存在时应有合理的默认值和错误处理

## Constraints
- **Technical**: 
  - 后端使用 Python 3.x + Flask
  - MQTT 客户端使用 paho-mqtt
  - 前端使用原生 HTML/CSS/JS，不引入重型框架
- **Dependencies**: 
  - 需要可访问的 MQTT Broker 服务
  - 配置文件存储在本地文件系统

## Assumptions
- 用户拥有修改配置的权限（无多用户场景）
- MQTT Broker 支持标准 MQTT v3.1.1 协议
- 设备 Topic 格式为 `door/{device_id}`，device_id 为芯片 ID
- 本地文件系统有读写权限

## Acceptance Criteria

### AC-1: MQTT 配置页面可访问
- **Given**: 用户访问 Web 应用首页
- **When**: 浏览器加载页面
- **Then**: 页面显示 MQTT 配置区域，包含服务器地址、端口、用户名、密码四个输入框，以及保存和测试连接按钮
- **Verification**: `programmatic`

### AC-2: 配置保存成功
- **Given**: 用户在配置页面填写了有效的 MQTT 服务器地址和端口
- **When**: 用户点击"保存配置"按钮
- **Then**: 配置被保存到本地 JSON 文件，页面显示保存成功的提示
- **Verification**: `programmatic`

### AC-3: 配置热加载
- **Given**: 用户已保存新的 MQTT 配置
- **When**: 用户再次发送"开门"命令
- **Then**: 命令使用新的配置参数连接 MQTT Broker
- **Verification**: `programmatic`

### AC-4: 测试连接功能
- **Given**: 用户填写了 MQTT 服务器配置
- **When**: 用户点击"测试连接"按钮
- **Then**: 系统尝试连接 MQTT Broker 并显示成功或失败的结果
- **Verification**: `programmatic`

### AC-5: Topic 管理
- **Given**: 用户已配置 MQTT 连接
- **When**: 用户添加一个设备 Topic 并保存
- **Then**: 系统订阅该 Topic，并在页面上显示已订阅的 Topic 列表
- **Verification**: `programmatic`

### AC-6: 开门功能正常
- **Given**: MQTT 配置正确且已连接
- **When**: 用户点击"开门"按钮
- **Then**: 系统向配置的 MQTT Broker 发送开门指令，页面显示操作成功
- **Verification**: `programmatic`

### AC-7: 配置持久化
- **Given**: 用户已保存配置并重启应用
- **When**: 应用重新启动
- **Then**: 应用自动从配置文件加载上次保存的 MQTT 参数
- **Verification**: `programmatic`

### AC-8: 错误处理
- **Given**: MQTT 服务器地址配置错误或无法连接
- **When**: 用户点击"测试连接"或"开门"
- **Then**: 页面显示清晰的错误提示，而不是崩溃或无响应
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要支持 TLS/SSL 连接 MQTT Broker？
- [ ] 是否需要支持多个 MQTT Broker 配置？
- [ ] 是否需要通过 Web 界面下发舵机初始化命令（init）？
- [ ] 前端与后端的配置 API 是否需要 CORS 支持（跨域部署场景）？