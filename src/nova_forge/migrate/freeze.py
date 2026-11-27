# src/nova_forge/migrate/freeze.py
"""迁移映射表的**唯一法源**：pyside-nova API 冻结清单。

T3 方案 §9.4 要求「映射表由 api/nova-api-1.x.0.json 自动生成」，本模块不手写
任何 Nova 类型清单：147 个公共类型、所属模块、文件、a11y 与公共面全部从冻结面
读取，映射规则的每个 AUTO 目标都在此校验存在 —— 法源链不留悬空。

默认自动探测同级工作区的 ``pyside-nova/api/nova-api-*.json`` 并取 apiVersion
最高者；也可由 ``--api`` 显式指定。史实口径：1.11.0 / 147 类型 /
指纹 ``9966483dda5a53c4``。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NovaType:
    """冻结面里一个公共类型的机器可读投影。"""

    fqname: str
    module: str
    name: str
    file: str
    kind: str
    a11y: str
    props: tuple[str, ...]
    signals: tuple[str, ...]
    methods: tuple[str, ...]


@dataclass(frozen=True)
class FreezeIndex:
    """一次迁移所依据的冻结面快照。"""

    path: Path
    api_version: str
    package_version: str
    fingerprint: str
    types: dict[str, NovaType]

    def has(self, fqname: str) -> bool:
        return fqname in self.types

    def by_short_name(self, name: str) -> NovaType | None:
        """按短名解析（同名类型在 147 面内唯一，歧义返回 None）。"""
        hits = [t for t in self.types.values() if t.name == name]
        return hits[0] if len(hits) == 1 else None

    @property
    def count(self) -> int:
        return len(self.types)


def _parse_version(text: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in text.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def discover_freeze(explicit: str | Path | None = None) -> Path:
    """定位冻结面 JSON：显式路径 > 同级工作区 api/ 目录内最新版本。

    遍历顺序保证「零硬编码版本号」——将来 1.12.0 落盘即自动接管。
    """
    if explicit is not None:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"指定的 API 冻结面不存在：{path}")
        return path

    here = Path(__file__).resolve()
    # migrate/ → nova_forge/ → src/ → nova-forge/ → Nova 工作区根
    workspace = here.parents[3].parent
    api_dir = workspace / "pyside-nova" / "api"
    if not api_dir.is_dir():
        raise FileNotFoundError(
            f"未找到同级 pyside-nova/api/ 目录（{api_dir}）；请用 --api 指定冻结面路径"
        )
    candidates = sorted(api_dir.glob("nova-api-*.json"))
    if not candidates:
        raise FileNotFoundError(f"{api_dir} 下没有 nova-api-*.json")
    return max(candidates, key=lambda p: _parse_version(p.stem.removeprefix("nova-api-")))


def load_freeze(explicit: str | Path | None = None) -> FreezeIndex:
    """读取并校验冻结面，产出 FreezeIndex。"""
    path = discover_freeze(explicit)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "nova-api-freeze/1":
        raise ValueError(f"冻结面 schema 不符：{data.get('schema')!r}（{path}）")
    raw_types = data.get("types")
    if not isinstance(raw_types, dict) or not raw_types:
        raise ValueError(f"冻结面 types 为空或结构异常：{path}")

    types: dict[str, NovaType] = {}
    for fqname, node in raw_types.items():
        module = str(node.get("module", ""))
        name = fqname.rsplit(".", 1)[-1]
        types[fqname] = NovaType(
            fqname=fqname,
            module=module,
            name=name,
            file=str(node.get("file", "")),
            kind=str(node.get("kind", "component")),
            a11y=str(node.get("a11y", "decorative")),
            props=tuple(str(p) for p in node.get("props", [])),
            signals=tuple(str(s) for s in node.get("signals", [])),
            methods=tuple(str(m) for m in node.get("methods", [])),
        )

    expected = int(data.get("counts", {}).get("total", 0))
    if expected and len(types) != expected:
        raise ValueError(
            f"冻结面账实不符：counts.total={expected}，实际 types={len(types)}（{path}）"
        )

    return FreezeIndex(
        path=path,
        api_version=str(data.get("apiVersion", "")),
        package_version=str(data.get("packageVersion", "")),
        fingerprint=str(data.get("fingerprint", "")),
        types=types,
    )
