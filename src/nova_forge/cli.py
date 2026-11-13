# ==========================================
# File 5: src/nova_forge/cli.py
# ==========================================
import argparse
from pathlib import Path

from .core.packager import run_package
from .core.releaser import run_publish
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

    # 命令 3: 一键发布 (Git Push + Tag)
    pub_parser = subparsers.add_parser("publish", help="一键提交代码、打标签并触发 GitHub Actions 自动发版")
    pub_parser.add_argument(
        "-m", "--message", default=None,
        help="Git commit 信息（留空则自动生成 chore(release): vX.Y.Z）",
    )

    # ✅ 命令 4: 本地打包并上传 PyPI
    subparsers.add_parser("build", help="一键清理、打包、校验并上传到 PyPI (本地全自动)")

    args = parser.parse_args()

    if args.command == "init":
        run_scaffolder()
    elif args.command == "tree":
        run_tree_builder(Path(args.file))
    elif args.command == "publish":
        run_publish(args.message)
    elif args.command == "build":
        run_package()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
