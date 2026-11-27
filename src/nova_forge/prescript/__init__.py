# src/nova_forge/prescript/__init__.py
# 创建时间：星期四 2026-11-26 15:20
"""nova-forge prescript —— 用 NovaIncubator 一键孵化九类企业级应用。

九类配方（Prescript）各对应一个 Prescient Layout Shell（NovaIncubator 本身除外）：
agent / copilot / de / orbit / desktop / chat / mobile / flex / wizard

生成物是一个可直接运行的 PySide6 应用：孵化器七槽 + 所选组合根舞台 + 三重校验台账。
"""
from .catalog import KIND_CODES, KINDS, get_kind
from .render import plan_project, render_project

__all__ = ["KINDS", "KIND_CODES", "get_kind", "plan_project", "render_project"]
