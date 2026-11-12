"""pytest 公共夹具。

约定：所有 GUI/QML 测试都走 pytest-qt 的 ``qapp``，并在 Linux CI 上用 ``xvfb-run`` 执行。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def qml_import_root() -> str:
    """返回包内 QML 导入根目录（同时写入 QML2_IMPORT_PATH）。"""
    from pyside_nova import install_qml_import_path

    return install_qml_import_path()
