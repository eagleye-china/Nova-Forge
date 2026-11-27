# tests/test_file_choices.py
# 创建时间：星期五 2026-11-27 11:05
"""文件组选框回归：预知清单 / 按选落盘 / manifest 与 README 账实同源。

纯逻辑层，不导入 PySide6（规避坑位 49 的 pytest 收尾 SIGSEGV）。
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova_forge.prescript.gui_model import (  # noqa: E402
    GUIConfig,
    file_choices,
    hatch,
    plan_summary,
)


class TestFileChoices(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(tempfile.mkdtemp())
        self.cfg = GUIConfig(
            kind="chat", path=str(self.workspace),
            name="Demo App", package="demo_app",
        )

    def test_full_choices_list_all_known_files(self) -> None:
        choices = file_choices(self.cfg)
        self.assertEqual(len(choices), 17)
        self.assertTrue(all(c["selected"] for c in choices))
        paths = [c["path"] for c in choices]
        for expected in ("pyproject.toml", "README.md", "prescript.json",
                         "src/demo_app/qml/Main.qml", "src/demo_app/qml/Stage.qml"):
            self.assertIn(expected, paths)
        self.assertEqual(len({c["path"] for c in choices}), len(choices))
        # project_structure.txt 是合法空文件（坑位 58），size 为 0 属预期
        self.assertTrue(all(c["size"] >= 0 for c in choices))

    def test_summary_counts_only_selected(self) -> None:
        self.assertEqual(plan_summary(self.cfg)["fileCount"], 17)
        self.cfg.selected_files = ["pyproject.toml", "README.md"]
        summary = plan_summary(self.cfg)
        self.assertEqual(summary["fileCount"], 2)
        # README 含结构树，选中子集后体量会缩短；以预览自身行数自洽为准
        self.assertEqual(summary["bytes"],
                         sum(row["size"] for row in summary["files"]))

    def test_hatch_writes_only_selected_subset(self) -> None:
        dropped = "project_structure.txt"
        self.cfg.selected_files = [c["path"] for c in file_choices(self.cfg)
                                   if c["path"] != dropped]
        result = hatch(self.cfg, confirmed=True)
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(result["summary"]["fileCount"], 16)

        root = self.workspace / "demo_app"
        disk = sorted(str(p.relative_to(root)).replace("\\", "/")
                      for p in root.rglob("*") if p.is_file())
        self.assertEqual(len(disk), 16)
        self.assertNotIn(dropped, disk)

        manifest = json.loads((root / "prescript.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(manifest["files"]), disk)
        self.assertNotIn(dropped, (root / "README.md").read_text(encoding="utf-8"))

    def test_empty_selection_is_rejected(self) -> None:
        self.cfg.selected_files = []
        result = hatch(self.cfg, confirmed=True)
        self.assertFalse(result["ok"])
        self.assertFalse(result["written"])
        self.assertIn("未勾选任何文件", result["message"])
        self.assertFalse((self.workspace / "demo_app").exists())

    def test_partial_selection_skips_scaffold_backfill(self) -> None:
        """按选落盘时 scaffold 不得把用户取消的治理文件补回来。"""
        self.cfg.selected_files = [
            c["path"] for c in file_choices(self.cfg)
            if c["path"] != "HOW_TO_PUBLISH.md"
        ]
        hatch(self.cfg, confirmed=True)
        root = self.workspace / "demo_app"
        self.assertFalse((root / "HOW_TO_PUBLISH.md").exists())


class TestHatchDialogSummary(unittest.TestCase):
    """确认孵化框摘要：从 pyproject.toml 解析，账实同源。"""

    def setUp(self) -> None:
        self.workspace = Path(tempfile.mkdtemp())
        self.cfg = GUIConfig(
            kind="chat", path=str(self.workspace),
            name="NovaChat", package="nova_chat",
        )

    def test_meta_parsed_from_generated_pyproject(self) -> None:
        meta = plan_summary(self.cfg)["meta"]
        self.assertEqual(meta["distName"], "nova-chat")
        self.assertEqual(meta["version"], "0.1.0")
        self.assertEqual(meta["license"], "MIT")
        self.assertEqual(meta["python"], ">=3.10")
        self.assertTrue(meta["author"])  # 作者来自模板单一事实源
        self.assertIn("NovaChat", meta["description"])

    def test_meta_matches_on_disk_pyproject(self) -> None:
        """摘要字段必须与真正落盘的 pyproject.toml 逐字一致。"""
        meta = plan_summary(self.cfg)["meta"]
        hatch(self.cfg, confirmed=True)
        text = (self.workspace / "nova_chat" / "pyproject.toml").read_text(
            encoding="utf-8")
        self.assertIn(f'version = "{meta["version"]}"', text)
        self.assertIn(f'name = "{meta["distName"]}"', text)
        self.assertIn(f'name = "{meta["author"]}"', text)

    def test_key_files_are_user_facing_essentials(self) -> None:
        keys = [k["path"] for k in plan_summary(self.cfg)["keyFiles"]]
        self.assertEqual(keys, ["pyproject.toml", "README.md", "README_zh.md",
                                "LICENSE", "CHANGELOG.md"])

    def test_key_files_reflect_selection(self) -> None:
        """T15 契约：5 项恒列，取消勾选只置 included=false（随时可勾回）。"""
        self.cfg.selected_files = ["pyproject.toml", "LICENSE"]
        key_map = {k["path"]: k["included"]
                   for k in plan_summary(self.cfg)["keyFiles"]}
        self.assertEqual(len(key_map), 5)
        self.assertTrue(key_map["pyproject.toml"])
        self.assertTrue(key_map["LICENSE"])
        for path in ("README.md", "README_zh.md", "CHANGELOG.md"):
            self.assertFalse(key_map[path], path)

    def test_prescript_and_scaffold_pyproject_meta_same_source(self) -> None:
        """作者/版本在 prescript 与 scaffold 两条生成链路逐字同源。"""
        from nova_forge.core.scaffold_logic import scaffold_file_plan

        root = str(self.workspace / "nova_chat")
        scaffold_toml = scaffold_file_plan(root)["pyproject.toml"]
        from nova_forge.prescript.render import plan_project
        prescript_toml = plan_project(
            "chat", root, "NovaChat", "nova_chat"
        ).files["pyproject.toml"]
        for key in ("version", "authors"):
            s = next(line for line in scaffold_toml.splitlines()
                     if line.startswith(f"{key} ="))
            p = next(line for line in prescript_toml.splitlines()
                     if line.startswith(f"{key} ="))
            self.assertEqual(s, p, key)

    def test_qml_gate_renders_summary_fields(self) -> None:
        qml = (ROOT / "src/nova_forge/ui/qml/prescript_main.qml").read_text(
            encoding="utf-8")
        for field in ("gateCard.m.version", "gateCard.m.author",
                     "gateCard.m.distName", "gateCard.m.description",
                     "gateCard.m.license", "gateCard.keys"):
            self.assertIn(field, qml, field)
        self.assertIn("将创建的主要文件", qml)


if __name__ == "__main__":
    unittest.main()
