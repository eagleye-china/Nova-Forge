# tests/test_prescript_gui.py
# 创建时间：星期四 2026-11-26 19:52
"""prescript GUI 式子命令回归测试（纯逻辑层，不导入 PySide6，规避 pytest 生命周期 SIGSEGV）。

覆盖：九配方单源 / 三重校验 / 预览不落盘 / **人工确认闸门** / 落盘四重静态校验
/ QML 七槽装配与治理契约 / CLI 默认 GUI 与带参数 CLI 的分发。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.prescript import gui_model  # noqa: E402
from nova_forge.prescript.catalog import KIND_CODES, KINDS  # noqa: E402

SEVEN_SLOTS = ("globalSlot", "recipeSlot", "stageSlot", "validateSlot",
               "pipelineSlot", "certificateSlot", "overlaySlot")


def _cfg(tmp: str, **overrides) -> gui_model.GUIConfig:
    data = {
        "kind": "chat",
        "path": str(Path(tmp) / "chat-app"),
        "name": "Mei Chat",
        "package": "mei_chat",
    }
    data.update(overrides)
    return gui_model.GUIConfig.from_mapping(data)


class TestKindSource(unittest.TestCase):
    def test_nine_kinds_single_source(self) -> None:
        rows = gui_model.kind_rows()
        self.assertEqual(len(rows), 9)
        self.assertEqual([r["code"] for r in rows], list(KIND_CODES))
        self.assertEqual([r["recipe"] for r in rows], [f"P{i}" for i in range(1, 10)])
        self.assertEqual({r["shell"] for r in rows}, {k.shell for k in KINDS})
        self.assertNotIn("NovaIncubator", [r["shell"] for r in rows])

    def test_kind_options_shape(self) -> None:
        options = gui_model.kind_options()
        self.assertEqual(len(options), 9)
        for opt in options:
            self.assertEqual(set(opt), {"label", "value"})
        self.assertEqual([o["value"] for o in options], list(KIND_CODES))

    def test_config_from_mapping_ignores_unknown(self) -> None:
        cfg = gui_model.GUIConfig.from_mapping({"kind": "agent", "bogus": 1})
        self.assertEqual(cfg.kind, "agent")
        self.assertFalse(hasattr(cfg, "bogus"))


class TestValidation(unittest.TestCase):
    def test_triple_check_all_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checks = gui_model.validate_config(_cfg(tmp))
            self.assertEqual(len(checks), 3)
            self.assertEqual([c["key"] for c in checks],
                             ["config", "directory", "contract"])
            self.assertTrue(all(c["ok"] for c in checks), checks)

    def test_unknown_kind_fails_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checks = gui_model.validate_config(_cfg(tmp, kind="wat"))
            self.assertFalse(checks[0]["ok"])
            self.assertFalse(gui_model.hatch(_cfg(tmp, kind="wat"), confirmed=True)["ok"])

    def test_occupied_directory_needs_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # 占据的是**工程目录**（根目录 / 包名），根目录本身允许非空
            target = Path(tmp) / "chat-app" / "mei_chat"
            target.mkdir(parents=True)
            (target / "keep.txt").write_text("x", encoding="utf-8")
            cfg = _cfg(tmp)
            checks = gui_model.validate_config(cfg)
            self.assertFalse(checks[1]["ok"])
            forced = gui_model.validate_config(_cfg(tmp, force=True))
            self.assertTrue(forced[1]["ok"])

    def test_project_nested_under_root_by_package(self) -> None:
        """CSA 2026-11-27 拍板：提供的是孵化根目录，项目必须落在 <根目录>/<包名>/。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "TEST_ROOT"
            root.mkdir()
            (root / "unrelated.txt").write_text("x", encoding="utf-8")
            cfg = gui_model.GUIConfig(kind="chat", path=str(root),
                                      name="Mei Chat", package="mei_chat")  # 根目录非空也合法：占满判定只看工程目录
            checks = gui_model.validate_config(cfg)
            self.assertTrue(all(c["ok"] for c in checks), checks)
            result = gui_model.hatch(cfg, confirmed=True)
            self.assertTrue(result["ok"], result["message"])
            project_dir = root / "mei_chat"
            self.assertTrue((project_dir / "pyproject.toml").exists())
            self.assertTrue((project_dir / "src" / "mei_chat").is_dir())
            # 根目录里除工程子目录外不被写入其他文件
            self.assertEqual([p.name for p in root.iterdir()],
                             ["mei_chat", "unrelated.txt"])

    def test_resolve_target_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = gui_model.GUIConfig(path=str(Path(tmp) / "ws"))
            root, name, pkg = gui_model.resolve_target(cfg)
            self.assertEqual(root, Path(tmp) / "ws" / "prescript_app")
            self.assertEqual(name, "Prescript App")
            self.assertEqual(pkg, "prescript_app")


class TestPlanAndGate(unittest.TestCase):
    def test_plan_summary_never_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "chat-app" / "mei_chat"
            summary = gui_model.plan_summary(_cfg(tmp))
            self.assertEqual(summary["package"], "mei_chat")
            self.assertEqual(summary["shell"], "NovaChat")
            self.assertEqual(summary["apiVersion"], "1.3.0")
            self.assertEqual(summary["root"], str(target))
            self.assertEqual(summary["workspace"], str(Path(tmp) / "chat-app"))
            self.assertGreater(summary["fileCount"], 5)
            self.assertGreater(summary["bytes"], 0)
            self.assertFalse(target.exists())

    def test_hatch_requires_explicit_confirmation(self) -> None:
        """治理铁律：未确认一律不落盘，壳只 emit 意图。"""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "chat-app" / "mei_chat"
            result = gui_model.hatch(_cfg(tmp), confirmed=False)
            self.assertFalse(result["ok"])
            self.assertFalse(result["written"])
            self.assertIn("人工确认", result["message"])
            self.assertFalse(target.exists())

    def test_dry_run_never_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "chat-app" / "mei_chat"
            result = gui_model.hatch(_cfg(tmp, dry_run=True), confirmed=True)
            self.assertTrue(result["ok"])
            self.assertFalse(result["written"])
            self.assertTrue(result["dryRun"])
            self.assertFalse(target.exists())

    def test_hatch_writes_and_passes_static_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "chat-app" / "mei_chat"
            result = gui_model.hatch(_cfg(tmp), confirmed=True)
            self.assertTrue(result["ok"], result["message"])
            self.assertTrue(result["written"])
            self.assertEqual(len(result["checks"]), 4)
            self.assertTrue(all(c["ok"] for c in result["checks"]), result["checks"])
            self.assertTrue((target / "src" / "mei_chat" / "qml" / "Main.qml").exists())
            self.assertIn("NovaIncubator",
                          (target / "src" / "mei_chat" / "qml" / "Main.qml").read_text(encoding="utf-8"))
            self.assertIn("python -m mei_chat.app", result["command"])


class TestWrittenTruth(unittest.TestCase):
    """账实相符（2026-11-27 CSA 实报）：written 是「当前配置」的真实落盘态。

    修复前 _written 是粘性会话旗标——孵化成功后改配方/目录，chip 仍亮
    「已落盘」绿灯，与文件清单「预览 · 未落盘」自相矛盾。
    """

    def _bridge(self, tmp: str) -> object:
        from nova_forge.bridge.prescript_bridge import PrescriptBridge

        bridge = PrescriptBridge()
        bridge.setPath(str(Path(tmp) / "truth-app"))
        bridge.setName("Truth App")
        return bridge

    def test_written_resets_on_any_config_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = self._bridge(tmp)
            bridge.setForce(True)  # 重复孵化同一目录需 force，与本测试主题无关
            result = bridge.hatch(True)
            self.assertTrue(result["written"])
            self.assertTrue(bridge.written)
            # 改目录 → 立即失效
            bridge.setPath(str(Path(tmp) / "truth-app-2"))
            self.assertFalse(bridge.written)
            # 再孵化成功 → 改应用名同样失效
            self.assertTrue(bridge.hatch(True)["written"])
            bridge.setName("Renamed")
            self.assertFalse(bridge.written)
            # 未生效的重复赋值（值相同）不复位
            self.assertTrue(bridge.hatch(True)["written"])
            bridge.setKind(bridge.kind)
            self.assertTrue(bridge.written)

    def test_dry_run_never_marks_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge = self._bridge(tmp)
            bridge.setDryRun(True)
            result = bridge.hatch(True)
            self.assertTrue(result["ok"])
            self.assertFalse(bridge.written)

    def test_qml_frozen_follows_written_not_sticky(self) -> None:
        """QML 契约：frozen 绑定 bridge.written，不得再手工赋值粘性旗标。"""
        qml = (SRC / "nova_forge" / "ui" / "qml" / "prescript_main.qml").read_text(encoding="utf-8")
        self.assertIn("readonly property bool frozen: bridge ? bridge.written : false", qml)
        self.assertNotIn("win.frozen =", qml)
        # 文件清单标题随落盘态切换，不再静态写死「未落盘」
        self.assertIn('"将生成的文件（勾选决定实际创建 · 未落盘）"', qml)
        self.assertIn('"已生成的文件（已落盘 · "', qml)
        # 文件清单改为组选框：逐项列出预知文件，勾选决定实际创建哪些
        self.assertIn("bridge.fileChoices", qml)
        self.assertIn("bridge.setFileSelected(modelData.path, v)", qml)
        self.assertIn("bridge.selectAllFiles(true)", qml)
        self.assertIn("bridge.selectAllFiles(false)", qml)


class TestQmlContract(unittest.TestCase):
    def setUp(self) -> None:
        self.qml = (SRC / "nova_forge" / "ui" / "qml" / "prescript_main.qml").read_text(encoding="utf-8")

    def test_seven_slots_all_injected(self) -> None:
        for slot in SEVEN_SLOTS:
            self.assertIn(slot + ":", self.qml, "缺 " + slot)

    def test_uses_nova_incubator(self) -> None:
        self.assertIn("NovaIncubator {", self.qml)
        self.assertIn("import Nova.Composite.LayoutShell", self.qml)
        self.assertIn("onFreezeRequested: bridge.requestHatch()", self.qml)

    def test_freeze_only_opens_gate(self) -> None:
        # 冻结意图不得直接落盘；落盘只发生在确认按钮的 hatch(true)
        self.assertIn("shell.requestFreeze()", self.qml)
        self.assertIn("bridge.hatch(true)", self.qml)
        self.assertNotIn("onFreezeRequested: bridge.hatch(", self.qml)
        self.assertNotIn("Component.onDestruction", self.qml)
        self.assertEqual(self.qml.count("bridge.hatch(true)"), 1)

    def test_single_completion_hook(self) -> None:
        # 坑：注入第二个 Component.onCompleted 会报 Property value set multiple times
        self.assertEqual(self.qml.count("Component.onCompleted"), 1)

    def test_dogfoods_nova_services_and_controls(self) -> None:
        # T23：README 展开区的滚动改由 NovaMarkdown 内部 NovaScrollArea 承担，
        # 宿主不再直接实例化 NovaScrollArea，故断言相应换成 NovaMarkdown。
        for token in ("NovaScreen.source", "NovaTheme.setDark", "NovaNotify.show",
                      "NovaDialog.show", "NovaLoading.show", "busyBar",
                      "NovaSelect", "NovaInput", "NovaCheckbox", "NovaBtn",
                      "NovaCard", "NovaChip", "NovaSeparator", "NovaSpinner",
                      "NovaMarkdown", "Flickable", "Repeater"):
            self.assertIn(token, self.qml, "未 dogfooding " + token)

    def test_emblem_click_opens_preview(self) -> None:
        """pyside-nova 1.3.0 additive：壳徽记可点 → 界面预览（CSA 原始愿望）。

        CSA 2026-11-27 追加：徽记挂 tooltip「界面预览」后，hero 卡独立按钮
        摘除——一功能一入口，不重复。
        """
        self.assertIn("emblemClickable: true", self.qml)
        self.assertIn("emblemToolTip: \"界面预览\"", self.qml)
        self.assertIn("onEmblemClicked: win.openPreview(\"\")", self.qml)
        # 独立按钮已摘除：hero 卡不再有第二个入口
        self.assertNotIn('text: "👁 界面预览"', self.qml)

    def test_size_formatting_human_units(self) -> None:
        """CSA 22:22 指令：体量达到 KB/MB/GB 显示对应单位，不统一 B。"""
        self.assertIn("function fmtSize(", self.qml)
        self.assertIn("win.fmtSize(bridge.summary.bytes", self.qml)
        self.assertNotIn('files[i].size + " B"', self.qml)

    def test_pipeline_bar_horizontally_centered(self) -> None:
        """CSA 22:22 指令：管道条整体水平居中，不左贴边。"""
        self.assertIn("horizontalCenter: parent.horizontalCenter", self.qml)

    def test_loading_bar_defect_is_recorded_and_avoided(self) -> None:
        """基础组件 NovaLoadingBar 的 qrc 缺陷：宿主侧规避，触发点写进 QML 注释。"""
        self.assertNotIn("NovaLoadingBar.start", self.qml)
        self.assertNotIn("NovaLoadingBar.stop", self.qml)
        self.assertIn("qrc:/pyside_nova/qml/Nova/Controls/NovaAjaxBar.qml", self.qml)


class TestStagePreview(unittest.TestCase):
    """界面预览：Stage.qml 与落盘产物同源（真 QML 实装渲染的单源保障）。"""

    def test_stage_qml_nine_kinds_selfcontained(self) -> None:
        from nova_forge.prescript.catalog import get_kind
        from nova_forge.prescript.stages import STAGES

        for code in KIND_CODES:
            text = gui_model.stage_qml(code)
            self.assertTrue(text.startswith("// Stage.qml ·"), code)
            self.assertIn(get_kind(code).shell, text, code)
            # 自包含：只依赖 Nova 模块，无 bridge / contextProperty，可在预览浮层实装
            self.assertNotIn("bridge", text, code)
            self.assertNotIn("contextProperty", text, code)
            self.assertEqual(STAGES[code], text, code)

    def test_stage_qml_unknown_kind_raises(self) -> None:
        with self.assertRaises(ValueError):
            gui_model.stage_qml("wat")

    def test_bridge_stage_qml_and_preview_stage(self) -> None:
        """桥接层：stageQml 全文 / previewStage 写临时副本并返回 file:// URI。"""
        from nova_forge.bridge.prescript_bridge import PrescriptBridge

        bridge = PrescriptBridge()
        self.assertIn("NovaChat", bridge.stageQml("chat"))
        self.assertEqual("", bridge.stageQml("wat"))
        uri = bridge.previewStage("chat")
        self.assertTrue(uri.startswith("file:///"), uri)
        # 每配方独立子目录：规避 QML 目录扫描缓存的 case-mismatch 假错
        target = Path(tempfile.gettempdir()) / "nova-forge-preview" / "chat" / "Stage.qml"
        self.assertTrue(target.exists())
        self.assertIn("NovaChat", target.read_text(encoding="utf-8"))
        # 未知配方：不写任何文件、返回空串
        self.assertEqual("", bridge.previewStage("wat"))
        self.assertFalse((Path(tempfile.gettempdir()) / "nova-forge-preview" / "wat").exists())

    def test_qml_preview_overlay_contract(self) -> None:
        """预览浮层：NovaCard 承载 + 九配方 chips 切换 + Esc 关闭 + 实装口径注释。"""
        qml = (SRC / "nova_forge" / "ui" / "qml" / "prescript_main.qml").read_text(encoding="utf-8")
        for token in ("previewOverlay", "previewLoader", "bridge.previewStage(",
                      "NovaCard { anchors.fill: previewBox", "clickable: true",
                      "win.previewKind = modelData.code", "真 QML 实装渲染"):
            self.assertIn(token, qml, "预览浮层缺 " + token)
        self.assertEqual(qml.count("Keys.onEscapePressed"), 1)


class TestCLIEntry(unittest.TestCase):
    def test_help_registers_gui_and_cli(self) -> None:
        import os
        import subprocess

        env = dict(os.environ)
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-m", "nova_forge.cli", "prescript", "--help"],
            cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ("--gui", "--cli", "--kind", "--list"):
            self.assertIn(flag, result.stdout)
        self.assertIn("NovaIncubator", result.stdout)

    def _dispatch(self, argv: list[str]):
        """打桩两个运行器后跑 cli.main()，返回 (gui mock, cli mock, 退出码)。"""
        from unittest import mock

        import nova_forge.cli as cli_mod

        with mock.patch.object(cli_mod, "run_prescript_gui", return_value=0) as gui, \
             mock.patch.object(cli_mod, "run_prescript", return_value=0) as cmd, \
             mock.patch.object(sys, "argv", ["nova-forge", *argv]):
            try:
                cli_mod.main()
            except SystemExit as exc:
                code = exc.code
            else:
                code = None
        return gui, cmd, code

    def test_bare_subcommand_opens_gui(self) -> None:
        gui, cmd, code = self._dispatch(["prescript"])
        self.assertEqual(gui.call_count, 1, "执行 prescript 应打开主窗口")
        self.assertEqual(cmd.call_count, 0)
        self.assertEqual(code, 0)

    def test_explicit_gui_flag_opens_gui(self) -> None:
        gui, cmd, _ = self._dispatch(["prescript", "--gui"])
        self.assertEqual(gui.call_count, 1)
        self.assertEqual(cmd.call_count, 0)

    def test_cli_flag_keeps_command_line(self) -> None:
        gui, cmd, _ = self._dispatch(["prescript", "--cli"])
        self.assertEqual(gui.call_count, 0)
        self.assertEqual(cmd.call_count, 1)

    def test_kind_argument_keeps_t4_cli_hatching(self) -> None:
        gui, cmd, _ = self._dispatch(["prescript", "--kind", "chat", "--dry-run"])
        self.assertEqual(gui.call_count, 0)
        self.assertEqual(cmd.call_count, 1)
        self.assertEqual(cmd.call_args.kwargs["kind"], "chat")
        self.assertTrue(cmd.call_args.kwargs["dry_run"])

    def test_list_keeps_cli(self) -> None:
        gui, cmd, _ = self._dispatch(["prescript", "--list"])
        self.assertEqual(gui.call_count, 0)
        self.assertEqual(cmd.call_args.kwargs["list_only"], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
