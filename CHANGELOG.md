# Changelog

所有版本变更记录，遵循 [Semantic Versioning](https://semver.org/) 规范。

## [0.2.0c] - 2026-11-13

### ✨ Features & Refactoring
- **发版双通道重构**：正式上线 `nova-forge publish` (云端 OIDC) 与 `nova-forge build` (本地 twine) 两个独立命令。
- **底层执行器**：抽离并封装 `_runner.py`，统一 `subprocess` 调用，强制 UTF-8 并增加静默成功回显提示。
- **安全解析**：新增 `project_meta.py`，使用 `tomllib` 统一解析 `pyproject.toml`，拒绝静默兜底发版。
- **防冲突机制**：在 `publish` 流水线中注入 `git pull --rebase`，防止远程并发变更导致 Push 失败。

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