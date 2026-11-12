"""
设计 Token —— 全库唯一真源。

改动本文件后，必须执行::

    python tools/gen_theme.py

重新生成 ``src/pyside_nova/qml/Nova/Theme.qml``。
生成文件不要手工修改，CI 会校验二者一致。

命名契约（与 pyside-quasar 保持一致，勿擅自新增同义别名）：
    primary / secondary / positive / negative / warning / info / dark / white
    surface / background / border / text_primary / text_secondary
    hover / pressed / disabled / focus
"""

from __future__ import annotations

TOKEN_VERSION = "0.1.0"

#: 颜色 token（浅色主题）
LIGHT: dict[str, str] = {
    "primary": "#1976D2",
    "secondary": "#26A69A",
    "positive": "#21BA45",
    "negative": "#C10015",
    "warning": "#F2C037",
    "info": "#31CCEC",
    "dark": "#1D1D1D",
    "white": "#FFFFFF",
    "background": "#F5F7FA",
    "surface": "#FFFFFF",
    "border": "#DDE3EA",
    "text_primary": "#1C1C1C",
    "text_secondary": "#6B7280",
    "hover": "#E8F0FE",
    "pressed": "#D2E3FC",
    "disabled": "#BDBDBD",
    "focus": "#1976D2",
}

#: 颜色 token（深色主题）
DARK: dict[str, str] = {
    "primary": "#64B5F6",
    "secondary": "#4DB6AC",
    "positive": "#3DD68C",
    "negative": "#FF6B6B",
    "warning": "#FFD54F",
    "info": "#4DD0E1",
    "dark": "#121212",
    "white": "#FFFFFF",
    "background": "#121212",
    "surface": "#1E1E1E",
    "border": "#333333",
    "text_primary": "#E6E6E6",
    "text_secondary": "#A0A6B1",
    "hover": "#2A2F37",
    "pressed": "#353B45",
    "disabled": "#4A4F57",
    "focus": "#64B5F6",
}

#: 间距（dp）
SPACING: dict[str, int] = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

#: 圆角（dp）
RADIUS: dict[str, int] = {
    "none": 0,
    "sm": 4,
    "md": 8,
    "lg": 16,
    "pill": 999,
}

#: 字号（px @96dpi）
TYPOGRAPHY: dict[str, int] = {
    "xs": 11,
    "sm": 12,
    "md": 14,
    "lg": 16,
    "xl": 18,
}

#: 控制件高度（dp）
BUTTON_HEIGHTS: dict[str, int] = {
    "xs": 20,
    "sm": 26,
    "md": 32,
    "lg": 40,
    "xl": 48,
}

#: 动效时长（ms）
MOTION: dict[str, int] = {
    "fast": 150,
    "base": 250,
}

#: 语义色名（组件 color 属性的合法取值），按顺序生成到 Theme.qml
COLOR_NAMES: tuple[str, ...] = tuple(LIGHT.keys())
