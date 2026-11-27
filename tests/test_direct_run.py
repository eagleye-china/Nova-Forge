# tests/test_direct_run.py
# 创建时间：星期五 2026-11-27 12:41
"""T19：prescript 产物 ``app.py`` 双模式启动真机回归。

T17 把薄入口改成 ``from .main import main`` 后，IDE / 命令行直接
``python app.py`` 会因 ``__package__`` 为空触发
``ImportError: attempted relative import with no known parent package``。
T19 让入口按 ``__package__`` 分支，本测试用真实子进程覆盖三种启动：

* ``python app.py``（脚本模式，**不把产物 src 加进 PYTHONPATH**，靠入口自举）
* ``python -m <pkg>.app``（模块模式，主口径）
* ``from <pkg>.app import main``（console entry ``<pkg>.app:main``）

离屏运行，``NOVA_PRESCRIPT_SMOKE=1`` 让启动器 1.2 s 后自动退出。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova_forge.prescript.gui_model import GUIConfig, hatch  # noqa: E402


def _env(*, include_src: bool, src: Path) -> dict[str, str]:
    """复用 ``_smoke_run`` 的离屏环境；脚本模式刻意不带产物 src。"""
    env = dict(os.environ)
    paths: list[str] = []
    if include_src:
        paths.append(str(src))
    try:
        import pyside_nova

        # 两仓库 editable，但子进程 PYTHONPATH 未必带 pyside-nova
        paths.append(str(Path(pyside_nova.__file__).resolve().parent.parent))
    except ImportError:
        pass
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env.update({
        "NOVA_PRESCRIPT_SMOKE": "1",
        "QT_QPA_PLATFORM": "offscreen",
        "QT_QUICK_BACKEND": "software",
        "PYTHONIOENCODING": "utf-8",
    })
    env.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    return env


class TestDualModeEntry(unittest.TestCase):
    """真机：孵化一次，三种入口各启一次；顺带守住账实同源。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cfg = GUIConfig(kind="chat", path=cls._tmp.name,
                        name="T19 App", package="t19_app")
        cls.result = hatch(cfg, confirmed=True)
        assert cls.result["ok"], cls.result.get("message")
        cls.root = Path(cls._tmp.name) / "t19_app"
        cls.src = cls.root / "src"
        cls.pkg_dir = cls.src / "t19_app"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _run(self, argv: list[str], *, include_src: bool = True) \
            -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *argv], cwd=self.root,
            env=_env(include_src=include_src, src=self.src),
            capture_output=True, text=True, encoding="utf-8", timeout=90,
        )

    def test_layout_and_manifest_unchanged(self) -> None:
        py_names = sorted(p.name for p in self.pkg_dir.glob("*.py"))
        self.assertEqual(py_names, ["__init__.py", "app.py", "main.py"])
        data = json.loads((self.root / "prescript.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["files"]), 17)
        self.assertEqual(data["app"]["entry"], "t19_app.app:main")

    def test_product_entry_matches_generator(self) -> None:
        """落盘 app.py 与生成器 ``_entrypoint()`` 逐字同源，防手工漂移。"""
        from nova_forge.prescript.render import _entrypoint

        actual = (self.pkg_dir / "app.py").read_text(encoding="utf-8")
        self.assertEqual(actual, _entrypoint("t19_app"))

    def test_direct_script_run(self) -> None:
        """核心回归：``python app.py`` 不得再报 attempted relative import。"""
        proc = self._run([str(self.pkg_dir / "app.py")], include_src=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("ImportError", proc.stderr)
        self.assertNotIn("attempted relative import", proc.stderr)

    def test_module_run(self) -> None:
        proc = self._run(["-m", "t19_app.app"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("ImportError", proc.stderr)

    def test_console_entry_importable(self) -> None:
        proc = self._run([
            "-c",
            "from t19_app.app import main; print('entry ok:', callable(main))",
        ])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("entry ok: True", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
