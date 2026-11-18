# src/nova_forge/core/cmd_git.py

from ._runner import run
from utils.project_meta import get_project_info


def run_git_only(commit_msg: str | None = None):
    """🐙 纯 Git 推送:仅提交代码并推 Tag，不处理复杂的联动和 rebase"""
    github_user, repo_name, project_name, version = get_project_info()
    tag_name = f"v{version}"

    if not commit_msg:
        commit_msg = f"chore(release): {tag_name}"

    print(f"🚀 开始纯净 Git 推送【{project_name}】 (v{version})...")
    print(f"📦 关联仓库: {github_user}/{repo_name}")

    run(["git", "add", "."])
    run(["git", "commit", "-m", commit_msg], ignore_error=True)
    run(["git", "push", "origin", "main"])

    tags = run(["git", "tag"]).stdout.split()
    if tag_name not in tags:
        run(["git", "tag", tag_name])
        print(f"✅ 标签 {tag_name} 创建成功。")
    else:
        print(f"⚠️ 标签 {tag_name} 已存在，将直接推送。")

    run(["git", "push", "origin", tag_name])
    print("\n🎉 Git 推送成功！")