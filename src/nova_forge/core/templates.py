# -*- coding: utf-8 -*-
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
requires = ["setuptools>=68.2", "wheel"]
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
except Exception:
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

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
    - uses: actions/checkout@v4
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

# ==================== init_git.py ====================
INIT_GIT_TMPL = """import os
import re
import subprocess
import sys
from pathlib import Path

GITHUB_USER = "$GITHUB_USER"

def run(cmd, ignore_error=False):
    print(f"👉 正在执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not ignore_error:
        print(f"❌ 错误: {result.stderr}")
        raise RuntimeError(result.stderr)
    if result.stdout.strip():
        print(result.stdout.strip())
    return result

def get_project_info():
    current_dir = Path.cwd()
    # ✅ 修复：直接使用生成时写死的 REPO_NAME，防止路径错乱
    repo_name = "$REPO_NAME"
    project_name = "$PROJECT_NAME"
    version = "0.1.0"
    toml_path = current_dir / "pyproject.toml"
    if toml_path.exists():
        with open(toml_path, "r", encoding="utf-8") as f:
            content = f.read()
            # ✅ 修复正则转义问题
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_match: project_name = name_match.group(1)

            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if version_match: version = version_match.group(1)
    return repo_name, project_name, version

def main():
    repo_name, project_name, version = get_project_info()
    remote_url = f"git@github.com:{GITHUB_USER}/{repo_name}.git"
    tag_name = f"v{version}"

    print(f"🚀 开始自动初始化并发布【{project_name}】 (v{version})...")

    if not os.path.exists(".git"):
        run(["git", "init"])
        run(["git", "branch", "-M", "main"])
        run(["git", "config", "core.autocrlf", "false"])
        run(["git", "add", "."])
        run(["git", "commit", "-m", f"feat: initial release of {project_name} v{version}"])
        print("✅ 本地 Git 初始化完成！")
    else:
        print("✅ 已检测到 Git 仓库，跳过初始化。")

    try:
        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout
        if "origin" not in remotes:
            run(["git", "remote", "add", "origin", remote_url])
            print(f"✅ 已关联远程仓库: {remote_url}")
        else:
            current_url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
            if current_url != remote_url:
                run(["git", "remote", "set-url", "origin", remote_url])
                print(f"✅ 已更新远程仓库地址: {remote_url}")
            else:
                print(f"✅ 远程仓库已配置正确，无需修改。")
    except Exception as e:
        print(f"❌ 配置远程仓库失败: {e}")

    print("\\n📤 正在推送代码到 GitHub...")
    try:
        run(["git", "push", "-f", "-u", "origin", "main"])
        print("✅ 代码推送成功！")
    except RuntimeError:
        print("❌ 推送失败，请检查 SSH Key 或网络连接！")
        sys.exit(1)

    print(f"\\n🏷️ 准备发布版本 {tag_name}...")
    try:
        tags = subprocess.run(["git", "tag"], capture_output=True, text=True).stdout
        if tag_name not in tags.split():
            run(["git", "tag", tag_name])
            print(f"✅ 标签 {tag_name} 创建成功。")
        else:
            print(f"✅ 标签 {tag_name} 已存在。")
        run(["git", "push", "origin", tag_name])
        print(f"🚀 标签 {tag_name} 推送成功！GitHub Actions 发版流水线已触发！")
    except Exception as e:
        print(f"❌ 标签推送失败: {e}")

    print("\\n🎉 全自动发布流程结束！请前往 GitHub 的 Actions 页面查看发版进度。")

if __name__ == "__main__":
    main()
"""

# ==================== build_prod.bat ====================
BUILD_PROD_TMPL = """@echo off
chcp 65001 >nul
echo =========================================
echo       $PROJECT_NAME 打包与发布
echo =========================================

if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist src\\*.egg-info rmdir /s /q src\\*.egg-info

python -m build
python -m twine check dist/*
python -m twine upload dist/*
pause
"""