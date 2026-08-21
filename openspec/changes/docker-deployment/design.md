## Context

当前 door-clicker 项目有两种运行模式：
1. **本地开发**：开发者在 macOS/Linux 本地创建 venv，`pip install -r requirements.txt` 后 `cd src && python app.py`；MQTT Broker 要么本地 brew/apt 装 Mosquitto，要么连接公网 Broker。
2. **服务器部署**：通过 `deploy/setup.sh` + `deploy/deploy.sh` 在 Linux 服务器上创建 `/opt/door-clicker` 目录、建立 venv、拷贝源码、配置 systemd 服务。

存在的痛点：
- 本地开发时 MQTT Broker 的安装和配置没有自动化，不同开发者机器状态不一致；
- 服务器部署强依赖宿主机 Python 版本（3.8/3.10/3.12 的 Flask/SocketIO 版本兼容）和是否已有 `python3-venv`、`python3-dev` 等系统包；
- 「我这能跑服务器挂了」排查成本高。

新增 Docker 部署要和以上两种模式**同时兼容**，不能破坏现有脚本。

## Goals / Non-Goals

**Goals:**
- 用户在一台只装了 Docker Engine + Compose v2 的干净机器上，克隆仓库后一条命令即可把完整栈跑起来（Web + MQTT Broker）。
- 提供本地混合开发模式：MQTT Broker 用 Docker 跑，Flask 用 venv 直接跑（保留热重载 + IDE 断点）。
- 应用镜像体积最小化（单镜像最终 < 300MB，理想 < 200MB）。
- `data/config.json`、`data/logs/`、Mosquitto 数据目录以 volume 形式持久化，容器销毁不丢数据。
- 容器之间通过 compose 内 DNS 通讯（Flask 连 `mosquitto:1883`），不需要写宿主机 IP。
- 容器内以非 root 用户运行 Web 进程，降低安全风险。
- 构建依赖**分层缓存**：COPY requirements.txt 放在 COPY 源码之前，依赖不变时 build 直接命中缓存。

**Non-Goals:**
- 不在本次变更内引入 K8s、Helm 或 Swarm；仅 Docker Compose。
- 不在本次变更内配置 TLS/HTTPS 反向代理（nginx/caddy），Web 直接暴露 5000 端口，TLS 留给后续变更。
- 不在本次变更内推送镜像到公共/私有仓库。
- 不修改现有 deploy.sh / setup.sh / systemd service 文件（保持向后兼容）。
- 不修改 door-clicker-firmware 的任何代码和构建。

## Decisions

### D1: 基础镜像选择 — `python:3.12-slim-bookworm`

**为什么不是 Alpine？** Alpine 用 musl libc，`paho-mqtt`、`flask_socketio`、`eventlet`/`gevent` 这些包偶尔有 musl 兼容坑；且 Alpine 的 pip wheel 缺失时会走源码编译，拖慢构建。slim 版 Debian 稳定、镜像体积（~130MB）和 Alpine（~80MB）差距不大，换体积优势的收益远低于稳定性收益。

**为什么固定 3.12 而不是 latest？** 确保任何机器、任何 CI 构建出来的镜像 Python 版本完全一致，消除行为差异。

### D2: 多阶段构建（builder + final）

**Stage 1 (builder)**：安装 gcc / rustc / python3-dev 等编译工具，`pip install --prefix=/install -r requirements.txt`，把 site-packages 安装到独立目录。
**Stage 2 (final)**：只 COPY `/install`、源码，和运行时必需的系统包（`libpq5` 一类）。丢掉构建工具，镜像从 ~500MB 降到 ~200MB 以内。

### D3: 非 root 用户

final 阶段 `groupadd -r app && useradd -r -g app app`，`WORKDIR /app` 属主改 `app:app`，最后 `USER app`。降低 CVE 利用时的提权面。

### D4: 启动命令 — 不依赖 Flask dev server 生产化

`CMD ["python", "-m", "gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]`

- `eventlet` worker 是 `flask_socketio` 的推荐 async mode，WebSocket 才能正常工作；
- `-w 1`（单 worker）是 Flask-SocketIO 多进程时的限制 —— 多 worker 需要额外的消息队列做广播同步，目前业务量完全不需要，单进程即可；
- requirements.txt 里需要新增 `gunicorn` 和 `eventlet` 两个依赖。

但**本地开发挂载源码时**，通过 compose 的 `command` override 回 `python app.py`（FLASK_ENV=development，debug 模式自动 reload + 热替换）。

### D5: Compose 服务拆分与网络

```
services:
  mosquitto:    image: eclipse-mosquitto:2, network internal + published 1883
  web:          build: ./door-clicker-web, depends_on mosquitto, published 5000
```

- 两个服务用默认 compose bridge 网络，Flask 访问 MQTT 用 hostname `mosquitto`（容器 DNS 解析）。
- `mosquitto` 挂载三个路径：
  - `./deploy/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro`
  - `mosquitto-data:/mosquitto/data`（命名 volume，持久化消息）
  - `mosquitto-log:/mosquitto/log`（命名 volume，持久化日志）
- `web` 挂载两个 bind mount（开发模式）：
  - `./door-clicker-web/src:/app/src:ro`（源码 read-only 挂载，宿主机修改即时生效）
  - `./door-clicker-web/data:/app/data`（config.json 读写，日志落盘）
- 生产模式只用命名 volume，不用源码挂载。

**开发 vs 生产模式切换**：用 compose `profiles` 或者 `COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml`。为了简单本次直接在一个 compose 里用环境变量 `ENV=development|production` + `command` override 控制，不拆两个文件。

### D6: MQTT 默认配置的安全分级

Mosquitto 默认配置分两档：
1. **本地开发默认值**：`listener 1883 0.0.0.0`，`allow_anonymous true` —— 配合 config_manager 的默认 `mqttUsername=""` `mqttPassword=""` 零配置即可跑。
2. **生产**：用户自行修改 `mosquitto.conf` 增加 `password_file`，关闭 `allow_anonymous`，或在 compose 里只暴露 1883 到内网，不暴露公网。

这部分只提供默认开发配置，**不**自动生成生产密码文件（避免密码泄露）。

### D7: .dockerignore

排除：
```
venv/
data/*.log
data/logs/
__pycache__/
*.pyc
.git/
.trae/
openspec/
tests/
deploy/
```

加快 build context 上传速度，避免 venv 里的东西污染镜像。

## Risks / Trade-offs

- **[风险] Flask-SocketIO + gunicorn eventlet worker 在极个别高并发场景下偶发消息没收到** → Mitigation：当前是个人/家庭场景，并发 < 10，且 `door-clicker-web` 本身就是轻量面板；如果真遇到就加 `-k gevent` 或换成 uWSGI，配置可后续 override。
- **[风险] bind mount `src` 在 macOS（Docker Desktop）上文件系统事件较慢，热 reload 可能延迟 1-3s** → Mitigation：开发模式可以退回到「Broker 用 Docker、Flask 用本地 venv 直接跑」的混合模式，绕开 bind mount 延迟；对用户来说命令就是 `docker compose up -d mosquitto`，不启动 web 容器即可。
- **[风险] Docker Desktop 默认开启了 `Use Compose V2`，但如果是非常老的 Linux 宿主机可能只有 `docker-compose`（Python 版 v1）** → Mitigation：文档里同时写明两种命令（`docker compose` 优先，`docker-compose` 备选）；要求是 Compose v2，但脚本里不加硬校验。
- **[风险] requirements.txt 增加 gunicorn + eventlet 后，venv 本地跑的用户如果不重新 pip install，不会装这两个包** → Mitigation：gunicorn/eventlet 只在 Docker 镜像里用（Dockerfile 里 RUN pip install 时会一起装），本地 venv 跑 `python app.py` 用的是 Flask dev server，不依赖它们。没有影响。
- **[权衡] 容器启动时 Web 进程默认等 MQTT Broker，但不做健康检查硬依赖** → compose 的 `depends_on` 只保证启动顺序，不保证 ready。在 app.py 的 MQTT client 启动逻辑里已经有 `connect_async` + 自动重连（见 `mqtt_client_manager.py`），Broker 慢几秒启动不影响，会自动连上。不需要在 entrypoint 加 `nc -z` 等待逻辑，减少复杂度。

## Migration Plan

- **零停机部署路径**：现有 systemd 部署可以共存，只是多了 Docker 部署选项。切换到 Docker：停掉 `systemctl stop door-clicker-web`，然后 `docker compose up -d`，旧的 systemd 服务保留不删。
- **配置迁移**：把宿主机已有 `/opt/door-clicker/door-clicker-web/data/config.json` 拷贝到 `./door-clicker-web/data/config.json`（bind mount 路径）即可，JSON 格式完全兼容，不需要重新生成密码 hash。
- **回滚**：`docker compose down`，再 `systemctl start door-clicker-web` 即可切回 systemd 方案。

## Open Questions

- （待用户确认）是否本次就把 `gunicorn` 和 `eventlet` 加入到 `requirements.txt`？还是只在 Dockerfile 里单独 `pip install`（避免污染 requirements.txt 给那些只跑 dev server 的用户）？—— 建议前者，一行依赖，没有副作用。
- （待用户确认）是否需要一个 `docker-compose.prod.yml` 来覆盖生产模式（去掉 bind mount、加 `restart: always`、限制 `mem_limit=256m`）？—— 建议本次加，否则用户部署时还得手动改 compose。
