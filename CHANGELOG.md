# Changelog

所有版本变更记录，遵循 [Semantic Versioning](https://semver.org/) 规范。

## [0.6.0] - 2026-11-28 — T3 完现：migrate2nova 子命令（100% 迁移）· 第 11 枚应用图标 / 专属暗色主题 ⭐ 当前版本（待 CSA 发布）

### ✨ Added（T3 · 原名 `migrate_to_nova`，CSA 建议更名便于输入）
- 新增主命令 **`nova-forge migrate2nova`**（旧名 `migrate_to_nova` 保留为隐藏 alias，史料不圆场 / 交叉引用不断）：一键 QtWidgets → pyside-nova 迁移助手，默认 **dry-run**，`--scaffold` 才写盘。
- 迁移包 `src/nova_forge/migrate/`：`freeze.py`（冻结面唯一法源，自动探测同级 `pyside-nova/api/nova-api-*.json` 最新版本）· `rules.py`（**72 条** QtWidgets → Nova 处置规则，`AUTO/RUNTIME/NATIVE/MANUAL` 四类 + `UNKNOWN_RULE` 兜底 MANUAL，零静默遗漏）· `scanner.py`（纯 AST 扫描，不导入 PySide6）· `contract.py`（§9.4 五道契约门）· `backup.py`（§9.3 `%TEMP%/nova-scratch/` 自建自删 / `--restore` 回滚）· `scaffold.py`（`Main.qml` + `main.py`，QML 优先、加载失败动态降级回原窗口类）· `report.py`（`MIGRATION_TODO.md` 人读 + `migration-report.json` 机读）· `plan.py`（编排层；契约门 FAIL 抛 `ContractBlockedError`，一个字节都不写）。
- 参数：`-p/--path` · `--api` · `--scaffold` · `--out` · `--force` · `--json` · `--entry-args` · `--qml-root` · `--list-mapping` · `--restore` · `--list-backups` · `--clean-backups`。双语 README 命令清单与 Quick Start 同步。

### 🎯 100% 口径（T3 验收定义，写实不写虚）
- 试验田 `src/nova_forge/ui/saver_window.py`：**1** 个 `.py` · **22 个唯一 Qt 名** · **100%（22/22）** 全部进入四类处置（`AUTO 11 / MANUAL 2 / NATIVE 5 / RUNTIME 4`），MANUAL 明确为 `QSplitter` 与 `QSystemTrayIcon`，未知 Qt 名一律兜底 MANUAL，零静默遗漏。
- 冻结面驱动映射表：`nova-api-1.11.0.json` · API `1.11.0` · **147 类型** · 指纹 `9966483dda5a53c4`；`--list-mapping` 实测 **72 条规则 / AUTO 目标悬空 0 个**，所有 AUTO 目标在冻结面真实存在（法源链零悬空），不手写 Nova 类型清单。
- 五道契约门 `static-tier` / `coverage` / `qmllint` / `modelValue` / `slot-constitution`：dry-run 下前两门 PASS、后三门 SKIP（未生成骨架）；`--scaffold` 时五门实跑全绿方落盘。
- 硬约束全守：原 `.py` 零改动 · 默认 dry-run · QML 加载失败降级回原窗口 · 补缺与迁移命令解耦（P2 生态建议只在 `MIGRATION_TODO.md §3.1` 登记，pyside-nova 147 公共面零改动、不重签）。

### ✨ Added（第 11 枚应用图标 + 第 11 套专属主题）
- `app-aireport.svg`（仪表钢蓝 **258°**）落两工程 `resources/icons/`，qrc 双别名 `:/icons/app-aireport` / `:/icons/app-aireport.svg`，`resources_rc.py` 重编；`catalog.py` / `gen_app_icons.py` 单一事实源 10 → 11。
- `NovaAIReport` 补齐 `_signatureOn` / `_themeHue`(+0.0694) / `_accent` / `_ink` / `_inkSoft` / `_glow` 与 `NovaIcon` 身份徽记，与其余 10 壳同构；`ai_report` demo `run.py` 自包含 DWM helper（`darkChromeChanged(bool)` → 属性 20/19）同步 Windows 原生暗色标题栏。`GUIDE_COMPONENT_THEMES.md` / `NovaAIReport.md` §6 登记。

### 🐛 Fixed（T3 · 坑位 83）
- 全量 pytest 暴露真实回归：**4 failed / 201 passed**，根因是 Windows 版 `qmllint.exe` **不支持 `-` stdin**（把 `-` 当文件名、返回 `-1`、stderr 只有 `Failed to open file -`），而 `contract.py` 把「0 error 但 `returncode != 0`」误判为 FAIL；且**导入 PySide6 会把 `site-packages/PySide6/`（内含 `qmllint.exe`）注入 PATH**，令契约门在「专向单跑 / 全量跑」间行为漂移（专向 25 passed、全量 4 failed）。
- 修法：qmllint 门改**落临时文件实跑、跑完自删**（`tempfile.TemporaryDirectory`），自动探测同级 `pyside-nova/src/pyside_nova/qml` 作 `-I` 令 `import Nova.*` 真解析（实测 RC=0 / 0 warning / 0 error）；判据改为**以 `Error:` 行为准零容忍**，warning 数与 rc 如实登记不掩盖，工具零输出非 0 退出时回退「静态契约 PASS（实跑未完成）」不谎称通过。新增 `test_qmllint_gate_survives_pyside6_import` 固化。

### ✅ 验证（T3 + 图标主题）
- 新增 `tests/test_migrate2nova.py` **26 passed**（含坑位 83 回归）：冻结面发现 / schema 异常 / 零悬空 / 未知名兜底 / 试验田 22 名 100% / 五门 / JSON·TODO / dry-run 不写盘 / scaffold 原 `.py` 字节不变 / QML 五槽 / 降级 / FAIL 不落盘 / 备份回滚清场 / CLI help 与旧 alias。
- nova-forge 全量 **206 passed + 32 subtests**（较 T23 的 180 + 32 增 26 项）· `test_titlebar_and_hatch.py` 18 passed · pyside-nova 图标/主题专项 26 passed · ruff 新增/修改文件 `All checks passed!` · qmllint 0 error。
- 真机：骨架 `Main.qml` 离屏 `ROOTS 1 / TOTAL_MSGS 0 / BAD_MSGS 0`；强制 QML 缺失时动态加载 `SaverWindow` `FALLBACK_RC 0`；`ai_report` demo `TOTAL_MSGS 0`；`check_api_freeze.py` **147 类型零漂移** · 三 `--check` 全绿 · 生成器幂等 · **wheel 干净构建通过（118 项，含 `migrate/` 9 文件 / `cmd_migrate.py` / `app-aireport.svg` / `resources_rc.py`）** · `mkdocs --strict` EXIT=0。

### 📌 如实登记
- T3 只改 nova-forge 侧与其文档/测试；**pyside-nova 1.11.0 冻结面 / 147 类型 / 指纹 `9966483dda5a53c4` 零改动**，不升版、不重签。
- **ruff 存量挂账（发布前只读扫描 · 按 CSA 拍板保持不修）**：全量 `src tests scripts` **15 条** = `UP012` 7（`tests/test_comment.py`）· `F401` 3（`cmd_saver.py` ×2 / `test_comment.py` ×1）· `N802` 2（`resources/resources_rc.py`，`pyside6-rcc` 生成物固有）· `RUF005` 1（`core/comment_logic.py:220`）· `SIM105` 1（`cmd_publish.py:28`）· `RUF015` 1（`test_comment.py:243`）；**9 条 `--fix` 可修（3 条 unsafe）/ 6 条需手工或豁免**。逐条归属：全部落在 `v0.5.0` 发布提交 `db76dd5e1` 或更早，T3 新增的 `migrate/` 9 文件 / `cmd_migrate.py` / `cli.py` / `test_migrate2nova.py` 全部 ruff 干净 → **不阻塞发布**。上一轮「均在 T23 未改动文件（`test_comment.py` 等）」口径不准确，此处如实校准（实际涉及 5 个文件，且 `resources_rc.py` 是本轮重编的生成物）。不一把 `--fix --unsafe-fixes` 梭哈：`N802` 属生成器固有、改了下次重编必回潮，`cmd_saver.py` 的 `import resources_rc` 是「导入即注册 qrc」的误报倾向，盲删会破坏资源注册与生成器幂等。
- wheel 首次以 `--no-isolation` 构建因当前解释器 setuptools 后端元数据校验差异失败，改隔离模式 `python -m build --wheel` 即通过 → 工具/环境差异，非本轮代码引入；生成器幂等首次 BEFORE/AFTER 不等系生成物追上本轮新增 `SESSION_HANDOFF.md` 输入，按项目口径连跑两遍后哈希一致（`IDEMPOTENT: PASS`）。
- §9.4 原方案骨架（根 `PROMPT.md §9`）、`nova-api-1.0.0.json` 史料行、旧名 `migrate_to_nova` 均按「史料不圆场」逐字保留，仅追加现行校准段。
- **发布态校准（11-28 04:50）**：`pyside-nova 1.11.0` **已由 CSA 发布**（HEAD `596f304` = tag `v1.11.0` = `origin/main`，工作树干净）；`nova-forge 0.5.0` **已发布**（tag `v0.5.0` → `db76dd5e1`），T3 全套随后以 `eb0bfef9d` 提交并推送 `origin/main`、**尚无新 tag**。按 CSA 拍板升 **0.6.0 minor**（T3 新增子命令 + 第 11 枚图标 / 主题，SemVer 向后兼容新功能），归档 `Unreleased` 为 `[0.6.0]`，`pyproject.toml` / `docs/PRESCRIPT_GALLERY.md` 版本同步。测试夹具中 `plan_project(..., "0.5.0")` 等字符串是入参常量而非版本声明，按最小改动不回改；`[0.5.0]` 段「当前版本（待 CSA 发布）」为当时点史料，按「史料不圆场」不回改。
- `commit / push / tag / PyPI / 站点上线` 全归 CSA；本轮升版与账本校准改动全部留本地工作树，等待 CSA 发版。

## [Unreleased] — 11-27 20:12 T23：README 英雄卡改用 NovaMarkdown 渲染 md

### ✨ Added / 🔧 Changed（T23）
- 英雄卡 README 展开区由「`NovaScrollArea` + 裸 `Text(Text.PlainText)` + Consolas 10px 显示 md 源码」整块替换为库组件 **`Nova.Controls.NovaMarkdown`**（1.4.0 第 145 类型）：真实点击 `readmeBtn` 后渲染标题 / 列表 / 表格 / 链接，左侧内置 TOC 大纲可跳转；`showToc: true` / `outlined: false` / `baseFontSize: NovaTheme.fontXS` / `openLinksExternally: false`，卡片展开高度 `330 → 400`。组件自带 `NovaScrollArea` 滚动 + 空态，故**不双层嵌套 Flickable**。
- 内容仍走 `bridge.readmeDoc` 单一事实源（生成器产物 `docs/components/<shell>.md`，缺失时回退将落盘的 `README.md`）；`linkClicked` / `linkBlocked` 复用窗口级 `showToast(kind, message)` → `NovaNotify.show({...})` 唯一实际调用点，不另立通知链路。
- `[project.optional-dependencies].gui` 下限 `pyside-nova>=1.3.0 → >=1.4.0`（`NovaMarkdown` 自 1.4.0 起导出，账实相符）；双语 README 补注「产物 ≥1.2.0 / GUI 工作台 ≥1.4.0」的分层口径。

### 🐛 Fixed（T23 · 坑位 76）
- 生成物 20 份组件文档各含 3 个 `![alt](../screenshots/*.png)` 相对图片（1280×800 史料截图）；`Text.MarkdownText` 以**实例化它的 QML 文件所在目录**（`pyside_nova/qml/Nova/Controls/`）为 baseUrl 解析，与 `docs/components/` 不同树 → 真机刷 **708 条 `Cannot open: .../Nova/screenshots/*.png`**；且大图内嵌进 400px 英雄卡三列表格会撑爆布局。
- 视图模型层 `gui_model.component_doc()` 新增纯函数 `_display_text()` 与显示适配字段 **`renderText`**（图片引用 → `alt（展示图 · 见仓库）` 文本占位）；**`text` 仍逐字等于生成物**（账实同源不变），bridge 转发并防御 mock 缺字段，QML 绑 `renderText`。不改生成物、不改冻结面、不动库组件。
- `verify_prescript_gui.py` 把 `Cannot open` / `Binding loop` / `failed` 一并纳入「坏消息」判定，不再只按字面 `error` 放行。

### ✅ 验证（T23）
- 全量 **180 passed + 32 subtests**（较 T19 的 176 增 4 项）· T23 改动 5 个文件 ruff 全净 · qmllint **0 error** · wheel 构建通过（`Requires-Dist: pyside-nova>=1.4.0; extra == "gui"`）。
- 离屏真机真实点击 README：`NovaMarkdown` 装载 · `toc=9` 条大纲 · `empty=False` · `markdown` 与 `renderText` 逐字同源 · 逐字原文 `text` 2975 字符保留 · **Qt 消息 0 条 / 坏消息 0 条 / exit 0**；三张截图（默认态 / README 展开态 / 三态装配图表格区）目视确认渲染后 Markdown 与连续等高表格、无破图无裁字。
- pyside-nova 冻结面零漂移：静态 3/3 · `gen_prompt.py` / `gen_api_freeze.py` / `sync_brand_version.py` 三个 `--check` ✓ · **146 类型 / 指纹 `9742de8638251876`**。

### 📌 如实登记（既有挂账，非 T23 引入，未越界批量扫荡）
- `ruff check src tests scripts` 全量 15 条均在 T23 未改动文件（`cmd_publish.py` / `cmd_saver.py` / `comment_logic.py` / `resources_rc.py`（生成物）/ `test_comment.py`）；T23 改动文件 0 条。
- nova-forge `pyside6-qmllint` 128 warning / 0 error，均为 `bridge.` / `win.` 上下文属性 unqualified 既有风格（nova-forge 无 warning 预算门禁；pyside-nova 594 预算门禁不受影响）。

## [Unreleased] — 11-27 12:41 T19：prescript 产物 app.py 双模式入口

### 🐛 Fixed（T19）
- 修复 T17 改名遗留缺陷：薄入口 `from .main import main` 在 IDE / 命令行直接 `python app.py` 时（`__package__` 为空）触发 `ImportError: attempted relative import with no known parent package`。`_entrypoint()` 改为按 `__package__` 分支的双模式入口：包内（`python -m <pkg>.app` / console entry `<pkg>.app:main`）走相对导入，直接脚本显式把脚本目录插入 `sys.path` 后走 `from main import main`；**刻意不用 `try/except ImportError`**，避免吞掉 `main.py` 内部真正的依赖错误。
- README「快速开始」新增直接运行说明，并按 `all_files` **条件渲染**：用户取消勾选 `src/<pkg>/app.py` 时不出现该段（T14 账实同源契约，旧断言已校准）。
- 产物自检 `test_entry_layout` 增加双模式三断言；`tests/test_entry_layout.py` 静态契约同步。
- 已落盘工程 `nova_incubator_app/src/nova_incubator_app/app.py` 用生成器 `_entrypoint()` 精确覆盖（逐字同源），README 快速开始同步。

### ✅ 验证（T19）
- 新增 `tests/test_direct_run.py` 5 项真机回归：布局 / manifest 不变（仍 17 文件）· 落盘入口与生成器逐字同源 · **脚本模式不带产物 src** 真机启动 · 模块模式 · console entry 可导入。
- 全量 **176 passed + 32 subtests** · ruff 全净 · `render.py` ast OK · 离屏三模式真机全绿 · 用户原始命令复跑 **exit 0 / 0 输出**。
- pyside-nova 冻结面零改动（144 类型 / API 1.3.0 / 指纹 `5d865b2d976af016`）。
## [Unreleased] — 11-27 12:28 T18：确认框 CTA 归位右下角

### 🔧 Changed（T18）
- 「取消 / 🤝 确认孵化」两个 `NovaBtn` 从 `Flickable` → `Column` 内容流移出，作为 `gateCard` 直接子项 `gateActions` 右下锚定（`rightMargin: 22` / `bottomMargin: 16`），**固定在卡片右下角、不随摘要内容滚动**；顺序保持「取消 → 确认孵化」，主按钮最右。
- Column 末尾新增 `gateActionSpacer`（高 46 = CTA 约 32 + 12 间距 + 余量），Flickable 内容区高度不缩水，滚到底时最后一行文字不被按钮遮挡。
- 三个 `objectName`（`gateActions` / `gateCancelBtn` / `gateConfirmBtn`）供离屏验收定位。

### ✅ 验证（T18）
- 新增 `tests/test_gate_actions.py`（4 项：右下锚定 / 结构归属 / 按钮顺序 / T15-T16 摘要与 GroupBox 契约不受影响）。
- 全量 **171 passed + 32 subtests** · ruff 全净 · qmllint 0 error · 离屏真机 roots=1 / 0 Qt 消息，右边距 22 / 下边距 16 精确命中、按钮在卡片右半部与下部、真实点击「取消」→ `gateOpen` false、实拍无遮挡。
- pyside-nova 冻结面零改动（144 类型 / API 1.3.0 / 指纹 `5d865b2d976af016`）。

## [Unreleased] — 11-27 12:11 T17：prescript 产物入口改名

### 🔧 Changed（T17）
- **入口改名**：`src/<pkg>/app.py` → `main.py`（启动器：QML 加载 / DWM 标题栏 / 应用图标），`src/<pkg>/__main__.py` → `app.py`（薄入口，`from .main import main` re-export）；**不再生成 `__main__.py`**，产物仍是 17 文件、包内 py 恰为 `__init__` / `app` / `main` 三件。
- **启动命令全链同步**：`python -m <pkg>` → **`python -m <pkg>.app`**（README 快速开始 / `__init__.py` docstring / CLI 成功提示 / `gui_model.hatch()` 返回 `command` / `_smoke_run` 离屏实跑 / `docs/PRESCRIPT_GALLERY.md` / 双语 README）；`[project.scripts]` 与 `prescript.json` 的 `<pkg>.app:main` 保持有效（薄入口 re-export `main`）。
- `scaffold` 叠加仍恒 `include_entry_py=False`：其 `main.py` 是占位模板，不得覆盖 prescript 启动器。
- 产物自检 `tests/test_smoke.py` 新增 `test_entry_layout`；标题栏断言改读 `main.py`。

### ✅ 验证（T17）
- 新增 `tests/test_entry_layout.py`（13 项：九配方布局 / 薄入口 re-export / 启动器 / 入口引用 / manifest / README 树 / 运行链路 / 按选落盘），校准 4 组旧断言。
- 全量 **167 passed + 32 subtests** · ruff 全净 · 离屏真机 `render_project` → 包内 py 三件 → `python -m <pkg>.app` 根对象加载成功 1.2 s 无 QML ERROR → `from <pkg>.app import main` 可调用。
- pyside-nova 冻结面零改动（144 类型 / API 1.3.0 / 指纹 `5d865b2d976af016`）。

## [Unreleased] — 11-27 12:02 T16：英雄卡 README 与隐显按钮归位

### ✨ Added（T16）
- **英雄卡 README 按钮**：`NovaBtn` 点击后卡片 68→330 展开 `NovaScrollArea` 视口，显示当前选中配方对应的组件说明 `docs/components/<shell>.md`；文件名由 `catalog.Kind.shell` 单一事实源推导，九配方 9/9 命中，`gui_model.component_doc()` 只读生成物（`NOVA_COMPONENT_DOCS` 显式覆盖 > 包位置推导 > 工作区回落），不复制台账。
- **回退内容账实同源**：`plan_summary().readme` / `bridge.readmeText` = 将落盘的 README.md 全文；组件文档未随 wheel 发布时 `bridge.readmeDoc` 自动回退，未勾选 README.md 则据实提示，绝不展示一份「其实不会创建」的文档。
- `tests/test_readme_hero.py`：单源 / 回退 / 桥接 / QML 契约 16 项回归。

### 🔧 Changed（T16）
- 左右轨隐显按钮从底部 `pipelineSlot` 移到 `globalSlot` 左上角 / 右上角，管道条只留 CARF 阶段块与请求孵化钮；壳受控契约不变。
- 校准 T15 遗留旧断言：`keyFiles` 为 5 项恒列，取消勾选只置 `included=false`。

### ✨ Added（T15 · 上轮）
- **确认孵化框项目摘要**：从「17 个文件 + 路径」升级为结构化摘要——版本 / 作者 /
  包名 / 许可证 2×2 网格 + 描述整行 + 「将创建的主要文件」chips（pyproject.toml /
  README.md / README_zh.md / LICENSE / CHANGELOG.md，与勾选联动置灰）。
- **摘要账实同源**：`plan_summary().meta` 直接解析生成的 `pyproject.toml`（新增
  `[project].authors`），`keyFiles` 从落盘清单取；确认框不另立台账，所见即落盘内容。
- `templates/tmpl_config.py` 新增 `DEFAULT_VERSION` / `DEFAULT_AUTHOR_EMAIL` 单一事实源，
  prescript 与 scaffold 两条生成链路的作者 / 版本同源，消除硬编码漂移。

### 🔧 Changed（T15 · 上轮）
- `prescript` 生成的 `pyproject.toml` 补上 `authors = [{ name, email }]` 字段。
- 确认弹窗用 Flickable 兜底防止内容溢出，暗色主题观感打磨。

## [Unreleased] — 11-27 11:05 T14：文件清单组选框（勾选决定实际创建哪些文件）

### ✨ Added
- **`fileChoices` 组选框列表**：「将生成的文件」面板由只读表格改为逐项 `NovaCheckbox`，
  按 PySide6 QML / src 布局列出全部 17 个预知文件（含路径与体量），可滚动；
  默认全选，新增「全选 / 清空」按钮。
- **按选落盘**：`GUIConfig.selected_files` + `plan_project(render_project)` 的
  `include_files` 过滤；`README.md` 结构树与 `prescript.json.files` 由过滤后的
  `all_rel` 生成，只写用户勾选的文件且清单与磁盘逐项一致。选中子集时跳过冗余
  scaffold 补齐调用（避免把取消的治理文件写回来）。
- 桥接层新增 `setFileSelected(path, bool)` / `selectAllFiles(bool)` Slot；
  配方 / 应用名 / 包名变化时重置选择（相对路径含包名，旧勾选会失效）。

### 🔧 Changed
- 文件面板标题改为「勾选决定实际创建 · 未落盘」；chip 的文件数与体量、
  确认孵化弹窗数字均随勾选实时变化。

### ✅ Tests
- 新增 `tests/test_file_choices.py` 5 项（完整清单 / 计数 / 按选落盘账实 /
  空选拒绝 / scaffold 不回补）；全量 **132 passed + 23 subtests**；
  ruff 全净；离屏 GUI roots=1、17 个复选框全渲染、0 QML 错误；
  pyside-nova 静态 3/3 PASS（冻结面零漂移）。

## [Unreleased] — 11-27 10:52 T13 补丁：修复 prescript 全部应用图标 404

### 🐛 Fixed
- **qrc 别名与 catalog 文件名对齐**：`resources.qrc` 的 10 枚 `app-*` 别名补 `.svg`
  后缀（与 `catalog.Kind.icon` / `gui_model` / `QIcon` / 测试断言回归一致），重编译
  `resources_rc.py`。此前 `:/icons/app-agent.svg` 等路径全部落空，配方卡与窗口图标不可见。
- **预览标题图标空值守卫**：`NovaIcon.icon` 改从 `previewKindSpec().icon` 单一事实源取值，
  `previewKind` 未选时不渲染，消除 `qrc:/icons/app-` 空路径报错。

### ✅ Tests
- 新增 `test_workbench_qrc_aliases_match_catalog_icon_files` 静态断言；全量
  **127 passed + 23 subtests**；离屏加载 prescript 主窗口 roots=1、切换
  agent/orbit/incubator 预览 **0 个 QML/资源错误**；三枚 `QIcon` 实测 `isNull=False`。

## [Unreleased] — 11-27 10:45 T13：scaffold ↔ prescript 打通（--project 绝对路径 + 完整工程 17 文件）

### ✨ Added
- **`scaffold --project/-p`**：显式传入项目完整绝对路径时跳过路径询问；不指定时仍要求用户输入绝对路径（交互行为不变）。
- **`core/scaffold_logic.py`**：scaffold 文件清单单一事实源（`COMMON_FILES` / `DESKTOP_FILES` / `MOBILE_FILES` + `scaffold_file_plan()` + `prescript_overlay_plan()`），CLI 与 prescript 共用，避免两处模板漂移。
- **非交互入口 `scaffold_project(target_root, ...)`**：返回结构化 `{ok, written, skipped, root, projectName}`；prescript 确认孵化后显式调用，幂等补齐通用工程骨架。

### 🔧 Changed
- **prescript 产物 11 → 17 文件**：叠加 scaffold 的 6 个通用治理文件（LICENSE / README_zh.md / CHANGELOG.md / HOW_TO_PUBLISH.md / `.github/workflows/publish.yml` / project_structure.txt）；同名文件一律保留 prescript 版本。
- **`prescript.json.files` 与 README 结构树改为从实际清单动态生成**，GUI 预览 fileCount / 落盘 / manifest 三方账实相符（17/17）。

### 🐛 Fixed
- 交互入口 `write_plan` 的 emit 回调签名不兼容（`write_file(rel, tmpl)` 被当成 `emit(msg)` 调用 → TypeError），统一为单项打印回调 + `force` 参数。
- 目录 vs 合法空文件（`project_structure.txt`）歧义：引入 `DIR_SENTINEL=None` 严格区分，修掉 force 模式 `FileExistsError`。
- Windows 大小写不敏感下 `qml/main.qml` 与 prescript `Main.qml` 冲突：叠加时排除 `main.qml` 与 `main.py`，避免三入口并存。

### ✅ Tests
- `tests/test_scaffold_integration.py` 8 项专项；全量 **126 passed + 23 subtests**；ruff 全净；pyside-nova 静态 3/3（冻结面零漂移）。
- 端到端 orbit 孵化：17 文件落盘、manifest 与磁盘逐项一致、scaffold 6 文件齐全；CLI `scaffold --project <abs>` 实跑 12 文件成功。

## [Unreleased] — 11-27 06:55 T12：10 个专属主题组合根的应用图标 + 暗色主题原生标题栏

### ✨ Added
- **10 枚应用图标**：`src/nova_forge/resources/icons/app-*.svg`，覆盖九配方壳
  （Agent 233° / Copilot 266° / DE 205° / Orbit 243° / Desktop 223° / Chat 216° /
  Mobile 193° / Flex 176° / SetupWizard 168°）+ 第 10 个 `NovaIncubator` 283°。
  色相由 `catalog.KINDS.hue` 单一事实源驱动，生成器 `scripts/gen_app_icons.py` 幂等
  （`--check` 校验）；纯几何 path，无 `textPath` / 渐变，QtSvg 实测 10/10 真实渲染有效。
  同步注册 `resources.qrc` 别名、重编译 `resources_rc.py`，`package-data` 补
  `resources/*.qrc` 与 `resources/icons/*.svg`。
- **图标接入三处**：GUI 配方库卡片（`prescript_main.qml` 的 `Image.source` 取
  `catalog.Kind.icon`）、孵化器工作台窗口图标（`QIcon(":/icons/app-incubator.svg")`）、
  **每个孵化产物**自带 `src/<pkg>/assets/app-<code>.svg` 并在 `app.py` 里 `setWindowIcon`
  （产物独立工程，故另产出 `resources/app_icons.py` 常量模块内嵌 SVG 文本）。
- **暗色主题原生标题栏**：`utils/window_utils.py` 泛化为 QWindow/QWidget 通吃，新增
  `apply_dark_title_bars(dark)` 遍历顶层窗口同步 DWM immersive dark mode；两个桥接层加
  `@Slot(bool) setDarkTitleBar`；GUI QML 用 `chromeDark: NovaTheme.isDark` 属性绑定 +
  `onChromeDarkChanged` 同步（含初始化与每次明暗切换）；`cmd_prescript` / `cmd_icons`
  窗口句柄就绪后初始同步。
- **孵化产物同样自带标题栏同步**：`app.py` 内嵌自包含 DWM helper（零 nova-forge 依赖），
  `Main.qml` 声明 `signal darkChromeChanged(bool dark)`，由 `onThemeModeChanged` 与
  `Component.onCompleted` emit；无监听者时 emit 无害，离屏 9/9 实跑仍 0 ERROR。
- `tests/test_app_icons.py` 新增 19 项专项回归；产物 `test_smoke.py` 增
  `test_app_icon_present` / `test_title_bar_sync_wired`；文件清单 10 → **11**（+图标），
  manifest / README 结构树 / GUI 预览同源自动账实相符。

### ✅ 验收（11-27 07:30）
- `pytest` **114 passed + 23 subtests** · 本轮触碰文件 `ruff` 全净 ·
  `gen_app_icons.py --check` 幂等 · 标准隔离 wheel 构建通过（106 文件，10 枚 SVG 入包）。
- GUI 离屏实跑 0 ERROR，抓图 `docs/prescript-gui-app-icons.png`（配方库九项图标可见）。
- 九配方落盘产物 **9/9 离屏实跑 0 ERROR**；产物 smoke `6 passed`（带 `PYTHONPATH`）。
- 端到端真实事件链：窗口级 `QTest.mouseClick` 主题按钮 → QML `onChromeDarkChanged`
  → 桥接 Slot → DWM `value` 1↔0 双向同步（spy 拦截，非源码自证）；
  QML `Image.status=Ready`、10 枚 SVG `QSvgRenderer.isValid()` 全 True。

## [0.5.0] - 2026-11-26 — `prescript` 子命令：NovaIncubator 一键孵化九类企业级应用 ⭐ 当前版本（待 CSA 发布）

> **additive minor**：新增子命令与生成器包，既有 11 个子命令零改动、公共 CLI 契约不破坏；
> 依赖 `pyside-nova>=1.2.0`（API 契约 1.2.0，冻结指纹 `4f882374ad52262b`）。

### ✨ Added
- **`nova-forge prescript`**：用 `NovaIncubator` 七槽孵化工作台一键生成可运行的 PySide6 应用，
  九类配方对应九个 Prescient Layout Shell（`NovaIncubator` 本身除外）：
  `agent` / `copilot` / `de` / `orbit` / `desktop` / `chat` / `mobile` / `flex` / `wizard`。
  交互式 + 全参数两种模式，支持 `--list` / `--dry-run` / `--force` / `--verify-run`。
  `--verify-run` 会离屏启动刚孵化的应用 1.2 s，把 QML 运行时错误也算进交付门禁。
- **九配方单源目录** `src/nova_forge/prescript/catalog.py`：品类、壳、定位、性能承诺、
  门禁、交付五件套、能力要点一处定义，QML / README / manifest / 自检共用。
- **九个成品级舞台** `stages.py`：每类一套真实业务界面（任务队列 / 落盘闸门 / SLA /
  意图轨道 / 仪表盘 / 会话 / 触控列表 / 自适应栅格 / 部署步骤），全部为本地状态机，
  不联网、不隐式写盘；舞台内壳断点按壳分档（agent/copilot/de/orbit=480，chat=700 响应式），七槽宿主与各壳自身槽位均按宽度合理呈现。
- **七槽宿主** `templates/tmpl_host_main_qml.py`（原 `tmpl_main_qml.py`，重命名自证归属
  ——这是**被孵化应用**的 Main.qml，非 nova-forge 自身 GUI）：配方库 / 三重校验 /
  CARF 四阶段 / 封版证书 / 人工确认闸门，封版必须点击确认，脚本不自动签发。
- **工程骨架** `render.py`：`pyproject.toml` / 双语启动器 / `Main.qml` / `Stage.qml` /
  `prescript.json` / README / 冒烟用例；生成时跑三重校验（完整性 / Python 语法 / QML 结构 / 清单一致）。
- **离屏实跑校验** `scripts/verify_prescript_app.py`：加载 Main.qml、收集 QML 运行时告警、
  可导出 Chrome 无关的 Qt 截图（`PRESCRIPT_SHOT`）。
- **GUI 界面预览**（CSA 2026-11-26 提案）：孵化工作台舞台 hero 卡新增「👁 界面预览」，
  全窗口 NovaCard 浮层内以 Loader **真 QML 实装渲染**所选配方的 Stage.qml——
  与落盘产物同源单字不变，非截图、非 mock；九配方 chips 可在浮层内独立切换，
  不污染工作台配置态；Esc / 点击遮罩关闭。实现链：
  `gui_model.stage_qml()` 单源 → `bridge.stageQml/previewStage` 写临时副本
  （每配方独立子目录，规避 QML 目录扫描缓存 case-mismatch 假错）→ QML Loader 加载。
  验收脚本新增 `prescript-gui-preview.png` 实拍 + chat/flex 双配方 Ready 断言。
- **徽记可点（pyside-nova 1.3.0 additive 对接 · CSA 22:22 拍板「给 pyside-nova 提改造，
  先升 minor 重签」）**：`NovaIncubator` 新增 `emblemClickable:bool` + `emblemClicked()`
  （API 契约 1.2.0 → 1.3.0 重签）；孵化工作台
  `shell.emblemClickable: true` + `onEmblemClicked: win.openPreview("")`——
  点壳右上角小太阳即看所选应用的真实界面（CSA 原始愿望达成）；
  `[gui]` extra 升 `pyside-nova>=1.3.0`、`API_VERSION` → 1.3.0
  （生成应用依赖下限 `NOVA_FLOOR` 仍 1.2.0：生成物只用 1.2.0 已有面）。
- **一功能一入口（CSA 2026-11-27 拍板）**：pyside-nova 1.3.0 同批追加
  `emblemToolTip:string` 后，徽记挂 `emblemToolTip: "界面预览"`（悬停即见入口说明），
  hero 卡独立「👁 界面预览」按钮摘除——避免双入口重复。
- **tooltip 悬停不显示 · 根因修复（CSA 2026-11-27 两次实测反馈）**：前两轮误判——
  先以为缺「受控写回」（`onUpdateModelValue` 补上仍不显示）。根因是
  **NovaTooltip 根 Item `visible: modelValue` 初始 false，Qt Quick 里不可见 Item 的
  HoverHandler 不参与指针命中 → 内建悬停死锁**（要显示先得 visible，visible 靠
  modelValue，modelValue 又靠内建 hover）。真实 `QTest.mouseMove` 探针实证：
  内建链 hover 后 visible 恒 False，宿主可见 MouseArea 绑定链 hover True / 移开 False。
  壳改**宿主绑定驱动**（`containsMouse` → 500ms Timer → `modelValue` 绑定），
  内部状态 `_tipHovered`（`_` 前缀不进冻结面，指纹 `5d865b2d976af016` 保持零漂移）；
  验收脚本弃「set modelValue 自证」，改 **QTest 真实鼠标悬停断言**（hover→visible=True /
  移开→hidden=True），`docs/prescript-gui-tooltip.png` 悬停实拍气泡可见。
- **体量人性化单位（CSA 22:22 指令）**：文件清单 / 体量 chip 达到 KB/MB/GB
  显示对应单位（`fmtSize()`），不再统一 B。
- **管道条水平居中（CSA 22:22 指令）**：CARF 四阶段行整体
  `horizontalCenter` 居中，不再左贴边。
- **「已落盘」账实不符 · 两层修复（CSA 2026-11-27 三连报）**：
  - **第一层（粘性旗标）**：`_written` / `win.frozen` 是粘性会话旗标，孵化成功过
    一次后改配方 / 目录不复位。修法：桥接 `_update()` 逐字段比对，配置实际变化即
    复位 `written=False`（同值赋值不误伤）；QML `frozen` 改 `readonly` 绑定
    `bridge.written`；文件清单标题动态化（预览·未落盘 ⇄ 已落盘·N 个）。
  - **第二层（真根因 · pyside-nova `NovaInput` 坑位 53）**：UI 仍显示新路径但文件
    落到 `prescript-app`（真实事故：浏览选 `D:/TEST_INCUBATOR` 后孵化落盘到旧目录）。
    最小实验铁证：外部写 `modelValue='SET_A'` 后 `text='SET_A'` 而 `modelValue='SEED'`
    （上一拍）——`NovaInput._emitChange()` 在变更级联里读 `typedValue` 绑定读到旧文本，
    浏览回显时把旧路径经宿主守卫误判 `setPath` **静默改回**。根因修复在
    pyside-nova（`_typedOf(t)` 纯函数直读 `input.text/area.text`，并入 1.3.0 同批）；
    宿主验收脚本新增「输入框回显同步」断言（写入 → `bridge.path` 必须一致，
    回退即坑位 53 复发）。修复后实测：回显同步 ✓ · hatch 落盘 14 个文件精准到
    指定目录 ✓。

### ✅ Tests
- `tests/test_prescript.py` 13 passed / 18 subtests：九配方稳定、七槽齐全、
  「只有一项 loaded=true」（回归 JS 字符串真值 bug）、清单一致、CLI 全路径。
- 九类产物逐个离屏实跑：9/9 根对象存在、0 QML ERROR；九张实拍截图目视验收通过。

### 🔧 Refactored（CSA 2026-11-27 三项拍板）
- **孵化目录语义**：GUI / 浏览框提供的是**孵化根目录**，项目必须在根目录之下以包名
  建独立子目录（如 `D:/TEST_INCUBATOR/nova_incubator_app/`），绝不直接写根目录本身
  ——占满判定也只看工程目录，根目录非空照常孵化；根目录不存在时向上探最近已存在
  祖先判合法性，落盘 `mkdir(parents=True)` 自动补齐。`gui_model.resolve_target()` 单点
  解析，`plan_summary` 新增 `workspace`（用户根目录）与 `root`（工程目录）双字段。
  CLI `--path` 保持「工程目录」显式语义不变（其默认值本就含应用目录名）。
- **桥与界面分离**：`ui/prescript_bridge.py` / `ui/icons_bridge.py` → `bridge/` 新包
  （QObject 桥专属层），`ui/` 只留窗口装配（`icons_window.py` / `saver_window.py`），
  QML 资产 → `ui/qml/`；`pyproject.toml` package-data、命令层与验收脚本引用同步。
- 新增回归 `test_project_nested_under_root_by_package`（根目录非空也合法、
  工程精准落 `<根目录>/<包名>/`、根目录不被写入杂文件）与 `test_resolve_target_defaults`。

### 🐛 Fixed（本轮实跑暴露）
- QML `ApplicationWindow` 需 `import QtQuick.Controls`，补入生成模板。
- JS 数组里 `"false"` 是非空字符串会被判真 → 配方库九项全显示「已装载」；改真布尔值并加回归测试。
- 孵化器内证书区只有舞台宽度 → 原横向排布挤出窗口，改 `Flow` 两列自适应，五件套全可见。
- 组合根默认断点 960/1024/1100 在孵化器内把左右槽全收起 → 舞台内壳断点设 480。
- `NovaAgent` 审批栏长文案与按钮重叠 → 左栏限宽 + `elide`。
- 离屏截图中文方框：补 `QT_QPA_FONTDIR`，并用 `QQuickWindow.grabWindow` 同步抓图（延迟回调中包装会降级为 `QWindow`）。

## [Unreleased] - 2026-11-24

### 🔄 Changed
- **会话接续流程简化为一步**：移除 `snapshot` 子命令与 `snapshot_*.md` 独立归档、移除接续模板
  （`tmpl_prompt.py`）；`prompt` 子命令改为「粘贴含快照的新会话提示词正文 → 一步存盘
  `docs/session-snapshots/prompt{yyyyMMddHH}.md` → 复制剪贴板」，快照内容由用户直接包含在提示词中。
  存量 `snapshot_*.md` 历史文件保留不动；同小时多次生成追加 `_1`、`_2` 避免覆盖。
- 优化 `prompt` 交互提示文案，明确"提示词正文已含会话快照"，剪贴板不可用时给出手动复制引导。

### 🐛 Bug Fixes
- 修复 `saver` 命令启动即抛 `ImportError: attempted relative import beyond top-level package`：
  `resources_rc.py` 位于项目根 `resources/`（包外），改用绝对导入并保留降级保护，与 `icons` 命令一致。
- 修复 `saver` 自动监听失效：`SaverController` 裸调用后被 GC 回收，导致 `signal_parse_requested`
  槽函数虽已发出信号却无人接收。控制器改为挂到窗口上持有，剪贴板→定时器→写入闭环恢复。
- 修复 `pypi` 命令版本查重目标错误：原实现写死查 `"nova-forge"` + 工具自身 `__version__`，
  导致构建 pyside-nova 1.0.0rc1 却报"0.4.10 已存在于 PyPI"。新增 `resolve_pypi_target()`
  从当前项目 pyproject.toml 解析 (包名, 版本)，按 PEP 503 规范化包名，与 dist 产物同源；
  查重时打印目标，便于确认查的是要上传的包。
- 修复 `git` / `publish` 命令在工作区重置或新环境后因 `origin` 丢失导致的
  `fatal: 'origin' does not appear to be a git repository` 崩溃。push 前新增 `ensure_origin()`
  自愈：origin 缺失时按协议偏好自动添加（默认 SSH，`NOVA_GIT_PROTOCOL=https` 可切换）；origin
  已存在则校验指向，指向其他仓库时拒绝推送并给出修正命令，绝不静默改写。
- 修复 push 失败时抛裸 Python traceback 的问题：改为捕获后输出可读诊断（分叉 / 权限 / 网络分类提示）
  并干净地以非零码退出。

### ✅ Tests
- 新增 5 项 origin 自愈单测（缺失添加 / HTTPS 切换 / 同仓库复用 / 异仓库拒绝 / SSH-HTTPS 归一化）。
- 新增 4 项 PyPI 查重目标单测（静态/动态版本解析 / PEP 503 包名规范化 / run_package 查重参数回归守护），
  全量 19 项测试通过。
- 新增 1 项 saver 控制器生命周期单测（控制器必须被窗口持有，防 GC 断开信号槽），全量 20 项通过。
- 新增 4 项 prompt 一步生成单测（CLI 仅暴露 prompt 不暴露 snapshot / 文件名格式与防覆盖 /
  端到端落盘并复制剪贴板 / 空输入忽略），并移除对旧 `_find_latest_snapshot` 的依赖；全量 24 项通过。

## [0.4.10] - 2026-11-23

### 🐛 Bug Fixes
- 修复 `pypi` 命令重复上传同名版本导致的 PyPI 400 Bad Request：上传前新增版本查重，已存在则给出明确提示并终止。
- 修复 CLI 顶层强制导入 PySide6/tkinter 导致无 GUI 依赖环境下 `--help` 崩溃的问题；GUI 命令改为按需加载。
- 修复 `tree` 命令读写编码不一致（BOM 残留）与字符串格式化缺 `f` 前缀的问题。
- 修复 `saver_window.py` 在 Python 3.10/3.11 下导入 `typing.override` 崩溃的兼容性问题。
- 修复 QRC 更新依赖不存在的外部私有包的问题，改为自包含实现并保留已有 alias。
- 修复图标清洗工具硬编码绝对路径、导入即执行副作用的问题。

### ✨ Features & Refactoring
- 新增零外部依赖冒烟测试套件（7 项），接入 CI 与发版前置卡口。
- 打包配置补充 package-data，确保 `styles.qss` 与 `example_structure.txt` 进入 wheel。

## [0.2.0c] - 2026-11-13

### ✨ Features & Refactoring
- **发版双通道重构**:正式上线 `nova-forge publish` (云端 OIDC) 与 `nova-forge build` (本地 twine) 两个独立命令。
- **底层执行器**:抽离并封装 `_runner.py`，统一 `subprocess` 调用，强制 UTF-8 并增加静默成功回显提示。
- **安全解析**:新增 `project_meta.py`，使用 `tomllib` 统一解析 `pyproject.toml`，拒绝静默兜底发版。
- **防冲突机制**:在 `publish` 流水线中注入 `git pull --rebase`，防止远程并发变更导致 Push 失败。

### 🐛 Bug Fixes
- 修复 `cli.py` 中 `publish` 缺少 `-m` 参数时导致默认提交信息被覆盖的问题。
- 修复 `tree_builder.py` 中的盲目异常捕获与未使用变量。
- 彻底清理全量 Ruff 警告（18项），代码全绿灯通过。

## [0.2.0] - 2026-11-12
### ✨ Features
- 正式加入 `tree` 指令，支持根据 `project_structure.txt` 一键生成目录树。
- 完善 `scaffolder.py` 生成的 OIDC 发版流水线模板。

## [0.1.0] - 2026-11-10
### ✨ Features
- 初始版本发布，搭建完整的 `Nova-Forge` 基础骨架。
- 引入 `init` 脚手架指令。