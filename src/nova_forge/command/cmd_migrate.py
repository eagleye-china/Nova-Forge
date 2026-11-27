# src/nova_forge/command/cmd_migrate.py
"""``nova-forge migrate2nova`` 命令实现（T3 完现）。

原名 ``migrate_to_nova``（根 PROMPT.md §9 方案骨架），CSA 2026-11-28 建议更名
为 ``migrate2nova`` 以便输入；旧名保留为隐藏 alias，史料不圆场、交叉引用不断。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..migrate import backup
from ..migrate.freeze import load_freeze
from ..migrate.plan import ContractBlocked, plan_migration
from ..migrate.report import build_json_report, build_todo
from ..migrate.rules import RULES, classify, validate_rules


def _parse_entry_args(raw: str | None) -> list[object]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--entry-args 不是合法 JSON 数组：{exc}") from exc
    if not isinstance(value, list):
        raise ValueError("--entry-args 必须是 JSON 数组，例如 '[\\\".\\\"]'")
    return value


def _cmd_restore(backup_id: str) -> int:
    try:
        handle = backup.find(backup_id)
    except FileNotFoundError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    if not handle.verify():
        print("❌ 备份校验失败（镜像哈希不符），拒绝回滚", file=sys.stderr)
        return 2
    n = handle.restore()
    print(f"✅ 已从备份 {backup_id} 恢复 {n} 个文件（产物回到迁移前状态）")
    return 0


def _cmd_list_backups() -> int:
    items = backup.list_backups()
    if not items:
        print("（无备份）")
        return 0
    for b in items:
        print(f"{b.backup_id}  files={len(b.files)}  root={b.root}")
    return 0


def _cmd_clean_backups() -> int:
    items = backup.list_backups()
    for b in items:
        b.clean()
    print(f"✅ 已清场 {len(items)} 个临时备份目录（自己建的自己删，不留痕迹）")
    return 0


def _cmd_list_mapping(api: str | None) -> int:
    index = load_freeze(api)
    dangling = validate_rules(index)
    print(
        f"冻结面 {index.path.name} · API {index.api_version} · "
        f"{index.count} 类型 · 指纹 {index.fingerprint}"
    )
    print(f"规则 {len(RULES)} 条 · AUTO 目标悬空 {len(dangling)} 个")
    for qt_name, rule in sorted(RULES.items()):
        print(
            f"  {qt_name:24s} {rule.disposition:8s} "
            f"{rule.target or '—':48s} {rule.layer}"
        )
    if dangling:
        print("❌ 悬空目标：" + ", ".join(dangling), file=sys.stderr)
        return 2
    print("✅ 全部 AUTO 目标在冻结面真实存在（法源链零悬空）")
    return 0


def run_migrate(args: argparse.Namespace) -> int:
    """命令入口；返回进程退出码。"""
    if args.restore:
        return _cmd_restore(args.restore)
    if args.list_backups:
        return _cmd_list_backups()
    if args.clean_backups:
        return _cmd_clean_backups()
    if args.list_mapping:
        return _cmd_list_mapping(args.api)

    try:
        entry_args = _parse_entry_args(args.entry_args)
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    root = Path(args.path).expanduser().resolve()
    try:
        plan = plan_migration(
            root,
            api=args.api,
            scaffold=args.scaffold,
            out=args.out,
            force=args.force,
            write=args.scaffold,     # 默认 dry-run；--scaffold 才落盘
            entry_args=entry_args,
            qml_root=args.qml_root,
        )
    except (FileNotFoundError, ValueError, FileExistsError, ContractBlocked) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(build_json_report(plan), end="")
    else:
        mode = "--scaffold（已落盘）" if plan.written else "dry-run（未落盘）"
        print(f"🔧 nova-forge migrate2nova · {plan.project_name} · {mode}")
        print()
        print(build_todo(plan), end="")

    if not plan.contract.passed:
        print(
            "❌ 契约门有 FAIL：不合格不落地（--scaffold 已拒绝写盘）",
            file=sys.stderr,
        )
        return 2
    if plan.written:
        out_dir = Path(args.out).expanduser().resolve() if args.out else (
            root if root.is_dir() else root.parent
        ) / "nova_migration"
        print(f"\n✅ 产物已写入 {out_dir}")
        if plan.backup_id:
            print(f"   备份 {plan.backup_id} · 回滚：nova-forge migrate2nova --restore {plan.backup_id}")
    return 0


def coverage_summary(plan) -> str:
    """供测试 / 其他命令复用的一行覆盖率口径。"""
    total = len(plan.scan.findings)
    resolved = sum(
        1 for f in plan.scan.findings
        if classify(f.qt_name).disposition in ("AUTO", "RUNTIME", "NATIVE", "MANUAL")
    )
    pct = 100.0 if total == 0 else resolved / total * 100
    return f"{resolved}/{total} = {pct:.0f}%"
