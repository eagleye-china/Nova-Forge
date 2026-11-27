# src/nova_forge/prescript/stages.py
# 创建时间：星期四 2026-11-26 15:26
"""九个舞台源码：每个组合根一个真实业务界面（Stage.qml）。

约束：
- 只用 QtQuick + Nova.Services + Nova.Controls + Nova.Composite.LayoutShell，
  与 pyside-nova 官方 demo 同一写法（手绘几何 + 设计令牌），不依赖未公开属性。
- 舞台只做「业务内容」，布局职责全部交给组合根；槽位按壳的公开 alias 注入。
- 全部交互为本地状态机，不联网、不隐式写盘，与孵化器「人工闸门」治理口径一致。
"""

STAGES: dict[str, str] = {}

# ── P1 · NovaAgent 智能体任务台 ─────────────────────────────────────────────
STAGES["agent"] = """// Stage.qml · NovaAgent 智能体任务台（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeTask: 0
    property bool approved: false

    readonly property var tasks: [
        { t: "季度对账差异定位", s: "执行中", p: 0.42, n: "3 张表 · 1.2 万行" },
        { t: "供应商主数据清洗", s: "待准入", p: 0.00, n: "8 个字段冲突" },
        { t: "月结凭证批量复核", s: "已完成", p: 1.00, n: "412 张凭证" },
        { t: "异常发票归因", s: "排队中", p: 0.00, n: "优先级 P1" }
    ]
    readonly property var steps: [
        { t: "读取账套", d: "finance.ledger · 只读", s: "done" },
        { t: "对齐科目", d: "科目映射表 v3", s: "done" },
        { t: "差异聚类", d: "按供应商 + 金额带", s: "run" },
        { t: "生成调整建议", d: "需人工审批后落库", s: "wait" }
    ]
    readonly property var verifies: [
        { t: "行数守恒", d: "入 12,480 = 出 12,480", s: "PASS" },
        { t: "金额守恒", d: "差额 0.00", s: "PASS" },
        { t: "抽样复核", d: "20 / 20 命中", s: "PASS" },
        { t: "写库影响面", d: "3 张表待批", s: "WAIT" }
    ]

    NovaAgent {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        breakpoint: 480
        onApprovalRequested: stage.approved = true

        taskSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "任务队列"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: stage.tasks.length + " 项 · 1 项执行中"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.tasks
                    Item {
                        required property var modelData
                        required property int index
                        width: parent.width
                        height: 64
                        Rectangle {
                            anchors.fill: parent
                            radius: NovaTheme.radiusM
                            color: stage.activeTask === index
                                ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.14)
                                : "transparent"
                            border.width: 1
                            border.color: stage.activeTask === index ? NovaTheme.primary : "transparent"
                        }
                        Rectangle {
                            id: dot
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 14 }
                            width: 6; height: 6; radius: 3
                            color: modelData.s === "已完成" ? NovaTheme.positive
                                 : modelData.s === "执行中" ? NovaTheme.primary
                                 : NovaTheme.textMuted
                        }
                        Text {
                            anchors { left: dot.right; leftMargin: 8; right: parent.right; top: parent.top; topMargin: 10 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            elide: Text.ElideRight
                            font { pixelSize: NovaTheme.fontS; bold: stage.activeTask === index }
                        }
                        Text {
                            anchors { left: dot.right; leftMargin: 8; right: parent.right; top: parent.top; topMargin: 30 }
                            text: modelData.n + " · " + modelData.s
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: NovaTheme.fontXS
                        }
                        Rectangle {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; bottom: parent.bottom; bottomMargin: 10 }
                            height: 2; radius: 1
                            color: NovaTheme.outline
                            Rectangle {
                                width: parent.width * modelData.p
                                height: parent.height; radius: 1
                                color: modelData.p >= 1 ? NovaTheme.positive : NovaTheme.primary
                            }
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeTask = index }
                    }
                }
            }
        }

        planSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 10
                Text {
                    y: (parent.height - height) / 2
                    text: "计划 · " + stage.steps.length + " 步"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.steps
                    Row {
                        required property var modelData
                        required property int index
                        spacing: 6
                        y: (parent.height - height) / 2
                        Rectangle {
                            width: 6; height: 6; radius: 3
                            y: (parent.height - height) / 2
                            color: modelData.s === "done" ? NovaTheme.positive
                                 : modelData.s === "run" ? NovaTheme.primary : NovaTheme.outline
                        }
                        Text {
                            y: (parent.height - height) / 2
                            text: (index + 1) + " " + modelData.t
                            color: modelData.s === "run" ? NovaTheme.textColor : NovaTheme.textMuted
                            font.pixelSize: NovaTheme.fontXS
                        }
                        Text {
                            y: (parent.height - height) / 2
                            visible: index < stage.steps.length - 1
                            text: "›"
                            color: NovaTheme.textMuted
                            font.pixelSize: NovaTheme.fontXS
                        }
                    }
                }
            }
        }

        contentSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 4 }
                spacing: 8
                Text {
                    text: "执行轨迹"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontM; bold: true }
                }
                Text {
                    text: "每一步都可回放；工具调用与证据链同行编号"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.steps
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: parent.width
                        height: 76
                        radius: NovaTheme.radiusM
                        color: modelData.s === "run"
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.10)
                            : NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: modelData.s === "run" ? NovaTheme.primary : NovaTheme.outline
                        Rectangle {
                            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                            width: 28; height: 28; radius: 8
                            color: modelData.s === "done" ? NovaTheme.positive
                                 : modelData.s === "run" ? NovaTheme.primary : "transparent"
                            border.width: 1
                            border.color: modelData.s === "wait" ? NovaTheme.outline : "transparent"
                            Text {
                                anchors.centerIn: parent
                                text: modelData.s === "done" ? "✓" : String(index + 1)
                                color: modelData.s === "wait" ? NovaTheme.textMuted : NovaTheme.textOnPrimary
                                font { pixelSize: NovaTheme.fontXS; bold: true }
                            }
                        }
                        Column {
                            anchors { left: parent.left; leftMargin: 54; right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                            spacing: 4
                            Text {
                                text: modelData.t
                                color: NovaTheme.textColor
                                font { pixelSize: NovaTheme.fontS; bold: true }
                            }
                            Text {
                                text: modelData.d
                                color: NovaTheme.textMuted
                                elide: Text.ElideRight
                                width: parent.width
                                font.pixelSize: NovaTheme.fontXS
                            }
                            Text {
                                text: modelData.s === "done" ? "已完成 · 证据已签名"
                                    : modelData.s === "run" ? "执行中 · 已调用 3 个工具"
                                    : "待人工审批后继续"
                                color: modelData.s === "run" ? NovaTheme.primary : NovaTheme.textMuted
                                elide: Text.ElideRight
                                width: parent.width
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 96
                    radius: NovaTheme.radiusM
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 10 }
                        text: "工具调用日志"
                        color: NovaTheme.textMuted
                        font { pixelSize: NovaTheme.fontXS; bold: true }
                    }
                    Column {
                        anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; top: parent.top; topMargin: 32 }
                        spacing: 4
                        Repeater {
                            model: ["ledger.read(table='ap_invoice') → 12,480 rows · 218 ms",
                                    "ledger.aggregate(by='vendor') → 412 groups · 96 ms",
                                    "diff.cluster(eps=0.01) → 37 clusters · 142 ms"]
                            Text {
                                required property string modelData
                                text: "· " + modelData
                                color: NovaTheme.textColor
                                elide: Text.ElideRight
                                width: parent.width
                                font { pixelSize: NovaTheme.fontXS; family: "Consolas" }
                            }
                        }
                    }
                }
            }
        }

        verifySlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "独立验证"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "验证器不共享执行器上下文"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.verifies
                    Item {
                        required property var modelData
                        width: parent.width
                        height: 58
                        Rectangle {
                            anchors.fill: parent
                            radius: NovaTheme.radiusM
                            color: NovaTheme.surfaceAlt
                            border.width: 1
                            border.color: NovaTheme.outline
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 9 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            font { pixelSize: NovaTheme.fontXS; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; top: parent.top; topMargin: 28 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: NovaTheme.fontXS
                        }
                        Rectangle {
                            anchors { right: parent.right; rightMargin: 10; top: parent.top; topMargin: 9 }
                            width: 42; height: 16; radius: 8
                            color: modelData.s === "PASS"
                                ? Qt.rgba(NovaTheme.positive.r, NovaTheme.positive.g, NovaTheme.positive.b, 0.18)
                                : Qt.rgba(NovaTheme.warning.r, NovaTheme.warning.g, NovaTheme.warning.b, 0.18)
                            Text {
                                anchors.centerIn: parent
                                text: modelData.s
                                color: modelData.s === "PASS" ? NovaTheme.positiveText : NovaTheme.warningText
                                font { pixelSize: 9; bold: true }
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
                    width: parent.width
                    text: "策略：金额差 > 0.01 即拒绝；写库前必须人工确认。"
                    color: NovaTheme.textMuted
                    wrapMode: Text.WordWrap
                    font.pixelSize: NovaTheme.fontXS
                }
            }
        }

        approvalSlot: Item {
            id: approvalHost
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                width: Math.max(160, approvalHost.width - 240)
                clip: true
                spacing: 10
                Rectangle {
                    width: 6; height: 6; radius: 3
                    y: (parent.height - height) / 2
                    color: NovaTheme.warning
                }
                Column {
                    width: parent.width - 20
                    y: (parent.height - height) / 2
                    spacing: 2
                    Text {
                        text: stage.approved ? "已批准 · 等待执行器落库" : "人工闸门：写库 3 张表 · 影响 412 行"
                        color: NovaTheme.textColor
                        width: parent.width
                        elide: Text.ElideRight
                        font { pixelSize: NovaTheme.fontS; bold: true }
                    }
                    Text {
                        text: stage.approved ? "审计已记录 approver=you · 可回滚" : "拒绝不会产生任何写入；批准后才执行"
                        color: NovaTheme.textMuted
                        width: parent.width
                        elide: Text.ElideRight
                        font.pixelSize: NovaTheme.fontXS
                    }
                }
            }
            Row {
                anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: 76; height: 30; radius: 8
                    color: "transparent"
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors.centerIn: parent
                        text: "拒绝"
                        color: NovaTheme.textColor
                        font.pixelSize: NovaTheme.fontXS
                    }
                    MouseArea { anchors.fill: parent; onClicked: stage.approved = false }
                }
                Rectangle {
                    width: 96; height: 30; radius: 8
                    color: stage.approved ? NovaTheme.positive : NovaTheme.primary
                    Text {
                        anchors.centerIn: parent
                        text: stage.approved ? "已批准" : "批准执行"
                        color: NovaTheme.textOnPrimary
                        font { pixelSize: NovaTheme.fontXS; bold: true }
                    }
                    MouseArea { anchors.fill: parent; onClicked: stage.approved = true }
                }
            }
        }
    }
}
"""


# ── P2 · NovaCopilot 协作副驾 ───────────────────────────────────────────────
STAGES["copilot"] = """// Stage.qml · NovaCopilot 协作副驾（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeSuggest: 0
    property bool gateOpen: false

    readonly property var suggests: [
        { t: "补全空值兜底", d: "parse_amount 缺少 None 分支", s: "强建议" },
        { t: "收窄异常捕获", d: "except Exception → ValueError", s: "强建议" },
        { t: "抽出重复分支", d: "第 42–58 行三处同构", s: "弱建议" }
    ]
    readonly property var code: [
        "def settle(rows, rate):",
        "    total = 0",
        "    for r in rows:",
        "        total += parse_amount(r['amt'])",
        "    return round(total * rate, 2)"
    ]
    readonly property var gates: [
        { t: "写入范围", d: "仅 src/billing/settle.py", s: "OK" },
        { t: "依据可追", d: "3 条引用已挂载", s: "OK" },
        { t: "单测覆盖", d: "新增 2 例待运行", s: "WAIT" }
    ]

    NovaCopilot {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        breakpoint: 480
        onActionProposed: stage.gateOpen = true

        suggestSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "建议"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "强建议优先 · 采纳前不动文件"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.suggests
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: parent.width
                        height: 72
                        radius: NovaTheme.radiusM
                        color: stage.activeSuggest === index
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.14)
                            : NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: stage.activeSuggest === index ? NovaTheme.primary : NovaTheme.outline
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; top: parent.top; topMargin: 10 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            elide: Text.ElideRight
                            font { pixelSize: NovaTheme.fontXS; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; top: parent.top; topMargin: 30 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            wrapMode: Text.WordWrap
                            elide: Text.ElideRight
                            maximumLineCount: 2
                            font.pixelSize: NovaTheme.fontXS
                        }
                        Rectangle {
                            anchors { left: parent.left; leftMargin: 10; bottom: parent.bottom; bottomMargin: 8 }
                            width: 44; height: 15; radius: 7
                            color: modelData.s === "强建议"
                                ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.18)
                                : "transparent"
                            border.width: modelData.s === "强建议" ? 0 : 1
                            border.color: NovaTheme.outline
                            Text {
                                anchors.centerIn: parent
                                text: modelData.s
                                color: modelData.s === "强建议" ? NovaTheme.primaryText : NovaTheme.textMuted
                                font { pixelSize: 9; bold: true }
                            }
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeSuggest = index }
                    }
                }
            }
        }

        inlineSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: 4; height: 16; radius: 2
                    y: (parent.height - height) / 2
                    color: NovaTheme.primary
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "内联 · " + stage.suggests[stage.activeSuggest].t
                    color: NovaTheme.textColor
                    font.pixelSize: NovaTheme.fontXS
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "Tab 采纳 · Esc 忽略（不夺输入焦点）"
                    color: NovaTheme.textMuted
                    font.pixelSize: 10
                }
            }
        }

        contentSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 4 }
                spacing: 10
                Row {
                    spacing: 8
                    Text {
                        text: "settle.py"
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontM; bold: true }
                    }
                    Text {
                        y: (parent.height - height) / 2
                        text: "· 修改中"
                        color: NovaTheme.warning
                        font.pixelSize: NovaTheme.fontXS
                    }
                }
                Rectangle {
                    width: parent.width
                    height: Math.max(120, lineCol.implicitHeight + 24)
                    radius: NovaTheme.radiusM
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Column {
                        id: lineCol
                        anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12; top: parent.top; topMargin: 12 }
                        spacing: 5
                        Repeater {
                            model: stage.code
                            Row {
                                required property string modelData
                                required property int index
                                spacing: 10
                                Text {
                                    width: 18
                                    horizontalAlignment: Text.AlignRight
                                    text: String(index + 1)
                                    color: NovaTheme.textMuted
                                    font { pixelSize: NovaTheme.fontXS; family: "Consolas" }
                                }
                                Text {
                                    text: modelData
                                    color: index === 3 ? NovaTheme.warning : NovaTheme.textColor
                                    font { pixelSize: NovaTheme.fontXS; family: "Consolas" }
                                }
                            }
                        }
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 84
                    radius: NovaTheme.radiusM
                    color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.08)
                    border.width: 1
                    border.color: NovaTheme.primary
                    Text {
                        anchors { left: parent.left; leftMargin: 12; top: parent.top; topMargin: 10 }
                        text: "拟改动 · 采纳后预览"
                        color: NovaTheme.textMuted
                        font { pixelSize: 9; bold: true }
                    }
                    Text {
                        anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12; top: parent.top; topMargin: 30 }
                        text: "+        if r['amt'] is None:\\n+            continue"
                        color: NovaTheme.textColor
                        wrapMode: Text.WrapAnywhere
                        font { pixelSize: NovaTheme.fontXS; family: "Consolas" }
                    }
                }
            }
        }

        gateSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "落盘闸门"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "未确认不写盘 · grounding 随行"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.gates
                    Item {
                        required property var modelData
                        width: parent.width
                        height: 54
                        Rectangle {
                            anchors.fill: parent
                            radius: NovaTheme.radiusM
                            color: NovaTheme.surfaceAlt
                            border.width: 1
                            border.color: NovaTheme.outline
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 8 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            font { pixelSize: NovaTheme.fontXS; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 48; top: parent.top; topMargin: 28 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 10
                        }
                        Text {
                            anchors { right: parent.right; rightMargin: 10; top: parent.top; topMargin: 8 }
                            text: modelData.s
                            color: modelData.s === "OK" ? NovaTheme.positiveText : NovaTheme.warningText
                            font { pixelSize: 9; bold: true }
                        }
                    }
                }
                Rectangle {
                    width: parent.width
                    height: 32
                    radius: 8
                    color: stage.gateOpen ? NovaTheme.positive : NovaTheme.primary
                    Text {
                        anchors.centerIn: parent
                        text: stage.gateOpen ? "已落盘 · 可回滚" : "确认落盘"
                        color: NovaTheme.textOnPrimary
                        font { pixelSize: NovaTheme.fontXS; bold: true }
                    }
                    MouseArea { anchors.fill: parent; onClicked: stage.gateOpen = true }
                }
                Text {
                    width: parent.width
                    text: stage.gateOpen ? "审计：write_event#A17 · 原文件已快照"
                                      : "提示：闸门只在人工点击后开启"
                    color: NovaTheme.textMuted
                    wrapMode: Text.WordWrap
                    font.pixelSize: 10
                }
            }
        }
    }
}
"""


# ── P3 · NovaDE 数字员工队伍 ────────────────────────────────────────────────
STAGES["de"] = """// Stage.qml · NovaDE 数字员工队伍（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeJob: 0
    property bool handoff: false

    readonly property var roles: [
        { t: "对账员", d: "只读账套", n: "3 人" },
        { t: "审单员", d: "改单需双签", n: "2 人" },
        { t: "归档员", d: "只写归档区", n: "1 人" }
    ]
    readonly property var jobs: [
        { t: "AP-2411-018", d: "供应商发票 · 12 张", s: "运行中", p: 0.62 },
        { t: "AP-2411-019", d: "差旅报销 · 41 张", s: "排队", p: 0.0 },
        { t: "AP-2411-020", d: "预付款核销 · 8 张", s: "排队", p: 0.0 },
        { t: "AP-2411-017", d: "月结调整 · 5 张", s: "已完成", p: 1.0 }
    ]
    readonly property var sla: [
        { t: "首响承诺", v: "≤ 2 h", ok: true },
        { t: "当前首响", v: "18 min", ok: true },
        { t: "超时单", v: "0", ok: true },
        { t: "影子运行", v: "52 h", ok: true }
    ]

    NovaDE {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        breakpoint: 480
        onHandoffRequested: stage.handoff = true

        roleSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 8
                Repeater {
                    model: stage.roles
                    Row {
                        required property var modelData
                        spacing: 8
                        y: (parent.height - height) / 2
                        Rectangle {
                            width: 22; height: 22; radius: 6
                            y: (parent.height - height) / 2
                            color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                            Text {
                                anchors.centerIn: parent
                                text: modelData.t.substring(0, 1)
                                color: NovaTheme.primaryText
                                font { pixelSize: 9; bold: true }
                            }
                        }
                        Column {
                            y: (parent.height - height) / 2
                            spacing: 1
                            Text {
                                text: modelData.t + " · " + modelData.n
                                color: NovaTheme.textColor
                                font { pixelSize: NovaTheme.fontXS; bold: true }
                            }
                            Text {
                                text: modelData.d
                                color: NovaTheme.textMuted
                                font.pixelSize: 9
                            }
                        }
                    }
                }
            }
        }

        queueSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "队列"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "按 SLA 截止排序"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.jobs
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: parent.width
                        height: 62
                        radius: NovaTheme.radiusM
                        color: stage.activeJob === index
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.14)
                            : "transparent"
                        border.width: 1
                        border.color: stage.activeJob === index ? NovaTheme.primary : "transparent"
                        Text {
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 9 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            font { pixelSize: NovaTheme.fontXS; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; top: parent.top; topMargin: 28 }
                            text: modelData.d + " · " + modelData.s
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 10
                        }
                        Rectangle {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; bottom: parent.bottom; bottomMargin: 8 }
                            height: 2; radius: 1
                            color: NovaTheme.outline
                            Rectangle {
                                width: parent.width * modelData.p
                                height: parent.height; radius: 1
                                color: modelData.p >= 1 ? NovaTheme.positive : NovaTheme.primary
                            }
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeJob = index }
                    }
                }
            }
        }

        contentSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 4 }
                spacing: 10
                Text {
                    text: "员工工作记录 · " + stage.jobs[stage.activeJob].t
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontM; bold: true }
                }
                Text {
                    text: "谁做的、做了什么、依据什么，逐条留痕"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: [
                        { t: "对账员 · L2", d: "抽取发票字段 12/12 · 命中模板 v4", tm: "14:02:11", ok: true },
                        { t: "对账员 · L2", d: "与 PO 三单匹配 · 差异 2 张", tm: "14:02:38", ok: true },
                        { t: "审单员 · L1", d: "差异单转人工复核 · 附 3 条依据", tm: "14:03:05", ok: false },
                        { t: "归档员 · L3", d: "等待复核结论后归档", tm: "—", ok: false }
                    ]
                    Row {
                        required property var modelData
                        width: parent.width
                        spacing: 10
                        Rectangle {
                            width: 8; height: 8; radius: 4
                            anchors.top: parent.top
                            anchors.topMargin: 6
                            color: modelData.ok ? NovaTheme.primary : NovaTheme.outline
                        }
                        Column {
                            spacing: 3
                            width: parent.width - 24
                            Text {
                                text: modelData.t + "  ·  " + modelData.tm
                                color: NovaTheme.textColor
                                font { pixelSize: NovaTheme.fontXS; bold: true }
                            }
                            Text {
                                text: modelData.d
                                color: NovaTheme.textMuted
                                width: parent.width
                                elide: Text.ElideRight
                                font.pixelSize: NovaTheme.fontXS
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
                    text: "吞吐 · 最近 12 分钟"
                    color: NovaTheme.textMuted
                    font { pixelSize: 9; bold: true }
                }
                Row {
                    spacing: 4
                    Repeater {
                        model: [0.4, 0.6, 0.55, 0.72, 0.68, 0.8, 0.75, 0.9, 0.86, 0.94, 0.88, 0.92]
                        Rectangle {
                            required property real modelData
                            width: Math.max(6, (parent.width - 44) / 12)
                            height: 42 * modelData
                            radius: 3
                            anchors.bottom: parent.bottom
                            color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.35 + 0.5 * modelData)
                        }
                    }
                }
            }
        }

        slaSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "SLA"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "越界自动升级人工"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.sla
                    Item {
                        required property var modelData
                        width: parent.width
                        height: 46
                        Rectangle {
                            anchors.fill: parent
                            radius: NovaTheme.radiusM
                            color: NovaTheme.surfaceAlt
                            border.width: 1
                            border.color: NovaTheme.outline
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.t
                            color: NovaTheme.textMuted
                            font.pixelSize: 10
                        }
                        Text {
                            anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                            text: modelData.v
                            color: modelData.ok ? NovaTheme.positiveText : NovaTheme.warningText
                            font { pixelSize: NovaTheme.fontXS; bold: true }
                        }
                    }
                }
            }
        }

        handoffSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 10
                Text {
                    y: (parent.height - height) / 2
                    text: stage.handoff ? "已发起交接 · 接收人：财务共享中心 / 王敏"
                                      : "跨角色交接需显式发起，不自动越权"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontXS; bold: true }
                }
            }
            Rectangle {
                anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                width: 92; height: 30; radius: 8
                color: stage.handoff ? NovaTheme.positive : NovaTheme.primary
                Text {
                    anchors.centerIn: parent
                    text: stage.handoff ? "已交接" : "发起交接"
                    color: NovaTheme.textOnPrimary
                    font { pixelSize: NovaTheme.fontXS; bold: true }
                }
                MouseArea { anchors.fill: parent; onClicked: stage.handoff = true }
            }
        }
    }
}
"""


# ── P4 · NovaOrbit 意图轨道工作台 ───────────────────────────────────────────
STAGES["orbit"] = """// Stage.qml · NovaOrbit 意图轨道工作台（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeMode: 0
    property string draft: ""
    property var events: []
    property int routed: 3

    readonly property var modes: [
        { t: "收件轨道", d: "未分类意图" },
        { t: "执行轨道", d: "已绑定实体" },
        { t: "复核轨道", d: "等待人工" },
        { t: "归档轨道", d: "已封存" }
    ]
    readonly property var nodes: [
        { t: "对账差异 · 华东区", d: "entity:region/east", s: "已绑定" },
        { t: "发票异常 · 供应商 A17", d: "entity:vendor/A17", s: "已绑定" },
        { t: "月结提前 · 11 月", d: "未绑定周期实体", s: "待绑定" }
    ]

    function route() {
        if (stage.draft.trim() === "") return
        stage.events = stage.events.concat([stage.draft])
        stage.draft = ""
        stage.routed = stage.routed + 1
    }

    NovaOrbit {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        breakpoint: 480
        onOrbitRequested: stage.route()

        globalSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 10
                Rectangle {
                    width: 6; height: 6; radius: 3
                    y: (parent.height - height) / 2
                    color: NovaTheme.primary
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "轨道 A · 意图 " + stage.routed + " 条 · 实体命中 96%"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontXS; bold: true }
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "改道留痕 · 可回退"
                    color: NovaTheme.textMuted
                    font.pixelSize: 10
                }
            }
        }

        railSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 8
                Text {
                    text: "轨道"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Repeater {
                    model: stage.modes
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: parent.width
                        height: 48
                        radius: NovaTheme.radiusM
                        color: stage.activeMode === index
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                            : "transparent"
                        border.width: 1
                        border.color: stage.activeMode === index ? NovaTheme.primary : "transparent"
                        Column {
                            anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                            spacing: 2
                            Text {
                                text: modelData.t
                                color: NovaTheme.textColor
                                font { pixelSize: NovaTheme.fontXS; bold: stage.activeMode === index }
                            }
                            Text {
                                text: modelData.d
                                color: NovaTheme.textMuted
                                font.pixelSize: 9
                            }
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeMode = index }
                    }
                }
            }
        }

        intentSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 4 }
                spacing: 10
                Text {
                    text: "意图入轨"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontL; bold: true }
                }
                Text {
                    text: "一句话说清目标；实体未绑定不入轨"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Rectangle {
                    width: parent.width
                    height: 96
                    radius: NovaTheme.radiusM
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 12 }
                        text: stage.draft === "" ? "例如：把华东区 11 月的对账差异按供应商聚一下…" : stage.draft
                        color: stage.draft === "" ? NovaTheme.textMuted : NovaTheme.textColor
                        wrapMode: Text.WordWrap
                        width: parent.width - 28
                        font.pixelSize: NovaTheme.fontS
                    }
                }
                Row {
                    spacing: 6
                    Repeater {
                        model: ["region/east", "vendor/A17", "period/2026-11"]
                        Rectangle {
                            required property string modelData
                            width: 88; height: 22; radius: 11
                            color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.12)
                            Text {
                                anchors.centerIn: parent
                                text: modelData
                                color: NovaTheme.primaryText
                                font.pixelSize: 9
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
                    text: "已入轨"
                    color: NovaTheme.textMuted
                    font { pixelSize: 9; bold: true }
                }
                Repeater {
                    model: stage.events
                    Text {
                        required property string modelData
                        width: parent.width
                        text: "· " + modelData
                        color: NovaTheme.textColor
                        elide: Text.ElideRight
                        font.pixelSize: NovaTheme.fontXS
                    }
                }
            }
        }

        composerSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: 56; height: 30; radius: 8
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors.centerIn: parent
                        text: "轨道 A"
                        color: NovaTheme.primaryText
                        font.pixelSize: 10
                    }
                }
                Rectangle {
                    width: parent.width - 170
                    height: 32; radius: 8
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                        text: "输入意图…"
                        color: NovaTheme.textMuted
                        font.pixelSize: 10
                    }
                }
                Rectangle {
                    width: 92; height: 32; radius: 8
                    color: NovaTheme.primary
                    Text {
                        anchors.centerIn: parent
                        text: "入轨"
                        color: NovaTheme.textOnPrimary
                        font { pixelSize: 10; bold: true }
                    }
                    MouseArea { anchors.fill: parent; onClicked: stage.route() }
                }
            }
        }

        canvasSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 8
                Text {
                    text: "轨道节点"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Repeater {
                    model: stage.nodes
                    Rectangle {
                        required property var modelData
                        width: parent.width
                        height: 66
                        radius: NovaTheme.radiusM
                        color: NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: modelData.s === "已绑定" ? NovaTheme.outline : NovaTheme.warning
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; top: parent.top; topMargin: 9 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            elide: Text.ElideRight
                            font { pixelSize: 10; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 28 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            font.pixelSize: 9
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; bottom: parent.bottom; bottomMargin: 8 }
                            text: modelData.s
                            color: modelData.s === "已绑定" ? NovaTheme.positiveText : NovaTheme.warningText
                            font { pixelSize: 9; bold: true }
                        }
                    }
                }
                Text {
                    text: "命中率"
                    color: NovaTheme.textMuted
                    font { pixelSize: 9; bold: true }
                }
                Row {
                    width: parent.width
                    height: 8
                    spacing: 3
                    Repeater {
                        model: 16
                        Rectangle {
                            required property int index
                            width: (parent.width - 45) / 16
                            height: 8
                            radius: 2
                            color: index < 15
                                ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.85)
                                : NovaTheme.outline
                        }
                    }
                }
            }
        }

        mapSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                spacing: 6
                Repeater {
                    model: 7
                    Rectangle {
                        required property int index
                        width: 5; height: 5; radius: 2.5
                        color: index < 5 ? NovaTheme.primary : NovaTheme.outline
                    }
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "缩略 · 5 / 7 节点"
                    color: NovaTheme.textMuted
                    font.pixelSize: 9
                }
            }
        }
    }
}
"""


# ── P5 · NovaDesktop 企业桌面 ───────────────────────────────────────────────
STAGES["desktop"] = """// Stage.qml · NovaDesktop 企业桌面（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeMenu: 0
    property int activeTab: 0

    readonly property var menus: ["财务", "采购", "库存", "报表", "设置"]
    readonly property var tabs: ["总览", "待办", "异常"]
    readonly property var kpis: [
        { k: "本月应付", v: "¥ 2,418,900", d: "+3.2% 环比", up: true },
        { k: "待审单据", v: "37", d: "其中超期 2 张", up: false },
        { k: "对账差异", v: "¥ 1,204", d: "37 笔待归因", up: false }
    ]
    readonly property var panels: [
        { t: "应付账龄", d: "0–30 天 62% · 31–60 天 24% · > 60 天 14%" },
        { t: "供应商集中度", d: "Top 5 供应商占采购额 41%" },
        { t: "异常趋势", d: "近 7 日差异笔数 37 → 21 → 18" }
    ]

    NovaDesktop {
        anchors.fill: parent
        _signatureOn: stage.signatureOn

        menuSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                spacing: 16
                Repeater {
                    model: stage.menus
                    Text {
                        required property string modelData
                        required property int index
                        y: (parent.height - height) / 2
                        text: modelData
                        color: stage.activeMenu === index ? NovaTheme.primaryText : NovaTheme.textMuted
                        font { pixelSize: NovaTheme.fontXS; bold: stage.activeMenu === index }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeMenu = index }
                    }
                }
            }
        }

        toolbarSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
                spacing: 8
                Repeater {
                    model: ["新建单据", "批量审核", "导出对账", "刷新"]
                    Rectangle {
                        required property string modelData
                        width: 76; height: 26; radius: 6
                        color: NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: NovaTheme.outline
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: NovaTheme.textColor
                            font.pixelSize: 10
                        }
                    }
                }
            }
        }

        pageSlot: Item {
            anchors.fill: parent
            Flickable {
                anchors.fill: parent
                contentHeight: pageCol.implicitHeight
                clip: true
                Column {
                    id: pageCol
                    width: parent.width
                    spacing: 12
                    Row {
                        width: parent.width
                        spacing: 12
                        Repeater {
                            model: stage.kpis
                            Rectangle {
                                required property var modelData
                                width: (pageCol.width - 24) / 3
                                height: 84
                                radius: NovaTheme.radiusM
                                color: NovaTheme.surface
                                border.width: 1
                                border.color: NovaTheme.outline
                                Text {
                                    anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 12 }
                                    text: modelData.k
                                    color: NovaTheme.textMuted
                                    font.pixelSize: 10
                                }
                                Text {
                                    anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 32 }
                                    text: modelData.v
                                    color: NovaTheme.textColor
                                    font { pixelSize: NovaTheme.fontL; bold: true }
                                }
                                Text {
                                    anchors { left: parent.left; leftMargin: 14; bottom: parent.bottom; bottomMargin: 12 }
                                    text: modelData.d
                                    color: modelData.up ? NovaTheme.positiveText : NovaTheme.warningText
                                    font.pixelSize: 9
                                }
                            }
                        }
                    }
                    Row {
                        width: parent.width
                        spacing: 12
                        Repeater {
                            model: stage.panels
                            Rectangle {
                                required property var modelData
                                width: (pageCol.width - 24) / 3
                                height: 140
                                radius: NovaTheme.radiusM
                                color: NovaTheme.surface
                                border.width: 1
                                border.color: NovaTheme.outline
                                Text {
                                    anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 12 }
                                    text: modelData.t
                                    color: NovaTheme.textColor
                                    font { pixelSize: NovaTheme.fontS; bold: true }
                                }
                                Text {
                                    anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; top: parent.top; topMargin: 38 }
                                    text: modelData.d
                                    color: NovaTheme.textMuted
                                    wrapMode: Text.WordWrap
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }
                }
            }
        }

        statusSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
                spacing: 14
                Text {
                    y: (parent.height - height) / 2
                    text: "● 已连接"
                    color: NovaTheme.positiveText
                    font.pixelSize: 9
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "同步 3 s 前 · 租户 east-fin · v1.2.3"
                    color: NovaTheme.textMuted
                    font.pixelSize: 9
                }
            }
        }
    }
}
"""


# ── P6 · NovaChat AI 对话工作台 ────────────────────────────────────────────
STAGES["chat"] = """// Stage.qml · NovaChat AI 对话工作台（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeChat: 0
    property string draft: ""
    property var sent: []

    readonly property var chats: [
        { t: "十一月对账口径", d: "差异阈值定 0.01 还是 0.05？", tm: "14:02" },
        { t: "供应商 A17 异常", d: "已附 3 条依据", tm: "13:40" },
        { t: "月结提前方案", d: "需财务共享中心确认", tm: "11:18" },
        { t: "发票 OCR 准确率", d: "98.6% · 12 张待复核", tm: "昨天" },
        { t: "报表导出模板", d: "已生成 v3 模板", tm: "昨天" }
    ]
    readonly property var baseMessages: [
        { who: "them", body: "十一月对账已跑完，差异 37 笔，集中在华东区。", ref: "ledger.run#2411" },
        { who: "me", body: "先把差异按供应商聚合，金额带 0.01 以上单独列。", ref: "" },
        { who: "them", body: "已聚合：A17 占 21 笔，建议优先人工复核。", ref: "cluster#37 · vendor/A17" }
    ]

    function send() {
        if (stage.draft.trim() === "") return
        stage.sent = stage.sent.concat([stage.draft])
        stage.draft = ""
    }

    NovaChat {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        // 对话壳三条侧栏 + 中心区需要 ~960px；在孵化器双栏之间默认收起，
        // 用户放大窗口到舞台 ≥700px 时自动展开完整六槽（响应式，不挤压正文）
        breakpoint: 700

        navSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; topMargin: 12; horizontalCenter: parent.horizontalCenter }
                spacing: 10
                Repeater {
                    model: 4
                    Rectangle {
                        required property int index
                        width: 30; height: 30; radius: 9
                        color: index === 0
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.18)
                            : "transparent"
                        border.width: index === 0 ? 0 : 1
                        border.color: NovaTheme.outline
                        Text {
                            anchors.centerIn: parent
                            text: ["◧", "☰", "◷", "⚙"][index]
                            color: index === 0 ? NovaTheme.primaryText : NovaTheme.textMuted
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }

        conversationSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 8
                Rectangle {
                    width: parent.width
                    height: 28; radius: 7
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors { left: parent.left; leftMargin: 9; verticalCenter: parent.verticalCenter }
                        text: "搜索会话…"
                        color: NovaTheme.textMuted
                        font.pixelSize: 10
                    }
                }
                Repeater {
                    model: stage.chats
                    Rectangle {
                        required property var modelData
                        required property int index
                        width: parent.width
                        height: 56
                        radius: NovaTheme.radiusM
                        color: stage.activeChat === index
                            ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.14)
                            : "transparent"
                        Text {
                            anchors { left: parent.left; leftMargin: 9; right: parent.right; rightMargin: 9; top: parent.top; topMargin: 8 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            elide: Text.ElideRight
                            font { pixelSize: 11; bold: stage.activeChat === index }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 9; right: parent.right; rightMargin: 9; top: parent.top; topMargin: 26 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 9
                        }
                        Text {
                            anchors { right: parent.right; rightMargin: 9; bottom: parent.bottom; bottomMargin: 7 }
                            text: modelData.tm
                            color: NovaTheme.textMuted
                            font.pixelSize: 8
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeChat = index }
                    }
                }
            }
        }

        headerSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 10
                Rectangle {
                    width: 24; height: 24; radius: 8
                    color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.2)
                    Text {
                        anchors.centerIn: parent
                        text: "财"
                        color: NovaTheme.primaryText
                        font { pixelSize: 10; bold: true }
                    }
                }
                Column {
                    spacing: 1
                    Text {
                        text: stage.chats[stage.activeChat].t
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontS; bold: true }
                    }
                    Text {
                        text: "3 位成员 · 上下文可追溯"
                        color: NovaTheme.textMuted
                        font.pixelSize: 9
                    }
                }
            }
        }

        contentSlot: Item {
            anchors.fill: parent
            Flickable {
                anchors.fill: parent
                contentHeight: msgCol.implicitHeight + 16
                clip: true
                Column {
                    id: msgCol
                    anchors { top: parent.top; left: parent.left; right: parent.right; margins: 4 }
                    spacing: 10
                    Repeater {
                        model: stage.baseMessages
                        Column {
                            required property var modelData
                            width: msgCol.width
                            spacing: 4
                            Row {
                                spacing: 6
                                Text {
                                    text: modelData.who === "me" ? "我" : "财务助手"
                                    color: NovaTheme.textMuted
                                    font { pixelSize: 9; bold: true }
                                }
                                Text {
                                    text: modelData.ref
                                    visible: modelData.ref !== ""
                                    color: NovaTheme.primaryText
                                    font.pixelSize: 8
                                }
                            }
                            Rectangle {
                                width: Math.min(msgCol.width * 0.82, implicitText.implicitWidth + 24)
                                height: implicitText.implicitHeight + 20
                                radius: NovaTheme.radiusM
                                color: modelData.who === "me"
                                    ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                                    : NovaTheme.surfaceAlt
                                border.width: 1
                                border.color: modelData.who === "me" ? NovaTheme.primary : NovaTheme.outline
                                Text {
                                    id: implicitText
                                    anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                    text: modelData.body
                                    color: NovaTheme.textColor
                                    wrapMode: Text.WordWrap
                                    font.pixelSize: NovaTheme.fontXS
                                }
                            }
                        }
                    }
                    Repeater {
                        model: stage.sent
                        Rectangle {
                            required property string modelData
                            width: Math.min(msgCol.width * 0.82, sentText.implicitWidth + 24)
                            height: sentText.implicitHeight + 20
                            radius: NovaTheme.radiusM
                            color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                            border.width: 1
                            border.color: NovaTheme.primary
                            Text {
                                id: sentText
                                anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                                text: modelData
                                color: NovaTheme.textColor
                                wrapMode: Text.WordWrap
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                    }
                }
            }
        }

        composerSlot: Item {
            anchors.fill: parent
            Column {
                anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: parent.width
                    height: 44
                    radius: NovaTheme.radiusM
                    color: NovaTheme.surfaceAlt
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors { left: parent.left; leftMargin: 12; verticalCenter: parent.verticalCenter }
                        text: stage.draft === "" ? "输入消息，Enter 发送…" : stage.draft
                        color: stage.draft === "" ? NovaTheme.textMuted : NovaTheme.textColor
                        elide: Text.ElideRight
                        width: parent.width - 24
                        font.pixelSize: 10
                    }
                }
                Row {
                    width: parent.width
                    spacing: 8
                    Text {
                        text: "草稿自动本地保存 · 切会话不丢失"
                        color: NovaTheme.textMuted
                        font.pixelSize: 8
                    }
                    Item { width: Math.max(0, parent.width - 300); height: 1 }
                    Rectangle {
                        width: 64; height: 24; radius: 6
                        color: NovaTheme.primary
                        Text {
                            anchors.centerIn: parent
                            text: "发送"
                            color: NovaTheme.textOnPrimary
                            font { pixelSize: 9; bold: true }
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.send() }
                    }
                }
            }
        }

        detailSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 12 }
                spacing: 10
                Text {
                    text: "上下文"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Repeater {
                    model: [
                        { t: "ledger.run#2411", d: "差异 37 笔 · 12,480 行" },
                        { t: "cluster#37", d: "按供应商 + 金额带聚类" },
                        { t: "policy/fin-v7", d: "阈值 0.01 · 双签规则" }
                    ]
                    Rectangle {
                        required property var modelData
                        width: parent.width
                        height: 54
                        radius: NovaTheme.radiusM
                        color: NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: NovaTheme.outline
                        Text {
                            anchors { left: parent.left; leftMargin: 10; top: parent.top; topMargin: 8 }
                            text: modelData.t
                            color: NovaTheme.primaryText
                            font { pixelSize: 9; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 10; right: parent.right; rightMargin: 10; top: parent.top; topMargin: 28 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 9
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
                    text: "回复只基于以上引用；无引用时明确说明。"
                    color: NovaTheme.textMuted
                    wrapMode: Text.WordWrap
                    font.pixelSize: 9
                }
            }
        }
    }
}
"""


# ── P7 · NovaMobile 移动触控应用 ───────────────────────────────────────────
STAGES["mobile"] = """// Stage.qml · NovaMobile 移动触控应用（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int activeTab: 0

    readonly property var items: [
        { t: "待我审批", d: "3 单 · 最晚今日 18:00", s: "紧急" },
        { t: "今日巡检", d: "2 个点位未打卡", s: "待办" },
        { t: "异常上报", d: "1 条待补充照片", s: "待办" },
        { t: "已完成", d: "昨日 6 项全部闭环", s: "完成" }
    ]

    NovaMobile {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        safeTop: 6
        safeBottom: 8
        onBackRequested: stage.activeTab = 0

        headerSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                spacing: 10
                Text {
                    y: (parent.height - height) / 2
                    text: "‹"
                    color: NovaTheme.textColor
                    font.pixelSize: 18
                }
                Column {
                    spacing: 1
                    Text {
                        text: ["现场作业", "审批", "消息", "我的"][stage.activeTab]
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontS; bold: true }
                    }
                    Text {
                        text: "工号 8821 · 华东巡检组"
                        color: NovaTheme.textMuted
                        font.pixelSize: 9
                    }
                }
            }
            Rectangle {
                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                width: 34; height: 22; radius: 11
                color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                Text {
                    anchors.centerIn: parent
                    text: "同步"
                    color: NovaTheme.primaryText
                    font { pixelSize: 9; bold: true }
                }
            }
        }

        contentSlot: Item {
            anchors.fill: parent
            Flickable {
                anchors.fill: parent
                contentHeight: mobCol.implicitHeight
                clip: true
                Column {
                    id: mobCol
                    width: parent.width
                    spacing: 10
                    Rectangle {
                        width: parent.width
                        height: 88
                        radius: NovaTheme.radiusM
                        color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.12)
                        border.width: 1
                        border.color: NovaTheme.primary
                        Text {
                            anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 12 }
                            text: "今日进度"
                            color: NovaTheme.textMuted
                            font.pixelSize: 9
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 14; top: parent.top; topMargin: 30 }
                            text: "4 / 6 项"
                            color: NovaTheme.textColor
                            font { pixelSize: NovaTheme.fontXL; bold: true }
                        }
                        Rectangle {
                            anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; bottom: parent.bottom; bottomMargin: 14 }
                            height: 4; radius: 2
                            color: NovaTheme.outline
                            Rectangle {
                                width: parent.width * 0.66
                                height: parent.height; radius: 2
                                color: NovaTheme.primary
                            }
                        }
                    }
                    Repeater {
                        model: stage.items
                        Rectangle {
                            required property var modelData
                            width: parent.width
                            height: 76
                            radius: NovaTheme.radiusM
                            color: NovaTheme.surfaceAlt
                            border.width: 1
                            border.color: NovaTheme.outline
                            Text {
                                anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 54; top: parent.top; topMargin: 12 }
                                text: modelData.t
                                color: NovaTheme.textColor
                                elide: Text.ElideRight
                                font { pixelSize: NovaTheme.fontS; bold: true }
                            }
                            Text {
                                anchors { left: parent.left; leftMargin: 14; right: parent.right; rightMargin: 14; top: parent.top; topMargin: 36 }
                                text: modelData.d
                                color: NovaTheme.textMuted
                                elide: Text.ElideRight
                                font.pixelSize: 9
                            }
                            Rectangle {
                                anchors { right: parent.right; rightMargin: 12; top: parent.top; topMargin: 12 }
                                width: 34; height: 18; radius: 9
                                color: modelData.s === "紧急"
                                    ? Qt.rgba(NovaTheme.warning.r, NovaTheme.warning.g, NovaTheme.warning.b, 0.18)
                                    : Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.14)
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.s
                                    color: modelData.s === "紧急" ? NovaTheme.warningText : NovaTheme.primaryText
                                    font { pixelSize: 8; bold: true }
                                }
                            }
                            Text {
                                anchors { right: parent.right; rightMargin: 12; bottom: parent.bottom; bottomMargin: 12 }
                                text: "›"
                                color: NovaTheme.textMuted
                                font.pixelSize: 14
                            }
                        }
                    }
                }
            }
        }

        bottomNavSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 8; right: parent.right; rightMargin: 8; top: parent.top; topMargin: 6 }
                spacing: 0
                Repeater {
                    model: ["作业", "审批", "消息", "我的"]
                    Item {
                        required property string modelData
                        required property int index
                        width: (parent.width - 16) / 4
                        height: 48
                        Rectangle {
                            anchors.centerIn: parent
                            width: 40; height: 40; radius: 12
                            color: stage.activeTab === index
                                ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.14)
                                : "transparent"
                            Text {
                                anchors.centerIn: parent
                                text: modelData
                                color: stage.activeTab === index ? NovaTheme.primaryText : NovaTheme.textMuted
                                font { pixelSize: 10; bold: stage.activeTab === index }
                            }
                        }
                        MouseArea { anchors.fill: parent; onClicked: stage.activeTab = index }
                    }
                }
            }
        }
    }
}
"""


# ── P8 · NovaFlexLayout 工业大屏 ────────────────────────────────────────────
STAGES["flex"] = """// Stage.qml · NovaFlexLayout 工业大屏（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int cols: 3

    readonly property var panels: [
        { t: "订单履约", v: "1,284", d: "准时率 97.2%" },
        { t: "库存周转", v: "18.4 天", d: "较上月 −1.2 天" },
        { t: "质检合格", v: "99.1%", d: "异常 3 批待判" },
        { t: "在途运单", v: "412", d: "延误 6 单" },
        { t: "产能负荷", v: "82%", d: "峰值 96%" },
        { t: "能耗", v: "1.42 kWh", d: "单件能耗" },
        { t: "工单积压", v: "37", d: "超 48 h 有 4 单" },
        { t: "设备在线", v: "148 / 152", d: "离线 4 台" }
    ]

    NovaFlexLayout {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        columns: stage.cols
        showFooter: true
        onLayoutChanged: function(c) { stage.cols = c }

        headerSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                spacing: 12
                Column {
                    spacing: 1
                    Text {
                        text: "生产运营看板"
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontM; bold: true }
                    }
                    Text {
                        text: "同一份内容 · 1–4 栏平滑重排"
                        color: NovaTheme.textMuted
                        font.pixelSize: 9
                    }
                }
                Row {
                    spacing: 4
                    Repeater {
                        model: [1, 2, 3, 4]
                        Rectangle {
                            required property int modelData
                            width: 26; height: 24; radius: 6
                            color: stage.cols === modelData
                                ? Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.18)
                                : "transparent"
                            border.width: 1
                            border.color: stage.cols === modelData ? NovaTheme.primary : NovaTheme.outline
                            Text {
                                anchors.centerIn: parent
                                text: modelData
                                color: stage.cols === modelData ? NovaTheme.primaryText : NovaTheme.textMuted
                                font { pixelSize: 9; bold: stage.cols === modelData }
                            }
                            MouseArea { anchors.fill: parent; onClicked: stage.cols = modelData }
                        }
                    }
                }
            }
        }

        contentSlot: Item {
            anchors.fill: parent
            Grid {
                anchors.fill: parent
                columns: stage.cols
                spacing: 10
                Repeater {
                    model: stage.panels
                    Rectangle {
                        required property var modelData
                        width: (parent.width - 10 * (stage.cols - 1)) / stage.cols
                        height: 104
                        radius: NovaTheme.radiusM
                        color: NovaTheme.surface
                        border.width: 1
                        border.color: NovaTheme.outline
                        Text {
                            anchors { left: parent.left; leftMargin: 12; top: parent.top; topMargin: 10 }
                            text: modelData.t
                            color: NovaTheme.textMuted
                            font.pixelSize: 9
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 12; top: parent.top; topMargin: 30 }
                            text: modelData.v
                            color: NovaTheme.textColor
                            font { pixelSize: NovaTheme.fontL; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 12; bottom: parent.bottom; bottomMargin: 10 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            width: parent.width - 24
                            font.pixelSize: 9
                        }
                    }
                }
            }
        }

        footerSlot: Item {
            anchors.fill: parent
            Row {
                anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                spacing: 14
                Text {
                    y: (parent.height - height) / 2
                    text: "8 面板 · " + stage.cols + " 栏"
                    color: NovaTheme.textMuted
                    font.pixelSize: 9
                }
                Text {
                    y: (parent.height - height) / 2
                    text: "零横向滚动 · 320 px 起可用"
                    color: NovaTheme.positiveText
                    font.pixelSize: 9
                }
            }
        }
    }
}
"""


# ── P9 · NovaSetupWizard 部署向导 ──────────────────────────────────────────
STAGES["wizard"] = """// Stage.qml · NovaSetupWizard 部署向导（nova-forge prescript 生成）
import QtQuick
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

Item {
    id: stage
    property bool signatureOn: true
    property int step: 0
    property var picked: ({})

    readonly property var titles: ["选择环境", "填写连接", "选择组件", "校验连通", "确认部署"]
    readonly property var envs: [
        { t: "生产环境", d: "多副本 · 强审计 · 变更需双签" },
        { t: "预发环境", d: "单副本 · 全量日志 · 可回滚" },
        { t: "本地试用", d: "单机 · 不接生产数据" }
    ]
    readonly property var comps: ["核心组件库", "审计接入", "单点登录", "可观测性"]

    NovaSetupWizard {
        anchors.fill: parent
        _signatureOn: stage.signatureOn
        stepCount: 5
        currentStep: stage.step
        onPreviousRequested: stage.step = Math.max(0, stage.step - 1)
        onNextRequested: stage.step = Math.min(4, stage.step + 1)
        onStepSelected: function(i) { stage.step = i }

        contentSlot: Item {
            anchors.fill: parent
            Column {
                anchors { top: parent.top; left: parent.left; right: parent.right; margins: 4 }
                spacing: 10
                Text {
                    text: (stage.step + 1) + " / 5 · " + stage.titles[stage.step]
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontM; bold: true }
                }
                Text {
                    text: "每一步先校验后放行；上一步内容原样保留"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: stage.envs
                    Rectangle {
                        required property var modelData
                        required property int index
                        visible: stage.step === 0
                        width: parent.width
                        height: 62
                        radius: NovaTheme.radiusM
                        color: NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: NovaTheme.outline
                        Text {
                            anchors { left: parent.left; leftMargin: 12; top: parent.top; topMargin: 10 }
                            text: modelData.t
                            color: NovaTheme.textColor
                            font { pixelSize: NovaTheme.fontS; bold: true }
                        }
                        Text {
                            anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12; top: parent.top; topMargin: 32 }
                            text: modelData.d
                            color: NovaTheme.textMuted
                            elide: Text.ElideRight
                            font.pixelSize: 9
                        }
                    }
                }
                Column {
                    visible: stage.step === 1
                    width: parent.width
                    spacing: 8
                    Repeater {
                        model: ["服务地址", "租户 ID", "访问密钥"]
                        Column {
                            required property string modelData
                            width: parent.width
                            spacing: 4
                            Text {
                                text: modelData
                                color: NovaTheme.textMuted
                                font.pixelSize: 9
                            }
                            Rectangle {
                                width: parent.width
                                height: 32; radius: 7
                                color: NovaTheme.surfaceAlt
                                border.width: 1
                                border.color: NovaTheme.outline
                                Text {
                                    anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                                    text: modelData === "服务地址" ? "https://api.example.com" : "••••••••"
                                    color: NovaTheme.textColor
                                    font.pixelSize: 10
                                }
                            }
                        }
                    }
                }
                Column {
                    visible: stage.step === 2
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: stage.comps
                        Row {
                            required property string modelData
                            spacing: 8
                            Rectangle {
                                width: 14; height: 14; radius: 4
                                color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.2)
                                border.width: 1
                                border.color: NovaTheme.primary
                                Text {
                                    anchors.centerIn: parent
                                    text: "✓"
                                    color: NovaTheme.primaryText
                                    font { pixelSize: 8; bold: true }
                                }
                            }
                            Text {
                                text: modelData
                                color: NovaTheme.textColor
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                    }
                }
                Column {
                    visible: stage.step === 3
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: ["DNS 解析", "TLS 证书", "数据库连通", "对象存储写入"]
                        Row {
                            required property string modelData
                            spacing: 8
                            Text {
                                text: "PASS"
                                color: NovaTheme.positiveText
                                font { pixelSize: 8; bold: true }
                            }
                            Text {
                                text: modelData
                                color: NovaTheme.textColor
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                    }
                }
                Column {
                    visible: stage.step === 4
                    width: parent.width
                    spacing: 6
                    Repeater {
                        model: ["环境：预发环境", "地址：api.example.com", "组件：4 项全选", "校验：4 / 4 通过"]
                        Text {
                            required property string modelData
                            text: "· " + modelData
                            color: NovaTheme.textColor
                            font.pixelSize: NovaTheme.fontXS
                        }
                    }
                }
            }
        }

        controlsSlot: Item {
            anchors.fill: parent
            Row {
                anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: 82; height: 30; radius: 8
                    color: "transparent"
                    border.width: 1
                    border.color: NovaTheme.outline
                    Text {
                        anchors.centerIn: parent
                        text: "上一步"
                        color: NovaTheme.textColor
                        font.pixelSize: 10
                    }
                    MouseArea { anchors.fill: parent; onClicked: stage.step = Math.max(0, stage.step - 1) }
                }
                Rectangle {
                    width: stage.step === 4 ? 108 : 82
                    height: 30; radius: 8
                    color: NovaTheme.primary
                    Text {
                        anchors.centerIn: parent
                        text: stage.step === 4 ? "确认部署" : "下一步"
                        color: NovaTheme.textOnPrimary
                        font { pixelSize: 10; bold: true }
                    }
                    MouseArea { anchors.fill: parent; onClicked: stage.step = Math.min(4, stage.step + 1) }
                }
            }
        }
    }
}
"""
