import glob
import os
import shutil
import sys
from pathlib import Path

from ._runner import run


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
        dist_files = glob.glob("dist/*")
        run([sys.executable, "-m", "twine", "check"] + dist_files)

        print("\n[4/4] 正在上传至 正式 PyPI...")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        run(
            [sys.executable, "-m", "twine", "upload", "--disable-progress-bar"] + dist_files,
            env=env,
        )

        print("\n" + "=" * 40)
        print("🎉 震撼发布！成功登陆全球 PyPI！")
        print("=" * 40)
    except Exception as e:  # noqa: BLE001
        print(f"\n❌ [ERROR] 任务中断: {e}")
        sys.exit(1)
