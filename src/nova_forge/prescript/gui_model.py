# src/nova_forge/prescript/gui_model.py
# 创建时间：星期四 2026-11-26 19:44
"""prescript --gui 的纯逻辑层：配置态 / 九配方单源 / 三重校验 / 落盘闸门。

本模块**不导入 PySide6**，便于无头回归测试；Qt 桥接在 ``bridge/prescript_bridge.py``。
唯一事实源：``catalog.KINDS``（九配方）、``render.plan_project`` / ``render_project``。

治理铁律（对齐 pyside-nova ``NovaIncubator`` 契约）：
``hatch()`` 必须显式 ``confirmed=True`` 才落盘；壳的 ``freezeRequested()`` 只 emit
意图，绝不自动封版、绝不自动执行。人工确认闸门在 QML 的 ``overlaySlot``。
"""
from __future__ import annotations

import json
import py_compile
import re
from dataclasses import dataclass
from pathlib import Path

from .. import __version__ as _forge_version
from .catalog import KIND_CODES, KINDS, get_kind
from .render import API_VERSION, normalise_package, plan_project, render_project


@dataclass
class GUIConfig:
    """GUI 配置态：七个可编辑字段，与 QML 双向绑定。"""

    kind: str = "chat"
    path: str = ""
    name: str = ""
    package: str = ""
    force: bool = False
    dry_run: bool = False
    verify_run: bool = False
    # None = 全选（默认，兼容 CLI / 旧调用）；列表 = 只创建这些相对路径
    selected_files: list[str] | None = None

    @classmethod
    def from_mapping(cls, data: dict) -> GUIConfig:
        """从 QML 传回的 JS 对象构造；只收已知字段，忽略多余键。"""
        raw = data.get("selected_files")
        return cls(
            kind=str(data.get("kind") or "chat"),
            path=str(data.get("path") or ""),
            name=str(data.get("name") or ""),
            package=str(data.get("package") or ""),
            force=bool(data.get("force")),
            dry_run=bool(data.get("dry_run")),
            verify_run=bool(data.get("verify_run")),
            selected_files=list(raw) if isinstance(raw, list) else None,
        )

    def as_mapping(self) -> dict:
        return {
            "kind": self.kind, "path": self.path, "name": self.name,
            "package": self.package, "force": self.force,
            "dry_run": self.dry_run, "verify_run": self.verify_run,
            "selected_files": self.selected_files,
        }


def forge_version() -> str:
    """当前 nova-forge 版本（生成器清单用）。"""
    return _forge_version


def resolve_target(cfg: GUIConfig) -> tuple[Path, str, str]:
    """把「根目录 + 应用名 + 包名」解析成真实工程目录。

    CSA 2026-11-27 拍板：GUI / 浏览框提供的是**孵化根目录**，项目必须在
    根目录之下以包名建独立子目录（如 ``D:/TEST_INCUBATOR/nova_incubator_app/``），
    绝不直接写根目录本身。应用名缺省回落 ``Prescript App``，包名缺省由
    应用名规整而来；返回 ``(工程目录, 应用名, 包名)``。
    """
    name = cfg.name.strip()
    pkg = cfg.package.strip() or normalise_package(name or "prescript_app")
    root = Path(cfg.path.strip()).expanduser().resolve() / pkg
    return root, (name or "Prescript App"), pkg


def kind_rows() -> list[dict]:
    """九类配方全量行：GUI 配方库 / 下拉框 / 证书区共用同一份数据。"""
    return [
        {
            "code": k.code,
            "recipe": k.recipe,
            "zh": k.zh,
            "en": k.en,
            "shell": k.shell,
            "tagline": k.tagline,
            "role": k.role,
            "pitch": k.pitch,
            "hue": k.hue,
            "icon": f"qrc:/icons/{k.icon}",   # 配方库卡片的应用图标（qrc 别名单一事实源）
            "size": list(k.size),
            "minimum": list(k.minimum),
            "metrics": [{"k": a, "v": b} for a, b in k.metrics],
            "gates": [{"k": a, "v": b} for a, b in k.gates],
            "deliverables": [{"k": a, "v": b} for a, b in k.deliverables],
            "focus": list(k.focus),
        }
        for k in KINDS
    ]


def kind_options() -> list[dict]:
    """NovaSelect 的 options：``[{label, value}]``，值即 CLI 的 --kind。"""
    return [
        {"label": f"{k.recipe} · {k.zh}（{k.shell}）", "value": k.code}
        for k in KINDS
    ]


def stage_qml(kind: str) -> str:
    """取某配方的 Stage.qml 全文（与落盘产物同源单字不变）。

    只读 ``stages.STAGES``，不触碰工程目录；未知配方抛 ``ValueError``。
    供 GUI「界面预览」做真 QML 实装渲染（非截图、非 mock）。
    """
    from .stages import STAGES  # 局部导入：stages 体积大，纯逻辑层按需加载

    spec = get_kind(kind)
    return STAGES[spec.code]


# T23 / 坑位 76：生成物含 ``![alt](../screenshots/*.png)`` 相对图片，而
# Text.MarkdownText 以「实例化它的 QML 文件所在目录」为 baseUrl 解析相对路径
# （pyside_nova/qml/Nova/Controls/），与 docs/components/ 不在同一棵树，
# 必然刷 ``Cannot open: .../Nova/screenshots/*.png``。且这些是 1280×800 史料
# 截图，内嵌进 400px 英雄卡的三列表格会撑爆布局。故在视图模型层做显示适配：
# ``text`` 逐字保留生成物（账实同源），``renderText`` 把图片降级为文本占位，
# 不改生成物、不改冻结面、不动库组件。
_IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _display_text(text: str) -> str:
    """紧凑英雄卡显示适配：图片引用 → 文本占位（不加载、不告警、不撑布局）。"""
    return _IMAGE_REF_RE.sub(
        lambda m: f"{m.group(1)}（展示图 · 见仓库）", text)


def component_doc(kind_code: str) -> dict:
    """当前选中应用的组件说明文档（pyside-nova ``docs/components/<shell>.md``）。

    T16：英雄卡 README 按钮展示的就是这批 md——九配方 ``Kind.shell`` 与
    ``docs/components/<shell>.md`` 一一对应，文件名由 catalog 单一事实源推导，
    不另立映射台账。文档是 ``gen_apidocs.py`` 的生成物，本函数只读不改。

    T23：额外返回 ``renderText`` —— 图片引用降级为文本占位的显示适配版；
    ``text`` 仍逐字等于生成物（账实同源），供追溯 / 站点使用；GUI 英雄卡
    绑定前者，避免紧凑卡片加载 1280×800 史料截图。

    目录定位优先级：显式 ``NOVA_COMPONENT_DOCS`` > 已安装的 pyside_nova 包位置
    推导（editable / site-packages 同口径）> mono-repo 工作区同级回落。纯逻辑层
    不 import pyside_nova（规避 PySide6 依赖与坑位 49 的 SIGSEGV），只用
    ``importlib.util.find_spec`` 查位置、不执行模块代码。
    """
    import importlib.util
    import os

    spec = get_kind(kind_code)   # 未知配方抛 ValueError，交由调用方兜底
    name = f"{spec.shell}.md"

    roots: list[Path] = []
    explicit = os.environ.get("NOVA_COMPONENT_DOCS", "").strip()
    if explicit:
        roots.append(Path(explicit))
    try:
        found = importlib.util.find_spec("pyside_nova")
        if found and found.submodule_search_locations:
            pkg = Path(next(iter(found.submodule_search_locations)))
            # .../pyside-nova/src/pyside_nova → .../pyside-nova/docs/components
            roots.append(pkg.parents[1] / "docs" / "components")
    except (ImportError, ValueError):
        pass
    # nova-forge/src/nova_forge/prescript/gui_model.py → <workspace>/pyside-nova
    roots.append(Path(__file__).resolve().parents[4] / "pyside-nova" / "docs" / "components")

    for root in roots:
        path = root / name
        if path.is_file():
            try:
                raw = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            return {
                "found": True,
                "title": name,
                "text": raw,
                "renderText": _display_text(raw),
                "note": "当前选中应用 · pyside-nova docs/components",
                "source": str(path),
            }
    return {"found": False, "title": name, "text": "", "renderText": "",
            "note": "组件文档未安装", "source": ""}


def _check(key: str, label: str, ok: bool, detail: str) -> dict:
    return {"key": key, "label": label, "ok": bool(ok), "detail": detail}


def validate_config(cfg: GUIConfig) -> list[dict]:
    """三重校验（配置态，不落盘）：配置完整性 / 目录合法性 / 契约合规。"""
    try:
        spec = get_kind(cfg.kind)
        kind_ok, kind_detail = True, f"{spec.recipe} · {spec.zh} · {spec.shell}"
    except ValueError:
        spec = None
        kind_ok = False
        kind_detail = f"未知配方 {cfg.kind!r}；可选 {', '.join(KIND_CODES)}"

    raw_path = cfg.path.strip()
    path_ok = bool(raw_path)
    path_detail = raw_path or "未选择孵化根目录"

    # 目录判定针对**工程目录**（根目录 / 包名），根目录本身允许非空
    project_dir = None
    name = cfg.name.strip()
    pkg = ""
    if path_ok:
        project_dir, name, pkg = resolve_target(cfg)
    name_ok = True
    name_detail = name if cfg.name.strip() else f"{name}（默认，可自行填写）"

    occupied = bool(project_dir and project_dir.exists() and any(project_dir.iterdir()))
    if not path_ok:
        dir_ok, dir_detail = False, "孵化根目录为空"
    elif project_dir.exists() and not project_dir.is_dir():
        dir_ok, dir_detail = False, "工程路径是文件，不是目录"
    elif occupied and not cfg.force and not cfg.dry_run:
        dir_ok, dir_detail = False, "工程目录已存在且非空 · 需勾选「覆盖同名文件」"
    else:
        # 根目录允许尚不存在（落盘时 mkdir(parents=True)），只需最近已存在祖先是目录
        probe = project_dir.parent
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        dir_ok = probe.is_dir()
        dir_detail = f"工程目录：{project_dir}" if dir_ok else f"根目录不存在：{project_dir.parent}"

    contract_pkg = pkg or normalise_package(name or "prescript_app")
    pkg_ok = contract_pkg == normalise_package(contract_pkg)
    shell_ok = bool(spec and spec.shell.startswith("Nova"))
    contract_ok = pkg_ok and shell_ok and len(KINDS) == 9
    contract_detail = (
        f"包名 {contract_pkg} · 壳 {spec.shell if spec else '—'} · API {API_VERSION} · 九配方单源"
        if contract_ok else f"包名 {contract_pkg} 或壳契约不合规"
    )

    return [
        _check("config", "配置完整性", kind_ok and path_ok and name_ok,
               f"{kind_detail} / {path_detail} / {name_detail}"),
        _check("directory", "目录合法性", dir_ok, dir_detail),
        _check("contract", "契约合规", contract_ok, contract_detail),
    ]


def _selected_set(cfg: GUIConfig) -> set[str] | None:
    """把配置里的选中路径转成集合；None 表示全选（不过滤）。"""
    return set(cfg.selected_files) if cfg.selected_files is not None else None


def file_choices(cfg: GUIConfig) -> list[dict]:
    """全部「事先可知」的待创建文件（src 布局），带当前勾选态。

    与 ``plan_summary`` 的差别：本函数**始终返回完整清单**（不受勾选过滤），
    供 GUI 组选框逐项列出；``selected`` 字段反映用户是否勾选。体量与路径
    都来自 ``plan_project`` 同一事实源，避免另立台账。
    """
    spec = get_kind(cfg.kind)
    root, name, _pkg = resolve_target(cfg)
    full = plan_project(spec.code, root, name, cfg.package.strip() or None,
                        forge_version())
    selected = _selected_set(cfg)
    return [
        {
            "path": rel,
            "size": len(text.encode("utf-8")),
            "selected": selected is None or rel in selected,
            "exists": (root / rel).exists(),
        }
        for rel, text in full.files.items()
    ]


# 用户最关心的「主要文件」：确认孵化框摘要区逐项列出（相对工程目录）
KEY_FILES: tuple[str, ...] = (
    "pyproject.toml", "README.md", "README_zh.md", "LICENSE", "CHANGELOG.md",
)


def _pyproject_meta(text: str) -> dict:
    """从生成的 pyproject.toml 文本解析摘要（账实同源，不另立台账）。

    TOML 的 ``[project]`` 段是单值行 + authors 行数组，用轻量正则提取即可，
    避免为 GUI 摘要引入 tomllib（>=3.10 才有，且会与写盘内容漂移）。
    """

    def field(key: str) -> str:
        m = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"', text, re.M)
        return m.group(1) if m else ""

    author = re.search(
        r'^\s*authors\s*=\s*\[\s*\{\s*name\s*=\s*"([^"]*)"', text, re.M
    )
    return {
        "distName": field("name"),
        "version": field("version"),
        "description": field("description"),
        "license": field("license"),
        "python": field("requires-python"),
        "author": author.group(1) if author else "",
    }


def plan_summary(cfg: GUIConfig) -> dict:
    """内存预览：不写任何文件，返回将生成的文件清单与体量。

    ``root`` 是**工程目录**（根目录 / 包名），``workspace`` 是用户提供的根目录。
    ``meta`` 从实际生成的 pyproject.toml 解析，``keyFiles`` 是用户最关心的
    主要文件子集；两者都与落盘内容同源，确认框据此展示项目摘要。
    """
    spec = get_kind(cfg.kind)
    root, name, _pkg = resolve_target(cfg)
    project = plan_project(
        spec.code, root, name, cfg.package.strip() or None, forge_version(),
        include_files=_selected_set(cfg),
    )
    rows = [
        {
            "path": rel,
            "size": len(text.encode("utf-8")),
            "exists": (root / rel).exists(),
        }
        for rel, text in project.files.items()
    ]
    # 主要文件清单恒列 5 项（GroupBox 里的 checkbox 组需要「可勾回」）：
    # 与左侧组选框共用 file_choices 全量清单作为单一事实源，取消勾选只把
    # included 置 false，不把该项从列表移除——否则用户再也无法勾回来。
    full_by_path = {c["path"]: c for c in file_choices(cfg)}
    key_files = [
        {
            "path": rel,
            "included": bool(full_by_path.get(rel, {}).get("selected")),
            "size": int(full_by_path.get(rel, {}).get("size", 0)),
        }
        for rel in KEY_FILES
    ]
    return {
        "root": str(root),
        "workspace": str(root.parent),
        "package": project.package,
        "appName": project.app_name,
        "kind": spec.code,
        "recipe": spec.recipe,
        "shell": spec.shell,
        "tagline": spec.tagline,
        "apiVersion": API_VERSION,
        "forgeVersion": forge_version(),
        "fileCount": len(rows),
        "bytes": sum(r["size"] for r in rows),
        "files": rows,
        "meta": _pyproject_meta(project.files.get("pyproject.toml", ""))
        or {
            # 用户取消了 pyproject.toml 时回退到配置态，避免摘要空白
            "distName": project.package.replace("_", "-"),
            "version": "", "description": spec.tagline, "license": "",
            "python": "", "author": "",
        },
        "keyFiles": key_files,
        # T16 英雄卡 README 预览：与将落盘的 README.md **逐字同源**（就是
        # plan_project 组装出的那一份），不另立台账、不读磁盘。用户取消勾选
        # README.md 时 project.files 不含该项 → 空串，QML 据实提示「不会创建」。
        "readme": project.files.get("README.md", ""),
    }


def _static_checks(project) -> list[dict]:
    """落盘后四重静态校验（与 CLI ``_verify`` 同口径）。"""
    root = project.root
    missing = [rel for rel in project.files if not (root / rel).exists()]
    results = [
        _check("files", "工程完整性", not missing,
               f"{len(project.files)} 个文件" if not missing else "缺失 " + ", ".join(missing[:3])),
    ]

    py_files = list((root / "src").rglob("*.py"))
    py_bad: list[str] = []
    for path in py_files:
        try:
            py_compile.compile(str(path), doraise=True, cfile=str(path) + ".pyc")
        except py_compile.PyCompileError as exc:
            py_bad.append(f"{path.name}: {exc.msg.splitlines()[0]}")
    for stray in (root / "src").rglob("*.pyc"):
        stray.unlink(missing_ok=True)
    results.append(_check("python", "Python 语法", not py_bad,
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
    results.append(_check("qml", "QML 结构", not qml_bad,
                          f"{len(qml_files)} 个界面结构完整" if not qml_bad else "; ".join(qml_bad[:2])))

    try:
        manifest = json.loads((root / "prescript.json").read_text(encoding="utf-8"))
        ok = (manifest["prescript"]["kind"] == project.kind.code
              and manifest["prescript"]["shell"] == project.kind.shell)
        detail = f"配方 {manifest['prescript']['recipe']} · 壳 {manifest['prescript']['shell']}"
    except Exception as exc:
        ok, detail = False, f"清单不可解析：{exc}"
    results.append(_check("manifest", "清单一致", ok, detail))
    return results


def _smoke(project) -> tuple[bool, str]:
    """复用 CLI 的离屏实跑实现（延迟导入，避免模块循环）。"""
    from ..command.cmd_prescript import _smoke_run

    return _smoke_run(project)


def hatch(cfg: GUIConfig, *, confirmed: bool = False) -> dict:
    """人工确认闸门之后的唯一落盘入口。

    ``confirmed`` 由 QML ``overlaySlot`` 的确认按钮显式传入；为 False 时
    **绝不写盘**，直接返回拒绝原因。这是「壳只 emit 意图」的第二道防线。
    """
    checks = validate_config(cfg)
    base = {"checks": checks, "written": False, "dryRun": cfg.dry_run}
    if not confirmed:
        return {**base, "ok": False,
                "message": "未通过人工确认闸门 · 未写入任何文件"}
    if not all(c["ok"] for c in checks):
        return {**base, "ok": False,
                "message": "三重校验未通过 · 请按右侧提示修正配置"}
    if cfg.selected_files is not None and not cfg.selected_files:
        return {**base, "ok": False,
                "message": "未勾选任何文件 · 请至少选择一个要创建的文件"}

    spec = get_kind(cfg.kind)
    root, name, _pkg = resolve_target(cfg)
    summary = plan_summary(cfg)

    if cfg.dry_run:
        return {**base, "ok": True, "summary": summary,
                "message": f"预览完成 · {summary['fileCount']} 个文件 / {summary['bytes']:,} B（未落盘）"}

    project = render_project(
        spec.code, root, name, cfg.package.strip() or None, forge_version(),
        force=cfg.force, include_files=_selected_set(cfg),
    )
    # T13：显式调用 scaffold 的非交互落盘入口补齐通用工程骨架（幂等——
    # render_project 已含 overlay，这里全部 skipped；保留调用链以便外部自检/审计）。
    # 按选落盘时跳过：scaffold 不认 include_files，会把用户取消的治理文件写回来；
    # 选中子集里的 overlay 文件已由 render_project 用同源 overlay 写入。
    if _selected_set(cfg) is None:
        from ..command.cmd_scaffolder import scaffold_project

        scaffold_result = scaffold_project(
            root, quiet=True, include_entry_py=False, include_entry_qml=False,
            project_name=project.package.replace("_", "-"),
        )
    else:
        scaffold_result = {"ok": True, "written": [], "skipped": [],
                           "root": str(root), "projectName": project.package}
    results = _static_checks(project)
    if cfg.verify_run:
        ok, detail = _smoke(project)
        results.append(_check("smoke", "离屏实跑", ok, detail))
    ok_all = all(c["ok"] for c in results)
    return {
        **base,
        "ok": ok_all,
        "written": True,
        "checks": results,
        "summary": summary,
        "message": (f"孵化完成 · {sum(c['ok'] for c in results)}/{len(results)} 校验通过 · {root}"
                    if ok_all else "产物已落盘，但存在未通过校验项"),
        "command": f"cd {root} && python -m {project.package}.app",
        "scaffold": {"ok": scaffold_result["ok"],
                     "projectName": scaffold_result["projectName"]},
    }
