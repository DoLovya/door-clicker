## ADDED Requirements

### Requirement: 一条命令启动完整服务栈
在仅安装 Docker Engine + Compose v2 的干净 Linux / macOS / Windows 机器上克隆仓库后，`docker compose up -d` SHALL 同时启动 door-clicker-web 和 MQTT Broker（Mosquitto）两个容器，两者均进入 healthy/running 状态。

#### Scenario: 干净环境首次 docker compose up
- **WHEN** 用户克隆仓库后在根目录执行 `docker compose up -d`
- **THEN** 3 分钟内 `docker compose ps` 输出 SHALL 显示 `web` 与 `mosquitto` 两个服务状态均为 `Up`
- **AND** 浏览器访问 `http://<host>:5000` SHALL 返回登录页 HTTP 200
- **AND** MQTT 客户端连接 `<host>:1883` SHALL 握手成功

#### Scenario: docker compose down 完全清理
- **WHEN** 运行 `docker compose down`
- **THEN** 所有容器 SHALL 被删除
- **AND** `data/config.json` 与命名 volume 中的持久化数据 SHALL 保留（不受影响）

### Requirement: 容器间网络与 DNS 解析
Compose 默认网络内，`web` 容器 SHALL 能通过 hostname `mosquitto` 解析到 Broker 容器的 IP 并发起 TCP 连接。

#### Scenario: web 容器内 MQTT 连接 broker
- **WHEN** 在 `web` 容器中对 `mosquitto:1883` 发起 TCP 连接（由 `mqtt_client_manager.py` 触发）
- **THEN** MQTT CONNECT SHALL 在 5s 内成功
- **AND** 订阅发布消息在两端正常流通

### Requirement: Web 应用配置、数据、日志持久化
`door-clicker-web/data/` 下的 `config.json` 与 `logs/` SHALL 通过 volume 映射到宿主机，容器重启或销毁重建后，配置与历史日志 SHALL 保持不变。

#### Scenario: 修改 config.json 后容器重启不丢失
- **WHEN** 用户在宿主机编辑 `door-clicker-web/data/config.json` 写入新的 `adminUser`，执行 `docker compose restart web`
- **THEN** 容器重新启动后登录页 SHALL 使用新用户名生效
- **AND** 容器内 `/app/data/config.json` 内容与宿主机完全一致

#### Scenario: 容器销毁重建后日志保留
- **WHEN** 运行 `docker compose down && docker compose up -d`
- **THEN** `door-clicker-web/data/logs/` 下已有的日志文件 SHALL 仍然存在

### Requirement: Mosquitto 配置与数据持久化
Mosquitto Broker SHALL 支持通过宿主机挂载的 `mosquitto.conf` 配置；消息与日志 SHALL 落到命名 volume。

#### Scenario: 自定义 Mosquitto 配置生效
- **WHEN** 用户编辑 `deploy/mosquitto/mosquitto.conf` 修改端口或鉴权规则，执行 `docker compose restart mosquitto`
- **THEN** 新的配置 SHALL 生效（例如允许匿名 = false 时，匿名连接 SHALL 被拒绝）

### Requirement: 生产模式下的安全与重启策略
`web` 与 `mosquitto` 服务 SHALL 配置 `restart: unless-stopped`；`web` 服务 SHALL 配置合理的 `mem_limit` 以避免异常内存泄漏把宿主机拖挂。

#### Scenario: Docker 服务重启后容器自动恢复
- **WHEN** 宿主机执行 `sudo systemctl restart docker`（或重启机器）
- **THEN** 服务 SHALL 在 Docker 恢复后自动启动
- **AND** `docker compose ps` 输出 SHALL 再次显示两个服务 `Up`

### Requirement: 端口映射可通过环境变量覆盖
默认宿主机端口映射 `5000:5000` 与 `1883:1883` SHALL 允许通过 `.env` 文件或命令行环境变量覆盖，避免与宿主机已有服务冲突。

#### Scenario: 修改端口映射避免冲突
- **WHEN** 用户设置 `export WEB_PORT=8080 MQTT_PORT=11883` 后执行 `docker compose up -d`
- **THEN** `docker compose port web 5000` SHALL 返回 `0.0.0.0:8080`
- **AND** `docker compose port mosquitto 1883` SHALL 返回 `0.0.0.0:11883`
