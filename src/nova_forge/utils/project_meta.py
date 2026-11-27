# src/nova_forge/utils/project_meta.py
# 创建时间：星期二 2026-11-24 21:39

import os
import re
import subprocess
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def _resolve_dynamic_version(root: Path, data: dict) -> str | None:
    """解析 PEP 621 dynamic version（当前支持 hatchling 的 path 模式）。"""
    project = data.get("project") or {}
    if "version" not in (project.get("dynamic") or []):
        return None

    version_conf = data.get("tool", {}).get("hatch", {}).get("version", {})
    rel_path = version_conf.get("path")
    if not rel_path:
        raise ValueError(
            "pyproject.toml 声明 version 为 dynamic，"
            "但缺少 [tool.hatch.version].path，无法确定版本号。"
        )

    version_file = root / rel_path
    if not version_file.exists():
        raise FileNotFoundError(f"动态版本文件不存在：{version_file}")

    match = _VERSION_RE.search(version_file.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"未能从 {version_file} 中解析 __version__。")
    return match.group(1)


def read_project_meta(root: Path | None = None) -> tuple[str, str]:
    """返回 (项目名, 版本号)。唯一解析入口，解析失败直接抛错，绝不静默兜底。"""
    root = root or Path.cwd()
    toml_path = root / "pyproject.toml"
    if not toml_path.exists():
        raise FileNotFoundError(f"未找到 {toml_path}，无法确定版本号。")

    with open(toml_path, "rb") as f:
        data = tomllib.load(f)

    # 兼容 PEP 621 [project] 与 Poetry [tool.poetry]
    section = data.get("project") or data.get("tool", {}).get("poetry", {})
    name = section.get("name")
    version = section.get("version") or _resolve_dynamic_version(root, data)
    if not name or not version:
        raise ValueError("pyproject.toml 中缺少 name 或 version，拒绝继续发版。")
    return name, version


def read_github_owner(root: Path | None = None) -> tuple[str, str]:
    """从 git remote 解析 (owner, repo)，失败回退默认值。"""
    root = root or Path.cwd()
    fallback = ("eagleye-china", root.name)
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=root,
        )
        remote_url = result.stdout.strip()
        if "github.com" not in remote_url:
            return fallback
        if remote_url.startswith("git@"):
            parts = remote_url.split(":")[1].split("/")
        else:
            parts = remote_url.split("/")
        return parts[0] if remote_url.startswith("git@") else parts[-2], parts[
            -1
        ].replace(".git", "")
    except Exception:
        return fallback


def get_project_info(root: Path | None = None) -> tuple[str, str, str, str]:
    """统一获取当前项目的基本信息 (GitHub用户, 仓库名, 项目名, 版本号)"""
    github_user, repo_name = read_github_owner(root)
    project_name, version = read_project_meta(root)
    return github_user, repo_name, project_name, version


def _origin_url(owner: str, repo: str) -> tuple[str, str]:
    """按协议偏好构造 (ssh_url, https_url)。协议由 NOVA_GIT_PROTOCOL 决定（默认 ssh）。"""
    ssh = f"git@github.com:{owner}/{repo}.git"
    https = f"https://github.com/{owner}/{repo}.git"
    return ssh, https


def _repo_key_from_url(url: str) -> str | None:
    """从 remote URL 提取 'owner/repo' 归一化键，用于校验指向。非 GitHub 返回 None。"""
    url = (url or "").strip()
    if "github.com" not in url:
        return None
    if url.startswith("git@"):
        path = url.split(":", 1)[-1]
    else:
        # https://github.com/owner/repo(.git)
        path = url.split("github.com/", 1)[-1]
    path = path.strip("/").removesuffix(".git")
    parts = path.split("/")
    if len(parts) < 2:
        return None
    return f"{parts[0]}/{parts[1]}".lower()


def ensure_origin(owner: str, repo: str, root: Path | None = None) -> str:
    """确保 origin remote 存在且指向目标仓库，返回最终使用的 URL。

    历史故障：nova-forge 的 git/publish 命令无条件 `git push origin main`，
    但工作区重置 / 新环境后 origin 丢失，直接崩溃并抛裸 traceback。
    此函数作为 push 前置步骤自愈该配置。

    - origin 不存在 → 按 NOVA_GIT_PROTOCOL（默认 ssh，可设 https）添加；
    - origin 已存在且指向本仓库 → 原样复用（尊重用户既有配置，不覆盖）；
    - origin 已存在但指向别的仓库 → 抛错，绝不静默改写 / 误推到错误仓库。
    """
    root = root or Path.cwd()
    ssh_url, https_url = _origin_url(owner, repo)
    protocol = (os.environ.get("NOVA_GIT_PROTOCOL") or "ssh").strip().lower()
    preferred = https_url if protocol in ("https", "http") else ssh_url
    target_key = f"{owner}/{repo}".lower()

    probe = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        check=False, capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=root,
    )
    if probe.returncode != 0:
        subprocess.run(
            ["git", "remote", "add", "origin", preferred],
            check=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace", cwd=root,
        )
        return preferred

    current = probe.stdout.strip()
    existing_key = _repo_key_from_url(current)
    if existing_key is not None and existing_key != target_key:
        raise RuntimeError(
            f"origin 已指向 {existing_key}（{current}），与目标仓库 {target_key} 不符。"
            f"请人工确认后执行 `git remote set-url origin {preferred}`。"
        )
    # 非 GitHub URL（如内网镜像）无法确定归属，尊重用户配置，原样复用
    return current
