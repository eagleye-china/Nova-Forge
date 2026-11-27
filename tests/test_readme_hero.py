# tests/test_readme_hero.py
# 创建时间：星期五 2026-11-27 11:56
"""T16：英雄卡 README 按钮（当前选中应用的组件说明 md）+ 左右轨隐显按钮归位。

内容源由 CSA 2026-11-27 指定：``pyside-nova/docs/components/<shell>.md``，
九配方与文档一一对应，文件名由 ``catalog.Kind.shell`` 单一事实源推导；
组件文档缺失时回退到将落盘的 README.md（``plan_summary.readme``）。

纯逻辑 / 静态契约层，不创建 QGuiApplication（规避坑位 49 的收尾 SIGSEGV）。
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.prescript import gui_model  # noqa: E402
from nova_forge.prescript.catalog import KINDS  # noqa: E402

QML = SRC / "nova_forge" / "ui" / "qml" / "prescript_main.qml"
DOCS = ROOT.parent / "pyside-nova" / "docs" / "components"


def _cfg(tmp: str, **overrides) -> gui_model.GUIConfig:
    data = {"kind": "chat", "path": tmp, "name": "Demo App", "package": "demo_app"}
    data.update(overrides)
    return gui_model.GUIConfig.from_mapping(data)


class TestComponentDocSingleSource(unittest.TestCase):
    """九配方 ↔ docs/components/<shell>.md，读的是生成器产物本身。"""

    def test_all_nine_kinds_have_their_own_doc(self) -> None:
        for k in KINDS:
            doc = gui_model.component_doc(k.code)
            self.assertTrue(doc["found"], k.code)
            self.assertEqual(doc["title"], f"{k.shell}.md", k.code)
            self.assertEqual(doc["source"], str(DOCS / f"{k.shell}.md"), k.code)
            self.assertIn(k.shell, doc["text"], k.code)
            self.assertIn("pyside-nova docs/components", doc["note"])

    def test_document_is_the_generated_one_not_a_copy(self) -> None:
        """账实同源：逐字等于 gen_apidocs.py 生成的那份 md。"""
        doc = gui_model.component_doc("chat")
        self.assertEqual(doc["text"], (DOCS / "NovaChat.md").read_text(encoding="utf-8"))
        self.assertIn("禁止手工编辑", doc["text"])

    def test_render_text_degrades_images_while_text_stays_verbatim(self) -> None:
        """T23 / 坑位 76：显示适配版不加载史料截图，原文逐字保留供追溯。

        docs/components/*.md 的 ``![alt](../screenshots/*.png)`` 会被
        Text.MarkdownText 按 QML 组件目录解析而刷 Cannot open 告警；紧凑英雄卡
        也不适合内嵌 1280×800 截图。故 renderText 降级为文本占位，text 不动。
        """
        raw = (DOCS / "NovaChat.md").read_text(encoding="utf-8")
        doc = gui_model.component_doc("chat")
        self.assertIn("![浅色](../screenshots/chat_showcase_light.png)", raw)
        self.assertEqual(doc["text"], raw, "逐字原文不得被显示适配改写")
        self.assertNotIn("![", doc["renderText"], "显示适配版不得残留图片语法")
        self.assertIn("浅色（展示图 · 见仓库）", doc["renderText"])
        self.assertIn("## 概览", doc["renderText"], "正文/标题须完整保留")

    def test_unknown_kind_raises(self) -> None:
        with self.assertRaises(ValueError):
            gui_model.component_doc("wat")

    def test_explicit_env_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "NovaChat.md"
            fake.write_text("# override\n", encoding="utf-8")
            old = os.environ.get("NOVA_COMPONENT_DOCS")
            os.environ["NOVA_COMPONENT_DOCS"] = tmp
            try:
                doc = gui_model.component_doc("chat")
            finally:
                if old is None:
                    os.environ.pop("NOVA_COMPONENT_DOCS", None)
                else:
                    os.environ["NOVA_COMPONENT_DOCS"] = old
            self.assertTrue(doc["found"])
            self.assertEqual(doc["text"], "# override\n")
            self.assertEqual(doc["source"], str(fake))


class TestReadmeFallback(unittest.TestCase):
    """组件文档缺失时的回退内容 = 将落盘的 README.md（账实同源）。"""

    def test_summary_readme_equals_planned_file(self) -> None:
        from nova_forge.prescript.render import plan_project

        with tempfile.TemporaryDirectory() as tmp:
            summary = gui_model.plan_summary(_cfg(tmp))
            project = plan_project(
                "chat", summary["root"], "Demo App", "demo_app",
                gui_model.forge_version(),
            )
            self.assertEqual(summary["readme"], project.files["README.md"])

    def test_readme_follows_current_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            chat = gui_model.plan_summary(_cfg(tmp))["readme"]
            agent = gui_model.plan_summary(_cfg(tmp, kind="agent"))["readme"]
            self.assertNotEqual(chat, agent)
            self.assertIn("P6", chat)
            self.assertIn("P1", agent)

    def test_readme_empty_when_file_unchecked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _cfg(tmp, selected_files=["pyproject.toml", "LICENSE"])
            self.assertEqual(gui_model.plan_summary(cfg)["readme"], "")


class TestBridgeReadmeDoc(unittest.TestCase):
    """桥接层：切换配方即换文档；组件文档缺失时回退到 readmeText。"""

    def _bridge(self, tmp: str):
        from nova_forge.bridge.prescript_bridge import PrescriptBridge

        bridge = PrescriptBridge()
        bridge.setPath(tmp)
        bridge.setName("Demo App")
        return bridge

    def test_doc_follows_current_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = self._bridge(tmp)
            self.assertEqual(bridge.readmeDoc["title"], "NovaChat.md")
            self.assertTrue(bridge.readmeDoc["found"])
            chat_text = bridge.readmeDoc["text"]
            chat_render = bridge.readmeDoc["renderText"]
            self.assertNotIn("![", chat_render)
            bridge.setKind("agent")
            self.assertEqual(bridge.readmeDoc["title"], "NovaAgent.md")
            self.assertNotEqual(bridge.readmeDoc["text"], chat_text)
            self.assertNotEqual(bridge.readmeDoc["renderText"], chat_render)

    def test_doc_still_available_when_readme_unchecked(self) -> None:
        """组件文档优先：取消勾选 README.md 不影响英雄卡文档展示。"""
        with tempfile.TemporaryDirectory() as tmp:
            bridge = self._bridge(tmp)
            bridge.setFileSelected("README.md", False)
            self.assertEqual(bridge.readmeText, "")
            self.assertEqual(bridge.readmeDoc["title"], "NovaChat.md")

    def test_fallback_when_component_docs_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = self._bridge(tmp)
            missing = {"found": False, "title": "NovaChat.md", "text": "",
                       "note": "组件文档未安装", "source": ""}
            with mock.patch.object(gui_model, "component_doc", return_value=missing):
                doc = bridge.readmeDoc
            self.assertEqual(doc["title"], "README.md")
            self.assertEqual(doc["text"], bridge.readmeText)
            self.assertEqual(doc["renderText"], bridge.readmeText)
            self.assertIn("逐字同源", doc["note"])

    def test_fallback_reports_unchecked_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = self._bridge(tmp)
            bridge.setFileSelected("README.md", False)
            missing = {"found": False, "title": "", "text": "", "note": "", "source": ""}
            with mock.patch.object(gui_model, "component_doc", return_value=missing):
                doc = bridge.readmeDoc
            self.assertEqual(doc["text"], "")
            self.assertEqual(doc["renderText"], "")
            self.assertIn("未勾选", doc["note"])


class TestHeroAndFoldButtons(unittest.TestCase):
    """QML 静态契约：英雄卡 README / 库组件 / 折叠按钮位置。"""

    def setUp(self) -> None:
        self.qml = QML.read_text(encoding="utf-8")

    def test_hero_card_readme_button_and_markdown_renderer(self) -> None:
        """T23：README 展开区改用库组件 NovaMarkdown 渲染 md，而非裸 Text 源码。"""
        for token in (
            'id: heroCard', 'objectName: "heroCard"',
            'property bool readmeOpen: false',
            'height: heroCard.readmeOpen ? 400 : 68',
            'objectName: "readmeBtn"',
            'text: heroCard.readmeOpen ? "✕ 收起" : "📄 README"',
            'onClicked: heroCard.readmeOpen = !heroCard.readmeOpen',
            'NovaMarkdown {', 'objectName: "readmeMarkdown"',
            'markdown: bridge.readmeDoc.renderText',
            'showToc: true', 'outlined: false',
            'bridge.readmeDoc.title', 'bridge.readmeDoc.renderText',
            'objectName: "readmeCaption"',
        ):
            self.assertIn(token, self.qml, token)

    def test_no_plain_text_source_rendering(self) -> None:
        """T23 回归：不得再出现 PlainText / 等宽源码字体的 md 源码展示。"""
        self.assertNotIn("textFormat: Text.PlainText", self.qml)
        self.assertNotIn('family: "Consolas"', self.qml)
        self.assertNotIn('objectName: "readmeBody"', self.qml)
        self.assertNotIn('id: readmeScroll', self.qml)

    def test_markdown_uses_library_component_and_safe_links(self) -> None:
        """库组件优先 + 危险协议交宿主 toast 单一事实源，不另立通知链路。"""
        self.assertIn("import Nova.Controls", self.qml)
        self.assertEqual(self.qml.count("NovaMarkdown {"), 1)
        self.assertIn("openLinksExternally: false", self.qml)
        self.assertIn("win.showToast(\"info\", \"文档链接：\" + url)", self.qml)
        self.assertIn("win.showToast(\"warning\", \"已拦截危险链接：\" + url)", self.qml)
        self.assertIn("function showToast(kind, message)", self.qml)
        # 窗口级 showToast 是 NovaNotify.show({...}) 的唯一实际调用点
        self.assertEqual(self.qml.count("NovaNotify.show({"), 1)

    def test_gui_extra_requires_nova_markdown_version(self) -> None:
        """账实相符：NovaMarkdown 自 pyside-nova 1.4.0 起导出，依赖下限须 >=1.4.0。"""
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"pyside-nova>=1.4.0"', pyproject)
        self.assertNotIn('"pyside-nova>=1.3.0"', pyproject)

    def test_readme_content_not_hardcoded(self) -> None:
        """不得在 QML 里复制一份文档台账：内容必须来自 bridge。"""
        self.assertNotIn("bridge.readmeText !== \"\"", self.qml)
        self.assertIn("bridge.readmeDoc", self.qml)

    def test_fold_buttons_in_global_slot_corners(self) -> None:
        g = self.qml[self.qml.index("globalSlot:"): self.qml.index("// ── ② 配方库")]
        for token in (
            'objectName: "foldRecipeBtn"', 'objectName: "foldValidateBtn"',
            "onClicked: shell.toggleRecipe()", "onClicked: shell.toggleValidate()",
            "anchors { left: parent.left; leftMargin: 10",
            "anchors { right: parent.right; rightMargin: 10",
            "anchors { left: foldRecipeBtn.right",
            "anchors { right: foldValidateBtn.left",
            "ToolTip.text: shell.recipeCollapsed", "ToolTip.text: shell.validateCollapsed",
        ):
            self.assertIn(token, g, token)

    def test_pipeline_no_longer_has_fold_buttons(self) -> None:
        p = self.qml[self.qml.index("pipelineSlot:"): self.qml.index("// ── ⑥ 孵化摘要证书")]
        self.assertNotIn("toggleRecipe()", p)
        self.assertNotIn("toggleValidate()", p)
        self.assertNotIn("foldRecipeBtn", p)
        self.assertNotIn("折叠图标", p)

    def test_ids_are_unique(self) -> None:
        for name in ("heroCard", "readmeBtn", "readmeMarkdown", "readmeCaption",
                     "readmePane", "foldRecipeBtn", "foldValidateBtn",
                     "foldRecipeArea", "foldValidateArea"):
            self.assertEqual(self.qml.count(f"id: {name}"), 1, name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
