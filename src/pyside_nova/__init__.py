"""
pyside-nova
===========
Nova —— 面向 PySide6 + Qt Quick(QML) 的企业级组件库。

与姊妹库 pyside-quasar（Widgets 版）共享同一套设计规范与属性契约：
一套属性，两套渲染底座。

快速开始::

    from pyside_nova import install_qml_import_path
    install_qml_import_path()

    # 之后 QML 中即可：
    # import Nova 1.0
    # NovaButton { label: "启动"; color: "positive" }
"""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version
from pathlib import Path
from typing import Any

try:
    __version__ = _dist_version("pyside-nova")
except PackageNotFoundError:  # 源码态直接运行（未 pip install）
    __version__ = "0.1.0"

#: 包内 QML 根目录，其下是模块目录 ``Nova/``
QML_ROOT: Path = Path(__file__).parent / "qml"


def install_qml_import_path(engine: Any | None = None) -> str:
    """把包内 QML 目录注册为 QML 导入路径，返回绝对路径字符串。

    :param engine: 可选，``QQmlApplicationEngine`` 实例；传入时会同时调用
        ``engine.addImportPath``。
    :return: QML 导入根目录绝对路径。
    :raises FileNotFoundError: 安装包缺少 QML 资源（多为打包漏文件）。

    用法::

        from pyside_nova import install_qml_import_path
        install_qml_import_path()          # 仅设置 QML2_IMPORT_PATH
        install_qml_import_path(engine)   # 同时注入当前引擎
    """
    if not QML_ROOT.is_dir():
        raise FileNotFoundError(
            f"QML 资源目录缺失：{QML_ROOT}。请确认 wheel 已包含 qml/Nova 目录（MANIFEST/package-data 配置）。"
        )

    root = str(QML_ROOT)

    if engine is not None:
        engine.addImportPath(root)

    paths = [p for p in os.environ.get("QML2_IMPORT_PATH", "").split(os.pathsep) if p]
    if root not in paths:
        paths.insert(0, root)
        os.environ["QML2_IMPORT_PATH"] = os.pathsep.join(paths)

    return root


def theme_manager() -> Any:
    """获取全局主题管理器单例（延迟导入，避免包导入即拉起 PySide6）。"""
    from .theme.manager import NovaThemeManager

    return NovaThemeManager.instance()


__all__ = ["__version__", "QML_ROOT", "install_qml_import_path", "theme_manager"]
