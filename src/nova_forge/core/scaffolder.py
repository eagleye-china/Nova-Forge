# src/nova_forge/core/scaffolder.py
import datetime
import os
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
    PYPROJECT_TMPL,
    README_EN_TMPL,
    README_ZH_TMPL,
    WORKFLOW_TMPL,
)


def ask(prompt, default):
    res = input(f"{prompt} [{default}]: ").strip()
    return res if res else default


def run_scaffolder():
    print("🔥 欢迎使用 Nova-Forge 终极项目锻造炉\n")

    # 1. 收集信息
    project_name = ask("📦 项目名 (PyPI包名, 如 nova-chat)", "my-awesome-project")
    repo_name = ask("📁 GitHub仓库名 (如 Nova-Agent)", project_name)
    github_user = ask("👤 GitHub用户名", DEFAULT_GITHUB_USER)
    real_name = ask("✍️ 真实姓名 (用于 LICENSE)", DEFAULT_REAL_NAME)
    desc_en = ask("🇬🇧 英文描述", DEFAULT_DESC_EN)
    desc_zh = ask("🇨🇳 中文描述", DEFAULT_DESC_ZH)

    year = datetime.datetime.now().year
    month = datetime.datetime.now().strftime("%m")
    day = datetime.datetime.now().strftime("%d")
    module_name = project_name.replace('-', '_')

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
        "CB": CB  # ✅ 核心：将防截断的反引号传入
    }

    def write_file(path, tmpl_string, custom_context=None):
        """通用写文件函数：非破坏性生成，存在则跳过"""
        ctx = {**context, **(custom_context or {})}
        # 先替换路径中的变量
        path = Template(path).safe_substitute(ctx)

        # 如果是目录，直接创建并返回
        if path.endswith("/"):
            try:
                os.makedirs(path, exist_ok=True)
                print(f"✅ 已生成目录: {path}")
            except Exception as e:  # noqa
                print(f"❌ 目录创建失败 {path}: {e}")
            return

        # ✅ 核心逻辑：如果文件已存在，跳过不覆盖
        if os.path.exists(path):
            print(f"⏭️ 已存在，跳过: {path}")
            return

        # 替换文件内容
        content = Template(tmpl_string).safe_substitute(ctx)

        # 写入文件（带异常保护）
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 已生成: {path}")
        except Exception as e:  # noqa: BLE001
            print(f"❌ 写入失败 {path}: {e}")

    # 2. 执行生成
    write_file("pyproject.toml", PYPROJECT_TMPL)
    write_file("LICENSE", LICENSE_TMPL)
    write_file("README.md", README_EN_TMPL)
    write_file("README_zh.md", README_ZH_TMPL)
    write_file("CHANGELOG.md", CHANGELOG_TMPL)
    write_file(".gitignore", GITIGNORE_TMPL)

    # ✅ 新增：OIDC 绑定指南
    write_file("HOW_TO_PUBLISH.md", HOW_TO_PUBLISH_TMPL)

    # 骨架文件
    os.makedirs("src", exist_ok=True)
    write_file("src/$MODULE_NAME/__init__.py", INIT_PY_TMPL)

    # CI/CD 流水线
    write_file(".github/workflows/publish.yml", WORKFLOW_TMPL)

    # ✅ 核心修复：空的 project_structure.txt 也要防止覆盖
    if not os.path.exists("project_structure.txt"):
        with open("project_structure.txt", "w", encoding="utf-8"):
            pass
        print("✅ 已生成: project_structure.txt (空文件)")
    else:
        print("⏭️ 已存在，跳过: project_structure.txt")

    print("\n🎉 企业级全家桶生成完毕！")

    # ✅ 核心：在终端打印耀眼的 OIDC 配置提示
    print("\n" + "=" * 60)
    print("⚠️  [重要提醒] 为了让自动发版流水线生效，你还需要完成最后一步：")
    print("👉 请前往 PyPI 绑定你的项目：https://pypi.org/manage/account/publishing/")
    print(f"   Project Name: {project_name}")
    print(f"   Owner:        {github_user}")
    print(f"   Repository:   {repo_name}")
    print("   Workflow:     publish.yml")
    print("   Environment:  pypi")
    print("=" * 60)
