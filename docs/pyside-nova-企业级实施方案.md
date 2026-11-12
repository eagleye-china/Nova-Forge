# pyside-nova 企业级实施方案（v1.0 基线）

> 文档定位：`pyside-nova` 旗舰版组件库的架构决策 + 工程规范 + 落地路线图。
> 建议入库路径：`pyside-nova/docs/ARCHITECTURE.md`（本文件可直接作为初版）。
> 姊妹库：`pyside-quasar`（PySide6 Widgets，前缀 `Quasar`）

---

## 一、定位与边界（先定死，避免后面反复摇摆）

| 项 | 定义 |
|---|---|
| 产品定位 | Material / Quasar 设计语言在 **Qt Quick(QML)** 上的企业级本地化实现，面向工控 HMI、触摸屏、监控大屏、嵌入式面板 |
| 目标用户 | PySide6 + QML 的工业 HMI / 桌面可视化开发者 |
| 渲染底座 | Qt Quick Scene Graph（GPU），纯 QML 实现为主，Python 只做主题、桥接、高性能组件补位 |
| 发布形态 | PyPI `pyside-nova`，导入 `pyside_nova`，QML 模块 `import Nova 1.0`，组件前缀 `Nova*` |
| 版本策略 | 独立 SemVer，与 `pyside-quasar` 版本**不强制对齐**，只保证同一份设计 token |
| 最低 Qt | PySide6 ≥ 6.5 LTS（主测 6.8 LTS），Python ≥ 3.10 |
| 非目标 | ❌ 不复刻 Web 专属行为（DOM、CSS、浏览器断点、Vue 路由）；❌ 不做 Quasar 1:1 移植；❌ 不承担业务层桥接（桥接只提供基类） |

**一句话定位（对外文案）**：
> PySide Nova —— 与 PySide Quasar 同一套设计规范、面向 QML 的旗舰组件库，GPU 渲染、MVVM 友好，专为工业 HMI 与触摸屏打造。

---

## 二、命名契约（双库统一，这是最大竞争力）

### 2.1 三层命名

| 层级 | pyside-quasar | pyside-nova |
|---|---|---|
| 包名 | `pyside-quasar` | `pyside-nova` |
| 导入 | `import pyside_quasar` | `import pyside_nova` |
| 组件命名空间 | Python 类 `QuasarButton` | QML 模块 `Nova` / 组件 `NovaButton` |
| 引用写法 | `QuasarButton(...)` | `NovaButton { }` |

### 2.2 属性命名契约（两库必须一致，写进文档并做自动化校验）

```
color       : primary | secondary | positive | negative | warning | info | dark | white
variant     : filled | outlined | flat | push | text
size        : xs | sm | md | lg | xl | <int px>
rounded     : bool | <int radius>
elevated    : bool
dense       : bool
loading     : bool
disabled    : bool
icon / iconRight : url
label / text     : string
```

> 工程保障：把属性名放进 `design_tokens/contract.json`，CI 里做一次字符串级校验，任一库新增组件属性名漂移就红灯。

### 2.3 设计 Token 单一真源

```
pyside-design-tokens/            # 独立仓库（可选，早期可先内嵌）
├── tokens.json                  # 唯一真源：颜色/间距/圆角/字号/动效时长
└── scripts/gen.py               # 生成：Theme.qml（Nova）+ palette.py（Quasar）
```

**为什么必须单一真源**：QML 侧 `Theme` 是 singleton，Python 侧 `ThemeManager` 是 QObject，双源必漂移。做法是构建期从 `tokens.json` 生成两份产物，禁止手改生成文件。

---

## 三、仓库结构（src-layout，PEP 621）

```
pyside-nova/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
├── ruff.toml
├── mkdocs.yml
├── MANIFEST.in
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── src/
│   └── pyside_nova/
│       ├── __init__.py              # __version__ / install_qml_import_path()
│       ├── py.typed
│       ├── core/
│       │   ├── bridge.py            # NovaBridgeBase(QObject)：信号/Property 基类
│       │   ├── worker.py            # BaseWorker / ThreadRunner（工控线程安全）
│       │   ├── logging.py           # NovaLog 单例
│       │   └── i18n.py
│       ├── theme/
│       │   ├── manager.py           # NovaThemeManager：明暗切换、token 查询
│       │   └── __init__.py
│       ├── components/
│       │   ├── table.py             # 唯一走 Python 的高性能组件（QQuickItem/QSGNode）
│       │   └── __init__.py
│       ├── assets/
│       │   ├── icons/*.svg
│       │   └── fonts/
│       └── qml/
│           ├── qmldir               # 外层：把 Nova/ 暴露出去
│           └── Nova/
│               ├── qmldir           # module Nova
│               ├── Theme.qml        # pragma Singleton（生成物）
│               ├── Units.qml        # dp 换算 helper
│               ├── NovaButton.qml
│               ├── NovaCard.qml
│               └── ...
├── examples/
│   ├── 00_gallery/                  # 主 Gallery（各组件分页演示）
│   └── 01_hmi_shell/                # 工控 HMI 整机模板
├── tests/
│   ├── conftest.py
│   ├── test_button.py
│   ├── visual/                      # 视觉回归基线图
│   └── qml/test_*.qml
└── docs/
    ├── ARCHITECTURE.md
    ├── component-spec.md            # 组件开发模板
    ├── api/
    └── roadmap.md
```

---

## 四、关键技术决策（这 8 条定下来，后面不返工）

### 决策 1：组件优先纯 QML，Python 只补位
- 原子/表单/容器/反馈组件 → **纯 `.qml` 文件**（Scene Graph 最优、支持 `pyside6-qmlformat`、Design Studio 可编辑、热重载可用）
- 只有「海量行表格、实时工业曲线、粒子/Shader」→ `QQuickItem` + QSGNode（Python/C++）
- ❌ 不要用 `QQuickPaintedItem` 做普通组件：CPU 绘制，高 DPI 下发虚，且无法参与 Scene Graph 批处理

### 决策 2：QML 模块用 `qmldir` 声明，不用逐个 `qmlRegisterType`
```
# src/pyside_nova/qml/Nova/qmldir
module Nova
singleton Theme 1.0 Theme.qml
singleton Units 1.0 Units.qml
NovaButton 1.0 NovaButton.qml
NovaCard 1.0 NovaCard.qml
```
理由：文件级注册可保留 `.qml` 原始形态，热重载、Design Studio、qmllint 全部可用；`qmlRegisterType` 只留给 Python 实现的少数组件。

### 决策 3：打包态用「外置 QML 文件 + addImportPath」，不用 qrc
```python
def install_qml_import_path(engine=None) -> str:
    """把包内 qml 目录注册为 QML 导入路径，返回该路径。"""
    from pathlib import Path
    qml_root = Path(__file__).parent / "qml"
    if engine is not None:
        engine.addImportPath(str(qml_root))
    import os
    os.environ["QML2_IMPORT_PATH"] = os.pathsep.join(
        filter(None, [os.environ.get("QML2_IMPORT_PATH"), str(qml_root)])
    )
    return str(qml_root)
```
- 优点：`pip install` 后即可 `import Nova 1.0`；热重载、qmllint 正常；用户可读可调试
- 嵌入式发布（Boot to Qt）再额外提供 `--embed-qrc` 构建开关，编译进资源（`pyside6-rcc`）

### 决策 4：主题走「Python 单例 + QML singleton 双通道，但单真源」
- 真源：`tokens.json`
- 生成：`Theme.qml`（QML 读色用）+ `palette.py`（Python 侧用）
- 运行时：`NovaThemeManager` 作为 context property 注入（`novaTheme`），QML 里 `Theme.primary` 直接取色，主题切换由 `novaTheme.mode` 驱动 `Theme` 重载

```python
# 注册示例
engine.rootContext().setContextProperty("novaTheme", NovaThemeManager.instance())
qmlRegisterSingletonInstance(...)  # 如需 QML 侧 import 方式访问
```

### 决策 5：高 DPI / 尺寸单位统一 dp
```qml
// Units.qml
pragma Singleton
import QtQuick
QtObject {
    readonly property real dp: 1.0        // Qt6 已做 DPR 缩放，基准 1dp = 1px@96dpi
    function px(v) { return v * dp }
}
```
规则：**间距、圆角、线宽、图标尺寸全部写 dp 值，禁止魔法数字直接写像素**；svg 图标必须矢量；文字字号用 `Theme.type.body` 等 token，不散写字号。

### 决策 6：焦点与键盘导航是一等公民（工控现场大量用键盘/触摸）
- 每个交互组件必须实现 `focusPolicy`、`activeFocusOnTab`
- 视觉焦点环统一由 `NovaFocusRing.qml` 原语绘制，禁止组件各自实现
- `KeyNavigation.tab` 显式串联，保证现场键盘可操作
- 触摸目标最小 44dp（HMI 手套操作场景建议 48dp）

### 决策 7：线程与桥接边界写进规范（工控 7×24 稳定性的根）
- 库只提供 `NovaBridgeBase` 与 `BaseWorker/ThreadRunner`
- 硬规则：**Worker 内不得触碰任何 QML 可绑定属性**，只能 `emit` 原始数据信号；属性更新回主线程
- 硬规则：**任何 IO / Modbus / 数据库不得出现在 QML 组件的 JS 函数里**（QML 的 JS 跑在主线程，一阻塞整屏卡死）

### 决策 8：无障碍与可访问名
- 所有组件默认设置 `Accessible.name` / `Accessible.description`
- 图标按钮（`NovaIconButton`、FAB）必须要求 `accessibleName` 或 `label`，否则文档标注为「不推荐用于主流程」

---

## 五、组件分层与命名清单（v1.0 只做 L0–L3）

### L0 基座原语（不对外暴露语义，供组件复用）
| 文件 | 说明 |
|---|---|
| `NovaTheme.qml` / `Theme.qml` | 色彩/字号/间距/动效 token |
| `NovaUnits.qml` / `Units.qml` | dp 换算 |
| `NovaStateLayer.qml` | hover/pressed/focus 叠加层（Material state layer） |
| `NovaFocusRing.qml` | 统一焦点环 |
| `NovaRipple.qml` | 水波纹（GPU 友好，ShaderEffect 可选） |
| `NovaIcon.qml` | SVG 图标注册与着色 |
| `NovaSurface.qml` | 圆角/阴影/边框基面 |

### L1 原子组件
`NovaButton`、`NovaIconButton`、`NovaFab`、`NovaBadge`、`NovaAvatar`、`NovaAvatarGroup`、`NovaChip`、`NovaSpinner`、`NovaProgress`（linear/circular）、`NovaDivider`、`NovaSkeleton`

### L2 表单组件
`NovaTextField`、`NovaTextArea`、`NovaSelect`、`NovaCheckbox`、`NovaSwitch`、`NovaRadio`、`NovaRadioGroup`、`NovaSlider`、`NovaStepper`、`NovaDatePicker`、`NovaForm`（校验容器）

### L3 容器与反馈
`NovaCard`、`NovaDialog`、`NovaDrawer`、`NovaTooltip`、`NovaSnackbar`、`NovaBanner`、`NovaTabs`、`NovaExpansion`、`NovaLinearStepper`、`NovaPageStack`

### L4 工控专属（v1.1 起，差异化护城河）
`NovaTableView`（虚拟化 + 列冻结 + 万行流畅）、`NovaTreeView`、`NovaTrendChart` / `NovaSparkline`（QQuickItem 自绘）、`NovaGauge`、`NovaStatusLED`、`NovaAlarmTag`、`NovaNumericKeypad`（触摸屏数字键盘）、`NovaIndicator`（工艺流程图节点）

> ⚠️ v1.0 严格**不做** L4，先把 L0–L3 做透、测试覆盖、文档齐全，否则战线拉长必失控。

---

## 六、单组件开发模板（DoD：Definition of Done）

每个组件必须同时交付 6 件东西，缺一不算完成：

1. `NovaXxx.qml` —— 实现文件，`[Component] { id: root }` 标准结构，`required property` 优先
2. `docs/api/NovaXxx.md` —— 属性表 + 枚举取值 + 示例代码 + 截图
3. `examples/00_gallery/pages/XxxPage.qml` —— Gallery 演示页（含所有变体矩阵）
4. `tests/qml/test_xxx.qml` + `tests/test_xxx.py` —— 行为断言（属性生效、焦点、禁用态、信号）
5. `tests/visual/xxx_all_variants.png` —— 视觉回归基线图
6. `CHANGELOG.md` 条目 + `qmldir` 注册

**组件代码规范**（写进 `docs/component-spec.md`）：
```qml
// NovaXxx.qml —— 首行类注释 + 属性契约 + 依赖声明
import QtQuick
import QtQuick.Controls.Basic   // 只用 Basic，不用平台默认样式

Item {
    id: root

    // ── 公共属性（顺序固定：语义 > 外观 > 状态 > 尺寸）
    property string color: "primary"
    property string variant: "filled"
    property string size: "md"
    property bool rounded: true
    property bool elevated: false
    property bool loading: false
    property bool disabled: false
    property string label: ""
    property url icon: ""

    // ── 信号
    signal clicked()

    // ── 只读派生
    readonly property bool _interactive: !disabled && !loading

    implicitWidth: Units.px(...)
    implicitHeight: Units.px(...)

    // 子结构：StateLayer → Ripple → Content → FocusRing（固定绘制顺序）
}
```

---

## 七、质量体系（四道闸门）

| 闸门 | 工具 | 命令 | 通过标准 |
|---|---|---|---|
| ① 格式 | ruff format | `ruff format src tests examples` | 无 diff |
| ② 静态检查 | ruff check | `ruff check src tests examples` | 0 error |
| ③ QML 静态检查 | qmllint | `pyside6-qmllint -I src/pyside_nova/qml src/pyside_nova/qml/Nova/*.qml` | 0 warning（warning 也当错） |
| ④ 行为测试 | pytest + pytest-qt | `pytest tests -v` | 覆盖率 ≥ 85%（core/theme ≥ 95%） |
| ⑤ 视觉回归 | grabWindow + 像素 diff | `pytest tests/visual` | 差异像素 < 0.3% |
| ⑥ 打包校验 | build + twine | `python -m build && twine check dist/*` | 0 warning |

`ruff.toml`：
```toml
line-length = 120
target-version = "py310"
select = ["E", "W", "F", "I", "B", "UP", "SIM"]
ignore = ["E501"]

[format]
quote-style = "double"
indent-width = 4
```

`pytest` 里加载 QML 的标准写法（`tests/conftest.py`）：
```python
import pytest
from PySide6.QtQml import QQmlApplicationEngine
from pyside_nova import install_qml_import_path

@pytest.fixture(scope="session")
def qml_engine(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(install_qml_import_path())
    yield engine
    engine.deleteLater()
```

CI 矩阵：`Python 3.10/3.11/3.12 × Qt 6.5/6.8 × ubuntu/windows`，Linux 用 `xvfb-run` 跑 GUI 测试。

---

## 八、打包与发布

### `pyproject.toml`（关键片段）
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pyside-nova"
version = "0.1.0"
description = "Nova: enterprise Qt Quick(QML) component library for PySide6 — same design spec as pyside-quasar, built for HMI & touch screens."
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
dependencies = ["PySide6>=6.5"]
keywords = ["pyside6", "qml", "qtquick", "hmi", "components", "quasar", "material"]

[project.urls]
Homepage = "https://github.com/eagleye-china/pyside-nova"
Documentation = "https://eagleye-china.github.io/pyside-nova/"
Changelog = "https://github.com/eagleye-china/pyside-nova/blob/main/CHANGELOG.md"

[project.optional-dependencies]
dev = ["pytest", "pytest-qt", "ruff", "build", "twine", "mypy"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
pyside_nova = [
    "py.typed",
    "qml/qmldir",
    "qml/Nova/qmldir",
    "qml/Nova/*.qml",
    "assets/icons/*.svg",
]
```

`MANIFEST.in`：
```
recursive-include src/pyside_nova/qml *
recursive-include src/pyside_nova/assets *
include src/pyside_nova/py.typed
```

发布流程：`tag → GitHub Actions → build → twine check → PyPI Trusted Publishing(OIDC)`，不再手工 `twine upload`。

---

## 九、实施路线图（8 周 v0.1.0 → v1.0.0）

| 阶段 | 周期 | 交付 |
|---|---|---|
| P0 骨架 | 第 1 周 | 仓库结构、pyproject、`install_qml_import_path`、`Theme`/`Units` 生成链、CI 骨架、Gallery 空壳可跑 |
| P1 基座原语 | 第 2 周 | L0 全部原语 + 视觉回归框架（黄金图） |
| P2 原子组件 | 第 3–4 周 | L1 全部（Button 打样，确立模板）→ 发布 `0.1.0a1` 到 PyPI 走通链路 |
| P3 表单组件 | 第 5–6 周 | L2 全部 + 校验/焦点/键盘导航专项测试 |
| P4 容器反馈 | 第 7 周 | L3 全部 + HMI Shell 模板示例 |
| P5 封版 | 第 8 周 | 文档站上线、覆盖率达标、`1.0.0` 发布、README 品牌文案统一 |

**打样原则**：`NovaButton` 是第一个组件，必须同时在它上面把「模板 → 测试 → 视觉基线 → 文档 → 注册 → 发布」全链路跑通，之后所有组件照抄这套流水线。**第一个组件不要追求功能多，要追求流程完整。**

---

## 十、风险清单与对策

| 风险 | 影响 | 对策 |
|---|---|---|
Qt 小版本 QML 行为差异（6.5/6.8） | 组件在新版本样式错位 | CI 双 Qt 矩阵；`qmllint` 当错误处理；文档标注最低版本 |
`pip install` 后 `import Nova 1.0` 找不到 | 用户第一体验崩 | `install_qml_import_path()` 必须在 README 第一步；发布前用干净 venv 做安装验证 |
QML 打包漏文件（qmldir 未进包） | wheel 缺模块 | CI 加一步：解压 wheel 校验 qmldir/qml 数量，数量不符即红 |
大列表/实时曲线卡顿 | HMI 现场致命 | L4 才做；TableView 走虚拟化 + `QQuickItem`；动画只改 transform，不改布局 |
双库设计 token 漂移 | 品牌失真 | `tokens.json` 单一真源 + 构建生成 + CI 校验 |
维护成本超预期 | 半途而废 | v1.0 砍掉 L4；每组件 DoD 六件套强制；不接业务定制需求进核心库 |

---

## 十一、v1.0 验收清单（逐项打勾才算封版）

- [ ] `pip install pyside-nova` 在干净 venv 可用，`import Nova 1.0` 成功
- [ ] L1 + L2 + L3 全部组件有 API 文档 + Gallery 页 + 测试 + 视觉基线
- [ ] 明/暗主题切换全组件无错色、无硬编码色值
- [ ] 125% / 150% / 200% 缩放下无线条发虚、图标模糊
- [ ] 全组件 `Tab` 可遍历，焦点环视觉一致
- [ ] 全交互组件触摸目标 ≥ 44dp
- [ ] 所有组件 `disabled` / `loading` 语义一致
- [ ] 覆盖率 ≥ 85%，`ruff` / `qmllint` 零告警
- [ ] wheel 解包校验 QML 资源完整
- [ ] 文档站可访问，单组件有可复制示例
- [ ] CHANGELOG、README 品牌文案与 pyside-quasar 统一为「同一设计规范、双渲染底座」

---

## 附：README 头部建议文案

```markdown
# PySide Nova

[![PyPI](https://img.shields.io/pypi/v/pyside-nova)](https://pypi.org/project/pyside-nova/)
[![Qt](https://img.shields.io/badge/Qt-6.5%2B-green)]()

**Nova** 是面向 **PySide6 + Qt Quick(QML)** 的企业级组件库，
与姊妹库 [pyside-quasar](https://github.com/eagleye-china/pyside-quasar)（Widgets 版）
共享同一套设计规范与属性契约 —— **一套属性，两套渲染底座**。

面向工业 HMI、触摸屏、监控大屏与嵌入式面板：GPU 渲染、MVVM 友好、
高 DPI 安全、键盘/触摸双模交互。

```python
from pyside_nova import install_qml_import_path
install_qml_import_path()
```
```qml
import Nova 1.0
NovaButton { label: "启动"; color: "positive"; onClicked: start() }
```
```
```

> （注：部分内容由豆包 AI 生成）