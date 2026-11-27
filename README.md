# Nova-Forge 🛠️

> **The ultimate project forging tool for PySide6 ecosystems. Scaffold, deploy, and publish enterprise-grade applications in seconds.**

**English** | [简体中文](https://github.com/eagleye-china/Nova-Forge/blob/main/README_zh.md)

[![PyPI version](https://img.shields.io/pypi/v/nova-forge?color=blue&label=PyPI)](https://pypi.org/project/nova-forge/)
[![Python Version](https://img.shields.io/pypi/pyversions/nova-forge)](https://pypi.org/project/nova-forge/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/eagleye-china/Nova-Forge/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eagleye-china/Nova-Forge?style=social)](https://github.com/eagleye-china/Nova-Forge)

📖 **[Read the Full User Guide (USAGE.md)](https://github.com/eagleye-china/Nova-Forge/blob/main/docs/USAGE.md)**

**Nova-Forge** is a blazing-fast CLI tool designed to eliminate the boilerplate of modern Python desktop and mobile applications. 

Stop copying and pasting `pyproject.toml`, fumbling with MIT licenses, or manually configuring WSL2 for Android deployment. With a single command, Nova-Forge generates complete architectures, automates Git/PyPI publishing, and cross-compiles Android APKs seamlessly on Windows.

## ✨ Core Features

- 🏗️ **`nova-forge scaffold`**: Interactively creates a complete, production-ready desktop or mobile project equipped with CI/CD and bilingual docs.
- 📱 **`nova-forge apk`**: **(Windows Only)** Zero-config Android APK builder. Automatically bridges Windows and WSL2, injecting NDK, Python environments, and dependencies to compile `.apk` files in one click.
- 🌲 **`nova-forge tree`**: Builds an entire directory structure instantly from a simple text-based tree diagram.
- 🔄 **`nova-forge rename`**: Safely rename project folders, package names, and global references in one go.
- 🚀 **`nova-forge publish` / `git` / `pypi`**: Enterprise-grade release pipelines. Automatically commit, push, tag, trigger GitHub Actions, or publish directly to PyPI.
- 🧬 **`nova-forge prescript`**: **Hatch an app, not a skeleton.** Generates one of nine production-grade PySide6 applications hosted by pyside-nova's `NovaIncubator` seven-slot workbench — each with a real business stage (agent console, inline copilot, digital-employee fleet, intent orbit, enterprise desktop, chat workbench, touch-first mobile, adaptive workspace, deployment wizard), a prescript manifest, CARF pipeline, three-way validation and a human-only freeze gate.

## 📦 Installation

```bash
pip install nova-forge
```

## 🛠️ Quick Start

### 1. Scaffold a New Project
```bash
nova-forge scaffold
```
Follow the interactive prompts. It will generate `pyproject.toml`, bilingual READMEs, a robust `.gitignore`, and GitHub Actions workflows.

### 2. The Magic: One-Click Android APK
If you are on Windows and developing a mobile app with PySide6, forget the nightmare of configuring WSL2, NDK, and Gradle manually. Just run:

```bash
nova-forge apk
```
*Enter your Windows project path, and Nova-Forge will automatically spin up WSL2, build the APK using the isolated Linux toolchain, copy the `.apk` back to your Windows folder, and gracefully shut down WSL to save memory.*

### 3. Generate Directory Structure
Paste your layout into `project_structure.txt` and run:
```bash
nova-forge tree
```

### 4. Hatch a Prescript Application
```bash
nova-forge prescript --list                         # nine recipes P1–P9
nova-forge prescript --kind chat --path ./mei-chat  # generate & self-check
cd mei-chat && python -m mei_chat.app               # run it
```
Requires `pyside-nova>=1.2.0` for the generated apps. The `--gui` workbench extra (which renders component docs with `NovaMarkdown`) requires `pyside-nova>=1.4.0`. See [PRESCRIPT_GALLERY.md](https://github.com/eagleye-china/Nova-Forge/blob/main/docs/PRESCRIPT_GALLERY.md) for screenshots of all nine stages.

## 📜 License

MIT License. See [LICENSE](https://github.com/eagleye-china/Nova-Forge/blob/main/LICENSE) for details.