# Nova-Forge 🛠️

> **PySide6 生态的终极项目锻造工具。数秒内搭建、发版并打包企业级桌面与移动端应用。**

[English](https://github.com/eagleye-china/Nova-Forge/blob/main/README.md) | **简体中文**

[![PyPI version](https://img.shields.io/pypi/v/nova-forge?color=blue&label=PyPI)](https://pypi.org/project/nova-forge/)
[![Python Version](https://img.shields.io/pypi/pyversions/nova-forge)](https://pypi.org/project/nova-forge/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/eagleye-china/Nova-Forge/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eagleye-china/Nova-Forge?style=social)](https://github.com/eagleye-china/Nova-Forge)

📖 **[阅读完整使用手册 (USAGE.md)](https://github.com/eagleye-china/Nova-Forge/blob/main/docs/USAGE.md)**

**Nova-Forge** 是一款专为现代 Python 应用打造的极速 CLI 锻造工具。

告别复制粘贴 `pyproject.toml`、手动配置 WSL2 环境、或痛苦地新建几百个空文件夹的日子。只需一行命令，Nova-Forge 就能为你生成企业级工程架构、接管 Git/PyPI 自动发版，甚至**在 Windows 上一键将项目打包为 Android APK**。

## ✨ 核心特性

- 🏗️ **`nova-forge scaffold`**：交互式生成企业级桌面端/移动端项目，自带 GitHub Actions 自动发版流水线。
- 📱 **`nova-forge apk`**：**(Windows 专属黑科技)** 全自动安卓打包。自动穿透 Windows 和 WSL2 底层，无感注入 NDK、Python 虚拟环境与专属轮子，一键编译出 `.apk` 并回传 Windows 目录。
- 🌲 **`nova-forge tree`**：根据一段简单的树形文本，瞬间生成完整的工程目录结构。
- 🔄 **`nova-forge rename`**：一键重命名项目文件夹、包名与全局依赖引用。
- 🚀 **`nova-forge publish` / `git` / `pypi`**：企业级发版流水线。自动提交、打 Tag、推 GitHub 触发 Actions，或直传 PyPI。

## 📦 安装

```bash
pip install nova-forge
```

## 🛠️ 使用指南

### 1. 交互式脚手架
```bash
nova-forge scaffold
```
根据提示输入项目信息，瞬间获得包含文档、LICENSE 和 CI/CD 的标准化工程。

### 2. 魔法时刻：一键打包安卓 APK
如果您在 Windows 下开发 PySide6 移动应用，请忘掉配置 WSL2、NDK 和 Gradle 的噩梦，直接运行：

```bash
nova-forge apk
```
*输入您的 Windows 项目绝对路径，Nova-Forge 会全自动唤醒 WSL2，分配 Linux 编译沙盒，打包完成后将 `.apk` 悄悄放回您的项目目录，并自动关闭 WSL 释放内存。*

### 3. 目录树生成
把你的 AI 架构规划粘贴到 `project_structure.txt`，然后运行：
```bash
nova-forge tree
```

## 📜 开源协议

MIT License，允许商用和二次修改。