# tests/test_comment.py
# 创建时间：星期二 2026-11-24 21:39
"""comment 子命令回归测试：守护"绝不损坏原文件" + "只加两行注释" + "跨项目通用"。

覆盖：两行注释格式、正文字节级不变、CRLF / 编码声明 / BOM / shebang 保留、
幂等、force 刷新、目录与生成物跳过、语法错误拒绝、QML 注释语法、
用户手写 docstring 保留、旧版档案头收敛、北京时间 UTC+8、零项目专属知识。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from nova_forge.core.comment_logic import (  # noqa: E402
    BEIJING_TZ,
    STAMP_PREFIX,
    WEEKDAYS_CN,
    _decode,
    _detect_newline,
    _extract_stamp,
    _find_docstring_span_py,
    _validate_qml,
    beijing_stamp,
    build_header,
    iter_source_files,
    process_file,
)


def _body_of(raw: bytes, ext: str) -> bytes:
    """剥离头部（shebang/coding + 路径行 + 创建时间行），返回正文原始字节。"""
    text, enc, _ = _decode(raw)
    marker = "# " if ext == ".py" else "// "
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("#!") or ("coding" in s and s.startswith("#")):
            i += 1
            continue
        break
    if i < len(lines) and lines[i].strip().startswith(marker) and lines[i].strip().endswith(ext):
        i += 1
    # 紧随的时间行：新版「创建时间：」或旧版「# 星期X ... 00:00」假戳
    while i < len(lines) and i < 4:
        s = lines[i].strip()
        if s.startswith(marker) and (
            STAMP_PREFIX in s or any(s[len(marker):].strip().startswith(w) for w in WEEKDAYS_CN)
        ):
            i += 1
        else:
            break
    return "".join(lines[i:]).encode(enc)


class HeaderFormatTests(unittest.TestCase):
    """守护：只加两行注释，不生成文档注释、不生成功能描述。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rel: str, content: bytes) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def test_py_exactly_two_comment_lines(self):
        p = self._write("pkg/mod.py", b"import os\n\nprint('hi')\n")
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done")
        lines = p.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "# pkg/mod.py")
        self.assertTrue(lines[1].startswith(f"# {STAMP_PREFIX}"))
        self.assertEqual(lines[2], "import os")
        self.assertNotIn('"""', "\n".join(lines[:2]))

    def test_qml_uses_double_slash_comments(self):
        p = self._write("qml/Foo.qml", b"import QtQuick\n\nItem { width: 100 }\n")
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done")
        text = p.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(lines[0], "// qml/Foo.qml")
        self.assertTrue(lines[1].startswith(f"// {STAMP_PREFIX}"))
        self.assertNotIn("/*", text)
        self.assertTrue(_validate_qml(text))

    def test_qml_regex_literal_not_rejected(self):
        """合法 QML 里的正则字面量 /\\[.../ 不能让括号平衡器误判为语法错误。"""
        src = (
            "import QtQuick\n\n"
            "Item {\n"
            "    readonly property var _dateTokenRe: /\\[((?:[^\\]\\\\]|\\\\]|\\\\)*)\\]|do|d{1,4}\n"
            "    width: 100\n"
            "}\n"
        ).encode("utf-8")
        p = self._write("qml/NovaUtils.qml", src)
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done", r["reason"])
        self.assertTrue(p.read_text(encoding="utf-8").startswith("// qml/NovaUtils.qml\n// 创建时间："))
        self.assertEqual(_body_of(src, ".qml"), _body_of(p.read_bytes(), ".qml"))

    def test_no_functional_description_generated(self):
        """输出里不得出现任何"功能描述/描述待补充"之类内容。"""
        p = self._write("pkg/whatever.py", b"x = 1\n")
        process_file(p, self.root)
        text = p.read_text(encoding="utf-8")
        for banned in ("描述待补充", "功能描述", "源码档案头由 comment", "自动生成"):
            self.assertNotIn(banned, text)

    def test_user_written_docstring_preserved(self):
        """用户手写的模块 docstring 绝不能被删。"""
        original = '"""用户手写说明。"""\nimport os\n'.encode("utf-8")
        p = self._write("pkg/kept.py", original)
        process_file(p, self.root)
        text = p.read_text(encoding="utf-8")
        self.assertIn('"""用户手写说明。"""', text)
        self.assertIsNotNone(_find_docstring_span_py(text))

    def test_legacy_archive_docstring_collapsed_to_two_lines(self):
        """旧版三段式档案头（docstring 内含创建时间）收敛为两行。"""
        original = (
            "# pkg/old.py\n"
            '"""旧版功能描述。\n\n'
            "创建时间：星期二 2026-11-24 20:19\n"
            '"""\n'
            "import os\n"
        ).encode("utf-8")
        p = self._write("pkg/old.py", original)
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done")
        text = p.read_text(encoding="utf-8")
        self.assertNotIn('"""', text)
        self.assertNotIn("旧版功能描述", text)
        self.assertTrue(text.startswith("# pkg/old.py\n# 创建时间："))
        self.assertTrue(text.rstrip().endswith("import os"))


class SafetyTests(unittest.TestCase):
    """守护"绝不损坏原文件"的安全铁律。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rel: str, content: bytes) -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return p

    def test_inject_preserves_body_bytes_and_crlf(self):
        original = b"# src/demo.py\r\nimport os\r\n\r\nprint('hi')\r\n"
        p = self._write("src/demo.py", original)
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done")
        new_raw = p.read_bytes()
        self.assertIn(b"\r\n", new_raw)
        self.assertEqual(_body_of(original, ".py"), _body_of(new_raw, ".py"))

    def test_inject_preserves_coding_declaration_at_first_line(self):
        original = "# -*- coding: utf-8 -*-\n# demo.py\nimport os\n".encode()
        p = self._write("demo.py", original)
        process_file(p, self.root)
        text = p.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# -*- coding: utf-8 -*-"))

    def test_bom_preserved(self):
        original = b"\xef\xbb\xbf# pkg/bom.py\nx = 1\n"
        p = self._write("pkg/bom.py", original)
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done", r["reason"])
        self.assertEqual(p.read_bytes().count(b"\xef\xbb\xbf"), 1)

    def test_shebang_preserved_at_first_line(self):
        original = b"#!/usr/bin/env python\n# pkg/tool.py\nimport os\n"
        p = self._write("pkg/tool.py", original)
        process_file(p, self.root)
        self.assertTrue(p.read_text(encoding="utf-8").startswith("#!/usr/bin/env python"))

    def test_idempotent_second_run(self):
        p = self._write("demo.py", b"# demo.py\nimport os\n")
        self.assertEqual(process_file(p, self.root)["status"], "done")
        self.assertEqual(process_file(p, self.root)["status"], "already")

    def test_existing_stamp_preserved(self):
        original = (
            "# demo.py\n# 创建时间：星期二 2026-11-24 11:31\nimport os\n"
        ).encode("utf-8")
        p = self._write("demo.py", original)
        process_file(p, self.root)
        self.assertIn("创建时间：星期二 2026-11-24 11:31", p.read_text(encoding="utf-8"))

    def test_force_refreshes_stamp(self):
        p = self._write(
            "demo.py",
            "# demo.py\n# 创建时间：星期一 2020-01-01 08:00\nimport os\n".encode("utf-8"),
        )
        self.assertEqual(process_file(p, self.root)["status"], "already")
        r = process_file(p, self.root, force=True)
        self.assertEqual(r["status"], "done")
        self.assertNotIn("2020-01-01", p.read_text(encoding="utf-8"))
        self.assertIn(STAMP_PREFIX, p.read_text(encoding="utf-8"))

    def test_syntax_error_rejected_without_modification(self):
        original = b"# bad.py\ndef broken(:\n  pass\n"
        p = self._write("bad.py", original)
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "failed")
        self.assertEqual(p.read_bytes(), original)

    def test_generated_rc_file_skipped(self):
        self._write("resources_rc.py", b"# generated\n")
        self.assertNotIn("resources_rc.py", [p.name for p in iter_source_files(self.root)])

    def test_backups_dir_skipped(self):
        self._write("backups/keep.py", b"# keep\n")
        self.assertNotIn("keep.py", [p.name for p in iter_source_files(self.root)])

    def test_legacy_fake_stamp_replaced_by_real_beijing_time(self):
        original = "# demo.py\n# 星期五 2026-11-20 00:00\nimport os\n".encode("utf-8")
        p = self._write("demo.py", original)
        r = process_file(p, self.root)
        self.assertEqual(r["status"], "done")
        text = p.read_text(encoding="utf-8")
        self.assertNotIn("2026-11-20 00:00", text)
        self.assertIn("创建时间：", text)
        # 真实执行时刻的北京戳：不可能是 00:00 的旧假值，且带星期前缀
        stamp_line = [ln for ln in text.splitlines() if STAMP_PREFIX in ln][0]
        self.assertTrue(any(w in stamp_line for w in WEEKDAYS_CN))
        self.assertNotIn("00:00", stamp_line)
        self.assertEqual(_body_of(original, ".py"), _body_of(p.read_bytes(), ".py"))


class CrossProjectTests(unittest.TestCase):
    """守护：引擎零项目专属知识，任意项目开箱即用。"""

    def test_engine_source_has_no_hardcoded_project_paths(self):
        src = (SRC / "nova_forge" / "core" / "comment_logic.py").read_text(encoding="utf-8")
        for banned in ("DESCRIPTIONS", "描述待补充", "src/nova_forge/cli.py", "tmpl_"):
            self.assertNotIn(banned, src)

    def test_foreign_project_layout_works(self):
        """模拟 pyside-nova：完全不同的目录结构 + .qml，仍只加两行注释。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            py = root / "src" / "pyside_nova" / "runtime.py"
            py.parent.mkdir(parents=True)
            py.write_bytes(b"from PySide6.QtCore import QObject\n\nclass NovaRuntime(QObject):\n    pass\n")
            qml = root / "src" / "pyside_nova" / "qml" / "Nova" / "Controls" / "NovaCarousel.qml"
            qml.parent.mkdir(parents=True)
            qml.write_bytes(b"import QtQuick\n\nItem { width: 100 }\n")

            for p in (py, qml):
                r = process_file(p, root)
                self.assertEqual(r["status"], "done", f"{p}: {r['reason']}")
                lines = p.read_text(encoding="utf-8").splitlines()
                self.assertTrue(lines[0].endswith(p.name))
                self.assertTrue(lines[1].startswith(("# ", "// ")))
                self.assertIn(STAMP_PREFIX, lines[1])

            self.assertNotIn("描述待补充", py.read_text(encoding="utf-8"))
            self.assertTrue(_validate_qml(qml.read_text(encoding="utf-8")))

    def test_build_header_no_description_arg(self):
        """签名里不再有描述推导参数，纯路径 + 时间。"""
        text, stamp = build_header("any/pkg/mod.py", ".py", "x = 1\n", b"\n", now_ts=0)
        self.assertEqual(text.splitlines()[0], "# any/pkg/mod.py")
        self.assertEqual(text.splitlines()[1], f"# {STAMP_PREFIX}{stamp}")
        self.assertEqual(text.splitlines()[2], "x = 1")


class BeijingTimeTests(unittest.TestCase):
    def test_stamp_uses_utc8_not_system_local(self):
        stamp = beijing_stamp(0)  # 1970-01-01 08:00 北京
        self.assertIn("1970-01-01 08:00", stamp)
        self.assertTrue(any(stamp.startswith(w) for w in WEEKDAYS_CN))
        self.assertEqual(BEIJING_TZ.utcoffset(None).total_seconds(), 8 * 3600)

    def test_stamp_only_from_real_creation_line(self):
        self.assertIsNone(
            _extract_stamp("# p.py\n# 星期五 2026-11-20 00:00\nimport os\n")
        )
        self.assertEqual(
            _extract_stamp("# p.py\n# 创建时间：星期二 2026-11-24 20:19\nimport os\n"),
            "星期二 2026-11-24 20:19",
        )

    def test_template_triple_quote_not_mistaken_for_docstring(self):
        self.assertIsNone(_find_docstring_span_py('# t.py\nX = """not a docstring"""\n'))


if __name__ == "__main__":
    unittest.main()
