# src/nova_forge/command/cmd_saver.py
# 星期二 2026-11-24 12:35
"""
Nova Multi-Block 源码保存工具 - 控制器与入口
连接 UI 与 业务逻辑，处理弹窗确认及写入流程。
"""

import contextlib
import sys
from pathlib import Path

# GUI 依赖延迟降级：CI / 无 PySide6 环境只需 import 本模块（供单测 patch），
# 不应因缺少 Qt 而崩。真实运行 run_clip_saver() 时若无 PySide6 给出明确提示。
try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

    _HAS_GUI = True
except ImportError:  # pragma: no cover - CI 无 GUI 依赖路径
    Qt = QIcon = QApplication = QMessageBox = QSystemTrayIcon = None
    _HAS_GUI = False

# 导入分层后的模块（注意路径）
from ..core.saver_logic import extract_blocks

try:
    from ..ui.saver_window import SaverWindow
except ImportError:  # pragma: no cover - saver_window 同样依赖 Qt
    SaverWindow = None

# resources_rc 位于项目根 resources/（与 src 同级），不可相对导入；
# 与 cmd_icons 保持一致：绝对导入 + 降级保护（PyPI 包不含该目录时不影响 GUI 启动）。
try:
    from nova_forge.resources import resources_rc
except ImportError:
    print("[WARN] 未找到 resources_rc,图标可能无法显示。")

# 颜色常量定义
COLOR_SUCCESS = "#4af626"
COLOR_ERROR = "#f44336"
COLOR_WARN = "#ff9800"
COLOR_INFO = "#00e5ff"
COLOR_COVER = "#ffeb3b"
COLOR_NEW = "#4af626"


class SaverController:
    """控制器：调度 UI 信号与 Core 逻辑"""

    def __init__(self, window: SaverWindow):
        self.window = window
        self.window.signal_parse_requested.connect(self.scan_and_save)

    def scan_and_save(self, is_auto: bool):
        text = self.window.text_edit.toPlainText()
        # 调用 Core 层的解析逻辑
        blocks = extract_blocks(text)

        if not blocks:
            msg = "未找到合法的代码块，请检查首行路径及扩展名。"
            self.window.add_log(f"❌ {msg}", COLOR_WARN)
            if is_auto and self.window.chk_show_error_popup.isChecked():
                msg_box = QMessageBox(self.window)
                msg_box.setWindowFlags(
                    Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
                )
                msg_box.setWindowTitle("解析失败")
                msg_box.setText(msg)
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.exec()
            return

        root_str = self.window.edit_root.text().strip()
        if not root_str:
            self.window.add_log("❌ 写入失败: 请先选择项目根目录!", COLOR_ERROR)
            return

        root = Path(root_str).resolve()
        if not root.exists() or not root.is_dir():
            self.window.add_log("❌ 写入失败: 根目录不存在!", COLOR_ERROR)
            return

        valid_blocks = []
        file_details_list = []

        # 安全校验
        for b in blocks:
            rel_path = b["path"]
            full_path = (root / rel_path).resolve()

            try:
                full_path.relative_to(root)
                is_safe = True
            except ValueError:
                is_safe = False

            if not is_safe:
                self.window.add_log(
                    f"❌ 安全拦截: {rel_path} (试图跳出项目根目录)", COLOR_ERROR
                )
                continue

            is_new = not full_path.exists()
            action_tag = "✨ [新建]" if is_new else "🔄 [覆盖]"

            valid_blocks.append(b)
            file_details_list.append(f"{action_tag} [{b['lang']}] {rel_path}")

        if not valid_blocks:
            self.window.add_log(
                "❌ 所有代码块均超出项目范围，已全部拦截。", COLOR_ERROR
            )
            return

        # 弹窗确认逻辑
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

        msg_box = QMessageBox(self.window)
        msg_box.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        msg_box.setWindowTitle(f"{trigger_mode} - 确认写入")
        msg_box.setText(msg_text)
        msg_box.setIcon(QMessageBox.Icon.Question)

        btn_no = msg_box.addButton("No (取消)", QMessageBox.ButtonRole.RejectRole)
        btn_yes = msg_box.addButton("Yes (写入)", QMessageBox.ButtonRole.AcceptRole)
        msg_box.setDefaultButton(btn_yes)

        btn_yes.clicked.connect(msg_box.accept)
        btn_no.clicked.connect(msg_box.reject)

        msg_box.raise_()
        msg_box.activateWindow()
        msg_box.exec()

        if msg_box.clickedButton() == btn_no:
            self.window.add_log("⏭️ 用户取消了写入操作", COLOR_WARN)
            return

        # 执行文件写入
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
                self.window.add_log(
                    f"{icon} [{b['lang']}] {action_desc}成功: {rel_path}", log_color
                )
                success_count += 1
            except Exception as e:
                self.window.add_log(f"❌ 写入失败: {rel_path} ({e!s})", COLOR_ERROR)

        if success_count > 0:
            self.window.add_log(
                f"🎉 共成功写入 {success_count}/{len(valid_blocks)} 个文件",
                COLOR_SUCCESS,
            )
            if is_auto and self.window.tray_icon.isVisible():
                self.window.tray_icon.showMessage(
                    "写入成功",
                    f"成功写入 {success_count} 个文件",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
        else:
            self.window.add_log("⚠️ 没有任何文件被写入。", COLOR_WARN)


def run_clip_saver():
    """CLI 入口函数"""
    if QApplication is None:
        raise SystemExit(
            "❌ saver 命令需要 PySide6，请先安装：pip install 'nova-forge[gui]'"
        )
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icons/nova1.svg"))

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[WARN] 系统托盘不可用。")

    # 注意这里：随着层级改变，寻找 qss 的相对路径可能会变。
    # 如果 utils/ui/styles.qss 还在原来的位置（src/nova_forge/utils/ui/），
    # 这里从 command/ 往上退回 src/nova_forge/ 再找 utils
    qss_path = Path(__file__).resolve().parents[1] / "utils/ui" / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    window = SaverWindow(root_path=str(Path.cwd()))
    # 必须持有控制器引用：QMainWindow 不会替我们保活普通 Python 对象，
    # 否则 SaverController 被 GC 后 signal_parse_requested 的槽函数失效，自动监听失效。
    # 挂到 window 上让生命周期与窗口绑定，避免裸调用被立即回收。
    window._saver_controller = SaverController(window)

    window.showMaximized()
    app.exec()
