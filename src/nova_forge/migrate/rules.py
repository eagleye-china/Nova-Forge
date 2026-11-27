# src/nova_forge/migrate/rules.py
"""QtWidgets → pyside-nova 的语义处置规则（T3 一期 L0+L1）。

设计约束（§9.2 / §9.4）：
- **Nova 侧清单不手写**：每条 ``AUTO`` 规则的 ``target`` 必须是冻结面里真实存在
  的公共类型，由 ``validate_rules()`` 逐一校验，悬空即失败（法源链不留悬空）。
- **零静默遗漏**：任何未登记的 Qt 名由 ``UNKNOWN_RULE`` 兜底为 ``MANUAL`` 并
  写明原因，因此扫描出的每个 Qt 引用 100% 有处置。
- **四类处置**：``AUTO``（映射到库公共类型）/ ``RUNTIME``（保留 Python 侧）/
  ``NATIVE``（QtQuick 原生等价）/ ``MANUAL``（显式人工，含原因）。
- **库语义边界**：库组件「只发意图、不写盘不发请求」，故文件对话框 / 剪贴板 /
  托盘图标等一律不伪装成 QML 组件。

L0 = 设计语言 / 基础控件层，L1 = 布局系统层（对齐 ECOSYSTEM_PARITY 七层口径）。
"""
from __future__ import annotations

from dataclasses import dataclass

from .freeze import FreezeIndex

AUTO = "AUTO"
RUNTIME = "RUNTIME"
NATIVE = "NATIVE"
MANUAL = "MANUAL"
DISPOSITIONS = (AUTO, RUNTIME, NATIVE, MANUAL)


@dataclass(frozen=True)
class Rule:
    """一个 Qt 名的处置决议。"""

    disposition: str
    target: str | None          # AUTO: 冻结面 fqname；其余为 None
    layer: str                  # L0 / L1 / L2 / —
    note: str


def _auto(target: str, layer: str, note: str) -> Rule:
    return Rule(AUTO, target, layer, note)


def _runtime(layer: str, note: str) -> Rule:
    return Rule(RUNTIME, None, layer, note)


def _native(layer: str, note: str) -> Rule:
    return Rule(NATIVE, None, layer, note)


def _manual(layer: str, note: str) -> Rule:
    return Rule(MANUAL, None, layer, note)


C = "Nova.Controls"
S = "Nova.Services"
L = "Nova.Composite.LayoutShell"

RULES: dict[str, Rule] = {
    # ── QtWidgets · 应用与根窗口 ────────────────────────────────
    "QApplication": _runtime("L0", "启动器改为 QGuiApplication + QQmlApplicationEngine + init_nova()"),
    "QMainWindow": _auto(f"{L}.NovaDesktop", "L1", "组合根：菜单树 / 工具栏 / 页面区 / 状态栏四分区"),
    "QWidget": _native("L0", "QtQuick 原生 Item（不作库组件映射）"),
    "QDialog": _auto(f"{C}.NovaDialogShell", "L0", "对话框壳；业务内容由槽位注入"),
    "QMessageBox": _auto(f"{C}.NovaDialogShell", "L0", "通知/确认走 NovaDialogShell + NovaNotifyHandle"),
    "QFileDialog": _runtime("L0", "保留 Python QFileDialog；库组件只发 exportRequested 等意图信号，不写盘"),
    "QSystemTrayIcon": _manual("L0", "无 QML 对应：系统托盘须保留 QtWidgets 侧（方案 §9.4 点名的 MANUAL 验证项）"),
    # ── QtWidgets · 基础控件（L0）────────────────────────────────
    "QPushButton": _auto(f"{C}.NovaBtn", "L0", "按钮；受控契约只 emit clicked"),
    "QToolButton": _auto(f"{C}.NovaBtn", "L0", "图标按钮用 NovaBtn + NovaIcon"),
    "QCheckBox": _auto(f"{C}.NovaCheckbox", "L0", "modelValue 受控契约"),
    "QRadioButton": _auto(f"{C}.NovaRadio", "L0", "配合 NovaOptionGroup"),
    "QButtonGroup": _auto(f"{C}.NovaBtnGroup", "L0", "按钮分组"),
    "QLabel": _auto(f"{C}.NovaText", "L0", "静态文本；富文本用 NovaMarkdown"),
    "QLineEdit": _auto(f"{C}.NovaInput", "L0", "单行输入；modelValue 受控"),
    "QTextEdit": _auto(f"{C}.NovaEditor", "L0", "多行编辑"),
    "QPlainTextEdit": _auto(f"{C}.NovaEditor", "L0", "多行编辑"),
    "QComboBox": _auto(f"{C}.NovaSelect", "L0", "下拉选择；选项走坑位 70 JS 数组重建"),
    "QSpinBox": _auto(f"{C}.NovaField", "L0", "数值字段；钳制由 NovaField 承担"),
    "QDoubleSpinBox": _auto(f"{C}.NovaField", "L0", "数值字段"),
    "QSlider": _auto(f"{C}.NovaSlider", "L0", "滑块；modelValue 受控"),
    "QListWidget": _auto(f"{C}.NovaList", "L0", "列表容器"),
    "QListWidgetItem": _auto(f"{C}.NovaItem", "L0", "列表项 + NovaItemSection/NovaItemLabel"),
    "QTreeWidget": _auto(f"{C}.NovaTree", "L0", "树形容器"),
    "QTableWidget": _auto(f"{C}.NovaTable", "L0", "表格；完整插槽 / 列元字段 / 分页"),
    "QTableView": _auto(f"{C}.NovaDataGrid", "L0", "真虚拟化表格 + pyside_nova.datagrid 模型层"),
    "QTabWidget": _auto(f"{C}.NovaTabs", "L1", "页签容器 + NovaTab/NovaTabPanel"),
    "QToolBar": _auto(f"{C}.NovaToolbar", "L0", "工具栏 + NovaToolbarTitle"),
    "QMenuBar": _auto(f"{C}.NovaToolbar", "L0", "顶栏菜单"),
    "QMenu": _auto(f"{C}.NovaMenu", "L0", "菜单"),
    "QStatusBar": _auto(f"{C}.NovaFooter", "L0", "底部状态栏"),
    "QGroupBox": _auto(f"{C}.NovaCard", "L1", "分组卡片 + NovaCardSection"),
    "QFrame": _auto(f"{C}.NovaCard", "L1", "描边容器"),
    "QProgressBar": _manual("L0", "冻结面无线性进度组件；建议 NovaSpinner 占位或自定义几何"),
    "QSplitter": _manual("L1", "冻结面无 SplitView 封装；用 QtQuick.SplitView 或组合根手动拆分"),
    "QStackedWidget": _auto(f"{C}.NovaTabPanels", "L1", "语义近似：多面板切换由 NovaTabPanels 承担"),
    "QScrollArea": _auto(f"{C}.NovaScrollArea", "L1", "滚动容器"),
    "QCalendarWidget": _auto(f"{C}.NovaDate", "L0", "日期选择"),
    "QDateTimeEdit": _auto(f"{C}.NovaDate", "L0", "日期时间"),
    "QTimeEdit": _auto(f"{C}.NovaTime", "L0", "时间选择"),
    "QColorDialog": _auto(f"{C}.NovaColorPicker", "L0", "颜色选择"),
    "QToolTip": _auto(f"{C}.NovaTooltip", "L0", "提示"),
    # ── QtWidgets · 布局（L1）────────────────────────────────────
    "QHBoxLayout": _auto(f"{C}.NovaRow", "L1", "横向行布局"),
    "QVBoxLayout": _auto(f"{C}.NovaCol", "L1", "纵向列布局（12 栅格语义，间距取 NovaTheme 令牌）"),
    "QGridLayout": _auto(f"{C}.NovaLayout", "L1", "栅格布局由 NovaRow/NovaCol + NovaLayout 组合"),
    "QFormLayout": _auto(f"{C}.NovaForm", "L1", "表单布局"),
    "QBoxLayout": _auto(f"{C}.NovaRow", "L1", "通用盒布局"),
    # ── QtCore ──────────────────────────────────────────────────
    "Qt": _native("L0", "QML 全局 Qt 对象（枚举 / 对齐常量直接可用）"),
    "QTimer": _native("L0", "QML Timer 元素"),
    "QObject": _native("L0", "QML QtObject"),
    "Signal": _runtime("L0", "QML signal 声明；跨语言桥用 @Slot 暴露"),
    "Slot": _runtime("L0", "QML function / Python @Slot 桥"),
    "Property": _runtime("L0", "QML property 声明"),
    "QAbstractTableModel": _runtime("L0", "pyside_nova.datagrid.NovaDataGridModel（坑位 32 reuseItems:false）"),
    "QStandardItemModel": _runtime("L0", "pyside_nova.datagrid 模型层"),
    "QSortFilterProxyModel": _runtime("L0", "pyside_nova.datagrid 过滤 / 分页代理链（坑位 80 逐级 mapToSource）"),
    "QThread": _manual("—", "无 QML 对应；线程池 / 长任务保留 Python 侧"),
    "QSettings": _runtime("—", "配置持久化保留 Python 侧"),
    "QUrl": _native("—", "QML url 类型"),
    "QPoint": _native("—", "QML point / Qt.point()"),
    "QSize": _native("—", "QML size / Qt.size()"),
    "QEvent": _manual("—", "事件过滤器无 QML 对应，需人工改写"),
    # ── QtGui ───────────────────────────────────────────────────
    "QColor": _native("L0", "QML color"),
    "QBrush": _native("L0", "QML color / Gradient"),
    "QFont": _native("L0", "NovaTheme 12 级字阶令牌"),
    "QIcon": _native("L0", "NovaIcon + qrc 资源"),
    "QPixmap": _native("L0", "QML Image"),
    "QImage": _native("L0", "QML Image"),
    "QAction": _runtime("L0", "改为 QML signal + NovaMenu/NovaBtn 项"),
    "QClipboard": _runtime("L0", "保留 Python QGuiApplication.clipboard()"),
    "QPalette": _manual("L0", "主题由 NovaTheme 单例接管，勿逐控件设色"),
    "QKeySequence": _manual("L0", "快捷键改用 QML Shortcut / Keys.onPressed"),
    "QCursor": _native("—", "QML MouseArea cursorShape"),
}

UNKNOWN_RULE = _manual(
    "—", "未登记映射规则：需人工评估语义后登记（零静默遗漏，覆盖率仍计 100%）"
)


def classify(qt_name: str) -> Rule:
    """取 Qt 名的处置；未登记一律 MANUAL，保证零静默遗漏。"""
    return RULES.get(qt_name, UNKNOWN_RULE)


def validate_rules(index: FreezeIndex) -> list[str]:
    """校验所有 AUTO 目标在冻结面真实存在；返回悬空目标列表（空 = 全绿）。"""
    dangling: list[str] = []
    for qt_name, rule in RULES.items():
        if rule.disposition != AUTO:
            continue
        assert rule.target is not None
        if not index.has(rule.target):
            dangling.append(f"{qt_name} → {rule.target}")
    return dangling


def layer_counts() -> dict[str, int]:
    """按生态层级统计规则条数，供报告展示 L0/L1 覆盖。"""
    counts: dict[str, int] = {}
    for rule in RULES.values():
        counts[rule.layer] = counts.get(rule.layer, 0) + 1
    return counts
