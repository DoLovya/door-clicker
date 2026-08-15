# Door Clicker - GitHub Actions CI/CD Product Requirement Document

## Overview
- **Summary**: 为 Door Clicker 项目的前后端组件（door-clicker-web Python/Flask 和 door-clicker-firmware PlatformIO/ESP8266）搭建 GitHub Actions CI/CD 流水线，实现代码质量检查、自动化测试和构建验证。
- **Purpose**: 当前项目缺乏自动化 CI/CD 流程，每次代码变更都需要手动验证。搭建 CI/CD 后，每次 Push 或 Pull Request 时自动执行 Lint 检查、单元测试和构建验证，确保代码质量，减少回归问题。
- **Target Users**: 项目开发者（个人或团队），在提交代码前希望自动验证代码质量和构建正确性。

## Goals
- 为 door-clicker-web（Python/Flask）搭建 CI 流程：代码风格检查 + 单元测试
- 为 door-clicker-firmware（PlatformIO/ESP8266）搭建 CI 流程：编译构建验证
- 触发时机：Push 到 main 分支、Pull Request 到 main 分支
- 构建状态徽章（Build Badge）显示在 README 中

## Non-Goals (Out of Scope)
- 不包含生产环境自动部署（CD 部分）
- 不包含固件 OTA 自动烧录到物理设备
- 不包含 Docker 镜像构建
- 不包含多环境（staging/production）部署
- 不包含代码覆盖率报告（仅验证测试能通过）

## Background & Context
- **项目结构**:
  - `door-clicker-web/` — Python 3 + Flask Web 应用，使用 unittest 框架
  - `door-clicker-firmware/` — PlatformIO + Arduino 框架的 ESP8266 固件
- **现有测试**:
  - door-clicker-web 已有多个 `*_test.py` 文件（app_test.py、config_manager_test.py 等），使用标准库 unittest
  - door-clicker-firmware 暂无自动化测试
- **依赖管理**:
  - web: `requirements.txt`（flask、paho-mqtt 等）
  - firmware: `platformio.ini`（PubSubClient、ArduinoJson 等）

## Functional Requirements
- **FR-1**: Push/PR 到 main 分支时自动触发 CI 流水线
- **FR-2**: Web CI 流程安装 Python 依赖、执行代码风格检查（flake8）、运行所有单元测试
- **FR-3**: Firmware CI 流程安装 PlatformIO CLI、执行编译构建验证（pio run）
- **FR-4**: CI 失败时在 GitHub 上标记 commit 为 red，成功为 green
- **FR-5**: README.md 中包含构建状态徽章

## Non-Functional Requirements
- **NFR-1**: CI 执行时间 < 5 分钟（Web），< 10 分钟（Firmware）
- **NFR-2**: 使用 GitHub 官方 runner（ubuntu-latest），无需自托管
- **NFR-3**: CI 配置文件放在 `.github/workflows/` 目录下
- **NFR-4**: 不硬编码任何密钥或敏感信息

## Constraints
- **Technical**:
  - Web CI: Python 3.x（与项目兼容），flake8，unittest
  - Firmware CI: PlatformIO CLI，platformio.ini
- **Business**: 个人项目，无需付费服务，使用 GitHub Actions 免费额度
- **Dependencies**: 依赖 GitHub Actions 服务可用性

## Assumptions
- GitHub Actions 免费额度对该项目足够（个人仓库每月 2000 分钟）
- PlatformIO 编译在 GitHub Actions runner 上能正常完成
- Web 单元测试能在无 MQTT Broker 的环境下通过（使用 mock）

## Acceptance Criteria

### AC-1: Web CI 流水线触发
- **Given**: 用户 Push 代码到 main 分支或发起 PR 到 main 分支
- **When**: GitHub Actions 检测到事件
- **Then**: door-clicker-web CI 流水线自动开始执行
- **Verification**: `programmatic`

### AC-2: Web 依赖安装成功
- **Given**: CI 流水线已触发
- **When**: 执行 pip install -r requirements.txt
- **Then**: 所有依赖正确安装，步骤不报错
- **Verification**: `programmatic`

### AC-3: Web 单元测试通过
- **Given**: 依赖已安装
- **When**: 执行所有 *_test.py 文件
- **Then**: 所有单元测试通过，无失败
- **Verification**: `programmatic`

### AC-4: Firmware 编译构建成功
- **Given**: CI 流水线已触发
- **When**: 执行 pio run 编译
- **Then**: 编译成功生成固件，无编译错误
- **Verification**: `programmatic`

### AC-5: CI 状态徽章
- **Given**: CI 流程已配置
- **When**: 查看 README.md
- **Then**: 包含 GitHub Actions 构建状态徽章，点击可跳转到 Actions 页面
- **Verification**: `programmatic`

### AC-6: 失败时正确标记
- **Given**: 代码提交有错误（测试失败或编译失败）
- **When**: CI 流水线执行
- **Then**: GitHub commit 状态标记为 failure，在 PR 中显示红色 X
- **Verification**: `human-judgment`

## Open Questions
- [ ] 是否需要为 web 增加 flake8 之外的代码覆盖率检查？
- [ ] 是否需要矩阵构建（多 Python 版本、多 PlatformIO 平台）？
- [ ] Firmware 编译产物是否需要作为 artifact 上传？
