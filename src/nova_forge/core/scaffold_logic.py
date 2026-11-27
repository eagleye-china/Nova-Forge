# src/nova_forge/core/scaffold_logic.py
# 创建时间：星期五 2026-11-27 10:30
"""scaffold 的纯逻辑层：项目骨架文件清单单一事实源（无 I/O、无 input）。

``scaffold_file_plan`` 返回「相对路径 → 文件内容」字典，与 prescript 的
``Project.files`` 同构，因此 CLI scaffold 与 prescript 叠加共用同一份清单，
避免两处模板漂移。目录条目以空字符串表示（由落盘层 mkdir）。
"""
from __future__ import annotations

import datetime
from pathlib import Path

from ..templates import (
    CB,
    CHANGELOG_TMPL,
    DEFAULT_AUTHOR_EMAIL,
    DEFAULT_DEPS,
    DEFAULT_DESC_EN,
    DEFAULT_DESC_ZH,
    DEFAULT_GITHUB_USER,
    DEFAULT_REAL_NAME,
    DEFAULT_VERSION,
    GITIGNORE_TMPL,
    HOW_TO_PUBLISH_TMPL,
    INIT_PY_TMPL,
    LICENSE_TMPL,
    MOBILE_MAIN_PY_TMPL,
    MOBILE_MAIN_QML_TMPL,
    PYPROJECT_TMPL,
    README_EN_TMPL,
    README_ZH_TMPL,
    WORKFLOW_TMPL,
)

# 目录条目哨兵：与合法的空文件（如 project_structure.txt = ""）严格区分
DIR_SENTINEL = None


# 公共工程文件（桌面端 / 移动端共用）——单一事实源
COMMON_FILES: tuple[tuple[str, str], ...] = (
    ("pyproject.toml", PYPROJECT_TMPL),
    ("LICENSE", LICENSE_TMPL),
    (".gitignore", GITIGNORE_TMPL),
    ("README.md", README_EN_TMPL),
    ("README_zh.md", README_ZH_TMPL),
    ("CHANGELOG.md", CHANGELOG_TMPL),
    ("HOW_TO_PUBLISH.md", HOW_TO_PUBLISH_TMPL),
    (".github/workflows/publish.yml", WORKFLOW_TMPL),
)

# 桌面端专属：入口 py + qml + 三个空目录
DESKTOP_FILES: tuple[tuple[str, str], ...] = (
    ("src/$MODULE_NAME/__init__.py", INIT_PY_TMPL),
    ("src/$MODULE_NAME/main.py", '"""Desktop entry point."""\nimport sys\n# 桌面端代码...'),
    ("src/$MODULE_NAME/qml/main.qml", "// Desktop QML template..."),
    ("src/$MODULE_NAME/ui", ""),
    ("src/$MODULE_NAME/utils", ""),
    ("tests", ""),
)

# 移动端专属
MOBILE_FILES: tuple[tuple[str, str], ...] = (
    ("src/$MODULE_NAME/__init__.py", INIT_PY_TMPL),
    ("src/$MODULE_NAME/main.py", MOBILE_MAIN_PY_TMPL),
    ("src/$MODULE_NAME/qml/main.qml", MOBILE_MAIN_QML_TMPL),
)


def module_name_from_path(target_root: str | Path) -> str:
    """从项目绝对路径末段派生合法 Python 模块名。"""
    name = Path(target_root).resolve().name
    return name.lower().replace("-", "_").replace(" ", "_")


def build_context(
    target_root: str | Path,
    *,
    project_name: str | None = None,
    repo_name: str | None = None,
    github_user: str | None = None,
    real_name: str | None = None,
    desc_en: str | None = None,
    desc_zh: str | None = None,
    is_mobile: bool = False,
) -> dict[str, object]:
    """按路径末段智能派生全部模板变量，调用方可覆盖任意项。"""
    root = Path(target_root).resolve()
    folder_name = root.name
    module_name = module_name_from_path(root)
    default_project_name = folder_name.lower().replace(" ", "-").replace("_", "-")
    default_repo_name = folder_name.replace(" ", "")
    if is_mobile:
        default_en = "A stunning, GPU-accelerated mobile application for PySide6."
        default_zh = "基于 PySide6 和 QML 打造的炫酷移动端应用框架。"
    else:
        default_en = DEFAULT_DESC_EN
        default_zh = DEFAULT_DESC_ZH
    now = datetime.datetime.now()
    return {
        "PROJECT_NAME": project_name or default_project_name,
        "REPO_NAME": repo_name or default_repo_name,
        "GITHUB_USER": github_user or DEFAULT_GITHUB_USER,
        "REAL_NAME": real_name or DEFAULT_REAL_NAME,
        "VERSION": DEFAULT_VERSION,
        "AUTHOR_EMAIL": DEFAULT_AUTHOR_EMAIL,
        "DESC_EN": desc_en or default_en,
        "DESC_ZH": desc_zh or default_zh,
        "YEAR": now.year,
        "MONTH": now.strftime("%m"),
        "DAY": now.strftime("%d"),
        "MODULE_NAME": module_name,
        "DEPS": DEFAULT_DEPS,
        "CB": CB,
    }


def resolve_templates(
    files: tuple[tuple[str, str], ...], context: dict[str, object]
) -> dict[str, str | None]:
    """把 (路径模板, 内容模板) 列表渲染成「相对路径 → 内容」。"""
    from string import Template

    out: dict[str, str | None] = {}
    for rel, text in files:
        out[Template(rel).safe_substitute(context)] = (
            DIR_SENTINEL if text == "" else Template(text).safe_substitute(context)
        )
    return out


def scaffold_file_plan(
    target_root: str | Path,
    *,
    is_mobile: bool = False,
    include_entry_qml: bool = True,
    include_entry_py: bool = True,
    include_project_structure: bool = True,
    **overrides: str | None,
) -> dict[str, str | None]:
    """生成完整工程骨架清单（纯内存，不落盘）。

    Args:
        target_root: 项目绝对路径（末段即模块名来源）。
        is_mobile: 移动端模板（默认桌面端）。
        include_entry_qml: 是否含 ``qml/main.qml``。prescript 叠加时须传 False——
            其 ``qml/Main.qml`` 在 Windows 大小写不敏感文件系统上会与之冲突。
        include_entry_py: 是否含 ``main.py`` 占位模板。prescript 的
            ``main.py`` 是真正的启动器、``app.py`` 是薄入口，叠加时须关掉，
            避免用占位模板覆盖启动器（T17 改名后同名，风险更高）。
        include_project_structure: 是否含空的 ``project_structure.txt``。
        **overrides: 覆盖 build_context 的任意模板变量（如 project_name）。

    Returns:
        相对路径 → 内容；``DIR_SENTINEL``（None）表示目录，空串是合法空文件。
    """
    ctx = build_context(target_root, is_mobile=is_mobile, **overrides)
    files = resolve_templates(COMMON_FILES, ctx)
    specific = MOBILE_FILES if is_mobile else DESKTOP_FILES
    for rel, text in specific:
        if rel == "src/$MODULE_NAME/main.py" and not include_entry_py:
            continue
        if rel == "src/$MODULE_NAME/qml/main.qml" and not include_entry_qml:
            continue
        rendered = resolve_templates(((rel, text),), ctx)
        files.update(rendered)
    if include_project_structure:
        files.setdefault("project_structure.txt", "")
    return files


# prescript 叠加时排除的同名/冲突文件：
# - pyproject.toml / README.md / .gitignore / src/<pkg>/__init__.py：prescript 自己的产物更完整
# - src/<pkg>/main.py：prescript 的 main.py 是启动器，scaffold 占位模板不得覆盖
# - src/<pkg>/qml/main.qml：Windows 大小写不敏感，与 prescript 的 Main.qml 冲突
# - ui/ / utils/ / tests/：空目录，render_project 会按需建父目录
_PRESCRIPT_EXCLUDE_PREFIXES = (
    "pyproject.toml", "README.md", ".gitignore", "project_structure.txt",
    "src/",
)


def prescript_overlay_plan(
    target_root: str | Path, *, app_name: str | None = None, package: str | None = None,
) -> dict[str, str]:
    """prescript 工程叠加的 scaffold 通用文件清单（纯内存）。


    只补 prescript 11 文件清单里没有的工程治理文件：LICENSE / README_zh.md /
    CHANGELOG.md / HOW_TO_PUBLISH.md / .github/workflows/publish.yml /
    project_structure.txt。同名文件一律由 prescript 版本保留。
    """
    overrides: dict[str, str | None] = {}
    if app_name:
        overrides["project_name"] = app_name.lower().replace(" ", "-").replace("_", "-")
    if package:
        overrides["project_name"] = package.replace("_", "-")
    plan = scaffold_file_plan(target_root, include_entry_py=False,
                              include_entry_qml=False, **overrides)
    overlay: dict[str, str] = {}
    for rel, text in plan.items():
        if rel == "project_structure.txt":
            overlay[rel] = text  # 空文件，prescript 清单未含
            continue
        if rel in _PRESCRIPT_EXCLUDE_PREFIXES or rel.startswith("src/"):
            continue
        if text is DIR_SENTINEL:  # 目录条目不纳入（render_project 按需 mkdir）
            continue
        overlay[rel] = text
    return overlay
