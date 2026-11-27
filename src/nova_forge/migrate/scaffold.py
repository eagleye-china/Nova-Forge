# src/nova_forge/migrate/scaffold.py
"""``--scaffold`` 产物：可运行的 QML 骨架 + 降级启动器。

设计约束（§9.4 / 组合宪法）：
- **原 .py 零改动**：只写新文件，绝不覆盖目标工程的既有 Python 源码。
- **组合根槽位注入**：骨架用 ``NovaDesktop`` 五槽承载，业务内容一律由槽位注入，
  不内联业务语义（CC-1~CC-8），故能通过 ``slot-constitution`` 门。
- **受控契约**：生成 QML 零 ``modelValue`` 自写，只发 ``actionRequested`` 意图。
- **降级**：``main.py`` 先试 QML；``rootObjects()`` 为空即动态加载原
  ``QMainWindow`` 子类并显示，绝不静默吞掉加载失败。
- **AUTO 目标来自冻结面**：每个实例化的组件都是冻结面真实存在的公共类型。
"""
from __future__ import annotations

import os
from pathlib import Path

from .scanner import ScanResult


def _relpath(target: Path, origin: Path) -> str:
    """原窗口文件相对产物目录的路径（POSIX 风格，供 Path 拼接）。

    跨盘符时 ``os.path.relpath`` 会抛 ValueError，此时退回绝对路径并在
    MIGRATION_TODO 提示可用 ``--out`` 落回工程内以获得可移植相对路径。
    """
    try:
        return Path(os.path.relpath(target.resolve(), origin.resolve())).as_posix()
    except ValueError:
        return target.resolve().as_posix()


def render_main_qml(
    project_name: str,
    pairs: list[tuple[str, str]],
    freeze_version: str,
) -> str:
    """渲染 Main.qml：五槽注入 + AUTO 组件实例清单。

    :param pairs: ``(Qt 名, Nova 冻结面 fqname)``，只含 AUTO 处置。
    """
    seen: dict[str, str] = {}
    for qt_name, target in pairs:
        seen.setdefault(target, qt_name)

    # 骨架根已用 NovaDesktop 承载（QMainWindow → NovaDesktop），不重复实例化组合根
    shell_root = "Nova.Composite.LayoutShell.NovaDesktop"
    instances: list[str] = []
    for target, qt_name in sorted(seen.items()):
        if target == shell_root:
            continue
        short = target.rsplit(".", 1)[-1]
        instances.append(
            f"                {short} {{ }}   // ← {qt_name} → {target}"
        )
    if not instances:
        instances.append('                NovaText { text: "（未发现可自动映射的控件）" }')

    body = "\n".join(instances)
    return f'''// Main.qml · {project_name} · 由 nova-forge migrate2nova 生成（骨架）
// 冻结面法源：pyside-nova {freeze_version}；AUTO 组件全部来自冻结面公共类型。
// 业务语义须由宿主经槽位注入；本骨架不含任何业务状态 / modelValue 自写。
import QtQuick
import QtQuick.Controls
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

ApplicationWindow {{
    id: win
    width: 1280
    height: 800
    minimumWidth: 760
    minimumHeight: 520
    visible: true
    title: "{project_name} · Nova 迁移骨架"
    color: NovaTheme.page

    // 受控契约：只 emit 意图，不自写宿主状态
    signal actionRequested(string name)

    NovaDesktop {{
        anchors.fill: parent

        menuSlot: Item {{
            NovaText {{ text: "菜单（由宿主注入）" }}
        }}
        toolbarSlot: Item {{
            NovaText {{ text: "工具栏（由宿主注入）" }}
        }}
        pageSlot: Item {{
            Column {{
                anchors {{ left: parent.left; top: parent.top; margins: 16 }}
                spacing: 8
                NovaText {{ text: "迁移装配区 · {freeze_version}" }}
{body}
            }}
        }}
        statusSlot: Item {{
            NovaText {{ text: "就绪 · QML 骨架" }}
        }}
        overlaySlot: Item {{ }}
    }}
}}
'''


def render_main_py(
    project_name: str,
    out_dir: Path,
    fallback_file: Path | None,
    fallback_class: str | None,
    fallback_args: list[object],
    freeze_version: str,
) -> str:
    """渲染 main.py：QML 优先，失败降级回原 QtWidgets 窗口。"""
    file_literal = (
        repr(_relpath(fallback_file, out_dir)) if fallback_file is not None else "None"
    )
    class_literal = repr(fallback_class) if fallback_class else "None"
    args_literal = repr(fallback_args)

    return f'''# main.py · {project_name} · 由 nova-forge migrate2nova 生成
"""QML 优先启动器：``init_nova()`` → Main.qml；加载失败降级回原 QtWidgets 窗口。

由 ``nova-forge migrate2nova --scaffold`` 生成（冻结面 {freeze_version}）。
原工程 .py 零改动；本文件是新增入口，不替代也不修改原窗口类。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from pyside_nova import init_nova

HERE = Path(__file__).resolve().parent
QML_FILE = HERE / "Main.qml"
FALLBACK_FILE = {file_literal}
FALLBACK_CLASS = {class_literal}
FALLBACK_ARGS = {args_literal}


def _run_fallback(app: QApplication) -> int:
    """QML 加载失败：动态加载原窗口模块并显示，绝不静默吞错。"""
    if FALLBACK_FILE is None or FALLBACK_CLASS is None:
        print(
            "QML 加载失败，且未配置降级入口（--entry 或 --entry-args）；"
            "请检查 pyside-nova 版本与 Main.qml",
            file=sys.stderr,
        )
        return 1
    path = (HERE / FALLBACK_FILE).resolve()
    if not path.is_file():
        print(f"降级入口文件不存在：{{path}}", file=sys.stderr)
        return 1
    spec = importlib.util.spec_from_file_location("nova_migrate_original", str(path))
    if spec is None or spec.loader is None:
        print(f"无法加载降级模块：{{path}}", file=sys.stderr)
        return 1
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cls = getattr(module, FALLBACK_CLASS)
    window = cls(*FALLBACK_ARGS)
    window.show()
    return app.exec()


def main() -> int:
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    init_nova(engine)
    engine.load(str(QML_FILE))
    if engine.rootObjects():
        return app.exec()
    print("QML 加载失败：降级回原 QtWidgets 窗口", file=sys.stderr)
    return _run_fallback(app)


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_scaffold(
    project_name: str,
    scan: ScanResult,
    freeze_version: str,
    pairs: list[tuple[str, str]],
    out_dir: Path,
    fallback_args: list[object] | None = None,
) -> dict[str, str]:
    """返回 ``相对路径 → 文本`` 的骨架产物集合（不落盘）。"""
    args = list(fallback_args or [])
    fallback = scan.fallback_windows[0] if scan.fallback_windows else None
    fb_file: Path | None = None
    fb_class: str | None = None
    if fallback is not None:
        base = scan.root if scan.root.is_dir() else scan.root.parent
        fb_file = base / fallback.file
        fb_class = fallback.class_name

    return {
        "Main.qml": render_main_qml(project_name, pairs, freeze_version),
        "main.py": render_main_py(
            project_name, out_dir, fb_file, fb_class, args, freeze_version
        ),
    }
