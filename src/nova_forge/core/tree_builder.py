# -*- coding: utf-8 -*-
"""
Nova Tree 🌲
============
项目目录结构生成器 (完美防套娃、智能识别版)
根据同目录下的 `project_structure.txt`，一键生成完整的工程目录。
"""
import re
from dataclasses import dataclass, field
from pathlib import Path


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
# 🔍 结构解析器
# ==========================================
class StructureParser:
    _TREE_MARKERS = ("├── ", "└── ", "├─ ", "└─ ", "|--- ", "|-- ", "└─ ")
    _INDENT_CHARS = set("│ ├└─|")

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
# 🛠️ 项目构建器
# ==========================================
class ProjectBuilder:
    def build(self, roots: list[Node], target: Path):
        result = BuildResult()
        target = Path(target).resolve()

        current_dir_name = target.name
        nodes_to_walk = []
        real_root = target

        # ✅ 核心逻辑 1：智能防套娃
        if len(roots) == 1 and roots[0].is_dir:
            if roots[0].name == current_dir_name:
                print(f"🔍 检测到当前目录名与根节点名一致 ('{current_dir_name}')，跳过根目录创建，直接生成子结构。")
                nodes_to_walk = roots[0].children
            else:
                print(f"🔍 根节点名 ('{roots[0].name}') 与当前目录 ('{current_dir_name}') 不一致，将创建新根节点。")
                real_root = target / roots[0].name
                real_root.mkdir(parents=True, exist_ok=True)
                nodes_to_walk = roots[0].children
        else:
            print(f"🔍 检测到多个顶级节点或散落文件，直接在当前目录生成。")
            nodes_to_walk = roots

        # 1. 递归生成节点
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

            # 自动补全 __init__.py (如果是 Python 包且有子节点)
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
        except Exception as e:
            result.failed.append((path, str(e)))

    @staticmethod
    def _default_content(path: Path) -> str:
        name = path.name
        suffix = path.suffix.lower()

        if name == "__init__.py": return ""
        if suffix == ".py":
            return f'# -*- coding: utf-8 -*-\n# {path.stem}.py\n\n'
        if suffix == ".md":
            return f"# {path.stem}\n\n> 文档生成中...\n"
        if suffix == ".qrc":
            return '<RCC>\n    <qresource prefix="/">\n    </qresource>\n</RCC>\n'
        if suffix == ".qml":
            return 'import QtQuick\n\nItem {\n    width: 100\n    height: 100\n}\n'
        return ""


# ==========================================
# 🚀 主程序入口
# ==========================================
# ==========================================
# 🚀 主程序入口 (改造为可传参函数)
# ==========================================
def run_tree_builder(file_path: Path):
    # 确保传入的是 Path 对象
    file_path = Path(file_path)

    # ✅ 核心逻辑 2：空文件与缺失检测
    if not file_path.exists():
        print(f"❌ 错误: 找不到 [{file_path.name}] 文件！")
        print("💡 请先创建该文件并填入目录树。")
        return

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        print(f"❌ 错误: [{file_path.name}] 文件内容为空！")
        print("💡 请写入类似以下的格式：\n项目名/\n├── src/\n│   └── main.py")
        return

    print("🔥 启动 Nova Tree 终极结构生成器...\n")

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
