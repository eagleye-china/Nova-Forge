# src/nova_forge/core/qrc_builder.py
# 创建时间：星期二 2026-11-24 21:39
"""纯标准库 QRC 生成逻辑，便于在无 PySide6 环境下测试与复用。"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_SUFFIX_RE = re.compile(r"_\d+$")


def _base_alias(alias: str) -> str:
    """剥掉重复更新追加的 _2/_3 后缀，得到别名基准。"""
    return _SUFFIX_RE.sub("", alias)


def update_qrc_from_directory(target_dir: str | Path) -> str:
    """扫描目录中的 SVG，生成/合并同级 resources.qrc，返回操作日志。

    已有且物理文件仍存在的条目会被保留，避免覆盖人工维护的 alias；
    新增文件以文件名（不含扩展名）作为 alias，重名时自动追加序号。
    """
    folder = Path(target_dir).resolve()
    if not folder.is_dir():
        raise ValueError(f"资源目录不存在: {folder}")

    qrc_path = folder.parent / "resources.qrc"
    prefix = f"/{folder.name}"
    entries: dict[str, tuple[str, str]] = {}
    # (rel, 基础别名) 去重：保留语义别名（nova.svg 等）与首个文件名别名，
    # 只清除重复更新遗留的 name_2/_3 后缀，不误删同文件的多语义入口。
    seen: set[tuple[str, str]] = set()

    if qrc_path.exists():
        try:
            existing_root = ET.parse(qrc_path).getroot()
        except ET.ParseError as exc:
            raise ValueError(f"现有 {qrc_path.name} 不是合法 XML: {exc}") from exc

        for qresource in existing_root.findall("qresource"):
            prefix = qresource.get("prefix") or prefix
            for file_el in qresource.findall("file"):
                rel = (file_el.text or "").strip()
                if not rel or not (qrc_path.parent / rel).exists():
                    continue
                alias = file_el.get("alias") or Path(rel).stem
                base = _base_alias(alias)
                if (rel, base) in seen:
                    continue  # 同一物理文件的 _2/_3 重复别名，丢弃
                seen.add((rel, base))
                entries[alias] = (alias, rel)

    added: list[str] = []
    for svg in sorted(folder.rglob("*.svg")):
        rel = svg.relative_to(qrc_path.parent).as_posix()
        base = _base_alias(svg.stem)
        if (rel, base) in seen:
            continue  # 已登记：保留原 alias，不再追加 _2
        alias = svg.stem
        if alias in entries:
            index = 2
            while f"{svg.stem}_{index}" in entries:
                index += 1
            alias = f"{svg.stem}_{index}"
        entries[alias] = (alias, rel)
        seen.add((rel, base))
        added.append(alias)

    root = ET.Element("RCC", {"version": "1.0"})
    qresource = ET.SubElement(root, "qresource", {"prefix": prefix})
    for alias, rel in sorted(entries.values(), key=lambda item: item[1]):
        file_el = ET.SubElement(qresource, "file", {"alias": alias})
        file_el.text = rel

    ET.indent(root, space="    ")
    qrc_path.write_text(
        "<!DOCTYPE RCC>\n" + ET.tostring(root, encoding="unicode") + "\n",
        encoding="utf-8",
    )

    kept = len(entries) - len(added)
    return (
        f"已更新 {qrc_path.name}\n"
        f"保留已有条目: {kept}\n"
        f"新增条目: {len(added)}\n"
        f"总计: {len(entries)}"
    )
