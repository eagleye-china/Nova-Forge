# tests/test_smoke.py
# 星期一 2026-11-23 03:10
"""零外部依赖的冒烟测试，守护历史故障点不被重新引入。"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """在干净的子进程里调用 CLI，显式注入本地源码路径。"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "nova_forge.cli", *args],
        cwd=cwd or ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class CliStartupTests(unittest.TestCase):
    def test_help_starts_without_gui_dependencies(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout.lower())
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_version_is_reported(self):
        result = run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nova-forge", result.stdout.lower())

    def test_gui_command_without_pyside6_exits_cleanly(self):
        from unittest.mock import patch

        from nova_forge import cli

        runner = cli._gui_runner("cmd_icons", "run_icons")
        missing = ModuleNotFoundError("No module named 'PySide6'", name="PySide6")
        with (
            patch.object(cli.importlib, "import_module", side_effect=missing),
            self.assertRaises(SystemExit) as ctx,
        ):
            runner()
        self.assertEqual(ctx.exception.code, 2)


class ModuleImportTests(unittest.TestCase):
    def test_prompt_module_imports_without_tkinter(self):
        import importlib

        module = importlib.import_module("nova_forge.command.cmd_prompt")
        self.assertTrue(callable(module._copy_to_clipboard))

    def test_clean_tool_import_has_no_side_effects(self):
        import importlib

        module = importlib.import_module("nova_forge.tools.clean_material_symbols")
        self.assertEqual(module.default_project_root(), ROOT)


class PublishGuardTests(unittest.TestCase):
    def test_version_exists_check_handles_all_cases(self):
        import urllib.error
        from unittest.mock import MagicMock, patch

        from nova_forge.command import cmd_pypi

        # 已存在：返回 JSON 带文件
        with patch.object(cmd_pypi.urllib.request, "urlopen") as mock_open:
            mock_open.return_value.__enter__ = MagicMock(
                return_value=MagicMock(read=lambda: b'{"urls": [{"filename": "x.whl"}]}')
            )
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            self.assertTrue(cmd_pypi._version_exists_on_pypi("nova-forge", "0.4.9"))

        # 不存在：404
        with patch.object(
            cmd_pypi.urllib.request,
            "urlopen",
            side_effect=urllib.error.HTTPError("", 404, "Not Found", {}, None),
        ):
            self.assertFalse(cmd_pypi._version_exists_on_pypi("nova-forge", "9.9.9"))

        # 网络异常：返回 None，不阻塞上传
        with patch.object(
            cmd_pypi.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            self.assertIsNone(cmd_pypi._version_exists_on_pypi("nova-forge", "0.4.10"))


class ResourceTests(unittest.TestCase):
    def test_tree_accepts_utf8_bom_structure_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            structure = workdir / "project_structure.txt"
            structure.write_text(
                "demo/\n├── src/\n│   └── app.py\n└── README.md\n",
                encoding="utf-8-sig",
            )
            result = run_cli("tree", "-f", str(structure), cwd=workdir)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((workdir / "demo" / "src" / "app.py").exists())
            self.assertFalse(any("\ufeff" in p.name for p in workdir.rglob("*")))

    def test_qrc_builder_preserves_aliases_and_drops_missing_files(self):
        from nova_forge.core.qrc_builder import update_qrc_from_directory

        with tempfile.TemporaryDirectory() as tmp:
            resources = Path(tmp) / "resources"
            icons = resources / "icons"
            icons.mkdir(parents=True)
            (icons / "home.svg").write_text("<svg/>", encoding="utf-8")
            (icons / "setting.svg").write_text("<svg/>", encoding="utf-8")
            (resources / "resources.qrc").write_text(
                '<!DOCTYPE RCC>\n<RCC version="1.0">'
                '<qresource prefix="/icons">'
                '<file alias="custom">icons/home.svg</file>'
                '<file alias="ghost">icons/missing.svg</file>'
                "</qresource></RCC>",
                encoding="utf-8",
            )

            log = update_qrc_from_directory(icons)
            output = (resources / "resources.qrc").read_text(encoding="utf-8")

            self.assertIn("新增条目: 2", log)
            self.assertIn('alias="custom"', output)
            self.assertNotIn("ghost", output)
            self.assertIn('alias="setting"', output)


if __name__ == "__main__":
    unittest.main()
