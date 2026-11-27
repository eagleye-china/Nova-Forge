# scripts/gen_app_icons.py
# 创建时间：星期五 2026-11-27 06:55
"""生成 11 个专属主题组合根的「应用图标」SVG（幂等 · 单一事实源）。

十一个组件 = 九配方壳（catalog.KINDS）+ NovaIncubator（孵化器工作台自身）
+ NovaAIReport（T24 第 21 组合根）。
色相 ``hue`` 直接取自 ``catalog``，与十一主题色相台账一致，禁止在图标里另写死色值。

设计约束（对齐品牌规范「克制矢量派」+ Aurora Core 亮核）：
- 纯几何 path / 基本形状，**无 text / textPath**（QtSvg 不渲染 textPath）；
- 无 SVG 渐变（Qt 6.12 QML 侧 RadialGradient 不可用，图标侧一并不用，保证离屏可渲染）；
- 统一深色圆角底 + 专属色相环 + 中性白芯 + 各自语义符号 + 底部身份色带；
- 同一组件一个语义符号，十枚可辨识、成套。

用法：
    python scripts/gen_app_icons.py            # 生成（已存在且内容一致则跳过）
    python scripts/gen_app_icons.py --check    # 只校验，不落盘；不一致 exit 1
"""
from __future__ import annotations

import colorsys
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nova_forge.prescript.catalog import (  # noqa: E402
    AI_REPORT_CODE,
    AI_REPORT_HUE,
    AI_REPORT_ICON,
    AI_REPORT_SHELL,
    AI_REPORT_ZH,
    INCUBATOR_HUE,
    INCUBATOR_ICON,
    INCUBATOR_SHELL,
    KINDS,
)

OUT_DIR = SRC / "nova_forge" / "resources" / "icons"
# 供 prescript 产物内嵌的 SVG 文本常量（产物是独立工程，不能依赖 nova-forge 运行时）
CONSTANTS_PY = SRC / "nova_forge" / "resources" / "app_icons.py"

# 不属九配方、但同属专属主题组合根的两枚附加组件（色相取自 catalog 单一事实源）
INCUBATOR = ("incubator", INCUBATOR_SHELL, INCUBATOR_HUE, "应用孵化器工作台")
AI_REPORT = (AI_REPORT_CODE, AI_REPORT_SHELL, AI_REPORT_HUE, AI_REPORT_ZH)
EXTRA_SPECS = (INCUBATOR, AI_REPORT)

# 十一枚图标的语义符号（256×256 坐标系，中心 128,124）。{c} = 专属色相亮色
GLYPHS: dict[str, str] = {
    # 智能体任务台：任务准入 → 计划 → 执行轨迹 → 独立验证勾
    "agent": """
  <path d="M52 170 L94 132 L136 152 L188 96" fill="none" stroke="{c}" stroke-width="10"
        stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="52" cy="170" r="13" fill="#FFFFFF"/>
  <circle cx="94" cy="132" r="13" fill="{c}"/>
  <circle cx="136" cy="152" r="13" fill="{c}"/>
  <path d="M180 96 l11 11 l22 -25" fill="none" stroke="#FFFFFF" stroke-width="10"
        stroke-linecap="round" stroke-linejoin="round"/>""",
    # 协作副驾：双栏 + 内联补全光标（不抢焦）
    "copilot": """
  <rect x="46" y="70" width="66" height="116" rx="11" fill="none" stroke="{c}" stroke-width="9"/>
  <rect x="128" y="70" width="82" height="116" rx="11" fill="none" stroke="{c}" stroke-width="9"/>
  <rect x="60" y="92" width="38" height="8" rx="4" fill="#FFFFFF" opacity="0.85"/>
  <rect x="60" y="114" width="30" height="8" rx="4" fill="#FFFFFF" opacity="0.5"/>
  <rect x="142" y="92" width="54" height="8" rx="4" fill="#FFFFFF" opacity="0.85"/>
  <rect x="142" y="114" width="40" height="8" rx="4" fill="#FFFFFF" opacity="0.5"/>
  <rect x="142" y="140" width="13" height="11" rx="2" fill="{c}"/>""",
    # 数字员工队伍：三张角色卡 + 队列
    "de": """
  <g fill="none" stroke="{c}" stroke-width="9" stroke-linecap="round">
    <rect x="44" y="72" width="48" height="112" rx="10"/>
    <rect x="104" y="72" width="48" height="112" rx="10"/>
    <rect x="164" y="72" width="48" height="112" rx="10"/>
  </g>
  <circle cx="68" cy="106" r="11" fill="#FFFFFF"/>
  <circle cx="128" cy="106" r="11" fill="#FFFFFF"/>
  <circle cx="188" cy="106" r="11" fill="#FFFFFF"/>
  <path d="M56 148 h24 M116 148 h24 M176 148 h24" stroke="#FFFFFF" stroke-width="8"
        opacity="0.6" stroke-linecap="round"/>""",
    # 意图轨道：双层轨道 + 入轨节点 + 白芯
    "orbit": """
  <ellipse cx="128" cy="124" rx="92" ry="52" fill="none" stroke="{c}" stroke-width="9"
           transform="rotate(-24 128 124)"/>
  <ellipse cx="128" cy="124" rx="56" ry="30" fill="none" stroke="{c}" stroke-width="7"
           opacity="0.55" transform="rotate(-24 128 124)"/>
  <circle cx="128" cy="124" r="17" fill="#FFFFFF"/>
  <circle cx="198" cy="92" r="12" fill="{c}"/>""",
    # 企业桌面：菜单树 / 工具栏 / 内容区 / 状态栏四分区
    "desktop": """
  <rect x="42" y="64" width="172" height="128" rx="13" fill="none" stroke="{c}" stroke-width="9"/>
  <path d="M42 94 H214 M94 94 V192" stroke="{c}" stroke-width="7" fill="none"/>
  <rect x="108" y="108" width="90" height="14" rx="4" fill="#FFFFFF" opacity="0.85"/>
  <rect x="108" y="134" width="62" height="12" rx="4" fill="#FFFFFF" opacity="0.55"/>
  <rect x="108" y="158" width="78" height="12" rx="4" fill="#FFFFFF" opacity="0.4"/>
  <rect x="42" y="182" width="172" height="10" fill="{c}" opacity="0.7"/>""",
    # AI 对话工作台：会话气泡 + 三点消息
    "chat": """
  <path d="M44 76 h116 a16 16 0 0 1 16 16 v46 a16 16 0 0 1 -16 16 h-52 l-28 24 v-24
           h-36 a16 16 0 0 1 -16 -16 v-46 a16 16 0 0 1 16 -16 z"
        fill="none" stroke="{c}" stroke-width="9" stroke-linejoin="round"/>
  <circle cx="86" cy="115" r="8" fill="#FFFFFF"/>
  <circle cx="118" cy="115" r="8" fill="#FFFFFF"/>
  <circle cx="150" cy="115" r="8" fill="#FFFFFF"/>""",
    # 移动触控应用：手机框 + 底部拇指导航 + 安全区
    "mobile": """
  <rect x="80" y="44" width="96" height="168" rx="19" fill="none" stroke="{c}" stroke-width="9"/>
  <rect x="112" y="58" width="32" height="6" rx="3" fill="#FFFFFF" opacity="0.6"/>
  <rect x="96" y="174" width="64" height="9" rx="4" fill="{c}"/>
  <circle cx="128" cy="196" r="8" fill="#FFFFFF"/>""",
    # 工业大屏：1~4 栏断点栅格
    "flex": """
  <rect x="42" y="70" width="46" height="116" rx="7" fill="{c}" opacity="0.9"/>
  <rect x="96" y="70" width="46" height="54" rx="7" fill="#FFFFFF" opacity="0.85"/>
  <rect x="96" y="132" width="46" height="54" rx="7" fill="#FFFFFF" opacity="0.5"/>
  <rect x="150" y="70" width="64" height="78" rx="7" fill="{c}" opacity="0.55"/>
  <rect x="150" y="156" width="64" height="30" rx="7" fill="#FFFFFF" opacity="0.7"/>""",
    # 部署向导：五步流程条 + 终审勾
    "wizard": """
  <path d="M52 124 H204" stroke="{c}" stroke-width="8" stroke-linecap="round" opacity="0.6"/>
  <circle cx="56" cy="124" r="13" fill="#FFFFFF"/>
  <circle cx="106" cy="124" r="13" fill="#FFFFFF"/>
  <circle cx="156" cy="124" r="13" fill="{c}"/>
  <path d="M186 110 l11 12 l22 -25" fill="none" stroke="#FFFFFF" stroke-width="10"
        stroke-linecap="round" stroke-linejoin="round"/>""",
    # 应用孵化器：七芒小太阳 + 同心亮核（对应徽记「界面预览」）
    "incubator": """
  <g stroke="{c}" stroke-width="9" stroke-linecap="round">
    <path d="M128 42 V70"/><path d="M128 178 V206"/>
    <path d="M50 124 H78"/><path d="M178 124 H206"/>
    <path d="M73 69 L93 89"/><path d="M163 159 L183 179"/>
    <path d="M183 69 L163 89"/><path d="M93 159 L73 179"/>
  </g>
  <circle cx="128" cy="124" r="34" fill="none" stroke="#FFFFFF" stroke-width="9"/>
  <circle cx="128" cy="124" r="12" fill="#FFFFFF"/>""",
    # 智能报表工作台：四柱报表栅格 + 趋势折线 + 对标游标 + 中性白芯
    # 抽象几何，不仿表格控件 / 图表控件；与其余十枚同套（深色圆角底 + 色相环 + 底部身份色带）
    "aireport": """
  <path d="M46 188 H210" stroke="{c}" stroke-width="8" stroke-linecap="round" opacity="0.55"/>
  <rect x="58"  y="132" width="24" height="46"  rx="4" fill="{c}" opacity="0.85"/>
  <rect x="96"  y="106" width="24" height="72"  rx="4" fill="{c}" opacity="0.60"/>
  <rect x="134" y="120" width="24" height="58"  rx="4" fill="{c}" opacity="0.85"/>
  <rect x="172" y="74"  width="24" height="104" rx="4" fill="#FFFFFF" opacity="0.85"/>
  <path d="M70 124 L108 94 L146 106 L184 58" fill="none" stroke="#FFFFFF" stroke-width="8"
        stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="184" cy="58" r="12" fill="{c}"/>""",
}


def hsl(hue: int, sat: float, light: float) -> str:
    """色相（度）→ #RRGGBB。十进制色相是唯一入参，避免图标里另立色值台账。"""
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, light, sat)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def icon_filename(code: str) -> str:
    return f"app-{code}.svg"


def all_specs() -> list[tuple[str, str, int, str]]:
    """11 个组件 → (code, shell, hue, 中文名)。九配方来自 catalog，另两枚为附加组合根。"""
    specs = [(k.code, k.shell, k.hue, k.zh) for k in KINDS]
    specs.extend(EXTRA_SPECS)
    # 账实相符：附加两枚的图标文件名必须与 catalog 常量逐字一致
    assert icon_filename(INCUBATOR[0]) == INCUBATOR_ICON
    assert icon_filename(AI_REPORT[0]) == AI_REPORT_ICON
    return specs


def render_svg(code: str, shell: str, hue: int, zh: str) -> str:
    ring = hsl(hue, 0.72, 0.52)
    core = hsl(hue, 0.86, 0.68)
    glyph = GLYPHS[code].format(c=core)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- app-{code}.svg · {shell}（{zh}）· hue {hue}° · 由 scripts/gen_app_icons.py 生成，禁手改 -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect x="8" y="8" width="240" height="240" rx="56" fill="#0D1424"/>
  <rect x="8" y="8" width="240" height="240" rx="56" fill="none"
        stroke="{ring}" stroke-width="4" opacity="0.9"/>
  <circle cx="128" cy="124" r="92" fill="{ring}" opacity="0.10"/>
  <circle cx="128" cy="124" r="70" fill="{ring}" opacity="0.10"/>
{glyph}
  <rect x="92" y="226" width="72" height="7" rx="3" fill="{core}"/>
</svg>
'''


def constants_module(specs: list[tuple[str, str, int, str]]) -> str:
    """产出纯 Python 常量模块：供 prescript 产物把图标 SVG 内嵌进自己的工程。

    产物是独立工程（只依赖 pyside-nova），运行时读不到 nova-forge 的 qrc，
    因此落盘时把 SVG 文本直接写进产物 ``src/<pkg>/assets/app-<code>.svg``。
    本模块即该文本的唯一事实源，与 ``resources/icons/`` 由同一次生成产出。
    """
    lines = [
        "# src/nova_forge/resources/app_icons.py",
        "# 由 scripts/gen_app_icons.py 生成，禁手改。",
        '"""11 个专属主题组合根的应用图标 SVG 文本（供 prescript 产物内嵌）。"""',
        "from __future__ import annotations",
        "",
        "ICONS: dict[str, str] = {",
    ]
    for code, shell, hue, zh in specs:
        name = icon_filename(code)
        lines.append(f"    # {shell} · {zh} · hue {hue}°")
        lines.append(f"    {name!r}: {render_svg(code, shell, hue, zh)!r},")
    lines += ["}", "", ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = all_specs()
    drift: list[str] = []
    for code, shell, hue, zh in specs:
        path = OUT_DIR / icon_filename(code)
        text = render_svg(code, shell, hue, zh)
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        drift.append(icon_filename(code))
        if not check:
            path.write_text(text, encoding="utf-8")

    module_text = constants_module(specs)
    if not CONSTANTS_PY.exists() or CONSTANTS_PY.read_text(encoding="utf-8") != module_text:
        drift.append(CONSTANTS_PY.name)
        if not check:
            CONSTANTS_PY.write_text(module_text, encoding="utf-8")

    if check:
        if drift:
            print(f"[check] ✗ {len(drift)} 项与单一事实源不一致：{', '.join(drift)}")
            return 1
        print(f"[check] ✓ {len(specs)} 枚应用图标 + 常量模块与 catalog 色相台账一致")
        return 0

    print(f"[gen] {len(specs)} 枚应用图标 + 常量模块已同步 · {len(drift)} 项写入 · 目录 {OUT_DIR}")
    for code, shell, hue, _ in specs:
        print(f"  {icon_filename(code):24s} {shell:20s} hue {hue}°")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
