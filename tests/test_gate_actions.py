# tests/test_gate_actions.py
# 创建时间：星期五 2026-11-27 12:28
"""T18：确认孵化框 CTA 固定在卡片右下角（CSA 截图红框位）静态契约。

按钮从 Flickable / Column 内容流移出，作为 gateCard 直接子项右下锚定；
Column 末尾留等高空白，保证滚到底时文字不被遮挡、内容区不缩水。

纯静态层，不创建 QGuiApplication（规避坑位 49）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

QML = SRC / "nova_forge" / "ui" / "qml" / "prescript_main.qml"


class TestGateActionsBottomRight(unittest.TestCase):
    def setUp(self) -> None:
        self.qml = QML.read_text(encoding="utf-8")

    def test_actions_anchored_bottom_right(self) -> None:
        block = self.qml[self.qml.index("id: gateActions"):
                         self.qml.index("// ── 界面预览浮层")]
        for token in (
            'objectName: "gateActions"',
            "right: parent.right; rightMargin: 22",
            "bottom: parent.bottom; bottomMargin: 16",
            'objectName: "gateCancelBtn"',
            'objectName: "gateConfirmBtn"',
            'text: "取消"',
            'text: "🤝 确认孵化"',
            "onClicked: win.gateOpen = false",
            "onClicked: bridge.hatch(true)",
            "disable: bridge.busy",
            "loading: bridge.busy",
            'variant: "outlined"',
            'variant: "filled"',
        ):
            self.assertIn(token, block, token)

    def test_actions_are_outside_content_flow(self) -> None:
        """CTA 只有一份、且不在滚动内容里；Column 末尾改为等高留白。"""
        self.assertEqual(self.qml.count('text: "取消"'), 1)
        self.assertEqual(self.qml.count('text: "🤝 确认孵化"'), 1)
        self.assertEqual(self.qml.count("id: gateActions"), 1)
        self.assertIn('objectName: "gateActionSpacer"', self.qml)
        spacer = self.qml[self.qml.index('objectName: "gateActionSpacer"') - 260:
                          self.qml.index('objectName: "gateActionSpacer"') + 200]
        self.assertIn("height: 46", spacer)
        self.assertIn("width: parent.width", spacer)
        # 内容区高度不被压缩：Flickable 仍锚到卡片底部
        self.assertIn("bottom: parent.bottom; bottomMargin: 16", self.qml)
        self.assertIn("contentHeight: gateCol.implicitHeight", self.qml)

    def test_button_order_cancel_then_confirm(self) -> None:
        """顺序「取消 → 确认孵化」，主按钮在最右。"""
        self.assertLess(self.qml.index('objectName: "gateCancelBtn"'),
                        self.qml.index('objectName: "gateConfirmBtn"'))

    def test_gate_still_uses_summary_and_group_box(self) -> None:
        """T15/T16 摘要与 GroupBox 契约不受按钮归位影响。"""
        for token in ("gateCard.m.version", "gateCard.keys",
                      'objectName: "keyFileGroupBox"', 'objectName: "keyFileGroup"'):
            self.assertIn(token, self.qml, token)


if __name__ == "__main__":
    unittest.main(verbosity=2)
