# src/nova_forge/cli.py
# 星期二 2026-11-24 13:16

import argparse
import importlib
import sys
from pathlib import Path

from . import __version__
from .command.cmd_apk import run_apk_build_interactive
from .command.cmd_git import run_git_only
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


run_icons = _gui_runner("cmd_icons", "run_icons")
run_clip_saver = _gui_runner("cmd_saver", "run_clip_saver")


def main():
    parser = argparse.ArgumentParser(description="Nova-Forge: 企业级项目锻造炉")
    parser.add_argument(
        "-v", "--version", action="version", version=f"nova-forge {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 命令 1: 交互式脚手架
    p_scaffold = subparsers.add_parser(
        "scaffold", help="🏗️ 交互式创建全新的桌面端/移动端项目"
    )
    p_scaffold.set_defaults(func=lambda _: run_scaffolder())

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

    # 命令 10: 图标资产管理工具
    p_icons = subparsers.add_parser("icons", help="🎨 启动图标资产管理工具 (GUI)")
    p_icons.set_defaults(func=lambda _: run_icons())

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
