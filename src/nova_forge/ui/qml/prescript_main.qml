// src/nova_forge/ui/prescript_main.qml
// 创建时间：星期四 2026-11-26 19:48
// nova-forge prescript --gui 主窗口：pyside-nova `NovaIncubator` 七槽装配「应用孵化器工作台」。
// 七槽各司其职（壳只托管布局，业务语义全部由本宿主注入）：
//   globalSlot 身份 / 配方 / 主题
//   recipeSlot 九类配方库（catalog.KINDS 单源，点选即装载）
//   stageSlot  配置态表单（目录 / 应用名 / 包名 / 开关）+ 文件清单预览
//   validateSlot 三重校验台账
//   pipelineSlot CARF 四阶段
//   certificateSlot 孵化摘要 + 交付五件套
//   overlaySlot 人工确认闸门（只有点了「确认孵化」才落盘）
// 治理铁律：freezeRequested() 只 emit 意图；shell 与本宿主都绝不自动封版、绝不自动写盘。
import QtQuick
import QtQuick.Controls
import Nova.Services
import Nova.Controls
import Nova.Composite.LayoutShell

ApplicationWindow {
    id: win
    width: 1440
    height: 900
    minimumWidth: 1100
    minimumHeight: 680
    visible: true
    title: "Nova-Forge · 应用孵化器工作台"
    color: NovaTheme.page

    property bool gateOpen: false
    // 账实相符：frozen 不再是粘性旗标，直接跟随 bridge.written（当前配置真实落盘态）。
    // 桥接层保证：配置一变 written 即复位 false，已孵化徽章 / 已签发证书 / 已落盘同步回退。
    readonly property bool frozen: bridge ? bridge.written : false
    property int stageIndex: 1
    // Windows 原生标题栏不随 QML 主题变化：属性绑定 + 变化处理器同步 DWM 明暗。
    // 「暗色主题配白色标题栏」根因即此；窗口级属性是 QML 绑定，任何改 isDark 的路径都会触发。
    property bool chromeDark: NovaTheme.isDark
    onChromeDarkChanged: bridge.setDarkTitleBar(chromeDark)
    property bool previewOpen: false
    property string previewKind: ""   // 预览浮层独立选型，不改工作台配置态
    // 0=Null 1=Ready 2=Loading 3=Error（QML 侧转 int，供无头实跑断言）
    readonly property int previewStatus: previewLoader.status
    // 初始化闸：NovaInput 构造期会把 modelValue 重置一次并触发 onModelValueChanged，
    // ready=false 时不向 bridge 提交，避免把配置态清空（icons 同款防回环口径）。
    property bool ready: false
    readonly property var stages: ["Conceive 构想", "Achieve 实现", "Refine 打磨", "Freeze 封版"]
    // 当前配方代号：required-property delegate 的隔离创建上下文里 context property
    // 会解析为 null（真实运行环境实测），delegate 一律改走窗口级只读别名与函数——
    // id 解析是编译期绑定，不受运行时上下文影响。
    readonly property string currentKind: bridge ? bridge.kind : ""

    function chooseKind(code) {
        bridge.setKind(code)
        kindSelect.selectOption(code)
    }

    // 通知单一事实源：bridge.toast 信号与 T23 文档链接信号共用同一条
    // NovaNotify.show(config) 链路，避免两处各写一份 config。
    function showToast(kind, message) {
        var tint = NovaTheme.info
        if (kind === "positive") tint = NovaTheme.positive
        else if (kind === "negative") tint = NovaTheme.negative
        else if (kind === "warning") tint = NovaTheme.warning
        NovaNotify.show({
            message: message,
            tint: tint,
            position: "bottom-right",
            timeout: 3600
        })
    }

    Component.onCompleted: {
        // NovaOverlayHost / NovaDialog / NovaNotify 都靠这个找宿主窗口
        NovaScreen.source = win
        NovaTheme.setDark(true)
        bridge.setDarkTitleBar(true)   // 初始同步：暗色主题下原生标题栏也必须是暗色
        pathInput.modelValue = bridge.path
        nameInput.modelValue = bridge.name
        packageInput.modelValue = bridge.package
        forceBox.modelValue = bridge.force
        dryBox.modelValue = bridge.dryRun
        verifyBox.modelValue = bridge.verifyRun
        kindSelect.selectOption(bridge.kind)
        win.ready = true
    }

    // 体量人性化（CSA 22:22 指令）：达到 KB/MB/GB 就显示对应单位，不统一 B
    function fmtSize(n) {
        n = Number(n) || 0
        if (n >= 1073741824) return (n / 1073741824).toFixed(2) + " GB"
        if (n >= 1048576) return (n / 1048576).toFixed(2) + " MB"
        if (n >= 1024) return (n / 1024).toFixed(1) + " KB"
        return n + " B"
    }

    // ── 确认框 GroupBox 的主要文件 checkbox 组 ────────────────────
    // 全部取自 bridge.summary.keyFiles（与左侧 17 项组选框同一事实源），
    // 逐项可勾选；取消只置 included=false，不移除条目，随时可勾回。
    function keyFileOptions() {
        var out = []
        var keys = bridge.summary.keyFiles || []
        for (var i = 0; i < keys.length; i++)
            out.push({
                label: keys[i].path + "  ·  " + win.fmtSize(keys[i].size || 0),
                value: keys[i].path
            })
        return out
    }

    function keyFileValues() {
        var out = []
        var keys = bridge.summary.keyFiles || []
        for (var i = 0; i < keys.length; i++)
            if (keys[i].included) out.push(keys[i].path)
        return out
    }

    function syncKeyFiles(values) {
        if (!win.ready) return
        var keys = bridge.summary.keyFiles || []
        for (var i = 0; i < keys.length; i++) {
            var p = keys[i].path
            var now = values.indexOf(p) > -1
            if (now !== keys[i].included)
                bridge.setFileSelected(p, now)
        }
    }

    function activeKind() {
        for (var i = 0; i < bridge.kinds.length; i++)
            if (bridge.kinds[i].code === bridge.kind)
                return bridge.kinds[i]
        return null
    }

    // ── 界面预览：真 QML 实装渲染所选配方的 Stage.qml（非截图、非 mock）──
    function previewKindSpec() {
        var code = win.previewKind
        for (var i = 0; i < bridge.kinds.length; i++)
            if (bridge.kinds[i].code === code)
                return bridge.kinds[i]
        return null
    }

    function openPreview(kind) {
        win.previewKind = (kind && kind !== "") ? kind : win.currentKind
        win.previewOpen = true
        previewOverlay.forceActiveFocus()
        win.loadPreview()
    }

    function loadPreview() {
        previewError.visible = false
        previewHint.visible = true
        previewHint.text = "正在渲染 " + win.previewKind + " · " +
            (win.previewKindSpec() ? win.previewKindSpec().zh : "—") + " …"
        var uri = bridge.previewStage(win.previewKind)
        if (uri === "") {
            previewHint.visible = false
            previewError.visible = true
            return
        }
        previewLoader.source = uri
    }

    // 忙碌指示：宿主侧自绘的极光扫掠条。
    // 触发点记录（2026-11-26）：Services 单例 NovaLoadingBar._ensure() 硬编码
    // "qrc:/pyside_nova/qml/Nova/Controls/NovaAjaxBar.qml"，但该库只把 icons 编入
    // qrc、QML 走 engine.addImportPath 文件系统加载，此路径恒不存在 → start() 必然
    // 降级 no-op 并刷 4 条告警。属 pyside-nova 基础组件缺陷，按「装配态驱动、按需
    // 反哺，须记录触发点」在宿主侧规避并挂账，冻结面（144 / 1.2.0 / 指纹）零改动。
    Rectangle {
        id: busyBar
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 3
        z: 999
        visible: bridge.busy
        color: "transparent"
        Rectangle {
            id: busyGlint
            width: busyBar.width * 0.28
            height: parent.height
            radius: 1.5
            color: NovaTheme.primary
            NumberAnimation on x {
                from: -busyGlint.width
                to: busyBar.width
                duration: 1100
                loops: Animation.Infinite
                running: bridge.busy
            }
        }
    }

    NovaIncubator {
        id: shell
        objectName: "incubatorShell"   // 离屏验收：真实事件链读取折叠态
        anchors.fill: parent
        breakpoint: 1100
        // 证书栏加高到 210：容纳「标题 + 应用信息行 + 五行交付物行卡」（Showcase 基准 190）
        certificateHeight: 210
        // pyside-nova 1.3.0 additive：壳身份徽记（七区分格环）可点 → 界面预览。
        // CSA 原始愿望达成：点小太阳即看所选应用的真实界面；tooltip 即入口说明，
        // hero 卡的独立按钮已由徽记取代（一功能一入口，不重复）。
        emblemClickable: true
        emblemToolTip: "界面预览"

        // 受控契约：壳只 emit 折叠意图，宿主写回状态
        onRecipeToggled: function(collapsed) { shell.recipeCollapsed = collapsed }
        onValidateToggled: function(collapsed) { shell.validateCollapsed = collapsed }
        // 冻结意图 → 只打开人工确认闸门，绝不落盘
        onFreezeRequested: bridge.requestHatch()
        // 徽记点击 → 界面预览（当前配方）
        onEmblemClicked: win.openPreview("")

        // ── ① 全局栏：身份 / 配方代号 / 主题 / 请求孵化 ──────────
        globalSlot: Item {
            anchors.fill: parent
            // ── 左右轨隐显按钮（T16）：从底部管道条移到窗口左上角 / 右上角 ──
            // 与身份徽记同排，手指不用来回跑；壳受控契约不变——按钮只 emit
            // 折叠意图，宿主通过 onRecipeToggled / onValidateToggled 写回状态。
            Rectangle {
                id: foldRecipeBtn
                objectName: "foldRecipeBtn"
                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                width: 30; height: 30; radius: 6
                color: shell.recipeCollapsed
                    ? NovaTheme.surfaceAlt
                    : Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                border.width: 1
                border.color: shell.recipeCollapsed ? NovaTheme.outline : NovaTheme.primary
                Rectangle {
                    x: 7; y: 8; width: 16; height: 14; radius: 2
                    color: "transparent"
                    border.width: 1
                    border.color: shell.recipeCollapsed ? NovaTheme.textMuted : NovaTheme.primary
                }
                Rectangle {
                    x: 7; y: 8; width: 6; height: 14; radius: 2
                    color: shell.recipeCollapsed ? NovaTheme.textMuted : NovaTheme.primary
                }
                MouseArea {
                    id: foldRecipeArea
                    objectName: "foldRecipeArea"
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: shell.toggleRecipe()
                }
                ToolTip.visible: foldRecipeArea.containsMouse
                ToolTip.text: shell.recipeCollapsed ? "展开配方库" : "收起配方库"
            }
            Rectangle {
                id: brandMark
                anchors { left: foldRecipeBtn.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                width: 26; height: 26; radius: 8
                color: Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.20)
                border.width: 1
                border.color: NovaTheme.primary
                Text {
                    anchors.centerIn: parent
                    text: "🤝"
                    color: NovaTheme.primaryText
                    font.pixelSize: 13
                }
            }
            Column {
                anchors { left: brandMark.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 1
                Text {
                    text: "应用孵化器工作台"
                    color: NovaTheme.textColor
                    font { family: NovaTheme.fontFamily; pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "nova-forge prescript --gui · 全库 dogfooding · API " + bridge.apiVersion
                          + " · 配方 " + (bridge.summary.recipe || "—")
                    color: NovaTheme.textMuted
                    font.pixelSize: 9
                }
            }
            Row {
                anchors { right: foldValidateBtn.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 8
                NovaChip {
                    text: bridge.forgeVersion
                    outlined: true
                    dense: true
                }
                Rectangle {
                    width: 76; height: 26; radius: 13
                    color: win.frozen
                        ? Qt.rgba(NovaTheme.positive.r, NovaTheme.positive.g, NovaTheme.positive.b, 0.18)
                        : Qt.rgba(NovaTheme.warning.r, NovaTheme.warning.g, NovaTheme.warning.b, 0.16)
                    Text {
                        anchors.centerIn: parent
                        text: win.frozen ? "已孵化" : "待孵化"
                        color: win.frozen ? NovaTheme.positiveText : NovaTheme.warningText
                        font { pixelSize: 9; bold: true }
                    }
                }
                NovaBtn {
                    text: NovaTheme.isDark ? "☀ 亮色" : "🌙 深色"
                    size: "sm"
                    variant: "flat"
                    onClicked: NovaTheme.setDark(!NovaTheme.isDark)
                }
            }
            // 右上角：右轨（三重校验）隐显按钮，镜像图形（填充半轨在右侧）
            Rectangle {
                id: foldValidateBtn
                objectName: "foldValidateBtn"
                anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter }
                width: 30; height: 30; radius: 6
                color: shell.validateCollapsed
                    ? NovaTheme.surfaceAlt
                    : Qt.rgba(NovaTheme.primary.r, NovaTheme.primary.g, NovaTheme.primary.b, 0.16)
                border.width: 1
                border.color: shell.validateCollapsed ? NovaTheme.outline : NovaTheme.primary
                Rectangle {
                    x: 7; y: 8; width: 16; height: 14; radius: 2
                    color: "transparent"
                    border.width: 1
                    border.color: shell.validateCollapsed ? NovaTheme.textMuted : NovaTheme.primary
                }
                Rectangle {
                    x: 17; y: 8; width: 6; height: 14; radius: 2
                    color: shell.validateCollapsed ? NovaTheme.textMuted : NovaTheme.primary
                }
                MouseArea {
                    id: foldValidateArea
                    objectName: "foldValidateArea"
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: shell.toggleValidate()
                }
                ToolTip.visible: foldValidateArea.containsMouse
                ToolTip.text: shell.validateCollapsed ? "展开校验轨" : "收起校验轨"
            }
        }

        // ── ② 配方库：九类应用（catalog.KINDS 单源）────────────
        // 卡片风格对齐 Showcase 基准：左侧 3px 身份色条 + 选中提亮 + 手型光标。
        recipeSlot: Item {
            anchors.fill: parent
            Flickable {
                anchors.fill: parent
                contentWidth: width
                contentHeight: recipeCol.height + 48
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                Column {
                    id: recipeCol
                    // 顶部预留壳的身份装饰（五列配方栅）高度，避免标题重叠
                    anchors { top: parent.top; topMargin: 40; left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12 }
                    spacing: 8
                    Text {
                        text: "配方库 · 九类应用"
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontS; bold: true }
                    }
                    Text {
                        text: "catalog.KINDS 单源 · 点选即装载"
                        color: NovaTheme.textMuted
                        font.pixelSize: NovaTheme.fontXS
                    }
                    Repeater {
                        model: bridge.kinds
                        Rectangle {
                            required property var modelData
                            width: recipeCol.width
                            height: 56
                            radius: 6
                            color: modelData.code === win.currentKind
                                ? Qt.lighter(NovaTheme.surfaceAlt, 1.08) : "transparent"
                            Rectangle {
                                anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                                width: 3
                                radius: 1
                                color: modelData.code === win.currentKind ? NovaTheme.primary : NovaTheme.outline
                            }
                            // 应用图标：九配方各自专属色相，source 来自 catalog.Kind.icon 单一事实源
                            Image {
                                anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
                                width: 32; height: 32
                                source: modelData.icon
                                sourceSize: Qt.size(64, 64)
                                fillMode: Image.PreserveAspectFit
                                asynchronous: false
                                opacity: modelData.code === win.currentKind ? 1.0 : 0.72
                            }
                            Column {
                                anchors { left: parent.left; leftMargin: 54; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                spacing: 4
                                Row {
                                    spacing: 8
                                    Text {
                                        text: modelData.recipe
                                        color: NovaTheme.primary
                                        font { pixelSize: NovaTheme.fontXS; bold: true }
                                    }
                                    Text {
                                        text: modelData.zh
                                        color: NovaTheme.textColor
                                        elide: Text.ElideRight
                                        font { pixelSize: NovaTheme.fontS; bold: modelData.code === win.currentKind }
                                    }
                                }
                                Text {
                                    width: parent.width
                                    text: modelData.shell + " · " + modelData.tagline
                                    color: NovaTheme.textMuted
                                    elide: Text.ElideRight
                                    font.pixelSize: NovaTheme.fontXS
                                }
                            }
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: win.chooseKind(modelData.code)
                            }
                        }
                    }
                }
            }
        }

        // ── ③ 孵化舞台：配置态表单 + 文件清单预览 ──────────────
        stageSlot: Item {
            anchors.fill: parent
            Flickable {
                anchors.fill: parent
                contentWidth: width
                contentHeight: stageCol.height + 24
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                Column {
                    id: stageCol
                    x: 12
                    y: 12
                    width: parent.width - 24
                    spacing: 10

                    // 英雄卡（舞台标题卡，Showcase 基准）：主题色边框 + 左侧 3px 色条。
                    // T16 立 README 按钮；T23 改用 pyside-nova 的 NovaMarkdown
                    // 库组件渲染（不再是裸 Text 显示 md 源码）。内容仍为
                    // docs/components/<shell>.md（catalog.Kind.shell 单一事实源
                    // 推导），组件文档缺失时由 bridge.readmeDoc 回退到将落盘的
                    // README.md，不另立台账、不硬编码。
                    Rectangle {
                        id: heroCard
                        objectName: "heroCard"
                        width: parent.width
                        // T23：Markdown 渲染后标题/列表/表格占位更多，展开高度
                        // 330 → 400，给正文与内置 TOC 侧栏留足可视区（stageCol
                        // 在 Flickable 内，卡片增高不影响表单可达性）。
                        height: heroCard.readmeOpen ? 400 : 68
                        radius: 8
                        color: NovaTheme.surface
                        border.width: 1
                        border.color: NovaTheme.primary
                        property bool readmeOpen: false
                        Behavior on height {
                            NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                        }
                        Rectangle {
                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                            width: 3
                            radius: 1
                            color: NovaTheme.primary
                        }
                        Column {
                            anchors {
                                left: parent.left; leftMargin: 14
                                right: readmeBtn.left; rightMargin: 12
                                top: parent.top; topMargin: 12
                            }
                            spacing: 6
                            Row {
                                spacing: 10
                                Text {
                                    text: win.currentKind
                                    color: NovaTheme.primary
                                    font { pixelSize: NovaTheme.fontS; bold: true }
                                }
                                Text {
                                    text: win.activeKind() ? win.activeKind().zh : "—"
                                    color: NovaTheme.textColor
                                    elide: Text.ElideRight
                                    font { pixelSize: NovaTheme.fontM; bold: true }
                                }
                                Text {
                                    text: win.activeKind() ? "· " + win.activeKind().tagline : ""
                                    color: NovaTheme.textMuted
                                    elide: Text.ElideRight
                                    font.pixelSize: NovaTheme.fontXS
                                }
                            }
                            Text {
                                width: parent.width
                                text: win.activeKind()
                                    ? "壳 " + win.activeKind().shell + "  ·  " + win.activeKind().deliverables.length + " 项交付物  ·  三重校验全过 → 人工确认后落盘"
                                    : "选配方后在此装配"
                                color: NovaTheme.textMuted
                                elide: Text.ElideRight
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                        // 库组件优先：按钮用 NovaBtn；rightMargin 34 让出壳右上角的
                        // 身份徽记装饰位，避免与 emblem 点击区重叠。
                        NovaBtn {
                            id: readmeBtn
                            objectName: "readmeBtn"
                            anchors {
                                right: parent.right; rightMargin: 34
                                top: parent.top; topMargin: 12
                            }
                            text: heroCard.readmeOpen ? "✕ 收起" : "📄 README"
                            size: "sm"
                            variant: "outlined"
                            onClicked: heroCard.readmeOpen = !heroCard.readmeOpen
                        }
                        Text {
                            id: readmeCaption
                            objectName: "readmeCaption"
                            anchors {
                                left: parent.left; leftMargin: 14
                                right: parent.right; rightMargin: 14
                                top: parent.top; topMargin: 68
                            }
                            visible: heroCard.readmeOpen
                            text: bridge.readmeDoc.title + " · "
                                  + (bridge.summary.appName || "—")
                                  + " · 配方 " + (bridge.summary.recipe || "—")
                                  + " · " + bridge.readmeDoc.note
                            color: NovaTheme.primary
                            font { pixelSize: NovaTheme.fontXS; bold: true }
                            elide: Text.ElideRight
                        }
                        Rectangle {
                            id: readmePane
                            anchors {
                                left: parent.left; leftMargin: 12
                                right: parent.right; rightMargin: 12
                                top: readmeCaption.bottom; topMargin: 6
                                bottom: parent.bottom; bottomMargin: 10
                            }
                            visible: heroCard.readmeOpen
                            radius: 4
                            color: NovaTheme.page
                            border.width: 1
                            border.color: NovaTheme.outline
                        }
                        // T23：库组件优先 —— README 展开区直接装 pyside-nova 的
                        // NovaMarkdown（1.4.0 第 145 类型）。组件内部自带
                        // NovaScrollArea 滚动 + 内置 TOC 侧栏 + 空态，故整块替换
                        // 原「NovaScrollArea + 裸 Text(PlainText) 显示 md 源码」，
                        // 绝不双层滚动嵌套。内容走 bridge.readmeDoc.renderText
                        // 单一事实源（生成器产物 docs/components/<shell>.md 的显示
                        // 适配版：图片引用降级为文本占位，坑位 76；逐字原文仍在
                        // readmeDoc.text），缺失时回退将落盘的 README.md，
                        // 不另立台账、不硬编码。
                        NovaMarkdown {
                            id: readmeMarkdown
                            objectName: "readmeMarkdown"
                            anchors.fill: readmePane
                            anchors.margins: 1
                            visible: heroCard.readmeOpen
                            markdown: bridge.readmeDoc.renderText !== ""
                                ? bridge.readmeDoc.renderText
                                : "## 未找到 " + bridge.readmeDoc.title + "\n\n"
                                  + "请确认 pyside-nova 组件文档已安装，"
                                  + "或在下方清单勾回 `README.md`。"
                            showToc: true
                            tocStart: 1
                            tocEnd: 3
                            outlined: false
                            baseFontSize: NovaTheme.fontXS
                            openLinksExternally: false
                            a11yLabel: bridge.readmeDoc.title + " · 组件说明文档"
                            // 文档内含源码路径与站内锚点：不自动外开，
                            // 只交给宿主处理（组件已拦截 javascript:/data:/file:）。
                            // 复用窗口级 showToast(kind, message) 单一事实源，
                            // 与 bridge.toast 信号共用同一条 NovaNotify 链路。
                            onLinkClicked: function(url) {
                                win.showToast("info", "文档链接：" + url)
                            }
                            onLinkBlocked: function(url) {
                                win.showToast("warning", "已拦截危险链接：" + url)
                            }
                        }
                    }

                    // NovaCard 的默认属性进入其内部 Column，注入项不得用 anchors；
                    // 这里用 Item 包裹：卡片只当背景，表单作为兄弟布局。
                    Item {
                        width: parent.width
                        height: formCol.height + 24
                        NovaCard { anchors.fill: parent; bordered: true }
                        Column {
                            id: formCol
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                            spacing: 9

                            NovaSelect {
                                id: kindSelect
                                width: parent.width
                                label: "应用类型（九配方）"
                                emitValue: true
                                options: bridge.kindOptions
                                noOptionLabel: "未找到配方"
                                onModelValueChanged: {
                                    var v = (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                                    if (v !== "" && v !== bridge.kind)
                                        bridge.setKind(v)
                                }
                            }

                            Row {
                                width: parent.width
                                spacing: 8
                                NovaInput {
                                    id: pathInput
                                    objectName: "pathInput"
                                    width: parent.width - 116
                                    placeholder: "孵化根目录（项目将在其下以包名创建）"
                                    onModelValueChanged: {
                                        var v = (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                                        if (win.ready && v !== bridge.path)
                                            bridge.setPath(v)
                                    }
                                }
                                NovaBtn {
                                    width: 108
                                    // Row 只管水平布局，纵轴可用锚点：与左侧输入框垂直居中对齐
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: "📂 浏览"
                                    size: "sm"
                                    variant: "outlined"
                                    onClicked: {
                                        bridge.pickDirectory()
                                        pathInput.modelValue = bridge.path
                                    }
                                }
                            }

                            Row {
                                width: parent.width
                                spacing: 8
                                NovaInput {
                                    id: nameInput
                                    width: (parent.width - 8) / 2
                                    placeholder: "应用显示名"
                                    onModelValueChanged: {
                                        var v = (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                                        if (win.ready && v !== bridge.name)
                                            bridge.setName(v)
                                    }
                                }
                                NovaInput {
                                    id: packageInput
                                    width: (parent.width - 8) / 2
                                    placeholder: "包名（留空自动派生）"
                                    onModelValueChanged: {
                                        var v = (modelValue === null || modelValue === undefined) ? "" : String(modelValue)
                                        if (win.ready && v !== bridge.package)
                                            bridge.setPackage(v)
                                    }
                                }
                            }

                            NovaSeparator { width: parent.width }

                            Text {
                                text: "生成选项"
                                color: NovaTheme.textMuted
                                font { pixelSize: NovaTheme.fontXS; bold: true }
                            }
                            Row {
                                width: parent.width
                                spacing: 14
                                NovaCheckbox {
                                    id: forceBox
                                    label: "覆盖同名文件"
                                    dense: true
                                    modelValue: bridge.force
                                    onValueChanged: function(v) {
                                        forceBox.modelValue = v
                                        if (win.ready && v !== bridge.force) bridge.setForce(v)
                                    }
                                }
                                NovaCheckbox {
                                    id: dryBox
                                    label: "仅预览不落盘"
                                    dense: true
                                    modelValue: bridge.dryRun
                                    onValueChanged: function(v) {
                                        dryBox.modelValue = v
                                        if (win.ready && v !== bridge.dryRun) bridge.setDryRun(v)
                                    }
                                }
                                NovaCheckbox {
                                    id: verifyBox
                                    label: "离屏实跑校验"
                                    dense: true
                                    modelValue: bridge.verifyRun
                                    onValueChanged: function(v) {
                                        verifyBox.modelValue = v
                                        if (win.ready && v !== bridge.verifyRun) bridge.setVerifyRun(v)
                                    }
                                }
                            }

                            Row {
                                width: parent.width
                                spacing: 8
                                NovaBtn {
                                    text: "🔍 刷新预览"
                                    size: "sm"
                                    variant: "outlined"
                                    onClicked: bridge.preview()
                                }
                                NovaBtn {
                                    text: "↺ 重置结果"
                                    size: "sm"
                                    variant: "flat"
                                    onClicked: bridge.reset()
                                }
                                Item { width: parent.width - 240; height: 1 }
                                NovaSpinner {
                                    visible: bridge.busy
                                    size: 20
                                    variant: "ring"
                                }
                            }
                        }
                    }

                    Row {
                        width: parent.width
                        spacing: 8
                        NovaChip {
                            text: (bridge.summary.fileCount || 0) + " 个文件"
                            outlined: true
                            dense: true
                        }
                        NovaChip {
                            text: win.fmtSize(bridge.summary.bytes || 0)
                            outlined: true
                            dense: true
                        }                        NovaChip {
                            text: bridge.written ? "已落盘" : "未落盘"
                            filled: bridge.written
                            dense: true
                        }
                    }

                    // 触发点留痕：NovaMarkupTable 的 titleArea 未设 color 会在暗色主题
                    // 露出白条；本面板改为 NovaCheckbox 组选框列表，不再触发该问题。
                    Text {
                        width: parent.width
                        text: bridge.written
                            ? "已生成的文件（已落盘 · " + bridge.summary.fileCount + " 个）"
                            : "将生成的文件（勾选决定实际创建 · 未落盘）"
                        color: NovaTheme.textColor
                        font { pixelSize: NovaTheme.fontS; bold: true }
                    }
                    Row {
                        width: parent.width
                        spacing: 8
                        NovaBtn {
                            text: "全选"
                            size: "sm"
                            variant: "flat"
                            onClicked: bridge.selectAllFiles(true)
                        }
                        NovaBtn {
                            text: "清空"
                            size: "sm"
                            variant: "flat"
                            onClicked: bridge.selectAllFiles(false)
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: "PySide6 QML · src 布局 · " + bridge.fileChoices.length + " 个预知文件"
                            color: NovaTheme.textMuted
                            font.pixelSize: NovaTheme.fontXS
                            elide: Text.ElideRight
                        }
                    }
                    Flickable {
                        id: fileFlick
                        width: parent.width
                        height: 232
                        contentWidth: width
                        contentHeight: fileListCol.height
                        clip: true
                        Column {
                            id: fileListCol
                            width: parent.width
                            spacing: 2
                            Repeater {
                                id: fileChoicesRepeater
                                objectName: "fileChoicesRepeater"
                                model: bridge.fileChoices
                                Rectangle {
                                    objectName: "fileChoiceRow"
                                    required property int index
                                    required property var modelData
                                    width: parent.width
                                    height: 26
                                    radius: 3
                                    color: modelData.selected
                                        ? (index % 2 === 0 ? NovaTheme.surfaceAlt : "transparent")
                                        : "transparent"
                                    NovaCheckbox {
                                        anchors { left: parent.left; leftMargin: 4; verticalCenter: parent.verticalCenter }
                                        width: parent.width - 92
                                        label: modelData.path
                                        dense: true
                                        modelValue: modelData.selected
                                        onValueChanged: function(v) {
                                            if (win.ready && v !== modelData.selected)
                                                bridge.setFileSelected(modelData.path, v)
                                        }
                                    }
                                    Text {
                                        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                                        text: win.fmtSize(modelData.size)
                                        color: NovaTheme.textMuted
                                        font.pixelSize: NovaTheme.fontXS
                                    }
                                }
                            }
                        }
                    }

                    Text {
                        width: parent.width
                        text: bridge.statusText
                        color: NovaTheme.textMuted
                        font.pixelSize: NovaTheme.fontXS
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        width: parent.width
                        text: bridge.command
                        visible: bridge.command !== ""
                        color: NovaTheme.primaryText
                        font.pixelSize: NovaTheme.fontXS
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }

        // ── ④ 三重校验台账（Showcase 基准：左侧状态色条 + 编号 + 状态文字）──
        validateSlot: Item {
            anchors.fill: parent
            Column {
                id: validateCol
                anchors { top: parent.top; topMargin: 40; left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12 }
                spacing: 8
                Text {
                    text: "三重校验"
                    color: NovaTheme.textColor
                    font { pixelSize: NovaTheme.fontS; bold: true }
                }
                Text {
                    text: "配置态实时判定 · 全部 PASS 才开闸门"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: bridge.checks
                    Rectangle {
                        required property int index
                        required property var modelData
                        width: validateCol.width
                        height: 60
                        radius: 6
                        color: NovaTheme.surface
                        border.width: 1
                        border.color: NovaTheme.outline
                        Rectangle {
                            anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
                            width: 3
                            radius: 1
                            color: modelData.ok ? NovaTheme.positive : NovaTheme.warning
                        }
                        Column {
                            anchors { left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                            spacing: 4
                            Row {
                                spacing: 8
                                Text {
                                    text: String(index + 1)
                                    color: NovaTheme.primary
                                    font.pixelSize: NovaTheme.fontXS
                                }
                                Text {
                                    text: modelData.label
                                    color: NovaTheme.textColor
                                    font { pixelSize: NovaTheme.fontS; bold: true }
                                }
                                Text {
                                    text: modelData.ok ? "PASS" : "WAIT"
                                    color: modelData.ok ? NovaTheme.positive : NovaTheme.warning
                                    font { pixelSize: NovaTheme.fontXS; bold: true }
                                }
                            }
                            Text {
                                width: parent.width
                                text: modelData.detail
                                color: NovaTheme.textMuted
                                elide: Text.ElideRight
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                    }
                }
                Rectangle { width: validateCol.width; height: 1; color: NovaTheme.outline }
                Text {
                    width: validateCol.width
                    text: "结论 · 三层全过方可请求孵化"
                    color: NovaTheme.primary
                    font.pixelSize: NovaTheme.fontXS
                }
                Text {
                    width: validateCol.width
                    text: "治理边界：freezeRequested() 只 emit 意图；壳不自动封版。生成动作只在人工确认闸门之后落盘。"
                    color: NovaTheme.textMuted
                    wrapMode: Text.WordWrap
                    font.pixelSize: 8
                }
            }
        }

        // ── ⑤ CARF 四阶段（Showcase 基准：可点击阶段块 + 请求孵化钮）──
        // T16：左右轨折叠图标开关已移到 globalSlot 的左上角 / 右上角，
        // 底部管道条只留阶段块与请求孵化钮，回归纯粹的 CARF 进度语义。
        // 壳受控契约：toggleRecipe/toggleValidate 只 emit 意图，宿主写回。
        pipelineSlot: Item {
            id: pipelineHost
            anchors.fill: parent
            Row {
                anchors { horizontalCenter: parent.horizontalCenter; verticalCenter: parent.verticalCenter }
                spacing: 8
                Repeater {
                    model: win.stages
                    Rectangle {
                        required property int index
                        required property string modelData
                        width: Math.max(96, (pipelineHost.width - 400) / 4)
                        height: 30
                        radius: 6
                        color: index <= win.stageIndex ? NovaTheme.primary : NovaTheme.surfaceAlt
                        border.width: 1
                        border.color: index <= win.stageIndex ? NovaTheme.primary : NovaTheme.outline
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: index <= win.stageIndex ? NovaTheme.textOnPrimary : NovaTheme.textMuted
                            font.pixelSize: NovaTheme.fontXS
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: win.stageIndex = index
                        }
                    }
                }
                Rectangle {
                    width: forgeLabel.implicitWidth + 24
                    height: 30
                    radius: 6
                    color: win.frozen ? NovaTheme.surfaceAlt : NovaTheme.primary
                    border.width: 1
                    border.color: win.frozen ? NovaTheme.outline : NovaTheme.primary
                    Text {
                        id: forgeLabel
                        anchors.centerIn: parent
                        text: win.frozen ? "已签发证书" : "请求孵化"
                        color: win.frozen ? NovaTheme.textMuted : NovaTheme.textOnPrimary
                        font.pixelSize: NovaTheme.fontS
                    }
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: shell.requestFreeze()
                    }
                }
            }
        }

        // ── ⑥ 孵化摘要证书（Showcase 基准：圆点行卡）──────────
        // 布局事实：certificateSlot 在右侧校验栏底部（NovaFooter，宽 ~340 × 高 210，
        // 壳公开属性 certificateHeight 已由宿主调高）。壳在右上角有「方章折角 + 封蜡点」
        // 身份装饰（占 y 6~26），内容 topMargin 36 起步完全避开；行卡 22px × 5 行。
        certificateSlot: Item {
            anchors.fill: parent
            Column {
                id: certCol
                anchors { top: parent.top; topMargin: 36; left: parent.left; leftMargin: 12; right: parent.right; rightMargin: 12 }
                spacing: 5
                Row {
                    spacing: 8
                    Text {
                        text: "孵化证书 · 五件套"
                        color: NovaTheme.textMuted
                        font.pixelSize: NovaTheme.fontXS
                    }
                    Text {
                        text: win.frozen ? "已落盘" : "待落盘"
                        color: win.frozen ? NovaTheme.positive : NovaTheme.warning
                        font.pixelSize: NovaTheme.fontXS
                    }
                }
                Text {
                    width: certCol.width
                    text: (bridge.summary.appName || "—") + " · " + (bridge.summary.recipe || "—")
                          + " · 包 " + (bridge.summary.package || "—")
                    color: NovaTheme.primaryText
                    elide: Text.ElideRight
                    font.pixelSize: NovaTheme.fontXS
                }
                Repeater {
                    model: win.activeKind() ? win.activeKind().deliverables : []
                    Rectangle {
                        required property var modelData
                        width: certCol.width
                        height: 22
                        radius: 4
                        color: NovaTheme.surface
                        Row {
                            anchors { left: parent.left; leftMargin: 8; right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                            spacing: 8
                            Rectangle {
                                width: 5; height: 5; radius: 2.5
                                color: win.frozen ? NovaTheme.positive : NovaTheme.outline
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: modelData.k
                                color: NovaTheme.textColor
                                font.pixelSize: NovaTheme.fontXS
                            }
                            Text {
                                width: parent.width - 118
                                text: modelData.v
                                color: NovaTheme.textMuted
                                elide: Text.ElideRight
                                font.pixelSize: NovaTheme.fontXS
                            }
                        }
                    }
                }
            }
        }

        // ── ⑦ 人工确认闸门：唯一落盘触发点 ────────────────────
        overlaySlot: Item {
            anchors.fill: parent
            visible: win.gateOpen
            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(0, 0, 0, 0.45)
                MouseArea { anchors.fill: parent }
            }
            Rectangle {
                id: gateCard
                anchors.centerIn: parent
                width: Math.min(560, parent.width - 48)
                height: Math.min(470, parent.height - 48)
                radius: NovaTheme.radiusL
                color: NovaTheme.surface
                border.width: 1
                border.color: NovaTheme.outline

                // 摘要数据一律取自 bridge.summary（由生成的 pyproject.toml 解析），
                // 确认框不另立台账——所见即落盘内容。
                property var m: bridge.summary.meta || ({})
                property var keys: bridge.summary.keyFiles || []

                Flickable {
                    anchors {
                        left: parent.left; leftMargin: 22
                        right: parent.right; rightMargin: 22
                        top: parent.top; topMargin: 18
                        bottom: parent.bottom; bottomMargin: 16
                    }
                    clip: true
                    contentWidth: width
                    contentHeight: gateCol.implicitHeight
                    Column {
                        id: gateCol
                        width: parent.width
                        spacing: 10

                        Row {
                            width: parent.width
                            spacing: 10
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: "确认孵化？"
                                color: NovaTheme.textColor
                                font { pixelSize: NovaTheme.fontM; bold: true }
                            }
                            NovaChip {
                                anchors.verticalCenter: parent.verticalCenter
                                text: (bridge.summary.appName || "—")
                                outlined: true
                                dense: true
                            }
                        }
                        NovaSeparator { width: parent.width }

                        // 关键信息网格：版本 / 作者 / 包名 / 许可证（2×2）
                        Grid {
                            width: parent.width
                            columns: 2
                            rowSpacing: 7
                            columnSpacing: 16
                            property real cellW: (width - columnSpacing) / 2
                            Column {
                                width: parent.cellW
                                Text { text: "版本"; color: NovaTheme.textMuted; font.pixelSize: 9 }
                                Text {
                                    text: (gateCard.m.version || "—")
                                    color: NovaTheme.textColor; font { pixelSize: 11; bold: true }
                                }
                            }
                            Column {
                                width: parent.cellW
                                Text { text: "作者"; color: NovaTheme.textMuted; font.pixelSize: 9 }
                                Text {
                                    text: (gateCard.m.author || "—")
                                    color: NovaTheme.textColor; font { pixelSize: 11; bold: true }
                                }
                            }
                            Column {
                                width: parent.cellW
                                Text { text: "包名"; color: NovaTheme.textMuted; font.pixelSize: 9 }
                                Text {
                                    text: (gateCard.m.distName || bridge.summary.package || "—")
                                    color: NovaTheme.textColor; font { pixelSize: 11; bold: true }
                                }
                            }
                            Column {
                                width: parent.cellW
                                Text { text: "许可证"; color: NovaTheme.textMuted; font.pixelSize: 9 }
                                Text {
                                    text: (gateCard.m.license || "—")
                                    color: NovaTheme.textColor; font { pixelSize: 11; bold: true }
                                }
                            }
                        }
                        // 描述整行显示（Grid 是 2 列，整行元素放外面避免跨列溢出）
                        Column {
                            width: parent.width
                            Text { text: "描述"; color: NovaTheme.textMuted; font.pixelSize: 9 }
                            Text {
                                width: parent.width
                                text: (gateCard.m.description || bridge.summary.tagline || "—")
                                color: NovaTheme.textColor; font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }

                        NovaSeparator { width: parent.width }

                        // 用户最关心的主要文件：库组件 GroupBox（NovaField 的
                        // outlined + 顶边浮动标题）内嵌 NovaOptionGroup 原生
                        // checkbox 组（内部即 NovaCheckbox），零手搓控件。
                        // 5 项恒列、逐项可勾选，与左侧 17 项组选框账实同源。
                        NovaField {
                            id: keyFileGroupBox
                            objectName: "keyFileGroupBox"
                            width: parent.width
                            label: "将创建的主要文件 · " + gateCard.keys.length
                                + " 项（勾选决定实际创建）"
                            stackLabel: true
                            outlined: true
                            dense: true
                            customControlH: 152

                            NovaOptionGroup {
                                id: keyFileGroup
                                objectName: "keyFileGroup"
                                width: parent.width
                                height: implicitHeight + 10
                                type: "checkbox"
                                dense: true
                                options: win.keyFileOptions()
                                modelValue: win.keyFileValues()
                                onValueChanged: function(values) {
                                    win.syncKeyFiles(values)
                                }
                            }
                        }
                        Connections {
                            target: bridge
                            // 坑位 53 同源守卫：NovaOptionGroup._setArray 会命令式
                            // 赋值 modelValue 打破 QML 绑定，预览刷新时显式回灌。
                            function onPlanReady() {
                                keyFileGroup.modelValue = win.keyFileValues()
                            }
                        }

                        NovaSeparator { width: parent.width }

                        Text {
                            width: parent.width
                            text: "共 " + (bridge.summary.fileCount || 0) + " 个文件 · " + (bridge.summary.root || "—")
                            color: NovaTheme.textMuted
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            text: (bridge.dryRun ? "仅预览模式：不会写盘" : "确认后立即写盘")
                                + " · 三重校验 3/3 PASS"
                            color: bridge.dryRun ? NovaTheme.warningText : NovaTheme.positiveText
                            font { pixelSize: 9; bold: true }
                        }

                        // T18：CTA 已上移为 gateCard 的固定子项（右下角常驻），
                        // 这里只留与按钮等高的滚动留白，Flickable 滚到底时
                        // 最后一行文字不会被覆盖；内容区高度不变、不缩水。
                        // 高度 = CTA 约 32 + 12 间距 + 2 余量。
                        Item {
                            objectName: "gateActionSpacer"
                            width: parent.width
                            height: 46
                        }
                    }
                }

                // T18：两个 CTA 固定在卡片右下角（CSA 截图红框位），
                // 不随 Flickable 摘要内容滚动；顺序「取消 → 确认孵化」，主按钮最右。
                Row {
                    id: gateActions
                    objectName: "gateActions"
                    anchors {
                        right: parent.right; rightMargin: 22
                        bottom: parent.bottom; bottomMargin: 16
                    }
                    spacing: 10
                    NovaBtn {
                        objectName: "gateCancelBtn"
                        text: "取消"
                        size: "sm"
                        variant: "outlined"
                        onClicked: win.gateOpen = false
                    }
                    NovaBtn {
                        objectName: "gateConfirmBtn"
                        text: "🤝 确认孵化"
                        size: "sm"
                        variant: "filled"
                        disable: bridge.busy
                        loading: bridge.busy
                        onClicked: bridge.hatch(true)
                    }
                }
            }
        }
    }

    // ── 界面预览浮层：NovaCard 容器 + 九配方 chips 切换 + Loader 真实渲染 ──
    // 用户最急切的诉求「所选应用的界面长什么样」：这里渲染的就是将来落盘的
    // Stage.qml 全文（bridge.previewStage 写临时副本后由 Loader 加载），
    // 与孵化产物同源单字不变——所见即所得，非截图、非 mock、非示意图。
    Item {
        id: previewOverlay
        anchors.fill: parent
        visible: win.previewOpen
        z: 10000
        enabled: visible

        Keys.onEscapePressed: win.previewOpen = false

        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.55)
            MouseArea { anchors.fill: parent; onClicked: win.previewOpen = false }
        }

        Item {
            id: previewBox
            anchors.centerIn: parent
            width: Math.min(previewOverlay.width - 56, 1120)
            height: Math.min(previewOverlay.height - 56, 700)

            NovaCard { anchors.fill: previewBox; bordered: true }

            // 头部：标题 + 关闭
            Row {
                id: previewHeader
                anchors { top: previewBox.top; topMargin: 12; left: previewBox.left; leftMargin: 14; right: previewBox.right; rightMargin: 14 }
                spacing: 8
                NovaIcon {
                    // 预览标题图标随选定配方切换（单一事实源 catalog.Kind.icon，空选型不渲染）
                    icon: win.previewKindSpec() ? "img:" + win.previewKindSpec().icon : ""
                    size: 20
                    monochrome: false
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "界面预览 · " + win.previewKind + " · "
                          + (win.previewKindSpec() ? win.previewKindSpec().zh : "—")
                    color: NovaTheme.textColor
                    elide: Text.ElideRight
                    width: parent.width - 124
                    font { pixelSize: NovaTheme.fontM; bold: true }
                    anchors.verticalCenter: parent.verticalCenter
                }
                NovaBtn {
                    text: "✕ 关闭"
                    size: "sm"
                    variant: "flat"
                    onClicked: win.previewOpen = false
                }
            }

            // 九配方切换 chips：预览独立选型，不改动工作台配置态
            Row {
                id: previewChips
                anchors { top: previewHeader.bottom; topMargin: 8; left: previewBox.left; leftMargin: 14; right: previewBox.right; rightMargin: 14 }
                spacing: 6
                Repeater {
                    model: bridge.kinds
                    NovaChip {
                        required property var modelData
                        text: modelData.zh
                        dense: true
                        clickable: true
                        selected: win.previewKind === modelData.code
                        onClicked: {
                            win.previewKind = modelData.code
                            win.loadPreview()
                        }
                    }
                }
            }

            // 舞台视口：Loader 实装渲染 Stage.qml
            Rectangle {
                id: previewViewport
                anchors {
                    top: previewChips.bottom; topMargin: 8
                    left: previewBox.left; leftMargin: 14
                    right: previewBox.right; rightMargin: 14
                    bottom: previewCaption.top; bottomMargin: 6
                }
                color: NovaTheme.page
                border.width: 1
                border.color: NovaTheme.outline
                clip: true

                Loader {
                    id: previewLoader
                    anchors.fill: parent
                    anchors.margins: 1
                    onStatusChanged: {
                        if (status === Loader.Error) {
                            previewHint.visible = false
                            previewError.visible = true
                        } else if (status === Loader.Ready) {
                            previewHint.visible = false
                        }
                    }
                }
                Text {
                    id: previewHint
                    anchors.centerIn: parent
                    text: "正在渲染 …"
                    color: NovaTheme.textMuted
                    font.pixelSize: NovaTheme.fontS
                }
                Text {
                    id: previewError
                    anchors { centerIn: parent; margins: 24 }
                    width: Math.min(560, parent.width - 48)
                    visible: false
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    text: "Stage.qml 实装渲染失败\n（未知配方或 QML 加载异常，详见控制台告警）"
                    color: NovaTheme.negative
                    font.pixelSize: NovaTheme.fontS
                }
            }

            // 底注：所见即所得口径
            Text {
                id: previewCaption
                anchors { bottom: previewBox.bottom; bottomMargin: 10; left: previewBox.left; leftMargin: 14; right: previewBox.right; rightMargin: 14 }
                text: "真 QML 实装渲染 · Stage.qml 与落盘产物同源单字不变 · 非截图、非 mock"
                      + (win.previewKindSpec() ? " · 壳 " + win.previewKindSpec().shell : "")
                color: NovaTheme.textMuted
                elide: Text.ElideRight
                font.pixelSize: NovaTheme.fontXS
            }
        }
    }

    // ── 桥接信号 → Nova 服务（全库 dogfooding）────────────────
    Connections {
        target: bridge

        function onGateOpened() {
            win.gateOpen = true
        }

        // fileChoices / summary 是属性绑定，planReady 时 QML 自动重算，无需手动搬数。

        function onToast(kind, message) {
            win.showToast(kind, message)
        }

        function onBusyChanged() {
            // 忙碌态由宿主 busyBar 扫掠条 + NovaLoading 遮罩服务呈现；
            // 不调用 NovaLoadingBar（基础组件 qrc 缺陷，见文件头触发点记录）。
            if (bridge.busy)
                NovaLoading.show({ group: "prescript", message: "正在孵化应用…" })
        }

        function onHatchFinished(ok, message) {
            NovaLoading.hide("prescript")
            win.gateOpen = false
            if (ok) {
                win.stageIndex = 4
            } else {
                NovaDialog.show({
                    title: "孵化未完成",
                    message: message,
                    ok: "知道了",
                    cancel: "关闭"
                })
            }
        }
    }
}
