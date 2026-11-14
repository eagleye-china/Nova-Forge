# src/nova_forge/cli.py

import argparse
from pathlib import Path

from .core.packager import run_package  # 对应 pypi
from .core.releaser import run_publish, run_git_only  # 对应 publish 和 git
from .core.scaffolder import run_scaffolder
from .core.tree_builder import run_tree_builder


def main():
    parser = argparse.ArgumentParser(description="Nova-Forge: 企业级项目锻造炉")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 命令 1: 初始化配置
    subparsers.add_parser("init", help="初始化项目配置文件 (pyproject, README, LICENSE 等)")

    # 命令 2: 根据 txt 生成目录树
    tree_parser = subparsers.add_parser("tree", help="根据 project_structure.txt 生成项目目录")
    tree_parser.add_argument("-f", "--file", default="project_structure.txt", help="指定结构树文件")

    # 命令 3: 联动发版 (原版 publish，高手最爱)
    pub_parser = subparsers.add_parser("publish", help="⭐ 高手专属：一键提交、推 GitHub、打 Tag 并触发 Actions 自动发版")
    pub_parser.add_argument(
        "-m", "--message", default=None,
        help="Git commit 信息（留空则自动生成 chore(release): vX.Y.Z）",
    )

    # 命令 4: 纯净 Git 推送 (新增)
    git_parser = subparsers.add_parser("git", help="纯 Git 推送：仅提交代码并打 Tag 推送 GitHub")
    git_parser.add_argument(
        "-m", "--message", default=None,
        help="Git commit 信息（留空则自动生成 chore(release): vX.Y.Z）",
    )

    # 命令 5: 纯本地传 PyPI (原 build)
    subparsers.add_parser("pypi", help="纯本地发版：一键清理、打包、校验并直传 PyPI")

    args = parser.parse_args()

    if args.command == "init":
        run_scaffolder()
    elif args.command == "tree":
        run_tree_builder(Path(args.file))
    elif args.command == "publish":
        run_publish(args.message)
    elif args.command == "git":
        run_git_only(args.message)
    elif args.command == "pypi":
        run_package()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
