# src/nova_forge/command/cmd_snapshot.py
# 星期五 2026-11-20 00:00
"""
快照归档命令实现：终端手动粘贴，自动使用 snapshot_yyyyMMddHH 命名。
零外部依赖，仅使用标准库。
"""

from datetime import datetime
from pathlib import Path


def _read_interactive_content() -> str:
    """交互式读取多行快照正文；单独一行输入 EOF 或 Ctrl-D/Ctrl-Z 结束。"""
    print("📋 请粘贴快照正文（粘贴后，另起一行输入 EOF 并回车结束）：")
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


def run_snapshot() -> None:
    """执行归档操作。"""
    # 1. 自动生成标题（yyyyMMddHH）
    default_title = datetime.now().strftime("%Y%m%d%H")
    title = default_title

    # 2. 从终端手动读取内容
    content = _read_interactive_content()

    if not content.strip():
        print("⚠️ 内容为空！未归档。")
        return

    # 3. 落盘
    snapshot_dir = Path("docs/session-snapshots")
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # 🌟 增加 snapshot_ 前缀
    filename = f"snapshot_{title}.md"
    target = snapshot_dir / filename

    # 防止同小时内多次归档覆盖
    counter = 1
    while target.exists():
        filename = f"snapshot_{title}_{counter}.md"
        target = snapshot_dir / filename
        counter += 1

    final_content = (
        "<!-- session_bridge snapshot\n"
        f"生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"标题：{title}\n"
        "工具：Nova-Forge snapshot（零外部 API）\n"
        "-->\n\n"
        f"{content.strip()}\n"
    )

    target.write_text(final_content, encoding="utf-8")
    print(f"✅ 已归档：{target}")
