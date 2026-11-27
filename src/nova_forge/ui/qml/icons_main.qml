// src/nova_forge/ui/icons_main.qml
// 创建时间：星期二 2026-11-24 22:03
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Nova.Services
import Nova.Controls

ApplicationWindow {
    id: win
    width: 1120
    height: 780
    minimumWidth: 900
    minimumHeight: 600
    visible: true
    title: "Nova-Forge · 图标资产管理"
    color: NovaTheme.page

    // Windows 原生标题栏不随 QML 主题变化：属性绑定同步 DWM 明暗（与 prescript GUI 同口径）
    property bool chromeDark: NovaTheme.isDark
    onChromeDarkChanged: bridge.setDarkTitleBar(chromeDark)

    Component.onCompleted: {
        // NovaOverlayHost / NovaNotify / NovaDialog 都靠这个找宿主窗口
        NovaScreen.source = win
        bridge.setDarkTitleBar(NovaTheme.isDark)
        assetSelect.modelValue = bridge.currentAssetFolder
        resSelect.modelValue = bridge.currentResourceFolder
    }

    // ── 全局共享 tooltip（页面根层，非 delegate 内）──────────────
    // 就地渲染口径：气泡会被 _place() clamp 到 parent 范围内。若声明在
    // 108×108 的 cell 里，气泡被压回 cell 盖住鼠标 → containsMouse 翻转
    // → 显示/隐藏死循环（边部闪烁、中心正常）。声明在根层后 parent 是
    // 整个窗口，气泡落在 cell 外侧，反馈环断开；同时 365 个 HoverHandler
    // 降为 1 个。
    property var tipTarget: null
    property string tipText: ""
    property bool tipVisible: false

    Timer {
        id: tipDelay
        interval: 260
        repeat: false
        onTriggered: win.tipVisible = true
    }

    // 0×0 空闲锚点：让组件内建 HoverHandler 无 hover 区域，不与 MouseArea 抢事件
    Item { id: idleAnchor; width: 0; height: 0 }

    // ── 资产侧 delegate（双击发布）────────────────────────────
    Component {
        id: assetDelegate
        Item {
            width: GridView.view.cellWidth
            height: GridView.view.cellHeight
            Rectangle {
                anchors.fill: parent
                anchors.margins: 4
                radius: NovaTheme.radiusM
                color: am.containsMouse ? NovaTheme.surfaceAlt : NovaTheme.surface
                border.width: 1
                border.color: am.containsMouse ? NovaTheme.primary : NovaTheme.outline

                Image {
                    anchors.top: parent.top
                    anchors.topMargin: 8
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 52
                    height: 52
                    source: modelData.url
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: true
                }
                Text {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 6
                    text: modelData.name
                    color: NovaTheme.textColor
                    font.family: NovaTheme.fontFamily
                    font.pixelSize: NovaTheme.fontXS
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideMiddle
                    maximumLineCount: 2
                    wrapMode: Text.Wrap
                }
                // 0×0 锚点：只给气泡定位用，不给组件内建 HoverHandler 留可悬停区域
                Item {
                    id: assetTipAnchor
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    width: 0
                    height: 0
                }
                MouseArea {
                    id: am
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        win.tipTarget = assetTipAnchor
                        win.tipText = modelData.tip + "\n双击发布到资源库"
                        tipDelay.restart()
                    }
                    onExited: {
                        tipDelay.stop()
                        win.tipVisible = false
                    }
                    onDoubleClicked: bridge.publishIcon(modelData.path)
                }
            }
        }
    }

    // ── 资源侧 delegate（右键删除）────────────────────────────
    Component {
        id: resDelegate
        Item {
            width: GridView.view.cellWidth
            height: GridView.view.cellHeight
            Rectangle {
                anchors.fill: parent
                anchors.margins: 4
                radius: NovaTheme.radiusM
                color: rm.containsMouse ? NovaTheme.surfaceAlt : NovaTheme.surface
                border.width: 1
                border.color: rm.containsMouse ? NovaTheme.negative : NovaTheme.outline

                Image {
                    anchors.top: parent.top
                    anchors.topMargin: 8
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 52
                    height: 52
                    source: modelData.url
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: true
                }
                Text {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 6
                    text: modelData.name
                    color: NovaTheme.textColor
                    font.family: NovaTheme.fontFamily
                    font.pixelSize: NovaTheme.fontXS
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideMiddle
                    maximumLineCount: 2
                    wrapMode: Text.Wrap
                }
                Item {
                    id: resTipAnchor
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    width: 0
                    height: 0
                }
                MouseArea {
                    id: rm
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onEntered: {
                        win.tipTarget = resTipAnchor
                        win.tipText = modelData.tip + "\n右键删除该资源"
                        tipDelay.restart()
                    }
                    onExited: {
                        tipDelay.stop()
                        win.tipVisible = false
                    }
                    onClicked: (m) => {
                        if (m.button === Qt.RightButton)
                            bridge.requestDelete(modelData.path, modelData.name)
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── 顶部应用栏 ────────────────────────────────────────
        NovaHeader {
            Layout.fillWidth: true
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: NovaTheme.spacingL
                anchors.rightMargin: NovaTheme.spacingL
                spacing: NovaTheme.spacingM

                Text {
                    text: "🎨  图标资产管理"
                    color: NovaTheme.textOnPrimary
                    font.family: NovaTheme.fontFamily
                    font.pixelSize: NovaTheme.fontL
                    font.bold: true
                }
                Text {
                    Layout.fillWidth: true
                    text: "Nova-Forge  ×  pyside-nova 组件库"
                    color: NovaTheme.textOnPrimary
                    opacity: 0.85
                    font.family: NovaTheme.fontFamily
                    font.pixelSize: NovaTheme.fontS
                }
                NovaChip {
                    text: "Nova UI"
                    filled: true
                    tint: Qt.rgba(1, 1, 1, 0.22)
                    dense: true
                }
            }
        }

        // ── 工具栏 ────────────────────────────────────────────
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            NovaToolbar { anchors.fill: parent }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: NovaTheme.spacingM
                anchors.rightMargin: NovaTheme.spacingM
                spacing: NovaTheme.spacingS

                NovaBtn {
                    text: "🔄 刷新"
                    size: "sm"
                    variant: "outlined"
                    onClicked: bridge.refresh()
                }
                NovaBtn {
                    text: "📝 更新 .qrc"
                    size: "sm"
                    disable: bridge.busy
                    loading: bridge.busy
                    onClicked: bridge.buildQrc()
                }
                NovaSeparator { vertical: true; spaced: true }
                NovaChip {
                    text: "资产 " + bridge.assetIcons.length
                    outlined: true
                    dense: true
                }
                NovaChip {
                    text: "资源 " + bridge.resourceIcons.length
                    outlined: true
                    dense: true
                }
                Item { Layout.fillWidth: true }
                NovaSpinner {
                    visible: bridge.busy
                    size: 22
                    variant: "ring"
                }
                NovaBtn {
                    text: NovaTheme.isDark ? "☀ 浅色主题" : "🌙 深色主题"
                    size: "sm"
                    variant: "flat"
                    onClicked: {
                        NovaTheme.isDark = !NovaTheme.isDark
                        bridge.setDarkTitleBar(NovaTheme.isDark)
                    }
                }
            }
        }

        // ── 左右双栏 ──────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: NovaTheme.spacingM
            spacing: NovaTheme.spacingM

            // 左：资产浏览
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                NovaCard { anchors.fill: parent; bordered: true }
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: NovaTheme.spacingM
                    spacing: NovaTheme.spacingS

                    Text {
                        text: "📥  浏览资产目录"
                        color: NovaTheme.textColor
                        font.family: NovaTheme.fontFamily
                        font.pixelSize: NovaTheme.fontM
                        font.bold: true
                    }
                    NovaSelect {
                        id: assetSelect
                        Layout.fillWidth: true
                        label: "资产文件夹"
                        emitValue: true
                        options: bridge.assetFolders
                        noOptionLabel: "未找到资产目录"
                        onModelValueChanged: {
                            var v = (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                            if (v !== "" && v !== "未找到资产目录")
                                bridge.selectAssetFolder(v)
                        }
                    }
                    NovaInput {
                        Layout.fillWidth: true
                        type: "search"
                        placeholder: "🔍 搜索资产图片…"
                        onModelValueChanged: bridge.setAssetFilter(
                            (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                        )
                    }
                    GridView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        cellWidth: 108
                        cellHeight: 108
                        model: bridge.assetIcons
                        delegate: assetDelegate
                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                            contentItem: Rectangle {
                                implicitWidth: 6
                                radius: 3
                                color: NovaTheme.outlineStrong
                            }
                            background: Rectangle { color: "transparent" }
                        }
                    }
                }
            }

            // 右：资源浏览
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                NovaCard { anchors.fill: parent; bordered: true }
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: NovaTheme.spacingM
                    spacing: NovaTheme.spacingS

                    Text {
                        text: "📦  浏览资源目录"
                        color: NovaTheme.textColor
                        font.family: NovaTheme.fontFamily
                        font.pixelSize: NovaTheme.fontM
                        font.bold: true
                    }
                    NovaSelect {
                        id: resSelect
                        Layout.fillWidth: true
                        label: "资源文件夹"
                        emitValue: true
                        options: bridge.resourceFolders
                        noOptionLabel: "未找到资源目录"
                        onModelValueChanged: {
                            var v = (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                            if (v !== "" && v !== "未找到资源目录")
                                bridge.selectResourceFolder(v)
                        }
                    }
                    NovaInput {
                        Layout.fillWidth: true
                        type: "search"
                        placeholder: "🔍 搜索资源图片…"
                        onModelValueChanged: bridge.setResourceFilter(
                            (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                        )
                    }
                    GridView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        cellWidth: 108
                        cellHeight: 108
                        model: bridge.resourceIcons
                        delegate: resDelegate
                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AsNeeded
                            contentItem: Rectangle {
                                implicitWidth: 6
                                radius: 3
                                color: NovaTheme.outlineStrong
                            }
                            background: Rectangle { color: "transparent" }
                        }
                    }
                }
            }
        }

        // ── 状态栏 ────────────────────────────────────────────
        NovaSeparator { Layout.fillWidth: true }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: NovaTheme.surface
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: NovaTheme.spacingM
                anchors.rightMargin: NovaTheme.spacingM
                Text {
                    Layout.fillWidth: true
                    text: bridge.statusText
                    color: NovaTheme.textMuted
                    font.family: NovaTheme.fontFamily
                    font.pixelSize: NovaTheme.fontS
                    elide: Text.ElideRight
                }
                Text {
                    text: bridge.currentAssetFolder + "  →  " + bridge.currentResourceFolder
                    color: NovaTheme.textMuted
                    font.family: NovaTheme.fontFamily
                    font.pixelSize: NovaTheme.fontS
                }
            }
        }
    }

    // ── 全局 tooltip 实例：parent 是整个窗口，气泡不再被 clamp 进 cell ──
    NovaTooltip {
        id: globalTip
        objectName: "globalTip"
        target: win.tipTarget === null ? idleAnchor : win.tipTarget
        text: win.tipText
        modelValue: win.tipVisible
        anchor: "bottom middle"
        self: "top middle"
        offset: [0, 8]
    }

    // ── 桥接信号 → Nova 服务 ─────────────────────────────────
    Connections {
        target: bridge

        function onToast(kind, message) {
            var tint = NovaTheme.info
            if (kind === "positive") tint = NovaTheme.positive
            else if (kind === "negative") tint = NovaTheme.negative
            else if (kind === "warning") tint = NovaTheme.warning
            NovaNotify.show({
                message: message,
                tint: tint,
                position: "bottom-right",
                timeout: 3200
            })
        }

        function onConfirmDelete(path, name) {
            NovaDialog.show({
                title: "确认删除",
                message: "确定从资源库删除 " + name + " 吗？\n（不会影响 assets 里的原文件）",
                ok: "删除",
                cancel: "取消",
                onOk: function () { bridge.deleteResource(path) }
            })
        }
    }
}
