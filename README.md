# PySide Nova

[![PyPI](https://img.shields.io/pypi/v/pyside-nova)](https://pypi.org/project/pyside-nova/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6.5%2B-green)](https://www.qt.io/)

**Nova** 是面向 **PySide6 + Qt Quick(QML)** 的企业级组件库。

与姊妹库 [pyside-quasar](https://github.com/eagleye-china/pyside-quasar)（PySide6 **Widgets** 版）
共享同一套设计规范与属性契约 —— **一套属性，两套渲染底座**。

面向工业 HMI、触摸屏、监控大屏与嵌入式面板：GPU 渲染、MVVM 友好、高 DPI 安全、
键盘 / 触摸 / 鼠标三模交互、统一的明暗主题与焦点环。

---

## 安装

```bash
pip install pyside-nova
```

开发态：

```bash
git clone <repo>
cd pyside-nova
pip install -e ".[dev]"
```

---

## 快速开始

```python
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from pyside_nova import install_qml_import_path, theme_manager

app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()

install_qml_import_path(engine)                       # ① 注册 QML 导入路径

tm = theme_manager()
engine.rootContext().setContextProperty("novaTheme", tm)   # ② 注入主题管理器（可选）

engine.load(Path(__file__).with_name("main.qml"))
if not engine.rootObjects():
    sys.exit(1)

tm.attach_engine(engine)                               # ③ load 之后绑定主题单例
sys.exit(app.exec())
```

```qml
import QtQuick
import Nova 1.0

Window {
    width: 480; height: 240
    visible: true
    color: Theme.background

    NovaButton {
        anchors.centerIn: parent
        label: "启动"
        color: "positive"
        onClicked: console.log("started")
    }
}
```

> ⚠️ 忘记调用 `install_qml_import_path()` 是最高频的踩坑点：QML 会报 `module "Nova" is not installed`。

---

## 属性契约（两库共用）

| 属性 | 取值 |
|---|---|
| `color` | `primary` `secondary` `positive` `negative` `warning` `info` `dark` `white` |
| `variant` | `filled` `outlined` `flat` `text` `push` |
| `size` | `xs` `sm` `md` `lg` `xl` 或整数像素 |
| `rounded` / `elevated` / `dense` | `bool` |
| `loading` / `disabled` | `bool` |
| `label` / `icon` / `iconRight` | `string` / `url` |

命名一旦发布**不再改动**，新增语义只允许追加，不允许改名或建同义别名。

---

## 目录速览

```
src/pyside_nova/
├── __init__.py            # install_qml_import_path() / theme_manager()
├── theme/
│   ├── tokens.py          # ⭐ 设计 token 唯一真源
│   └── manager.py         # NovaThemeManager：明暗切换
├── core/
│   ├── bridge.py          # NovaBridgeBase：异常兜底的桥基类
│   └── worker.py          # BaseWorker / ThreadRunner：工控线程基座
└── qml/Nova/
    ├── qmldir             # QML 模块声明（新增组件必须在此登记）
    ├── Theme.qml          # ⚠️ 生成物，由 tools/gen_theme.py 产出
    ├── Units.qml          # dp 单位入口
    └── NovaButton.qml
```

**改颜色 / 改间距的唯一姿势**：编辑 `theme/tokens.py` → 运行 `python tools/gen_theme.py` → 提交两个文件。
禁止手改 `Theme.qml`（CI 会用 `--check` 校验一致性）。

---

## 开发命令

```bash
ruff format src tests examples tools      # 格式化
ruff check src tests examples tools       # 静态检查
python tools/gen_theme.py                 # 生成 Theme.qml
python tools/gen_theme.py --check         # 校验生成物是否最新
pyside6-qmllint -I src/pyside_nova/qml src/pyside_nova/qml/Nova/*.qml
pytest -v                                 # 单元测试
python examples/01_minimal/main.py        # 最小示例
python -m build && twine check dist/*     # 打包校验
```

---

## 版本策略

- 独立 SemVer，与 `pyside-quasar` **不强制对齐**，只保证同一份设计 token；
- 最低 Qt：PySide6 ≥ 6.5 LTS（主测 6.8 LTS）；
- 新增组件只能在 v1.0 之后追加，不删减已发布属性。

## License

MIT
