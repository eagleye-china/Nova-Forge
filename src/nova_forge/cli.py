# src/nova_forge/cli.py

import argparse
from pathlib import Path

from .core.cmd_scaffolder import run_scaffolder
from .core.cmd_renamer import run_renamer
from .core.cmd_tree import run_tree_builder
from .core.cmd_pypi import run_package
from .core.cmd_publish import run_publish
from .core.cmd_git import run_git_only
from .core.cmd_apk import run_apk_build_interactive
from .core.cmd_saver import run_clip_saver


def main():
    parser = argparse.ArgumentParser(description="Nova-Forge: 企业级项目锻造炉")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 命令 1: 交互式脚手架
    p_scaffold = subparsers.add_parser(
        "scaffold", help="🏗️ 交互式创建全新的桌面端/移动端项目"
    )
    # 🌟 用 lambda 接收 args 并忽略
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
    # 🌟 使用带参数的 lambda
    p_tree.set_defaults(func=lambda args: run_tree_builder(Path(args.file)))

    # 命令 4: 联动发版
    p_publish = subparsers.add_parser(
        "publish", help="⭐ 一键提交、推 GitHub、打 Tag 并触发 Actions 自动发版"
    )
    p_publish.add_argument("-m", "--message", default=None, help="Git commit 信息")
    p_publish.set_defaults(func=lambda args: run_publish(args.message))

    # 命令 5: 纯 Git 推送
    p_git = subparsers.add_parser(
        "git", help="🐙 纯 Git 推送：仅提交代码并打 Tag 推送 GitHub"
    )
    p_git.add_argument("-m", "--message", default=None, help="Git commit 信息")
    p_git.set_defaults(func=lambda args: run_git_only(args.message))

    # 命令 6: 纯本地传 PyPI
    p_pypi = subparsers.add_parser(
        "pypi", help="📦 纯本地发版：一键清理、打包、校验并直传 PyPI"
    )
    # 🌟 同样加 lambda 忽略 args
    p_pypi.set_defaults(func=lambda _: run_package())

    # 命令 7: 一键 APK 打包
    p_apk = subparsers.add_parser(
        "apk", help="📱 自动化打包：将项目移交 WSL 2 一键编译生成 Android APK"
    )
    p_apk.set_defaults(func=lambda _: run_apk_build_interactive())

    # 命令 8: 多文件剪贴板保存工具
    p_saver = subparsers.add_parser("saver", help="📋 启动多文件剪贴板保存工具 (GUI)")
    p_saver.set_defaults(func=lambda _: run_clip_saver())

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