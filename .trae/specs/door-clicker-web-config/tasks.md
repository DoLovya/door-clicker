# Door Clicker Web 配置管理 - The Implementation Plan

## [x] Task 1: 后端配置管理模块
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 创建 `config_manager.py`，实现配置的加载、保存、热加载功能
  - 使用 JSON 文件存储配置（`config.json`）
  - 配置项包括：mqttServer, mqttPort, mqttUsername, mqttPassword, topics 列表
  - 提供默认配置值
  - 提供线程安全的配置读写接口
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-7
- **Test Requirements**:
  - `programmatic` TR-1.1: 初始化时若配置文件不存在，使用默认值创建新文件
  - `programmatic` TR-1.2: `save_config()` 能正确将配置写入 JSON 文件
  - `programmatic` TR-1.3: `load_config()` 能正确从 JSON 文件读取配置
  - `programmatic` TR-1.4: 配置文件损坏时能捕获异常并使用默认值
  - `programmatic` TR-1.5: 保存后再次读取能拿到最新值
- **Notes**: 使用单例模式或模块级变量确保全局唯一配置实例

## [x] Task 2: MQTT 客户端管理器
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 重构 `mqtt_command_publisher.py`，创建 `MqttClientManager` 类
  - 从 ConfigManager 读取连接参数，而非硬编码
  - 支持连接/断开/重连操作
  - 支持动态订阅/取消订阅 Topic
  - 支持连接测试功能
  - 支持发送开门指令
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-2.1: 使用配置中的参数成功连接 MQTT Broker
  - `programmatic` TR-2.2: 连接失败时返回错误信息而非异常崩溃
  - `programmatic` TR-2.3: `test_connection()` 能正确返回连接状态
  - `programmatic` TR-2.4: `subscribe_topic()` 能成功订阅指定 Topic
  - `programmatic` TR-2.5: `publish_open_door()` 能发送正确格式的开门指令
  - `programmatic` TR-2.6: 配置变更后下次连接使用新参数
- **Notes**: 使用 paho-mqtt 库，注意回调函数的线程安全

## [x] Task 3: REST API 路由
- **Priority**: high
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 在 `app.py` 中添加配置管理相关的 API 路由：
    - `GET /api/config` - 获取当前配置
    - `PUT /api/config` - 更新配置
    - `POST /api/mqtt/test` - 测试 MQTT 连接
    - `GET /api/mqtt/status` - 获取 MQTT 连接状态
    - `GET /api/topics` - 获取已订阅 Topic 列表
    - `POST /api/topics` - 添加 Topic 订阅
    - `DELETE /api/topics/<topic>` - 取消 Topic 订阅
  - 保持现有 `/api/open/door` 路由，改为使用 MqttClientManager
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-4, AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-3.1: GET /api/config 返回完整配置 JSON
  - `programmatic` TR-3.2: PUT /api/config 接收新配置并保存
  - `programmatic` TR-3.3: POST /api/mqtt/test 返回连接测试结果
  - `programmatic` TR-3.4: POST /api/topics 成功添加 Topic 并返回列表
  - `programmatic` TR-3.5: DELETE /api/topics/<topic> 成功移除 Topic
  - `programmatic` TR-3.6: POST /api/open/door 正常触发开门指令
  - `programmatic` TR-3.7: 所有 API 返回正确的 HTTP 状态码和 JSON 格式
- **Notes**: 输入验证：端口号应为整数，服务器地址非空等

## [x] Task 4: 前端配置页面
- **Priority**: high
- **Depends On**: Task 3
- **Description**: 
  - 重构 `templates/index.html`，添加配置管理界面
  - 页面分为三个区域：MQTT 连接配置、Topic 管理、开门控制
  - MQTT 配置区域：服务器地址、端口、用户名、密码输入框 + 保存/测试按钮
  - Topic 管理区域：显示已订阅列表 + 添加/删除功能
  - 开门控制区域：保持现有开门按钮
  - 支持连接状态指示（已连接/未连接/连接中）
  - 响应式布局，兼容移动端
- **Acceptance Criteria Addressed**: AC-1, AC-5, AC-6, AC-8
- **Test Requirements**:
  - `human-judgement` TR-4.1: 页面布局清晰，三个功能区域一目了然
  - `human-judgement` TR-4.2: 表单输入和按钮交互流畅
  - `human-judgement` TR-4.3: 操作结果有明确的成功/失败反馈
  - `human-judgement` TR-4.4: 移动端浏览体验可接受
  - `programmatic` TR-4.5: 保存配置后刷新页面能看到最新值
  - `programmatic` TR-4.6: 测试连接按钮点击后显示结果
  - `programmatic` TR-4.7: 添加/删除 Topic 后列表实时更新
- **Notes**: 可使用简单的 CSS 框架或手写样式，保持轻量

## [x] Task 5: 错误处理与边界情况
- **Priority**: medium
- **Depends On**: Task 1, Task 2, Task 3, Task 4
- **Description**: 
  - 添加全局错误处理，确保 API 异常时返回 500 JSON 响应
  - MQTT 连接超时处理
  - 配置文件并发写入保护
  - 空值/null 值处理
  - 端口号范围校验（1-65535）
  - 前端表单输入校验
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `programmatic` TR-5.1: MQTT 连接超时返回超时错误信息
  - `programmatic` TR-5.2: 无效端口号（如 0, 99999）被拒绝
  - `programmatic` TR-5.3: 空的服务器地址被拒绝
  - `programmatic` TR-5.4: API 异常时返回 {\"error\": \"message\"} 格式
  - `human-judgement` TR-5.5: 前端错误提示清晰友好
- **Notes**: 错误信息应具体，便于用户排查问题

## [x] Task 6: 启动流程与集成测试
- **Priority**: medium
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 确保应用启动时自动加载配置并初始化 MQTT 连接
  - 添加启动日志输出
  - 添加简单的健康检查端点 `/api/health`
  - 验证完整流程：启动→加载配置→连接 MQTT→Web 访问→配置修改→热加载
- **Acceptance Criteria Addressed**: AC-3, AC-7
- **Test Requirements**:
  - `programmatic` TR-6.1: 启动后 /api/config 返回已保存的配置
  - `programmatic` TR-6.2: /api/health 返回 {\"status\": \"ok\"}
  - `programmatic` TR-6.3: 修改配置后无需重启即可使用新配置
  - `programmatic` TR-6.4: 配置文件存在时正确加载，不存在时使用默认值
- **Notes**: 此任务主要是集成验证，确保各模块协同工作