# src/nova_forge/core/scaffolder.py

import datetime
from pathlib import Path
from string import Template

from .templates import (
    CB,
    CHANGELOG_TMPL,
    DEFAULT_DEPS,
    DEFAULT_DESC_EN,
    DEFAULT_DESC_ZH,
    DEFAULT_GITHUB_USER,
    DEFAULT_REAL_NAME,
    GITIGNORE_TMPL,
    HOW_TO_PUBLISH_TMPL,
    INIT_PY_TMPL,
    LICENSE_TMPL,
    MOBILE_MAIN_PY_TMPL,
    MOBILE_MAIN_QML_TMPL,
    PYPROJECT_TMPL,
    README_EN_TMPL,
    README_ZH_TMPL,
    WORKFLOW_TMPL,
)


def ask(prompt, default):
    res = input(f"{prompt} [{default}]: ").strip()
    return res if res else default


def run_scaffolder():
    print("\n🔥 欢迎使用 Nova-Forge 终极项目锻造炉")
    print("=" * 60)

    # 1. 先问路径 (符合直觉)
    target_dir_str = ask("📂 项目完整绝对路径 (如 D:\\Projects\\AluBrain-Copilot)", "")
    if not target_dir_str:
        print("❌ 错误: 必须提供项目根目录路径！")
        return

    target_root = Path(target_dir_str).resolve()

    # 自动从路径提取项目名
    folder_name = target_root.name
    if not folder_name:
        print("❌ 错误: 无效的项目路径！")
        return

    force_overwrite = False
    # 🚨 安全校验：发现非空目录时，让用户决定如何处理
    if target_root.exists() and any(target_root.iterdir()):
        print(f"\n⚠️  警告: 目录 {target_root} 已存在且非空！")
        print("请选择如何处理已存在的同名文件：")
        print("  [Y] 跳过：保留原文件，仅补充生成缺失的文件")
        print("  [N] 覆盖：强制覆盖所有同名文件（请谨慎）")
        print("  [C] 取消：退出当前操作")
        action = ask("你的选择 (Y/N/C)", "Y").upper()

        if action == "C":
            print("❌ 操作已取消。")
            return
        elif action == "N":
            force_overwrite = True
            print("⚠️  已启用【覆盖模式】，同名文件将被重写！")
        else:
            print("✅ 已启用【跳过模式】，同名文件将被安全保留。")

    # 2. 再问应用类型
    app_type = ask("🖥️ 应用类型 (1: 桌面端, 2: 移动端)", "1")
    is_mobile = (app_type == "2")

    # ✅ 智能默认值：全部由 folder_name 派生
    default_project_name = folder_name.lower().replace(" ", "-").replace("_", "-")
    default_repo_name = folder_name.replace(" ", "")
    module_name = folder_name.lower().replace("-", "_").replace(" ", "_")

    if is_mobile:
        default_desc_en = "A stunning, GPU-accelerated mobile application for PySide6."
        default_desc_zh = "基于 PySide6 和 QML 打造的炫酷移动端应用框架。"
    else:
        default_desc_en = DEFAULT_DESC_EN
        default_desc_zh = DEFAULT_DESC_ZH

    print(f"\n✨ 识别到项目名: {folder_name} (包名将自动设为: {default_project_name})")

    project_name = ask("📦 PyPI 包名 (如 alubrain-copilot)", default_project_name)
    repo_name = ask("📁 GitHub 仓库名 (如 AluBrain-Copilot)", default_repo_name)
    github_user = ask("👤 GitHub 用户名", DEFAULT_GITHUB_USER)
    real_name = ask("✍️ 真实姓名 (用于 LICENSE)", DEFAULT_REAL_NAME)
    desc_en = ask("🇬🇧 英文描述", default_desc_en)
    desc_zh = ask("🇨🇳 中文描述", default_desc_zh)

    year = datetime.datetime.now().year
    month = datetime.datetime.now().strftime("%m")
    day = datetime.datetime.now().strftime("%d")

    # 用于注入的全局字典
    context = {
        "PROJECT_NAME": project_name,
        "REPO_NAME": repo_name,
        "GITHUB_USER": github_user,
        "REAL_NAME": real_name,
        "DESC_EN": desc_en,
        "DESC_ZH": desc_zh,
        "YEAR": year,
        "MONTH": month,
        "DAY": day,
        "MODULE_NAME": module_name,
        "DEPS": DEFAULT_DEPS,
        "CB": CB
    }

    def write_file(rel_path, tmpl_string, custom_context=None):
        """通用写文件函数：解析路径变量，写入目标根目录"""
        ctx = {**context, **(custom_context or {})}

        # 替换路径中的变量
        parsed_path = Template(rel_path).safe_substitute(ctx)
        full_path = target_root / parsed_path

        # 🚨 核心修复：如果传入的 tmpl_string 是空字符串 ""，代表要创建的是目录！
        if tmpl_string == "":
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 已创建目录: {full_path.relative_to(target_root)}/")
            except Exception as e:  # noqa
                print(f"❌ 目录创建失败 {full_path}: {e}")
            return

        # 否则，它绝对是一个文件！
        if full_path.exists() and not force_overwrite:
            print(f"⏭️ 已存在，安全跳过: {full_path.relative_to(target_root)}")
            return

        # 替换文件内容
        content = Template(tmpl_string).safe_substitute(ctx)

        # 写入文件
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            if full_path.exists() and force_overwrite:
                print(f"📄 已覆盖生成: {full_path.relative_to(target_root)}")
            else:
                print(f"📄 已生成: {full_path.relative_to(target_root)}")
        except Exception as e:  # noqa: BLE001
            print(f"❌ 写入失败 {parsed_path}: {e}")

    print("\n🚀 开始锻造企业级项目骨架...\n")

    # 3. 生成公共配置与文档
    write_file("pyproject.toml", PYPROJECT_TMPL)
    write_file("LICENSE", LICENSE_TMPL)
    write_file(".gitignore", GITIGNORE_TMPL)
    write_file("README.md", README_EN_TMPL)
    write_file("README_zh.md", README_ZH_TMPL)
    write_file("CHANGELOG.md", CHANGELOG_TMPL)
    write_file("HOW_TO_PUBLISH.md", HOW_TO_PUBLISH_TMPL)
    write_file(".github/workflows/publish.yml", WORKFLOW_TMPL)

    # 4. 差异化生成骨架结构
    if not is_mobile:
        # === 桌面端布局 ===
        write_file("src/$MODULE_NAME/__init__.py", INIT_PY_TMPL)
        write_file("src/$MODULE_NAME/main.py", '"""Desktop entry point."""\nimport sys\n# 桌面端代码...')
        write_file("src/$MODULE_NAME/qml/main.qml", '// Desktop QML template...')
        write_file("src/$MODULE_NAME/ui", "")
        write_file("src/$MODULE_NAME/utils", "")
        write_file("tests", "")
        print("🖥️  已生成【桌面端】专属 src 布局。")
    else:
        # === 移动端布局 ===
        write_file("src/$MODULE_NAME/__init__.py", INIT_PY_TMPL)
        write_file("src/$MODULE_NAME/main.py", MOBILE_MAIN_PY_TMPL)
        write_file("src/$MODULE_NAME/qml/main.qml", MOBILE_MAIN_QML_TMPL)
        print("📱 已生成【移动端】专属 src 布局。")

    # 默认生成空的 project_structure.txt 便于后续 tree 指令
    if not (target_root / "project_structure.txt").exists():
        (target_root / "project_structure.txt").touch()
        print("📄 已生成: project_structure.txt (空文件)")

    print("\n" + "=" * 60)
    print(f"🎉 项目【{project_name}】锻造完毕！")
    print(f"👉 请执行以下命令开始开发：")
    print(f"   cd {target_root}")
    print(f"   pip install -e .")
    print("\n⚠️  [重要提醒] 为了让自动发版流水线生效，请前往 PyPI 绑定项目：")
    print(f"   Project Name: {project_name}")
    print(f"   Owner:        {github_user}")
    print(f"   Repository:   {repo_name}")
    print(f"   Workflow:     publish.yml")
    print(f"   Environment:  pypi")
    print("=" * 60 + "\n")
