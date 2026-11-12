"""
Nova 最小可运行示例。

运行（两种都行）::

    # 方式 A：仓库内直接跑（无需安装）
    python examples/01_minimal/main.py

    # 方式 B：安装后跑
    pip install -e .
    python examples/01_minimal/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from pyside_nova import install_qml_import_path, theme_manager  # noqa: E402


def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("PySide Nova Minimal")

    engine = QQmlApplicationEngine()
    install_qml_import_path(engine)

    tm = theme_manager()
    engine.rootContext().setContextProperty("novaTheme", tm)

    qml_file = Path(__file__).with_name("main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print("[ERROR] QML 加载失败，请查看上方控制台输出。")
        return 1

    # 必须在 load 之后再绑定 Theme 单例
    tm.attach_engine(engine)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
