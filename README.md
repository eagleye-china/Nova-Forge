# Nova-Forge 🛠️

> **The ultimate project forging tool for PySide6 ecosystems. Scaffold enterprise-grade architectures in seconds.**

**English** | [简体中文](https://github.com/eagleye-china/Nova-Forge/blob/main/README_zh.md)

[![PyPI version](https://img.shields.io/pypi/v/nova-forge?color=blue&label=PyPI)](https://pypi.org/project/nova-forge/)
[![Python Version](https://img.shields.io/pypi/pyversions/nova-forge)](https://pypi.org/project/nova-forge/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/eagleye-china/Nova-Forge/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eagleye-china/Nova-Forge?style=social)](https://github.com/eagleye-china/Nova-Forge)
📖 **[Read the Full User Guide (USAGE.md)](https://github.com/eagleye-china/Nova-Forge/blob/main/docs/USAGE.md)**

**Nova-Forge** is a blazing-fast CLI scaffolding tool designed to eliminate the boilerplate of modern Python desktop applications. 

Stop copying and pasting `pyproject.toml`, fumbling with MIT licenses, or manually creating hundreds of folders. With a single command, Nova-Forge generates a complete, production-ready `src-layout` project equipped with CI/CD, bilingual docs, and PyPI packaging scripts.

## ✨ Features

- 🚀 **`nova-forge init`**: Generates `pyproject.toml`, bilingual `README.md`, `LICENSE`, and a GitHub Actions workflow for automatic PyPI publishing.
- 🌲 **`nova-forge tree`**: Builds an entire directory structure instantly from a simple text-based tree diagram.
- 🤖 **AI-Ready**: Perfect for pairing with AI coding assistants (like DeepSeek or ChatGPT) to instantly materialize AI-generated architectures.

## 📦 Installation

```bash
pip install nova-forge
```

## 🛠️ Usage

### 1. Initialize Project Configuration
Run this in your empty project folder. It will interactively ask for your project details and generate all necessary metadata.

```bash
nova-forge init
```

### 2. Build Directory Structure
Got a project layout from your AI architect? Paste it into `project_structure.txt`:

```text
my-awesome-app/
├── src/
│   └── my_awesome_app/
│       ├── __init__.py
│       └── main.py
└── examples/
```

Then run:

```bash
nova-forge tree
```

*Boom! Your entire folder structure is created with auto-generated `__init__.py` and boilerplate code.*

## 📜 License

MIT License. See [LICENSE](https://github.com/eagleye-china/Nova-Forge/blob/main/LICENSE) for details.