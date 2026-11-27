# tests/test_icons_tool.py
# 创建时间：星期五 2026-11-27 09:50
"""icons 工具回归：以「当前项目」为准扫描资源 + qrc 更新幂等去重。

纯逻辑 / 静态层，全程不在 pytest 进程内 import PySide6（规避坑位 49 的
pytest 生命周期 SIGSEGV）。qrc_builder 是纯标准库模块，可安全直测；
目录探测用 AST 静态断言其签名与接线，真实扫描由子进程离屏验证。
"""
from __future__ import annotations

import ast
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nova_forge.core.qrc_builder import update_qrc_from_directory  # noqa: E402

BRIDGE = SRC / "nova_forge" / "bridge" / "icons_bridge.py"
CLI = SRC / "nova_forge" / "cli.py"
CMD_ICONS = SRC / "nova_forge" / "command" / "cmd_icons.py"
QRC_BUILDER = SRC / "nova_forge" / "core" / "qrc_builder.py"


def _aliases(qrc: Path) -> list[str]:
    root = ET.parse(qrc).getroot()
    return [
        el.get("alias") or ""
        for r in root.findall("qresource")
        for el in r.findall("file")
    ]


class TestQrcIdempotent(unittest.TestCase):
    """重复更新不再产生 _2/_3 别名。"""

    def test_three_updates_keep_one_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            icons = base / "icons"
            icons.mkdir()
            (icons / "sample.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8"
            )
            logs = [update_qrc_from_directory(icons) for _ in range(3)]
            self.assertEqual(_aliases(base / "resources.qrc"), ["sample"])
            self.assertIn("新增条目: 1", logs[0])
            self.assertIn("新增条目: 0", logs[1])
            self.assertIn("新增条目: 0", logs[2])

    def test_semantic_aliases_preserved_and_dup_suffix_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            icons = base / "icons"
            icons.mkdir()
            (icons / "nova.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8"
            )
            (base / "resources.qrc").write_text(
                '<!DOCTYPE RCC>\n<RCC version="1.0">\n'
                '  <qresource prefix="/icons">\n'
                '    <file alias="nova.svg">icons/nova.svg</file>\n'
                '    <file alias="nova">icons/nova.svg</file>\n'
                '    <file alias="nova_2">icons/nova.svg</file>\n'
                '  </qresource>\n</RCC>\n',
                encoding="utf-8",
            )
            update_qrc_from_directory(icons)
            aliases = _aliases(base / "resources.qrc")
            self.assertIn("nova.svg", aliases)   # 语义别名保留
            self.assertIn("nova", aliases)       # 文件名别名保留
            self.assertNotIn("nova_2", aliases)  # 重复后缀清除


class TestProjectScope(unittest.TestCase):
    """目录探测以当前项目为准，且 CLI/GUI 接线完整。"""

    @staticmethod
    def _functions(path: Path) -> dict[str, ast.FunctionDef]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return {
            n.name: n
            for n in tree.body
            if isinstance(n, ast.FunctionDef)
        }

    def test_detect_project_root_accepts_explicit(self) -> None:
        fns = self._functions(BRIDGE)
        args = [a.arg for a in fns["detect_project_root"].args.args]
        self.assertIn("explicit", args)
        for name in ("detect_assets_base", "detect_resources_base"):
            self.assertIn("root", [a.arg for a in fns[name].args.args])

    def test_no_hardcoded_nova_forge_resources(self) -> None:
        # 资源库探测的代码语句不再固定写死 nova_forge 包目录（docstring 说明不算）
        fns = self._functions(BRIDGE)
        code = [
            n for n in fns["detect_resources_base"].body
            if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str))
        ]
        stmts = "\n".join(
            ast.get_source_segment(BRIDGE.read_text(encoding="utf-8"), n) or ""
            for n in code
        )
        self.assertNotIn("nova_forge", stmts)

    def test_cli_project_flag_wired(self) -> None:
        cli = CLI.read_text(encoding="utf-8")
        self.assertIn('"--project"', cli)
        # 行为契约：CLI 把整个 args 透传给 run_icons，由内部取 args.project；
        # 不写死 lambda 参数名（曾因 lambda 传 project_root= 触发 TypeError）。
        self.assertIn("p_icons.set_defaults(func=run_icons)", cli)
        self.assertIn('getattr(args, "project", None)', cli)

    def test_cmd_icons_wires_project_root(self) -> None:
        text = CMD_ICONS.read_text(encoding="utf-8")
        self.assertIn("def run_icons(project_root", text)
        self.assertIn("IconsBridge(project_root=project_root)", text)

    def test_bridge_init_accepts_project_root(self) -> None:
        tree = ast.parse(BRIDGE.read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "IconsBridge")
        init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        args = [a.arg for a in init.args.args]
        self.assertIn("project_root", args)


if __name__ == "__main__":
    unittest.main()
