# src/nova_forge/utils/project_meta.py

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
