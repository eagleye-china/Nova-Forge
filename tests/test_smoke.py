# tests/test_smoke.py
# 星期二 2026-11-24 13:18
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
    def test_cli_exposes_prompt_but_not_snapshot(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("prompt", result.stdout)
        self.assertNotIn("snapshot", result.stdout.lower())

    def test_prompt_module_imports_without_tkinter(self):
        import importlib

        module = importlib.import_module("nova_forge.command.cmd_prompt")
        self.assertTrue(callable(module._copy_to_clipboard))
        self.assertTrue(callable(module._build_prompt_file_name))
        self.assertFalse(hasattr(module, "_find_latest_snapshot"))

    def test_clean_tool_import_has_no_side_effects(self):
        import importlib

        module = importlib.import_module("nova_forge.tools.clean_material_symbols")
        self.assertEqual(module.default_project_root(), ROOT)


class PromptCommandTests(unittest.TestCase):
    def test_file_name_uses_prompt_stamp_pattern_and_avoids_collision(self):
        """回归守护：文件名必须是 prompt{yyyyMMddHH}.md，且同小时不覆盖。"""
        from nova_forge.command.cmd_prompt import _build_prompt_file_name

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            first = _build_prompt_file_name("2026112413", directory)
            self.assertEqual(first.name, "prompt2026112413.md")

            first.write_text("x", encoding="utf-8")
            second = _build_prompt_file_name("2026112413", directory)
            self.assertEqual(second.name, "prompt2026112413_1.md")

    def test_run_prompt_writes_prompt_file_and_copies_to_clipboard(self):
        """端到端（IO mock）：粘贴 → 落盘 promptyyyyMMddHH.md → 复制剪贴板。"""
        from unittest.mock import patch

        from nova_forge.command import cmd_prompt

        body = "# 新会话提示词\n\n会话快照正文……"
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            fake_now = cmd_prompt.datetime(2026, 11, 24, 13, 20, 0)
            with (
                patch.object(cmd_prompt, "PROMPT_DIR", directory),
                patch.object(cmd_prompt, "_read_interactive_content", return_value=body),
                patch.object(cmd_prompt, "_copy_to_clipboard", return_value=True) as copy,
                patch.object(cmd_prompt, "datetime") as dt_cls,
            ):
                dt_cls.now.return_value = fake_now
                cmd_prompt.run_prompt()

            written = directory / "prompt2026112413.md"
            self.assertTrue(written.exists(), "应生成 promptyyyyMMddHH.md")
            text = written.read_text(encoding="utf-8")
            self.assertIn("nova-forge prompt", text)
            self.assertIn(body, text)
            copy.assert_called_once_with(text)

    def test_run_prompt_ignores_empty_input(self):
        from unittest.mock import patch

        from nova_forge.command import cmd_prompt

        with (
            patch.object(cmd_prompt, "_read_interactive_content", return_value="   "),
            patch.object(cmd_prompt, "_copy_to_clipboard") as copy,
        ):
            cmd_prompt.run_prompt()
        copy.assert_not_called()


class SaverLifecycleTests(unittest.TestCase):
    def test_controller_is_kept_alive_by_window(self):
        """回归守护：控制器必须被窗口持有，否则 GC 后自动监听槽函数全部失效。"""
        from unittest.mock import MagicMock, patch

        from nova_forge.command import cmd_saver

        fake_window = MagicMock()
        fake_controller = MagicMock()
        with (
            patch.object(cmd_saver, "SaverWindow", return_value=fake_window),
            patch.object(cmd_saver, "SaverController", return_value=fake_controller) as ctor,
            patch.object(cmd_saver, "QApplication") as app_cls,
            patch.object(cmd_saver, "QIcon"),
            patch.object(cmd_saver, "QSystemTrayIcon"),
        ):
            app_cls.instance.return_value = MagicMock()  # 已有 app，跳过新建与 exec
            cmd_saver.run_clip_saver()

        ctor.assert_called_once_with(fake_window)
        self.assertIs(
            getattr(fake_window, "_saver_controller", None),
            fake_controller,
            "SaverController 必须被挂到 window 上持有，防止 GC 断开信号槽",
        )


class CommitMessageTests(unittest.TestCase):
    def test_feature_builds_conventional_commit_message(self):
        from nova_forge.command.cmd_git import build_commit_message

        # --feature 自动补 feat: 前缀
        self.assertEqual(
            build_commit_message("v0.4.10", feature="新增 QRC 构建器"),
            "feat: 新增 QRC 构建器",
        )
        # 已自带前缀不重复添加
        self.assertEqual(
            build_commit_message("v0.4.10", feature="feat(ui): 修波浪线"),
            "feat(ui): 修波浪线",
        )
        # 显式 -m 优先级最高
        self.assertEqual(
            build_commit_message("v0.4.10", commit_msg="custom msg", feature="desc"),
            "custom msg",
        )
        # 都没给走默认 release 信息
        self.assertEqual(
            build_commit_message("v0.4.10"),
            "chore(release): v0.4.10",
        )

    def test_git_and_publish_expose_feature_flag(self):
        for command in ("git", "publish"):
            result = run_cli(command, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--feature", result.stdout)
            self.assertIn("-F", result.stdout)


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


class PypiTargetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_pyproject(self, body: str):
        (self.root / "pyproject.toml").write_text(body, encoding="utf-8")

    def test_resolves_static_name_and_version(self):
        from nova_forge.command.cmd_pypi import resolve_pypi_target

        self._write_pyproject(
            '[project]\nname = "pyside-nova"\nversion = "1.0.0rc1"\n'
        )
        self.assertEqual(resolve_pypi_target(self.root), ("pyside-nova", "1.0.0rc1"))

    def test_resolves_dynamic_hatch_version(self):
        # 贴近 pyside-nova 真实情况：dynamic version 从 __init__.py 读
        from nova_forge.command.cmd_pypi import resolve_pypi_target

        self._write_pyproject(
            '[project]\nname = "pyside-nova"\ndynamic = ["version"]\n\n'
            '[tool.hatch.version]\npath = "src/pyside_nova/__init__.py"\n'
        )
        init = self.root / "src" / "pyside_nova" / "__init__.py"
        init.parent.mkdir(parents=True)
        init.write_text('__version__ = "1.0.0rc1"\n', encoding="utf-8")
        self.assertEqual(resolve_pypi_target(self.root), ("pyside-nova", "1.0.0rc1"))

    def test_normalizes_pep503_name(self):
        from nova_forge.command.cmd_pypi import resolve_pypi_target

        self._write_pyproject(
            '[project]\nname = "PySide_Nova.Tools"\nversion = "2.0"\n'
        )
        self.assertEqual(resolve_pypi_target(self.root), ("pyside-nova-tools", "2.0"))

    def test_run_package_checks_project_target_not_tool(self):
        """回归守护：查重参数必须是当前项目，不能是 nova-forge/__version__。"""
        from unittest.mock import patch

        from nova_forge.command import cmd_pypi

        self._write_pyproject(
            '[project]\nname = "pyside-nova"\nversion = "1.0.0rc1"\n'
        )
        dist = self.root / "dist"
        dist.mkdir()
        (dist / "pyside_nova-1.0.0rc1-py3-none-any.whl").write_text(
            "fake", encoding="utf-8"
        )

        cwd = os.getcwd()
        try:
            os.chdir(self.root)
            with (
                patch.object(cmd_pypi, "_clean_build_dirs"),
                patch.object(cmd_pypi, "run") as mock_run,
                patch.object(
                    cmd_pypi, "_version_exists_on_pypi", return_value=False
                ) as mock_check,
            ):
                cmd_pypi.run_package()
        finally:
            os.chdir(cwd)

        # 核心断言：查的是 pyside-nova 1.0.0rc1，不是工具自己的 0.4.10
        mock_check.assert_called_once_with("pyside-nova", "1.0.0rc1")
        # 上传命令确实带着 dist 产物
        cmds = [call.args[0] for call in mock_run.call_args_list]
        upload = [c for c in cmds if "upload" in c]
        self.assertTrue(upload)
        self.assertTrue(any("pyside_nova-1.0.0rc1" in str(x) for x in upload[0]))


class OriginSelfHealTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self._proto = os.environ.get("NOVA_GIT_PROTOCOL")

    def tearDown(self):
        if self._proto is None:
            os.environ.pop("NOVA_GIT_PROTOCOL", None)
        else:
            os.environ["NOVA_GIT_PROTOCOL"] = self._proto
        self._tmp.cleanup()

    def _origin(self):
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"], cwd=self.root,
            capture_output=True, text=True,
        )
        return r.stdout.strip() if r.returncode == 0 else None

    def test_adds_origin_when_missing_default_ssh(self):
        from nova_forge.utils.project_meta import ensure_origin

        os.environ.pop("NOVA_GIT_PROTOCOL", None)
        url = ensure_origin("eagleye-china", "pyside-nova", self.root)
        self.assertEqual(url, "git@github.com:eagleye-china/pyside-nova.git")
        self.assertEqual(self._origin(), url)

    def test_adds_origin_with_https_when_protocol_env_set(self):
        from nova_forge.utils.project_meta import ensure_origin

        os.environ["NOVA_GIT_PROTOCOL"] = "https"
        url = ensure_origin("eagleye-china", "pyside-nova", self.root)
        self.assertEqual(url, "https://github.com/eagleye-china/pyside-nova.git")
        self.assertEqual(self._origin(), url)

    def test_reuses_existing_origin_for_same_repo(self):
        from nova_forge.utils.project_meta import ensure_origin

        existing = "git@github.com:eagleye-china/pyside-nova.git"
        subprocess.run(["git", "remote", "add", "origin", existing], cwd=self.root, check=True)
        url = ensure_origin("eagleye-china", "pyside-nova", self.root)
        self.assertEqual(url, existing)  # 原样复用，不覆盖
        self.assertEqual(self._origin(), existing)

    def test_rejects_origin_pointing_to_other_repo(self):
        from nova_forge.utils.project_meta import ensure_origin

        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:other/wrong.git"],
            cwd=self.root, check=True,
        )
        with self.assertRaises(RuntimeError) as ctx:
            ensure_origin("eagleye-china", "pyside-nova", self.root)
        self.assertIn("不符", str(ctx.exception))
        self.assertEqual(self._origin(), "git@github.com:other/wrong.git")  # 未被改写

    def test_https_and_ssh_urls_normalize_to_same_repo(self):
        from nova_forge.utils.project_meta import ensure_origin

        existing = "https://github.com/eagleye-china/pyside-nova.git"
        subprocess.run(["git", "remote", "add", "origin", existing], cwd=self.root, check=True)
        # 目标是同仓库，即使协议不同也应复用（不抛错）
        url = ensure_origin("eagleye-china", "pyside-nova", self.root)
        self.assertEqual(url, existing)


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
