# src/nova_forge/bridge/icons_bridge.py
# 创建时间：星期二 2026-11-24 22:03
"""icons 子命令的 Python↔QML 桥接层（pyside-nova 组件库界面）。

QML 只负责渲染与交互，所有文件系统读写都留在本层；
复用 core/icons_logic.ResourceBuilderWorker 做后台 .qrc 构建。
"""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from ..core.icons_logic import ResourceBuilderWorker

IMAGE_EXTS = frozenset({".svg", ".png", ".jpg", ".jpeg", ".ico"})
NAME_PATTERN = re.compile(r"^\d+-(.+)\.(svg|png|jpg|jpeg|ico)$", re.IGNORECASE)


def detect_project_root(explicit: str | Path | None = None) -> Path:
    """当前项目根：icons 子命令「在哪个项目执行，就扫哪个项目」的基准。

    优先级：显式 --project > 当前工作目录向上找 pyproject.toml > 包所在仓库回落。
    """
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if not candidate.is_dir():
            raise ValueError(f"--project 目录不存在：{candidate}")
        return candidate

    cwd = Path.cwd().resolve()
    for base in (cwd, Path(__file__).resolve()):
        for parent in (base, *base.parents):
            if (parent / "pyproject.toml").is_file():
                return parent
    return cwd


def _package_src_roots(root: Path) -> list[Path]:
    """项目下 ``src/<pkg>`` 候选（按名字排序，稳定）。"""
    src = root / "src"
    if not src.is_dir():
        return []
    return sorted(
        (d for d in src.iterdir() if d.is_dir() and not d.name.startswith(("_", "."))),
        key=lambda d: d.name,
    )


def detect_assets_base(root: Path | None = None) -> Path:
    """素材库：当前项目根下的 assets/（含 icons 等子目录）。

    按「谁真的有图标子目录」来选，避免误命中只有一个 txt 的占位目录。
    """
    root = root or detect_project_root()
    candidate = root / "assets"
    if candidate.is_dir() and any(
        d.is_dir() and not d.name.startswith(("_", ".")) for d in candidate.iterdir()
    ):
        return candidate
    return root / "assets"


def detect_resources_base(root: Path | None = None) -> Path:
    """资源库：当前项目下真正参与打包的 ``src/<pkg>/resources``。

    qrc_builder 把 .qrc 写到目标目录同级，故必须指向当前项目的包内 resources，
    而不是固定写死 nova_forge —— 这样在 pyside-nova 目录执行 icons 时，
    扫描的就是 pyside-nova 的 resources/icons（10 枚应用图标所在处）。
    """
    root = root or detect_project_root()
    for pkg in _package_src_roots(root):
        candidate = pkg / "resources"
        if candidate.is_dir() and (
            (candidate / "resources.qrc").is_file() or (candidate / "icons").is_dir()
        ):
            return candidate
    legacy = root / "resources"
    if legacy.is_dir():
        return legacy
    return root / "resources"


def _subdirs(base: Path) -> list[str]:
    if not base.is_dir():
        return []
    return sorted(
        d.name
        for d in base.iterdir()
        if d.is_dir() and not d.name.startswith(("_", "."))
    )


def _icons(base: Path, folder: str, keyword: str) -> list[dict]:
    """返回 [{name, path, url, tip}]，供 QML GridView 消费。"""
    if not folder:
        return []
    target = base / folder
    if not target.is_dir():
        return []
    files = sorted(
        (p for p in target.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
        key=lambda x: x.name,
    )
    kw = keyword.strip().lower()
    out: list[dict] = []
    for p in files:
        display = p.name
        m = NAME_PATTERN.match(display)
        if m:
            display = m.group(1) + p.suffix.lower()
        if kw and kw not in display.lower():
            continue
        out.append(
            {
                "name": display,
                "path": str(p),
                "url": QUrl.fromLocalFile(str(p)).toString(),
                "tip": p.name,
            }
        )
    return out


class IconsBridge(QObject):
    """暴露给 QML 的 ``bridge`` 上下文对象。"""

    foldersChanged = Signal()
    iconsChanged = Signal()
    stateChanged = Signal()
    toast = Signal(str, str)  # (kind: positive|negative|info|warning, message)
    confirmDelete = Signal(str, str)  # (绝对路径, 显示名)
    buildStateChanged = Signal(bool, str)  # (构建中, 状态文案)

    def __init__(self, parent=None, project_root: str | Path | None = None):
        super().__init__(parent)
        self.project_root = detect_project_root(project_root)
        self.assets_base = detect_assets_base(self.project_root)
        self.resources_base = detect_resources_base(self.project_root)

        self._asset_folders: list[str] = []
        self._resource_folders: list[str] = []
        self._asset_icons: list[dict] = []
        self._resource_icons: list[dict] = []
        self._asset_folder = ""
        self._resource_folder = ""
        self._asset_filter = ""
        self._resource_filter = ""
        self._status = "就绪"
        self._busy = False
        self._worker = None

        self.refresh()

    # ── QML 只读属性 ──────────────────────────────────────────
    @Property("QVariantList", notify=foldersChanged)
    def assetFolders(self):
        return self._asset_folders

    @Property("QVariantList", notify=foldersChanged)
    def resourceFolders(self):
        return self._resource_folders

    @Property("QVariantList", notify=iconsChanged)
    def assetIcons(self):
        return self._asset_icons

    @Property("QVariantList", notify=iconsChanged)
    def resourceIcons(self):
        return self._resource_icons

    @Property(str, notify=stateChanged)
    def currentAssetFolder(self):
        return self._asset_folder

    @Property(str, notify=stateChanged)
    def currentResourceFolder(self):
        return self._resource_folder

    @Property(str, notify=stateChanged)
    def statusText(self):
        return self._status

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    # ── QtWidgets 版遗留的公开属性（便于无头测试 / 复用） ──────
    @property
    def current_asset_folder(self) -> str:
        return self._asset_folder

    @property
    def current_resource_folder(self) -> str:
        return self._resource_folder

    # ── 内部 ──────────────────────────────────────────────────
    def _set_status(self, text: str) -> None:
        self._status = text
        self.stateChanged.emit()

    def _reload_asset_icons(self) -> None:
        self._asset_icons = _icons(self.assets_base, self._asset_folder, self._asset_filter)
        self.iconsChanged.emit()

    def _reload_resource_icons(self) -> None:
        self._resource_icons = _icons(
            self.resources_base, self._resource_folder, self._resource_filter
        )
        self.iconsChanged.emit()

    # ── QML Slots ─────────────────────────────────────────────
    @Slot(bool)
    def setDarkTitleBar(self, dark: bool) -> None:
        """QML 主题变化时同步 Windows 原生标题栏明暗。"""
        from ..utils.window_utils import apply_dark_title_bars

        apply_dark_title_bars(bool(dark))

    @Slot()
    def refresh(self) -> None:
        """重扫两侧目录；保留当前选中项，目录消失时才回退到首个。"""
        self._asset_folders = _subdirs(self.assets_base)
        self._resource_folders = _subdirs(self.resources_base)

        if self._asset_folder not in self._asset_folders:
            self._asset_folder = (
                "icons" if "icons" in self._asset_folders
                else (self._asset_folders[0] if self._asset_folders else "")
            )
        if self._resource_folder not in self._resource_folders:
            want = self._asset_folder if self._asset_folder in self._resource_folders else ""
            self._resource_folder = want or (
                self._resource_folders[0] if self._resource_folders else ""
            )

        self._reload_asset_icons()
        self._reload_resource_icons()
        self._set_status("就绪")
        self.foldersChanged.emit()

    @Slot(str)
    def selectAssetFolder(self, folder: str) -> None:
        folder = folder or ""
        if folder == self._asset_folder:
            return
        self._asset_folder = folder
        self._asset_filter = ""
        self._reload_asset_icons()
        self._set_status(f"资产目录：{folder or '—'}")
        self.stateChanged.emit()

    @Slot(str)
    def selectResourceFolder(self, folder: str) -> None:
        folder = folder or ""
        if folder == self._resource_folder:
            return
        self._resource_folder = folder
        self._resource_filter = ""
        self._reload_resource_icons()
        self._set_status(f"资源目录：{folder or '—'}")
        self.stateChanged.emit()

    @Slot(str)
    def setAssetFilter(self, text: str) -> None:
        text = text or ""
        if text == self._asset_filter:
            return
        self._asset_filter = text
        self._reload_asset_icons()

    @Slot(str)
    def setResourceFilter(self, text: str) -> None:
        text = text or ""
        if text == self._resource_filter:
            return
        self._resource_filter = text
        self._reload_resource_icons()

    @Slot(str)
    def publishIcon(self, path: str) -> None:
        """双击资产图标 → 复制到同名资源目录。"""
        src = Path(path)
        if not src.is_file():
            self.toast.emit("negative", f"源文件不存在：{src.name}")
            return
        if not self._asset_folder:
            self.toast.emit("warning", "请先选择资产目录")
            return
        dest_dir = self.resources_base / self._asset_folder
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            import shutil

            shutil.copy2(src, dest_dir / src.name)
        except OSError as exc:
            self.toast.emit("negative", f"复制失败：{exc}")
            return
        self.toast.emit("positive", f"已发布 {src.name} → {self._asset_folder}/")
        self.refresh()

    @Slot(str, str)
    def requestDelete(self, path: str, name: str) -> None:
        """右键资源图标 → 请求 QML 弹 NovaDialog 确认。"""
        self.confirmDelete.emit(path, name)

    @Slot(str)
    def deleteResource(self, path: str) -> None:
        target = Path(path)
        try:
            target.unlink()
        except OSError as exc:
            self.toast.emit("negative", f"删除失败：{exc}")
            return
        self.toast.emit("positive", f"已删除 {target.name}")
        self._reload_resource_icons()

    @Slot()
    def buildQrc(self) -> None:
        if self._busy:
            return
        if not self._resource_folder:
            self.toast.emit("warning", "请先选择资源目录")
            return
        target = self.resources_base / self._resource_folder
        if not target.is_dir():
            self.toast.emit("negative", f"资源目录不存在：{target}")
            return

        self._busy = True
        self._set_status(f"正在更新 .qrc：{self._resource_folder} …")
        self.buildStateChanged.emit(True, self._status)

        self._worker = ResourceBuilderWorker(target_dir=str(target))
        self._worker.log_signal.connect(lambda msg: self._set_status(str(msg).strip() or self._status))
        self._worker.finished_signal.connect(self.onBuildFinished)
        self._worker.start()

    @Slot(bool, str)
    def onBuildFinished(self, success: bool, msg: str) -> None:
        self._busy = False
        self._set_status(msg)
        self.buildStateChanged.emit(False, msg)
        self.toast.emit("positive" if success else "negative", msg)
