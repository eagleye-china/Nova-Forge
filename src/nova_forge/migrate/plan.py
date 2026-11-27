# src/nova_forge/migrate/plan.py
"""migrate2nova 编排层：一次迁移 = 冻结面 → 扫描 → 规则 → 契约门 → 产物。

硬约束（§9.3 / §9.4）：
- **默认 dry-run**：不传 ``write=True`` 时一律不落盘。
- **原 .py 零改动**：只写 ``--out`` 目录下的新文件。
- **不合格不落地**：``--scaffold`` 时若契约门有 FAIL，抛 ``ContractBlocked``，
  一个字节都不写。
- **备份**：写盘前对将被覆盖的产物做 §9.3 临时目录备份，可 ``--restore``。
"""
from __future__ import annotations

from pathlib import Path

from . import backup
from .contract import run_contract_gates
from .freeze import load_freeze
from .report import MigrationPlan, build_json_report, build_todo
from .rules import AUTO, classify
from .scaffold import build_scaffold
from .scanner import scan_python


class ContractBlockedError(RuntimeError):
    """契约门未全绿，禁止 --scaffold 落盘。"""


# 兼容别名：§9 方案骨架与既有交叉引用沿用短名（史料不圆场）
ContractBlocked = ContractBlockedError


def _out_dir(root: Path, out: str | Path | None) -> Path:
    if out is not None:
        return Path(out).expanduser().resolve()
    base = root if root.is_dir() else root.parent
    return base / "nova_migration"


def _pairs(scan) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for finding in scan.findings:
        rule = classify(finding.qt_name)
        if rule.disposition == AUTO and rule.target:
            out.append((finding.qt_name, rule.target))
    return tuple(out)


def plan_migration(
    root: str | Path,
    *,
    api: str | Path | None = None,
    scaffold: bool = False,
    out: str | Path | None = None,
    force: bool = False,
    write: bool = False,
    entry_args: list[object] | None = None,
    qml_root: str | None = None,
) -> MigrationPlan:
    """编排一次迁移；``write=True`` 且 ``scaffold=True`` 才真正落盘。"""
    root_path = Path(root).expanduser().resolve()
    freeze = load_freeze(api)
    scan = scan_python(root_path)
    pairs = _pairs(scan)
    out_dir = _out_dir(root_path, out)
    project_name = root_path.name if root_path.is_dir() else root_path.stem

    scaffold_files: dict[str, str] = {}
    if scaffold:
        scaffold_files = build_scaffold(
            project_name, scan, freeze.api_version, list(pairs), out_dir,
            fallback_args=entry_args,
        )
        scaffold_files["MIGRATION_TODO.md"] = ""   # 占位，落盘前由最终 plan 重写
        scaffold_files["migration-report.json"] = ""

    qml_text = scaffold_files.get("Main.qml") if scaffold else None
    contract = run_contract_gates(freeze, scan, qml_text, qml_root=qml_root)

    if scaffold and write and not contract.passed:
        raise ContractBlocked(
            "契约门未全绿，禁止落盘："
            + "; ".join(f"{g.name}={g.status}: {g.detail}" for g in contract.blockers)
        )

    written = False
    backup_id: str | None = None
    if scaffold and write:
        targets = [out_dir / name for name in scaffold_files]
        existing = [p for p in targets if p.is_file()]
        if existing and not force:
            raise FileExistsError(
                "产物已存在，需 --force 覆盖：" + ", ".join(p.name for p in existing)
            )
        if existing:
            backup_id = backup.create(out_dir, existing).backup_id
        out_dir.mkdir(parents=True, exist_ok=True)
        # 先构造最终 plan 以生成报告文本（written 尚为 False，报告如实标注）
        draft = MigrationPlan(
            project_name=project_name,
            root=str(root_path),
            freeze=freeze,
            scan=scan,
            contract=contract,
            pairs=pairs,
            scaffold_files=tuple(scaffold_files),
            written=False,
            backup_id=backup_id,
        )
        files = dict(scaffold_files)
        files["MIGRATION_TODO.md"] = build_todo(draft)
        files["migration-report.json"] = build_json_report(draft)
        for name, text in files.items():
            (out_dir / name).write_text(text, encoding="utf-8")
        written = True

    return MigrationPlan(
        project_name=project_name,
        root=str(root_path),
        freeze=freeze,
        scan=scan,
        contract=contract,
        pairs=pairs,
        scaffold_files=tuple(scaffold_files),
        written=written,
        backup_id=backup_id,
    )


def written_artifacts(plan: MigrationPlan, out: str | Path | None = None) -> dict[str, str]:
    """返回最终应落盘/展示的产物文本（报告按最终 plan 重算，账实相符）。"""
    result: dict[str, str] = {}
    if plan.scaffold_files:
        root_path = Path(plan.root)
        out_dir = _out_dir(root_path, out)
        scaffold_files = build_scaffold(
            plan.project_name, plan.scan, plan.freeze.api_version,
            list(plan.pairs), out_dir,
        )
        result.update(scaffold_files)
    result["MIGRATION_TODO.md"] = build_todo(plan)
    result["migration-report.json"] = build_json_report(plan)
    return result
