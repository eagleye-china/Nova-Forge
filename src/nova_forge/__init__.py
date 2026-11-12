# src/nova_forge/__init__.py
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# 优先从本地的 pyproject.toml 读取版本号（开发模式）
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

try:
    _pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(_pyproject_path, "rb") as f:
        _data = tomllib.load(f)
        __version__ = _data["project"]["version"]
except Exception:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("nova-forge")
    except PackageNotFoundError:
        __version__ = "0.1.0"

__all__ = ["__version__"]
