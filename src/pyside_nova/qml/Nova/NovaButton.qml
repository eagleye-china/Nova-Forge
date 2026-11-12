// NovaButton.qml
// ---------------------------------------------------------------------------
// 企业级按钮原语（Material 语义，纯 Qt Quick 实现，无 QtQuick.Controls 依赖）
//
// 属性契约（与 pyside-quasar 的 QuasarButton 保持一致）：
//   color / variant / size / rounded / elevated / dense / loading / disabled
//   label / icon / iconRight
//
// 交互：鼠标、触摸（TapHandler）、键盘（Space / Enter）三模一致
// 无障碍：默认暴露 Accessible.Button 角色
// ---------------------------------------------------------------------------
pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    // ── 公共属性（属性契约，勿擅自改名 / 加同义别名）
    property string label: ""
    property url icon: ""
    property url iconRight: ""
    property string color: "primary"      // 语义色名，取值见 theme/tokens.py
    property string variant: "filled"     // filled | outlined | flat | text | push
    property string size: "md"            // xs | sm | md | lg | xl | <int px>
    property bool rounded: true
    property bool elevated: false
    property bool dense: false
    property bool loading: false
    property bool disabled: false

    signal clicked()

    // ── 派生状态（只读，禁止外部改写）
    readonly property bool hovered: hoverHandler.hovered
    readonly property bool down: tapHandler.pressed
    readonly property bool interactive: !disabled && !loading
    readonly property color accent: Theme.colorOf(color)
    readonly property int hPad: dense ? Units.px(Theme.spaceSm) : Units.px(Theme.spaceMd)
    readonly property int iconPx: Units.px(Math.round(Theme.buttonHeight(size) * 0.5))
    readonly property int radiusPx: !rounded ? 0 : (size === "xs" || size === "sm" ? Theme.radiusSm : Theme.radiusMd)

    readonly property color bgColor: {
        if (!interactive) {
            const plain = variant === "outlined" || variant === "flat" || variant === "text"
            return plain ? "transparent" : Theme.disabled
        }
        return (variant === "filled" || variant === "push") ? accent : "transparent"
    }

    readonly property color fgColor: {
        if (!interactive)
            return (variant === "filled" || variant === "push") ? Theme.white : Theme.text_secondary
        if (variant === "filled" || variant === "push")
            return Theme.contrast(accent)
        return accent
    }

    implicitHeight: Units.px(Theme.buttonHeight(size))
    implicitWidth: Math.max(implicitHeight * 2, contentRow.implicitWidth + hPad * 2)

    activeFocusOnTab: interactive
    opacity: disabled ? 0.85 : 1.0

    Accessible.role: Accessible.Button
    Accessible.name: label
    Accessible.focusable: true

    // ── 阴影（elevated）
    Rectangle {
        anchors.fill: bg
        anchors.topMargin: Units.px(2)
        visible: root.elevated && root.variant !== "flat" && root.variant !== "text"
        radius: bg.radius
        color: "#000000"
        opacity: root.interactive ? 0.16 : 0.06
        z: -1
    }

    // ── 底：填充 / 描边
    Rectangle {
        id: bg
        anchors.fill: parent
        radius: root.radiusPx
        color: root.bgColor
        border.width: root.variant === "outlined" ? Units.px(1) : 0
        border.color: root.accent

        Behavior on color {
            ColorAnimation {
                duration: Theme.durationFast
            }
        }
    }

    // ── 状态层（hover / pressed）
    Rectangle {
        anchors.fill: bg
        radius: bg.radius
        color: root.fgColor
        opacity: {
            if (!root.interactive)
                return 0
            if (root.down)
                return 0.12
            if (root.hovered)
                return 0.08
            return 0
        }
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.durationFast
            }
        }
    }

    // ── 内容：左图标 + 文本 + 右图标
    Row {
        id: contentRow
        anchors.centerIn: parent
        spacing: Units.px(6)
        opacity: root.loading ? 0 : 1

        Image {
            anchors.verticalCenter: parent.verticalCenter
            visible: root.icon.toString() !== ""
            source: root.icon
            sourceSize.width: root.iconPx
            sourceSize.height: root.iconPx
            fillMode: Image.PreserveAspectFit
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            visible: root.label !== ""
            text: root.label
            color: root.fgColor
            font.pixelSize: Theme.fontSizeFor(root.size)
            font.bold: true
            elide: Text.ElideRight
        }

        Image {
            anchors.verticalCenter: parent.verticalCenter
            visible: root.iconRight.toString() !== ""
            source: root.iconRight
            sourceSize.width: root.iconPx
            sourceSize.height: root.iconPx
            fillMode: Image.PreserveAspectFit
        }
    }

    // ── 加载指示（三点脉冲，GPU 友好、无 Controls 依赖）
    Row {
        anchors.centerIn: parent
        spacing: Units.px(3)
        visible: root.loading

        Repeater {
            model: 3

            Rectangle {
                id: dot

                required property int index

                width: Units.px(4)
                height: width
                radius: width / 2
                color: root.fgColor

                SequentialAnimation on opacity {
                    running: root.loading
                    loops: Animation.Infinite
                    PauseAnimation {
                        duration: dot.index * 150
                    }
                    NumberAnimation {
                        to: 1.0
                        duration: 300
                        easing.type: Easing.InOutQuad
                    }
                    NumberAnimation {
                        to: 0.3
                        duration: 300
                        easing.type: Easing.InOutQuad
                    }
                }
            }
        }
    }

    // ── 焦点环（统一由该原语绘制，组件不要各自实现）
    Rectangle {
        anchors.fill: bg
        anchors.margins: -Units.px(2)
        radius: bg.radius + Units.px(2)
        color: "transparent"
        border.width: Units.px(2)
        border.color: Theme.focus
        visible: root.activeFocus && root.interactive
        opacity: 0.9
    }

    // ── 输入
    HoverHandler {
        id: hoverHandler
        enabled: root.interactive
        cursorShape: root.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    TapHandler {
        id: tapHandler
        enabled: root.interactive
        onTapped: root.clicked()
    }

    Keys.onPressed: function (event) {
        if (!root.interactive)
            return
        if (event.key === Qt.Key_Space || event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            root.clicked()
            event.accepted = true
        }
    }
}
