# src/nova_forge/bridge/prescript_bridge.py
# 创建时间：星期四 2026-11-26 19:46
"""prescript --gui 的 Python↔QML 桥接层（pyside-nova 组件库界面）。

QML 只负责渲染与交互；九配方、三重校验、目录判定与**全部文件写入**都留在
Python 层（``prescript/gui_model.py``），便于无头回归测试。

治理铁律：``hatch()`` 只有收到 QML 人工确认闸门传入的 ``confirmed=True``
才落盘。``NovaIncubator.freezeRequested()`` 只 emit 意图，本层与壳都不自动执行。
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtWidgets import QApplication, QFileDialog

from ..prescript import gui_model


class PrescriptBridge(QObject):
    """暴露给 QML 的 ``bridge`` 上下文对象。"""

    stateChanged = Signal()
    planReady = Signal()
    checksChanged = Signal()
    busyChanged = Signal()   # 同时作为 busy 属性的 NOTIFY，须无参
    toast = Signal(str, str)                 # (kind: positive|negative|info|warning, message)
    hatchFinished = Signal(bool, str)        # (ok, message)
    gateOpened = Signal()                    # 只通知 QML 打开确认闸门，不落盘

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cfg = gui_model.GUIConfig()
        # path 是**孵化根目录**：工程会落在 <根目录>/<包名>/ 下，不直接写根目录
        self._cfg.path = str(Path.cwd())
        self._cfg.name = "Nova Incubator App"
        self._kinds = gui_model.kind_rows()
        self._options = gui_model.kind_options()
        self._summary: dict = {}
        self._file_choices: list[dict] = []
        self._checks: list[dict] = []
        self._busy = False
        self._status = "就绪 · 选配方 / 目标目录 / 应用名，然后请求孵化"
        self._written = False
        self._command = ""
        self._refresh()
        self._preview_silent()

    # ── 只读数据 ───────────────────────────────────────────────
    @Property("QVariantList", notify=stateChanged)
    def kinds(self):
        return self._kinds

    @Property("QVariantList", notify=stateChanged)
    def kindOptions(self):
        return self._options

    @Property("QVariantList", notify=checksChanged)
    def checks(self):
        return self._checks

    @Property("QVariantMap", notify=planReady)
    def summary(self):
        return self._summary

    @Property("QVariantList", notify=planReady)
    def fileChoices(self):
        """全部待创建文件（src 布局预知清单）+ 当前勾选态，供 GUI 组选框。"""
        return self._file_choices

    @Property(str, notify=planReady)
    def readmeText(self):
        """将落盘的 README.md 全文（组件文档缺失时的回退内容）。

        单一事实源 = ``plan_summary()["readme"]`` = ``plan_project()`` 组装的
        落盘内容；配置 / 勾选一变，``planReady`` 即刷新。未勾选 README.md
        时返回空串，绝不展示一份「其实不会创建」的文档。
        """
        return self._summary.get("readme", "")

    @Property("QVariantMap", notify=planReady)
    def readmeDoc(self):
        """英雄卡 README 按钮内容：当前选中应用的说明文档。

        优先取 pyside-nova ``docs/components/<shell>.md``（CSA 2026-11-27
        指定，九配方与文档一一对应）；该批生成物未随 wheel 发布时回退到
        ``readmeText``（将落盘的 README.md），保证按钮永远有内容可看。

        T23：``text`` 是生成物逐字原文，``renderText`` 是紧凑卡片的显示适配版
        （图片引用降级为文本占位，坑位 76）；QML 英雄卡绑定 ``renderText``。
        """
        try:
            doc = gui_model.component_doc(self._cfg.kind)
        except ValueError:
            doc = {"found": False, "title": "README.md", "text": "",
                   "renderText": "", "note": "未知配方", "source": ""}
        if doc["found"]:
            # 防御 mock / 旧版返回值：缺 renderText 时退回逐字原文
            doc.setdefault("renderText", doc.get("text", ""))
            return doc
        text = self._summary.get("readme", "")
        return {
            "found": bool(text),
            "title": "README.md",
            "text": text,
            "renderText": text,
            "note": "将落盘产物 README.md · 逐字同源（组件文档未安装）"
                    if text else "README.md 未勾选 —— 当前配置不会创建该文件",
            "source": "",
        }

    @Property(str, notify=stateChanged)
    def statusText(self):
        return self._status

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=stateChanged)
    def written(self):
        return self._written

    @Property(str, notify=stateChanged)
    def command(self):
        return self._command

    @Property(str, notify=stateChanged)
    def apiVersion(self):
        return gui_model.API_VERSION

    @Property(str, notify=stateChanged)
    def forgeVersion(self):
        return gui_model.forge_version()

    # ── 配置态（QML 只读 + Slot 写回，受控组件不发隐式写入）─────
    @Property(str, notify=stateChanged)
    def kind(self):
        return self._cfg.kind

    @Property(str, notify=stateChanged)
    def path(self):
        return self._cfg.path

    @Property(str, notify=stateChanged)
    def name(self):
        return self._cfg.name

    @Property(str, notify=stateChanged)
    def package(self):
        return self._cfg.package

    @Property(bool, notify=stateChanged)
    def force(self):
        return self._cfg.force

    @Property(bool, notify=stateChanged)
    def dryRun(self):
        return self._cfg.dry_run

    @Property(bool, notify=stateChanged)
    def verifyRun(self):
        return self._cfg.verify_run

    # ── 内部 ──────────────────────────────────────────────────
    def _set_status(self, text: str) -> None:
        self._status = text
        self.stateChanged.emit()

    def _set_busy(self, value: bool) -> None:
        self._busy = value
        self.busyChanged.emit()

    def _refresh(self) -> None:
        self._checks = gui_model.validate_config(self._cfg)
        self.checksChanged.emit()
        self.stateChanged.emit()

    def _update(self, **fields) -> None:
        # 账实相符：written 描述的是「当前配置」的落盘状态，配置一变即失效。
        # 修复前 _written 是粘性会话旗标——孵化成功后改配方/目录，chip 仍亮
        # 「已落盘」绿灯，与文件清单「预览 · 未落盘」自相矛盾（2026-11-27 CSA 实报）。
        changed = {k: v for k, v in fields.items() if getattr(self._cfg, k) != v}
        if not changed:
            return
        for key, value in changed.items():
            setattr(self._cfg, key, value)
        if self._written:
            self._written = False
            self._command = ""
        self._refresh()
        self._preview_silent()

    def _preview_silent(self) -> None:
        """配置变化后刷新内存预览（不落盘、不弹提示）。"""
        try:
            self._summary = gui_model.plan_summary(self._cfg)
            self._file_choices = gui_model.file_choices(self._cfg)
        except (ValueError, OSError):
            self._summary = {}
            self._file_choices = []
        self.planReady.emit()

    # ── QML Slots ─────────────────────────────────────────────
    @Slot(bool)
    def setDarkTitleBar(self, dark: bool) -> None:
        """QML 主题变化时同步 Windows 原生标题栏明暗（暗色界面不再配白标题栏）。

        非 Windows 平台静默 no-op；窗口句柄创建有延迟，内部走 10 ms 定时应用。
        """
        from ..utils.window_utils import apply_dark_title_bars

        apply_dark_title_bars(bool(dark))

    @Slot(str)
    def setKind(self, value: str) -> None:
        # 清单里的源码路径 / 图标名随配方变化，旧勾选不再对应任何文件 → 重置全选
        self._update(kind=(value or "chat").strip().lower(), selected_files=None)

    @Slot(str)
    def setPath(self, value: str) -> None:
        self._update(path=value or "")

    @Slot(str)
    def setName(self, value: str) -> None:
        self._update(name=value or "", selected_files=None)

    @Slot(str)
    def setPackage(self, value: str) -> None:
        self._update(package=value or "", selected_files=None)

    @Slot(bool)
    def setForce(self, value: bool) -> None:
        self._update(force=bool(value))

    @Slot(bool)
    def setDryRun(self, value: bool) -> None:
        self._update(dry_run=bool(value))

    @Slot(bool)
    def setVerifyRun(self, value: bool) -> None:
        self._update(verify_run=bool(value))

    @Slot(str, bool)
    def setFileSelected(self, path: str, selected: bool) -> None:
        """组选框单项勾选；全选时回落到 None（默认语义），便于下游兼容。"""
        rel = (path or "").strip()
        if not rel:
            return
        current = self._cfg.selected_files
        if current is None:
            current = [c["path"] for c in self._file_choices if c["selected"]]
        picked = set(current)
        if selected:
            picked.add(rel)
        else:
            picked.discard(rel)
        if len(picked) == len(self._file_choices):
            self._update(selected_files=None)
        else:
            self._update(selected_files=sorted(picked))

    @Slot(bool)
    def selectAllFiles(self, selected: bool) -> None:
        """全选 / 全不选；QML 的「全选」「清空」按钮走这里。"""
        self._update(selected_files=None if selected else [])

    @Slot()
    def pickDirectory(self) -> None:
        """QtWidgets 原生目录选择（QApplication 已由命令层创建）。"""
        app = QApplication.instance()
        if app is None:
            self.toast.emit("warning", "当前无 GUI 应用实例，无法打开目录选择")
            return
        start = self._cfg.path or str(Path.cwd())
        chosen = QFileDialog.getExistingDirectory(
            None, "选择孵化根目录（项目将在其下以包名创建）", start,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if chosen:
            self.setPath(chosen)
            self.toast.emit("info", f"目标目录：{chosen}")

    @Slot()
    def preview(self) -> None:
        """刷新预览；只算内存快照，不写盘。"""
        self._preview_silent()
        if self._summary:
            self.toast.emit("info", f"预览 {self._summary['fileCount']} 个文件 · 未落盘")
            self._set_status("预览已刷新 · 尚未落盘（需人工确认）")
        else:
            self.toast.emit("warning", "配置不完整，无法生成预览")

    @Slot()
    def requestHatch(self) -> None:
        """壳的冻结意图落到本层：只打开人工确认闸门，绝不落盘。"""
        checks = gui_model.validate_config(self._cfg)
        if not all(c["ok"] for c in checks):
            self.toast.emit("warning", "三重校验未通过 · 请按右栏提示修正配置")
            self._set_status("配置未就绪 · 确认闸门未打开")
            return
        self._preview_silent()
        self.gateOpened.emit()
        self._set_status("人工确认闸门已打开 · 等待你确认后才落盘")

    @Slot(bool, result="QVariantMap")
    def hatch(self, confirmed: bool) -> dict:
        """人工确认闸门之后的唯一落盘入口。confirmed=False 一律拒绝。"""
        self._set_busy(True)
        try:
            result = gui_model.hatch(self._cfg, confirmed=bool(confirmed))
        except Exception as exc:  # 桥接层需把任何异常转成可读提示（ruff BLE001 未启用）
            result = {"ok": False, "written": False,
                      "message": f"孵化异常：{exc}", "checks": []}
        finally:
            self._set_busy(False)

        ok = bool(result.get("ok"))
        message = str(result.get("message", ""))
        self._checks = result.get("checks", self._checks)
        self.checksChanged.emit()
        if result.get("summary"):
            self._summary = result["summary"]
            self.planReady.emit()
        if result.get("written"):
            self._written = True
            self._command = str(result.get("command", ""))
        self._set_status(message)
        self.toast.emit("positive" if ok else "negative", message)
        self.hatchFinished.emit(ok, message)
        return result

    @Slot()
    def reset(self) -> None:
        """清空本次孵化结果，保留配置态，允许连续孵化多个工程。"""
        self._written = False
        self._command = ""
        self._checks = gui_model.validate_config(self._cfg)
        self.checksChanged.emit()
        self._preview_silent()
        self._set_status("已重置 · 可继续配置下一个工程")

    # ── 界面预览（真 QML 实装渲染）──────────────────────────────
    @Slot(str, result=str)
    def stageQml(self, kind: str) -> str:
        """某配方的 Stage.qml 全文（与落盘产物同源单字不变）；未知配方返回空串。"""
        try:
            return gui_model.stage_qml(kind or self._cfg.kind)
        except (ValueError, KeyError):
            return ""

    @Slot(str, result=str)
    def previewStage(self, kind: str) -> str:
        """把某配方的 Stage.qml 写入系统临时目录（不触碰工程目录与孵化目标），
        返回 ``file://`` URI 供 QML Loader 实装加载；失败返回空串。

        只写临时目录的一个展示副本，治理铁律不受影响：这不是落盘交付，
        交付物只经 ``hatch(confirmed=True)`` 闸门写用户目录。
        实测（2026-11-26）：多配方共用一个临时目录会命中 QML 目录扫描缓存，
        后写入的配方报「File name case mismatch」→ Loader Error；故每配方
        独立子目录，先写盘后加载，首次扫描即含全部文件。
        """
        try:
            text = gui_model.stage_qml(kind or self._cfg.kind)
        except (ValueError, KeyError):
            return ""
        try:
            cache = Path(tempfile.gettempdir()) / "nova-forge-preview" / (kind or self._cfg.kind)
            cache.mkdir(parents=True, exist_ok=True)
            target = cache / "Stage.qml"
            target.write_text(text, encoding="utf-8")
            return target.as_uri()
        except OSError:
            return ""
