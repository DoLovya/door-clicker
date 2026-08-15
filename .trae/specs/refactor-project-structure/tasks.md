# Door Clicker Web - 项目结构重构实施计划

## [x] Task 1: 创建新目录结构
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 在 `door-clicker-web/` 下创建 `src/`、`tests/`、`data/` 目录
  - 创建 `src/__init__.py` 和 `tests/__init__.py`
  - 移动 `templates/` 到 `src/templates/`
  - 移动 `config.example.json` 到 `data/`
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: `src/`, `tests/`, `data/` 目录存在 ✅
  - `programmatic` TR-1.2: `src/__init__.py` 和 `tests/__init__.py` 存在 ✅
  - `programmatic` TR-1.3: `src/templates/` 包含所有 HTML 文件 ✅
  - `programmatic` TR-1.4: `data/config.example.json` 存在 ✅

## [x] Task 2: 迁移源代码到 src/ 目录
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 移动 `app.py`, `auth.py`, `config_manager.py`, `log_manager.py`, `mqtt_client_manager.py` 到 `src/`
  - 移动 `mqtt_command_publisher.py`, `mqtt_command_subscriber.py` 到 `src/`
  - 保持文件内容不变
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: 所有源文件在 `src/` 目录下 ✅
  - `programmatic` TR-2.2: 原位置的源文件已删除 ✅

## [x] Task 3: 更新路径配置
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 修改 `config_manager.py`: 配置路径改为 `../data/config.json`（相对于 src 目录）
  - 修改 `log_manager.py`: 日志目录改为 `../data/logs/`
  - 修改 `app.py`: Flask 模板路径指向 `templates/`（因 app.py 在 src/ 下，templates 相对路径正确）
- **Acceptance Criteria Addressed**: AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-3.1: `config_manager.py` 中配置路径指向 `data/config.json` ✅
  - `programmatic` TR-3.2: `log_manager.py` 中日志目录指向 `data/logs/` ✅
  - `programmatic` TR-3.3: `app.py` 中模板路径指向 `src/templates/` ✅

## [x] Task 4: 创建启动入口 run.py
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - 在 `door-clicker-web/` 根目录创建 `run.py`
  - 设置 `sys.path` 包含 `src/`
  - 从 `src.app` 导入 app 并启动
  - 自动创建 `data/` 和 `data/logs/` 目录
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-4.1: `python run.py` 可成功启动服务 ✅
  - `programmatic` TR-4.2: 自动创建必要的目录 ✅

## [x] Task 5: 迁移测试代码到 tests/ 目录
- **Priority**: high
- **Depends On**: Task 2, Task 3
- **Description**:
  - 移动所有 `*_test.py` 文件到 `tests/`
  - 更新测试文件中的导入路径（通过 sys.path.insert 添加 src/）
  - 测试文件通过 `sys.path.insert(0, ...)` 找到 `src/` 模块
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-5.1: 所有测试文件在 `tests/` 下 ✅
  - `programmatic` TR-5.2: 测试中的导入路径正确 ✅
  - `programmatic` TR-5.3: 每个测试文件可独立运行 ✅

## [x] Task 6: 更新 .gitignore
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 添加 `door-clicker-web/data/config.json`
  - 添加 `door-clicker-web/data/logs/`
  - 添加 `door-clicker-web/data/*.log`
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `programmatic` TR-6.1: `.gitignore` 包含 `data/config.json` 规则 ✅
  - `programmatic` TR-6.2: `.gitignore` 包含 `data/logs/` 规则 ✅
  - `programmatic` TR-6.3: `git status` 显示敏感文件被排除 ✅

## [x] Task 7: 更新 CI/CD 配置
- **Priority**: medium
- **Depends On**: Task 5
- **Description**:
  - 更新 `.github/workflows/web-ci.yml` 中的 flake8 路径为 `door-clicker-web/src/`
  - 更新 unittest discover 路径为 `door-clicker-web/tests`
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic` TR-7.1: CI 配置中测试路径指向 `tests/` ✅
  - `programmatic` TR-7.2: CI 配置中 flake8 包含 `src/` 目录 ✅

## [x] Task 8: 运行完整测试验证
- **Priority**: high
- **Depends On**: Task 1-7
- **Description**:
  - 运行所有单元测试
  - 验证应用启动和 API 功能
  - 验证配置文件读写
  - 验证日志写入
  - 验证模板渲染
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-4, AC-5, AC-8
- **Test Requirements**:
  - `programmatic` TR-8.1: 所有单元测试通过 (87/87) ✅
  - `programmatic` TR-8.2: `python run.py` 启动成功 ✅
  - `programmatic` TR-8.3: API 接口功能正常 ✅
  - `human-judgment` TR-8.4: 页面渲染正确 ✅
