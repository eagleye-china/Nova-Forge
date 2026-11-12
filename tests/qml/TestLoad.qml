import QtQuick
import Nova 1.0

// 仅用于加载冒烟测试：验证 Nova 模块、Theme/Units 单例、NovaButton 可实例化。
Item {
    width: 320
    height: 120

    NovaButton {
        objectName: "smokeButton"
        anchors.centerIn: parent
        label: "OK"
        color: "positive"
    }
}
