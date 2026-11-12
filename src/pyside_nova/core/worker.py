"""
通用后台工作线程基座（工控 7×24 场景必备）。

铁则：
1. 所有 IO / Modbus / 串口 / 数据库 / 长耗时计算，必须放 ``BaseWorker`` 子类里跑；
2. Worker 内部【禁止】直接修改 QML 可绑定属性，也禁止弹窗；
3. Worker 只通过 ``dataReady`` / ``error`` / ``finished`` 信号把原始结果抛回主线程；
4. QML 组件的 JS 函数里【禁止】写 IO（QML 的 JS 跑在主线程，一阻塞整屏卡死）。

典型用法::

    class ReaderWorker(BaseWorker):
        dataReady = Signal(dict)

        @Slot()
        def run(self) -> None:
            try:
                self.dataReady.emit({"value": 1.0})
            except Exception as exc:
                self.error.emit(f"采集失败: {exc}")
            finally:
                self.finished.emit()

    runner = ThreadRunner(ReaderWorker())
    runner.start_run()
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Slot


class BaseWorker(QObject):
    """业务线程内执行体。子类必须实现 ``run()`` 槽函数。"""

    dataReady = Signal(object)
    error = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:  # pragma: no cover - 抽象方法
        raise NotImplementedError


class ThreadRunner(QThread):
    """把一个 ``BaseWorker`` 甩到子线程执行，并在结束后自动回收。"""

    def __init__(self, worker: BaseWorker, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker = worker
        worker.moveToThread(self)
        self.started.connect(worker.run)
        worker.finished.connect(self.quit)
        worker.finished.connect(worker.deleteLater)
        self.finished.connect(self.deleteLater)

    @Slot()
    def start_run(self) -> None:
        """启动线程（QML 侧可直接调用）。"""
        self.start()

    def stop(self, timeout_ms: int = 5000) -> None:
        """请求退出并等待（用于窗口关闭时的收尾）。"""
        self.quit()
        self.wait(timeout_ms)
