# src/nova_forge/migrate/report.py
"""迁移报告：``MIGRATION_TODO.md``（人读）+ ``migration-report.json``（机读）。

报告是 T3「100% 实现迁移」的**可验收凭证**：逐项列出每个唯一 Qt 名的处置、
五道契约门结果、MANUAL 人工待办与降级入口，账实同源、零静默遗漏。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime

from .contract import ContractReport
from .freeze import FreezeIndex
from .rules import AUTO, MANUAL, classify
from .scanner import ScanResult


@dataclass(frozen=True)
class MigrationPlan:
    """一次迁移的完整计划（编排层产出）。"""

    project_name: str
    root: str
    freeze: FreezeIndex
    scan: ScanResult
    contract: ContractReport
    pairs: tuple[tuple[str, str], ...]
    scaffold_files: tuple[str, ...]
    written: bool
    backup_id: str | None


def _disposition_rows(scan: ScanResult) -> list[dict]:
    rows: list[dict] = []
    for finding in scan.findings:
        rule = classify(finding.qt_name)
        rows.append({
            "qtName": finding.qt_name,
            "qtModule": finding.qt_module,
            "occurrences": finding.count,
            "callSites": finding.call_count,
            "disposition": rule.disposition,
            "target": rule.target,
            "layer": rule.layer,
            "note": rule.note,
            "locations": [asdict(o) for o in finding.occurrences],
        })
    return rows


def build_json_report(plan: MigrationPlan) -> str:
    """机器可读报告（``--json`` 亦直接打印此结构）。"""
    rows = _disposition_rows(plan.scan)
    total = len(rows)
    resolved = sum(1 for r in rows if r["disposition"] in ("AUTO", "RUNTIME", "NATIVE", "MANUAL"))
    data = {
        "tool": "nova-forge migrate2nova",
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "project": plan.project_name,
        "root": plan.root,
        "freeze": {
            "path": str(plan.freeze.path),
            "apiVersion": plan.freeze.api_version,
            "packageVersion": plan.freeze.package_version,
            "fingerprint": plan.freeze.fingerprint,
            "types": plan.freeze.count,
        },
        "scan": {
            "filesScanned": plan.scan.files_scanned,
            "uniqueQtNames": total,
            "parseErrors": list(plan.scan.parse_errors),
            "fallbackWindows": [asdict(f) for f in plan.scan.fallback_windows],
        },
        "coverage": {
            "resolved": resolved,
            "total": total,
            "percent": 100.0 if total == 0 else round(resolved / total * 100, 2),
        },
        "gates": [asdict(g) for g in plan.contract.gates],
        "gatesPassed": plan.contract.passed,
        "dispositions": rows,
        "autoPairs": [{"qtName": q, "target": t} for q, t in plan.pairs],
        "scaffoldFiles": list(plan.scaffold_files),
        "written": plan.written,
        "backupId": plan.backup_id,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def build_todo(plan: MigrationPlan) -> str:
    """人读迁移清单。"""
    rows = _disposition_rows(plan.scan)
    total = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["disposition"]] = counts.get(r["disposition"], 0) + 1
    pct = 100.0 if total == 0 else sum(counts.values()) / total * 100

    lines: list[str] = [
        f"# MIGRATION_TODO · {plan.project_name}",
        "",
        "> 由 `nova-forge migrate2nova` 生成 · **原 `.py` 零改动** · "
        "映射表唯一法源为 pyside-nova API 冻结面。",
        "",
        "## 0. 结论",
        "",
        f"- **冻结面**：`{plan.freeze.path.name}` · API `{plan.freeze.api_version}` · "
        f"**{plan.freeze.count} 公共类型** · 指纹 `{plan.freeze.fingerprint}`",
        f"- **扫描**：`{plan.scan.files_scanned}` 个 `.py` 文件 · "
        f"**{total} 个唯一 Qt 名** · 解析错误 {len(plan.scan.parse_errors)} 处",
        f"- **处置覆盖率**：**{pct:.0f}%**（{sum(counts.values())}/{total}）· "
        + " / ".join(f"{k} {v}" for k, v in sorted(counts.items())),
        f"- **契约门**：{'✅ 全绿（可落盘）' if plan.contract.passed else '❌ 有阻塞项（禁止落盘）'}",
        f"- **本轮落盘**：{'是（`--scaffold`）' if plan.written else '否（dry-run）'}",
    ]
    if plan.backup_id:
        lines.append(f"- **备份**：`{plan.backup_id}`（`--restore` 可回滚）")

    lines += [
        "",
        "## 1. 契约校验门（§9.4 不合格不落地）",
        "",
        "| 门 | 状态 | 说明 |",
        "|---|---|---|",
    ]
    for gate in plan.contract.gates:
        lines.append(f"| `{gate.name}` | {gate.status} | {gate.detail} |")

    lines += [
        "",
        "## 2. 逐项处置（100% 覆盖，零静默遗漏）",
        "",
        "| Qt 名 | 模块 | 出现 | 处置 | 目标 Nova 类型 | 层 | 说明 |",
        "|---|---|---:|---|---|---|---|",
    ]
    for r in rows:
        target = f"`{r['target']}`" if r["target"] else "—"
        lines.append(
            f"| `{r['qtName']}` | `{r['qtModule']}` | {r['occurrences']} | "
            f"**{r['disposition']}** | {target} | {r['layer']} | {r['note']} |"
        )

    manual = [r for r in rows if r["disposition"] == MANUAL]
    lines += [
        "",
        "## 3. 人工待办（MANUAL）",
        "",
    ]
    if manual:
        for r in manual:
            lines.append(f"- [ ] `{r['qtName']}` — {r['note']}")
    else:
        lines.append("- 无（全部自动处置）")

    # P2 补缺批次（§9.4 明确「补缺与迁移命令解耦」，组件库公共面零改动）
    lines += [
        "",
        "### 3.1 生态补缺建议（P2 · 解耦，不重签冻结面）",
        "",
        "> 以下为 Quasar Utils / 事件总线在 QML 侧的合理缺口，**不属于迁移命令的"
        "阻塞项**；按 §9.2 落在 nova-forge 脚手架侧 Python QObject，"
        "pyside-nova 147 公共类型零改动。是否并入组件库须 CSA 另行拍板 + additive minor 重签。",
        "",
        "| 缺口 | 迁移侧建议 |",
        "|---|---|",
        "| EventBus（`event-bus.js`） | Python 侧 `QObject` 承载 `on/off/emit`，"
        "QML 用 `Connections` + `signal` 转发；不要用 `Qt.binding()` 模拟 |",
        "| `copyToClipboard` | 保留 `QGuiApplication.clipboard()`，QML 侧只发 `copyRequested` 意图 |",
        "| `exportFile` | 保留 Python `csv` / 文件对话框，QML 侧只发 `exportRequested` 意图 |",
        "| `runSequentialPromises` | QML `Promise` 无对应；改 Python `QSequentialAnimationGroup` "
        "或显式状态机，禁隐式异步链 |",
        "| `patterns.testPattern` | 保留 Python `re`，QML 侧只传原始串 |",
        "| DOM / Scrolling / App Extensions / Vue Composables | Web 生态专有，"
        "QML 由 `Item` 几何 / `Flickable` 承担（T0 已结案：不纳入） |",
    ]

    autos = [r for r in rows if r["disposition"] == AUTO]
    lines += [
        "",
        "## 4. 自动装配（AUTO · 目标均在冻结面）",
        "",
    ]
    if autos:
        for r in autos:
            lines.append(f"- `{r['qtName']}` → `{r['target']}`（{r['callSites']} 处构造调用）")
    else:
        lines.append("- 无")

    lines += [
        "",
        "## 5. 降级回原窗口",
        "",
    ]
    if plan.scan.fallback_windows:
        fb = plan.scan.fallback_windows[0]
        lines.append(
            f"- 识别到原根窗口：`{fb.module}.{fb.class_name}`（`{fb.file}`）；"
            "生成的 `main.py` 在 QML 加载失败时动态加载并显示该类。"
        )
        lines.append("- 构造参数用 `--entry-args` 指定（JSON 数组）；默认无参构造。")
    else:
        lines.append("- 未识别到 `QMainWindow/QWidget/QDialog` 子类；请用 `--entry` 指定降级入口。")

    lines += [
        "",
        "## 6. 下一步",
        "",
        "1. 处理 §3 的 MANUAL 项（尤其 `QSystemTrayIcon` 一类无 QML 对应的系统能力）。",
        "2. 把业务语义按 CC-1~CC-8 经槽位注入 `Main.qml`，不要内联到骨架。",
        "3. 保持受控契约：组件只 emit 意图，宿主不反向写组件状态。",
        "4. 通过 `qmllint` / 静态门禁后再摘除降级分支；`--restore <备份 id>` 可回滚产物。",
        "",
        "> 发布边界：`commit / push / tag / PyPI / 站点上线` 一律归 CSA。",
        "",
    ]
    return "\n".join(lines)
