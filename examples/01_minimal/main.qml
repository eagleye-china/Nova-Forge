import QtQuick
import Nova 1.0

Window {
    id: win

    width: 760
    height: 520
    visible: true
    title: "PySide Nova · 最小示例"
    color: Theme.background

    Column {
        anchors.centerIn: parent
        spacing: Theme.spaceMd

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "NovaButton 属性矩阵"
            color: Theme.text_primary
            font.pixelSize: Theme.fontXl
            font.bold: true
        }

        // 1. 变体
        Row {
            spacing: Theme.spaceSm

            NovaButton {
                label: "Filled"
                onClicked: console.log("[demo] filled clicked")
            }
            NovaButton {
                label: "Outlined"
                color: "primary"
                variant: "outlined"
                onClicked: console.log("[demo] outlined clicked")
            }
            NovaButton {
                label: "Flat"
                color: "secondary"
                variant: "flat"
                onClicked: console.log("[demo] flat clicked")
            }
            NovaButton {
                label: "Text"
                variant: "text"
                onClicked: console.log("[demo] text clicked")
            }
        }

        // 2. 语义色
        Row {
            spacing: Theme.spaceSm

            NovaButton {
                label: "Positive"
                color: "positive"
            }
            NovaButton {
                label: "Negative"
                color: "negative"
            }
            NovaButton {
                label: "Warning"
                color: "warning"
            }
            NovaButton {
                label: "Info"
                color: "info"
            }
        }

        // 3. 尺寸
        Row {
            spacing: Theme.spaceSm

            NovaButton {
                label: "XS"
                size: "xs"
                dense: true
            }
            NovaButton {
                label: "SM"
                size: "sm"
                dense: true
            }
            NovaButton {
                label: "MD"
                size: "md"
            }
            NovaButton {
                label: "LG"
                size: "lg"
            }
            NovaButton {
                label: "XL"
                size: "xl"
            }
        }

        // 4. 状态
        Row {
            spacing: Theme.spaceSm

            NovaButton {
                label: "禁用"
                disabled: true
            }
            NovaButton {
                label: "加载中"
                loading: true
                color: "info"
            }
            NovaButton {
                label: "凸起"
                elevated: true
            }
            NovaButton {
                label: "非圆角"
                rounded: false
            }
        }

        // 5. 键盘焦点演示：按 Tab 切换，观察焦点环
        NovaButton {
            anchors.horizontalCenter: parent.horizontalCenter
            label: "Tab 到我，看焦点环"
            color: "secondary"
            variant: "outlined"
        }

        // 6. 主题切换
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Theme.spaceMd

            NovaButton {
                label: "切换明暗主题"
                variant: "flat"
                onClicked: novaTheme.toggle()
            }

            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: "当前模式：" + (novaTheme ? novaTheme.mode : "-")
                color: Theme.text_secondary
                font.pixelSize: Theme.fontMd
            }
        }
    }
}
