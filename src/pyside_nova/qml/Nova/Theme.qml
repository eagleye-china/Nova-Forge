pragma Singleton
import QtQuick

// ⚠️ 自动生成文件，请勿手工修改。
// 真源：src/pyside_nova/theme/tokens.py
// 重新生成：python tools/gen_theme.py

QtObject {
    id: root

    // 当前主题模式："light" / "dark"，由 Python 侧 NovaThemeManager 同步
    property string mode: "light"

    // ── 语义颜色（明暗二选一，切换 mode 自动重算）
    readonly property color primary: mode === "dark" ? "#64B5F6" : "#1976D2"
    readonly property color secondary: mode === "dark" ? "#4DB6AC" : "#26A69A"
    readonly property color positive: mode === "dark" ? "#3DD68C" : "#21BA45"
    readonly property color negative: mode === "dark" ? "#FF6B6B" : "#C10015"
    readonly property color warning: mode === "dark" ? "#FFD54F" : "#F2C037"
    readonly property color info: mode === "dark" ? "#4DD0E1" : "#31CCEC"
    readonly property color dark: mode === "dark" ? "#121212" : "#1D1D1D"
    readonly property color white: mode === "dark" ? "#FFFFFF" : "#FFFFFF"
    readonly property color background: mode === "dark" ? "#121212" : "#F5F7FA"
    readonly property color surface: mode === "dark" ? "#1E1E1E" : "#FFFFFF"
    readonly property color border: mode === "dark" ? "#333333" : "#DDE3EA"
    readonly property color text_primary: mode === "dark" ? "#E6E6E6" : "#1C1C1C"
    readonly property color text_secondary: mode === "dark" ? "#A0A6B1" : "#6B7280"
    readonly property color hover: mode === "dark" ? "#2A2F37" : "#E8F0FE"
    readonly property color pressed: mode === "dark" ? "#353B45" : "#D2E3FC"
    readonly property color disabled: mode === "dark" ? "#4A4F57" : "#BDBDBD"
    readonly property color focus: mode === "dark" ? "#64B5F6" : "#1976D2"

    readonly property var _colors: ({
        "primary": primary,
        "secondary": secondary,
        "positive": positive,
        "negative": negative,
        "warning": warning,
        "info": info,
        "dark": dark,
        "white": white,
        "background": background,
        "surface": surface,
        "border": border,
        "text_primary": text_primary,
        "text_secondary": text_secondary,
        "hover": hover,
        "pressed": pressed,
        "disabled": disabled,
        "focus": focus
    })

    // ── 间距（dp）
    readonly property int spaceXs: 4
    readonly property int spaceSm: 8
    readonly property int spaceMd: 16
    readonly property int spaceLg: 24
    readonly property int spaceXl: 32

    // ── 圆角（dp）
    readonly property int radiusNone: 0
    readonly property int radiusSm: 4
    readonly property int radiusMd: 8
    readonly property int radiusLg: 16
    readonly property int radiusPill: 999

    // ── 字号
    readonly property int fontXs: 11
    readonly property int fontSm: 12
    readonly property int fontMd: 14
    readonly property int fontLg: 16
    readonly property int fontXl: 18

    // ── 动效时长（ms）
    readonly property int durationFast: 150
    readonly property int durationBase: 250

    readonly property var _buttonHeights: ({ "xs": 20, "sm": 26, "md": 32, "lg": 40, "xl": 48 })

    readonly property var _fontSizes: ({
        "xs": fontXs,
        "sm": fontSm,
        "md": fontMd,
        "lg": fontLg,
        "xl": fontXl
    })

    function buttonHeight(size) {
        if (typeof size === 'number')
            return size
        const h = _buttonHeights[size]
        return h === undefined ? _buttonHeights['md'] : h
    }

    function fontSizeFor(size) {
        if (typeof size === 'number')
            return Math.round(size * 0.45)
        const s = _fontSizes[size]
        return s === undefined ? _fontSizes['md'] : s
    }

    function colorOf(name) {
        const c = _colors[name]
        return c === undefined ? primary : c
    }

    // 根据背景色返回可读前景色（深底白字 / 浅底深字）
    function contrast(c) {
        const y = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b
        return y > 0.55 ? '#1C1C1C' : '#FFFFFF'
    }
}
