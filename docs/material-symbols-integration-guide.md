# Material Symbols 图标提取与集成指南（pyside-nova / NovaIcon）

> 文档定位：Google **Material Symbols（M3 新版符号）** 官方 SVG 的批量提取、清洗、资源化、组件接入与预览画廊完整落地流程。
> 适用工程：`pyside-nova`（QML 模块 `import Nova 1.0`，组件前缀 `Nova*`）
> 图标协议：**Apache 2.0**，可商用，无需署名。
> 相关文档：[`pyside6-android-deploy-guide.md`](./pyside6-android-deploy-guide.md)、[`pyside6-android-wsl-build.md`](./pyside6-android-wsl-build.md)

---

## 一、结论与前置认知（先定死，避免反复踩坑）

### 1.1 Material Icons 与 Material Symbols 不是一套东西

| 名称 | 形态 | 包名 | 变体维度 | 适用 |
|---|---|---|---|---|
| Material Icons（经典 / 旧版） | 固定 24×24 独立 SVG | `@material-design-icons/svg` | `filled / outlined / rounded / sharp / twotone` | 传统 5 风格，组件库常规使用 |
| **Material Symbols（M3 新版）** | 独立 SVG（离散版本） | `@material-symbols/svg-{字重}` | `outlined / rounded / sharp` × 字重 100~700 × fill 0/1 | M3 设计语言，本指南主线 |

> ⚠️ 两套可**共存**，目录分开即可：`assets/icons/material/` 与 `assets/symbols/`。
> ⚠️ Material Symbols 另有一套可变字体 `.ttf`，本指南走的是**独立 SVG 离散版本**，更适合 PySide6 QML 直接加载渲染。

### 1.2 官方 npm 包的真实目录结构（最容易踩的坑）

```
node_modules/@material-symbols/svg-400/
├─ outlined/
│  ├─ home.svg          # fill=0，线框
│  └─ home-fill.svg     # fill=1，填充
├─ rounded/
└─ sharp/
```

**没有 `0/` 和 `1/` 子文件夹！** 填充与否靠文件名后缀 `-fill` 区分。
早期网上流传的 `rounded/0/`、`rounded/1/` 结构是错的，按那个写脚本只会生成空目录。

### 1.3 为什么必须清洗 SVG（核心动机）

原始 SVG 内容近似如下：

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="#000000">
  <path d="M..."/>
</svg>
```

两个致命问题：

| 属性 | 问题 | 后果 |
|---|---|---|
| `fill="#000000"` | 颜色硬编码 | QML `Image.color` **完全失效**，图标无法随主题变色 |
| `width="24" height="24"` | 尺寸硬编码 | 高 DPI、缩放、安卓端渲染易裁切或模糊 |

清洗 = 删除 `width` / `height` / `fill` 三个属性，把颜色与尺寸的控制权交还给 QML 组件。

---

## 二、步骤 1：npm 拉取全部官方 SVG 包

在 `Nova-Forge` 项目根目录执行：

```powershell
npm install @material-symbols/svg-100 @material-symbols/svg-200 @material-symbols/svg-300 @material-symbols/svg-400 @material-symbols/svg-500 @material-symbols/svg-600 @material-symbols/svg-700
```

说明：

- 官方按**字重**拆分 7 个独立包，没有"一次性全量包"。
- 每包含 `outlined / rounded / sharp` 三套外形。
- 图标基数约 3800+ 个，全部变体合计 15000+ 个 SVG，磁盘占用约 300MB。
- 安装完成后的验证命令：

```powershell
Get-ChildItem "D:\MyProjects\PyCharm\Project_Nova\Nova-Forge\node_modules\@material-symbols\svg-400\rounded\*.svg" | Select-Object -First 5
```

正常应输出类似 `10k-fill.svg`、`10k.svg`、`10mp-fill.svg`…… 说明结构确认无误。

> 💡 开发阶段可只装 `svg-400` 提速，正式发布前再补齐全部字重。

---

## 三、步骤 2：清洗导出脚本

**文件路径**：`src/dev_toolbox_pro/tools/clean_material_symbols.py`

```python
# src/dev_toolbox_pro/tools/clean_material_symbols.py
"""
Material Symbols 官方 SVG 批量清洗导出工具

能力：
  1. 遍历 @material-symbols/svg-{100..700} 全部字重
  2. 覆盖 outlined / rounded / sharp 三种外形
  3. 按文件名 -fill 后缀区分 fill=0 / fill=1，分别归一化到 0/ 与 1/ 目录
  4. 清洗 SVG：删除 width / height / fill 硬编码，交由 QML 控制
  5. 生成 symbol_index.json 图标索引，供预览画廊使用
"""
from pathlib import Path
import re
import json

# ========== 工程路径配置（按实际项目调整） ==========
ROOT = Path(r"D:\MyProjects\PyCharm\Project_Nova\Nova-Forge")
SRC_BASE = ROOT / "node_modules" / "@material-symbols"
DST = ROOT / "pyside-nova" / "src" / "pyside_nova" / "qml" / "Nova" / "assets" / "symbols"

WEIGHTS = [100, 200, 300, 400, 500, 600, 700]
STYLES = ["outlined", "rounded", "sharp"]

# 清洗规则：删除写死的 width / height / fill 属性
CLEAN_ATTR = re.compile(r'\s*(width|height|fill)="[^"]*"')

index = {}

for w in WEIGHTS:
    pkg_dir = SRC_BASE / f"svg-{w}"
    print(f"\n[INFO] 正在处理 weight={w} | 源目录：{pkg_dir}")
    if not pkg_dir.exists():
        print(f"[WARN] 跳过：{pkg_dir} 不存在")
        continue

    index[w] = {}
    for style in STYLES:
        src_dir = pkg_dir / style
        index[w][style] = {"0": [], "1": []}

        dst0 = DST / str(w) / style / "0"
        dst1 = DST / str(w) / style / "1"
        dst0.mkdir(parents=True, exist_ok=True)
        dst1.mkdir(parents=True, exist_ok=True)

        svg_list = list(src_dir.glob("*.svg"))
        print(f"  -- {style} 共找到 {len(svg_list)} 个 SVG")

        for svg in svg_list:
            raw = svg.read_text(encoding="utf-8")
            clean_svg = CLEAN_ATTR.sub("", raw)
            stem = svg.stem

            if stem.endswith("-fill"):
                # fill=1 填充图标
                icon_name = stem.removesuffix("-fill")
                out = dst1 / f"{icon_name}.svg"
                index[w][style]["1"].append(icon_name)
            else:
                # fill=0 线框图标
                icon_name = stem
                out = dst0 / f"{icon_name}.svg"
                index[w][style]["0"].append(icon_name)

            out.write_text(clean_svg, encoding="utf-8")

# 输出索引文件，供图标预览画廊读取
index_file = DST / "symbol_index.json"
index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n[OK] 全部处理完毕！索引文件：{index_file}")
print(f"[OK] 资源输出目录：{DST}")
```

### 3.1 运行

```powershell
# 建议先删除旧的 symbols 目录，避免空文件夹残留
Remove-Item -Recurse -Force "D:\MyProjects\PyCharm\Project_Nova\Nova-Forge\pyside-nova\src\pyside_nova\qml\Nova\assets\symbols" -ErrorAction SilentlyContinue

python src/dev_toolbox_pro/tools/clean_material_symbols.py
```

### 3.2 输出目录结构（统一标准）

```
assets/symbols/
├─ 100/
│  ├─ outlined/
│  │  ├─ 0/          # fill=0 线框版
│  │  └─ 1/          # fill=1 填充版
│  ├─ rounded/
│  └─ sharp/
├─ 200/
├─ 300/
├─ 400/
├─ 500/
├─ 600/
├─ 700/
└─ symbol_index.json
```

### 3.3 验证

```powershell
Get-ChildItem "D:\MyProjects\PyCharm\Project_Nova\Nova-Forge\pyside-nova\src\pyside_nova\qml\Nova\assets\symbols\400\rounded\0\*.svg" | Select-Object -First 5
```

应能列出 `10k.svg`、`10mp.svg`、`11mp.svg`、`123.svg`、`12mp.svg` 等文件。

---

## 四、步骤 3：资源打包（qrc）

将 `symbols` 目录纳入 Qt 资源系统，桌面端与 Android 打包统一走 `qrc:/` 访问。

```xml
<RCC>
    <qresource prefix="/pyside_nova">
        <file>Nova/assets/symbols</file>
        <file>Nova/assets/icons/material</file>
    </qresource>
</RCC>
```

> ⚠️ 全量 15000+ SVG 会让 qrc 编译明显变慢。开发阶段可只保留 400 字重，或按需注释部分目录；正式发布再全量打包。

---

## 五、步骤 4：NovaIcon 组件（封板版）

**文件路径**：`src/pyside_nova/qml/Nova/NovaIcon.qml`

```qml
// src/pyside_nova/qml/Nova/NovaIcon.qml
import QtQuick

/**
 * NovaIcon 旗舰版
 * 同时支持：经典 Material Icons / 新版 Material Symbols(M3)
 *
 * 使用示例：
 *   NovaIcon {
 *       icon: "home"
 *       type: "symbols"
 *       weight: 400
 *       style: "rounded"
 *       filled: false
 *       color: Theme.textPrimary
 *       pixelSize: 24
 *   }
 */
Item {
    id: root

    // 图标名称（Material Symbols 官网图标名）
    property string icon: "home"

    // 图标体系：symbols(新版M3) / icons(经典Material Icons)
    property string type: "symbols"

    // —— symbols 专属参数 ——
    property int weight: 400            // 100 / 200 / 300 / 400 / 500 / 600 / 700
    property string style: "rounded"    // outlined / rounded / sharp
    property bool filled: false         // false=线框(fill0) / true=填充(fill1)

    // —— 通用参数 ——
    property color color: Theme.textPrimary
    property int pixelSize: 24

    readonly property string _fillStr: filled ? "1" : "0"

    readonly property string _srcPath: {
        if (type === "symbols") {
            return "qrc:/pyside_nova/Nova/assets/symbols/"
                 + weight + "/" + style + "/" + _fillStr + "/" + icon + ".svg"
        }
        // 经典 Material Icons（需先按 5 风格目录整理）
        return "qrc:/pyside_nova/Nova/assets/icons/material/"
             + style + "/" + icon + ".svg"
    }

    implicitWidth: pixelSize
    implicitHeight: pixelSize

    Image {
        anchors.fill: parent
        source: root._srcPath
        sourceSize.width: root.pixelSize
        sourceSize.height: root.pixelSize
        fillMode: Image.PreserveAspectFit
        smooth: true
        // 因 SVG 已清除 fill 硬编码，此处 color 可正常着色
        color: root.color
    }
}
```

### 5.1 调用示例

```qml
// M3 新版 Symbols（主力）
NovaIcon {
    icon: "10k"
    type: "symbols"
    weight: 400
    style: "rounded"
    filled: false
    color: "#2196F3"
    pixelSize: 48
}

// 经典 Material Icons
NovaIcon {
    icon: "home"
    type: "icons"
    style: "outlined"
    pixelSize: 24
}
```

---

## 六、步骤 5：图标预览 Gallery 完整 QML

**文件路径**：`src/pyside_nova/qml/Nova/Gallery/SymbolGallery.qml`

```qml
// src/pyside_nova/qml/Nova/Gallery/SymbolGallery.qml
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Nova 1.0

Rectangle {
    id: root
    color: Theme.background

    property var indexData: ({})
    property string searchText: ""
    property int selWeight: 400
    property string selStyle: "rounded"
    property bool selFilled: false

    Component.onCompleted: {
        // 读取图标索引 json
        const xhr = new XMLHttpRequest()
        xhr.open("GET", "qrc:/pyside_nova/Nova/assets/symbols/symbol_index.json")
        xhr.onreadystatechange = function () {
            if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
                indexData = JSON.parse(xhr.responseText)
            }
        }
        xhr.send()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // ===== 顶部筛选栏 =====
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            TextField {
                Layout.fillWidth: true
                placeholderText: "搜索图标名称..."
                onTextChanged: root.searchText = text
            }

            ComboBox {
                model: [100, 200, 300, 400, 500, 600, 700]
                currentIndex: 3          // 默认 400
                onCurrentValueChanged: root.selWeight = currentValue
            }

            ComboBox {
                model: ["outlined", "rounded", "sharp"]
                currentIndex: 1          // 默认 rounded
                onCurrentValueChanged: root.selStyle = currentValue
            }

            CheckBox {
                text: "Filled 填充"
                onCheckedChanged: root.selFilled = checked
            }
        }

        // ===== 图标网格 =====
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            GridLayout {
                columns: 8
                columnSpacing: 12
                rowSpacing: 12

                Repeater {
                    model: {
                        if (!root.indexData[root.selWeight]
                                || !root.indexData[root.selWeight][root.selStyle])
                            return []

                        const fillKey = root.selFilled ? "1" : "0"
                        const allIcons = root.indexData[root.selWeight][root.selStyle][fillKey]
                        if (!allIcons) return []

                        if (!root.searchText)
                            return allIcons

                        const kw = root.searchText.toLowerCase()
                        return allIcons.filter(n => n.toLowerCase().includes(kw))
                    }

                    delegate: Rectangle {
                        width: 80
                        height: 80
                        radius: 8
                        color: Theme.surface
                        border.color: Theme.border
                        border.width: 1

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                // 点击复制图标名称到系统剪贴板
                                const clip = QGuiApplication.clipboard()
                                clip.setText(modelData)
                            }
                        }

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4

                            NovaIcon {
                                Layout.alignment: Qt.AlignHCenter
                                icon: modelData
                                type: "symbols"
                                weight: root.selWeight
                                style: root.selStyle
                                filled: root.selFilled
                                color: Theme.textPrimary
                                pixelSize: 32
                            }

                            Text {
                                Layout.alignment: Qt.AlignHCenter
                                text: modelData
                                font.pixelSize: 10
                                color: Theme.textSecondary
                                width: 70
                                horizontalAlignment: Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }

        // ===== 状态提示条 =====
        Text {
            Layout.fillWidth: true
            text: "点击图标复制名称 | weight:" + root.selWeight
                + " | style:" + root.selStyle
                + " | filled:" + root.selFilled
                + " | 当前共 " + iconGridRepeaterCount + " 个"
            color: Theme.textSecondary
            font.pixelSize: 12
        }
    }

    // 统计当前展示数量（供状态条使用）
    property int iconGridRepeaterCount: {
        if (!root.indexData[root.selWeight]
                || !root.indexData[root.selWeight][root.selStyle])
            return 0
        const fillKey = root.selFilled ? "1" : "0"
        const all = root.indexData[root.selWeight][root.selStyle][fillKey]
        if (!all) return 0
        if (!root.searchText) return all.length
        const kw = root.searchText.toLowerCase()
        return all.filter(n => n.toLowerCase().includes(kw)).length
    }
}
```

### 6.1 使用方式

在任意页面直接挂载：

```qml
SymbolGallery {
    anchors.fill: parent
}
```

### 6.2 功能清单

| 功能 | 说明 |
|---|---|
| 名称搜索 | 实时过滤，不区分大小写 |
| 字重切换 | 100 / 200 / 300 / 400 / 500 / 600 / 700 |
| 外形切换 | outlined / rounded / sharp |
| 填充切换 | 线框（fill=0）↔ 填充（fill=1） |
| 点击复制 | 点击图标把名称写入系统剪贴板，可直接粘进 `NovaIcon.icon` |
| 数量统计 | 状态条实时显示当前筛选项下的图标数量 |

### 6.3 依赖项

- `Theme`：pyside-nova 全局主题对象（`Theme.background` / `surface` / `border` / `textPrimary` / `textSecondary`）
- `NovaIcon`：第五章组件
- `symbol_index.json`：第三章脚本产物，必须随 qrc 一起打包

---

## 七、排错清单（实测高频）

| 现象 | 根因 | 处理 |
|---|---|---|
| 导出目录全是空文件夹 | 按 `style/0/`、`style/1/` 结构找源文件，但官方包没有这两层 | 改用 `-fill` 后缀判定，见第三章脚本 |
| `Get-ChildItem` 报"路径不存在" | 同上，路径多了 `\0` 一层 | 直接读 `svg-400\rounded\*.svg` |
| 图标颜色改不动 | SVG 内 `fill` 硬编码未清除 | 确认脚本正则 `CLEAN_ATTR` 生效，检查导出文件内容 |
| QML 里图标不显示 | qrc 未注册 / 前缀写错 / 资源未打包 | 核对 `resources.qrc` 的 `prefix` 与 `_srcPath` 拼接 |
| `symbol_index.json` 加载失败 | 只打了 svg，没把 json 纳入 qrc | 在 qrc 中补上 json 文件 |
| 图标模糊 / 边缘裁切 | 原 SVG 的固定宽高未清或 `sourceSize` 未设 | 确认清洗成功，并设置 `sourceSize.width/height` |
| twotone 双色图标异常 | 双色图标内含两组 path 与独立 fill | 走经典 Icons 时单列处理，或统一改用 Symbols |
| 打包编译极慢 | 全量 15000+ SVG 进 qrc | 开发期精简字重，发布期全量 |

---

## 八、工程约定汇总（建议写进 ARCHITECTURE.md）

1. **目录分工**：`assets/symbols/` 放 M3 Symbols，`assets/icons/material/` 放经典 Material Icons，互不混用。
2. **路径契约**：`symbols/{weight}/{style}/{fill}/{icon}.svg`，禁止在业务代码里硬编码路径，必须走 `NovaIcon`。
3. **命名契约**：图标名一律原样使用官方名称（小写、连字符），不重命名、不翻译。
4. **清洗强制**：任何新图标入库前必须经过 `clean_material_symbols.py`，禁止把带 `fill` 的原始 SVG 直接入库。
5. **协议合规**：全部图标 Apache 2.0，可商用，无需署名；如需在 README 中声明，可注明来源 Google Material Symbols。
6. **版本升级**：升级 npm 包后重跑清洗脚本 + 重新生成索引，Gallery 会自动看到新图标。

---

## 九、附录：命令速查

```powershell
# 1. 安装全部 7 个字重包
npm install @material-symbols/svg-100 @material-symbols/svg-200 @material-symbols/svg-300 @material-symbols/svg-400 @material-symbols/svg-500 @material-symbols/svg-600 @material-symbols/svg-700

# 2. 验证源结构
Get-ChildItem "D:\MyProjects\PyCharm\Project_Nova\Nova-Forge\node_modules\@material-symbols\svg-400\rounded\*.svg" | Select-Object -First 5

# 3. 清理旧产物
Remove-Item -Recurse -Force "D:\MyProjects\PyCharm\Project_Nova\Nova-Forge\pyside-nova\src\pyside_nova\qml\Nova\assets\symbols" -ErrorAction SilentlyContinue

# 4. 执行清洗导出
python src/dev_toolbox_pro/tools/clean_material_symbols.py

# 5. 验证导出结果
Get-ChildItem "D:\MyProjects\PyCharm\Project_Nova\Nova-Forge\pyside-nova\src\pyside_nova\qml\Nova\assets\symbols\400\rounded\0\*.svg" | Select-Object -First 5
```

> 版本细节以 Google Material Symbols 官方仓库与 npm 包发布说明为准；图标总数、目录结构随版本可能微调，升级后请重跑第三章验证命令。

> （注：部分内容由豆包 AI 生成）