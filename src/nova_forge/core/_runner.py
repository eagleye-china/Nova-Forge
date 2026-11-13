import subprocess


def run(cmd, ignore_error=False, env=None):
    """统一的子进程执行封装：强制 UTF-8，失败时打印 stdout+stderr。"""
    print(f"👉 正在执行: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0 and not ignore_error:
        error_msg = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        print(f"❌ 错误: {error_msg}")
        raise RuntimeError(error_msg)
    if result.stdout and result.stdout.strip():
        print(result.stdout.strip())
    return result
