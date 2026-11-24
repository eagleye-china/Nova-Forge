# src/nova_forge/command/cmd_icons.py
# 星期五 2026-11-20 00:00
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ..ui.icons_window import IconsWindow

try:
    from nova_forge.resources import resources_rc
except ImportError:
    print("[WARN] 未找到 resources_rc,图标可能无法显示。")


def run_icons():
    """启动图标资产管理工具 (GUI)"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(":/icons/nova.svg"))

    # 实例化窗口
    window = IconsWindow()
    window.setWindowTitle("Nova-Forge 图标管理")
    window.resize(1000, 800)
    window.show()

    # 如果 app 是这里创建的，则进入事件循环
    if app.exec_():
        pass
