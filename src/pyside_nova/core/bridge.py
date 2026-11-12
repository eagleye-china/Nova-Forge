"""
QML ↔ Python 桥接基类。

约定：
- 桥接类只能承载「界面状态 + 业务编排」，不承载视图绘制；
- 对外暴露给 QML 的属性统一用 ``@Property(..., notify=...)``，否则 QML 绑定无法刷新；
- 槽函数用 ``@Slot`` 并在内部捕获异常，通过 ``errorOccurred`` 上报，避免异常穿透到 Qt 事件循环。

示例::

    class DeviceBridge(NovaBridgeBase):
        voltageChanged = Signal(float)

        def __init__(self):
            super().__init__()
            self._voltage = 0.0

        @Property(float, notify=voltageChanged)
        def voltage(self) -> float:
            return self._voltage

        @Slot()
        def read_device(self) -> None:
            ...
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger("pyside_nova.core")

F = TypeVar("F", bound=Callable[..., Any])


class NovaBridgeBase(QObject):
    """所有业务桥的基类。

    :param parent: Qt 父对象，交由 Qt 管理生命周期时传入。
    """

    errorOccurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def guarded(self, func: F) -> F:
        """装饰器：捕获槽函数异常并转成 ``errorOccurred`` 信号。

        用法::

            @Slot()
            @bridge.guarded
            def do_work(self) -> None:
                ...
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - 边界处统一兜底
                logger.exception("桥接槽函数异常: %s", func.__name__)
                self.errorOccurred.emit(f"{func.__name__} 执行失败: {exc}")
                return None

        return wrapper  # type: ignore[return-value]

    @Slot(str)
    def log(self, message: str) -> None:
        """QML 侧调试输出入口（console.log 的 Python 落点）。"""
        logger.info("[QML] %s", message)
