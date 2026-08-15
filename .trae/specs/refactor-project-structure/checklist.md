# Door Clicker Web - 项目结构重构验证清单

## 目录结构验证
- [x] `src/` 目录存在且包含所有源代码文件
- [x] `tests/` 目录存在且包含所有测试文件
- [x] `data/` 目录存在
- [x] `src/__init__.py` 存在
- [x] `tests/__init__.py` 存在
- [x] `src/templates/` 包含 `door.html`, `index.html`, `login.html`
- [x] `data/config.example.json` 存在

## 路径配置验证
- [x] `config_manager.py` 中配置路径指向 `data/config.json`
- [x] `log_manager.py` 中日志目录指向 `data/logs/`
- [x] `app.py` 中模板路径指向 `src/templates/`
- [x] 路径使用相对路径，不硬编码绝对路径

## 启动入口验证
- [x] `run.py` 在项目根目录
- [x] `python run.py` 可成功启动服务
- [x] 自动创建 `data/` 目录
- [x] 自动创建 `data/logs/` 目录

## 测试验证
- [x] 所有单元测试通过 (87/87)
- [x] 集成测试通过
- [x] 错误处理测试通过
- [x] MQTT 客户端测试通过
- [x] 测试中的导入路径正确

## 功能验证
- [x] `GET /` 页面正常渲染（开门页, 200）
- [x] `GET /config` 页面跳转到登录页（302）
- [x] `GET /login` 页面正常渲染（登录页, 200）
- [x] `PUT /api/config` 可正常保存配置
- [x] `GET /api/config` 可正常读取配置
- [x] `POST /api/open/door` 可正常发送开门指令
- [x] `GET /api/logs` 可正常获取日志
- [x] 日志正常写入 `data/logs/`

## 安全验证
- [x] `.gitignore` 排除 `data/config.json`
- [x] `.gitignore` 排除 `data/logs/`
- [x] `.gitignore` 排除 `data/*.log`
- [x] `git status` 不显示敏感文件

## CI/CD 验证
- [x] GitHub Actions 工作流测试路径正确
- [x] flake8 配置正确（指向 src/）
- [x] unittest discover 指向 tests/
