# src/nova_forge/cli.py
# 创建时间：星期二 2026-11-24 21:39

import argparse
import importlib
import sys
from pathlib import Path

from . import __version__
from .command.cmd_apk import run_apk_build_interactive
from .command.cmd_comment import run_comment
from .command.cmd_git import run_git_only
from .command.cmd_migrate import run_migrate
from .command.cmd_prescript import run_prescript, run_prescript_gui
from .command.cmd_prompt import run_prompt
from .command.cmd_publish import run_publish
from .command.cmd_pypi import run_package
from .command.cmd_renamer import run_renamer
from .command.cmd_scaffolder import run_scaffolder
from .command.cmd_tree import run_tree_builder


def _gui_runner(module_name: str, func_name: str):
    """延迟加载 GUI 命令，避免未安装 PySide6 时整个 CLI 无法启动。"""
    def _run() -> None:
        try:
            module = importlib.import_module(f".command.{module_name}", __package__)
        except ModuleNotFoundError as exc:
            if exc.name == "PySide6":
                print(
                    "❌ 该命令需要 PySide6，请先安装：pip install 'nova-forge[gui]'",
                    file=sys.stderr,
                )
                raise SystemExit(2) from exc
            raise
        getattr(module, func_name)()

    return _run


def run_icons(args=None):
    """延迟加载 icons GUI 命令，透传 --project 项目根。"""
    project_root = getattr(args, "project", None) if args is not None else None
    try:
        module = importlib.import_module(".command.cmd_icons", __package__)
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            print(
                "❌ 该命令需要 PySide6，请先安装：pip install 'nova-forge[gui]'",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc
        raise
    module.run_icons(project_root=project_root)


run_clip_saver = _gui_runner("cmd_saver", "run_clip_saver")


def main():
    parser = argparse.ArgumentParser(description="Nova-Forge: 企业级项目锻造炉")
    parser.add_argument(
        "-v", "--version", action="version", version=f"nova-forge {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 命令 1: 交互式脚手架（--project 显式绝对路径可跳过路径询问）
    p_scaffold = subparsers.add_parser(
        "scaffold", help="🏗️ 交互式创建全新的桌面端/移动端项目"
    )
    p_scaffold.add_argument(
        "-p", "--project", default=None,
        help="项目完整绝对路径；不指定时交互要求用户输入",
    )
    p_scaffold.set_defaults(func=lambda a: run_scaffolder(a.project))

    # 命令 2: 项目重命名
    p_rename = subparsers.add_parser(
        "rename", help="🔄 一键重命名项目文件夹、包名与全局依赖引用"
    )
    p_rename.set_defaults(func=lambda _: run_renamer())

    # 命令 3: 根据 txt 生成目录树
    p_tree = subparsers.add_parser(
        "tree", help="🌲 根据 project_structure.txt 生成项目目录"
    )
    p_tree.add_argument(
        "-f", "--file", default="project_structure.txt", help="指定结构树文件"
    )
    p_tree.add_argument(
        "--sync",
        action="store_true",
        help="🔄 反向同步：扫描当前磁盘结构并覆盖 TXT 文件",
    )
    p_tree.set_defaults(func=lambda args: run_tree_builder(Path(args.file), args.sync))
    # 命令 4: 联动发版
    p_publish = subparsers.add_parser(
        "publish", help="⭐ 一键提交、推 GitHub、打 Tag 并触发 Actions 自动发版"
    )
    p_publish.add_argument("-m", "--message", default=None, help="Git commit 信息（显式指定，优先级最高）")
    p_publish.add_argument(
        "-F", "--feature", default=None,
        help="本次提交的功能描述，自动生成 `feat: 描述` 提交信息",
    )
    p_publish.set_defaults(func=lambda args: run_publish(args.message, args.feature))

    # 命令 5: 纯 Git 推送
    p_git = subparsers.add_parser(
        "git", help="🐙 纯 Git 推送：仅提交代码并打 Tag 推送 GitHub"
    )
    p_git.add_argument("-m", "--message", default=None, help="Git commit 信息（显式指定，优先级最高）")
    p_git.add_argument(
        "-F", "--feature", default=None,
        help="本次提交的功能描述，自动生成 `feat: 描述` 提交信息",
    )
    p_git.set_defaults(func=lambda args: run_git_only(args.message, args.feature))

    # 命令 6: 纯本地传 PyPI
    p_pypi = subparsers.add_parser(
        "pypi", help="📦 纯本地发版：一键清理、打包、校验并直传 PyPI"
    )
    p_pypi.set_defaults(func=lambda _: run_package())

    # 命令 7: 一键 APK 打包
    p_apk = subparsers.add_parser(
        "apk", help="📱 自动化打包：将项目移交 WSL 2 一键编译生成 Android APK"
    )
    p_apk.set_defaults(func=lambda _: run_apk_build_interactive())

    # 命令 8: 多文件剪贴板保存工具
    p_saver = subparsers.add_parser("saver", help="📋 启动多文件剪贴板保存工具 (GUI)")
    p_saver.set_defaults(func=lambda _: run_clip_saver())

    # 命令 9: 新会话提示词（含快照，粘贴即存盘并复制）
    p_prompt = subparsers.add_parser(
        "prompt", help="📝 粘贴含快照的新会话提示词，一步存盘并复制到剪贴板"
    )
    p_prompt.set_defaults(func=lambda _: run_prompt())

    # 命令 10: 图标资产管理工具（在哪个项目执行就扫哪个项目）
    p_icons = subparsers.add_parser("icons", help="🎨 启动图标资产管理工具 (GUI)")
    p_icons.add_argument(
        "-p", "--project", default=None,
        help="要扫描的项目根目录（默认当前工作目录所在项目）",
    )
    p_icons.set_defaults(func=run_icons)

    # 命令 11: 源码档案头注入
    p_comment = subparsers.add_parser(
        "comment", help="📝 一键为当前目录的 .py/.qml 加两行注释（路径 + 北京时间）"
    )
    p_comment.add_argument(
        "-r", "--root", default=".", help="项目根目录（默认当前目录）"
    )
    p_comment.add_argument(
        "--dry-run", action="store_true", help="仅预览将改动的文件，不写入"
    )
    p_comment.add_argument(
        "--force", action="store_true", help="刷新创建时间为本次执行时刻的北京时间"
    )
    p_comment.add_argument(
        "--ext", default="all", choices=["all", "py", "qml"], help="只处理指定扩展名"
    )
    p_comment.set_defaults(
        func=lambda a: run_comment(a.root, a.dry_run, a.force, a.ext)
    )

    # 命令 12: 配方孵化（NovaIncubator 七槽 + 九类组合根）
    p_prescript = subparsers.add_parser(
        "prescript", help="🧬 用 NovaIncubator 一键孵化九类企业级应用"
    )
    p_prescript.add_argument(
        "-k", "--kind", default=None,
        help="配方：agent / copilot / de / orbit / desktop / chat / mobile / flex / wizard",
    )
    p_prescript.add_argument("-p", "--path", default=None, help="目标工程目录")
    p_prescript.add_argument("-n", "--name", default=None, help="应用显示名")
    p_prescript.add_argument("--package", default=None, help="Python 包名（默认由应用名派生）")
    p_prescript.add_argument("-f", "--force", action="store_true", help="覆盖已存在的同名文件")
    p_prescript.add_argument("--dry-run", action="store_true", help="只预览，不落盘")
    p_prescript.add_argument(
        "--verify-run", action="store_true",
        help="离屏实跑刚孵化的应用（需 PySide6 + pyside-nova）",
    )
    p_prescript.add_argument("-l", "--list", action="store_true", help="列出九类配方")
    p_prescript.add_argument(
        "-g", "--gui", action="store_true",
        help="打开应用孵化器工作台 GUI（NovaIncubator 七槽 · 人工确认后落盘）",
    )
    p_prescript.add_argument(
        "--cli", action="store_true",
        help="强制走命令行交互 / 一键孵化（默认已为 GUI 主窗口）",
    )

    def _dispatch_prescript(a) -> int:
        """执行 `nova-forge prescript` 即打开主窗口；带参数时保留 CLI 一键孵化。

        - 无参数 / -g --gui  → GUI 主窗口（用户规格，T11）
        - --cli              → 显式命令行交互模式
        - 其余任一孵化参数   → T4 已交付的 CLI 一键孵化
        """
        cli_args_given = any(
            (a.kind, a.path, a.name, a.package,
             a.force, a.dry_run, a.list, a.verify_run)
        )
        if not a.cli and (a.gui or not cli_args_given):
            return run_prescript_gui()
        return run_prescript(
            kind=a.kind,
            path=a.path,
            name=a.name,
            package=a.package,
            force=a.force,
            dry_run=a.dry_run,
            list_only=a.list,
            verify_run=a.verify_run,
        )

    p_prescript.set_defaults(func=lambda a: sys.exit(_dispatch_prescript(a)))

    # 命令 13: T3 迁移助手（CSA 2026-11-28 更名 migrate2nova；旧名保留为隐藏 alias）
    p_migrate = subparsers.add_parser(
        "migrate2nova",
        aliases=["migrate_to_nova"],
        help="🔄 一键 QtWidgets → pyside-nova 迁移助手（默认 dry-run）",
    )
    p_migrate.add_argument(
        "-p", "--path", default=".", help="目标工程目录 / 单个 .py 文件"
    )
    p_migrate.add_argument(
        "--api", default=None,
        help="API 冻结面 JSON 路径（默认自动探测同级 pyside-nova/api/ 最新版本）",
    )
    p_migrate.add_argument(
        "--scaffold", action="store_true",
        help="写新文件（Main.qml / main.py / MIGRATION_TODO.md / JSON 报告）；默认 dry-run",
    )
    p_migrate.add_argument(
        "--out", default=None, help="产物目录（默认 <path>/nova_migration/）"
    )
    p_migrate.add_argument(
        "--force", action="store_true", help="覆盖已存在的产物（写盘前自动备份）"
    )
    p_migrate.add_argument(
        "--json", action="store_true", help="输出机器可读 JSON 报告"
    )
    p_migrate.add_argument(
        "--entry-args", default=None, metavar="JSON",
        help="降级入口构造参数（JSON 数组，如 '[\".\"]'）",
    )
    p_migrate.add_argument(
        "--qml-root", default=None, help="qmllint 的 QML import 根（可选）"
    )
    p_migrate.add_argument(
        "--list-mapping", action="store_true", help="列出映射规则并校验冻结面零悬空"
    )
    p_migrate.add_argument(
        "--restore", default=None, metavar="ID", help="按备份 id 回滚产物"
    )
    p_migrate.add_argument(
        "--list-backups", action="store_true", help="列出 §9.3 临时备份"
    )
    p_migrate.add_argument(
        "--clean-backups", action="store_true", help="清场全部临时备份（自建自删）"
    )
    p_migrate.set_defaults(func=lambda a: sys.exit(run_migrate(a)))

    # ==========================================
    # 🎯 极简路由分发
    # ==========================================

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
