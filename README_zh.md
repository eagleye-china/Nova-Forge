# Nova-Forge 🛠️

> **PySide6 生态的终极项目锻造工具。数秒内搭建企业级架构。**

[English](https://github.com/eagleye-china/Nova-Forge/blob/main/README.md) | **简体中文**

[![PyPI version](https://img.shields.io/pypi/v/nova-forge?color=blue&label=PyPI)](https://pypi.org/project/nova-forge/)
[![Python Version](https://img.shields.io/pypi/pyversions/nova-forge)](https://pypi.org/project/nova-forge/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/eagleye-china/Nova-Forge/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eagleye-china/Nova-Forge?style=social)](https://github.com/eagleye-china/Nova-Forge)
📖 **[Read the Full User Guide (USAGE.md)](https://github.com/eagleye-china/Nova-Forge/blob/main/docs/USAGE.md)**

**Nova-Forge** 是一款专为现代 Python 桌面应用打造的极速 CLI 脚手架工具。

告别复制粘贴 `pyproject.toml`、手动编写 LICENSE 或痛苦地新建几百个空文件夹的日子。只需一行命令，Nova-Forge 就能为你生成一个包含 CI/CD 自动化发版、中英双语门面、符合企业级 `src-layout` 规范的完整项目架构。

## ✨ 核心特性

- 🚀 **`nova-forge init`**：一键生成 `pyproject.toml`、双语 `README.md`、`LICENSE`，以及自动发布到 PyPI 的 GitHub Actions 流水线。
- 🌲 **`nova-forge tree`**：根据一段简单的树形文本，瞬间生成完整的工程目录结构。
- 🤖 **AI 原生适配**：完美对接 AI 编程助手（如 DeepSeek、ChatGPT），让 AI 生成的架构一秒落地。

## 📦 安装

```bash
pip install nova-forge
```

## 🛠️ 使用指南

### 1. 初始化项目配置
在你的空项目文件夹中运行以下命令，它会引导你完成配置，并生成所有必需的元数据文件。

```bash
nova-forge init
```

### 2. 生成目录结构
如果你从 AI 架构师那里拿到了一份目录规划，把它粘贴到 `project_structure.txt` 中：

```text
my-awesome-app/
├── src/
│   └── my_awesome_app/
│       ├── __init__.py
│       └── main.py
└── examples/
```

然后运行：

```bash
nova-forge tree
```

*瞬间！你的工程目录拔地而起，连 `__init__.py` 和基础代码模版都帮你写好了。*

## 📜 开源协议

MIT License，允许商用和二次修改。