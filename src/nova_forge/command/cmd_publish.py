# src/nova_forge/command/cmd_publish.py
# 创建时间：星期二 2026-11-24 21:39

from ..utils.project_meta import ensure_origin, get_project_info
from ._runner import run
from .cmd_git import _push_or_die, build_commit_message


def run_publish(commit_msg: str | None = None, feature: str | None = None):
    """⭐ 高手专属:一键提交、同步、推 GitHub、打 Tag 触发 Actions"""
    github_user, repo_name, project_name, version = get_project_info()
    tag_name = f"v{version}"

    message = build_commit_message(tag_name, commit_msg, feature)

    print(f"🚀 开始自动提交流水线【{project_name}】 (v{version})...")
    print(f"📦 关联仓库: {github_user}/{repo_name}")
    print(f"💬 提交信息: {message}")

    # 自愈：确保 origin 存在且指向目标仓库（工作区重置后常丢失）
    remote_url = ensure_origin(github_user, repo_name)
    print(f"🔗 远程地址: {remote_url}")

    run(["git", "add", "."])
    run(["git", "commit", "-m", message], ignore_error=True)
    print("🔄 正在同步远程仓库最新变更...")
    # pull --rebase 失败同样给可读诊断（常见于首次推送 / 历史分叉）
    try:
        run(["git", "pull", "--rebase", "origin", "main"], ignore_error=True)
    except RuntimeError:
        pass
    _push_or_die(["git", "push", "origin", "main"], "推送 main 分支")

    tags = run(["git", "tag"]).stdout.split()
    if tag_name not in tags:
        run(["git", "tag", tag_name])
        print(f"✅ 标签 {tag_name} 创建成功。")
    else:
        print(f"⚠️ 标签 {tag_name} 已存在，将直接推送。")

    _push_or_die(["git", "push", "origin", tag_name], f"推送标签 {tag_name}")
    print("\n🎉 推送成功！请前往 GitHub Actions 查看自动发版流水线！")
