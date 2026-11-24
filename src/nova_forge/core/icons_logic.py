# src/nova_forge/core/icons_logic.py
# 星期一 2026-11-23 00:20
"""QRC 资源更新线程（无外部私有依赖）。"""

from PySide6.QtCore import QThread, Signal

from .qrc_builder import update_qrc_from_directory


class ResourceBuilderWorker(QThread):
    """后台更新 QRC 资源的线程。"""

    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, target_dir: str):
        super().__init__()
        self.target_dir = target_dir

    def run(self):
        try:
            logs = update_qrc_from_directory(self.target_dir)
        except (OSError, ValueError) as exc:
            self.finished_signal.emit(False, f"更新失败: {exc}")
            return

        self.log_signal.emit(logs)
        self.finished_signal.emit(True, "QRC 资源文件更新完毕!")
