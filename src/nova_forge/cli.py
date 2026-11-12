import argparse
from pathlib import Path

from .core.scaffolder import run_scaffolder
from .core.tree_builder import run_tree_builder


def main():
    parser = argparse.ArgumentParser(description="Nova-Forge: 企业级项目锻造炉")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 命令 1: 初始化配置 (原来的 nova_forge)
    subparsers.add_parser("init", help="初始化项目配置文件 (pyproject, README, LICENSE 等)")

    # 命令 2: 根据 txt 生成目录树 (原来的 nova_tree)
    tree_parser = subparsers.add_parser("tree", help="根据 project_structure.txt 生成项目目录")
    tree_parser.add_argument("-f", "--file", default="project_structure.txt", help="指定结构树文件")

    args = parser.parse_args()

    if args.command == "init":
        run_scaffolder()
    elif args.command == "tree":
        run_tree_builder(Path(args.file))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
