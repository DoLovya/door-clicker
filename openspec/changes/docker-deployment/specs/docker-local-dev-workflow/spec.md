## ADDED Requirements

### Requirement: 支持仅启动 MQTT Broker
开发者 SHALL 能够仅通过 compose 启动 `mosquitto` 容器，而不启动 `web` 容器，以支持「Broker 走 Docker、Flask 走本地 venv」的混合开发模式。

#### Scenario: 单独启动 Mosquitto
- **WHEN** 用户在项目根执行 `docker compose up -d mosquitto`
- **THEN** 仅 `mosquitto` 容器 SHALL 为 `Up`，`web` 容器 SHALL 不存在
- **AND** 本地 venv 中的 Flask 进程连接 `127.0.0.1:1883` SHALL 握手成功

### Requirement: 开发模式下源码挂载 + 热重载
在开发模式（ENV=development 或 compose override）下，`web` 容器 SHALL 将宿主机 `door-clicker-web/src/` 以只读 bind mount 形式挂载到容器内对应路径，且 Flask 以 debug/reload 模式启动；用户在 IDE 里保存 `.py` 文件 SHALL 在 ≤ 3 秒内触发容器内进程自动重载。

#### Scenario: 修改 Python 源码后容器内自动 reload
- **WHEN** 用户在宿主机修改 `src/app.py` 中任意可观察行为（例如一个接口的返回文本）并保存
- **THEN** 在 3 秒内，容器内 stdout 日志 SHALL 出现 `* Detected change in '/app/src/app.py', reloading` 或等价的 reload 提示
- **AND** 重新访问该接口 SHALL 返回新内容

### Requirement: 开发模式允许 IDE 附加调试器
开发模式下 `web` 容器 SHALL 不使用 gunicorn/eventlet 启动，而是使用 Flask 内置 dev server，且端口映射 SHALL 允许 IDE（VS Code / PyCharm）attach 到容器内 Python 进程进行断点调试（至少支持 `debugpy` attach，端口可通过 compose 暴露）。

#### Scenario: debugpy attach 断点命中
- **WHEN** 用户在 compose 里打开 `DEBUGPY=1`，容器内启动时自动执行 `python -m debugpy --listen 0.0.0.0:5678 --wait-for-client app.py`（或等价方式）
- **THEN** IDE 连接 `<host>:5678` SHALL 成功 attach
- **AND** 设断点后访问路由 SHALL 正常命中断点

### Requirement: 两种开发模式的文档与命令约定
项目根 README 或等价说明 SHALL 清晰列出两种本地开发模式的完整命令与差异对比表：

| 模式 | Web 端运行位置 | MQTT Broker 运行位置 | 启动命令 | 热重载 | IDE 断点 |
|---|---|---|---|---|---|
| 混合模式（推荐默认） | 本地 venv | Docker Mosquitto | `docker compose up -d mosquitto` + `venv/bin/python src/app.py` | ✅ | ✅ |
| 全容器模式 | Docker web 容器 | Docker Mosquitto | `docker compose --profile dev up -d`（或 compose.dev 叠加）| ✅（bind mount）| 需 debugpy 端口 |

#### Scenario: 新开发者按 README 从零开始 ≤ 5 分钟跑起来
- **WHEN** 新开发者按 README 选择推荐的「混合模式」执行
- **THEN** 从克隆仓库到浏览器看到首页的整个流程 SHALL ≤ 5 分钟（带宽正常情况下）
