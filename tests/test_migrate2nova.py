# tests/test_migrate2nova.py
"""T3 · migrate2nova 完现专项回归（纯逻辑，不导入 PySide6）。

把「100% 实现迁移」固化为四条可机检口径：
1. 映射表唯一法源 = pyside-nova API 冻结面（147 类型 / 指纹），AUTO 目标零悬空；
2. 试验田 ``ui/saver_window.py`` 的全部唯一 Qt 名 100% 有处置（零静默遗漏）；
3. 五道契约门全绿，**不合格不落地**；dry-run 不写盘、原 .py 零改动；
4. scaffold 产物（QML 骨架 + 降级启动器 + 两份报告）齐备且契约合规，
   §9.3 备份 / --restore 回滚可用，CLI 主名与旧 alias 均可输入。
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.migrate import backup  # noqa: E402
from nova_forge.migrate.contract import run_contract_gates  # noqa: E402
from nova_forge.migrate.freeze import discover_freeze, load_freeze  # noqa: E402
from nova_forge.migrate.plan import (  # noqa: E402
    ContractBlocked,
    plan_migration,
)
from nova_forge.migrate.report import build_json_report, build_todo  # noqa: E402
from nova_forge.migrate.rules import (  # noqa: E402
    AUTO,
    MANUAL,
    classify,
    validate_rules,
)
from nova_forge.migrate.scanner import scan_python  # noqa: E402

TRIAL = SRC / "nova_forge" / "ui" / "saver_window.py"
DISPOSITIONS = (AUTO, "RUNTIME", "NATIVE", MANUAL)


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(SRC))
    return subprocess.run(
        [sys.executable, "-m", "nova_forge.cli", *args],
        cwd=str(ROOT), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
    )


class TestFreezeIsOnlySource(unittest.TestCase):
    """法源链：映射表由冻结面自动生成，无手写 Nova 类型清单。"""

    def test_autodiscover_latest_freeze(self) -> None:
        path = discover_freeze()
        self.assertEqual(path.name, "nova-api-1.11.0.json")
        index = load_freeze()
        self.assertEqual(index.api_version, "1.11.0")
        self.assertEqual(index.count, 147)
        self.assertEqual(index.fingerprint, "9966483dda5a53c4")

    def test_explicit_path_and_bad_schema(self) -> None:
        index = load_freeze(ROOT.parent / "pyside-nova" / "api" / "nova-api-1.11.0.json")
        self.assertEqual(index.count, 147)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.json"
            bad.write_text('{"schema": "nope", "types": {}}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_freeze(bad)

    def test_every_auto_target_exists(self) -> None:
        self.assertEqual(validate_rules(load_freeze()), [])

    def test_unknown_qt_name_falls_back_to_manual(self) -> None:
        rule = classify("QDefinitelyNotRegistered")
        self.assertEqual(rule.disposition, MANUAL)
        self.assertIn("人工评估", rule.note)


class TestScannerCoversTrialField(unittest.TestCase):
    """§9.4 试验田：14 类控件 / 全部 Qt 引用零遗漏。"""

    def setUp(self) -> None:
        self.scan = scan_python(TRIAL)

    def test_trial_field_is_fully_scanned(self) -> None:
        self.assertEqual(self.scan.files_scanned, 1)
        self.assertEqual(self.scan.parse_errors, ())
        names = set(self.scan.unique_qt_names)
        self.assertEqual(len(names), 22)
        for expected in (
            "QApplication", "QCheckBox", "QFileDialog", "QHBoxLayout", "QLabel",
            "QLineEdit", "QListWidget", "QListWidgetItem", "QMainWindow", "QMenu",
            "QPushButton", "QSplitter", "QSystemTrayIcon", "QTextEdit",
            "QVBoxLayout", "QWidget",
        ):
            self.assertIn(expected, names, expected)

    def test_fallback_window_detected(self) -> None:
        self.assertEqual(len(self.scan.fallback_windows), 1)
        self.assertEqual(self.scan.fallback_windows[0].class_name, "SaverWindow")

    def test_alias_import_form_detected(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "alias_form.py"
            p.write_text(
                "from PySide6 import QtWidgets\n"
                "w = QtWidgets.QPushButton()\n", encoding="utf-8"
            )
            scan = scan_python(p)
            self.assertIn("QPushButton", scan.unique_qt_names)


class TestHundredPercentCoverage(unittest.TestCase):
    """100% 口径：每个唯一 Qt 名都有四类处置之一。"""

    def setUp(self) -> None:
        self.index = load_freeze()
        self.scan = scan_python(TRIAL)

    def test_all_names_resolved(self) -> None:
        total = len(self.scan.findings)
        resolved = sum(
            1 for f in self.scan.findings
            if classify(f.qt_name).disposition in DISPOSITIONS
        )
        self.assertEqual(resolved, total)
        self.assertGreater(total, 0)

    def test_auto_targets_all_in_freeze(self) -> None:
        for finding in self.scan.findings:
            rule = classify(finding.qt_name)
            if rule.disposition == AUTO:
                self.assertTrue(self.index.has(rule.target), finding.qt_name)

    def test_five_gates_all_green(self) -> None:
        report = run_contract_gates(self.index, self.scan)
        self.assertEqual(len(report.gates), 5)
        self.assertTrue(report.passed)
        self.assertEqual(report.blockers, ())

    def test_json_and_todo_declare_100_percent(self) -> None:
        plan = plan_migration(TRIAL, scaffold=True, write=False)
        data = json.loads(build_json_report(plan))
        self.assertEqual(data["coverage"]["percent"], 100.0)
        self.assertEqual(data["coverage"]["resolved"], data["coverage"]["total"])
        self.assertTrue(data["gatesPassed"])
        todo = build_todo(plan)
        self.assertIn("100%", todo)
        self.assertIn("QSystemTrayIcon", todo)


class TestDryRunAndOriginalIntegrity(unittest.TestCase):
    """默认 dry-run 不落盘；--scaffold 也绝不改原 .py。"""

    def test_dry_run_writes_nothing(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            plan = plan_migration(TRIAL, scaffold=True, out=out, write=False)
            self.assertFalse(plan.written)
            self.assertFalse(out.exists())

    def test_scaffold_keeps_original_py_byte_identical(self) -> None:
        before = hashlib.sha256(TRIAL.read_bytes()).hexdigest()
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            plan = plan_migration(
                TRIAL, scaffold=True, out=out, write=True, entry_args=["."]
            )
            self.assertTrue(plan.written)
            self.assertEqual({p.name for p in out.iterdir()}, {
                "Main.qml", "main.py", "MIGRATION_TODO.md", "migration-report.json",
            })
        after = hashlib.sha256(TRIAL.read_bytes()).hexdigest()
        self.assertEqual(before, after)


class TestScaffoldArtifacts(unittest.TestCase):
    """骨架 QML / 降级启动器的静态契约。"""

    def setUp(self) -> None:
        from nova_forge.migrate.scaffold import build_scaffold
        self.index = load_freeze()
        self.scan = scan_python(TRIAL)
        pairs = [
            (f.qt_name, classify(f.qt_name).target)
            for f in self.scan.findings
            if classify(f.qt_name).disposition == AUTO
        ]
        self.files = build_scaffold(
            "probe", self.scan, self.index.api_version, pairs, Path("/tmp/probe")
        )

    def test_qml_uses_all_five_slots(self) -> None:
        qml = self.files["Main.qml"]
        for slot in ("menuSlot:", "toolbarSlot:", "pageSlot:", "statusSlot:", "overlaySlot:"):
            self.assertIn(slot, qml, slot)
        # 与契约门口径一致：注释里的说明文字不算自写 modelValue
        active_lines = "\n".join(
            ln for ln in qml.splitlines() if not ln.strip().startswith("//")
        )
        self.assertNotIn("modelValue", active_lines)
        self.assertNotIn("NovaDesktop { }", active_lines, "组合根不得重复嵌套")
        self.assertEqual(qml.count("{"), qml.count("}"))
        self.assertIn("import Nova.Composite.LayoutShell", qml)

    def test_qml_gates_pass(self) -> None:
        report = run_contract_gates(self.index, self.scan, self.files["Main.qml"])
        self.assertTrue(report.passed)
        statuses = {g.name: g.status for g in report.gates}
        self.assertEqual(statuses["modelValue"], "PASS")
        self.assertEqual(statuses["slot-constitution"], "PASS")
        self.assertNotEqual(statuses["qmllint"], "FAIL")

    def test_qmllint_gate_survives_pyside6_import(self) -> None:
        """坑位 83：导入 PySide6 会把 qmllint.exe 注入 PATH；Windows 版不支持
        stdin ``-``，门须落临时文件实跑且零 error 才 PASS，专向单跑与全量跑一致。
        """
        import PySide6

        self.assertIsNotNone(PySide6.__file__)
        report = run_contract_gates(self.index, self.scan, self.files["Main.qml"])
        gate = {g.name: g for g in report.gates}["qmllint"]
        self.assertNotEqual(gate.status, "FAIL", gate.detail)
        self.assertIn("0 error", gate.detail)

    def test_main_py_is_valid_and_has_fallback(self) -> None:
        py = self.files["main.py"]
        tree = ast.parse(py)
        funcs = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        self.assertIn("main", funcs)
        self.assertIn("_run_fallback", funcs)
        self.assertIn("init_nova", py)
        self.assertIn("rootObjects()", py)
        self.assertIn("FALLBACK_CLASS", py)


class TestContractBlocksWrite(unittest.TestCase):
    """契约门 FAIL → 一个字节都不写。"""

    def test_blocked_when_static_tier_fails(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            with patch(
                "nova_forge.migrate.contract.validate_rules",
                return_value=["QPushButton → Nova.Controls.Missing"],
            ), self.assertRaises(ContractBlocked):
                plan_migration(TRIAL, scaffold=True, out=out, write=True)
            self.assertFalse(out.exists(), "契约门 FAIL 时不得创建产物目录")

    def test_existing_artifacts_require_force(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out"
            plan_migration(TRIAL, scaffold=True, out=out, write=True)
            with self.assertRaises(FileExistsError):
                plan_migration(TRIAL, scaffold=True, out=out, write=True)


class TestBackupRoundTrip(unittest.TestCase):
    """§9.3 临时目录自建自删 + --restore 回滚。"""

    def test_create_verify_restore_clean(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "proj"
            root.mkdir()
            target = root / "Main.qml"
            target.write_text("ORIGINAL", encoding="utf-8")
            handle = backup.create(root, [target])
            self.assertTrue(handle.verify())
            target.write_text("CORRUPTED", encoding="utf-8")
            self.assertEqual(handle.restore(), 1)
            self.assertEqual(target.read_text(encoding="utf-8"), "ORIGINAL")
            self.assertEqual(backup.find(handle.backup_id).backup_id, handle.backup_id)
            handle.clean()
            self.assertFalse(handle.path.exists())

    def test_new_file_rollback_deletes_artifact(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "proj"
            root.mkdir()
            fresh = root / "main.py"
            handle = backup.create(root, [fresh])   # existed=false
            fresh.write_text("GENERATED", encoding="utf-8")
            handle.restore()
            self.assertFalse(fresh.exists())
            handle.clean()


class TestCliSurface(unittest.TestCase):
    """CLI 主名 / 旧 alias / 各子模式。"""

    def test_help_lists_migrate2nova(self) -> None:
        result = _cli("migrate2nova", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--scaffold", result.stdout)
        self.assertIn("--restore", result.stdout)

    def test_legacy_alias_still_works(self) -> None:
        result = _cli("migrate_to_nova", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_list_mapping_zero_dangling(self) -> None:
        result = _cli("migrate2nova", "--list-mapping")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("法源链零悬空", result.stdout)

    def test_json_dry_run_reports_100_percent(self) -> None:
        result = _cli(
            "migrate2nova", "-p", str(TRIAL), "--json"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["coverage"]["percent"], 100.0)
        self.assertTrue(data["gatesPassed"])
        self.assertFalse(data["written"])

    def test_root_help_exposes_command(self) -> None:
        result = _cli("--help")
        self.assertIn("migrate2nova", result.stdout)


if __name__ == "__main__":
    unittest.main()
