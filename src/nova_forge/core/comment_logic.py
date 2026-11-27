# src/nova_forge/core/comment_logic.py
# 创建时间：星期二 2026-11-24 21:39
from __future__ import annotations

import ast
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 北京时间：硬编码 UTC+8，不受运行机器系统时区影响
BEIJING_TZ = timezone(timedelta(hours=8))
WEEKDAYS_CN = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")

# 默认跳过的目录（相对路径的任何层级匹配）
SKIP_DIRS = frozenset(
    {
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        ".tox",
        "site-packages",
        "backups",
        "output",
    }
)

# Qt 生成物：禁止手改（总管纪律：生成物只改生成器）
GENERATED_SUFFIXES = ("_rc.py",)
SUPPORTED_EXTS = (".py", ".qml")
STAMP_PREFIX = "创建时间："


def beijing_stamp(ts: float) -> str:
    """把 Unix 时间戳格式化为北京时间「星期X YYYY-MM-DD HH:MM」。"""
    dt = datetime.fromtimestamp(ts, tz=BEIJING_TZ)
    return f"{WEEKDAYS_CN[dt.weekday()]} {dt:%Y-%m-%d %H:%M}"


def _detect_newline(raw: bytes) -> bytes:
    """检测文件主换行符：优先 CRLF（出现即认定），否则 LF。"""
    return b"\r\n" if b"\r\n" in raw else b"\n"


def _decode(raw: bytes) -> tuple[str, str, bytes]:
    """解码字节为文本，返回 (text, 原编码名, BOM 字节)。"""
    if raw.startswith(b"\xef\xbb\xbf"):
        # BOM 单独返回，编码名仍用 utf-8，避免 _encode 时二次写入 BOM
        return raw[3:].decode("utf-8"), "utf-8", b"\xef\xbb\xbf"
    try:
        return raw.decode("utf-8"), "utf-8", b""
    except UnicodeDecodeError:
        return raw.decode("gbk"), "gbk", b""


def _encode(text: str, encoding: str, bom: bytes) -> bytes:
    return bom + text.encode(encoding)


def _leading_special_lines(text: str) -> tuple[list[str], int]:
    """提取文件开头的 shebang / coding 声明，返回 (去换行的行, 字符偏移)。

    Python 要求编码声明位于第 1/2 行，故这些行必须保持在档案头之前。
    """
    lines = text.splitlines(keepends=True)
    special: list[str] = []
    offset = 0
    for ln in lines[:2]:
        s = ln.strip()
        if s.startswith("#!") or ("coding" in s and s.startswith("#")):
            special.append(ln.rstrip("\r\n"))
            offset += len(ln)
        else:
            break
    return special, offset


def _is_path_line(line: str, ext: str) -> bool:
    """判断是否为档案头首行路径注释（# path / // path）。"""
    marker = "# " if ext == ".py" else "// "
    s = line.strip()
    return s.startswith(marker) and s[len(marker) :].strip().endswith(ext)


def _is_stamp_line(line: str) -> bool:
    """判断是否为旧式时间行 / 创建时间行（均属档案头，需覆盖重写）。"""
    s = line.strip()
    if not s.startswith(("#", "//")):
        return False
    payload = s.lstrip("#/").strip()
    return payload.startswith(STAMP_PREFIX) or any(
        payload.startswith(w) for w in WEEKDAYS_CN
    )


def _find_docstring_span_py(text: str) -> tuple[int, int] | None:
    """用 AST 定位模块级 docstring 的字符区间 [start, end)。

    只认真正的模块第一语句字符串；模板文件里的三引号赋值不会被误判。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    if not tree.body:
        return None
    first = tree.body[0]
    if not (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return None
    lines = text.splitlines(keepends=True)
    start = sum(len(x) for x in lines[: first.lineno - 1]) + (first.col_offset or 0)
    end = sum(len(x) for x in lines[: first.end_lineno - 1]) + (
        first.end_col_offset or 0
    )
    return (start, end)


def _find_docstring_span_qml(text: str) -> tuple[int, int] | None:
    """识别紧跟路径注释后的 /* ... */ 块（旧版档案头文档注释）。"""
    lines = text.splitlines(keepends=True)
    idx = 0
    while idx < len(lines):
        s = lines[idx].strip()
        if not s or s.startswith("//") or "#!" in s or "coding" in s:
            idx += 1
            continue
        break
    if idx < len(lines) and lines[idx].lstrip().startswith("/*"):
        start = sum(len(x) for x in lines[:idx])
        j = idx
        while j < len(lines):
            if "*/" in lines[j]:
                return (start, sum(len(x) for x in lines[: j + 1]))
            j += 1
    return None


def _extract_stamp(text: str) -> str | None:
    """从文件头部注释 / 文档注释内取出「创建时间：...」，用于幂等保留。

    旧式独立行「# 星期X ... 00:00」是历史硬编码假戳，不含创建时间标记，
    不识别、不继承，一律由 beijing_stamp() 重新生成真实北京时间。
    """
    for ln in text.splitlines()[:8]:
        s = ln.strip()
        if STAMP_PREFIX not in s:
            continue
        if not (s.startswith(("#", "//")) or s.startswith(STAMP_PREFIX)):
            continue
        value = s.split(STAMP_PREFIX, 1)[1].strip().rstrip("*/\"'").strip()
        if value:
            return value
    return None


def build_header(
    rel: str,
    ext: str,
    original_text: str,
    nl: bytes,
    force: bool = False,
    now_ts: float | None = None,
) -> tuple[str, str]:
    """构造新头部，返回 (新完整文本, 使用的创建时间)。

    只重写头部的两行注释；正文（含用户手写 docstring、空行、缩进）逐字节不变。

    策略：
      - shebang / coding 声明永远保持在最前（Python 语法要求）；
      - 覆盖掉旧的路径注释行、旧式假时间行、创建时间行；
      - 旧版三段式档案头里的 docstring，仅当内含「创建时间：」才视为
        本工具注入、可安全剥离；用户手写 docstring 一律保留；
      - 时间戳：非 force 时沿用已有真实戳，否则取执行时刻北京时间。
    """
    nl_s = nl.decode()
    marker = "# " if ext == ".py" else "// "
    special, special_end = _leading_special_lines(original_text)
    work = original_text[special_end:]
    lines = work.splitlines(keepends=True)

    cut = 0
    path_found = bool(lines) and _is_path_line(lines[0], ext)
    if path_found:
        cut = len(lines[0])
        k = 1
        while k < len(lines) and k <= 2:
            if _is_stamp_line(lines[k]):
                cut += len(lines[k])
                k += 1
            else:
                break

        d = (
            _find_docstring_span_py(work)
            if ext == ".py"
            else _find_docstring_span_qml(work)
        )
        if d and STAMP_PREFIX in work[d[0] : d[1]] and d[0] <= cut + len(nl_s):
            cut = max(cut, d[1])

    body = work[cut:]
    old_stamp = None if force else _extract_stamp(original_text)
    stamp = old_stamp or beijing_stamp(now_ts if now_ts is not None else time.time())

    head = special + [f"{marker}{rel}", f"{marker}{STAMP_PREFIX}{stamp}"]
    new_text = nl_s.join(head) + nl_s + body
    return new_text, stamp


def _body_after_archive_header(text: str, ext: str) -> str:
    """剥离档案头（兼容新旧格式），返回正文，用于字节级一致性比对。"""
    _, special_end = _leading_special_lines(text)
    work = text[special_end:]
    lines = work.splitlines(keepends=True)
    cut = 0
    if lines and _is_path_line(lines[0], ext):
        cut = len(lines[0])
        k = 1
        while k < len(lines) and k <= 2 and _is_stamp_line(lines[k]):
            cut += len(lines[k])
            k += 1
        d = (
            _find_docstring_span_py(work)
            if ext == ".py"
            else _find_docstring_span_qml(work)
        )
        if d and STAMP_PREFIX in work[d[0] : d[1]] and d[0] <= cut + 1:
            cut = max(cut, d[1])
    return work[cut:]


def _validate_py(text: str) -> bool:
    try:
        ast.parse(text)
        return True
    except SyntaxError:
        return False


def _validate_qml(text: str) -> bool:
    """轻量括号平衡检查，避免生成明显破坏语法的注释。"""
    depth = 0
    in_str: str | None = None
    i = 0
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
        elif c in ('"', "'"):
            in_str = c
        elif c == "/" and i + 1 < len(text) and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = j + 1 if j >= 0 else len(text)
        elif c == "/" and i + 1 < len(text) and text[i + 1] == "/":
            j = text.find("\n", i)
            i = j if j >= 0 else len(text)
        elif c in "({[":
            depth += 1
        elif c in ")}]":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0 and in_str is None


def _atomic_write(path: Path, data: bytes) -> None:
    """同目录临时文件 + os.replace 原子替换，避免半写文件。"""
    tmp = path.with_name(path.name + ".comment-tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def process_file(
    path: Path,
    root: Path,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """处理单个文件，返回结构化结果。

    结果 status ∈ {done, skipped, failed, already}；任何异常都不会抛出到调用方。
    """
    rel = path.relative_to(root).as_posix()
    result = {"file": rel, "status": "skipped", "reason": "", "stamp": ""}
    try:
        raw = path.read_bytes()
        text, encoding, bom = _decode(raw)
        nl = _detect_newline(raw)

        new_text, stamp = build_header(rel, path.suffix, text, nl, force, time.time())
        result["stamp"] = stamp

        if new_text == text and not force:
            result["status"] = "already"
            return result

        # 门禁①：正文逐字节一致（只许改头部两行，绝不碰原内容）
        # 门禁②：Python 另做 ast.parse；QML 不用括号平衡器——正则字面量
        #         （如 /\[.../）会让合法 QML 被误判，故只依赖门禁①。
        body_ok = _body_after_archive_header(new_text, path.suffix) == _body_after_archive_header(
            text, path.suffix
        )
        syntax_ok = _validate_py(new_text) if path.suffix == ".py" else True
        if not (body_ok and syntax_ok):
            result["status"] = "failed"
            result["reason"] = "正文一致性 / 语法校验未通过，已放弃写入"
            return result

        new_raw = _encode(new_text, encoding, bom)
        if dry_run:
            result["status"] = "done"
            result["reason"] = "dry-run 预览"
            return result

        _atomic_write(path, new_raw)

        # 写后复核：与写入同源解码（GBK / BOM 文件不能硬用 utf-8 读），
        # 校验正文与写入前完全一致 + Python 可解析；QML 不跑括号平衡器。
        after_text, _, _ = _decode(path.read_bytes())
        check_ok = (
            _body_after_archive_header(after_text, path.suffix)
            == _body_after_archive_header(text, path.suffix)
        )
        if path.suffix == ".py":
            check_ok = check_ok and _validate_py(after_text)
        if not check_ok:
            result["status"] = "failed"
            result["reason"] = "写后校验失败"
            return result

        result["status"] = "done"
        return result
    except Exception as exc:
        result["status"] = "failed"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return result


def iter_source_files(root: Path) -> list[Path]:
    """遍历当前项目目录，返回待处理的 .py/.qml 文件（已排除跳过目录与生成物）。"""
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(SUPPORTED_EXTS):
                continue
            if name.endswith(GENERATED_SUFFIXES):
                continue
            found.append(Path(dirpath) / name)
    return sorted(found)
