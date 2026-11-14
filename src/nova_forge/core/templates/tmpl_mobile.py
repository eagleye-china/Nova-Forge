# src/nova_forge/core/templates/tmpl_mobile.py

MOBILE_MAIN_PY_TMPL = """# src/$MODULE_NAME/main.py

import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

def main() -> int:
    app = QGuiApplication(sys.argv)

    # ✅ 移动端特有设置：锁定屏幕方向（如竖屏）
    # from PySide6.QtCore import Qt
    # app.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi) # 可选

    engine = QQmlApplicationEngine()
    qml_file = Path(__file__).parent / "qml" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        return -1

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
"""

MOBILE_MAIN_QML_TMPL = """// src/$MODULE_NAME/qml/main.qml

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 400
    height: 800
    title: "$PROJECT_NAME (Mobile)"

    // 移动端暗黑风
    color: "#121212"

    Text {
        anchors.centerIn: parent
        text: "Welcome to $PROJECT_NAME Mobile! 📱"
        color: "#64B5F6"
        font.pixelSize: 24
        font.bold: true
    }
}
"""
