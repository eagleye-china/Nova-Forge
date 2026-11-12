# Nova-Forge User Guide 📖

This guide dives deep into the core features of `Nova-Forge`, helping you build, manage, and publish enterprise-grade Python desktop applications at maximum speed.

## 🛠️ Requirements
- Python 3.10+
- OS: Windows / macOS / Linux

## 📦 1. `init` Command: Generate Project Infrastructure

Run the following command in your **empty folder**:

```bash
nova-forge init
```

### Interactive Prompts
You'll be guided to input:
1. **Project Name** (e.g., `nova-chat`, used as the PyPI package name).
2. **GitHub Repo Name** (defaults to project name).
3. **Your Name** (auto-filled into the MIT License).
4. **Bilingual Descriptions** (for README and project metadata).

### Generated Magic
Instantly generates:
- `pyproject.toml`: PEP 639 compliant packaging.
- `README.md` & `README_zh.md`: Bilingual docs with badges and quick-start examples.
- `LICENSE`: MIT with current year and author.
- `CHANGELOG.md`: Version history.
- `.github/workflows/publish.yml`: GitHub Actions CI/CD pipeline.
- `src/project_name/__init__.py`: Dynamic version loader.
- `init_git.py` & `build_prod.bat`: One-click publish scripts.

---

## 🌲 2. `tree` Command: Instant Directory Scaffolding

Paste your AI-generated architecture into `project_structure.txt`.

### Syntax Rules
Supports `├── `, `└── `, `|--- `, and **automatically ignores `#` comments**.

```text
my-awesome-app/
├── src/
│   └── my_awesome_app/
│       ├── __init__.py
│       └── main.py
├── examples/
└── README.md
```

### Run It
```bash
nova-forge tree
```

### Smart Root-Directory Logic
- If the root name in the txt matches the current folder, it skips creating the root and generates inside.
- If different, it creates a new root folder to prevent pollution.

---

## 🚀 3. Publishing

### Push to GitHub
Run `init_git.py`. It initializes Git, commits, pushes to `main`, and tags `v0.1.0` to trigger GitHub Actions.

### Publish to PyPI
Run `build_prod.bat`. It cleans, builds, checks, and uploads to PyPI in seconds.

---

## ❓ FAQ

**Q: `403 Forbidden` error on PyPI upload?**
A: Check your `.pypirc` for a valid API Token with sufficient scopes.

**Q: `License classifiers have been superseded` error?**
A: Remove `"License :: OSI Approved :: MIT License"` from `classifiers` in `pyproject.toml`.