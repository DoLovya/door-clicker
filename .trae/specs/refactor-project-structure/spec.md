# Door Clicker Web - 项目结构重构 PRD

## Overview
- **Summary**: 对 `door-clicker-web` 项目进行结构重构，采用 src/test 分级目录结构，将源代码、测试代码、配置文件、运行时数据（日志）进行清晰分离
- **Purpose**: 解决当前项目文件扁平分布问题，方便后续维护、CI/CD、版本管理，保护敏感配置信息不被误提交
- **Target Users**: 项目开发者、维护者

## Goals
- 建立清晰的 src/test/data 目录分级结构
- 将源代码迁移到 `src/` 目录
- 将测试代码迁移到 `tests/` 目录
- 将配置文件迁移到 `data/` 目录（集中管理运行时数据）
- 保持应用功能完全正常（零功能变更）
- 保持现有测试全部通过

## Non-Goals (Out of Scope)
- 不修改任何业务逻辑或功能
- 不修改 API 接口
- 不修改前端页面
- 不修改固件代码
- 不引入新的依赖或框架

## Background & Context
- 当前所有文件扁平分布在 `door-clicker-web/` 根目录下
- 配置文件 `config.json` 和日志文件 `logs/` 与源代码混在一起
- 测试文件 (`*_test.py`) 与源代码并列
- `config_manager.py` 中配置路径硬编码为 `os.path.dirname(__file__) + "/config.json"`
- `log_manager.py` 中日志路径硬编码为 `os.path.dirname(__file__) + "/logs"`
- Flask 的模板路径 `templates/` 与代码目录绑定

## Functional Requirements

### FR-1: 源代码目录结构
- 在 `door-clicker-web/src/` 下存放所有 Python 源模块
- 包括: `app.py`, `auth.py`, `config_manager.py`, `log_manager.py`, `mqtt_client_manager.py`
- 包括: `templates/` 模板目录

### FR-2: 测试代码目录结构
- 在 `door-clicker-web/tests/` 下存放所有测试文件
- 包括: `app_test.py`, `config_manager_test.py`, `error_handling_test.py`, `integration_test.py`, `mqtt_client_manager_test.py`
- 添加 `__init__.py` 支持测试发现

### FR-3: 配置与数据目录
- 在 `door-clicker-web/data/` 下存放运行时数据
- `data/config.json` - 运行时配置文件（被 .gitignore 排除）
- `data/config.example.json` - 配置模板（提交到 Git）
- `data/logs/` - 日志目录（被 .gitignore 排除）

### FR-4: 启动入口
- 在 `door-clicker-web/` 根目录创建 `run.py` 作为统一启动入口
- 运行 `python run.py` 即可启动服务

### FR-5: 路径配置更新
- `ConfigManager` 的默认配置路径改为 `data/config.json`
- `LogManager` 的日志目录改为 `data/logs/`
- Flask 模板路径指向 `src/templates/`
- 所有路径使用相对项目根目录的路径

### FR-6: 导入路径更新
- 源代码内部模块导入保持不变（同目录互相导入）
- 测试代码导入路径更新为 `from src.xxx import`
- `sys.path` 设置正确以便测试运行

### FR-7: .gitignore 更新
- 排除 `data/config.json`
- 排除 `data/logs/` 目录
- 排除 `data/*.log` 文件

### FR-8: CI/CD 适配
- 更新 GitHub Actions 工作流中的测试命令
- 更新 flake8 配置排除路径

### FR-9: 向后兼容
- 保留根目录下的 `config.example.json` 的引用（README 文档）
- 提供清晰的迁移说明

## Non-Functional Requirements

### NFR-1: 零功能影响
- 重构后所有 API 行为保持不变
- 前后端交互完全兼容
- 数据库/配置文件格式不变

### NFR-2: 测试全部通过
- 所有现有单元测试和集成测试必须通过
- 测试覆盖率不降低

### NFR-3: 启动命令简洁
- 只需 `python run.py` 即可启动服务
- 配置文件和日志路径自动创建

## Constraints
- **Technical**: Python 3.x, Flask, 不能修改业务逻辑
- **Dependencies**: 现有依赖不变 (flask, paho-mqtt 等)
- **Testing**: unittest 框架，不能迁移到 pytest

## Assumptions
- 用户接受新的目录结构
- 配置文件路径变更后，前端无需修改（因为是通过 API 读写）
- 日志查看 API 无需修改
- 现有部署方式可通过修改启动脚本来适配

## Target Directory Structure

```
door-clicker-web/
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── config_manager.py
│   ├── log_manager.py
│   ├── mqtt_client_manager.py
│   └── templates/
│       ├── door.html
│       ├── index.html
│       └── login.html
├── tests/
│   ├── __init__.py
│   ├── app_test.py
│   ├── config_manager_test.py
│   ├── error_handling_test.py
│   ├── integration_test.py
│   └── mqtt_client_manager_test.py
├── data/
│   ├── config.example.json
│   ├── config.json          # (gitignore)
│   └── logs/               # (gitignore)
├── run.py
├── requirements.txt
├── .flake8
└── README.md
```

## Acceptance Criteria

### AC-1: 目录结构正确
- **Given**: 项目已完成重构
- **When**: 检查 `door-clicker-web/` 目录
- **Then**: 源代码在 `src/`、测试在 `tests/`、数据在 `data/`、启动入口在根目录
- **Verification**: `programmatic`

### AC-2: 应用可正常启动
- **Given**: 配置文件 `data/config.json` 存在或可自动创建
- **When**: 运行 `python run.py`
- **Then**: 服务在端口 8080 启动，访问 `http://localhost:8080` 返回 200
- **Verification**: `programmatic`

### AC-3: 所有测试通过
- **Given**: 测试环境已配置
- **When**: 运行 `python -m pytest door-clicker-web/tests/` 或 `python -m unittest discover`
- **Then**: 所有测试通过，无失败
- **Verification**: `programmatic`

### AC-4: 配置文件正确读写
- **Given**: 前端页面提交配置
- **When**: 调用 `PUT /api/config` 接口
- **Then**: 配置写入 `data/config.json`，重启后可正常读取
- **Verification**: `programmatic`

### AC-5: 日志正常写入
- **Given**: 系统正在运行
- **When**: 发送开门指令或其他操作
- **Then**: 日志写入 `data/logs/door_clicker.log`
- **Verification**: `programmatic`

### AC-6: Git 安全性
- **Given**: 新的目录结构
- **When**: 检查 `.gitignore`
- **Then**: `data/config.json` 和 `data/logs/` 被正确排除
- **Verification**: `programmatic`

### AC-7: CI/CD 正常
- **Given**: GitHub Actions 工作流
- **When**: 推送代码触发 CI
- **Then**: flake8 和 unittest 命令正确执行且通过
- **Verification**: `programmatic`

### AC-8: 模板渲染正常
- **Given**: Flask 应用已启动
- **When**: 访问 `/` 和 `/config` 页面
- **Then**: 正确渲染 `templates/door.html` 和 `templates/index.html`
- **Verification**: `human-judgment`
