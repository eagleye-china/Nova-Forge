"""主题子系统。

- :mod:`pyside_nova.theme.tokens` —— 设计 token 唯一真源（纯 Python，无 Qt 依赖）
- :mod:`pyside_nova.theme.manager` —— 运行时主题管理器（QObject 单例，需 PySide6）
"""

from __future__ import annotations

from typing import Any

from .tokens import (  # noqa: F401
    BUTTON_HEIGHTS,
    COLOR_NAMES,
    DARK,
    LIGHT,
    MOTION,
    RADIUS,
    SPACING,
    TOKEN_VERSION,
    TYPOGRAPHY,
)

__all__ = [
    "BUTTON_HEIGHTS",
    "COLOR_NAMES",
    "DARK",
    "LIGHT",
    "MOTION",
    "RADIUS",
    "SPACING",
    "TOKEN_VERSION",
    "TYPOGRAPHY",
    "NovaThemeManager",
]


def __getattr__(name: str) -> Any:
    """延迟导入 NovaThemeManager，保证纯 token 场景不依赖 PySide6。"""
    if name == "NovaThemeManager":
        from .manager import NovaThemeManager

        return NovaThemeManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
