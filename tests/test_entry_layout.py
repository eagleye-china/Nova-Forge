# tests/test_entry_layout.py
# 创建时间：星期五 2026-11-27 12:11
"""T17：prescript 产物入口改名（app.py→main.py / __main__.py→app.py）契约回归。

CSA 2026-11-27 拍板：孵化工程里不再出现 ``__main__.py``；``app.py`` 是薄入口、
``main.py`` 是启动器。改名必须连带打通导入链 / pyproject scripts / manifest
entry / README / CLI 提示 / GUI 返回命令 / 离屏实跑，法源链不留悬空引用。

纯逻辑 / 静态层，不导入 PySide6（规避坑位 49）。
"""
from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.prescript.catalog import KINDS  # noqa: E402
from nova_forge.prescript.gui_model import (  # noqa: E402
    GUIConfig,
    file_choices,
    hatch,
    plan_summary,
)
from nova_forge.prescript.render import plan_project  # noqa: E402


class TestPlannedEntryLayout(unittest.TestCase):
    """内存快照：文件名、内容、入口引用逐项对齐。"""

    def setUp(self) -> None:
        self.p = plan_project("chat", "/tmp/t17-plan", "T17 App", "t17_app", "0.5.0")

    def test_no_dunder_main_module(self) -> None:
        self.assertNotIn("src/t17_app/__main__.py", self.p.files)
        self.assertIn("src/t17_app/app.py", self.p.files)
        self.assertIn("src/t17_app/main.py", self.p.files)
        self.assertEqual(len(self.p.files), 17)  # 改名不增减文件数

    def test_app_is_thin_entry_with_reexport(self) -> None:
        app = self.p.files["src/t17_app/app.py"]
        self.assertIn("from .main import main", app)   # 包内 / console entry
        self.assertIn("from main import main", app)    # T19：直接 python app.py
        self.assertIn("__package__", app)
        self.assertIn('if __name__ == "__main__":', app)
        self.assertNotIn("def main(", app)  # 启动器只在 main.py
        self.assertIn("# src/t17_app/app.py", app)
        ast.parse(app)

    def test_main_is_launcher(self) -> None:
        main = self.p.files["src/t17_app/main.py"]
        for token in ("def main() -> int:", "setWindowIcon(QIcon", "NOVA_PRESCRIPT_SMOKE",
                      "_sync_title_bar", "init_nova(engine)", "APP_ICON"):
            self.assertIn(token, main, token)
        self.assertIn("# src/t17_app/main.py", main)
        ast.parse(main)

    def test_pkg_init_and_readme_point_to_new_entry(self) -> None:
        init = self.p.files["src/t17_app/__init__.py"]
        self.assertIn("python -m t17_app.app", init)
        readme = self.p.files["README.md"]
        self.assertIn("python -m t17_app.app", readme)
        self.assertNotIn("python -m t17_app\n", readme)  # 不留悬空旧命令

    def test_scripts_and_manifest_entry_stay_consistent(self) -> None:
        toml = self.p.files["pyproject.toml"]
        self.assertIn('t17-app = "t17_app.app:main"', toml)
        data = json.loads(self.p.files["prescript.json"])
        self.assertEqual(data["app"]["entry"], "t17_app.app:main")
        self.assertEqual(set(data["files"]), set(self.p.files))

    def test_readme_tree_lists_renamed_files_only(self) -> None:
        readme = self.p.files["README.md"]
        self.assertIn("src/t17_app/main.py", readme)
        self.assertIn("src/t17_app/app.py", readme)
        self.assertNotIn("src/t17_app/__main__.py", readme)

    def test_all_nine_kinds_follow_same_layout(self) -> None:
        for k in KINDS:
            with self.subTest(kind=k.code):
                p = plan_project(k.code, "/tmp/t17-all", "A", "a_pkg", "0.5.0")
                self.assertIn("src/a_pkg/main.py", p.files)
                self.assertIn("src/a_pkg/app.py", p.files)
                self.assertNotIn("src/a_pkg/__main__.py", p.files)
                ast.parse(p.files["src/a_pkg/app.py"])
                ast.parse(p.files["src/a_pkg/main.py"])

    def test_product_self_check_covers_entry_layout(self) -> None:
        smoke = self.p.files["tests/test_smoke.py"]
        self.assertIn("def test_entry_layout()", smoke)
        self.assertIn("__main__.py", smoke)
        self.assertIn('"main.py"', smoke)
        ast.parse(smoke)


class TestRuntimeChain(unittest.TestCase):
    """运行链路：smoke / CLI / GUI / 落盘，全部指向新入口。"""

    def test_smoke_run_uses_new_module(self) -> None:
        from nova_forge.command import cmd_prescript

        text = Path(cmd_prescript.__file__).read_text(encoding="utf-8")
        self.assertIn('"-m", project.package + ".app"', text)

    def test_cli_and_gui_commands_point_to_new_entry(self) -> None:
        from nova_forge.prescript import gui_model

        cli = (SRC / "nova_forge" / "command" / "cmd_prescript.py").read_text(
            encoding="utf-8")
        self.assertIn("python -m {project.package}.app", cli)
        self.assertIn(
            "python -m {project.package}.app",
            Path(gui_model.__file__).read_text(encoding="utf-8"),
        )

    def test_hatch_command_and_disk_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = GUIConfig(kind="chat", path=tmp, name="T17 App", package="t17_app")
            result = hatch(cfg, confirmed=True)
            self.assertTrue(result["ok"], result.get("message"))
            self.assertIn("python -m t17_app.app", result["command"])
            pkg_dir = Path(tmp) / "t17_app" / "src" / "t17_app"
            self.assertTrue((pkg_dir / "app.py").is_file())
            self.assertTrue((pkg_dir / "main.py").is_file())
            self.assertFalse((pkg_dir / "__main__.py").exists())
            manifest = json.loads(
                (Path(tmp) / "t17_app" / "prescript.json").read_text(encoding="utf-8"))
            self.assertIn("src/t17_app/main.py", manifest["files"])
            self.assertIn("src/t17_app/app.py", manifest["files"])
            self.assertNotIn("src/t17_app/__main__.py", manifest["files"])

    def test_selected_subset_still_accounts_for_renamed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = GUIConfig(kind="chat", path=tmp, name="T17 App", package="t17_app")
            paths = [c["path"] for c in file_choices(cfg)]
            cfg.selected_files = [p for p in paths if p != "src/t17_app/app.py"]
            summary = plan_summary(cfg)
            self.assertEqual(summary["fileCount"], len(paths) - 1)
            self.assertNotIn("src/t17_app/app.py",
                             [r["path"] for r in summary["files"]])
            self.assertNotIn("src/t17_app/app.py", summary["readme"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
