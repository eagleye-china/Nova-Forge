# src/nova_forge/ui/saver_window.py
# 创建时间：星期二 2026-11-24 21:39
"""
Nova Multi-Block 源码保存工具 - 纯 UI 视图层
（已移除全局快捷键功能）
"""

from pathlib import Path

try:
    from typing import override  # Python 3.12+
except ImportError:  # Python 3.10 / 3.11：override 仅用于类型检查
    def override(func):
        return func

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QSplitter,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from nova_forge.utils.window_utils import enable_dark_title_bar
except ImportError:

    def enable_dark_title_bar(window):
        pass


class SaverWindow(QMainWindow):
    signal_parse_requested = Signal(bool)

    def __init__(self, root_path: str):
        super().__init__()
        self.setWindowTitle("Nova Multi-Block Saver")
        self.resize(1200, 800)
        self.root_path = root_path

        self.clipboard = QApplication.clipboard()
        self.clip_timer = QTimer(self)
        self.clip_timer.setSingleShot(True)
        self.clip_timer.setInterval(400)
        self.clip_timer.timeout.connect(self.auto_load_from_clipboard)

        self.init_ui()
        self.init_tray()

        self.clipboard.dataChanged.connect(self.on_clipboard_changed)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        row_top = QHBoxLayout()
        row_top.addWidget(QLabel("项目根目录:"))

        self.edit_root = QLineEdit()
        self.edit_root.setText(self.root_path)
        row_top.addWidget(self.edit_root)

        btn_select = QPushButton("📁 选择")
        btn_select.clicked.connect(self.select_root)
        row_top.addWidget(btn_select)

        self.chk_auto_monitor = QCheckBox("⚡ 自动监听")
        self.chk_auto_monitor.setChecked(True)
        row_top.addWidget(self.chk_auto_monitor)

        self.chk_auto_write = QCheckBox("💾 自动写入")
        self.chk_auto_write.setChecked(True)
        row_top.addWidget(self.chk_auto_write)

        self.chk_show_error_popup = QCheckBox("⚠️ 解析失败弹窗")
        self.chk_show_error_popup.setChecked(False)
        row_top.addWidget(self.chk_show_error_popup)

        btn_clip = QPushButton("📋 加载剪贴板")
        btn_clip.clicked.connect(self.manual_load_from_clipboard)
        row_top.addWidget(btn_clip)

        btn_save = QPushButton("💾 写入文件")
        btn_save.clicked.connect(lambda: self.signal_parse_requested.emit(False))
        row_top.addWidget(btn_save)

        layout.addLayout(row_top)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：文本编辑区
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 8, 0, 0)
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet(
            "QTextEdit { color: #a9b7c6; background-color: #1e1e1e; font-family: Consolas, monospace; font-size: 14px; }"
        )
        left_layout.addWidget(self.text_edit)

        # 右侧：日志区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 8, 0, 0)

        lbl_log = QLabel("运行与写入日志 (Terminal):")
        lbl_log.setStyleSheet("color: #00e5ff; font-weight: bold;")
        right_layout.addWidget(lbl_log)

        self.list_result = QListWidget()
        self.list_result.setStyleSheet(
            "QListWidget { background-color: #0d0d0d; color: #d4d4d4; border: 1px solid #333; font-family: Consolas, 'Courier New', monospace; font-size: 13px; }"
        )
        right_layout.addWidget(self.list_result)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)
        enable_dark_title_bar(self)

    def init_tray(self):
        icon = QApplication.windowIcon()
        if icon.isNull():
            icon = self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            )

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Nova Multi-Block Saver")

        tray_menu = QMenu(self)
        action_show = QAction("🖥️ 显示主界面", self)
        action_show.triggered.connect(self.show_main_window)
        tray_menu.addAction(action_show)

        self.action_toggle_monitor = QAction("⚡ 开启自动监听", self, checkable=True)
        self.action_toggle_monitor.setChecked(self.chk_auto_monitor.isChecked())
        self.action_toggle_monitor.triggered.connect(self.toggle_monitor_from_tray)
        tray_menu.addAction(self.action_toggle_monitor)

        tray_menu.addSeparator()
        action_quit = QAction("❌ 退出", self)
        action_quit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window()

    def toggle_monitor_from_tray(self, checked):
        self.chk_auto_monitor.setChecked(checked)
        self.action_toggle_monitor.setText(
            "⚡ 关闭自动监听" if checked else "⚡ 开启自动监听"
        )

    def show_main_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    @override
    def closeEvent(self, event):  # noqa: N802 - Qt 覆写方法，必须保持驼峰命名
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Nova Saver 运行中",
                "程序已最小化到托盘，双击托盘图标可重新打开主界面。",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
            event.ignore()
        else:
            event.accept()

    def on_clipboard_changed(self):
        if self.chk_auto_monitor.isChecked():
            self.clip_timer.start()

    def auto_load_from_clipboard(self):
        if not self.chk_auto_monitor.isChecked():
            return
        try:
            mime = self.clipboard.mimeData()
            if not mime.hasText():
                return
            text = mime.text()
        except Exception:
            return

        if not text:
            return

        self.text_edit.setText(text)
        self.add_log("⚡ --- 触发剪贴板监听 ---", "#00e5ff")

        if self.chk_auto_write.isChecked():
            self.signal_parse_requested.emit(True)

    def manual_load_from_clipboard(self):
        try:
            mime = self.clipboard.mimeData()
            text = mime.text() if mime.hasText() else ""
        except Exception:
            text = ""

        if not text.strip():
            self.add_log("❌ 剪贴板是空的!", "#f44336")
            return
        self.text_edit.clear()
        self.text_edit.setText(text)
        self.add_log("📋 手动加载剪贴板成功", "#00e5ff")

    def select_root(self):
        folder = QFileDialog.getExistingDirectory(self, "选择项目根目录")
        if folder:
            self.edit_root.setText(str(Path(folder).resolve()))
            self.add_log(f"📁 已设置根目录: {folder}", "#00e5ff")

    def add_log(self, text: str, color_hex: str):
        item = QListWidgetItem(text)
        item.setForeground(QBrush(QColor(color_hex)))
        self.list_result.addItem(item)
        self.list_result.scrollToBottom()
