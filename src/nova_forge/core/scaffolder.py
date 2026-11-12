# src/nova_forge/core/scaffolder.py
import datetime
import os
from string import Template

# ✅ 从 templates.py 导入所有模版
from .templates import (
    DEFAULT_GITHUB_USER, DEFAULT_REAL_NAME, DEFAULT_DESC_EN, DEFAULT_DESC_ZH, DEFAULT_DEPS,
    PYPROJECT_TMPL, LICENSE_TMPL, README_EN_TMPL, README_ZH_TMPL,
    CHANGELOG_TMPL, INIT_PY_TMPL, WORKFLOW_TMPL, GITIGNORE_TMPL,
    INIT_GIT_TMPL, BUILD_PROD_TMPL, CB
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
        """通用写文件函数"""
        ctx = {**context, **(custom_context or {})}
        content = Template(tmpl_string).safe_substitute(ctx)
        path = Template(path).safe_substitute(ctx)

        if not path.endswith("/"):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        else:
            os.makedirs(path, exist_ok=True)

        if not path.endswith("/"):
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 已生成: {path}")

    # 2. 执行生成
    write_file("pyproject.toml", PYPROJECT_TMPL)
    write_file("LICENSE", LICENSE_TMPL)
    write_file("README.md", README_EN_TMPL)
    write_file("README_zh.md", README_ZH_TMPL)
    write_file("CHANGELOG.md", CHANGELOG_TMPL)
    write_file(".gitignore", GITIGNORE_TMPL)

    # 骨架文件
    os.makedirs("src", exist_ok=True)
    write_file("src/$MODULE_NAME/__init__.py", INIT_PY_TMPL)

    # 工具脚本
    write_file("init_git.py", INIT_GIT_TMPL)
    write_file("build_prod.bat", BUILD_PROD_TMPL)
    write_file(".github/workflows/publish.yml", WORKFLOW_TMPL)

    # 空的 project_structure.txt
    with open("project_structure.txt", "w", encoding="utf-8") as f:
        pass
    print("✅ 已生成: project_structure.txt (空文件)")

    print("\n🎉 企业级全家桶生成完毕！")
    print("👉 已包含：动态版本号、CHANGELOG、GitHub Actions 自动发版！")
