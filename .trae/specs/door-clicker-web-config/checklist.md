# Door Clicker Web 配置管理 - Verification Checklist

## 后端配置管理
- [x] Checkpoint 1: `config_manager.py` 模块已创建，支持配置的加载和保存
- [x] Checkpoint 2: 配置文件使用 JSON 格式，包含 mqttServer, mqttPort, mqttUsername, mqttPassword, topics 字段
- [x] Checkpoint 3: 配置文件不存在时使用默认值，损坏时有错误处理
- [x] Checkpoint 4: 配置保存后再次读取能获取最新值

## MQTT 客户端管理
- [x] Checkpoint 5: `MqttClientManager` 类从配置读取连接参数，不再硬编码
- [x] Checkpoint 6: 支持连接测试功能，能返回成功/失败状态
- [x] Checkpoint 7: 支持动态订阅和取消订阅 Topic
- [x] Checkpoint 8: 开门指令使用配置中的参数发送到正确的 Broker
- [x] Checkpoint 9: 连接失败时有明确的错误处理，不会导致崩溃

## REST API
- [x] Checkpoint 10: `GET /api/config` 返回当前配置 JSON
- [x] Checkpoint 11: `PUT /api/config` 能保存新配置并热加载
- [x] Checkpoint 12: `POST /api/mqtt/test` 返回连接测试结果
- [x] Checkpoint 13: `GET /api/mqtt/status` 返回 MQTT 连接状态
- [x] Checkpoint 14: `GET /api/topics` 返回已订阅 Topic 列表
- [x] Checkpoint 15: `POST /api/topics` 能添加新的 Topic 订阅
- [x] Checkpoint 16: `DELETE /api/topics/<topic>` 能移除 Topic 订阅
- [x] Checkpoint 17: `POST /api/open/door` 使用最新配置发送开门指令
- [x] Checkpoint 18: `GET /api/health` 返回健康检查响应
- [x] Checkpoint 19: 所有 API 返回正确的 HTTP 状态码和 JSON 响应格式

## 前端界面
- [x] Checkpoint 20: 页面包含 MQTT 配置区域、Topic 管理区域、开门控制区域
- [x] Checkpoint 21: MQTT 配置表单能正确显示和编辑服务器地址、端口、用户名、密码
- [x] Checkpoint 22: "保存配置"按钮能触发保存并给出成功/失败反馈
- [x] Checkpoint 23: "测试连接"按钮能显示 MQTT 连接测试结果
- [x] Checkpoint 24: Topic 管理区域显示已订阅列表，支持添加和删除
- [x] Checkpoint 25: 连接状态指示器能反映当前 MQTT 连接状态
- [x] Checkpoint 26: 开门按钮保持原有功能正常工作
- [x] Checkpoint 27: 页面在移动端浏览器可正常使用（响应式布局）

## 错误处理
- [x] Checkpoint 28: 无效端口号被前端和后端双重校验拒绝
- [x] Checkpoint 29: 空的服务器地址被拒绝
- [x] Checkpoint 30: MQTT 连接超时或失败有清晰的错误提示
- [x] Checkpoint 31: API 异常时返回结构化错误响应

## 集成验证
- [x] Checkpoint 32: 应用启动时自动加载配置文件
- [x] Checkpoint 33: 修改配置后无需重启即可生效（热加载）
- [x] Checkpoint 34: 完整流程：启动→配置→连接→开门 能正常工作
