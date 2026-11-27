# src/nova_forge/tools/clean_material_symbols.py
# 创建时间：星期二 2026-11-24 21:39
"""清洗 Material Symbols SVG 并生成预览索引（仅标准库依赖）。"""

import argparse
import json
import re
from pathlib import Path

# 清洗规则：删除写死的 width / height / fill 属性，让 QML 可以上色、缩放
CLEAN_ATTR = re.compile(r'\s*(width|height|fill)="[^"]*"')
WEIGHTS = [100, 200, 300, 400, 500, 600, 700]
STYLES = ["outlined", "rounded", "sharp"]


def default_project_root() -> Path:
    """tools -> nova_forge -> src -> 项目根目录。"""
    return Path(__file__).resolve().parents[3]


def clean_symbols(root: Path) -> int:
    """清洗 SVG 并写入 symbol_index.json，返回处理的文件数。"""
    src_base = root / "node_modules" / "@material-symbols"
    dst = (
        root
        / "pyside-nova"
        / "src"
        / "pyside_nova"
        / "qml"
        / "Nova"
        / "assets"
        / "symbols"
    )

    if not src_base.is_dir():
        print(f"⚠️ 跳过：未找到 {src_base}，请先执行 npm install。")
        return 0

    index: dict[int, dict[str, dict[str, list[str]]]] = {}
    total = 0

    for weight in WEIGHTS:
        pkg_dir = src_base / f"svg-{weight}"
        print(f"\n👉 正在处理 weight={weight} | 源目录：{pkg_dir}")
        if not pkg_dir.is_dir():
            print(f"⚠️ 跳过：{pkg_dir} 不存在")
            continue

        index[weight] = {}
        for style in STYLES:
            src_dir = pkg_dir / style
            index[weight][style] = {"0": [], "1": []}
            if not src_dir.is_dir():
                print(f"   ⚠️ 跳过：{src_dir} 不存在")
                continue

            dst0 = dst / str(weight) / style / "0"
            dst1 = dst / str(weight) / style / "1"
            dst0.mkdir(parents=True, exist_ok=True)
            dst1.mkdir(parents=True, exist_ok=True)

            svg_list = sorted(src_dir.glob("*.svg"))
            print(f"   -- {style} 一共找到 {len(svg_list)} 个 SVG")
            for svg in svg_list:
                clean_svg = CLEAN_ATTR.sub("", svg.read_text(encoding="utf-8"))
                stem = svg.stem
                if stem.endswith("-fill"):
                    icon_name = stem.removesuffix("-fill")
                    out = dst1 / f"{icon_name}.svg"
                    index[weight][style]["1"].append(icon_name)
                else:
                    icon_name = stem
                    out = dst0 / f"{icon_name}.svg"
                    index[weight][style]["0"].append(icon_name)

                out.write_text(clean_svg, encoding="utf-8")
                total += 1

    dst.mkdir(parents=True, exist_ok=True)
    index_file = dst / "symbol_index.json"
    index_file.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✅ 全部处理完毕！共 {total} 个 SVG，索引文件：{index_file}")
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="清洗 Material Symbols SVG 资源")
    parser.add_argument(
        "--root",
        type=Path,
        default=default_project_root(),
        help="项目根目录（默认按脚本位置自动推断）",
    )
    args = parser.parse_args(argv)
    clean_symbols(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
