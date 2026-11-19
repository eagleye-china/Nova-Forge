# src/nova_forge/core/cmd_saver.py
"""
星期四 2026-11-19 12:45
Nova Multi-Block 源码保存工具
【最终封版 v3.0】原生弹窗 Yes 在右、系统托盘驻留、首行注释补全、静默容错。
"""

import re
import sys
from pathlib import Path

try:
    from nova_forge.utils.window_utils import enable_dark_title_bar
except ImportError:
    try:
        from ..utils.window_utils import enable_dark_title_bar
    except ImportError:
        try:
            from nova_forge.utils.window_utils import enable_dark_title_bar
        except ImportError:
            try:
                from nova_forge.utils import enable_dark_title_bar
            except ImportError:

                def enable_dark_title_bar(window):
                    pass

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QAction
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
    QMessageBox,
    QMenu,
    QPushButton,
    QSplitter,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from resources import resources_rc  # noqa
except ImportError:
    print("[WARN] 未找到 resources_rc, 图标可能无法显示。")

EXTENSION_LANG_MAP = {
    ".py": "Python",
    ".qml": "QML",
    ".md": "Markdown",
    ".json": "JSON",
    ".txt": "Text",
}

PATH_PATTERN = re.compile(
    r"^(?://|#)\s*((?:src|tools|tests|examples|docs|theme)/[^\n]*?(?:\.(?:qml|py|md|json|txt)|qmldir))(?:\s|$)",
    re.MULTILINE,
)

COLOR_SUCCESS = "#4af626"
COLOR_ERROR = "#f44336"
COLOR_WARN = "#ff9800"
COLOR_INFO = "#00e5ff"
COLOR_COVER = "#ffeb3b"
COLOR_NEW = "#4af626"


class MultiBlockSaverWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nova Multi-Block Saver (最终封版 v3.0)")
        self.resize(1200, 800)

        self.root_path = Path.cwd()

        self.clipboard = QApplication.clipboard()
        self.clip_timer = QTimer(self)
        self.clip_timer.setSingleShot(True)
        self.clip_timer.setInterval(400)  # 防抖时间
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
        self.edit_root.setText(str(self.root_path))
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
        btn_save.clicked.connect(lambda: self.scan_and_save(is_auto=False))
        row_top.addWidget(btn_save)

        layout.addLayout(row_top)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 8, 0, 0)
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet(
            "QTextEdit { color: #a9b7c6; background-color: #1e1e1e; font-family: Consolas, monospace; font-size: 14px; }"
        )
        left_layout.addWidget(self.text_edit)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 8, 0, 0)

        lbl_log = QLabel("运行与写入日志 (Terminal):")
        lbl_log.setStyleSheet(f"color: {COLOR_INFO}; font-weight: bold;")
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
        """初始化系统托盘图标与右键菜单"""
        icon = QApplication.windowIcon()
        if icon.isNull():
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)

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
        self.action_toggle_monitor.setText("⚡ 关闭自动监听" if checked else "⚡ 开启自动监听")

    def show_main_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """重写关闭事件：点 X 隐藏到托盘"""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Nova Saver 运行中",
                "程序已最小化到托盘，自动监听功能继续有效。",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
            event.ignore()
        else:
            event.accept()

    def add_log(self, text: str, color: str):
        item = QListWidgetItem(text)
        item.setForeground(QBrush(QColor(color)))
        self.list_result.addItem(item)
        self.list_result.scrollToBottom()

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
        self.add_log("⚡ --- 触发剪贴板监听 ---", COLOR_INFO)

        if self.chk_auto_write.isChecked():
            self.scan_and_save(is_auto=True)

    def manual_load_from_clipboard(self):
        try:
            mime = self.clipboard.mimeData()
            text = mime.text() if mime.hasText() else ""
        except Exception:
            text = ""

        if not text.strip():
            self.add_log("❌ 剪贴板是空的!", COLOR_ERROR)
            return
        self.text_edit.clear()
        self.text_edit.setText(text)
        self.add_log("📋 手动加载剪贴板成功", COLOR_INFO)

    def extract_blocks(self, text: str):
        blocks = []
        lines = text.splitlines()
        
        current_path = None
        current_lang = None
        code_lines = []
        in_code_block = False

        for line in lines:
            match = PATH_PATTERN.match(line)
            if match:
                if current_path and code_lines:
                    blocks.append(self._finalize_block(current_path, current_lang, code_lines))
                    code_lines = []
                
                current_path = match.group(1).strip()
                file_name = Path(current_path).name
                ext = Path(current_path).suffix.lower()
                
                current_lang = None
                if file_name == "qmldir":
                    current_lang = "QML-Dir"
                elif ext in EXTENSION_LANG_MAP:
                    current_lang = EXTENSION_LANG_MAP[ext]
                
                code_lines = [line]
                in_code_block = False
                continue
            
            if current_path:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                
                code_lines.append(line)

        if current_path and code_lines:
            blocks.append(self._finalize_block(current_path, current_lang, code_lines))

        return blocks

    def _finalize_block(self, rel_path: str, lang: str, code_lines: list) -> dict:
        comment_symbol = "//" if lang in ["QML", "QML-Dir"] else "#"
        expected_header = f"{comment_symbol} {rel_path}"
        
        while code_lines and not code_lines[0].strip():
            code_lines.pop(0)
        while code_lines and not code_lines[-1].strip():
            code_lines.pop()

        if code_lines and code_lines[0].strip() == expected_header:
            raw_code = "\n".join(code_lines) + "\n"
        else:
            raw_code = f"{expected_header}\n" + "\n".join(code_lines) + "\n"

        return {"lang": lang, "path": rel_path, "raw_code": raw_code}

    def select_root(self):
        folder = QFileDialog.getExistingDirectory(self, "选择项目根目录")
        if folder:
            self.root_path = Path(folder).resolve()
            self.edit_root.setText(str(self.root_path))
            self.add_log(f"📁 已设置根目录: {self.root_path}", COLOR_INFO)

    def scan_and_save(self, is_auto=False):
        text = self.text_edit.toPlainText()
        blocks = self.extract_blocks(text)

        if not blocks:
            msg = "未找到合法的代码块，请检查首行路径及扩展名。"
            self.add_log(f"❌ {msg}", COLOR_WARN)
            if is_auto and self.chk_show_error_popup.isChecked():
                msg_box = QMessageBox(self)
                msg_box.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
                msg_box.setWindowTitle("解析失败")
                msg_box.setText(msg)
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.exec()
            return

        root_str = self.edit_root.text().strip()
        if not root_str:
            self.add_log("❌ 写入失败: 请先选择项目根目录!", COLOR_ERROR)
            return

        root = Path(root_str).resolve()
        if not root.exists() or not root.is_dir():
            self.add_log("❌ 写入失败: 根目录不存在!", COLOR_ERROR)
            return

        valid_blocks = []
        file_details_list = []

        for b in blocks:
            rel_path = b["path"]
            full_path = (root / rel_path).resolve()

            try:
                full_path.relative_to(root)
                is_safe = True
            except ValueError:
                is_safe = False

            if not is_safe:
                self.add_log(
                    f"❌ 安全拦截: {rel_path} (试图跳出项目根目录)", COLOR_ERROR
                )
                continue

            is_new = not full_path.exists()
            action_tag = "✨ [新建]" if is_new else "🔄 [覆盖]"

            valid_blocks.append(b)
            file_details_list.append(f"{action_tag} [{b['lang']}] {rel_path}")

        if not valid_blocks:
            self.add_log("❌ 所有代码块均超出项目范围，已全部拦截。", COLOR_ERROR)
            return

        if len(file_details_list) > 12:
            display_details = "\n".join(file_details_list[:12])
            display_details += f"\n... 等共 {len(file_details_list)} 个文件"
        else:
            display_details = "\n".join(file_details_list)

        trigger_mode = "⚡ 自动监听触发" if is_auto else "🖱️ 手动操作触发"

        msg_text = (
            f"检测到 {len(valid_blocks)} 个可写入文件。\n"
            f"当前项目根目录: {root}\n\n"
            f"【文件清单】:\n{display_details}\n\n"
            f"确认将这些内容写入对应路径吗？"
        )

        # 使用原生 QMessageBox，自定义按钮顺序
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        msg_box.setWindowTitle(f"{trigger_mode} - 确认写入")
        msg_box.setText(msg_text)
        msg_box.setIcon(QMessageBox.Icon.Question)

        # 手工添加按钮：先 No（左），后 Yes（右）
        btn_no = msg_box.addButton("No (取消)", QMessageBox.ButtonRole.RejectRole)
        btn_yes = msg_box.addButton("Yes (写入)", QMessageBox.ButtonRole.AcceptRole)

        msg_box.setDefaultButton(btn_yes)
        
        btn_yes.clicked.connect(msg_box.accept)
        btn_no.clicked.connect(msg_box.reject)

        msg_box.raise_()
        msg_box.activateWindow()
        
        msg_box.exec()

        if msg_box.clickedButton() == btn_no:
            self.add_log("⏭️ 用户取消了写入操作", COLOR_WARN)
            return

        success_count = 0
        for b in valid_blocks:
            rel_path = b["path"]
            clean_code = b["raw_code"]
            full_path = (root / rel_path).resolve()

            is_new = not full_path.exists()
            action_desc = "新建" if is_new else "覆盖"
            icon = "✨" if is_new else "🔄"
            log_color = COLOR_NEW if is_new else COLOR_COVER

            full_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                full_path.write_text(clean_code, encoding="utf-8")
                self.add_log(
                    f"{icon} [{b['lang']}] {action_desc}成功: {rel_path}", log_color
                )
                success_count += 1
            except Exception as e:
                self.add_log(f"❌ 写入失败: {rel_path} ({e!s})", COLOR_ERROR)

        if success_count > 0:
            self.add_log(
                f"🎉 共成功写入 {success_count}/{len(valid_blocks)} 个文件",
                COLOR_SUCCESS,
            )
            if is_auto and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "写入成功",
                    f"成功写入 {success_count} 个文件",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
        else:
            self.add_log("⚠️ 没有任何文件被写入。", COLOR_WARN)


def run_clip_saver():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icons/date.svg"))

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[WARN] 系统托盘不可用。")

    qss_path = Path(__file__).resolve().parents[1] / "utils/ui" / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    win = MultiBlockSaverWindow()
    win.showMaximized()
    app.exec()


if __name__ == "__main__":
    run_clip_saver()
