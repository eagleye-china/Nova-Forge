# Changelog

所有版本变更记录，遵循 [Semantic Versioning](https://semver.org/) 规范。

## [0.4.10] - 2026-11-23

### 🐛 Bug Fixes
- 修复 `pypi` 命令重复上传同名版本导致的 PyPI 400 Bad Request：上传前新增版本查重，已存在则给出明确提示并终止。
- 修复 CLI 顶层强制导入 PySide6/tkinter 导致无 GUI 依赖环境下 `--help` 崩溃的问题；GUI 命令改为按需加载。
- 修复 `tree` 命令读写编码不一致（BOM 残留）与字符串格式化缺 `f` 前缀的问题。
- 修复 `saver_window.py` 在 Python 3.10/3.11 下导入 `typing.override` 崩溃的兼容性问题。
- 修复 QRC 更新依赖不存在的外部私有包的问题，改为自包含实现并保留已有 alias。
- 修复图标清洗工具硬编码绝对路径、导入即执行副作用的问题。

### ✨ Features & Refactoring
- 新增零外部依赖冒烟测试套件（7 项），接入 CI 与发版前置卡口。
- 打包配置补充 package-data，确保 `styles.qss` 与 `example_structure.txt` 进入 wheel。

## [0.2.0c] - 2026-11-13

### ✨ Features & Refactoring
- **发版双通道重构**:正式上线 `nova-forge publish` (云端 OIDC) 与 `nova-forge build` (本地 twine) 两个独立命令。
- **底层执行器**:抽离并封装 `_runner.py`，统一 `subprocess` 调用，强制 UTF-8 并增加静默成功回显提示。
- **安全解析**:新增 `project_meta.py`，使用 `tomllib` 统一解析 `pyproject.toml`，拒绝静默兜底发版。
- **防冲突机制**:在 `publish` 流水线中注入 `git pull --rebase`，防止远程并发变更导致 Push 失败。

### 🐛 Bug Fixes
- 修复 `cli.py` 中 `publish` 缺少 `-m` 参数时导致默认提交信息被覆盖的问题。
- 修复 `tree_builder.py` 中的盲目异常捕获与未使用变量。
- 彻底清理全量 Ruff 警告（18项），代码全绿灯通过。

## [0.2.0] - 2026-11-12
### ✨ Features
- 正式加入 `tree` 指令，支持根据 `project_structure.txt` 一键生成目录树。
- 完善 `scaffolder.py` 生成的 OIDC 发版流水线模板。

## [0.1.0] - 2026-11-10
### ✨ Features
- 初始版本发布，搭建完整的 `Nova-Forge` 基础骨架。
- 引入 `init` 脚手架指令。