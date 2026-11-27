# src/nova_forge/command/cmd_comment.py
# 创建时间：星期二 2026-11-24 21:39


from __future__ import annotations

import sys
from pathlib import Path

from ..core.comment_logic import iter_source_files, process_file


def _print_report(results: list[dict]) -> None:
    """分组打印处理结果，给出可读摘要。"""
    done = [r for r in results if r["status"] == "done"]
    already = [r for r in results if r["status"] == "already"]
    failed = [r for r in results if r["status"] == "failed"]
    skipped = [r for r in results if r["status"] == "skipped"]

    for r in done:
        print(f"  ✅ {r['file']}")
    if already:
        print(f"\n⏭️  已有两行注释，跳过 {len(already)} 个（加 --force 刷新时间）：")
        for r in already:
            print(f"     {r['file']}")
    if failed:
        print(f"\n❌ 失败 {len(failed)} 个（原文件未改动）：")
        for r in failed:
            print(f"     {r['file']} —— {r['reason']}")
    if skipped:
        print(f"\n⊘  跳过 {len(skipped)} 个：")
        for r in skipped:
            print(f"     {r['file']} —— {r['reason']}")

    print(
        f"\n📊 汇总：处理 {len(done)} 个 / 已存在 {len(already)} 个 / "
        f"失败 {len(failed)} 个 / 跳过 {len(skipped)} 个"
    )


def run_comment(
    root: str = ".",
    dry_run: bool = False,
    force: bool = False,
    ext: str = "all",
) -> None:
    """执行两行头部注释注入。

    Args:
        root:   项目根目录（默认当前目录）
        dry_run: 仅预览，不写文件
        force:  刷新创建时间为本次执行时刻的北京时间
        ext:    'all' / 'py' / 'qml' 过滤扩展名
    """
    project_root = Path(root).resolve()
    if not project_root.is_dir():
        print(f"❌ 目录不存在：{project_root}", file=sys.stderr)
        raise SystemExit(2)

    files = iter_source_files(project_root)
    if ext != "all":
        wanted = f".{ext.lstrip('.')}"
        files = [p for p in files if p.suffix == wanted]

    mode = "🔍 预览模式（dry-run，不写文件）" if dry_run else "✍️  写入模式"
    print(f"🚀 两行注释注入（路径 + 北京时间）—— {project_root}")
    print(f"   目标：{len(files)} 个源文件 | {mode} | {'强制刷新' if force else '幂等跳过'}")
    print()

    if not files:
        print("ℹ️  当前目录未找到 .py / .qml 文件。")
        return

    results: list[dict] = []
    for path in files:
        result = process_file(
            path=path,
            root=project_root,
            dry_run=dry_run,
            force=force,
        )
        results.append(result)

    _print_report(results)

    if any(r["status"] == "failed" for r in results):
        raise SystemExit(1)
