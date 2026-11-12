# Nova-Forge 完全使用指南 📖

本指南将带你深入了解 `Nova-Forge` 的核心功能，帮助你以极限速度搭建、管理并发布企业级 Python 桌面应用。

## 🛠️ 环境要求

- Python 3.10 或更高版本
- 操作系统：Windows / macOS / Linux

## 📦 1. `init` 命令：一键生成项目基建

在你的**空文件夹**中运行以下命令：

```bash
nova-forge init
```

### 交互流程
运行后，终端会引导你输入：
1. **项目名**（如 `nova-chat`，会作为 PyPI 包名）。
2. **GitHub 仓库名**（默认与项目名相同，可自定义大小写）。
3. **你的大名**（自动填入 MIT 协议的版权人）。
4. **中英文描述**（用于自动生成 README 和项目元数据）。

### 它为你变出了什么？
敲下回车后，你的空文件夹会瞬间出现：
- `pyproject.toml`：完美符合 PEP 639 标准的打包配置。
- `README.md` & `README_zh.md`：带全套徽章（Badges）和 10 行代码示例的双语门面。
- `LICENSE`：自动填入当前年份和你大名的 MIT 协议。
- `CHANGELOG.md`：带日期时间戳的版本更新记录。
- `.github/workflows/publish.yml`：GitHub Actions 自动化发版流水线。
- `src/项目名/__init__.py`：自动读取 `pyproject.toml` 版本的动态挂载文件。
- `init_git.py` & `build_prod.bat`：一键推 GitHub 和一键推 PyPI 的终极脚本。

---

## 🌲 2. `tree` 命令：极速生成目录骨架

你可以在 AI（如 ChatGPT / DeepSeek）那里让它帮你设计一个架构，然后把生成的文本保存为 `project_structure.txt`。

### 结构树语法规范
`Nova-Forge` 极其智能，支持多种树形符号（如 `├── `、`└── `、`|--- `），并且**自动忽略 `#` 后面的注释**。

```text
my-awesome-app/
├── src/                # 核心源码目录
│   └── my_awesome_app/
│       ├── __init__.py
│       └── main.py
├── examples/           # 演示代码
└── README.md
```

### 运行生成
```bash
nova-forge tree
```

### 智能防呆机制（防套娃）
- **情况 A**：如果 `txt` 的第一行 `my-awesome-app/` 与当前文件夹名称**完全一致**，它会跳过根目录创建，直接在里面铺开 `src` 和 `examples`。
- **情况 B**：如果名字**不一致**，它会安全地在里面新建一个 `my-awesome-app/` 文件夹，绝不污染当前目录。

---

## 🚀 3. 发布项目：一键推 GitHub 和 PyPI

### 推送到 GitHub
在生成的项目中，双击运行 `init_git.py`。
它会自动：
1. 初始化 Git 仓库，提交代码。
2. 关联你的远程 GitHub 仓库。
3. 推送到 `main` 分支。
4. 打上 `v0.1.0` 标签（触发 GitHub Actions 自动发布）。

### 手动发布到 PyPI（备用）
如果你没有配置 GitHub Actions，直接双击 `build_prod.bat`。
它会在 3 秒内完成清理、构建、检查和上传，随后你就可以在 PyPI 看到你的包了！

---

## ❓ 常见问题 (FAQ)

**Q: 为什么上传 PyPI 时报错 `403 Forbidden`？**
A: 请检查你电脑上的 `.pypirc` 文件是否配置了正确的 API Token，且 Token 的权限范围包含了你要上传的项目。

**Q: 打包时报错 `License classifiers have been superseded`？**
A: 请在 `pyproject.toml` 中删除 `classifiers` 里的 `"License :: OSI Approved :: MIT License"` 这一行。保留 `license = "MIT"` 即可。