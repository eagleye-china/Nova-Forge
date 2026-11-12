# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/), versioning follows [SemVer](https://semver.org/).

## [0.1.0] - 2026-11-07

### Added
- 项目骨架：src-layout、PEP 621 `pyproject.toml`、`MANIFEST.in`、`ruff.toml`、CI（lint / qmllint / pytest / build / wheel 资源校验）。
- `pyside_nova.install_qml_import_path()`：把包内 `qml/` 注册为 QML 导入路径，安装后即可 `import Nova 1.0`。
- 设计 token 单一真源 `theme/tokens.py` + 生成器 `tools/gen_theme.py` → `qml/Nova/Theme.qml`。
- `NovaThemeManager` 单例：明暗主题切换，与 QML `Theme` 单例同步。
- `Theme` / `Units` QML 单例；`NovaButton` 首个组件（color / variant / size / rounded / elevated / dense / loading / disabled / label / icon）。
- `core/bridge.py`（`NovaBridgeBase`）与 `core/worker.py`（`BaseWorker` / `ThreadRunner`）工控线程基座。
- `examples/01_minimal` 最小可运行示例；`tests` 冒烟测试与 token 契约测试。
