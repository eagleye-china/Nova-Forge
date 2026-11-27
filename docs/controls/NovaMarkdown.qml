// src/pyside_nova/qml/Nova/Controls/NovaMarkdown.qml
// NovaMarkdown Markdown 文档渲染器（对标 Quasar QMarkdown · 原生渲染精简版）
// v0.17.0 优化：
//   1. GFM 表格自研 Grid 渲染（Qt Text.MarkdownText 对表格支持不稳定）
//   2. TOC 侧栏可滚动（原版超过约 15 条溢出）
//   3. _slug 用计数器去重，锚点不随前文内容漂移
//   4. _lineKind 严格化：table 首尾须有 |；独立判定 hr / tasklist
//   5. 独占一行的图片块独立渲染，宽度自适应约束
//   6. scrollToAnchor 用 anchorIndex O(1) 查找
// 设计原则：零外部依赖 · Qt 原生 Text.MarkdownText · 分块渲染 · NovaTheme 令牌
// a11y: 只读文档内容，可读名由 a11yLabel 覆盖，默认「Markdown 文档」
pragma ComponentBehavior: Bound
import QtQuick
import Nova.Services

Item {
    id: root

    // ── 可访问性（WCAG 2.1 AA）────────────────────────────
    property string a11yLabel: ""
    Accessible.role: Accessible.StaticText
    Accessible.name: root.a11yLabel !== "" ? root.a11yLabel : "Markdown 文档"

    // ── 输入 API ─────────────────────────────────────────
    property string markdown: ""             // Markdown 源文本（唯一输入）
    property bool showToc: false             // 是否显示内置大纲侧栏
    property int tocStart: 1                 // 大纲起始标题层级（1~6）
    property int tocEnd: 3                   // 大纲结束标题层级（1~6）
    property bool openLinksExternally: true  // 安全链接是否自动交给系统打开
    property bool outlined: true             // 卡片边框与圆角
    // 字号：默认跟随主题；宿主显式赋值后「接管」，主题切换不再覆盖（标准 QML 语义）
    property int baseFontSize: NovaTheme.bodyFontSize

    // ── 只读输出 ─────────────────────────────────────────
    readonly property var toc: root._toc
    readonly property bool empty: root._blocks.length === 0

    // ── 信号 ─────────────────────────────────────────────
    signal linkClicked(string url)

    signal linkBlocked(string url)

    signal tocReady(var items)

    // ── 私有状态（_ 前缀不进冻结面）─────────────────────
    property var _blocks: []                 // 解析后的块列表
    property var _toc: []                    // 大纲条目
    property var _anchorIndex: ({})          // anchor → blockIndex（O(1) 跳转）
    property var _slugCounter: ({})          // 标题 slug 去重计数器

    implicitWidth: 480
    implicitHeight: 360

    onMarkdownChanged: root._rebuild()
    onTocStartChanged: root._rebuild()
    onTocEndChanged: root._rebuild()
    Component.onCompleted: root._rebuild()

    // ══════════════════════════════════════════════════════
    // 解析工具
    // ══════════════════════════════════════════════════════
    function _isHr(line) {
        // --- / *** / ___ ，至少 3 个字符（允许中间空格）
        return /^\s*([-*_])\s*\1\s*\1[\s\1]*$/.test(line)
    }

    function _isSeparatorLine(line) {
        // GFM 表格分隔行 |---|---| / |:--|--:|:--:|
        return /^\s*\|?(\s*:?-+:?\s*\|)+(\s*:?-+:?\s*)?\|?\s*$/.test(line)
    }

    function _lineKind(line) {
        if (/^\s*\|.*\|\s*$/.test(line)) return "table"          // 首尾必须有 |
        if (/^\s*>/.test(line)) return "quote"
        if (root._isHr(line)) return "hr"
        if (/^\s*([-+*]|\d+\.)\s+\[[ xX]\]\s+/.test(line)) return "tasklist"
        if (/^\s*([-+*]|\d+\.)\s+/.test(line)) return "list"
        return "paragraph"
    }

    function _isImageOnly(line) {
        return /^\s*!\[[^\]]*\]\([^)]+\)\s*$/.test(line)
    }

    function _extractImage(line) {
        var m = String(line).match(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/)
        if (!m) return null
        return {alt: m[1] || "", src: m[2] || "", title: m[3] || ""}
    }

    function _splitRow(line) {
        var s = String(line).trim()
        if (s.charAt(0) === "|") s = s.substring(1)
        if (s.charAt(s.length - 1) === "|") s = s.substring(0, s.length - 1)
        return s.split("|").map(function (c) {
            return c.trim()
        })
    }

    function _extractTable(headerLine, sepLine, dataLines) {
        var header = root._splitRow(headerLine)
        var aligns = root._splitRow(sepLine).map(function (c) {
            var l = c.charAt(0) === ":"
            var r = c.charAt(c.length - 1) === ":"
            return l && r ? "center" : r ? "right" : l ? "left" : "left"
        })
        var rows = []
        for (var k = 0; k < dataLines.length; k++)
            rows.push(root._splitRow(dataLines[k]))
        return {header: header, aligns: aligns, rows: rows}
    }

    function _slug(title) {
        // 按标题文本 + 去重计数生成锚点，不依赖 blocks.length（避免锚点漂移）
        var s = String(title).toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9\u4e00-\u9fa5_-]/g, "")
        var base = s !== "" ? s : "section"
        var n = root._slugCounter[base] || 0
        root._slugCounter[base] = n + 1
        return n === 0 ? base : base + "-" + n
    }

    // ══════════════════════════════════════════════════════
    // 解析主体：逐行扫描，按 kind 分组为「块」
    // ══════════════════════════════════════════════════════
    function _parse(src) {
        var lines = String(src || "").replace(/\r\n/g, "\n").split("\n")
        var blocks = []
        var tocList = []
        var anchorMap = {}
        var i = 0

        while (i < lines.length) {
            var line = lines[i]

            // ── 围栏代码块 ─────────────────────────────
            var fence = line.match(/^\s*(`{3,}|~{3,})/)
            if (fence) {
                var mark = fence[1].charAt(0)
                var width = fence[1].length
                var buf = [line]
                i++
                var closeRe = new RegExp("^\\s*" + mark + "{" + width + ",}\\s*$")
                while (i < lines.length) {
                    var fl = lines[i]
                    buf.push(fl)
                    i++
                    if (closeRe.test(fl)) break
                }
                blocks.push({
                    kind: "fence", text: buf.join("\n"),
                    level: 0, anchor: ""
                })
                continue
            }

            // ── 空行 ───────────────────────────────────
            if (/^\s*$/.test(line)) {
                i++;
                continue
            }

            // ── 标题 ───────────────────────────────────
            var head = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/)
            if (head) {
                var level = head[1].length
                var title = head[2].replace(/[*_`~]/g, "").trim()
                var anchor = root._slug(title)
                blocks.push({
                    kind: "heading", text: line,
                    level: level, anchor: anchor
                })
                if (level >= root.tocStart && level <= root.tocEnd)
                    tocList.push({
                        level: level, title: title,
                        anchor: anchor, index: blocks.length - 1
                    })
                anchorMap[anchor] = blocks.length - 1
                i++
                continue
            }

            // ── 分隔线 ─────────────────────────────────
            if (root._isHr(line)) {
                blocks.push({kind: "hr", text: line, level: 0, anchor: ""})
                i++
                continue
            }

            // ── GFM 表格（header + 分隔行 + 数据行）────
            if (root._lineKind(line) === "table"
                && i + 1 < lines.length
                && root._isSeparatorLine(lines[i + 1])) {
                var headerLine = line
                var sepLine = lines[i + 1]
                var dataLines = []
                var j = i + 2
                while (j < lines.length && /^\s*\|.*\|\s*$/.test(lines[j])) {
                    dataLines.push(lines[j])
                    j++
                }
                var table = root._extractTable(headerLine, sepLine, dataLines)
                blocks.push({
                    kind: "table", text: "", level: 0,
                    anchor: "", table: table
                })
                i = j
                continue
            }

            // ── 独占一行的图片 ─────────────────────────
            if (root._isImageOnly(line)) {
                var img = root._extractImage(line)
                if (img) {
                    blocks.push({
                        kind: "image", text: line, level: 0,
                        anchor: "", image: img
                    })
                    i++
                    continue
                }
            }

            // ── 普通块（按 kind 分组） ─────────────────
            var hint = root._lineKind(line)
            var group = [line]
            i++
            while (i < lines.length) {
                var nx = lines[i]
                if (/^\s*$/.test(nx)) break
                if (/^\s*(`{3,}|~{3,})/.test(nx)) break
                if (/^(#{1,6})\s+/.test(nx)) break
                if (root._isHr(nx)) break
                // 段落里遇到「表格起点」也中断
                if (root._lineKind(nx) === "table"
                    && i + 1 < lines.length
                    && root._isSeparatorLine(lines[i + 1])) break
                if (root._lineKind(nx) !== hint) break
                group.push(nx)
                i++
            }
            blocks.push({
                kind: hint, text: group.join("\n"),
                level: 0, anchor: ""
            })
        }

        return {blocks: blocks, toc: tocList, anchorMap: anchorMap}
    }

    function _rebuild() {
        root._slugCounter = {}
        var r = root._parse(root.markdown)
        root._blocks = r.blocks
        root._toc = r.toc
        root._anchorIndex = r.anchorMap
        root.tocReady(r.toc)
    }

    // ══════════════════════════════════════════════════════
    // 安全 & 导航
    // ══════════════════════════════════════════════════════
    function _safeUrl(url) {
        var u = String(url || "").trim().toLowerCase()
        return !(u.indexOf("javascript:") === 0
            || u.indexOf("vbscript:") === 0
            || u.indexOf("data:") === 0
            || u.indexOf("file:") === 0)
    }

    function _onLink(url) {
        if (!root._safeUrl(url)) {
            root.linkBlocked(url);
            return
        }
        if (url.length > 0 && url.charAt(0) === "#") {
            root.scrollToAnchor(url.substring(1))
            return
        }
        root.linkClicked(url)
        if (root.openLinksExternally) Qt.openUrlExternally(url)
    }

    function scrollToTop() {
        if (scroller._flick) scroller._flick.contentY = 0
    }

    function scrollToAnchor(anchor) {
        if (!anchor || !scroller._flick) return
        var idx = root._anchorIndex[anchor]
        if (idx === undefined || idx < 0) return
        var it = blockRepeater.itemAt(idx)
        if (!it) return
        var maxY = Math.max(0, scroller._flick.contentHeight - scroller._flick.height)
        scroller._flick.contentY = Math.max(0, Math.min(it.y, maxY))
    }

    function reload() {
        root._rebuild()
    }

    // ══════════════════════════════════════════════════════
    // 视觉
    // ══════════════════════════════════════════════════════
    Rectangle {
        anchors.fill: parent
        radius: NovaTheme.radiusM
        color: NovaTheme.surface
        border.width: root.outlined ? 1 : 0
        border.color: NovaTheme.outline
    }

    Item {
        id: stage
        anchors.fill: parent
        anchors.margins: root.outlined ? 1 : 0

        // ─────────────── TOC 侧栏（可滚动） ────────────────
        Rectangle {
            id: tocPane
            anchors {
                left: parent.left; top: parent.top; bottom: parent.bottom
            }
            width: root.showToc ? 190 : 0
            visible: root.showToc
            color: NovaTheme.surfaceAlt
            clip: true

            Rectangle {
                anchors {
                    right: parent.right; top: parent.top; bottom: parent.bottom
                }
                width: 1
                color: NovaTheme.outline
            }

            Text {
                id: tocTitle
                anchors {
                    left: parent.left; top: parent.top
                    leftMargin: 12; topMargin: 10
                }
                text: "大纲 · " + root._toc.length
                color: NovaTheme.textMuted
                font {
                    family: NovaTheme.fontFamily; pixelSize: NovaTheme.fontXS
                }
            }

            NovaScrollArea {
                anchors {
                    left: parent.left; right: parent.right
                    top: tocTitle.bottom; bottom: parent.bottom
                }

                Column {
                    id: tocColContent      // ← 新增 id
                    width: parent.width
                    spacing: 2
                    Item {
                        width: 1; height: 8
                    }

                    Repeater {
                        model: root._toc
                        delegate: Item {
                            id: tocRow
                            required property int index
                            required property var modelData
                            width: parent.width - 12
                            height: 26
                            x: 6 + Math.max(0, tocRow.modelData.level - root.tocStart) * 10

                            // hover 背景（separate opacity，避免 Qt.rgba 拿不到颜色分量）
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 1
                                radius: NovaTheme.radiusS
                                color: NovaTheme.primary
                                opacity: tocHover.containsMouse ? 0.10 : 0
                                Behavior on opacity {
                                    NumberAnimation {
                                        duration: 120
                                    }
                                }
                            }

                            Text {
                                anchors {
                                    fill: parent
                                    leftMargin: 8; rightMargin: 8
                                }
                                text: tocRow.modelData.title
                                color: tocHover.containsMouse
                                    ? NovaTheme.primary : NovaTheme.textColor
                                font {
                                    family: NovaTheme.fontFamily
                                    pixelSize: NovaTheme.fontXS
                                }
                                elide: Text.ElideRight
                                verticalAlignment: Text.AlignVCenter
                            }

                            MouseArea {
                                id: tocHover
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.scrollToAnchor(tocRow.modelData.anchor)
                            }
                        }
                    }

                    Item {
                        width: 1; height: 8
                    }
                }
            }

        }

        // ─────────────── 文档滚动区 ──────────────────────
        NovaScrollArea {
            id: scroller
            anchors {
                left: tocPane.right; right: parent.right
                top: parent.top; bottom: parent.bottom
            }

            Column {
                id: docColumn
                width: scroller.width
                Item {
                    width: 1; height: 12
                }

                Repeater {
                    id: blockRepeater
                    model: root._blocks

                    delegate: Item {
                        id: blockItem
                        required property int index
                        required property var modelData

                        readonly property bool isFence: modelData.kind === "fence"
                        readonly property bool isTable: modelData.kind === "table"
                        readonly property bool isHr: modelData.kind === "hr"
                        readonly property bool isImage: modelData.kind === "image"
                        readonly property bool isBody: !isFence && !isTable
                            && !isHr && !isImage

                        objectName: blockItem.modelData.anchor || ""
                        width: docColumn.width

                        height: {
                            if (blockItem.isHr) return 20
                            if (blockItem.isTable) return tableGrid.height + 6
                            if (blockItem.isImage) return Math.max(0, imageBody.height + 6)
                            return bodyText.implicitHeight + (blockItem.isFence ? 20 : 6)
                        }

                        // 围栏代码底
                        Rectangle {
                            anchors.fill: parent
                            visible: blockItem.isFence
                            radius: NovaTheme.radiusS
                            color: NovaTheme.surfaceAlt
                            border.width: 1
                            border.color: NovaTheme.outline
                        }

                        // 分隔线
                        Rectangle {
                            visible: blockItem.isHr
                            anchors.verticalCenter: parent.verticalCenter
                            x: 14
                            width: Math.max(0, parent.width - 28)
                            height: 1
                            color: NovaTheme.outline
                        }

                        // ── GFM 表格（自研 Grid） ────────────
                        Grid {
                            id: tableGrid
                            visible: blockItem.isTable
                            x: 14
                            y: 3
                            width: Math.max(0, parent.width - 28)
                            columns: blockItem.isTable
                                ? blockItem.modelData.table.header.length
                                : 1
                            spacing: 0

                            Repeater {
                                model: blockItem.isTable
                                    ? [blockItem.modelData.table.header]
                                        .concat(blockItem.modelData.table.rows)
                                    : []

                                delegate: Rectangle {
                                    id: cellRect
                                    required property int index
                                    required property var modelData

                                    readonly property var table:
                                        blockItem.isTable ? blockItem.modelData.table : null
                                    readonly property int colCount:
                                        table ? table.header.length : 1
                                    readonly property int colIdx: index % colCount
                                    readonly property int rowIdx:
                                        Math.floor(index / colCount)
                                    readonly property bool isHeader: rowIdx === 0
                                    readonly property string cellText:
                                        (modelData && modelData[colIdx] !== undefined)
                                            ? String(modelData[colIdx]) : ""
                                    readonly property string align:
                                        (table && table.aligns[colIdx]) || "left"

                                    width: colCount > 0 ? tableGrid.width / colCount : 0
                                    height: cellBody.implicitHeight + 12
                                    color: isHeader
                                        ? NovaTheme.surfaceAlt : NovaTheme.surface
                                    border.width: 1
                                    border.color: NovaTheme.outline

                                    Text {
                                        id: cellBody
                                        anchors {
                                            left: parent.left; right: parent.right
                                            top: parent.top
                                            leftMargin: 8; rightMargin: 8; topMargin: 6
                                        }
                                        text: cellRect.cellText
                                        textFormat: Text.MarkdownText
                                        wrapMode: Text.WordWrap
                                        color: NovaTheme.textColor
                                        font {
                                            family: NovaTheme.fontFamily
                                            pixelSize: root.baseFontSize
                                            bold: cellRect.isHeader
                                        }
                                        horizontalAlignment:
                                                cellRect.align === "center" ? Text.AlignHCenter
                                            : cellRect.align === "right" ? Text.AlignRight
                                                : Text.AlignLeft
                                        onLinkActivated: function (url) {
                                            root._onLink(url)
                                        }
                                    }
                                }
                            }
                        }

                        // ── 独占一行的图片 ────────────────
                        Image {
                            id: imageBody
                            visible: blockItem.isImage
                            x: 14
                            y: 3
                            width: Math.max(1, parent.width - 28)
                            source: blockItem.isImage && blockItem.modelData.image
                                ? blockItem.modelData.image.src : ""
                            sourceSize.width: Math.max(1, Math.floor(width))
                            fillMode: Image.PreserveAspectFit
                            asynchronous: true
                            smooth: true
                            // 高度随宽度自适应；加载失败或未就绪时为 0
                            height: status === Image.Ready && sourceSize.width > 0
                                ? Math.min(
                                    sourceSize.height * (width / sourceSize.width),
                                    1200)
                                : 0
                        }

                        // ── 正文（heading / paragraph / list /
                        //            tasklist / quote / fence） ─
                        Text {
                            id: bodyText
                            visible: blockItem.isBody || blockItem.isFence
                            anchors {
                                left: parent.left; right: parent.right; top: parent.top
                                leftMargin: blockItem.isFence ? 10 : 14
                                rightMargin: blockItem.isFence ? 10 : 14
                                topMargin: blockItem.isFence ? 8 : 2
                            }
                            text: blockItem.modelData.text
                            textFormat: Text.MarkdownText
                            wrapMode: Text.WordWrap
                            color: NovaTheme.textColor
                            linkColor: NovaTheme.primaryText
                            font {
                                family: NovaTheme.fontFamily
                                pixelSize: root.baseFontSize
                            }
                            lineHeight: NovaTheme.bodyLineHeight
                            onLinkActivated: function (url) {
                                root._onLink(url)
                            }
                        }
                    }
                }

                Item {
                    width: 1; height: 12
                }
            }
        }

        // 空态：绝不白屏
        Text {
            anchors.centerIn: parent
            visible: root.empty
            text: "暂无内容"
            color: NovaTheme.textMuted
            font {
                family: NovaTheme.fontFamily; pixelSize: NovaTheme.fontM
            }
        }
    }
}