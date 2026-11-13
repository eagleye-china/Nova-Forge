# src/nova_forge/core/tree_builder.py
"""
Nova Tree 🌲 (双向同步终极版)
============================
1. 根据 `project_structure.txt` 创建缺失的目录。
2. 自动扫描当前真实目录，如果发现磁盘上的文件比 txt 新/多，则反向修正 txt 文件。
"""
import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


# ==========================================
# 📦 数据模型
# ==========================================
@dataclass(slots=True)
class Node:
    name: str
    is_dir: bool
    level: int = 0
    children: list["Node"] = field(default_factory=list)

    def add_child(self, child: "Node") -> None:
        self.children.append(child)


@dataclass(slots=True)
class BuildResult:
    created_dirs: list[Path] = field(default_factory=list)
    created_files: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"📁 新建目录: {len(self.created_dirs)} | "
            f"📄 新建文件: {len(self.created_files)} | "
            f"⏭️ 跳过已存在: {len(self.skipped)} | "
            f"❌ 失败: {len(self.failed)}"
        )


# ==========================================
# 🔍 结构解析器 (TXT -> Node)
# ==========================================
class StructureParser:
    _TREE_MARKERS = ("├── ", "└── ", "├─ ", "└─ ", "|--- ", "|-- ", "└─ ")
    _INDENT_CHARS: ClassVar[set[str]] = set("│ ├└─|")

    def parse(self, text: str) -> list[Node]:
        roots: list[Node] = []
        stack: list[tuple[int, Node]] = []

        for raw in text.splitlines():
            parsed = self._parse_line(raw)
            if parsed is None:
                continue

            level, name, is_dir = parsed
            node = Node(name=name, is_dir=is_dir, level=level)

            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                stack[-1][1].add_child(node)
            else:
                roots.append(node)

            stack.append((level, node))

        return roots

    def _parse_line(self, line: str) -> tuple[int, str, bool] | None:
        line = line.rstrip()
        if not line.strip() or all(c in "│ ├└─|" for c in line.strip()):
            return None
        if "|" in line and not any(m in line for m in self._TREE_MARKERS):
            return None
        if line.lstrip().startswith(("```", "---", "===")):
            return None

        for marker in self._TREE_MARKERS:
            idx = line.find(marker)
            if idx >= 0:
                prefix = line[:idx]
                if all(ch in self._INDENT_CHARS for ch in prefix):
                    level = idx // 4 + 1
                    name = line[idx + len(marker):]
                    clean_name = self._clean_name(name)
                    if clean_name:
                        return level, clean_name, self._is_dir(name)

        if line[0].isspace() and not line.lstrip().startswith(("def ", "class ", "import ", "from ", "@")):
            stripped = line.lstrip()
            level = (len(line) - len(stripped)) // 4
            clean_name = self._clean_name(stripped)
            if clean_name:
                return level, clean_name, self._is_dir(stripped)

        clean_name = self._clean_name(line)
        if clean_name:
            return 0, clean_name, self._is_dir(line)

        return None

    @staticmethod
    def _clean_name(name: str) -> str:
        name = name.split("#")[0].strip()
        name = name.rstrip("/\\:").strip()
        name = re.sub(r'[<>:"|?*]', '_', name)
        return name.strip()

    @staticmethod
    def _is_dir(name: str) -> bool:
        name = name.rstrip()
        if name.endswith(("/", "\\")):
            return True
        last = name.split("/")[-1].split("\\")[-1]
        return "." not in last


# ==========================================
# 🌲 目录提取器 (Disk -> TXT)
# (从 UI 中完美剥离出来的纯 Python 核心)
# ==========================================
class TreeGenerator:
    def __init__(self, ignore_dirs=None, ignore_files=None):
        if ignore_dirs is None:
            ignore_dirs = {
                ".git", "__pycache__", "venv", ".venv",
                "build", "dist", ".pytest_cache", ".mypy_cache",
                ".idea", ".vscode"
            }
        if ignore_files is None:
            ignore_files = {".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.bak"}
        self.ignore_dirs = set(ignore_dirs)
        self.ignore_files = set(ignore_files)
        self.image_extensions = {"*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico", "*.webp"}

    def _is_ignored_file(self, name: str) -> bool:
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.ignore_files)

    def generate_tree_text(self, root_path: Path, show_files: bool = True, show_hidden: bool = False,
                           ignore_images: bool = True) -> str:
        if not root_path.exists() or not root_path.is_dir():
            return "❌ 无效的项目目录！"

        lines = [root_path.name + "/"]

        current_ignore = self.ignore_files.copy()
        if ignore_images:
            current_ignore.update(self.image_extensions)

        self._walk(root_path, "", lines, show_files, show_hidden, current_ignore)
        return "\n".join(lines)

    def _walk(self, current: Path, prefix: str, lines: list, show_files: bool, show_hidden: bool, ignore_rules: set):
        try:
            entries = list(current.iterdir())
        except PermissionError:
            return

        entries.sort(key=lambda _p: (not _p.is_dir(), _p.name.lower()))
        filtered = []

        for p in entries:
            name = p.name
            if not show_hidden and name.startswith("."):
                continue
            if p.is_dir() and name in self.ignore_dirs:
                continue
            if p.is_file():
                if any(fnmatch.fnmatch(name, pattern) for pattern in ignore_rules):
                    continue
                if not show_files:
                    continue
            filtered.append(p)

        count = len(filtered)
        for idx, path in enumerate(filtered):
            is_last = (idx == count - 1)
            connector = "└── " if is_last else "├── "
            name = path.name
            if path.is_dir():
                name += "/"
            lines.append(prefix + connector + name)

            if path.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._walk(path, new_prefix, lines, show_files, show_hidden, ignore_rules)


# ==========================================
# 🛠️ 项目构建器 (Node -> Disk)
# ==========================================
class ProjectBuilder:
    def build(self, roots: list[Node], target: Path):
        result = BuildResult()
        target = Path(target).resolve()

        current_dir_name = target.name
        real_root = target

        # ✅ 智能防套娃
        if len(roots) == 1 and roots[0].is_dir:
            if roots[0].name == current_dir_name:
                print("🔍 检测到根节点名与当前目录一致，跳过根目录创建。")
                nodes_to_walk = roots[0].children
            else:
                print("🔍 根节点名不一致，将创建新根节点: {roots[0].name}")
                real_root = target / roots[0].name
                real_root.mkdir(parents=True, exist_ok=True)
                nodes_to_walk = roots[0].children
        else:
            print("🔍 检测到多个顶级节点或散落文件，直接生成。")
            nodes_to_walk = roots

        for node in nodes_to_walk:
            self._create_node(node, real_root, result)

        return result

    def _create_node(self, node: Node, parent: Path, result: BuildResult):
        path = parent / node.name

        if node.is_dir:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                result.created_dirs.append(path)
            else:
                result.skipped.append(path)

            # 自动补全 __init__.py
            if node.children and not any(c.name == "__init__.py" for c in node.children):
                init_file = path / "__init__.py"
                self._write_file(init_file, "", result)

            for child in node.children:
                self._create_node(child, path, result)
        else:
            self._write_file(path, "", result)

    def _write_file(self, path: Path, content: str, result: BuildResult):
        if path.exists():
            result.skipped.append(path)
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        if not content:
            content = self._default_content(path)

        try:
            path.write_text(content, encoding="utf-8")
            result.created_files.append(path)
        except Exception as e:# noqa: BLE001
            result.failed.append((path, str(e)))

    @staticmethod
    def _default_content(path: Path) -> str:
        name = path.name
        suffix = path.suffix.lower()
        if name == "__init__.py": return ""
        if suffix == ".py": return f'# -*- coding: utf-8 -*-\n# {path.stem}.py\n\n'
        if suffix == ".md": return f"# {path.stem}\n\n> 文档生成中...\n"
        if suffix == ".qrc": return '<RCC>\n    <qresource prefix="/">\n    </qresource>\n</RCC>\n'
        if suffix == ".qml": return 'import QtQuick\n\nItem {\n    width: 100\n    height: 100\n}\n'
        return ""


# ==========================================
# 🚀 主程序入口 (安全解耦版)
# ==========================================
def run_tree_builder(file_path: Path, sync_mode: bool = False):
    file_path = Path(file_path)
    generator = TreeGenerator()

    # 【场景 1】反向同步模式 (仅当用户显式要求 --sync 时)
    if sync_mode:
        print("🔄 启动反向同步：扫描当前磁盘结构，覆盖 TXT 文件...")
        text = generator.generate_tree_text(Path.cwd(), ignore_images=True)
        file_path.write_text(text, encoding="utf-8")
        print(f"✅ 磁盘结构已成功写入 [{file_path.name}]！")
        return

    # 【场景 2】正向生成模式 (默认行为，安全、不碰 TXT)
    if not file_path.exists() or not file_path.read_text(encoding="utf-8").strip():
        print(f"❌ 错误: [{file_path.name}] 不存在或内容为空！")
        print("💡 请先填入目录树，或使用 `nova-forge tree --sync` 从当前磁盘反向生成。")
        return

    content = file_path.read_text(encoding="utf-8").strip()
    print("🔥 启动正向生成：根据 TXT 创建缺失的目录和文件...\n")

    parser = StructureParser()
    roots = parser.parse(content)

    if not roots:
        print("❌ 错误: 未能解析出有效目录，请检查 txt 语法格式。")
        return

    builder = ProjectBuilder()
    result = builder.build(roots, target=Path.cwd())

    print("\n" + "=" * 40)
    print("🎉 构建执行完毕！")
    print(result.summary())
    if result.failed:
        print("\n❌ 失败列表:")
        for path, err in result.failed:
            print(f"  - {path}: {err}")
    print("=" * 40)
    print("\n💡 提示: 若你想把当前磁盘的最新结构反向保存到 TXT，请运行:")
    print("    nova-forge tree --sync")
