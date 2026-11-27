# tests/test_prescript.py
# 创建时间：星期四 2026-11-26 16:02
"""prescript 子命令回归测试：九类配方 / 七槽宿主 / 九舞台 / 清单一致 / CLI 行为。"""

from __future__ import annotations

import json
import py_compile
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.prescript.catalog import KIND_CODES, KINDS, get_kind  # noqa: E402
from nova_forge.prescript.render import plan_project, render_project  # noqa: E402
from nova_forge.prescript.stages import STAGES  # noqa: E402

SEVEN_SLOTS = ("globalSlot", "recipeSlot", "stageSlot", "validateSlot",
               "pipelineSlot", "certificateSlot", "overlaySlot")


class TestCatalog(unittest.TestCase):
    def test_nine_kinds_stable(self) -> None:
        self.assertEqual(len(KINDS), 9)
        self.assertEqual(tuple(k.recipe for k in KINDS),
                         tuple(f"P{i}" for i in range(1, 10)))
        self.assertEqual(len({k.code for k in KINDS}), 9)
        self.assertEqual(len({k.shell for k in KINDS}), 9)
        self.assertNotIn("NovaIncubator", [k.shell for k in KINDS])

    def test_unknown_kind_raises(self) -> None:
        with self.assertRaises(ValueError):
            get_kind("not-a-kind")

    def test_all_stages_present(self) -> None:
        self.assertEqual(set(STAGES), set(KIND_CODES))
        for code, source in STAGES.items():
            self.assertIn(get_kind(code).shell, source, code)
            self.assertIn("_signatureOn", source, code)

    def test_breakpoint_by_shell(self) -> None:
        # 回归：chat 设 480 会把三条侧栏挤成竖条，必须保持 700 响应式
        expected = {"agent": 480, "copilot": 480, "de": 480, "orbit": 480,
                    "chat": 700}
        for code, value in expected.items():
            with self.subTest(kind=code):
                self.assertIn(f"breakpoint: {value}", STAGES[code])


class TestPlan(unittest.TestCase):
    def test_main_qml_seven_slots(self) -> None:
        for kind in KINDS:
            with self.subTest(kind=kind.code):
                project = plan_project(kind.code, ROOT / "tmp", "Demo")
                main = project.files["src/demo/qml/Main.qml"]
                self.assertIn("NovaIncubator", main)
                for slot in SEVEN_SLOTS:
                    self.assertIn(slot + ":", main, kind.code + " 缺 " + slot)

    def test_only_one_preset_loaded(self) -> None:
        # 回归：JS 里 "false" 是非空字符串会被判真 → 九项全显示「已装载」
        for kind in KINDS:
            with self.subTest(kind=kind.code):
                project = plan_project(kind.code, ROOT / "tmp", "Demo")
                main = project.files["src/demo/qml/Main.qml"]
                self.assertEqual(main.count('"loaded": true'), 1, kind.code)
                self.assertEqual(main.count('"loaded": false'), 8, kind.code)

    def test_manifest_matches(self) -> None:
        project = plan_project("chat", ROOT / "tmp", "Mei Chat")
        data = json.loads(project.files["prescript.json"])
        self.assertEqual(data["prescript"]["kind"], "chat")
        self.assertEqual(data["prescript"]["shell"], "NovaChat")
        self.assertEqual(data["contract"]["api_version"], "1.3.0")
        self.assertEqual(len(data["gates"]), 3)
        self.assertEqual(len(data["deliverables"]), 5)
        self.assertEqual(project.manifest["app"]["package"], "mei_chat")

    def test_package_normalisation(self) -> None:
        from nova_forge.prescript.render import normalise_package
        self.assertEqual(normalise_package("Mei Chat 2"), "mei_chat_2")
        self.assertEqual(normalise_package("123-app"), "app_123_app")
        self.assertEqual(normalise_package("中文应用"), "prescript_app")


class TestRender(unittest.TestCase):
    def test_writes_and_compiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "chat-app"
            project = render_project("chat", root, "Mei Chat", forge_version="0.5.0")
            for rel in project.files:
                self.assertTrue((root / rel).exists(), rel)
            for py in (root / "src").rglob("*.py"):
                py_compile.compile(str(py), doraise=True, cfile=str(py) + ".pyc")
            self.assertIn("nova-forge prescript", (root / "README.md").read_text(encoding="utf-8"))
            self.assertIn("NOVA_PRESCRIPT_SMOKE",
                          (root / "src" / "mei_chat" / "main.py").read_text(encoding="utf-8"))

    def test_force_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "chat-app"
            render_project("chat", root, "Old", force=False)
            (root / "README.md").write_text("stale", encoding="utf-8")
            render_project("chat", root, "Old", force=False)
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), "stale")
            render_project("chat", root, "New", force=True)
            self.assertIn("# New", (root / "README.md").read_text(encoding="utf-8"))


class TestCLI(unittest.TestCase):
    def _cli(self, *args: str):
        import os
        import subprocess

        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-m", "nova_forge.cli", *args],
            cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
        )

    def test_list_nine(self) -> None:
        result = self._cli("prescript", "--list")
        self.assertEqual(result.returncode, 0, result.stderr)
        for code in KIND_CODES:
            self.assertIn(code, result.stdout)

    def test_unknown_kind_exit_2(self) -> None:
        result = self._cli("prescript", "--kind", "wat", "--path", "x")
        self.assertEqual(result.returncode, 2)

    def test_dry_run_no_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "dry"
            result = self._cli("prescript", "--kind", "flex", "--path", str(target), "--dry-run")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(target.exists())

    def test_full_generation_exit_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "wizard-app"
            result = self._cli("prescript", "--kind", "wizard", "--path", str(target),
                               "--name", "Deploy Wizard")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((target / "src" / "deploy_wizard" / "qml" / "Main.qml").exists())
            self.assertIn("校验通过", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
