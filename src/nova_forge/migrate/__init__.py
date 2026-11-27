# src/nova_forge/migrate/__init__.py
"""T3 · migrate2nova：一键 QtWidgets → pyside-nova 迁移助手（L0+L1 一期）。

法源链：根 ``PROMPT.md §9``（T3 方案）→ ``nova-forge/docs/MIGRATE2NOVA.md``
→ 本包。映射表由 pyside-nova API 冻结面自动生成，契约门不合格不落地。
"""
from __future__ import annotations

from .backup import Backup, create, find, list_backups
from .contract import ContractReport, Gate, run_contract_gates
from .freeze import FreezeIndex, NovaType, discover_freeze, load_freeze
from .plan import ContractBlocked, plan_migration, written_artifacts
from .report import MigrationPlan, build_json_report, build_todo
from .rules import DISPOSITIONS, RULES, Rule, classify, layer_counts, validate_rules
from .scaffold import build_scaffold, render_main_py, render_main_qml
from .scanner import Finding, Occurrence, ScanResult, scan_python

__all__ = [
    "DISPOSITIONS",
    "RULES",
    "Backup",
    "ContractBlocked",
    "ContractReport",
    "Finding",
    "FreezeIndex",
    "Gate",
    "MigrationPlan",
    "NovaType",
    "Occurrence",
    "Rule",
    "ScanResult",
    "build_json_report",
    "build_scaffold",
    "build_todo",
    "classify",
    "create",
    "discover_freeze",
    "find",
    "layer_counts",
    "list_backups",
    "load_freeze",
    "plan_migration",
    "render_main_py",
    "render_main_qml",
    "run_contract_gates",
    "scan_python",
    "validate_rules",
    "written_artifacts",
]
