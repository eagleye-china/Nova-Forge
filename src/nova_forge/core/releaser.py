# ==========================================
# File 4: src/nova_forge/core/releaser.py
# ==========================================
from ._runner import run
from .project_meta import read_github_owner, read_project_meta


def get_project_info():
    github_user, repo_name = read_github_owner()
    project_name, version = read_project_meta()
    return github_user, repo_name, project_name, version


def run_publish(commit_msg: str | None = None):
    github_user, repo_name, project_name, version = get_project_info()
    tag_name = f"v{version}"

    # 未显式传 -m 时，自动生成带版本号的默认提交信息
    if not commit_msg:
        commit_msg = f"chore(release): {tag_name}"

    print(f"🚀 开始自动提交流水线【{project_name}】 (v{version})...")
    print(f"📦 关联仓库: {github_user}/{repo_name}")
    print(f"💬 提交信息: {commit_msg}")

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
    print("\n🎉 推送成功！请前往 GitHub Actions 查看自动发版流水线！")
