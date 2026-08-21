## 1. 依赖与配置准备

- [ ] 1.1 在 `door-clicker-web/requirements.txt` 追加 `gunicorn` 与 `eventlet`（容器内生产运行所需）
- [ ] 1.2 创建 `deploy/mosquitto/mosquitto.conf`，默认配置允许本地匿名连接 + 持久化数据

## 2. door-clicker-web 镜像构建文件

- [ ] 2.1 创建 `door-clicker-web/.dockerignore`，排除 venv/、data/logs/、__pycache__/、.git/、.trae/、openspec/、tests/、deploy/ 等
- [ ] 2.2 创建 `door-clicker-web/Dockerfile`：采用多阶段构建（builder + final），基础镜像 `python:3.12-slim-bookworm`；先 COPY requirements.txt 做分层缓存，再 COPY 源码；创建 `app` 非 root 用户；`EXPOSE 5000`；`WORKDIR /app/src`；`CMD` 用 `gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 app:app`
- [ ] 2.3 执行 `docker build -t door-clicker-web:latest ./door-clicker-web` 验证可构建，并检查镜像 SIZE ≤ 300MB、Python 版本为 3.12.x、`pip list` 仅包含项目依赖

## 3. Compose 编排与默认配置

- [ ] 3.1 创建项目根目录 `docker-compose.yml`：定义两个 service `mosquitto`（`eclipse-mosquitto:2`）和 `web`（`build: ./door-clicker-web`）；声明依赖；默认 `restart: unless-stopped`；`web` 加 `mem_limit: 256m`
- [ ] 3.2 在 compose 中配置 mosquitto 的三个挂载：`mosquitto.conf:ro`、`mosquitto-data` 命名 volume、`mosquitto-log` 命名 volume；发布端口 `1883`（可由环境变量 `MQTT_PORT` 覆盖）
- [ ] 3.3 在 compose 中配置 web 的挂载：`door-clicker-web/data:/app/data` 持久化（bind mount）；发布端口 `5000`（可由环境变量 `WEB_PORT` 覆盖）；`depends_on: mosquitto`
- [ ] 3.4 创建项目根 `.env.example`，列出 `WEB_PORT=5000`、`MQTT_PORT=1883`、`ENV=production`、`FLASK_ENV=production` 等变量并配注释；`.env` 加入 `.gitignore`（如未加入）

## 4. 本地开发模式支持（混合 + 全容器）

- [ ] 4.1 在 `docker-compose.yml` 中为 `web` 服务支持开发模式：当 `ENV=development` 时，bind mount `door-clicker-web/src:/app/src:ro`；`command` 覆盖为 `python app.py`；环境变量里加 `FLASK_ENV=development`、`PYTHONUNBUFFERED=1`
- [ ] 4.2 增加可选 `DEBUGPY` 支持：当 `DEBUGPY=1` 时通过 compose override 暴露 `5678` 端口并把 `command` 切到 `python -m debugpy --listen 0.0.0.0:5678 app.py`（不强制，给 comment + compose.dev.yml 片段即可）
- [ ] 4.3 验证混合模式：`docker compose up -d mosquitto` 后，本地 venv 里 `cd src && FLASK_ENV=development python app.py` 能连上 `127.0.0.1:1883`，无报错

## 5. 端到端验证

- [ ] 5.1 **栈启动验证**：干净环境下 `docker compose up -d`，3 分钟内 `docker compose ps` 显示 2 个服务 Up，`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/login` 返回 200
- [ ] 5.2 **MQTT 连通验证**：用 `mosquitto_sub/pub` 或 `paho` 客户端连 `127.0.0.1:1883`，向 `door/DEVICE_ID` 发消息，web 容器日志出现接收记录
- [ ] 5.3 **持久化验证**：编辑宿主机 `door-clicker-web/data/config.json` 改 `adminUser`，`docker compose restart web` 后访问登录页显示新用户名；`docker compose down && up -d` 后 `data/logs/` 旧日志仍然存在
- [ ] 5.4 **开发热重载验证**：开发模式下改 `src/app.py` 一段可观察返回（如首页 title），3 秒内刷新页面看到更新
- [ ] 5.5 **构建缓存验证**：`touch src/app.py` 后 re-build，`pip install` 层输出 "Using cache"

## 6. 文档（可选增强，如 README 已存在则更新）

- [ ] 6.1 在 `door-clicker-web/README.md` 末尾新增「Docker 部署」章节，列出三种运行模式的完整命令：生产一键部署、全容器开发、混合开发（Broker in Docker + Flask in venv），附对比表
- [ ] 6.2 补充 `.env.example` 中 `MQTT_USERNAME` / `MQTT_PASSWORD` 的用法，说明如何关闭 Mosquitto 匿名模式以用于公网部署
