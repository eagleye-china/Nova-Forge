# tests/test_titlebar_and_hatch.py
# 迁移时间：星期五 2026-11-27 09:54（自 test_app_icons.py 拆出）
"""nova-forge 侧接线回归：配方图标路径 / 标题栏 DWM 同步 / 孵化产物自包含。

图标资产本身的测试已迁至 pyside-nova/tests/test_app_icons.py（图标新归属）。
本文件只校验 nova-forge 自己的源码与产物模板，不依赖图标磁盘位置。
纯逻辑 / 静态层，全程不导入 PySide6（规避坑位 49 的 pytest 生命周期 SIGSEGV）。
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.prescript import gui_model  # noqa: E402
from nova_forge.prescript.catalog import KINDS, icon_for  # noqa: E402
from nova_forge.prescript.render import plan_project  # noqa: E402
from nova_forge.resources.app_icons import ICONS  # noqa: E402

QML_GUI = SRC / "nova_forge" / "ui" / "qml" / "prescript_main.qml"
QML_ICONS = SRC / "nova_forge" / "ui" / "qml" / "icons_main.qml"


class TestRecipeIconWiring(unittest.TestCase):
    """配方卡片的图标路径由 catalog 单一事实源生成。"""

    def test_icon_for_and_kind_rows(self) -> None:
        for k in KINDS:
            self.assertEqual(icon_for(k.code), f"qrc:/icons/{k.icon}")
        self.assertEqual(icon_for("incubator"), "qrc:/icons/app-incubator.svg")
        self.assertEqual(icon_for("aireport"), "qrc:/icons/app-aireport.svg")
        with self.assertRaises(ValueError):
            icon_for("no-such-kind")
        rows = gui_model.kind_rows()
        self.assertEqual(len(rows), 9)
        for row, kind in zip(rows, KINDS, strict=True):
            self.assertEqual(row["icon"], f"qrc:/icons/{kind.icon}")


class TestDarkTitleBarWiring(unittest.TestCase):
    """标题栏：QML 属性绑定 → 桥接 Slot → DWM helper 的完整链路（静态契约）。"""

    def test_bridge_slots_declared(self) -> None:
        for rel in ("bridge/prescript_bridge.py", "bridge/icons_bridge.py"):
            tree = ast.parse((SRC / "nova_forge" / rel).read_text(encoding="utf-8"))
            slots = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "setDarkTitleBar":
                    decs = [ast.unparse(d) for d in node.decorator_list]
                    slots.append(decs)
            self.assertEqual(len(slots), 1, rel)
            self.assertTrue(any("Slot(bool)" in d for d in slots[0]), rel)

    def test_window_utils_api(self) -> None:
        tree = ast.parse(
            (SRC / "nova_forge" / "utils" / "window_utils.py").read_text(encoding="utf-8")
        )
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertIn("enable_dark_title_bar", names)   # 兼容旧 QtWidgets 调用方
        self.assertIn("apply_dark_title_bars", names)   # QML 主题同步入口
        self.assertIn("_apply_hwnd", names)

    def test_gui_qml_binds_theme_to_chrome(self) -> None:
        for qml in (QML_GUI, QML_ICONS):
            text = qml.read_text(encoding="utf-8")
            self.assertIn("property bool chromeDark: NovaTheme.isDark", text, qml.name)
            self.assertIn("onChromeDarkChanged: bridge.setDarkTitleBar(chromeDark)", text, qml.name)
            self.assertIn("bridge.setDarkTitleBar(", text, qml.name)

    def test_gui_shows_recipe_icons(self) -> None:
        text = QML_GUI.read_text(encoding="utf-8")
        self.assertIn("source: modelData.icon", text)
        self.assertIn("Image {", text)

    def test_gui_window_icon_and_initial_sync(self) -> None:
        text = (SRC / "nova_forge" / "command" / "cmd_prescript.py").read_text(encoding="utf-8")
        self.assertIn('QIcon(":/icons/app-incubator.svg")', text)
        self.assertIn("apply_dark_title_bars(True)", text)
        self.assertIn("from ..resources import resources_rc", text)

    def test_icons_window_initial_sync(self) -> None:
        text = (SRC / "nova_forge" / "command" / "cmd_icons.py").read_text(encoding="utf-8")
        self.assertIn("apply_dark_title_bars(True)", text)


class TestHatchedProjectCarriesIcon(unittest.TestCase):
    """孵化产物：独立工程自带图标 + 自包含标题栏 helper，清单/模板账实相符。"""

    def setUp(self) -> None:
        self.project = plan_project("chat", "/tmp/t12-probe", "T12 App", "t12_app", "0.5.0")

    def test_icon_file_embedded(self) -> None:
        rel = "src/t12_app/assets/app-chat.svg"
        self.assertIn(rel, self.project.files)
        self.assertEqual(self.project.files[rel], ICONS["app-chat.svg"])

    def test_manifest_lists_icon(self) -> None:
        self.assertIn("src/t12_app/assets/app-chat.svg", self.project.manifest["files"])

    def test_readme_tree_lists_icon(self) -> None:
        self.assertIn("app-chat.svg", self.project.files["README.md"])

    def test_bootstrap_self_contained(self) -> None:
        app = self.project.files["src/t12_app/main.py"]
        self.assertIn("setWindowIcon(QIcon", app)
        self.assertIn("_sync_title_bar", app)
        self.assertIn("darkChromeChanged.connect", app)
        self.assertIn("APP_ICON", app)
        ast.parse(app)  # 产物 main.py 必须是合法 Python

    def test_entry_rename_layout(self) -> None:
        """T17：app.py 薄入口 / main.py 启动器 / 无 __main__.py。"""
        files = self.project.files
        self.assertIn("src/t12_app/app.py", files)
        self.assertIn("src/t12_app/main.py", files)
        self.assertNotIn("src/t12_app/__main__.py", files)
        self.assertIn("from .main import main", files["src/t12_app/app.py"])
        ast.parse(files["src/t12_app/app.py"])
        self.assertIn("def main() -> int:", files["src/t12_app/main.py"])

    def test_host_qml_emits_signal(self) -> None:
        main = self.project.files["src/t12_app/qml/Main.qml"]
        self.assertIn("signal darkChromeChanged(bool dark)", main)
        self.assertIn('darkChromeChanged(win.themeMode === "signature")', main)
        self.assertIn("darkChromeChanged(true)", main)
        # 离屏实跑无 context property，模板不得引入新的 QML 外部依赖
        self.assertNotIn("chrome.", main)
        # 模板残留占位符检查（与产物 smoke 同源）
        self.assertEqual(main.count("${"), 0)

    def test_smoke_asserts_new_contract(self) -> None:
        smoke = self.project.files["tests/test_smoke.py"]
        self.assertIn("test_app_icon_present", smoke)
        self.assertIn("test_title_bar_sync_wired", smoke)
        ast.parse(smoke)

    def test_all_nine_kinds_embed_own_icon(self) -> None:
        for kind in KINDS:
            p = plan_project(kind.code, "/tmp/t12-all", "A", "a_pkg", "0.5.0")
            rel = f"src/a_pkg/assets/{kind.icon}"
            self.assertIn(rel, p.files, kind.code)
            self.assertEqual(p.files[rel], ICONS[kind.icon], kind.code)


class TestPreviewTitleIcon(unittest.TestCase):
    """预览浮层标题图标随 previewKind 切换，不再用固定 emoji。"""

    def test_preview_header_uses_dynamic_nova_icon(self) -> None:
        qml = QML_GUI.read_text(encoding="utf-8")
        self.assertIn('win.previewKindSpec() ? "img:" + win.previewKindSpec().icon : ""', qml)
        self.assertIn("monochrome: false", qml)
        # 固定的 👁 emoji 已移除（否则每配方看到的都是同一图标）
        self.assertNotIn("👁", qml)
        self.assertIn('text: "界面预览 · "', qml)

    def test_all_kinds_have_matching_qrc_alias(self) -> None:
        """九配方 code 与 qrc 的 app-<code> 别名一一对应。"""
        from xml.etree import ElementTree as ET

        qrc = ROOT.parent / "pyside-nova" / "src" / "pyside_nova" / "resources" / "resources.qrc"
        aliases = {
            el.get("alias")
            for r in ET.parse(qrc).getroot().findall("qresource")
            for el in r.findall("file")
        }
        for kind in KINDS:
            self.assertIn(f"app-{kind.code}", aliases, kind.code)
        self.assertIn("app-incubator", aliases)
        self.assertIn("app-aireport", aliases)

    def test_workbench_qrc_aliases_match_catalog_icon_files(self) -> None:
        """工作台 qrc 以 catalog.Kind.icon 文件名作别名（带 .svg），与 QML/QIcon 引用一致。"""
        from xml.etree import ElementTree as ET

        qrc = SRC / "nova_forge" / "resources" / "resources.qrc"
        aliases = {
            el.get("alias")
            for r in ET.parse(qrc).getroot().findall("qresource")
            for el in r.findall("file")
        }
        for kind in KINDS:
            self.assertIn(kind.icon, aliases, kind.code)
        self.assertIn("app-incubator.svg", aliases)
        self.assertIn("app-aireport.svg", aliases)


if __name__ == "__main__":
    unittest.main()
