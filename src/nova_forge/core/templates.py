# src/nova_forge/core/templates.py

"""
Nova-Forge 模版库
集中管理所有的文件生成模版，保持 scaffolder.py 的整洁。
"""

# ==================== 默认配置 ====================
DEFAULT_GITHUB_USER = "eagleye-china"
DEFAULT_REAL_NAME = "单保录"
DEFAULT_DESC_EN = "A stunning, GPU-accelerated desktop application for PySide6."
DEFAULT_DESC_ZH = "基于 PySide6 和 QML 打造的炫酷桌面级应用框架。"
DEFAULT_DEPS = '["PySide6>=6.6", "openai>=1.0", "markdown>=3.5"]'

# ✅ 核心防截断变量
CB = "`" * 3

# ==================== pyproject.toml ====================
PYPROJECT_TMPL = """# ==========================================================
# 🚀 $PROJECT_NAME 企业级打包配置
# ==========================================================
[build-system]
# ✅ 升级到 >=77，完美支持 PEP 639 license-files 规范
requires = ["setuptools>=77", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$PROJECT_NAME"
version = "0.1.0"
description = "$DESC_EN"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "$GITHUB_USER", email = "zdt168@sina.cn" }]
dependencies = $DEPS

[project.urls]
Homepage = "https://github.com/$GITHUB_USER/$REPO_NAME"
Repository = "https://github.com/$GITHUB_USER/$REPO_NAME"
Issues = "https://github.com/$GITHUB_USER/$REPO_NAME/issues"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"$MODULE_NAME" = [
    "ui/*.qml",
    "qml/*.qml",
    "resources/*"
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["N802", "E501"]

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true
"""

# ==================== LICENSE ====================
LICENSE_TMPL = """MIT License

Copyright (c) $YEAR $REAL_NAME ($GITHUB_USER)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# ==================== README.md ====================
README_EN_TMPL = """# $PROJECT_NAME 🌟

> **$DESC_EN**

**English** | [简体中文](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/README_zh.md)

[![PyPI version](https://img.shields.io/pypi/v/$PROJECT_NAME?color=blue&label=PyPI)](https://pypi.org/project/$PROJECT_NAME/)
[![Python Version](https://img.shields.io/pypi/pyversions/$PROJECT_NAME)](https://pypi.org/project/$PROJECT_NAME/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/$GITHUB_USER/$REPO_NAME?style=social)](https://github.com/$GITHUB_USER/$REPO_NAME)

## 🤔 Why $PROJECT_NAME?

- 🚀 **Blazing Fast**: Built with pure PySide6 and QML.
- 🎨 **Stunning UI**: Native dark mode, smooth animations.

## 📦 Installation

${CB}bash
pip install $PROJECT_NAME
${CB}

## 🚀 Quick Start

${CB}python
from $MODULE_NAME import __version__
print(f"Version: {__version__}")
${CB}

## 📜 License

MIT License. See [LICENSE](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/LICENSE).
"""

# ==================== README_zh.md ====================
README_ZH_TMPL = """# $PROJECT_NAME 🌟

> **$DESC_ZH**

[English](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/README.md) | **简体中文**

[![PyPI version](https://img.shields.io/pypi/v/$PROJECT_NAME?color=blue&label=PyPI)](https://pypi.org/project/$PROJECT_NAME/)
[![Python Version](https://img.shields.io/pypi/pyversions/$PROJECT_NAME)](https://pypi.org/project/$PROJECT_NAME/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/$GITHUB_USER/$REPO_NAME?style=social)](https://github.com/$GITHUB_USER/$REPO_NAME)

## 🤔 为什么选择 $PROJECT_NAME？

- 🚀 **极致性能**：基于原生 PySide6 和 QML，拒绝笨重的 WebView。
- 🎨 **顶级颜值**：原生暗黑模式，丝滑动画，像素级布局。

## 📦 安装

${CB}bash
pip install $PROJECT_NAME
${CB}

## 📜 开源协议

MIT License。
"""

# ==================== CHANGELOG.md ====================
CHANGELOG_TMPL = """# Changelog
所有版本变更记录，遵循 [Semantic Versioning](https://semver.org/) 规范。

## [0.1.0] - $YEAR-$MONTH-$DAY
### ✨ Features
- 初始版本发布，搭建完整的企业级工程骨架。
- 完成 PyPI 和 GitHub 的发版流水线配置。
"""

# ==================== __init__.py ====================
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

# ==================== GitHub Actions ====================
WORKFLOW_TMPL = """name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:  # ✅ 支持手动触发发版

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Build package
      run: |
        python -m pip install --upgrade pip
        pip install build
        python -m build
        
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
"""

# ==================== .gitignore ====================
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

# ==================== HOW_TO_PUBLISH.md (OIDC 绑定指南) ====================
HOW_TO_PUBLISH_TMPL = """# 🚀 How to Publish to PyPI (Trusted Publishing)

本项目已自动配置了 **OIDC Trusted Publishing**（免密安全发版）。
你不需要在 GitHub 里存任何密码（API Token），只需在 PyPI 网页端完成一次绑定：

1. 登录 PyPI，访问 [Publishing 设置页](https://pypi.org/manage/account/publishing/)。
2. 找到 **"Add a new pending publisher"** 并填写以下信息（请严格区分大小写）：
   - **PyPI Project Name**: `$PROJECT_NAME`
   - **Owner**: `$GITHUB_USER`
   - **Repository name**: `$REPO_NAME`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
3. 点击保存。

完成上述配置后，在本地打上 Git Tag 并推送，或者直接在 GitHub Actions 页面手动触发，即可全自动发版：

${CB}bash
git tag v0.1.0
git push origin v0.1.0
${CB}
"""
