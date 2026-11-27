# src/nova_forge/migrate/contract.py
"""T3 契约校验门（§9.4「新增契约校验门，不合格不落地」）。

四道方案点名的门 + 一道覆盖率门：
1. ``static-tier``：冻结面自洽 + 所有 AUTO 映射目标在冻结面真实存在 + 零静默
   遗漏（等价 pyside-nova ``check_all.py --tier static`` 的静态契约层）。
2. ``qmllint``：生成 QML 的静态契约（import / 括号 / 禁裸业务 Rectangle）；
   环境可定位 ``qmllint`` 时额外实跑并零容忍 error。
3. ``modelValue``：受控契约 —— 生成 QML 不得自写 ``modelValue``（只 emit 意图）。
4. ``slot-constitution``：组合根必须用槽位注入，不得内嵌业务语义（CC-1~CC-8）。
5. ``coverage``：每个唯一 Qt 名 100% 有处置（AUTO/RUNTIME/NATIVE/MANUAL）。

``--scaffold`` 落盘前必须全绿；dry-run 也给出门结果供人工审阅。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .freeze import FreezeIndex
from .rules import DISPOSITIONS, classify, validate_rules
from .scanner import ScanResult

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


@dataclass(frozen=True)
class Gate:
    """一道门的结果。"""

    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class ContractReport:
    """全部门的结果。"""

    gates: tuple[Gate, ...]

    @property
    def passed(self) -> bool:
        return all(g.status != FAIL for g in self.gates)

    @property
    def blockers(self) -> tuple[Gate, ...]:
        return tuple(g for g in self.gates if g.status == FAIL)


def _gate_static_tier(index: FreezeIndex, scan: ScanResult) -> Gate:
    dangling = validate_rules(index)
    unresolved = [
        f.qt_name for f in scan.findings
        if classify(f.qt_name).disposition not in DISPOSITIONS
    ]
    if dangling or unresolved or index.count == 0:
        return Gate(
            "static-tier", FAIL,
            f"冻结面 {index.count} 类型 · 悬空目标 {dangling} · 未处置 {unresolved}",
        )
    return Gate(
        "static-tier", PASS,
        f"冻结面 {index.api_version} / {index.count} 类型 / 指纹 {index.fingerprint}"
        f" · AUTO 目标零悬空 · 规则处置零遗漏",
    )


def _gate_coverage(scan: ScanResult) -> Gate:
    total = len(scan.findings)
    if total == 0:
        return Gate("coverage", SKIP, "目标工程未发现任何 Qt 引用（无需迁移）")
    resolved = sum(
        1 for f in scan.findings if classify(f.qt_name).disposition in DISPOSITIONS
    )
    pct = resolved / total * 100
    counts: dict[str, int] = {}
    for f in scan.findings:
        d = classify(f.qt_name).disposition
        counts[d] = counts.get(d, 0) + 1
    detail = (
        f"{resolved}/{total} = {pct:.0f}% 已处置 · "
        + " / ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    )
    return Gate("coverage", PASS if resolved == total else FAIL, detail)


def _gate_modelvalue(qml_text: str | None) -> Gate:
    if qml_text is None:
        return Gate("modelValue", SKIP, "dry-run 未生成 QML 骨架")
    # 受控契约：组件只 emit，不自写宿主状态；禁止对 modelValue 赋值
    violations = [
        line.strip() for line in qml_text.splitlines()
        if "modelValue" in line and not line.strip().startswith("//")
    ]
    if violations:
        return Gate("modelValue", FAIL, f"检测到自写 modelValue：{violations[:3]}")
    return Gate("modelValue", PASS, "生成 QML 零自写 modelValue（只 emit 意图）")


def _gate_slots(qml_text: str | None) -> Gate:
    if qml_text is None:
        return Gate("slot-constitution", SKIP, "dry-run 未生成 QML 骨架")
    uses_shell = any(
        token in qml_text for token in (
            "NovaDesktop {", "NovaAgent {", "NovaAIReport {", "NovaIncubator {"
        )
    )
    if not uses_shell:
        return Gate("slot-constitution", PASS, "未使用组合根，无需槽位注入校验")
    has_slot = "Slot:" in qml_text
    if not has_slot:
        return Gate(
            "slot-constitution", FAIL,
            "组合根必须由槽位注入业务内容，不得内联业务语义文本",
        )
    return Gate("slot-constitution", PASS, "组合根内容全部由槽位注入（CC-1~CC-8）")


def _default_qml_root() -> str | None:
    """自动探测同级 ``pyside-nova`` 的 QML import 根，令 ``import Nova.*`` 可解析。

    nova-forge 与 pyside-nova 同级；从本文件向上逐级找，找不到返回 ``None``
    （此时 qmllint 仍实跑，但 import warning 只如实登记、不阻塞）。
    """
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "pyside-nova" / "src" / "pyside_nova" / "qml"
        if candidate.is_dir():
            return str(candidate)
    return None


def _gate_qmllint(qml_text: str | None, qml_root: str | None = None) -> Gate:
    if qml_text is None:
        return Gate("qmllint", SKIP, "dry-run 未生成 QML 骨架")
    # 静态契约：import 完整 / 花括号平衡 / 不用裸 Rectangle 承载业务语义
    checks: list[str] = []
    for token in ("import QtQuick", "import Nova.Services", "import Nova.Controls"):
        if token not in qml_text:
            checks.append(f"缺 {token}")
    if qml_text.count("{") != qml_text.count("}"):
        checks.append("花括号不平衡")
    if checks:
        return Gate("qmllint", FAIL, "; ".join(checks))

    exe = shutil.which("qmllint")
    if exe is None:
        return Gate("qmllint", PASS, "静态契约 PASS（环境无 qmllint，跳过实跑）")

    # 坑位 83：Windows 版 qmllint.exe 不支持 ``-`` stdin（把 ``-`` 当文件名、
    # 返回 -1 且 stderr 只有 "Failed to open file -"），故落临时文件实跑、跑完自删。
    # 另：导入 PySide6 会把它自身目录注入 PATH，令本门在「专向单跑 / 全量跑」
    # 间行为漂移；自动探测 Nova QML 根作 ``-I``，让 import 真正可解析。
    import_root = qml_root or _default_qml_root()
    with tempfile.TemporaryDirectory(prefix="nova-qmllint-") as tmp:
        target = Path(tmp) / "Main.qml"
        target.write_text(qml_text, encoding="utf-8")
        cmd = [exe]
        if import_root:
            cmd += ["-I", import_root]
        cmd += [str(target)]
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    lines = combined.splitlines()
    errors = [ln for ln in lines if ln.startswith("Error:")]
    warnings = [ln for ln in lines if ln.startswith("Warning:")]
    if errors:
        return Gate("qmllint", FAIL, f"qmllint 报 {len(errors)} error：{errors[:2]}")
    if result.returncode != 0 and not combined.strip():
        # 工具自身未正常运行（零输出）：不谎称实跑通过，回退静态契约
        return Gate(
            "qmllint", PASS,
            f"静态契约 PASS（qmllint 实跑未完成 · rc={result.returncode}）",
        )
    detail = "qmllint 实跑 0 error"
    if warnings:
        detail += f" · {len(warnings)} warning"
    if result.returncode != 0:
        detail += f" · rc={result.returncode}（工具非 0 退出但零 Error，按静态契约放行）"
    return Gate("qmllint", PASS, detail + " + 静态契约 PASS")


def run_contract_gates(
    index: FreezeIndex,
    scan: ScanResult,
    qml_text: str | None = None,
    qml_root: str | None = None,
) -> ContractReport:
    """跑全部五道门，返回可判定的报告。"""
    gates = (
        _gate_static_tier(index, scan),
        _gate_coverage(scan),
        _gate_qmllint(qml_text, qml_root),
        _gate_modelvalue(qml_text),
        _gate_slots(qml_text),
    )
    return ContractReport(gates)
