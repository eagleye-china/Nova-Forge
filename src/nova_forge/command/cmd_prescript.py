# src/nova_forge/command/cmd_prescript.py
# 创建时间：星期四 2026-11-26 15:42
"""nova-forge prescript —— 用 NovaIncubator 孵化九类企业级应用。

用法（默认 GUI 主窗口，T11；带参数时保留 T4 的 CLI 一键孵化）：
    nova-forge prescript                       # 打开应用孵化器工作台 GUI（七槽 + 人工确认闸门）
    nova-forge prescript --gui                 # 同上，显式入口
    nova-forge prescript --cli                 # 命令行交互模式
    nova-forge prescript --list                # 列九类配方
    nova-forge prescript --kind chat --path D:\\apps\\mei-chat
    nova-forge prescript --kind chat --path . --dry-run
"""

from __future__ import annotations

import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path

from .. import __version__
from ..prescript.catalog import KINDS, get_kind
from ..prescript.render import plan_project, render_project

# 模块级保活：外部已有 QApplication 时 GUI 函数会立即返回，
# QML 引擎 / 桥接对象必须挂在这里，否则被 GC 后主窗口会崩。
_GUI_KEEPALIVE: list = []


def _ask(prompt: str, default: str = "") -> str:
    raw = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return raw or default


def _rule(char: str = "─", width: int = 66) -> str:
    return char * width


def print_kinds() -> None:
    print()
    print("  🧬 nova-forge prescript · 九类应用配方")
    print("  " + _rule())
    print(f"  {'代号':<4} {'--kind':<10} {'应用':<14} {'壳':<20} 定位")
    print("  " + _rule())
    for k in KINDS:
        print(f"  {k.recipe:<5} {k.code:<11} {k.zh:<15} {k.shell:<21} {k.tagline}")
    print("  " + _rule())
    print("  例：nova-forge prescript --kind chat --path D:\\apps\\mei-chat")
    print()


def _verify(project) -> list[tuple[str, bool, str]]:
    """静态三重校验：工程完整性 / Python 语法 / QML 结构 + 清单一致。"""
    results: list[tuple[str, bool, str]] = []
    root = project.root

    missing = [rel for rel in project.files if not (root / rel).exists()]
    results.append(("工程完整性", not missing, f"{len(project.files)} 个文件" if not missing
                    else "缺失 " + ", ".join(missing[:3])))

    py_files = list((root / "src").rglob("*.py"))
    py_bad: list[str] = []
    for path in py_files:
        try:
            py_compile.compile(str(path), doraise=True, cfile=str(path) + ".pyc")
        except py_compile.PyCompileError as exc:
            py_bad.append(f"{path.name}: {exc.msg.splitlines()[0]}")
    for stray in (root / "src").rglob("*.pyc"):
        stray.unlink(missing_ok=True)
    results.append(("Python 语法", not py_bad,
                    f"{len(py_files)} 个模块编译通过" if not py_bad else "; ".join(py_bad[:2])))

    qml_files = sorted((root / "src").rglob("*.qml"))
    qml_bad: list[str] = []
    for path in qml_files:
        text = path.read_text(encoding="utf-8")
        if text.count("{") != text.count("}"):
            qml_bad.append(f"{path.name} 花括号不配对")
        if path.name == "Main.qml" and "NovaIncubator" not in text:
            qml_bad.append("Main.qml 未使用 NovaIncubator")
        if path.name == "Stage.qml" and project.kind.shell not in text:
            qml_bad.append(f"Stage.qml 未使用 {project.kind.shell}")
    results.append(("QML 结构", not qml_bad,
                    f"{len(qml_files)} 个界面结构完整" if not qml_bad else "; ".join(qml_bad[:2])))

    try:
        manifest = json.loads((root / "prescript.json").read_text(encoding="utf-8"))
        ok = (manifest["prescript"]["kind"] == project.kind.code
              and manifest["prescript"]["shell"] == project.kind.shell)
        detail = f"配方 {manifest['prescript']['recipe']} · 壳 {manifest['prescript']['shell']}"
    except Exception as exc:
        ok, detail = False, f"清单不可解析：{exc}"
    results.append(("清单一致", ok, detail))
    return results


def _smoke_run(project) -> tuple[bool, str]:
    """端到端实跑：离屏启动刚孵化的应用 1.2 s，检查 QML 运行时是否有错误。"""
    try:
        import PySide6  # noqa: F401
    except ImportError:
        return True, "跳过（当前环境未安装 PySide6，静态校验仍有效）"

    env = dict(os.environ)
    paths = [str(project.root / "src")]
    try:
        import pyside_nova

        # 开发环境常见：两仓库都 editable，但 CLI 进程的 PYTHONPATH 未必带 pyside-nova
        paths.append(str(Path(pyside_nova.__file__).resolve().parent.parent))
    except ImportError:
        pass
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    env.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    env["NOVA_PRESCRIPT_SMOKE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", project.package + ".app"],
            cwd=project.root, env=env, capture_output=True,
            text=True, encoding="utf-8", timeout=45,
        )
    except subprocess.TimeoutExpired:
        return False, "离屏启动超时（45 s）"

    output = (proc.stdout or "") + (proc.stderr or "")
    noisy = [line for line in output.splitlines()
             if ("error" in line.lower() and "QFontDatabase" not in line)
             or "加载失败" in line]
    if proc.returncode != 0:
        return False, f"退出码 {proc.returncode}"
    if noisy:
        return False, noisy[0][:110]
    return True, "根对象加载成功 · 1.2 s 无 QML ERROR"


def _preview(project) -> str:
    """dry-run 预览：列出将写入的文件与体量。"""
    lines = [f"  📁 {project.root}", "  " + _rule()]
    total = 0
    for rel, text in project.files.items():
        size = len(text.encode("utf-8"))
        total += size
        lines.append(f"  {'+' if not (project.root / rel).exists() else '='} {rel:<46} {size:>6,} B")
    lines.append("  " + _rule())
    lines.append(f"  共 {len(project.files)} 个文件 · {total:,} B（dry-run 未落盘）")
    return "\n".join(lines)


def run_prescript(
    kind: str | None = None,
    path: str | None = None,
    name: str | None = None,
    package: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    list_only: bool = False,
    verify_run: bool = False,
) -> int:
    if list_only:
        print_kinds()
        return 0

    if not kind:
        print_kinds()
        kind = _ask("  选择配方代号或 --kind（如 P6 / chat）", "chat")
        if re.fullmatch(r"[pP]\d", kind):
            code = kind.upper()[1:]
            kind = KINDS[int(code) - 1].code if code.isdigit() and 1 <= int(code) <= len(KINDS) else kind

    try:
        spec = get_kind(kind)
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if not path:
        path = _ask("  📂 目标目录（绝对路径或相对路径）", f"./{spec.code}-app")
    root = Path(path).expanduser()
    occupied = root.exists() and any(root.iterdir())
    if occupied and not force and not dry_run:
        print(f"\n⚠️  目录已存在且非空：{root.resolve()}")
        choice = _ask("  如何继续？[Y] 跳过同名文件 / [N] 覆盖 / [C] 取消", "Y").upper()
        if choice == "C":
            print("  已取消，未写入任何文件。")
            return 1
        force = choice == "N"

    if not name:
        name = root.name or spec.zh
    project = plan_project(spec.code, root, name, package, __version__)

    print()
    print("  🧬 nova-forge prescript · 一键孵化")
    print("  " + _rule())
    print(f"  配方    {spec.recipe} · {spec.zh}（{spec.en}）")
    print(f"  壳      {spec.shell}  · 宿主 NovaIncubator 七槽")
    print(f"  工程    {project.root}")
    print(f"  包名    {project.package}")
    print("  " + _rule())

    if dry_run:
        print(_preview(project))
        print("  下一步：去掉 --dry-run 真正落盘。")
        return 0

    project = render_project(spec.code, root, name, package, __version__, force=force)

    results = _verify(project)
    if verify_run:
        ok, detail = _smoke_run(project)
        results.append(("离屏实跑", ok, detail))
    print()
    print("  🔍 交付校验")
    for label, ok, detail in results:
        mark = "✓" if ok else "✗"
        print(f"   {mark} {label:<8} {detail}")

    ok_all = all(ok for _, ok, _ in results)
    print()
    print("  " + _rule())
    if ok_all:
        print(f"  ✅ 孵化完成 · {len(results)}/{len(results)} 校验通过")
        print()
        print("  启动：")
        print(f"    cd {project.root}")
        print(f"    python -m {project.package}.app")
        print()
        print("  发布：")
        print("    python -m build && twine upload dist/*")
        print("  " + _rule())
        return 0

    print("  ❌ 校验未通过 · 产物已落盘，请按上面提示修正")
    return 1


def run_prescript_gui() -> int:
    """启动 ``prescript`` 默认主窗口：QML + pyside-nova ``NovaIncubator`` 七槽。

    照 ``icons`` 的 ``QApplication + QQmlApplicationEngine + init_nova + bridge +
    _KEEPALIVE`` 模式；组件库缺失或 QML 加载失败时降级回原命令行交互模式，
    保证子命令始终可用。所有落盘只在主窗口人工确认闸门之后发生。
    """
    import os
    from pathlib import Path

    # Fusion 跨平台一致、支持自定义滚动条，避免 Basic/Windows 样式告警
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QIcon
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtWidgets import QApplication
        from pyside_nova import init_nova
    except ImportError:
        print(
            "[WARN] GUI 需要 PySide6 + pyside-nova（pip install 'nova-forge[gui]'），"
            "已回退到命令行交互模式。",
            file=sys.stderr,
        )
        return run_prescript()

    from ..bridge.prescript_bridge import PrescriptBridge
    from ..resources import resources_rc  # noqa: F401  注册 :/icons/ 应用图标
    from ..utils.window_utils import apply_dark_title_bars

    qml_file = Path(__file__).resolve().parent.parent / "ui" / "qml" / "prescript_main.qml"

    app = QApplication.instance()
    created_here = app is None
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("nova-forge")
        app.setApplicationDisplayName("Nova-Forge · 应用孵化器工作台")

    # 第 10 个专属主题组合根 NovaIncubator 的应用图标（孵化器工作台自己的窗口图标）
    app.setWindowIcon(QIcon(":/icons/app-incubator.svg"))

    engine = QQmlApplicationEngine()
    init_nova(engine)  # 注册 Nova.* QML 模块（含 Nova.Composite.LayoutShell）
    bridge = PrescriptBridge()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("[WARN] QML 主窗口加载失败，已回退到命令行交互模式。", file=sys.stderr)
        engine.deleteLater()
        return run_prescript()

    # 窗口句柄此刻才有效：初始按暗色主题同步原生标题栏（QML 侧另有主题变化同步）
    apply_dark_title_bars(True)
    _GUI_KEEPALIVE.append((engine, bridge))
    if created_here:
        return app.exec()
    return 0
