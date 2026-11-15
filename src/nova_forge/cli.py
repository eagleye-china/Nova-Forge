# src/nova_forge/cli.py

import argparse
from pathlib import Path

from .core.packager import run_package
from .core.releaser import run_publish, run_git_only
from .core.scaffolder import run_scaffolder  # 交互式脚手架
from .core.renamer import run_renamer  # ✅ 新增：重命名引擎
from .core.tree_builder import run_tree_builder


def main():
    parser = argparse.ArgumentParser(description="Nova-Forge: 企业级项目锻造炉")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 命令 1: 交互式脚手架
    subparsers.add_parser("scaffold", help="🏗️ 交互式创建全新的桌面端/移动端项目")

    # ✅ 命令 2: 项目重命名
    subparsers.add_parser("rename", help="🔄 一键重命名项目文件夹、包名与全局依赖引用")

    # 命令 3: 根据 txt 生成目录树
    tree_parser = subparsers.add_parser("tree", help="根据 project_structure.txt 生成项目目录")
    tree_parser.add_argument("-f", "--file", default="project_structure.txt", help="指定结构树文件")

    # 命令 4: 联动发版
    pub_parser = subparsers.add_parser("publish", help="⭐ 高手专属：一键提交、推 GitHub、打 Tag 并触发 Actions 自动发版")
    pub_parser.add_argument("-m", "--message", default=None, help="Git commit 信息")

    # 命令 5: 纯 Git 推送
    git_parser = subparsers.add_parser("git", help="纯 Git 推送：仅提交代码并打 Tag 推送 GitHub")
    git_parser.add_argument("-m", "--message", default=None, help="Git commit 信息")

    # 命令 6: 纯本地传 PyPI
    subparsers.add_parser("pypi", help="纯本地发版：一键清理、打包、校验并直传 PyPI")

    args = parser.parse_args()

    if args.command == "scaffold":
        run_scaffolder()
    elif args.command == "rename":
        run_renamer()  # ✅ 路由分发
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
