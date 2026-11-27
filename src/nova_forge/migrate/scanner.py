# src/nova_forge/migrate/scanner.py
"""目标工程的 QtWidgets 引用扫描（纯 AST，零导入 PySide6）。

扫描三类引用并去重到「唯一 Qt 名 + 出现位置」：
1. ``from PySide6.Qt* import Xxx`` —— import 声明（覆盖率的基准口径）；
2. ``Xxx(...)`` —— 构造调用（统计真实使用次数，报告里给出热度）；
3. ``class Foo(Xxx)`` —— 类继承（同时识别可降级回退的原 QMainWindow 子类）。

不执行目标代码、不导入 PySide6，规避坑位 49 的 pytest 生命周期 SIGSEGV。
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

QT_PREFIX = "PySide6.Qt"
SKIP_DIRS = frozenset({
    "__pycache__", ".git", ".hg", ".svn", ".venv", "venv", "env",
    "node_modules", "dist", "build", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", "site-packages", ".workbuddy", ".idea",
})
QT_WIDGET_WINDOW_BASES = frozenset({"QMainWindow", "QWidget", "QDialog"})


@dataclass(frozen=True)
class Occurrence:
    """一处引用。"""

    file: str
    line: int
    kind: str  # "import" | "call" | "base"


@dataclass(frozen=True)
class Finding:
    """一个唯一 Qt 名及其全部出现位置。"""

    qt_name: str
    qt_module: str
    occurrences: tuple[Occurrence, ...]

    @property
    def count(self) -> int:
        return len(self.occurrences)

    @property
    def call_count(self) -> int:
        return sum(1 for o in self.occurrences if o.kind == "call")


@dataclass(frozen=True)
class FallbackWindow:
    """可降级回原窗口的 QtWidgets 根窗口类。"""

    module: str
    class_name: str
    file: str


@dataclass(frozen=True)
class ScanResult:
    """一次扫描的完整结果。"""

    root: Path
    files_scanned: int
    findings: tuple[Finding, ...]
    fallback_windows: tuple[FallbackWindow, ...]
    parse_errors: tuple[str, ...]

    @property
    def unique_qt_names(self) -> tuple[str, ...]:
        return tuple(f.qt_name for f in self.findings)


def _iter_python_files(root: Path):
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _module_of(path: Path, root: Path) -> str:
    """把文件路径还原成可 import 的点分模块名（用于降级启动器）。"""
    try:
        rel = path.relative_to(root if root.is_dir() else root.parent)
    except ValueError:
        rel = path
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) if parts else "main"


def scan_python(root: str | Path) -> ScanResult:
    """扫描文件或目录，返回去重后的 Qt 引用清单。"""
    target = Path(root).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"迁移目标不存在：{target}")

    occurrences: dict[str, list[Occurrence]] = {}
    modules: dict[str, str] = {}
    fallbacks: list[FallbackWindow] = []
    parse_errors: list[str] = []
    files_scanned = 0
    base_root = target if target.is_dir() else target.parent

    for path in _iter_python_files(target):
        files_scanned += 1
        rel = str(path.relative_to(base_root)) if path.is_relative_to(base_root) else str(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append(f"{rel}: {exc}")
            continue

        imported: dict[str, str] = {}  # 本地别名 → Qt 名
        qt_module_aliases: set[str] = set()  # from PySide6 import QtWidgets 形式

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "PySide6":
                    for alias in node.names:
                        if alias.name.startswith("Qt"):
                            qt_module_aliases.add(alias.asname or alias.name)
                elif node.module and node.module.startswith(QT_PREFIX):
                    for alias in node.names:
                        qt_name = alias.name
                        local = alias.asname or qt_name
                        imported[local] = qt_name
                        modules.setdefault(qt_name, node.module)
                        occurrences.setdefault(qt_name, []).append(
                            Occurrence(rel, node.lineno, "import")
                        )
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in imported:
                    qt_name = imported[func.id]
                    occurrences.setdefault(qt_name, []).append(
                        Occurrence(rel, node.lineno, "call")
                    )
                elif (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id in qt_module_aliases
                ):
                    qt_name = func.attr
                    modules.setdefault(qt_name, f"PySide6.{func.value.id}")
                    occurrences.setdefault(qt_name, []).append(
                        Occurrence(rel, node.lineno, "call")
                    )
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    name = None
                    if isinstance(base, ast.Name):
                        name = base.id
                    elif isinstance(base, ast.Attribute):
                        name = base.attr
                    if name and name in QT_WIDGET_WINDOW_BASES:
                        modules.setdefault(name, "PySide6.QtWidgets")
                        occurrences.setdefault(name, []).append(
                            Occurrence(rel, node.lineno, "base")
                        )
                        fallbacks.append(
                            FallbackWindow(_module_of(path, base_root), node.name, rel)
                        )

    findings = tuple(
        Finding(name, modules.get(name, QT_PREFIX), tuple(locs))
        for name, locs in sorted(occurrences.items())
    )
    return ScanResult(
        root=target,
        files_scanned=files_scanned,
        findings=findings,
        fallback_windows=tuple(fallbacks),
        parse_errors=tuple(parse_errors),
    )
