# src/nova_forge/command/cmd_pypi.py
# 星期一 2026-11-23 03:25
"""本地构建并上传 PyPI 的完整流水线。"""

import glob
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

from ._runner import run

_PYPI_JSON = "https://pypi.org/pypi/{name}/{version}/json"


def _version_exists_on_pypi(name: str, version: str, timeout: float = 5.0):
    """查询 PyPI 上是否已存在该版本。

    返回 True/False；网络异常时返回 None（未知），不阻塞上传。
    """
    url = _PYPI_JSON.format(name=name, version=version)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        return None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None

    files = data.get("urls")
    return bool(files)


def _clean_build_dirs():
    print("[1/4] 正在清理旧构建文件...")
    for d in ["dist", "build"]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    src_dir = Path("src")
    if src_dir.exists():
        for egg_info in src_dir.glob("*.egg-info"):
            shutil.rmtree(egg_info, ignore_errors=True)
    print("✅ 清理完成。")


def run_package():
    try:
        _clean_build_dirs()

        print("\n[2/4] 正在构建安装包 (python -m build)...")
        run([sys.executable, "-m", "build"])

        print("\n[3/4] 正在检查 README 和包元数据 (twine check)...")
        dist_files = sorted(glob.glob("dist/*"))
        if not dist_files:
            print("❌ 错误: dist 目录为空，没有可上传的构建产物。")
            return
        run([sys.executable, "-m", "twine", "check", *dist_files])

        # 上传前查重：版本撞车是 PyPI 400 的常见根因，提前给出清晰提示
        from .. import __version__

        exists = _version_exists_on_pypi("nova-forge", __version__)
        if exists is True:
            print(
                f"\n❌ 版本 {__version__} 已存在于 PyPI，无法重复上传同名版本。\n"
                "💡 请先在 pyproject.toml 中升版（并更新 CHANGELOG.md），再重新执行。"
            )
            return
        if exists is None:
            print("\n⚠️ 无法连接 PyPI 校验版本，跳过查重，继续上传。")

        print("\n[4/4] 正在上传至 正式 PyPI...")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        run(
            [
                sys.executable,
                "-m",
                "twine",
                "upload",
                "--disable-progress-bar",
                *dist_files,
            ],
            env=env,
        )

        print("\n" + "=" * 40)
        print("🎉 震撼发布！成功登陆全球 PyPI！")
        print("=" * 40)
    except RuntimeError:
        # run() 已打印完整错误，这里不再重复刷一遍
        sys.exit(1)
