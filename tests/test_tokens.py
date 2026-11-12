"""设计 token 与主题管理器的纯 Python 测试（不需要 GUI）。"""

from __future__ import annotations

from pyside_nova.theme import tokens
from pyside_nova.theme.manager import NovaThemeManager


def test_palettes_have_same_keys() -> None:
    """浅色 / 深色两套调色板的语义键必须完全一致，否则主题切换会缺色。"""
    assert set(tokens.LIGHT.keys()) == set(tokens.DARK.keys())


def test_no_duplicate_semantic_colors() -> None:
    """所有颜色值必须是合法 hex，防止手滑写入非法值。"""
    for palette in (tokens.LIGHT, tokens.DARK):
        for name, value in palette.items():
            assert value.startswith("#") and len(value) == 7, f"{name} 颜色值非法: {value}"


def test_button_heights_cover_all_sizes() -> None:
    assert set(tokens.BUTTON_HEIGHTS.keys()) == set(tokens.TYPOGRAPHY.keys())


def test_theme_manager_toggle_and_color() -> None:
    tm = NovaThemeManager.instance()
    tm.reset()
    assert tm.mode == "light"
    assert tm.color("primary") == tokens.LIGHT["primary"]

    tm.toggle()
    assert tm.mode == "dark"
    assert tm.color("primary") == tokens.DARK["primary"]

    tm.set_mode("不存在的模式")
    assert tm.mode == "light"

    tm.reset()


def test_theme_manager_is_singleton() -> None:
    assert NovaThemeManager.instance() is NovaThemeManager.instance()
