# Changelog

所有版本变更记录，遵循 [Semantic Versioning](https://semver.org/) 规范。

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