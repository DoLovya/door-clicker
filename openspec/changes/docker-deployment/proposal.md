## Why

当前部署流程依赖手动创建虚拟环境、安装系统依赖、配置 systemd 服务，新手部署门槛高，且容易出现「本地能跑、服务器挂了」的环境不一致问题（如 pip 与 python 解释器不配对、Python 版本差异）。项目需要一种零环境依赖、一条命令即可跑起来的部署方案，同时保留本地开发时的热重载和断点调试能力。

## What Changes

- 新增 `door-clicker-web/Dockerfile`：基于 `python:3.12-slim` 的多阶段构建，产物镜像包含 Flask 应用及全部依赖。
- 新增 `docker-compose.yml`（项目根目录）：定义两个服务 `door-clicker-web` 和 `mosquitto`（Eclipse Mosquitto MQTT Broker），容器间通过 compose 网络通信。
- 新增 `deploy/mosquitto/mosquitto.conf`：Mosquitto Broker 的默认配置文件，允许匿名+密码两种模式，持久化挂载。
- 新增 `.dockerignore`：排除 venv、data、logs、__pycache__、.git 等非必要文件进入镜像。
- 不修改现有 `deploy.sh` / `setup.sh` / systemd 部署方式，与 Docker 方案同时保留。
- 非破坏性变更（无 BREAKING）。

## Capabilities

### New Capabilities
- `docker-image-build`: door-clicker-web 的 Docker 镜像构建规范（Python 版本固定、依赖分层缓存、非 root 用户启动、暴露端口）。
- `docker-compose-stack`: door-clicker-web + Mosquitto Broker 的容器编排能力，包含一键启动/停止、数据卷持久化、端口映射、本地开发时的源码挂载与热重载。
- `docker-local-dev-workflow`: 本地混合开发模式的约定（Mosquitto 用 Docker 跑、Flask 用 venv 直接跑 + 断点调试）。

### Modified Capabilities
- （无）现有部署脚本和运行时代码逻辑不修改。

## Impact

- **新增依赖**：构建和部署环境需要安装 Docker Engine 与 Docker Compose v2（`docker compose` CLI）。
- **新增文件**：
  - `door-clicker-web/Dockerfile`
  - `door-clicker-web/.dockerignore`
  - `docker-compose.yml`（项目根）
  - `deploy/mosquitto/mosquitto.conf`
- **端口占用约定**：默认暴露主机 `5000/tcp`（Web UI / API / WebSocket）与 `1883/tcp`（MQTT），可通过 compose override 或环境变量修改。
- **数据持久化**：`door-clicker-web/data/`（config.json + logs）与 `deploy/mosquitto/data/` 均以命名 volume 或 bind mount 形式挂载到宿主机，容器销毁不丢数据。
- **CI**：可在后续变更中新增 `docker build` 缓存加速步骤与镜像推送到私有仓库，但不在本次变更范围。
