# src/nova_forge/templates/tmpl_python_files.py
# 创建时间：星期二 2026-11-24 21:39

CHANGELOG_TMPL = """# Changelog
所有版本变更记录，遵循 [Semantic Versioning](https://semver.org/) 规范。

## [0.1.0] - $YEAR-$MONTH-$DAY
### ✨ Features
- 初始版本发布，搭建完整的企业级工程骨架。
- 完成 PyPI 和 GitHub 的发版流水线配置。
"""

INIT_PY_TMPL = """# -*- coding: utf-8 -*-
from pathlib import Path
import sys

# 优先从本地的 pyproject.toml 读取版本号（开发模式）
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

try:
    # 假设当前文件在 src/项目名/__init__.py，往上找 3 层就是项目根目录
    _pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(_pyproject_path, "rb") as f:
        _data = tomllib.load(f)
        __version__ = _data["project"]["version"]
except Exception:  # noqa: BLE001
    # 如果读不到，再尝试从已安装的包元数据读取（生产模式）
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("$PROJECT_NAME")
    except PackageNotFoundError:
        __version__ = "0.1.0"

__all__ = ["__version__"]
"""

GITIGNORE_TMPL = """# Python
__pycache__/
*.py[cod]
build/
dist/
*.egg-info/

# IDE
.idea/
.vscode/
.DS_Store

# Environments
.env
.venv
venv/
"""
