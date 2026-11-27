# src/nova_forge/utils/window_utils.py
# 创建时间：星期二 2026-11-24 21:39 · 11-27 泛化：QML 窗口 + 主题切换同步
"""Windows 原生标题栏明暗同步（DWM immersive dark mode）。

背景：Qt 的 ``ApplicationWindow`` 在 Windows 上用系统原生标题栏，其颜色由 DWM
控制，不随 QML 侧 ``NovaTheme.isDark`` 变化 —— 暗色界面配白色标题栏即由此而来。
本模块把「按当前主题同步所有顶层窗口标题栏」收敛为一个无窗口引用的函数
``apply_dark_title_bars(dark)``，QML 侧只需在主题变化时调用桥接 Slot。

兼容性：
- Win10 1809~1909 用属性 19，Win10 2004+ / Win11 用属性 20（自动回退）；
- 非 Windows 平台静默 no-op；
- 窗口句柄在创建后才有效，统一用 ``QTimer.singleShot(10, ...)`` 延迟应用。
"""
from __future__ import annotations

import ctypes
import logging
import sys

logger = logging.getLogger(__name__)

# Windows API 常量
DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19  # Win10 1809 - 1909
DWMWA_USE_IMMERSIVE_DARK_MODE_NEW = 20  # Win10 2004+ / Win11
DWMWA_BORDER_COLOR = 34  # Win11 专有:窗口边框颜色
DWMWA_CAPTION_COLOR = 35  # Win11 专有:标题栏背景色


def _set_dwm_attribute(hwnd: int, attribute: int, value: int) -> bool:
    """底层封装:安全地设置 DWM 属性"""
    if sys.platform != "win32" or not hwnd:
        return False
    try:
        # 显式声明参数类型,防止 64 位下的指针截断
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32
        ]
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long

        res = dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            attribute,
            ctypes.byref(ctypes.c_int(value)),
            ctypes.sizeof(ctypes.c_int)
        )
        return res == 0  # S_OK == 0
    except Exception as e:
        logger.debug(f"[WARN] 调用 DWM API 失败: {e}")
        return False


def _apply_hwnd(hwnd: int, dark: bool) -> None:
    """把明暗态写到单个原生窗口句柄（内部函数，不做延迟）。"""
    if not hwnd:
        return
    value = 1 if dark else 0
    # 尝试 Win10 2004+ / Win11 属性 (20)，失败回退 Win10 1809 - 1909 (19)
    if not _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_NEW, value):
        _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, value)


def _hwnd_of(window) -> int:
    """QWidget / QWindow / QQuickWindow 通吃：只依赖 ``winId()``。"""
    try:
        return int(window.winId())
    except Exception as e:
        logger.debug(f"[WARN] 无法取得窗口句柄: {e}")
        return 0


def enable_dark_title_bar(window, enable: bool = True) -> None:
    """对**单个**窗口设置原生标题栏明暗（兼容旧 QtWidgets 调用方）。

    :param window: 任何提供 ``winId()`` 的 Qt 窗口对象（QWidget / QWindow / QQuickWindow）
    :param enable: True 深色，False 浅色（跟随系统）
    """
    if sys.platform != "win32":
        return
    from PySide6.QtCore import QTimer

    QTimer.singleShot(10, lambda: _apply_hwnd(_hwnd_of(window), enable))


def apply_dark_title_bars(dark: bool) -> int:
    """按当前主题同步**所有顶层窗口**的原生标题栏，返回实际处理的窗口数。

    无需持有具体窗口引用（QML 侧拿不到 Python 窗口对象也能工作）：从
    ``QGuiApplication.topLevelWindows()`` 取全部 QWindow，逐个写 DWM 属性。
    由 QML 的主题变化经桥接 Slot 调用，启动时与每次明暗切换都会触发。
    """
    if sys.platform != "win32":
        return 0
    try:
        from PySide6.QtGui import QGuiApplication
    except ImportError:
        return 0

    app = QGuiApplication.instance()
    if app is None:
        return 0

    windows = list(app.topLevelWindows())
    from PySide6.QtCore import QTimer

    def _apply_all() -> None:
        for window in windows:
            _apply_hwnd(_hwnd_of(window), dark)

    QTimer.singleShot(10, _apply_all)
    return len(windows)
