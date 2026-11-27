# src/nova_forge/core/saver_logic.py
# 创建时间：星期二 2026-11-24 21:39
"""
Nova Multi-Block 源码保存工具 - 业务解析层
负责正则提取、路径安全校验、文件读写操作。
"""

import re
from pathlib import Path

EXTENSION_LANG_MAP = {
    ".py": "Python",
    ".qml": "QML",
    ".md": "Markdown",
    ".json": "JSON",
    ".txt": "Text",
}

PATH_PATTERN = re.compile(
    r"^(?://|#)\s*((?:src|tools|tests|examples|docs|theme)/[^\n]*?(?:\.(?:qml|py|md|json|txt)|qmldir))(?:\s|$)",
    re.MULTILINE,
)

def extract_blocks(text: str) -> list[dict]:
    """从原始文本中提取代码块元数据。"""
    blocks = []
    lines = text.splitlines()

    current_path = None
    current_lang = None
    code_lines = []
    in_code_block = False

    for line in lines:
        match = PATH_PATTERN.match(line)
        if match:
            if current_path and code_lines:
                blocks.append(_finalize_block(current_path, current_lang, code_lines))
                code_lines = []

            current_path = match.group(1).strip()
            file_name = Path(current_path).name
            ext = Path(current_path).suffix.lower()

            current_lang = None
            if file_name == "qmldir":
                current_lang = "QML-Dir"
            elif ext in EXTENSION_LANG_MAP:
                current_lang = EXTENSION_LANG_MAP[ext]

            code_lines = [line]
            in_code_block = False
            continue

        if current_path:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            code_lines.append(line)

    if current_path and code_lines:
        blocks.append(_finalize_block(current_path, current_lang, code_lines))

    return blocks

def _finalize_block(rel_path: str, lang: str, code_lines: list) -> dict:
    comment_symbol = "//" if lang in ["QML", "QML-Dir"] else "#"
    expected_header = f"{comment_symbol} {rel_path}"

    while code_lines and not code_lines[0].strip():
        code_lines.pop(0)
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()

    if code_lines and code_lines[0].strip() == expected_header:
        raw_code = "\n".join(code_lines) + "\n"
    else:
        raw_code = f"{expected_header}\n" + "\n".join(code_lines) + "\n"

    return {"lang": lang, "path": rel_path, "raw_code": raw_code}
