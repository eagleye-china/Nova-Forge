"""QML 模块加载冒烟测试：保证 pip 装完后 ``import Nova 1.0`` 真的能用。"""

from __future__ import annotations

from pathlib import Path

import pytest

QML_FILE = Path(__file__).parent / "qml" / "TestLoad.qml"


@pytest.mark.gui
def test_qml_module_loads(qapp, qml_import_root: str) -> None:
    from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

    engine = QQmlApplicationEngine()
    engine.addImportPath(qml_import_root)

    component = QQmlComponent(engine, str(QML_FILE))
    obj = component.create()

    assert obj is not None, "\n".join(err.message() for err in component.errors())
    assert obj.objectName() == ""  # 根 Item

    child = obj.findChild(type(obj), "smokeButton")
    assert child is not None, "NovaButton 实例化失败"

    obj.deleteLater()


@pytest.mark.gui
def test_install_qml_import_path_sets_env(monkeypatch) -> None:
    from pyside_nova import QML_ROOT, install_qml_import_path

    monkeypatch.delenv("QML2_IMPORT_PATH", raising=False)
    root = install_qml_import_path()
    assert Path(root) == QML_ROOT
    assert Path(root).is_dir()


def test_qml_assets_present() -> None:
    """打包漏文件的守门测试：qmldir 与核心 qml 必须存在。"""
    from pyside_nova import QML_ROOT

    module_dir = QML_ROOT / "Nova"
    assert (module_dir / "qmldir").is_file()
    assert (module_dir / "Theme.qml").is_file()
    assert (module_dir / "Units.qml").is_file()
    assert (module_dir / "NovaButton.qml").is_file()
