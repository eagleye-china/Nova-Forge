# src/nova_forge/command/cmd_git.py
# 创建时间：星期二 2026-11-24 21:39

import sys

from ..utils.project_meta import ensure_origin, get_project_info
from ._runner import run


def _push_or_die(cmd: list[str], what: str) -> None:
    """执行 push，失败时给可读诊断而非裸 traceback，干净地非零退出。"""
    try:
        run(cmd)
    except RuntimeError as exc:
        detail = str(exc)
        print(f"\n❌ {what}失败。排查提示：", file=sys.stderr)
        if "Could not read from remote" in detail or "does not appear" in detail:
            print("   · 仓库地址不可达：确认网络 / GitHub 权限（SSH key 或 HTTPS 凭证）", file=sys.stderr)
        elif "non-fast-forward" in detail or "rejected" in detail.lower():
            print("   · 本地与远程历史分叉：需先 rebase/merge，或由你确认强推策略", file=sys.stderr)
        elif "Permission denied" in detail or "403" in detail:
            print("   · 权限不足：确认账号对仓库有 push 权限", file=sys.stderr)
        print(f"   · 原始错误：{detail}", file=sys.stderr)
        raise SystemExit(1) from None


def build_commit_message(
    tag_name: str, commit_msg: str | None = None, feature: str | None = None
) -> str:
    """生成 commit 信息。

    优先级：显式 -m > --feature > 默认 release 信息。
    --feature 会自动补 Conventional Commits 的 `feat: ` 前缀；
    若用户已自带 `feat:` / `feat(...)` 前缀则不重复添加。
    """
    if commit_msg and commit_msg.strip():
        return commit_msg.strip()
    if feature and feature.strip():
        text = feature.strip()
        if text.lower().startswith(("feat:", "feat(")):
            return text
        return f"feat: {text}"
    return f"chore(release): {tag_name}"


def run_git_only(commit_msg: str | None = None, feature: str | None = None):
    """🐙 纯 Git 推送:仅提交代码并推 Tag，不处理复杂的联动和 rebase"""
    github_user, repo_name, project_name, version = get_project_info()
    tag_name = f"v{version}"

    message = build_commit_message(tag_name, commit_msg, feature)

    print(f"🚀 开始纯净 Git 推送【{project_name}】 (v{version})...")
    print(f"📦 关联仓库: {github_user}/{repo_name}")
    print(f"💬 提交信息: {message}")

    # 自愈：确保 origin 存在且指向目标仓库（工作区重置后常丢失）
    remote_url = ensure_origin(github_user, repo_name)
    print(f"🔗 远程地址: {remote_url}")

    run(["git", "add", "."])
    run(["git", "commit", "-m", message], ignore_error=True)
    _push_or_die(["git", "push", "origin", "main"], "推送 main 分支")

    tags = run(["git", "tag"]).stdout.split()
    if tag_name not in tags:
        run(["git", "tag", tag_name])
        print(f"✅ 标签 {tag_name} 创建成功。")
    else:
        print(f"⚠️ 标签 {tag_name} 已存在，将直接推送。")

    _push_or_die(["git", "push", "origin", tag_name], f"推送标签 {tag_name}")
    print("\n🎉 Git 推送成功！")
