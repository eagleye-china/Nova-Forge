# src/nova_forge/prescript/catalog.py
# 创建时间：星期四 2026-11-26 15:20
"""九类应用配方目录：生成器、CLI 列表、README、manifest 共用同一事实源。

设计约束（对齐 pyside-nova 组合宪法 1.0.0）：
- 每个配方只声明「业务语义」，不复制壳的布局职责；壳仍是 Prescient Layout Shell。
- 配方代号 P1~P9 与 pyside-nova Gallery 的 R1~R5 区分：R 是孵化器内置示范配方，
  P 是 prescript 可生成的应用品类，编号稳定、不复用。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Kind:
    """一类可孵化应用的全部规格（同一份数据驱动 QML / README / manifest / 自检）。"""

    code: str                    # CLI 标识（stable）
    shell: str                   # 对应组合根 QML 类型
    zh: str                      # 中文应用名
    en: str                      # 英文应用名
    recipe: str                  # 配方代号 P1~P9
    tagline: str                 # 一句话定位（UI 副标题）
    pitch: str                   # README 开场：这类应用解决什么问题
    role: str                    # 适用场景（README / manifest）
    hue: int                     # 组合根专属色相（文档口径，非运行时写入）
    size: tuple[int, int]        # 默认窗口
    minimum: tuple[int, int]     # 最小窗口
    metrics: list[tuple[str, str]] = field(default_factory=list)      # 性能承诺（右栏展示）
    gates: list[tuple[str, str]] = field(default_factory=list)        # 门禁（证书页展示）
    deliverables: list[tuple[str, str]] = field(default_factory=list)  # 交付五件套
    focus: list[str] = field(default_factory=list)                     # 舞台能力要点（README）

    @property
    def icon(self) -> str:
        """应用图标文件名 —— 单一事实源：``code`` → ``app-<code>.svg``。

        图标实体由 ``scripts/gen_app_icons.py`` 依本表的 ``hue`` 生成，落在
        ``nova_forge/resources/icons/``，并由 ``resources.qrc`` 以同名别名注册。
        本处不另立色值/文件名台账，避免账实不符。
        """
        return f"app-{self.code}.svg"


# 第 10 个组件：孵化器工作台自身（不属九配方，但同样是专属主题组合根，色相 283°）
INCUBATOR_SHELL = "NovaIncubator"
INCUBATOR_HUE = 283
INCUBATOR_ICON = "app-incubator.svg"

# 第 11 个组件：NovaAIReport（T24 加入的第 21 组合根，同样不属九配方）。
# 专属色相 258° = 基准 233° + 偏移 0.0694×360 ≈ 25°，与组件私有令牌
# ``_themeHue: (NovaTheme.primary.hsvHue + 0.0694 + 1) % 1`` 账实相符（仪表钢蓝）。
AI_REPORT_SHELL = "NovaAIReport"
AI_REPORT_CODE = "aireport"
AI_REPORT_HUE = 258
AI_REPORT_ICON = "app-aireport.svg"
AI_REPORT_ZH = "智能报表工作台"


KINDS: tuple[Kind, ...] = (
    Kind(
        code="agent",
        shell="NovaAgent",
        zh="智能体任务台",
        en="Autonomous Task Console",
        recipe="P1",
        tagline="任务准入 · 计划可审 · 结果可验",
        pitch="把「让智能体自己干」变成可治理的生产力：任务先准入、计划先审阅、"
              "执行留轨迹、结果由独立验证器复核，人工只在闸门处出现。",
        role="长链路自主执行 / 需要人工闸门的自动化",
        hue=233,
        size=(1440, 900),
        minimum=(1040, 660),
        metrics=[("任务领取", "p95 120 ms"), ("执行流刷新", "60 fps"),
                 ("轨迹留存", "全量可回放")],
        gates=[("任务准入", "八项准入校验先于执行"),
               ("计划审阅", "计划变更必须重新审阅"),
               ("独立验证", "验证器不与执行器共享上下文")],
        deliverables=[("运行包", "agent_console · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + task_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["任务队列与准入状态机", "计划步骤可展开审阅", "执行轨迹逐步留痕",
               "右侧独立验证清单", "底部人工审批闸门"],
    ),
    Kind(
        code="copilot",
        shell="NovaCopilot",
        zh="协作副驾",
        en="Inline Copilot",
        recipe="P2",
        tagline="建议在先 · 落盘在闸 · 依据可追",
        pitch="单职能嵌入式协作：把建议、内联提示、正文与落盘闸门放在同一视线内，"
              "任何写操作都必须经过 gate 显式确认，grounding 依据随行可查。",
        role="代码 / 文档 / 表单的嵌入式写作与改写",
        hue=266,
        size=(1360, 860),
        minimum=(980, 640),
        metrics=[("建议生成", "p95 240 ms"), ("内联补全", "< 40 ms 键入延迟"),
                 ("落盘确认", "零隐式写入")],
        gates=[("建议分级", "强建议 / 弱建议分栏呈现"),
               ("内联不抢焦", "补全不夺输入焦点"),
               ("落盘闸门", "写操作前必须人工确认")],
        deliverables=[("运行包", "inline_copilot · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + suggestion_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["建议列表分级与采纳", "内联提示条（不抢焦）", "正文编辑区行级留痕",
               "落盘闸门与依据清单"],
    ),
    Kind(
        code="de",
        shell="NovaDE",
        zh="数字员工队伍",
        en="Digital Employee Fleet",
        recipe="P3",
        tagline="角色分工 · 队列编排 · SLA 兜底",
        pitch="部门级数字员工流水线：以角色卡定义职责边界，以队列编排并行工作，"
              "以 SLA 面板守住响应承诺，跨角色交接必须显式发起。",
        role="部门级流程自动化 / 多角色协作",
        hue=205,
        size=(1440, 900),
        minimum=(1040, 660),
        metrics=[("队列吞吐", "≥ 120 单/分钟"), ("SLA 计时", "1 s 粒度"),
                 ("交接留痕", "100% 可追溯")],
        gates=[("角色四要件", "职责 / 权限 / 边界 / 交接齐备"),
               ("影子模式", "上线前影子运行 ≥ 48 h"),
               ("SLA 兜底", "越界自动升级人工")],
        deliverables=[("运行包", "de_fleet · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + employee_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["角色卡与职责边界", "队列编排与优先级", "工作记录时间线",
               "SLA 指标与越界升级", "跨角色交接"],
    ),
    Kind(
        code="orbit",
        shell="NovaOrbit",
        zh="意图轨道工作台",
        en="Intent Orbit",
        recipe="P4",
        tagline="意图入轨 · 实体路由 · 画布收敛",
        pitch="把散落的意图收进轨道：一句话进入意图区，由路由器绑定实体，"
              "在画布上收敛成可执行的轨道节点，全程可见、可改道、可回退。",
        role="复杂工作台 / 多实体协同 / 意图驱动",
        hue=243,
        size=(1520, 940),
        minimum=(1100, 700),
        metrics=[("意图入轨", "p95 160 ms"), ("画布拖拽", "60 fps"),
                 ("路由命中", "≥ 96% 首轮")],
        gates=[("实体绑定", "未绑定实体不入轨"),
               ("改道留痕", "每次改道生成新版本"),
               ("回退可用", "任一节点可回退到上一轨")],
        deliverables=[("运行包", "intent_orbit · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + orbit_event_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["轨道模式切换", "意图输入与实体建议", "轨道节点画布",
               "右图缩略与命中率", "改道与回退"],
    ),
    Kind(
        code="desktop",
        shell="NovaDesktop",
        zh="企业桌面",
        en="Enterprise Desktop",
        recipe="P5",
        tagline="菜单成树 · 页签成组 · 状态可读",
        pitch="企业级桌面外壳：左侧菜单树承载信息架构，顶部工具栏承载高频动作，"
              "页面区承载业务，底部状态栏承载运行态，四者边界清晰不互相争位。",
        role="后台管理系统 / 多页签业务桌面",
        hue=223,
        size=(1440, 900),
        minimum=(1024, 640),
        metrics=[("页面切换", "< 80 ms"), ("首屏渲染", "< 600 ms"),
                 ("状态刷新", "1 s 心跳")],
        gates=[("信息架构", "菜单层级不超过 3 级"),
               ("动作可达", "高频动作不进二级菜单"),
               ("状态常显", "连接 / 同步 / 版本三态常显")],
        deliverables=[("运行包", "enterprise_desktop · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + page_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["菜单树与分组", "工具栏高频动作", "仪表盘卡片页",
               "多页签切换", "运行状态栏"],
    ),
    Kind(
        code="chat",
        shell="NovaChat",
        zh="AI 对话工作台",
        en="Conversation Workbench",
        recipe="P6",
        tagline="会话可检索 · 上下文可见 · 输入不丢",
        pitch="对话不是聊天框：左侧会话可检索、中间上下文可追溯、右侧详情可核验，"
              "输入草稿零丢失，长会话仍保持 60 fps。",
        role="客服 / 知识助手 / 内部问答",
        hue=216,
        size=(1280, 800),
        minimum=(860, 600),
        metrics=[("消息渲染", "60 fps"), ("会话检索", "p95 90 ms"),
                 ("草稿留存", "切换会话零丢失")],
        gates=[("上下文可见", "每条回复可查引用来源"),
               ("草稿保护", "切会话不丢输入"),
               ("长列表稳态", "1 万条消息不塌陷")],
        deliverables=[("运行包", "chat_workbench · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + conversation_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["会话检索与切换", "消息流与引用", "composer 草稿保护",
               "右侧上下文详情"],
    ),
    Kind(
        code="mobile",
        shell="NovaMobile",
        zh="移动触控应用",
        en="Touch-First Mobile",
        recipe="P7",
        tagline="拇指可达 · 安全区避让 · 触控优先",
        pitch="为真实手持场景做的移动壳：底部导航落在拇指热区，安全区避让刘海与手势条，"
              "触控目标不小于 44 px，窄屏下自动收起侧栏。",
        role="现场作业 / 移动审批 / 巡检",
        hue=193,
        size=(430, 920),
        minimum=(360, 640),
        metrics=[("触控响应", "< 50 ms"), ("滚动", "60 fps"),
                 ("安全区", "刘海 / 手势条双避让")],
        gates=[("触控目标", "≥ 44 × 44 px"),
               ("窄屏收敛", "< 1100 px 收起侧栏"),
               ("安全区", "safeTop / safeBottom 生效")],
        deliverables=[("运行包", "touch_mobile · 移动构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + session_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["头部与返回", "触控卡片列表", "底部四页签",
               "窄屏自动收起侧栏"],
    ),
    Kind(
        code="flex",
        shell="NovaFlexLayout",
        zh="工业大屏",
        en="Industrial Big Screen",
        recipe="P8",
        tagline="产线一屏尽览 · 1~4 栏自由拼 · 断点零溢出",
        pitch="把产线、设备、能耗、质检、在途运单收进同一块工业大屏：1~4 栏随屏宽自动重排，"
              "关键指标一眼可见、异常一眼可辨；从车间 32 寸屏到指挥中心 4K 拼接墙，"
              "都不出现横向滚动与挤压变形。",
        role="车间产线 / 设备监控 / 指挥中心大屏",
        hue=176,
        size=(1440, 900),
        minimum=(720, 560),
        metrics=[("大屏重排", "< 120 ms"), ("指标刷新", "1 s 心跳"),
                 ("极端宽度", "320 px 不溢出")],
        gates=[("断点覆盖", "320 / 768 / 1024 / 1440 四档"),
               ("零横向滚动", "任意宽度无溢出"),
               ("密度一致", "间距随档位统一缩放")],
        deliverables=[("运行包", "industrial_screen · 大屏构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + panel_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["产线指标卡片栅格", "1~4 栏断点重排", "设备状态与告警",
               "能耗 / 质检实时块", "底部运行态"],
    ),
    Kind(
        code="wizard",
        shell="NovaSetupWizard",
        zh="部署向导",
        en="Deployment Wizard",
        recipe="P9",
        tagline="步骤可控 · 上一步不丢 · 校验前置",
        pitch="把部署这件高风险动作拆成可回退的步骤：每一步先校验后放行，"
              "上一步不丢已填内容，最终一步汇总所有选择再确认。",
        role="安装部署 / 初始化配置 / 合规向导",
        hue=168,
        size=(1080, 760),
        minimum=(840, 600),
        metrics=[("步骤切换", "< 60 ms"), ("校验", "单步 < 200 ms"),
                 ("回退", "内容零丢失")],
        gates=[("校验前置", "未过校验不放行下一步"),
               ("回退保真", "上一步内容原样保留"),
               ("终审汇总", "最后一步展示全部选择")],
        deliverables=[("运行包", "deploy_wizard · 桌面构建产物"),
                      ("治理清单", "governance.manifest.yaml"),
                      ("审计接入", "OTel span + step_id 映射"),
                      ("封版证书", "incubation.certificate.yaml"),
                      ("升级路径", "upgrade.path.yaml · semver")],
        focus=["五步流程条", "分步表单", "上一步 / 下一步闸门",
               "终审汇总与确认"],
    ),
)

KIND_CODES: tuple[str, ...] = tuple(k.code for k in KINDS)
_BY_CODE = {k.code: k for k in KINDS}

# 十一个组件的图标文件名（九配方 + 孵化器 + 智能报表），供生成器 / qrc / 测试共用；单一事实源
APP_ICON_FILES: tuple[str, ...] = (
    *(k.icon for k in KINDS), INCUBATOR_ICON, AI_REPORT_ICON
)
APP_ICON_QRC: tuple[str, ...] = tuple(f"qrc:/icons/{name}" for name in APP_ICON_FILES)


def icon_for(code: str) -> str:
    """按组件代号取应用图标 qrc 路径；``incubator`` / ``aireport`` 落附加两枚，未知 code 抛 ValueError。"""
    if code == "incubator":
        return f"qrc:/icons/{INCUBATOR_ICON}"
    if code == AI_REPORT_CODE:
        return f"qrc:/icons/{AI_REPORT_ICON}"
    return f"qrc:/icons/{get_kind(code).icon}"


def get_kind(code: str) -> Kind:
    """按 code 取配方；未知 code 抛 ValueError（CLI 统一捕获提示）。"""
    try:
        return _BY_CODE[code.strip().lower()]
    except KeyError as exc:
        raise ValueError(
            f"未知配方 {code!r}；可选：{', '.join(KIND_CODES)}"
        ) from exc
