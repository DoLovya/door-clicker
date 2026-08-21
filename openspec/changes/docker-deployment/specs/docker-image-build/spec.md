## ADDED Requirements

### Requirement: 镜像可被干净构建且结果可重现
在任意安装了 Docker Engine ≥ 24 的机器上，对 `door-clicker-web/` 目录执行 `docker build` SHALL 产出一个可运行的 OCI 镜像，镜像内的 Python 大版本、依赖版本、启动命令在相同源码输入下完全一致。

#### Scenario: 本地机器执行 docker build
- **WHEN** 用户在项目根目录执行 `docker build -t door-clicker-web:latest ./door-clicker-web`
- **THEN** 构建 SHALL 在 5 分钟内成功（假设依赖下载带宽正常）
- **AND** 最终镜像 SIZE SHALL ≤ 300MB

#### Scenario: 依赖未变更时构建命中缓存
- **WHEN** 用户未修改 `requirements.txt`、仅修改 `src/` 下的 `.py` / `.html` / `.css` 文件后再次 build
- **THEN** 构建 SHALL 命中 `pip install` 之前的全部 layer 缓存
- **AND** 增量 build 时间 SHALL ≤ 30 秒

### Requirement: 镜像内固定 Python 版本与运行时基础
镜像内执行 `python3 --version` SHALL 返回主版本 `3.12`；镜像内的全部 Python 依赖 SHALL 来自 `requirements.txt`，不包含宿主机环境的遗留包。

#### Scenario: 容器启动后检查 Python 版本
- **WHEN** 对运行中的容器执行 `docker compose exec web python3 --version`
- **THEN** 输出 SHALL 为 `Python 3.12.x`

#### Scenario: 容器内不包含 venv 和宿主机污染
- **WHEN** `docker compose exec web pip list` 执行
- **THEN** 输出列表 SHALL 仅包含 `requirements.txt` 声明的依赖及其传递依赖
- **AND** 镜像内 SHALL 不存在 `/app/venv` 目录

### Requirement: 镜像以非 root 用户运行
容器内主进程 SHALL 以非 root、具备最少权限的系统用户启动，`whoami` 返回值不为 `root`。

#### Scenario: 容器主进程 uid 校验
- **WHEN** `docker compose exec web id -u` 执行
- **THEN** 返回值 SHALL ≥ 100（非 root uid）

### Requirement: 镜像暴露正确端口与工作目录
镜像 `EXPOSE` SHALL 声明 `5000/tcp`；`WORKDIR` SHALL 设为 `/app` 或等价路径以支持相对路径引用。

#### Scenario: inspect 镜像暴露端口
- **WHEN** `docker inspect door-clicker-web:latest --format '{{.Config.ExposedPorts}}'`
- **THEN** 输出 SHALL 包含 `5000/tcp`
