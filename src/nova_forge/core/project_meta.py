import subprocess
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


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
    name, version = section.get("name"), section.get("version")
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
        return parts[0] if remote_url.startswith("git@") else parts[-2], parts[-1].replace(".git", "")
    except Exception:  # noqa: BLE001
        return fallback
