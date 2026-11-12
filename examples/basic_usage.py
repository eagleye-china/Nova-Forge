# -*- coding: utf-8 -*-
# examples/basic_usage.py

"""
Nova-Forge 编程式调用示例。

虽然在真实场景下，我们通常直接在终端使用 `nova-forge init`，
但如果你想在 Python 脚本中自动化调用，可以参考以下写法。
"""
from pathlib import Path

from nova_forge.core.tree_builder import run_tree_builder


def main():
    print("🚀 这是一个编程式调用的示例。")

    # 示例 1: 调用脚手架（注意：这会触发交互式提问）
    # run_scaffolder()

    # 示例 2: 通过代码直接生成目录树
    # 假设你在当前目录下有一个 my_tree.txt，里面写好了目录结构
    tree_file = Path("my_tree.txt")
    if tree_file.exists():
        print(f"发现 {tree_file.name}，开始生成目录...")
        run_tree_builder(tree_file)
    else:
        print("💡 提示：请先创建一个 my_tree.txt 填入树形结构，然后再运行此脚本。")


if __name__ == "__main__":
    main()
