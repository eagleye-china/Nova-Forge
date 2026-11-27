# scripts/verify_prescript_gui.py
# 创建时间：星期四 2026-11-26 19:53
"""离屏实跑 ``prescript --gui`` 主窗口：收集 QML 运行时告警 + 同步抓图。

用法：
    PRESCRIPT_GUI_SHOT=docs/prescript-gui.png python scripts/verify_prescript_gui.py

退出码：0 = 根对象存在且无 ERROR；2 = 加载失败 / 降级；3 = 有运行时 ERROR。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

from PySide6.QtCore import (
    QEventLoop,
    QMetaObject,
    QObject,
    QPointF,
    Qt,
    QTimer,
    qInstallMessageHandler,
)
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import getCppPointer, wrapInstance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nova_forge.command import cmd_prescript  # noqa: E402


def main() -> int:
    messages: list[str] = []

    def handler(_mode, _ctx, message: str) -> None:
        messages.append(message)

    qInstallMessageHandler(handler)

    app = QApplication.instance() or QApplication(sys.argv[:1])
    cmd_prescript.run_prescript_gui()

    if not cmd_prescript._GUI_KEEPALIVE:
        print("✗ 未创建 QML 引擎（GUI 已降级到命令行模式）")
        for m in messages[:12]:
            print("   ", m)
        return 2

    engine = cmd_prescript._GUI_KEEPALIVE[-1][0]
    roots = engine.rootObjects()
    if not roots:
        print("✗ QML 主窗口加载失败")
        for m in messages[:12]:
            print("   ", m)
        return 2

    window = roots[0]  # 立即持引用：进入事件循环后会被降级成 QWindow 包装

    bridge = cmd_prescript._GUI_KEEPALIVE[-1][1]
    print("三重校验（配置态实况）：")
    for c in bridge.checks:
        mark = "PASS" if c["ok"] else "WAIT"
        print(f"   [{mark}] {c['label']} · {c['detail']}")
    summary = bridge.summary
    print(f"   预览：{summary.get('fileCount', 0)} 个文件 · {summary.get('bytes', 0)} B"
          f" · 配方 {summary.get('recipe', '—')} · 壳 {summary.get('shell', '—')}")

    shot = os.environ.get("PRESCRIPT_GUI_SHOT")
    if shot:
        # 同步抓图：此刻 rootObjects 仍是 QQuickWindow 包装
        image = QQuickWindow.grabWindow(window)
        if not image.isNull():
            image.save(shot)
            print(f"📸 截图：{shot} ({image.width()}×{image.height()})")
        else:
            print("⚠ 抓图为空（不影响运行时判定）")

    # ── 折叠态验证：走壳受控契约 toggleRecipe / toggleValidate（只 emit 意图）──
    collapse_shot = Path(shot).with_name("prescript-gui-collapsed.png") if shot else None
    if collapse_shot:
        def _find_shell(item):
            for child in item.childItems():
                if child.metaObject().className().startswith("NovaIncubator"):
                    return child
                found = _find_shell(child)
                if found is not None:
                    return found
            return None

        shell_item = _find_shell(window.contentItem())
        if shell_item is None:
            print("⚠ 未找到 NovaIncubator 实例，跳过折叠态验证")
        else:
            def _wait(ms: int) -> None:
                loop = QEventLoop()
                QTimer.singleShot(ms, loop.quit)
                loop.exec()

            QMetaObject.invokeMethod(shell_item, "toggleRecipe", Qt.DirectConnection)
            QMetaObject.invokeMethod(shell_item, "toggleValidate", Qt.DirectConnection)
            _wait(500)  # 等宽度动画走完
            collapsed = (shell_item.property("recipeCollapsed"), shell_item.property("validateCollapsed"))
            img2 = QQuickWindow.grabWindow(window)
            if not img2.isNull():
                img2.save(str(collapse_shot))
                print(f"📸 折叠态截图：{collapse_shot} ({img2.width()}×{img2.height()})")
            print(f"   折叠回写：recipeCollapsed={collapsed[0]} · validateCollapsed={collapsed[1]}")
            QMetaObject.invokeMethod(shell_item, "toggleRecipe", Qt.DirectConnection)
            QMetaObject.invokeMethod(shell_item, "toggleValidate", Qt.DirectConnection)
            _wait(500)  # 展开复原后再做预览 / 闸门演练
            restored = (shell_item.property("recipeCollapsed"), shell_item.property("validateCollapsed"))
            print(f"   展开复原：recipeCollapsed={restored[0]} · validateCollapsed={restored[1]}")

    # ── 界面预览浮层验证：真 QML 实装渲染所选配方的 Stage.qml ──
    if shot:
        def _wait2(ms: int) -> None:
            loop = QEventLoop()
            QTimer.singleShot(ms, loop.quit)
            loop.exec()

        def _find_shell_pv(item):
            for child in item.childItems():
                if child.metaObject().className().startswith("NovaIncubator"):
                    return child
                found = _find_shell_pv(child)
                if found is not None:
                    return found
            return None

        # 徽记可点（pyside-nova 1.3.0 additive）：emit emblemClicked → 预览自动打开
        shell_pv = _find_shell_pv(window.contentItem())
        if shell_pv is not None:
            QMetaObject.invokeMethod(shell_pv, "emblemClicked", Qt.DirectConnection)
            _wait2(300)
            emblem_open = window.property("previewOpen")
            print(f"   徽记点击：emblemClickable={shell_pv.property('emblemClickable')}"
                  f" · previewOpen={emblem_open}（应 True）")
            if emblem_open is not True:
                print("✗ 徽记点击未打开预览浮层")

        # 徽记 tooltip（pyside-nova 1.3.0 emblemToolTip）：真实鼠标悬停验证。
        # ⚠️ 不用「set modelValue」自证——那绕过了整条悬停触发链，曾两次误判为修好。
        # 这里用 QTest.mouseMove 把真实鼠标移到徽记 MouseArea 中心，等 500ms 延迟 Timer，
        # 断言 visible=True；再移开断言 False。target 是 var 属性经 property() 取回会降级
        # 成 QObject，用 shiboken 还原 QQuickItem 才能 mapToScene。
        tip = window.findChild(QObject, "incubatorEmblemTooltip")
        if tip is not None:
            tgt = wrapInstance(getCppPointer(tip.property("target"))[0], QQuickItem)
            emblem_pos = tgt.mapToScene(QPointF(tgt.width() / 2, tgt.height() / 2)).toPoint()
            QTest.mouseMove(window, emblem_pos)
            _wait2(750)  # 延迟 500ms + 余量
            tip_shown = tip.property("visible")
            QTest.mouseMove(window, QPointF(20, 20).toPoint())
            _wait2(250)
            tip_hidden = not tip.property("visible")
            print(f"   徽记tooltip：text={tip.property('text')!r}"
                  f" · 真实hover visible={tip_shown}（应 True）"
                  f" · 移开 hidden={tip_hidden}（应 True）")
            if tip_shown is not True or tip_hidden is not True:
                print("✗ 徽记 tooltip 真实悬停显隐失败")

        preview_shot = Path(shot).with_name("prescript-gui-preview.png")
        # QML 方法带参 invokeMethod 在 PySide6 上签名不匹配（实测），
        # 走等价路径：先写窗口属性，再调无参 loadPreview()。
        window.setProperty("previewKind", "chat")
        window.setProperty("previewOpen", True)
        QMetaObject.invokeMethod(window, "loadPreview", Qt.DirectConnection)
        _wait2(1200)  # 等 Loader 加载临时副本 Stage.qml
        # Loader.status 枚举无法跨 PySide6 转换（实测），用窗口级 int 别名 previewStatus
        status = window.property("previewStatus")
        print(f"   预览浮层：previewKind={window.property('previewKind')}"
              f" · Loader status={status}（1=Ready）")
        if window.property("previewOpen") is not True:
            print("✗ 预览浮层未打开")
        elif status != 1:
            print("✗ Stage.qml 实装渲染未就绪（Loader 未 Ready）")
        img3 = QQuickWindow.grabWindow(window)
        if not img3.isNull():
            img3.save(str(preview_shot))
            print(f"📸 预览浮层截图：{preview_shot} ({img3.width()}×{img3.height()})")
        # 换配方实装：预览独立选型，不改工作台配置态
        window.setProperty("previewKind", "flex")
        QMetaObject.invokeMethod(window, "loadPreview", Qt.DirectConnection)
        _wait2(1200)
        status_flex = window.property("previewStatus")
        bench_kind = bridge.kind
        print(f"   切换预览：previewKind={window.property('previewKind')}"
              f" · Loader status={status_flex} · 工作台配置态 kind={bench_kind}（应仍为 chat）")
        if bench_kind != "chat":
            print("✗ 预览选型污染了工作台配置态")
        window.setProperty("previewOpen", False)
        _wait2(200)

    # ── 输入框回显同步（坑位 53 回归）：宿主写 modelValue 回显 bridge.path 时，
    # NovaInput 修复后提交值必须等于写入值，不得把旧文本经
    # onModelValueChanged → setPath 送回桥接层（曾致浏览选目录后被静默回退）。
    path_input = window.findChild(QObject, "pathInput")
    if path_input is not None:
        import tempfile as _tf

        def _wait_echo(ms: int) -> None:
            loop = QEventLoop()
            QTimer.singleShot(ms, loop.quit)
            loop.exec()

        _probe_target = _tf.mkdtemp(prefix="prescript_echo_").replace("\\", "/")
        _before = bridge.path
        path_input.setProperty("modelValue", _probe_target)
        _wait_echo(200)
        _after = bridge.path
        print(f"   输入框回显：写入 {_probe_target}")
        print(f"               bridge.path = {_after} · "
              f"同步{'✓' if Path(_after) == Path(_probe_target) else '✗ 回退（坑位 53 复发）'}")
        if Path(_after) != Path(_probe_target):
            print("✗ NovaInput 回显回退复发")
        bridge.setPath(_before)  # 复原配置态，不干扰后续演练
        _wait_echo(100)

    # ── T23：README 按钮 → NovaMarkdown 渲染 md（不是裸 Text 源码）──
    # 真实鼠标点击 readmeBtn，断言 readmeMarkdown 组件已装载、大纲已解析、
    # markdown 与 bridge.readmeDoc.renderText 逐字同源（显示适配版，图片降级为
    # 文本占位 → 坑位 76 零告警）、逐字原文仍在 readmeDoc.text、empty=false。
    def _wait_md(ms: int) -> None:
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    readme_btn = window.findChild(QObject, "readmeBtn")
    if readme_btn is not None:
        btn_item = wrapInstance(getCppPointer(readme_btn)[0], QQuickItem)
        btn_pos = btn_item.mapToScene(
            QPointF(btn_item.width() / 2, btn_item.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, btn_pos)
        _wait_md(400)  # 等 200ms 展开动画 + Markdown 分块解析

    md = window.findChild(QObject, "readmeMarkdown")
    if md is None:
        print("✗ 未找到 NovaMarkdown 实例（readmeMarkdown）—— QML 类型未解析？")
    else:
        # readonly property var 经 property() 取回是 QJSValue，须 toVariant()
        # 才能当 Python list 用（T21 坑位：QML 侧 var 不自动降级）。
        toc = md.property("toc")
        toc_list = toc.toVariant() if hasattr(toc, "toVariant") else toc
        text = md.property("markdown")
        empty = md.property("empty")
        visible = md.property("visible")
        expected = bridge.readmeDoc["renderText"]
        verbatim = bridge.readmeDoc["text"]
        toc_len = len(toc_list) if toc_list else 0
        print(f"   README 渲染：visible={visible} · toc={toc_len} 条大纲"
              f" · empty={empty} · markdown {len(text or '')} 字符"
              f" · 与 renderText 逐字同源={text == expected}"
              f" · 原文 text {len(verbatim)} 字符（图片占位已降级）")
        if visible is not True or toc_len == 0 or empty is not False:
            print("✗ NovaMarkdown 未正确渲染（visible/toc/empty 不达标）")
        if text != expected:
            print("✗ markdown 内容与 bridge 单一事实源不一致")
        if "![" in (text or "") or "screenshots/" in (text or ""):
            print("✗ 仍残留相对图片引用，会触发 Cannot open 告警")
        if shot:
            readme_shot = Path(shot).with_name("prescript-gui-readme.png")
            img_md = QQuickWindow.grabWindow(window)
            if not img_md.isNull():
                img_md.save(str(readme_shot))
                print(f"📸 README 展开截图：{readme_shot}"
                      f" ({img_md.width()}×{img_md.height()})")
        # 坑位 76 观感取证：滚到「三态装配图」章节，确认图片占位后表格
        # 仍是连续等高网格、不裁字、不撑爆 400px 英雄卡。
        try:
            from PySide6.QtQml import QQmlExpression, qmlContext

            ex = QQmlExpression(qmlContext(md), md,
                                "scrollToAnchor('三态装配图')")
            ex.evaluate()
            _wait_md(250)
            if shot:
                tbl_shot = Path(shot).with_name("prescript-gui-readme-table.png")
                img_tbl = QQuickWindow.grabWindow(window)
                if not img_tbl.isNull() and img_tbl.save(str(tbl_shot)):
                    print(f"📸 README 表格区截图：{tbl_shot}")
        except Exception as exc:  # 附加取证失败不干扰门禁判定
            print(f"⚠ 表格区取证跳过：{exc}")
        # 复位收起，不干扰后续闸门演练
        if readme_btn is not None:
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, btn_pos)
            _wait_md(250)

    QTimer.singleShot(1500, app.quit)

    # 端到端演练（PRESCRIPT_GUI_HATCH=1）：在真实 GUI 进程里模拟人工确认闸门
    # 落盘一次 + 未确认拒绝一次，验证「壳只 emit 意图、确认后才写盘」全链路。
    if os.environ.get("PRESCRIPT_GUI_HATCH"):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            bridge.setPath(str(Path(tmp) / "gui-hatch-root"))
            bridge.setName("GUI Hatch Demo")
            refused = bridge.hatch(False)
            # 项目落在根目录之下以包名建的子目录（CSA 2026-11-27 拍板）
            refused_dir = Path(tmp) / "gui-hatch-root" / "gui_hatch_demo"
            print(f"   闸门拒绝：ok={refused['ok']} · 已落盘={refused['written']}"
                  f" · 目录未创建={not refused_dir.exists()}")
            accepted = bridge.hatch(True)
            main_qml = refused_dir / "src" / accepted.get("summary", {}).get(
                "package", "gui_hatch_demo") / "qml" / "Main.qml"
            print(f"   确认孵化：ok={accepted['ok']} · 已落盘={accepted['written']}"
                  f" · Main.qml 存在={main_qml.exists()} · {accepted['message']}")

    app.exec()

    # 坑位 76：资源加载失败（Cannot open）与绑定环同列为「坏消息」，
    # 不能只按字面 "error" 放行 —— 否则 708 条图片告警会被误判为无害。
    errors = [m for m in messages
              if "error" in m.lower() or "Cannot open" in m
              or "Binding loop" in m or "failed" in m.lower()]
    warnings = [m for m in messages if m not in errors]
    print(f"✓ 根对象 {len(roots)} 个 · NovaIncubator 七槽主窗口 · 离屏运行 1.5 s"
          f" · Qt 消息 {len(messages)} 条 · 坏消息 {len(errors)} 条")
    if messages:
        from collections import Counter
        for msg, count in Counter(messages).most_common(6):
            print(f"   [{count}×] {msg[:150]}")
    if warnings:
        print(f"⚠ 其余告警 {len(warnings)} 条")
    if errors:
        print(f"✗ 坏消息 {len(errors)} 条：")
        for m in errors[:12]:
            print("   ", m)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
