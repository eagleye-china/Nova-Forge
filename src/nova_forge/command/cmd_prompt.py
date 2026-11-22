# src/nova_forge/command/cmd_prompt.py
# 星期一 2026-11-23 00:20
"""
会话接续命令实现：查找最新快照，从模板文件读取接续指令，拼装并落盘。
零外部依赖，仅使用标准库。
"""

from pathlib import Path

# 引入刚刚剥离出来的模板
from .templates.tmpl_prompt import TMPL_prompt_PROMPT


def _find_latest_snapshot(snapshot_dir: Path) -> Path | None:
    """按修改时间查找最新快照文件。"""
    if not snapshot_dir.exists() or not snapshot_dir.is_dir():
        return None
    files = [p for p in snapshot_dir.glob("snapshot_*.md") if p.is_file()]
    if not files:
        return None
    files.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
    return files[0]


def _copy_to_clipboard(text: str) -> bool:
    """将文本复制到系统剪贴板；tkinter 不可用时静默降级。"""
    try:
        import tkinter as tk
    except ImportError:
        return False

    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except tk.TclError:
        return False


def run_prompt() -> None:
    """执行接续 Prompt 生成操作。"""
    snapshot_dir = Path("docs/session-snapshots")
    target_path = _find_latest_snapshot(snapshot_dir)

    if target_path is None:
        print(f"❌ 错误：未在 {snapshot_dir} 找到任何 snapshot_*.md 快照文件。")
        return

    try:
        snapshot_text = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"❌ 错误：读取快照失败：{exc}")
        return

    # 使用模板进行字符串替换
    prompt = TMPL_prompt_PROMPT.replace("{{SNAPSHOT_CONTENT}}", snapshot_text.strip())

    # 在快照目录生成 ready_prompt.md
    output_file = snapshot_dir / "ready_prompt.md"
    output_file.write_text(prompt, encoding="utf-8")

    print(f"✅ 成功读取最新快照：{target_path.name}")
    print(f"📄 交接指令已生成：{output_file}")

    # 顺手复制到剪贴板
    if _copy_to_clipboard(prompt):
        print("📋 已同步复制到剪贴板，你可以直接去网页端 Ctrl+V 粘贴。")
