pragma Singleton
import QtQuick

QtObject {
    readonly property var _known: [
        "bg-primary", "bg-secondary", "bg-positive", "bg-negative", "bg-warning",
        "bg-info", "bg-dark", "bg-white", "bg-background", "bg-surface",
        "text-white", "text-primary", "text-secondary", "text-positive",
        "text-negative", "text-warning", "text-dark", "text-muted", "text-disabled",
        "elevation-1", "elevation-2", "elevation-3", "elevation-4", "elevation-5",
        "rounded-none", "rounded-sm", "rounded-md", "rounded-lg", "rounded-pill"
    ]

    function parse(classes) {
        if (!classes) return []
        return classes.split(/\s+/).filter(function(c) { return c !== "" })
    }

    function validate(classes) {
        var list = parse(classes)
        for (var i = 0; i < list.length; i++) {
            if (_known.indexOf(list[i]) === -1) {
                console.warn("[Nova] unknown utility class: " + list[i])
            }
        }
    }

    function bgColorOf(classes) {
        var list = parse(classes)
        for (var i = list.length - 1; i >= 0; i--) {
            var c = list[i]
            if (c === "bg-primary") return Theme.primary
            if (c === "bg-secondary") return Theme.secondary
            if (c === "bg-positive") return Theme.positive
            if (c === "bg-negative") return Theme.negative
            if (c === "bg-warning") return Theme.warning
            if (c === "bg-info") return Theme.info
            if (c === "bg-dark") return Theme.dark
            if (c === "bg-white") return Theme.white
            if (c === "bg-background") return Theme.background
            if (c === "bg-surface") return Theme.surface
        }
        return "transparent"
    }

    function textColorOf(classes) {
        var list = parse(classes)
        for (var i = list.length - 1; i >= 0; i--) {
            var c = list[i]
            if (c === "text-white") return Theme.white
            if (c === "text-primary") return Theme.primary
            if (c === "text-secondary") return Theme.secondary
            if (c === "text-positive") return Theme.positive
            if (c === "text-negative") return Theme.negative
            if (c === "text-warning") return Theme.warning
            if (c === "text-dark") return Theme.text_primary
            if (c === "text-muted") return Theme.text_secondary
            if (c === "text-disabled") return Theme.disabled
        }
        return "transparent"
    }

    function elevationOf(classes) {
        var list = parse(classes)
        for (var i = list.length - 1; i >= 0; i--) {
            var c = list[i]
            if (c.startsWith("elevation-")) {
                var lv = parseInt(c.replace("elevation-", ""))
                if (lv >= 1 && lv <= 5) return lv
            }
        }
        return 0
    }

    function radiusTokenOf(classes) {
        var list = parse(classes)
        for (var i = list.length - 1; i >= 0; i--) {
            var c = list[i]
            if (c === "rounded-pill") return "pill"
            if (c === "rounded-lg") return "lg"
            if (c === "rounded-md") return "md"
            if (c === "rounded-sm") return "sm"
            if (c === "rounded-none") return "none"
        }
        return ""
    }

    function radiusPxOf(classes) {
        var token = radiusTokenOf(classes)
        if (token === "pill") return Units.px(Theme.radiusPill)
        if (token === "lg") return Units.px(Theme.radiusLg)
        if (token === "md") return Units.px(Theme.radiusMd)
        if (token === "sm") return Units.px(Theme.radiusSm)
        if (token === "none") return Units.px(Theme.radiusNone)
        return 0
    }

    // 核心机制:深色背景自动对比度判定
    function isDarkBackground(classes) {
        var bg = bgColorOf(classes)
        if (bg === "transparent") return false
        // QML 颜色 r/g/b 返回 0-1 浮点数
        return (bg.r * 0.299 + bg.g * 0.587 + bg.b * 0.114) < 0.5
    }
}
