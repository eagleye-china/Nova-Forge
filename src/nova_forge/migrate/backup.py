# src/nova_forge/migrate/backup.py
"""§9.3 备份 / 临时目录约定（伙伴 05:31 拍板，长期有效）。

- 在系统临时目录自建 ``%TEMP%/nova-scratch/migrate2nova-<时间戳>/``，
  **不占用项目内任何已有目录**；镜像存原文件 + ``manifest.json``。
- 「自己建的自己删」：``clean()`` 整目录删除，不留空目录、不改 .gitignore、
  不留 git 痕迹；清场前 ``restore()`` 始终可用。
- 本工具默认 dry-run、``--scaffold`` 也只写新文件、**原 .py 零改动**，
  故备份对象是「将被覆盖的产物文件」，风险面极小。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TASK = "migrate2nova"
MANIFEST = "manifest.json"


def scratch_root() -> Path:
    """``%TEMP%/nova-scratch/`` 根目录（不存在则惰性创建）。"""
    return Path(tempfile.gettempdir()) / "nova-scratch"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Backup:
    """一次备份的句柄。"""

    backup_id: str
    path: Path
    root: Path
    files: tuple[str, ...]

    def restore(self) -> int:
        """从镜像恢复所有文件到原始位置，返回恢复文件数。"""
        manifest = json.loads((self.path / MANIFEST).read_text(encoding="utf-8"))
        restored = 0
        for item in manifest["files"]:
            rel = item["path"]
            dst = self.root / rel
            if item.get("existed", True) is False:
                # 原本不存在的文件：恢复 = 删除产物（回到迁移前状态）
                dst.unlink(missing_ok=True)
                restored += 1
                continue
            src = self.path / "mirror" / rel
            if not src.is_file():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored += 1
        return restored

    def clean(self) -> None:
        """整目录删除（自己建的自己删）。"""
        shutil.rmtree(self.path, ignore_errors=True)

    def verify(self) -> bool:
        """校验镜像哈希与 manifest 一致。"""
        manifest = json.loads((self.path / MANIFEST).read_text(encoding="utf-8"))
        for item in manifest["files"]:
            if not item.get("existed", True):
                continue
            src = self.path / "mirror" / item["path"]
            if not src.is_file() or _sha256(src) != item["sha256"]:
                return False
        return True


def create(root: str | Path, files: list[Path]) -> Backup:
    """备份一组**将被覆盖**的产物文件；不存在的文件也登记（existed=false）。"""
    root_path = Path(root).expanduser().resolve()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_id = f"{TASK}-{stamp}"
    path = scratch_root() / backup_id
    mirror = path / "mirror"
    mirror.mkdir(parents=True, exist_ok=False)

    records: list[dict] = []
    for item in files:
        target = Path(item).expanduser().resolve()
        try:
            rel = str(target.relative_to(root_path))
        except ValueError:
            rel = target.name
        existed = target.is_file()
        record: dict = {"path": rel, "existed": existed}
        if existed:
            dst = mirror / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dst)
            record["sha256"] = _sha256(target)
        records.append(record)

    manifest = {
        "tool": "nova-forge migrate2nova",
        "id": backup_id,
        "created": datetime.now().isoformat(timespec="seconds"),
        "root": str(root_path),
        "files": records,
    }
    (path / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return Backup(backup_id, path, root_path, tuple(r["path"] for r in records))


def list_backups() -> tuple[Backup, ...]:
    """列出全部可用备份（按 id 倒序）。"""
    base = scratch_root()
    if not base.is_dir():
        return ()
    result: list[Backup] = []
    for path in sorted(base.glob(f"{TASK}-*"), reverse=True):
        mf = path / MANIFEST
        if not mf.is_file():
            continue
        data = json.loads(mf.read_text(encoding="utf-8"))
        result.append(
            Backup(
                backup_id=data["id"],
                path=path,
                root=Path(data["root"]),
                files=tuple(i["path"] for i in data["files"]),
            )
        )
    return tuple(result)


def find(backup_id: str) -> Backup:
    """按 id 定位备份；不存在抛 FileNotFoundError。"""
    for b in list_backups():
        if b.backup_id == backup_id:
            return b
    raise FileNotFoundError(f"备份不存在：{backup_id}")
