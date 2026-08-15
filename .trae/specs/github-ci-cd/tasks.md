# Door Clicker - GitHub Actions CI/CD Implementation Plan

## [x] Task 1: 创建 Web CI 工作流（Python/Flask）
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 创建 `.github/workflows/web-ci.yml`
  - 触发条件：push 到 main、pull_request 到 main
  - 使用 ubuntu-latest runner
  - Step 1: Checkout 代码
  - Step 2: 设置 Python 3.x 环境
  - Step 3: 安装依赖 `pip install -r door-clicker-web/requirements.txt`
  - Step 4: 代码风格检查 `flake8 door-clicker-web/`（排除 test 文件和 migrations）
  - Step 5: 运行单元测试 `python -m unittest discover -s door-clicker-web -p "*_test.py"`
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-1.1: 工作流 YAML 语法正确，GitHub Actions 能解析
  - `programmatic` TR-1.2: Push 到 main 分支能触发工作流
  - `programmatic` TR-1.3: 单元测试在 CI 环境全部通过
  - `programmatic` TR-1.4: flake8 检查不报错（或仅有可接受的警告）
- **Notes**: flake8 配置可以在项目根目录添加 `.flake8` 文件定义规则

## [x] Task 2: 创建 Firmware CI 工作流（PlatformIO/ESP8266）
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 创建 `.github/workflows/firmware-ci.yml`
  - 触发条件：push 到 main、pull_request 到 main
  - 使用 ubuntu-latest runner
  - Step 1: Checkout 代码（含子模块）
  - Step 2: 安装 PlatformIO CLI `pip install platformio`
  - Step 3: 进入 door-clicker-firmware 目录
  - Step 4: 执行编译 `pio run`（验证编译通过）
- **Acceptance Criteria Addressed**: AC-1, AC-4
- **Test Requirements**:
  - `programmatic` TR-2.1: 工作流 YAML 语法正确
  - `programmatic` TR-2.2: PlatformIO 在 CI 环境能成功编译固件
  - `programmatic` TR-2.3: 编译产物（.bin 文件）存在
- **Notes**: PlatformIO 首次运行会下载工具链，CI 时间较长（约 5-10 分钟）。可使用 cache 加速。

## [x] Task 3: 在 README.md 添加构建状态徽章
- **Priority**: medium
- **Depends On**: Task 1, Task 2
- **Description**:
  - 在 README.md 顶部添加 GitHub Actions 构建状态徽章
  - 为 web-ci 和 firmware-ci 分别添加徽章
  - 徽章链接指向仓库的 Actions 页面
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-3.1: README.md 中包含两个徽章图片链接
  - `human-judgement` TR-3.2: 徽章在 GitHub 页面正确渲染，可点击跳转

## [x] Task 4: 添加 flake8 配置文件
- **Priority**: medium
- **Depends On**: Task 1
- **Description**:
  - 在项目根目录创建 `.flake8` 配置文件
  - 设置合理的规则：max-line-length=120，排除 tests、migrations 等
  - 确保现有代码能通过 flake8 检查
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: `flake8 door-clicker-web/` 命令执行不报错（退出码 0）
  - `programmatic` TR-4.2: flake8 配置文件存在且格式正确
- **Notes**: 如果现有代码有风格问题，可选择放宽规则而非大量修改代码

## [x] Task 5: 创建 CI 状态检查的 PR 分支保护规则
- **Priority**: low
- **Depends On**: Task 1, Task 2
- **Description**:
  - 在项目根目录创建 `.github/CODEOWNERS` 或说明文档（可选）
  - 配置 PR 需要通过 CI 才能合并（需要在 GitHub 仓库设置中手动开启 branch protection）
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `human-judgement` TR-5.1: PR 页面正确显示 CI 状态（成功/失败）
  - `human-judgement` TR-5.2: CI 失败时 commit 显示红色 X 标记
- **Notes**: 分支保护需要仓库管理员在 GitHub Settings > Branches 中手动配置
