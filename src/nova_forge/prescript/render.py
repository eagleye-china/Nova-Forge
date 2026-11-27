# src/nova_forge/prescript/render.py
# 创建时间：星期四 2026-11-26 15:38
"""把配方渲染成可直接运行的 PySide6 工程（含运行包 / 治理清单 / 自检用例）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..templates import DEFAULT_AUTHOR_EMAIL, DEFAULT_GITHUB_USER, DEFAULT_VERSION
from ..templates.tmpl_host_main_qml import build_main_qml
from .catalog import KINDS, Kind, get_kind
from .stages import STAGES

API_VERSION = "1.3.0"
NOVA_FLOOR = "1.2.0"


@dataclass
class Project:
    """渲染结果：路径 → 内容；写入与自检共用同一份内存快照。"""

    kind: Kind
    root: Path
    app_name: str
    package: str
    files: dict[str, str] = field(default_factory=dict)

    @property
    def manifest(self) -> dict:
        return json.loads(self.files["prescript.json"])


def normalise_package(name: str) -> str:
    """把任意应用名压成合法 Python 包名；空值回落到 prescript_app。"""
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
    if not slug:
        slug = "prescript_app"
    if slug[0].isdigit():
        slug = "app_" + slug
    return slug


def plan_project(
    kind_code: str,
    target_dir: str | Path,
    app_name: str | None = None,
    package: str | None = None,
    forge_version: str = "0.0.0",
    include_files: set[str] | None = None,
) -> Project:
    """在内存中组装整个工程（不落盘），便于 dry-run 与自检。

    ``include_files`` 为 None 时生成全部文件；否则只保留集合内的相对路径。
    README 结构树与 ``prescript.json.files`` 都由过滤后的 ``all_rel`` 生成，
    因此选中子集落盘后依旧账实相符（不会列出未创建的文件）。
    """
    kind = get_kind(kind_code)
    root = Path(target_dir).expanduser().resolve()
    name = (app_name or root.name or "Prescript App").strip()
    pkg = normalise_package(package or name)

    presets = [
        {
            "code": k.recipe,
            "kind": k.code,
            "zh": k.zh,
            "shell": k.shell,
            "loaded": k.code == kind.code,
        }
        for k in KINDS
    ]

    # T13：先算 scaffold 叠加清单，让 README 结构树 / manifest.files 与实际落盘同源
    from ..core.scaffold_logic import prescript_overlay_plan

    overlay = prescript_overlay_plan(root, app_name=name, package=pkg)
    all_rel = sorted([
        "pyproject.toml", "README.md", ".gitignore",
        # T17 入口改名：启动器 app.py → main.py，薄入口 __main__.py → app.py；
        # 不再生成 __main__.py，模块启动统一为 `python -m <pkg>.app`。
        f"src/{pkg}/__init__.py", f"src/{pkg}/app.py", f"src/{pkg}/main.py",
        f"src/{pkg}/qml/Main.qml", f"src/{pkg}/qml/Stage.qml",
        f"src/{pkg}/assets/{kind.icon}", "prescript.json", "tests/test_smoke.py",
        *overlay.keys(),
    ])
    if include_files is not None:
        all_rel = [rel for rel in all_rel if rel in include_files]

    files: dict[str, str] = {}
    files["pyproject.toml"] = _pyproject(name, pkg, kind)
    files["README.md"] = _readme(name, pkg, kind, all_rel)
    files[".gitignore"] = _gitignore()
    files[f"src/{pkg}/__init__.py"] = _pkg_init(name, pkg, kind)
    files[f"src/{pkg}/app.py"] = _entrypoint(pkg)
    files[f"src/{pkg}/main.py"] = _bootstrap(name, pkg, kind)
    files[f"src/{pkg}/qml/Main.qml"] = build_main_qml(
        kind, name, presets, API_VERSION, forge_version
    )
    files[f"src/{pkg}/qml/Stage.qml"] = STAGES[kind.code]
    # 应用图标随产物落盘：产物是独立工程，运行时读不到 nova-forge 的 qrc
    from ..resources.app_icons import ICONS

    files[f"src/{pkg}/assets/{kind.icon}"] = ICONS[kind.icon]
    files["prescript.json"] = _manifest(name, pkg, kind, forge_version, all_rel)
    files["tests/test_smoke.py"] = _test(pkg)
    # T13：叠加 scaffold 通用工程骨架（LICENSE / README_zh / CHANGELOG /
    # HOW_TO_PUBLISH / publish.yml / project_structure.txt），单一事实源来自
    # core.scaffold_logic；与 prescript 专属文件合并后由 render_project 统一落盘，
    # GUI 预览 fileCount / written 自然账实相符。
    files.update(overlay)
    if include_files is not None:
        files = {rel: text for rel, text in files.items() if rel in all_rel}
    return Project(kind=kind, root=root, app_name=name, package=pkg, files=files)


def render_project(
    kind_code: str,
    target_dir: str | Path,
    app_name: str | None = None,
    package: str | None = None,
    forge_version: str = "0.0.0",
    force: bool = False,
    include_files: set[str] | None = None,
) -> Project:
    """落盘；默认不覆盖已存在文件（force=True 才覆盖）。

    ``include_files`` 透传给 ``plan_project``：GUI 组选框取消的文件不写入，
    且 README / manifest 同步剔除，保持账实相符。
    """
    project = plan_project(
        kind_code, target_dir, app_name, package, forge_version,
        include_files=include_files,
    )
    project.root.mkdir(parents=True, exist_ok=True)
    for rel, text in project.files.items():
        path = project.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force:
            continue
        path.write_text(text, encoding="utf-8", newline="\n")
    return project


# ── 各文件模板 ─────────────────────────────────────────────────────────────
def _pyproject(name: str, pkg: str, kind: Kind) -> str:
    return f"""[build-system]
requires = ["setuptools>=68.2", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{pkg.replace('_', '-')}"
version = "{DEFAULT_VERSION}"
description = "{name} —— {kind.zh}（nova-forge prescript · {kind.recipe} · {kind.shell}）"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{{ name = "{DEFAULT_GITHUB_USER}", email = "{DEFAULT_AUTHOR_EMAIL}" }}]
dependencies = [
    "PySide6>=6.6",
    "pyside-nova>={NOVA_FLOOR}",
]

[project.scripts]
{pkg.replace('_', '-')} = "{pkg}.app:main"

[tool.setuptools.packages.find]
where = ["src"]
include = ["{pkg}*"]

[tool.setuptools.package-data]
{pkg} = ["qml/*.qml"]
"""


def _gitignore() -> str:
    return """__pycache__/
*.py[cod]
.venv/
venv/
dist/
build/
*.egg-info/
.pytest_cache/
.ruff_cache/
.idea/
.vscode/
"""


def _pkg_init(name: str, pkg: str, kind: Kind) -> str:
    return f'''""" {name} —— {kind.zh}（配方 {kind.recipe} · 壳 {kind.shell}）。

由 nova-forge prescript 生成：运行 `python -m {pkg}.app` 启动。
"""
__version__ = "0.1.0"
__prescript__ = "{kind.code}"
__shell__ = "{kind.shell}"
'''


def _entrypoint(pkg: str) -> str:
    """薄入口（原 ``__main__.py``）：把 ``main`` 从启动器 re-export 给命令行脚本。

    三种启动都落在这里；真正的应用装配在 ``main.py``（``_bootstrap``）：
    ``python -m <pkg>.app`` · ``[project.scripts] <dist> = "<pkg>.app:main"`` ·
    ``python app.py``（IDE 直接 Run）。按 ``__package__`` 分支而非
    ``try/except ImportError``，避免吞掉 ``main.py`` 内部真正的依赖错误。
    """
    dist = pkg.replace("_", "-")
    return f'''# src/{pkg}/app.py
# 应用入口：python -m {pkg}.app / python app.py / 安装后 {dist}
"""启动入口：应用装配在 main.py，此处只负责转发。

* 包内运行（``python -m {pkg}.app``、console entry ``{pkg}.app:main``）：
  ``__package__`` 非空，走相对导入 ``.main``；
* 直接脚本（``python app.py``、PyCharm 右键 Run）：``__package__`` 为空，
  把脚本目录加入 ``sys.path`` 后绝对导入 ``main``。
按 ``__package__`` 分支，不吞 ``main.py`` 内部真正的 ImportError。
"""
import sys
from pathlib import Path

if __package__ in (None, ""):
    # 直接脚本：显式补脚本目录（Python -P / PYTHONSAFEPATH 下 sys.path[0] 不含它）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from main import main
else:
    # 包内：python -m <pkg>.app / console entry <pkg>.app:main
    from .main import main

if __name__ == "__main__":
    sys.exit(main())
'''


# 孵化产物自带的原生标题栏明暗同步 helper（普通字符串，避免 f-string 大括号转义）。
# 产物是独立工程，运行时读不到 nova-forge 的 qrc / utils，必须自包含、零外部依赖。
_WINDOW_CHROME_HELPER = '''

# ── Windows 原生标题栏明暗同步（自包含，不依赖 nova-forge）──────────
def _sync_title_bar(dark: bool) -> None:
    """暗色主题时把系统原生标题栏一并变暗（DWM immersive dark mode）。

    Qt 的 ApplicationWindow 用系统标题栏，其颜色不受 QML 的 NovaTheme 控制；
    这里按 QML 侧 darkChromeChanged 信号同步。非 Windows 平台静默 no-op。
    """
    import ctypes
    import sys

    if sys.platform != "win32":
        return
    try:
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32
        ]
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
        value = ctypes.c_int(1 if dark else 0)
        for window in QGuiApplication.topLevelWindows():
            try:
                hwnd = int(window.winId())
            except Exception:
                continue
            if not hwnd:
                continue
            # 属性 20 = Win10 2004+ / Win11；失败回退属性 19 = Win10 1809~1909
            res = dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd), 20, ctypes.byref(value), ctypes.sizeof(value)
            )
            if res != 0:
                dwmapi.DwmSetWindowAttribute(
                    ctypes.c_void_p(hwnd), 19, ctypes.byref(value), ctypes.sizeof(value)
                )
    except Exception:
        pass  # 无 DWM / 句柄未就绪都不影响应用主流程
'''


def _bootstrap(name: str, pkg: str, kind: Kind) -> str:
    return f'''# src/{pkg}/main.py
# {name} 启动器：初始化 pyside-nova QML 导入路径并加载 Main.qml
"""启动 {kind.zh}：由 app.py 入口调用（python -m {pkg}.app）"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from pyside_nova import init_nova

QML_DIR = Path(__file__).resolve().parent / "qml"
# {kind.shell} 的专属应用图标（随产物落盘，独立工程不依赖 nova-forge 资源）
APP_ICON = Path(__file__).resolve().parent / "assets" / "{kind.icon}"
{_WINDOW_CHROME_HELPER}

def main() -> int:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("{pkg}")
    app.setApplicationDisplayName("{name}")
    app.setWindowIcon(QIcon(str(APP_ICON)))

    engine = QQmlApplicationEngine()
    init_nova(engine)
    engine.load(str(QML_DIR / "Main.qml"))
    roots = engine.rootObjects()
    if not roots:
        print("QML 加载失败：请检查 pyside-nova 版本与 qml/ 目录", file=sys.stderr)
        return 1
    window = roots[0]  # 立即持引用：延迟回调里再取会被降级成 QWindow 包装
    # 原生标题栏随 QML 主题同步：初始暗色 + 每次明暗切换
    try:
        window.darkChromeChanged.connect(_sync_title_bar)
        QTimer.singleShot(10, lambda: _sync_title_bar(True))
    except Exception:
        pass  # 非 Windows / 无信号时不影响主流程
    # 一键自检：离屏跑 1.2 s 后自动退出，供 nova-forge prescript --verify-run 调用
    if os.environ.get("NOVA_PRESCRIPT_SMOKE") == "1":
        QTimer.singleShot(1200, app.quit)
    return app.exec()
'''


_LEGACY_README_TREE = """.
├── pyproject.toml
├── prescript.json
├── src/
└── tests/"""


def _render_tree(files: list[str]) -> str:
    """由实际文件清单生成 README 结构树（单行缩进，避免分支符号歧义）。"""
    lines = ["."]
    for rel in sorted(set(files)):
        lines.append(f"├── {rel}")
    return "\n".join(lines)


def _readme(name: str, pkg: str, kind: Kind, all_files: list[str] | None = None) -> str:
    focus = "\n".join(f"- {x}" for x in kind.focus)
    gates = "\n".join(f"| {t} | {d} |" for t, d in kind.gates)
    metrics = "\n".join(f"| {k} | {v} |" for k, v in kind.metrics)
    deliver = "\n".join(f"- **{k}** · {d}" for k, d in kind.deliverables)
    tree = _render_tree(all_files) if all_files else _LEGACY_README_TREE
    entry_rel = f"src/{pkg}/app.py"
    # T19：直接运行说明必须与清单同源 —— 用户取消了 app.py 就不该教他运行它。
    direct_run = (
        f"\n在 IDE 里也可直接运行 `{entry_rel}`（入口自带双模式导入，无需 `-m`）：\n"
        f"\n```bash\npython {entry_rel}\n```\n"
        if all_files is None or entry_rel in all_files else ""
    )
    return f"""# {name}

> {kind.tagline}

**配方 {kind.recipe} · {kind.zh}（{kind.en}）· 壳 `{kind.shell}` · API 契约 {API_VERSION}**

{kind.pitch}

由 `nova-forge prescript --kind {kind.code}` 一键孵化：外壳是 pyside-nova 的
`NovaIncubator`（七槽孵化工作台），舞台是 `{kind.shell}`
（Prescient Layout Shell）。布局职责全在壳里，业务语义全在本工程。

## 快速开始

```bash
pip install -e .
python -m {pkg}.app
```
{direct_run}
或安装后直接运行命令行入口：

```bash
{pkg.replace('_', '-')}
```

## 舞台能力

{focus}

## 三重校验

| 校验 | 口径 |
|---|---|
{gates}

生成器在孵化时已跑过一遍静态校验（文件完整性 / Python 语法 / QML 结构 / 清单一致性）。

## 性能承诺

| 指标 | 目标 |
|---|---|
{metrics}

## 交付五件套

{deliver}

## 结构

```
{tree}
```

## 治理边界

- 封版必须人工点击确认闸门（`overlaySlot`），脚本不自动签发证书。
- 舞台所有交互为本地状态机，不联网、不隐式写盘。
- 生成物可自由改造；改动舞台不影响 `{kind.shell}` 的冻结契约。

---
Generated by **nova-forge prescript** · 配方 {kind.recipe} · {kind.zh}
"""


def _manifest(name: str, pkg: str, kind: Kind, forge_version: str,
              all_files: list[str] | None = None) -> str:
    data = {
        "schema": "nova.prescript/v1",
        "generator": {"tool": "nova-forge", "command": "prescript", "version": forge_version},
        "app": {"name": name, "package": pkg, "entry": f"{pkg}.app:main"},
        "prescript": {
            "recipe": kind.recipe,
            "kind": kind.code,
            "name_zh": kind.zh,
            "name_en": kind.en,
            "tagline": kind.tagline,
            "role": kind.role,
            "shell": kind.shell,
        },
        "contract": {"api_version": API_VERSION, "nova_floor": NOVA_FLOOR,
                     "incubator_slots": ["global", "recipe", "stage", "validate",
                                         "pipeline", "certificate", "overlay"]},
        "gates": [{"name": t, "rule": d} for t, d in kind.gates],
        "metrics": [{"name": k, "target": v} for k, v in kind.metrics],
        "deliverables": [{"name": k, "detail": d} for k, d in kind.deliverables],
        "files": sorted(set(all_files)) if all_files else [
            "pyproject.toml", "README.md", "prescript.json",
            f"src/{pkg}/app.py", f"src/{pkg}/main.py", f"src/{pkg}/qml/Main.qml",
            f"src/{pkg}/qml/Stage.qml", f"src/{pkg}/assets/{kind.icon}",
            "tests/test_smoke.py"],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _test(pkg: str) -> str:
    return f'''"""孵化产物自检：清单可解析、入口可导入、QML 结构完整。"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_parses() -> None:
    data = json.loads((ROOT / "prescript.json").read_text(encoding="utf-8"))
    assert data["schema"] == "nova.prescript/v1"
    assert data["prescript"]["shell"].startswith("Nova")


def test_package_importable() -> None:
    import importlib

    module = importlib.import_module("{pkg}")
    assert module.__prescript__
    assert module.__shell__


def test_qml_present() -> None:
    qml = ROOT / "src" / "{pkg}" / "qml"
    for name in ("Main.qml", "Stage.qml"):
        text = (qml / name).read_text(encoding="utf-8")
        assert text.count("{{") == text.count("}}")
        assert "import Nova." in text


def test_app_icon_present() -> None:
    """每个孵化产物自带专属应用图标，且与配方代号一致。"""
    icons = sorted((ROOT / "src" / "{pkg}" / "assets").glob("app-*.svg"))
    assert len(icons) == 1
    assert icons[0].read_text(encoding="utf-8").startswith("<?xml")


def test_title_bar_sync_wired() -> None:
    """暗色主题下原生标题栏必须同步：QML 信号 + main.py 侧 DWM helper 双端齐备。"""
    main = (ROOT / "src" / "{pkg}" / "qml" / "Main.qml").read_text(encoding="utf-8")
    app = (ROOT / "src" / "{pkg}" / "main.py").read_text(encoding="utf-8")
    assert "signal darkChromeChanged" in main
    assert "_sync_title_bar" in app
    assert "setWindowIcon" in app


def test_entry_layout() -> None:
    """T17/T19：app.py 双模式薄入口、main.py 启动器，不残留 __main__.py。"""
    pkg_dir = ROOT / "src" / "{pkg}"
    assert not (pkg_dir / "__main__.py").exists()
    entry = (pkg_dir / "app.py").read_text(encoding="utf-8")
    assert "from .main import main" in entry   # 包内 / console entry
    assert "from main import main" in entry    # T19：直接 python app.py
    assert "__package__" in entry
    launcher = (pkg_dir / "main.py").read_text(encoding="utf-8")
    assert "def main() -> int:" in launcher
    assert "setWindowIcon" in launcher


def test_pyside6_available() -> None:
    pytest.importorskip("PySide6")
'''
