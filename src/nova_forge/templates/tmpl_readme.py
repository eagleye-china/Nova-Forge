# src/nova_forge/templates/tmpl_readme.py
# 创建时间：星期二 2026-11-24 21:39

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

README_ZH_TMPL = """# $PROJECT_NAME 🌟

> **$DESC_ZH**

[English](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/README.md) | **简体中文**

[![PyPI version](https://img.shields.io/pypi/v/$PROJECT_NAME?color=blue&label=PyPI)](https://pypi.org/project/$PROJECT_NAME/)
[![Python Version](https://img.shields.io/pypi/pyversions/$PROJECT_NAME)](https://pypi.org/project/$PROJECT_NAME/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/$GITHUB_USER/$REPO_NAME/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/$GITHUB_USER/$REPO_NAME?style=social)](https://github.com/$GITHUB_USER/$REPO_NAME)

## 🤔 为什么选择 $PROJECT_NAME？

- 🚀 **极致性能**:基于原生 PySide6 和 QML，拒绝笨重的 WebView。
- 🎨 **顶级颜值**:原生暗黑模式，丝滑动画，像素级布局。

## 📦 安装

${CB}bash
pip install $PROJECT_NAME
${CB}

## 📜 开源协议

MIT License。
"""
