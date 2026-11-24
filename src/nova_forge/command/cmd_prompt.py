# src/nova_forge/command/cmd_prompt.py
# 星期二 2026-11-24 13:15
"""
新会话提示词命令实现：终端粘贴含快照的提示词正文，一步存盘并复制剪贴板。
不再单独生成快照文件、不再套用接续模板——粘贴即所得。
零外部依赖，仅使用标准库（tkinter 剪贴板不可用时静默降级）。
"""

from datetime import datetime
from pathlib import Path

PROMPT_DIR = Path("docs/session-snapshots")


def _read_interactive_content() -> str:
    """交互式读取提示词正文；单独一行输入 EOF 或 Ctrl-D/Ctrl-Z 结束。"""
    print("📝 请粘贴【新会话提示词正文】（其中已包含会话快照）。")
    print("   粘贴完成后，另起一行输入 EOF 并回车结束：")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "EOF":
            break
        lines.append(line)
    return "\n".join(lines)


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


def _build_prompt_file_name(stamp: str, directory: Path) -> Path:
    """生成 prompt{yyyyMMddHH}.md；同小时内多次追加 _1、_2 避免覆盖。"""
    candidate = directory / f"prompt{stamp}.md"
    counter = 1
    while candidate.exists():
        candidate = directory / f"prompt{stamp}_{counter}.md"
        counter += 1
    return candidate


def run_prompt() -> None:
    """执行新会话提示词生成：粘贴 → 存盘 → 复制剪贴板，一步完成。"""
    content = _read_interactive_content()
    if not content.strip():
        print("⚠️ 内容为空！未生成提示词。")
        return

    now = datetime.now()
    prompt_dir = PROMPT_DIR
    prompt_dir.mkdir(parents=True, exist_ok=True)
    target = _build_prompt_file_name(now.strftime("%Y%m%d%H"), prompt_dir)

    final_content = (
        "<!-- nova-forge prompt · 新会话提示词（含会话快照）\n"
        f"生成时间：{now:%Y-%m-%d %H:%M:%S}\n"
        "工具：Nova-Forge prompt（粘贴即存盘，零外部 API）\n"
        "-->\n\n"
        f"{content.strip()}\n"
    )
    target.write_text(final_content, encoding="utf-8")

    print(f"✅ 新会话提示词已存盘：{target}")
    if _copy_to_clipboard(final_content):
        print("📋 已同步复制到剪贴板，可直接粘贴到新会话首条消息。")
    else:
        print("⚠️ 剪贴板不可用（tkinter 缺失），请手动打开文件复制。")
