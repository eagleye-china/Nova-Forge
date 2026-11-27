# src/nova_forge/command/cmd_icons.py
# 创建时间：星期二 2026-11-24 22:03
"""icons 子命令：图标资产管理 GUI。

主路径使用 pyside-nova 组件库（QML）；组件库缺失或 QML 加载失败时，
自动降级到原 QtWidgets 版 IconsWindow，保证命令始终可用。
"""
from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

# 默认 QtQuick.Controls 样式：Basic/Windows 在部分环境会把 ScrollBar 渲染成黑块，
# 且不允许自定义 contentItem（会刷 "current style does not support customization" 警告）。
# Fusion 跨平台一致、支持自定义，保证零警告且滚动条正常；用户可用环境变量覆盖。
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

with contextlib.suppress(ImportError):
    from nova_forge.resources import resources_rc  # noqa: F401

QML_FILE = Path(__file__).resolve().parent.parent / "ui" / "qml" / "icons_main.qml"

# 模块级保活：外部已有 QGuiApplication 时函数会立即返回，
# 引擎/桥接对象必须挂在这里，否则被 GC 后 QML 界面会崩。
_KEEPALIVE: list = []


def _run_legacy(app: QApplication) -> None:
    """降级路径：原 QtWidgets 实现（复用同一个 QApplication）。"""
    from ..ui.icons_window import IconsWindow

    window = IconsWindow()
    window.setWindowTitle("Nova-Forge 图标管理")
    window.resize(1000, 800)
    window.show()
    app.exec()


def run_icons(project_root: str | None = None):
    """启动图标资产管理工具 (GUI)。

    project_root: 显式指定要扫描的项目根；缺省按当前工作目录向上探测。
    """
    # QApplication 同时支持 QML 与 QtWidgets，主/降级两条路径共用一个实例
    app = QApplication.instance()
    created_here = app is None
    if app is None:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(":/icons/nova.svg"))

    try:
        from pyside_nova import init_nova
    except ImportError:
        print("[WARN] 未找到 pyside-nova，已回退到 QtWidgets 窗口。", file=sys.stderr)
        return _run_legacy(app)

    from ..bridge.icons_bridge import IconsBridge

    engine = QQmlApplicationEngine()
    init_nova(engine)  # 注册 Nova.* QML 模块
    bridge = IconsBridge(project_root=project_root)
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(str(QML_FILE)))

    if not engine.rootObjects():
        print("[WARN] QML 界面加载失败，已回退到 QtWidgets 窗口。", file=sys.stderr)
        engine.deleteLater()
        return _run_legacy(app)

    # 窗口句柄此刻才有效：按当前主题同步 Windows 原生标题栏明暗
    from ..utils.window_utils import apply_dark_title_bars

    apply_dark_title_bars(True)
    _KEEPALIVE.append((engine, bridge))
    if created_here:
        return app.exec()
    return None
