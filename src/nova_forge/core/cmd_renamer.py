# src/nova_forge/core/cmd_renamer.py

import os
import re
from pathlib import Path
from ..utils.project_meta import read_project_meta


def ask(prompt, default):
    res = input(f"{prompt} [{default}]: ").strip()
    return res if res else default


def run_renamer():
    print("\n🔄 欢迎使用 Nova-Forge 项目重命名引擎")
    print("=" * 60)

    # 1. 输入旧路径
    old_path_str = ask(
        "📂 原项目完整绝对路径 (如 D:\\Projects\\Nova-Mobile)", str(Path.cwd())
    )
    old_root = Path(old_path_str).resolve()

    if not (old_root / "pyproject.toml").exists():
        print("❌ 错误: 未找到 pyproject.toml，这可能不是一个标准项目！")
        return

    # 2. 读取旧信息
    try:
        old_pypi_name, _ = read_project_meta(old_root)
    except Exception as e:
        print(f"❌ 无法读取项目信息: {e}")
        return

    old_module = old_pypi_name.replace("-", "_")
    old_src_pkg = old_root / "src" / old_module

    if not old_src_pkg.exists():
        print(f"❌ 错误: 在 src/ 下找不到包目录 {old_module}")
        return

    # 3. 输入新名称
    new_name = ask("🆕 新的项目名称 (如 Nova-Copilot)", old_root.name)
    if new_name == old_root.name:
        print("⏭️ 项目名称未改变，已取消操作。")
        return

    new_pypi_name = new_name.lower().replace(" ", "-").replace("_", "-")
    new_module = new_pypi_name.replace("-", "_")

    # 推导新路径（在同一个父目录下）
    new_root = old_root.parent / new_name

    print(f"\n⚠️  即将执行以下操作:")
    print(f"  1. 根文件夹: {old_root.name} -> {new_name}")
    print(f"  2. PyPI 包名: {old_pypi_name} -> {new_pypi_name}")
    print(f"  3. Python 模块: src/{old_module} -> src/{new_module}")
    print(f"  4. 自动替换所有代码文件中的旧名称引用")

    confirm = ask("确认执行重命名吗？(y/N)", "N").lower()
    if confirm != "y":
        print("❌ 操作已取消。")
        return

    # ================= 开始执行 =================

    # 4. 重命名根文件夹
    print("\n🚀 [1/3] 正在重命名根文件夹...")
    try:
        old_root.rename(new_root)
        print(f"✅ 根文件夹已重命名为: {new_name}")
    except Exception as e:
        print(f"❌ 根文件夹重命名失败: {e}")
        print("💡 提示:如果你的终端当前正处于该目录，请先 cd 退出去再执行！")
        return

    # 更新路径引用，后面都在新文件夹里操作
    old_src_pkg = new_root / "src" / old_module
    new_src_pkg = new_root / "src" / new_module

    # 5. 重命名 src 下的模块包
    print("\n🚀 [2/3] 正在重命名 Python 模块...")
    try:
        old_src_pkg.rename(new_src_pkg)
        print(f"✅ 模块目录已重命名: src/{new_module}")
    except Exception as e:
        print(f"❌ 模块重命名失败: {e}")
        return

    # 6. 全局文本替换
    print("\n🚀 [3/3] 正在全局扫描并替换文件内容...")

    ignore_dirs = {
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "dist",
        "build",
        ".idea",
        ".vscode",
        ".pytest_cache",
    }
    text_exts = {
        ".py",
        ".toml",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".qml",
        ".json",
        ".xml",
    }

    count = 0
    for root, dirs, files in os.walk(new_root):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() not in text_exts and file_path.name not in {
                "LICENSE",
                ".gitignore",
            }:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                # 使用正则边界确保精准替换
                new_content = re.sub(rf"\b{old_module}\b", new_module, content)
                new_content = re.sub(rf"\b{old_pypi_name}\b", new_pypi_name, content)
                # 顺便把大驼峰/中划线的名字也替换掉 (比如 README 里的标题)
                new_content = re.sub(rf"\b{old_root.name}\b", new_name, new_content)

                if new_content != content:
                    file_path.write_text(new_content, encoding="utf-8")
                    print(f"📄 已更新: {file_path.relative_to(new_root)}")
                    count += 1
            except Exception as e:
                print(f"⚠️ 跳过无法解析的文件 {file_path.name}: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 重命名大功告成！共修改了 {count} 个文件。")
    print(f"👉 请执行以下命令继续开发:")
    print(f"   cd {new_root}")
    print(f"   pip install -e .")
    print("=" * 60 + "\n")