# tests/test_scaffold_integration.py
# 创建时间：星期五 2026-11-27 10:40
"""T13：scaffold --project 非交互 + prescript 叠加 scaffold 通用骨架的契约回归。

纯逻辑层，不导入 PySide6（规避坑位 49）。
"""
from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestScaffoldProjectFlag(unittest.TestCase):
    def test_cli_registers_project_flag(self) -> None:
        cli = (SRC / "nova_forge" / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(cli)
        # scaffold parser 必须有 --project，且 func 消费 args
        self.assertIn('"--project"', cli)
        self.assertIn("func=lambda a: run_scaffolder(a.project)", cli)
        self.assertIsInstance(tree, ast.Module)

    def test_noninteractive_scaffold_writes_and_is_idempotent(self) -> None:
        from nova_forge.command.cmd_scaffolder import scaffold_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "nova_chat_app"
            first = scaffold_project(root, quiet=True)
            self.assertTrue(first["ok"])
            self.assertEqual(first["projectName"], "nova-chat-app")
            self.assertEqual(first["skipped"], [])  # 全新目录：全部写入，无跳过
            self.assertGreaterEqual(len(first["written"]), 11)
            self.assertTrue((root / "pyproject.toml").is_file())
            self.assertTrue((root / "LICENSE").is_file())
            self.assertTrue((root / "src" / "nova_chat_app" / "main.py").is_file())
            count = len(first["written"])

            second = scaffold_project(root, quiet=True)
            self.assertEqual(second["written"], [])  # 幂等：不覆盖
            self.assertEqual(len(second["skipped"]), count)

    def test_module_name_from_path(self) -> None:
        from nova_forge.core.scaffold_logic import module_name_from_path

        self.assertEqual(module_name_from_path("D:/x/Nova-Chat App"), "nova_chat_app")

    def test_write_plan_accepts_print_callback_and_force(self) -> None:
        """交互入口曾把 write_file(rel, tmpl) 当成 emit(msg) 传入导致 TypeError。"""
        from nova_forge.command.cmd_scaffolder import write_plan
        from nova_forge.core.scaffold_logic import DIR_SENTINEL

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = {"a.txt": "first", "sub": DIR_SENTINEL}
            messages: list[str] = []
            self.assertEqual(write_plan(plan, root, messages.append), ["a.txt", "sub"])
            self.assertEqual((root / "a.txt").read_text(encoding="utf-8"), "first")
            # force 覆盖
            plan["a.txt"] = "second"
            write_plan(plan, root, messages.append, force=True)
            self.assertEqual((root / "a.txt").read_text(encoding="utf-8"), "second")
            self.assertTrue(any("已覆盖生成" in m for m in messages))


class TestPrescriptOverlay(unittest.TestCase):
    def test_plan_includes_scaffold_common_files(self) -> None:
        from nova_forge.prescript.render import plan_project

        p = plan_project("chat", "/tmp/t13-overlay", "NovaChat App", "nova_chat_app", "0.5.0")
        for rel in ("LICENSE", "README_zh.md", "CHANGELOG.md",
                    "HOW_TO_PUBLISH.md", ".github/workflows/publish.yml",
                    "project_structure.txt"):
            self.assertIn(rel, p.files, rel)
        self.assertEqual(len(p.files), 17)

    def test_no_windows_case_collision_and_no_duplicate_entry(self) -> None:
        from nova_forge.prescript.render import plan_project

        p = plan_project("chat", "/tmp/t13-overlay", "NovaChat App", "nova_chat_app", "0.5.0")
        rels = set(p.files)
        # Windows 大小写不敏感：main.qml 与 Main.qml 不能并存
        self.assertIn("src/nova_chat_app/qml/Main.qml", rels)
        self.assertNotIn("src/nova_chat_app/qml/main.qml", rels)
        # T17：入口改名后 main.py 是启动器、app.py 是薄入口，__main__.py 退场；
        # scaffold 的 main.py 占位模板仍不得叠加进来覆盖启动器。
        self.assertIn("src/nova_chat_app/main.py", rels)
        self.assertIn("src/nova_chat_app/app.py", rels)
        self.assertNotIn("src/nova_chat_app/__main__.py", rels)
        self.assertIn("def main() -> int:", p.files["src/nova_chat_app/main.py"])

    def test_manifest_and_readme_match_actual_files(self) -> None:
        from nova_forge.prescript.render import plan_project

        p = plan_project("chat", "/tmp/t13-overlay", "NovaChat App", "nova_chat_app", "0.5.0")
        self.assertEqual(set(p.manifest["files"]), set(p.files))
        readme = p.files["README.md"]
        for rel in p.files:
            self.assertIn(rel, readme, rel)

    def test_hatch_reports_scaffold_result(self) -> None:
        from nova_forge.prescript.gui_model import GUIConfig, hatch

        with tempfile.TemporaryDirectory() as tmp:
            cfg = GUIConfig(kind="chat", path=tmp, name="NovaChat App",
                            package="nova_chat_app", force=False, dry_run=False,
                            verify_run=False)
            result = hatch(cfg, confirmed=True)
            self.assertTrue(result["ok"], result.get("message"))
            self.assertTrue(result["written"])
            self.assertTrue(result["scaffold"]["ok"])
            self.assertEqual(result["scaffold"]["projectName"], "nova-chat-app")
            root = Path(tmp) / "nova_chat_app"
            self.assertTrue((root / "LICENSE").is_file())
            manifest_files = set(json.loads(
                (root / "prescript.json").read_text(encoding="utf-8"))["files"])
            disk_files = {
                p.relative_to(root).as_posix()
                for p in root.rglob("*")
                if p.is_file() and "__pycache__" not in p.parts
            }
            self.assertEqual(manifest_files, disk_files)


if __name__ == "__main__":
    unittest.main()
