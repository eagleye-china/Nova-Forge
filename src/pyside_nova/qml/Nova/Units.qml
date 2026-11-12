pragma Singleton
import QtQuick

// 尺寸单位统一入口。
// 规则：所有间距 / 圆角 / 线宽 / 图标尺寸都必须经过 Units.px()，禁止裸写像素魔法数字。
// Qt6 已自动处理 devicePixelRatio，因此 dp 基准为 1.0；
// 未来如需做「密度桶」（紧凑/舒适/手套触控），只在这里改，全库自动生效。
QtObject {
    readonly property real dp: 1.0

    function px(value) {
        return value * dp
    }
}
