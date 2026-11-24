# src/nova_forge/command/tmpl_pyproject.py

PYPROJECT_TMPL = """# ==========================================================
# 🚀 $PROJECT_NAME 企业级打包配置
# ==========================================================
[build-system]
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
