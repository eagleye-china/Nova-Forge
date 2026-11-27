# src/nova_forge/templates/tmpl_host_main_qml.py
# 创建时间：星期四 2026-11-26 15:34 · 重命名 2026-11-26 22:05（tmpl_main_qml → 语义自证）
"""生成**被孵化应用**的 Main.qml：NovaIncubator 七槽全注入 + 所选组合根舞台。

归属说明（CSA 2026-11-26 反馈「tmpl_main_qml 不知是谁的」）：本模板产出的是
prescript 孵化出的那个应用的七槽宿主主窗口，与 nova-forge 自身 GUI
（``ui/qml/prescript_main.qml``，nova-forge 自身界面）无关，故定名 ``tmpl_host_main_qml.py``。

七槽各司其职（与 pyside-nova 孵化器「无业务语义骨架」契约一致）：
globalSlot  应用身份 / 配方代号 / 主题与封版入口
recipeSlot  九类配方库（当前装载 / 其余可孵化）
stageSlot   所选组合根的完整业务舞台（Stage.qml）
validateSlot 三重校验 + 性能承诺
pipelineSlot CARF 四阶段进度
certificateSlot 封版证书（配方 / 壳 / API 契约 / 生成器）
overlaySlot 人工确认闸门（只有点了才「封版」）
"""

from __future__ import annotations

from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 仅作类型注解（文件启用 from __future__ import annotations，注解为惰性字符串）。
    # 运行期不导入：prescript.render 会在 prescript 包初始化时反过来导入本模块，
    # 直接导入 ..prescript.catalog 会形成循环导入（冷启动先 import 本模块必炸）。
    from ..prescript.catalog import Kind

MAIN_QML = Template(
    """// Main.qml · ${app}（nova-forge prescript · 配方 ${recipe} · ${shell}）
// 由 nova-forge 生成：七槽全部注入真实业务内容，布局职责仍归 NovaIncubator。
// 生成器：nova-forge prescript --kind ${code}
import QtQuick
import QtQuick.Controls
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

ApplicationWindow {
    id: win
    width: ${w}
    height: ${h}
    minimumWidth: ${mw}
    minimumHeight: ${mh}
    visible: true
    title: "${app} · ${kind_zh}"
    color: NovaTheme.page

    // 专属态（深底 + 组合根专属色相，默认） / 亮色态（浅底 + 全局品牌蓝）
    property string themeMode: "signature"
    // Windows 原生标题栏不随 QML 主题变化；emit 信号由 main.py 同步 DWM 明暗。
    // 无监听者时 emit 无害（离屏实跑亦 0 ERROR），故本模板不依赖任何 context property。
    signal darkChromeChanged(bool dark)
    onThemeModeChanged: {
        NovaTheme.setDark(win.themeMode === "signature")
        darkChromeChanged(win.themeMode === "signature")
    }

    property int stageIndex: 1
    property bool gateOpen: false
    property bool frozen: false
    property string hint: "（点击左侧任一未装载配方可查看孵化命令）"

    readonly property var presets: ${presets_js}
    readonly property var checks: ${checks_js}
    readonly property var metrics: ${metrics_js}
    readonly property var deliverables: ${deliverables_js}
    readonly property var stages: ["Conceive 构想", "Achieve 实现", "Refine 打磨", "Freeze 封版"]

    Component.onCompleted: {
        NovaScreen.source = win
        NovaTheme.setDark(win.themeMode === "signature")
        darkChromeChanged(true)   // 初始按专属暗色态同步原生标题栏
    }

    function toggleTheme() {
        win.themeMode = (win.themeMode === "signature") ? "light" : "signature"
    }
    function seal() {
        if (win.frozen) return
        win.gateOpen = true
    }
    function confirmSeal() {
        win.frozen = true
        win.gateOpen = false
        win.stageIndex = 4
    }
    function pick(p) {
        if (p.loaded) {
            win.hint = "当前装载：" + p.code + " · " + p.zh
        } else {
            win.hint = "孵化此配方：nova-forge prescript --kind " + p.kind + " --path <新目录>"
        }
    }

    NovaIncubator {
        id: shell
        anchors.fill: parent
        _signatureOn: win.themeMode === "signature"
        onFreezeRequested: win.seal()

        // ① 应用身份 / 配方 / 主题 / 封版入口
        globalSlot: Item {
            anchors.fill: parent
            Rectangle {
                id: brand
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                width: 24; height: 24; radius: 7
                color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.18)
                border.width: 1
                border.color: NovaTheme.primary
                Text {
                    anchors.centerIn: parent
                    text: "${initial}"
                    color: NovaTheme.primaryText
                    font { pixelSize: 11; bold: true }
                }
            }
            Column {
                anchors { left: brand.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 1
                Text {
                    text: "${app}"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "${recipe} · ${shell} · ${tagline}"
                    color: NovaTheme.textMuted
                    font.pixelSize: 9
                }
            }
            Row {
                anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: 92; height: 26; radius: 13
                    color: win.frozen
                        ? Qt.rgba(NovaTheme.positive.r, NovaTheme.positive.g, NovaTheme.positive.b, 0.18)
                        : Qt.rgba(NovaTheme.warning.r, NovaTheme.warning.g, NovaTheme.warning.b, 0.16)
                    Text {
                        anchors.centerIn: parent
                        text: win.frozen ? "已封版" : "待封版"
                        color: win.frozen ? NovaTheme.positiveText : NovaTheme.warningText
                        font { pixelSize: 9; bold: true }
                    }
                }
                Rectangle {
                    width: 26; height: 26; radius: 13
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors.centerIn: parent
                        text: win.themeMode === "signature" ? "◐" : "◑"
                        color: NovaTheme.textColor
                        font.pixelSize: 11
                    }
                    MouseArea { anchors.fill: parent; onClicked: win.toggleTheme() }
                }
                Rectangle {
                    width: 72; height: 26; radius: 8
                    color: win.frozen ? NovaTheme.surfaceAlt : NovaTheme.primary
                    Text {
                        anchors.centerIn: parent
                        text: win.frozen ? "证书" : "请求封版"
                        color: win.frozen ? NovaTheme.textColor : NovaTheme.textOnPrimary
                        font { pixelSize: 9; bold: true }
                    }
                    MouseArea { anchors.fill: parent; onClicked: shell.requestFreeze() }
                }
            }
        }

        // ② 九类配方库：当前装载高亮，其余标注可孵化命令
        recipeSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 8
                Text {
                    text: "配方库"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "nova-forge prescript · 九类应用"
                    color: NovaTheme.textMuted
                    font.pixelSize: 9
                }
                Repeater {
                    model: win.presets
                    Rectangle {
                        required property var modelData
                        width: parent.width
                        height: 50
                        radius: NovaTheme.radiusM
                        color: modelData.loaded
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                            : "transparent"
                        border.width: 1
                        border.color: modelData.loaded ? NovaTheme.primary : "transparent"
                        Text {
                            anchors { left: parent.left; leftMargin: 9; right: parent.right; rightMargin: 9; top: parent.top; topMargin: 7 }
                            text: modelData.code + " · " + modelData.zh
                            color: NovaTheme.textColor
                            elide: Text.ElideRight
                            font { pixelSize: 10; bold: modelData.loaded }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 9; right: parent.right; rightMargin: 9; top: parent.top; topMargin: 26 }
                            text: modelData.loaded ? "已装载 · " + modelData.shell : modelData.shell + " · 可孵化"
                            color: modelData.loaded ? NovaTheme.primaryText : NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 8
                        }
                        MouseArea { anchors.fill: parent; onClicked: win.pick(modelData) }
                    }
                }
            }
        }

        // ③ 舞台：所选组合根的完整业务界面
        stageSlot: Item {
            anchors.fill: parent
            Stage {
                anchors.fill: parent
                signatureOn: win.themeMode === "signature"
            }
        }

        // ④ 三重校验 + 性能承诺
        validateSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 8
                Text {
                    text: "三重校验"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Repeater {
                    model: win.checks
                    Rectangle {
                        required property var modelData
                        width: parent.width
                        height: 56
                        radius: NovaTheme.radiusM
                        color: NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: NovaTheme.outline
                        Text {
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 8 }
                            text: modelData.k
                            color: NovaTheme.textColor
                            font { pixelSize: 9; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 46; top: parent.top; topMargin: 26 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 8
                        }
                        Rectangle {
                            anchors { right: parent.right; rightMargin: 9; top: parent.top; topMargin: 8 }
                            width: 40; height: 15; radius: 7
                            color: Qt.rgba(NovaTheme.positive.r, NovaTheme.positive.g, NovaTheme.positive.b, 0.18)
                            Text {
                                anchors.centerIn: parent
                                text: "PASS"
                                color: NovaTheme.positiveText
                                font { pixelSize: 8; bold: true }
                            }
                        }
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 1
                    color: NovaTheme.outline
                }
                Text {
                    text: "性能承诺"
                    color: NovaTheme.textMuted
                    font { pixelSize: 8; bold: true }
                }
                Repeater {
                    model: win.metrics
                    Item {
                        required property var modelData
                        width: parent.width
                        height: 20
                        Text {
                            anchors { left: parent.left; verticalCenter: parent.verticalCenter }
                            text: modelData.k
                            color: NovaTheme.textMuted
                            font.pixelSize: 8
                        }
                        Text {
                            anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                            text: modelData.v
                            color: NovaTheme.textColor
                            font { pixelSize: 8; bold: true }
                        }
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 1
                    color: NovaTheme.outline
                }
                Text {
                    width: parent.width
                    text: win.hint
                    color: NovaTheme.primaryText
                    wrapMode: Text.WordWrap
                    font.pixelSize: 8
                }
            }
        }

        // ⑤ CARF 四阶段
        pipelineSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 10
                Repeater {
                    model: win.stages
                    Row {
                        required property string modelData
                        required property int index
                        spacing: 6
                        Rectangle {
                            width: 8; height: 8; radius: 4
                            color: index < win.stageIndex ? NovaTheme.primary
                                 : index === win.stageIndex ? NovaTheme.primary : NovaTheme.outline
                            opacity: index <= win.stageIndex ? 1 : 0.5
                        }
                        Text {
                            text: modelData
                            color: index <= win.stageIndex ? NovaTheme.textColor : NovaTheme.textMuted
                            font { pixelSize: 9; bold: index === win.stageIndex }
                        }
                    }
                }
            }
        }

        // ⑥ 封版证书（宽度自适应：孵化器证书区实际只有舞台宽度）
        certificateSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; top: parent.top; topMargin: 10 }
                spacing: 10
                Column {
                    width: 200
                    spacing: 3
                    Text {
                        text: "封版证书 · ${recipe}"
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontS; bold: true }
                    }
                    Text {
                        text: "${app}"
                        color: NovaTheme.primaryText
                        elide: Text.ElideRight
                        width: parent.width
                        font.pixelSize: 9
                    }
                    Text {
                        width: parent.width
                        text: "壳 ${shell} · API ${api_version} · ${forge_version}"
                        color: NovaTheme.textMuted
                        wrapMode: Text.WordWrap
                        font.pixelSize: 8
                    }
                }
                Flow {
                    width: Math.max(140, parent.width - 210)
                    spacing: 8
                    Repeater {
                        model: win.deliverables
                        Column {
                            required property var modelData
                            width: (parent.width - 8) / 2
                            spacing: 2
                            Text {
                                text: modelData.k
                                color: NovaTheme.textMuted
                                font { pixelSize: 8; bold: true }
                            }
                            Text {
                                text: modelData.d
                                color: NovaTheme.textColor
                                elide: Text.ElideRight
                                width: parent.width
                                font.pixelSize: 8
                            }
                        }
                    }
                }
            }
        }

        // ⑦ 人工确认闸门：只有点了才封版
        overlaySlot: Item {
            anchors.fill: parent
            visible: win.gateOpen
            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(0, 0, 0, 0.45)
                MouseArea { anchors.fill: parent }
            }
            Rectangle {
                anchors.centerIn: parent
                width: Math.min(420, parent.width - 48)
                height: 196
                radius: NovaTheme.radiusL
                color: NovaTheme.surface
                border.width: 1
                border.color: NovaTheme.outline
                Column {
                    anchors { left: parent.left; leftMargin: 20; right: parent.right; rightMargin: 20; top: parent.top; topMargin: 18 }
                    spacing: 8
                    Text {
                        text: "确认封版？"
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontM; bold: true }
                    }
                    Text {
                        width: parent.width
                        text: "封版后将签发 ${recipe} 证书并锁定配方快照；之后修改需重新走 CARF。"
                        color: NovaTheme.textMuted
                        wrapMode: Text.WordWrap
                        font.pixelSize: 10
                    }
                    Row {
                        spacing: 8
                        Text {
                            text: "三重校验 3/3 PASS"
                            color: NovaTheme.positiveText
                            font { pixelSize: 9; bold: true }
                        }
                        Text {
                            text: "· 影响范围仅本地工程"
                            color: NovaTheme.textMuted
                            font.pixelSize: 9
                        }
                    }
                    Row {
                        spacing: 10
                        Rectangle {
                            width: 84; height: 30; radius: 8
                            color: "transparent"
                            border.width: 1
                            border.color: NovaTheme.outline
                            Text {
                                anchors.centerIn: parent
                                text: "取消"
                                color: NovaTheme.textColor
                                font.pixelSize: 10
                            }
                            MouseArea { anchors.fill: parent; onClicked: win.gateOpen = false }
                        }
                        Rectangle {
                            width: 104; height: 30; radius: 8
                            color: NovaTheme.primary
                            Text {
                                anchors.centerIn: parent
                                text: "确认封版"
                                color: NovaTheme.textOnPrimary
                                font { pixelSize: 10; bold: true }
                            }
                            MouseArea { anchors.fill: parent; onClicked: win.confirmSeal() }
                        }
                    }
                }
            }
        }
    }
}
"""
)


def build_main_qml(
    kind: Kind,
    app_name: str,
    presets: list[dict],
    api_version: str,
    forge_version: str,
) -> str:
    """把配方规格渲染成 Main.qml 文本。"""
    initial = kind.zh[:1]
    return MAIN_QML.substitute(
        app=_escape(app_name),
        initial=initial,
        kind_zh=_escape(kind.zh),
        code=kind.code,
        recipe=kind.recipe,
        shell=kind.shell,
        tagline=_escape(kind.tagline),
        w=kind.size[0],
        h=kind.size[1],
        mw=kind.minimum[0],
        mh=kind.minimum[1],
        presets_js=_js_array(presets),
        checks_js=_js_array([
            {"k": "配方合规", "d": "七区完整 · 配方 " + kind.recipe},
            {"k": "契约合规", "d": "槽位边界 + 壳契约 " + kind.shell},
            {"k": "门禁合规", "d": kind.gates[0][0] + " · " + kind.gates[1][0]},
        ]),
        metrics_js=_js_array([{"k": k, "v": v} for k, v in kind.metrics]),
        deliverables_js=_js_array([{"k": k, "d": d} for k, d in kind.deliverables]),
        api_version=api_version,
        forge_version=forge_version,
    )


def _escape(text: str) -> str:
    """QML 字符串转义：只处理会破坏字符串的双引号与反斜杠。"""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _js_array(rows: list[dict]) -> str:
    """把 Python 字典列表渲染成 QML 可读的 JS 数组字面量（键加引号，值转义）。"""
    if not rows:
        return "[]"
    parts = []
    for row in rows:
        cells = []
        for key, value in row.items():
            if isinstance(value, bool):
                cells.append(f'"{key}": {"true" if value else "false"}')
            else:
                cells.append(f'"{key}": "{_escape(str(value))}"')
        parts.append("{ " + ", ".join(cells) + " }")
    return "[\n        " + ",\n        ".join(parts) + "\n    ]"
