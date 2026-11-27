# src/nova_forge/command/cmd_scaffolder.py
# 创建时间：星期二 2026-11-24 21:39

from pathlib import Path

from ..templates import (
    DEFAULT_DESC_EN,
    DEFAULT_DESC_ZH,
    DEFAULT_GITHUB_USER,
    DEFAULT_REAL_NAME,
)


def ask(prompt, default):
    res = input(f"{prompt} [{default}]: ").strip()
    return res if res else default


def write_plan(plan: dict, target_root: Path, emit, force: bool = False) -> list[str]:
    """把 scaffold_file_plan 清单逐项落盘；emit 负责单项打印。

    DIR_SENTINEL 代表目录（mkdir），其余（含空串）为文件；存在且非 force
    时安全跳过。返回实际落盘的相对路径列表（含目录），供调用方汇总。
    """

    from string import Template

    from ..core.scaffold_logic import DIR_SENTINEL

    written: list[str] = []
    for rel, text in plan.items():
        full = target_root / Template(rel).safe_substitute({})
        if text is DIR_SENTINEL:
            full.mkdir(parents=True, exist_ok=True)
            emit(f"📁 已创建目录: {rel}/")
            written.append(rel)
            continue
        if full.exists() and not force:
            emit(f"⏭️ 已存在，安全跳过: {rel}")
            continue
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(text, encoding="utf-8", newline="\n")
        emit(f"📄 {'已覆盖生成' if force and full.exists() else '已生成'}: {rel}")
        written.append(rel)
    return written


def scaffold_project(
    target_root: str | Path,
    *,
    is_mobile: bool = False,
    force: bool = False,
    quiet: bool = True,
    include_entry_py: bool = True,
    include_entry_qml: bool = True,
    include_project_structure: bool = True,
    **overrides,
) -> dict:
    """非交互入口：给定项目绝对路径，直接补齐完整工程骨架。

    prescript 确认孵化后调用本函数，把通用工程文件（LICENSE / README_zh /
    CHANGELOG / HOW_TO_PUBLISH / publish.yml / project_structure.txt）叠加到
    配方工程；同名文件已存在时安全跳过，绝不覆盖 prescript 的专属产物。

    Returns:
        ``{"ok", "written", "skipped", "root", "projectName"}`` 结构化结果。
    """
    from ..core.scaffold_logic import (
        DIR_SENTINEL,
        build_context,
        scaffold_file_plan,
    )

    root = Path(target_root).expanduser().resolve()
    plan = scaffold_file_plan(
        root, is_mobile=is_mobile, include_entry_py=include_entry_py,
        include_entry_qml=include_entry_qml,
        include_project_structure=include_project_structure, **overrides,
    )
    ctx = build_context(root, is_mobile=is_mobile, **overrides)

    def emit(msg: str) -> None:
        if not quiet:
            print(msg)

    # 目录项不参与 written/skipped 账本（每次 mkdir 都是幂等的，不算"写文件"）
    file_rel = [rel for rel, text in plan.items() if text is not DIR_SENTINEL]
    written = write_plan(plan, root, emit, force=force)
    written_files = [rel for rel in written if plan.get(rel) is not DIR_SENTINEL]
    return {
        "ok": True,
        "written": written_files,
        "skipped": [rel for rel in file_rel if rel not in written_files],
        "root": str(root),
        "projectName": ctx["PROJECT_NAME"],
    }


def run_scaffolder(project_root: str | None = None):
    print("\n🔥 欢迎使用 Nova-Forge 终极项目锻造炉")
    print("=" * 60)

    # 1. 路径：CLI --project 显式传入则跳过询问；否则要求用户输入绝对路径
    if project_root:
        target_root = Path(project_root).expanduser().resolve()
    else:
        target_dir_str = ask("📂 项目完整绝对路径 (如 D:\\Projects\\AluBrain-Copilot)", "")
        if not target_dir_str:
            print("❌ 错误: 必须提供项目根目录路径！")
            return
        target_root = Path(target_dir_str).expanduser().resolve()

    # 自动从路径提取项目名
    folder_name = target_root.name
    if not folder_name:
        print("❌ 错误: 无效的项目路径！")
        return

    force_overwrite = False
    # 🚨 安全校验:发现非空目录时，让用户决定如何处理
    if target_root.exists() and any(target_root.iterdir()):
        print(f"\n⚠️  警告: 目录 {target_root} 已存在且非空！")
        print("请选择如何处理已存在的同名文件:")
        print("  [Y] 跳过:保留原文件，仅补充生成缺失的文件")
        print("  [N] 覆盖:强制覆盖所有同名文件（请谨慎）")
        print("  [C] 取消:退出当前操作")
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

    # ✅ 智能默认值:全部由 folder_name 派生
    default_project_name = folder_name.lower().replace(" ", "-").replace("_", "-")
    default_repo_name = folder_name.replace(" ", "")

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

    print("\n🚀 开始锻造企业级项目骨架...\n")

    # 单一事实源：core.scaffold_logic 生成完整清单，交互值作为覆盖注入
    from ..core.scaffold_logic import scaffold_file_plan

    plan = scaffold_file_plan(
        target_root,
        is_mobile=is_mobile,
        project_name=project_name,
        repo_name=repo_name,
        github_user=github_user,
        real_name=real_name,
        desc_en=desc_en,
        desc_zh=desc_zh,
    )
    written = write_plan(plan, target_root, print, force=force_overwrite)
    print(f"🖥️  已生成【{'移动端' if is_mobile else '桌面端'}】专属 src 布局（{len(written)} 项）。")

    print("\n" + "=" * 60)
    print(f"🎉 项目【{project_name}】锻造完毕！")
    print("👉 请执行以下命令开始开发:")
    print(f"   cd {target_root}")
    print("   pip install -e .")
    print("\n⚠️  [重要提醒] 为了让自动发版流水线生效，请前往 PyPI 绑定项目:")
    print(f"   Project Name: {project_name}")
    print(f"   Owner:        {github_user}")
    print(f"   Repository:   {repo_name}")
    print("   Workflow:     publish.yml")
    print("   Environment:  pypi")
    print("=" * 60 + "\n")
