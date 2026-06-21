#!/usr/bin/env python3
"""
修仙体系知识库导出工具

将 data/*.yaml 导出为：
  1. dist/xiuxian.json         整本知识库（JSON）
  2. dist/<name>.csv           每个体系一张 CSV
  3. dist/HANDBOOK.md          单文件 markdown 手册

使用：
  python3 scripts/export.py            # 导出全部到 dist/
  python3 scripts/export.py --format json
  python3 scripts/export.py --format csv
  python3 scripts/export.py --format md
  python3 scripts/export.py --output /tmp/out
"""
import argparse
import csv
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少依赖 pyyaml，请安装：pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# 体系元信息：filename -> (中文名, 简短说明)
SYSTEMS = {
    "realms":        ("境界体系", "9 大境界 + 突破规则"),
    "spirit_roots":  ("灵根体系", "5 品级 + 8 属性 + 3 变异"),
    "aether":        ("天地灵气", "4 浓度 + 5 灵脉 + 3 界面"),
    "elixirs":       ("丹药体系", "6 品级 + 9 丹药"),
    "techniques":    ("功法体系", "4 品级 + 3 功法"),
    "artifacts":     ("法器体系", "5 品级 + 4 法器"),
    "factions":      ("势力体系", "5 规模 + 5 形态 + 3 范例"),
    "spirit_stones": ("灵石体系", "5 品级 + 3 属性 + 4 来源"),
    "monsters":      ("妖兽体系", "5 品级 + 灵兽 + 契约"),
    "formations":    ("阵法体系", "6 类别 + 4 等级 + 3 例"),
    "talismans":     ("符箓体系", "4 品级 + 6 类别 + 3 例"),
    "relations":     ("跨体系关联", "关系图数据"),
}


# ────────────────────────────────────────────────────────
# 数据加载
# ────────────────────────────────────────────────────────
def load_all():
    """加载所有 yaml 为 dict，key 为 yaml 名（不含扩展名）"""
    out = {}
    for name in SYSTEMS:
        path = DATA_DIR / f"{name}.yaml"
        if not path.exists():
            print(f"⚠️  跳过 {name}.yaml（不存在）", file=sys.stderr)
            continue
        with open(path, encoding="utf-8") as fp:
            out[name] = yaml.safe_load(fp) or {}
    return out


# ────────────────────────────────────────────────────────
# 1. JSON 导出
# ────────────────────────────────────────────────────────
def export_json(data, out_dir):
    out_path = out_dir / "xiuxian.json"
    payload = {
        "_meta": {
            "version": "1.0.0",
            "source": "https://github.com/shushuzn/xiuxian-structure",
            "description": "修仙体系知识库（基于《凡人修仙传》参考的通用设定）",
            "systems": {
                k: {"name": v[0], "description": v[1]}
                for k, v in SYSTEMS.items()
            },
        },
        "data": data,
    }
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2, sort_keys=False)
    return out_path


# ────────────────────────────────────────────────────────
# 2. CSV 导出
# ────────────────────────────────────────────────────────
def _flatten(obj, prefix=""):
    """把嵌套 dict / list 拍平成 {col: value} 字典"""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}{k}."))
    elif isinstance(obj, list):
        if all(isinstance(x, (str, int, float, bool)) for x in obj):
            out[prefix[:-1]] = ", ".join(str(x) for x in obj)
        else:
            out[prefix[:-1]] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix[:-1]] = obj
    return out


def export_csv(data, out_dir):
    """每个 yaml 中每个 list-of-dict 段生成一个 CSV"""
    out_files = []
    for name, payload in data.items():
        if not isinstance(payload, dict):
            continue
        for section, content in payload.items():
            if not isinstance(content, list) or not content:
                continue
            # 必须是 list of dict
            if not all(isinstance(x, dict) for x in content):
                continue
            rows = [_flatten(item) for item in content]
            if not rows:
                continue
            # 字段顺序：所有行 union
            fieldnames = []
            seen = set()
            for r in rows:
                for k in r.keys():
                    if k not in seen:
                        seen.add(k)
                        fieldnames.append(k)
            out_path = out_dir / f"{name}__{section}.csv"
            with open(out_path, "w", encoding="utf-8", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            out_files.append(out_path)
    return out_files


# ────────────────────────────────────────────────────────
# 3. Markdown 手册导出
# ────────────────────────────────────────────────────────
def export_handbook(data, out_dir):
    """把所有 yaml 拼成一本单文件 MD 手册"""
    # 章节名英→中映射（让手册更可读）
    SECTION_LABELS = {
        "realms":            "境界",
        "spirit_roots":      "灵根品级",
        "attributes":        "属性",
        "concentrations":    "灵气浓度",
        "veins":             "灵脉等级",
        "attribute_modifiers":"灵气属性",
        "elixirs":           "丹药",
        "tiers":             "品级",
        "styles":            "风格",
        "inheritances":      "传承",
        "techniques":        "功法",
        "recognitions":      "灵识认证",
        "artifacts":         "法器",
        "scales":            "势力规模",
        "forms":             "势力形态",
        "disciple_levels":   "弟子等级",
        "examples":          "示例",
        "purposes":          "用途",
        "sources":           "来源",
        "grades":            "品级",
        "intelligence":      "灵智",
        "contracts":         "契约",
        "spirit_beast_tiers":"灵兽品级",
        "categories":        "类别",
        "deploy_types":      "布阵方式",
        "components":        "构成要素",
        "production":        "制作方式",
        "relations":         "关联",
    }

    lines = [
        "# 修仙体系手册",
        "",
        "> 自动生成自 [xiuxian-structure](https://github.com/shushuzn/xiuxian-structure) 知识库",
        "> 本手册为「设定速查」用，完整文档请参见 GitHub 仓库。",
        "",
        "## 目录",
        "",
    ]
    for name, (zh, desc) in SYSTEMS.items():
        lines.append(f"- [{zh}](#{name})")
    lines.append("")

    for name, (zh, desc) in SYSTEMS.items():
        if name not in data:
            continue
        payload = data[name]
        lines.append(f"## {zh}")
        lines.append("")
        lines.append(f"_{desc}_")
        lines.append("")
        if not isinstance(payload, dict):
            continue
        for section, content in payload.items():
            if section == "references":
                continue
            label = SECTION_LABELS.get(section, section)
            lines.append(f"### {label}")
            lines.append("")
            if isinstance(content, list):
                if not content:
                    lines.append("（空）")
                else:
                    for item in content:
                        if isinstance(item, dict):
                            lines.append(format_dict(item))
                        else:
                            lines.append(f"- {item}")
            elif isinstance(content, dict):
                lines.append(format_dict(content))
            else:
                lines.append(f"`{content}`")
            lines.append("")

    out_path = out_dir / "HANDBOOK.md"
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))
    return out_path


def format_dict(d, indent=0):
    """把 dict 格式化为 markdown 列表"""
    lines = []
    for k, v in d.items():
        prefix = "  " * indent
        if isinstance(v, dict):
            lines.append(f"{prefix}- **{k}**：")
            lines.append(format_dict(v, indent + 1))
        elif isinstance(v, list):
            if all(isinstance(x, (str, int, float, bool)) for x in v):
                lines.append(f"{prefix}- **{k}**：{', '.join(str(x) for x in v)}")
            else:
                lines.append(f"{prefix}- **{k}**：")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(format_dict(item, indent + 1))
                    else:
                        lines.append(f"{prefix}  - {item}")
        else:
            lines.append(f"{prefix}- **{k}**：{v}")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────
# main
# ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="导出修仙体系知识库到 JSON / CSV / Markdown"
    )
    parser.add_argument(
        "--format",
        choices=["all", "json", "csv", "md"],
        default="all",
        help="导出格式（默认 all）",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "dist"),
        help="输出目录（默认 dist/）",
    )
    args = parser.parse_args()

    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 加载 yaml 数据...")
    data = load_all()
    print(f"   加载了 {len(data)}/{len(SYSTEMS)} 个体系")

    results = []
    fmt = args.format

    def _rel(p):
        try:
            return p.relative_to(ROOT)
        except ValueError:
            return p  # 输出目录在 ROOT 之外，原样显示

    if fmt in ("all", "json"):
        p = export_json(data, out_dir)
        results.append(("JSON", p))
        print(f"✅ JSON     → {_rel(p)}")

    if fmt in ("all", "csv"):
        paths = export_csv(data, out_dir)
        for p in paths:
            results.append(("CSV", p))
        print(f"✅ CSV      → {len(paths)} 个文件于 {_rel(paths[0]).parent}/")

    if fmt in ("all", "md"):
        p = export_handbook(data, out_dir)
        results.append(("MD", p))
        print(f"✅ Markdown → {_rel(p)}")

    print(f"\n🎉 导出完成：{len(results)} 个产物")
    return 0


if __name__ == "__main__":
    sys.exit(main())
