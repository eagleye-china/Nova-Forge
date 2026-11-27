# scripts/verify_prescript_app.py
# 创建时间：星期四 2026-11-26 15:50
"""离屏实跑校验：加载 prescript 产物 Main.qml，收集 QML 运行时告警。

用法：
    python scripts/verify_prescript_app.py .prescript_test/chat-app mei_chat

退出码：0 = 无 ERROR、根对象存在；2 = 加载失败；3 = 有运行时 ERROR。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtQuick import QQuickWindow

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from pyside_nova import init_nova

CASES = {
    "agent": "NovaAgent", "copilot": "NovaCopilot", "de": "NovaDE",
    "orbit": "NovaOrbit", "desktop": "NovaDesktop", "chat": "NovaChat",
    "mobile": "NovaMobile", "flex": "NovaFlexLayout", "wizard": "NovaSetupWizard",
}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法：verify_prescript_app.py <工程目录> [包名]")
        return 2
    root = Path(argv[1]).resolve()
    main_qml = root / "src" / (argv[2] if len(argv) > 2 else "") / "qml" / "Main.qml"
    if not main_qml.exists():
        candidates = list((root / "src").glob("*/qml/Main.qml"))
        if not candidates:
            print(f"✗ 未找到 Main.qml：{root}")
            return 2
        main_qml = candidates[0]

    messages: list[str] = []

    def handler(_mode, _ctx, message: str) -> None:
        messages.append(message)

    qInstallMessageHandler(handler)

    app = QGuiApplication(sys.argv[:1])
    engine = QQmlApplicationEngine()
    init_nova(engine)
    engine.load(str(main_qml))
    roots = engine.rootObjects()
    if not roots:
        print(f"✗ QML 加载失败：{main_qml}")
        for m in messages:
            print("   ", m)
        return 2
    window = roots[0]  # 立即持引用：延迟回调里再取会被降级成 QWindow 包装

    shot = os.environ.get("PRESCRIPT_SHOT")
    if shot:
        # 同步抓图：此刻 rootObjects 仍是 QQuickWindow 包装；进入事件循环后会被降级
        image = QQuickWindow.grabWindow(window)
        if not image.isNull():
            image.save(shot)
            print(f"📸 截图：{shot} ({image.width()}×{image.height()})")

    QTimer.singleShot(1500, app.quit)
    app.exec()

    stage = main_qml.with_name("Stage.qml").read_text(encoding="utf-8")
    shell = next((s for s in CASES.values() if s in stage), "?")
    errors = [m for m in messages if "error" in m.lower() or "Error" in m]
    warnings = [m for m in messages if m not in errors]

    print(f"✓ 根对象 {len(roots)} 个 · Stage 壳 {shell} · 运行 1.5 s")
    if warnings:
        print(f"⚠ 告警 {len(warnings)} 条：")
        for m in warnings[:12]:
            print("   ", m)
    if errors:
        print(f"✗ 错误 {len(errors)} 条：")
        for m in errors[:12]:
            print("   ", m)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
