# src/nova_forge/bridge/__init__.py
# 创建时间：星期五 2026-11-27 06:20
"""nova-forge 的 Python↔QML 桥接层。

CSA 2026-11-27 拍板：桥与界面分离——本包只放 QObject 桥（暴露给 QML 的
上下文对象与业务 Slot），窗口装配与 QML 资产留在 ``nova_forge.ui``。
"""
