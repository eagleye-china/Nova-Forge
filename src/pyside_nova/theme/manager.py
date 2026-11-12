"""
NovaThemeManager —— 运行时主题管理器（QObject 单例）。

职责：
1. 保存当前主题模式（light / dark）；
2. 与 QML 侧 ``Theme`` 单例同步 ``mode`` 属性，触发颜色绑定刷新；
3. 供 Python 侧查询语义色值。

典型用法::

    from pyside_nova.theme.manager import NovaThemeManager

    tm = NovaThemeManager.instance()
    engine.rootContext().setContextProperty("novaTheme", tm)
    engine.load(qml_path)
    tm.attach_engine(engine)     # 必须在 load 之后，Theme 单例才可被取到
    tm.set_mode("dark")

注意：本模块只管理主题，不负责业务桥接，不要在这里塞设备、数据库逻辑。
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from .tokens import COLOR_NAMES, DARK, LIGHT

logger = logging.getLogger("pyside_nova.theme")

_MODES = ("light", "dark")


class NovaThemeManager(QObject):
    """主题管理器单例。"""

    modeChanged = Signal(str)

    _instance: NovaThemeManager | None = None

    def __init__(self, mode: str = "light", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mode: str = mode if mode in _MODES else "light"
        self._theme_singleton: Any = None

    # ── 单例 ───────────────────────────────────────────────
    @classmethod
    def instance(cls) -> NovaThemeManager:
        if cls._instance is None:
            cls._instance = NovaThemeManager()
        return cls._instance

    # ── 模式属性 ───────────────────────────────────────────
    @Property(str, notify=modeChanged)
    def mode(self) -> str:  # noqa: D401
        """当前主题模式：``light`` / ``dark``。"""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self.set_mode(value)

    @Slot(str)
    def set_mode(self, value: str) -> None:
        """切换主题模式（非法值回退为 light）。"""
        new_mode = str(value).strip().lower()
        if new_mode not in _MODES:
            logger.warning("非法主题模式 %r，已回退为 light", value)
            new_mode = "light"
        if new_mode == self._mode:
            return
        self._mode = new_mode
        self._sync_to_qml()
        self.modeChanged.emit(new_mode)

    @Slot()
    def toggle(self) -> None:
        """在 light / dark 之间切换。"""
        self.set_mode("dark" if self._mode == "light" else "light")

    # ── 与 QML 单例同步 ────────────────────────────────────
    def attach_engine(self, engine: Any) -> None:
        """绑定 QQmlApplicationEngine，拿到 ``Nova/Theme`` 单例实例。

        必须在 ``engine.load()`` 之后调用，否则模块尚未注册、返回 None。
        """
        try:
            self._theme_singleton = engine.singletonInstance("Nova", "Theme")
        except Exception:  # pragma: no cover - 版本差异兜底
            logger.exception("获取 QML Theme 单例失败")
            self._theme_singleton = None

        if self._theme_singleton is None:
            logger.warning(
                "未取到 QML Theme 单例，主题切换仅影响 Python 侧；请确认在 engine.load() 之后调用 attach_engine()"
            )
            return

        self._sync_to_qml()

    def _sync_to_qml(self) -> None:
        if self._theme_singleton is None:
            return
        self._theme_singleton.setProperty("mode", self._mode)

    # ── Python 侧取色 ──────────────────────────────────────
    def palette(self) -> dict[str, str]:
        """返回当前模式下的完整调色板（hex 字符串字典）。"""
        return dict(DARK if self._mode == "dark" else LIGHT)

    def color(self, name: str) -> str:
        """按语义名取色；未知名称回退到 primary。"""
        palette = self.palette()
        if name not in COLOR_NAMES:
            return palette["primary"]
        return palette[name]

    def reset(self) -> None:
        """重置为浅色（主要给测试用例用）。"""
        self._mode = "light"
        self._sync_to_qml()
        self.modeChanged.emit("light")
