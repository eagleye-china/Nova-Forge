"""
从设计 token 生成 QML 主题单例。

用法::

    python tools/gen_theme.py           # 生成 Theme.qml
    python tools/gen_theme.py --check   # 仅校验，产物与真源不一致则退出码 1（CI 用）

产物：``src/pyside_nova/qml/Nova/Theme.qml``
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # noqa: E402

from pyside_nova.theme import tokens  # noqa: E402

OUT_FILE = ROOT / "src" / "pyside_nova" / "qml" / "Nova" / "Theme.qml"


def render() -> str:
    """按 token 渲染 Theme.qml 文本（扁平属性，便于 qmllint 静态分析）。"""
    lines: list[str] = [
        "pragma Singleton",
        "import QtQuick",
        "",
        "// ⚠️ 自动生成文件，请勿手工修改。",
        "// 真源：src/pyside_nova/theme/tokens.py",
        "// 重新生成：python tools/gen_theme.py",
        "",
        "QtObject {",
        "    id: root",
        "",
        '    // 当前主题模式："light" / "dark"，由 Python 侧 NovaThemeManager 同步',
        '    property string mode: "light"',
        "",
        "    // ── 语义颜色（明暗二选一，切换 mode 自动重算）",
    ]

    for name in tokens.COLOR_NAMES:
        light = tokens.LIGHT[name]
        dark = tokens.DARK[name]
        lines.append(f'    readonly property color {name}: mode === "dark" ? "{dark}" : "{light}"')
    lines.append("")

    lines.append("    readonly property var _colors: ({")
    for index, name in enumerate(tokens.COLOR_NAMES):
        comma = "" if index == len(tokens.COLOR_NAMES) - 1 else ","
        lines.append(f'        "{name}": {name}{comma}')
    lines.append("    })")
    lines.append("")

    lines.append("    // ── 间距（dp）")
    for key, value in tokens.SPACING.items():
        lines.append(f"    readonly property int space{key.capitalize()}: {value}")
    lines.append("")

    lines.append("    // ── 圆角（dp）")
    for key, value in tokens.RADIUS.items():
        lines.append(f"    readonly property int radius{key.capitalize()}: {value}")
    lines.append("")

    lines.append("    // ── 字号")
    for key, value in tokens.TYPOGRAPHY.items():
        lines.append(f"    readonly property int font{key.capitalize()}: {value}")
    lines.append("")

    lines.append("    // ── 动效时长（ms）")
    for key, value in tokens.MOTION.items():
        lines.append(f"    readonly property int duration{key.capitalize()}: {value}")
    lines.append("")

    heights = ", ".join(f'"{k}": {v}' for k, v in tokens.BUTTON_HEIGHTS.items())
    lines.append(f"    readonly property var _buttonHeights: ({{ {heights} }})")
    lines.append("")
    lines.append("    readonly property var _fontSizes: ({")
    for index, (key, _value) in enumerate(tokens.TYPOGRAPHY.items()):
        comma = "" if index == len(tokens.TYPOGRAPHY) - 1 else ","
        lines.append(f'        "{key}": font{key.capitalize()}{comma}')
    lines.append("    })")
    lines.append("")

    lines.append("    function buttonHeight(size) {")
    lines.append("        if (typeof size === 'number')")
    lines.append("            return size")
    lines.append("        const h = _buttonHeights[size]")
    lines.append("        return h === undefined ? _buttonHeights['md'] : h")
    lines.append("    }")
    lines.append("")
    lines.append("    function fontSizeFor(size) {")
    lines.append("        if (typeof size === 'number')")
    lines.append("            return Math.round(size * 0.45)")
    lines.append("        const s = _fontSizes[size]")
    lines.append("        return s === undefined ? _fontSizes['md'] : s")
    lines.append("    }")
    lines.append("")
    lines.append("    function colorOf(name) {")
    lines.append("        const c = _colors[name]")
    lines.append("        return c === undefined ? primary : c")
    lines.append("    }")
    lines.append("")
    lines.append("    // 根据背景色返回可读前景色（深底白字 / 浅底深字）")
    lines.append("    function contrast(c) {")
    lines.append("        const y = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b")
    lines.append("        return y > 0.55 ? '#1C1C1C' : '#FFFFFF'")
    lines.append("    }")
    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    content = render()

    if check_only:
        current = OUT_FILE.read_text(encoding="utf-8") if OUT_FILE.exists() else ""
        if current != content:
            print(f"[FAIL] {OUT_FILE} 与 tokens.py 不一致，请运行 python tools/gen_theme.py", file=sys.stderr)
            return 1
        print(f"[OK] {OUT_FILE} 已与 tokens.py 同步")
        return 0

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(content, encoding="utf-8")
    print(f"[OK] 已生成 {OUT_FILE}（{len(content.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
