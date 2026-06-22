#!/usr/bin/env python3
"""
build_graph.py — 关系图数据生成器（v2.2 E. 数据可视化）

读 data/relations.yaml + 各体系 yaml 文件，
输出 dist/graph.json（节点 + 边），供前端可视化使用。

节点 = 体系中的概念（如：境界:lianqi / 法器:qing_feng_jian）
边 = relations 中的关联（type: influences / enables / blocks / parallels / requires / triggers）

用法：
  python3 scripts/build_graph.py --output dist/graph.json
  python3 scripts/build_graph.py --output dist/graph.json --filter-system realm
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# 关系类型 → 颜色映射（用于前端渲染）
RELATION_COLORS = {
    "influences": "#42a5f5",   # 蓝
    "enables": "#66bb6a",       # 绿
    "blocks": "#ef5350",        # 红
    "parallels": "#ffa726",     # 橙
    "requires": "#ab47bc",      # 紫
    "triggers": "#26a69a",      # 青
    "all_aggregate": "#78909c", # 灰
}
RELATION_TYPES = list(RELATION_COLORS.keys())

# 体系 → 颜色（节点配色）
SYSTEM_COLORS = {
    "realm": "#1976d2",
    "spirit_root": "#388e3c",
    "aether": "#00838f",
    "monster": "#5d4037",
    "yao_xiu": "#827717",
    "faction": "#c2185b",
    "spirit_stone": "#f57c00",
    "formation": "#5e35b1",
    "talisman": "#d32f2f",
    "technique": "#00796b",
    "elixir": "#689f38",
    "artifact": "#455a64",
    "secret_realm": "#6d4c41",
    "heart_demon": "#c62828",
    "tribulation": "#ff6f00",
    "divine_sense": "#0277bd",
    "spirit_weapon": "#558b2f",
    "contract": "#ad1457",
    "ascension": "#6a1b9a",
    "immortal_realm": "#4527a0",
}


def build_graph(yaml_dir, filter_system=None):
    """从 relations.yaml 构建图数据。"""
    relations_file = yaml_dir / "relations.yaml"
    if not relations_file.exists():
        return {"nodes": [], "edges": [], "metadata": {"error": "relations.yaml not found"}}

    with open(relations_file, encoding="utf-8") as f:
        relations_data = yaml.safe_load(f) or {}

    relations = relations_data.get("relations", [])

    # 收集节点
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    edge_id = 0

    # 关系类型计数
    type_counts: dict[str, int] = defaultdict(int)
    system_counts: dict[str, int] = defaultdict(int)

    for rel in relations:
        for key in ("from", "to"):
            ref = rel.get(key)
            if not ref or ":" not in ref:
                continue
            system, nid = ref.split(":", 1)
            if filter_system and system != filter_system:
                continue
            if ref not in nodes:
                nodes[ref] = {
                    "id": ref,
                    "system": system,
                    "name": nid,
                    "color": SYSTEM_COLORS.get(system, "#666666"),
                }
                system_counts[system] += 1
            break  # 一个 relation 算一个 from/to 对

        rel_type = rel.get("type", "unknown")
        if rel_type not in RELATION_TYPES:
            rel_type = "all_aggregate"

        if filter_system:
            from_sys = rel.get("from", "").split(":")[0] if rel.get("from") else ""
            to_sys = rel.get("to", "").split(":")[0] if rel.get("to") else ""
            if filter_system not in (from_sys, to_sys):
                continue

        edge_id += 1
        edges.append({
            "id": f"e{edge_id}",
            "source": rel.get("from"),
            "target": rel.get("to"),
            "type": rel_type,
            "color": RELATION_COLORS[rel_type],
            "description": rel.get("description", ""),
        })
        type_counts[rel_type] += 1

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "type_counts": dict(type_counts),
            "system_counts": dict(system_counts),
            "relation_types": RELATION_TYPES,
            "relation_colors": RELATION_COLORS,
            "system_colors": SYSTEM_COLORS,
            "filter_system": filter_system,
        },
    }


def main(argv=None):
    """CLI 入口"""
    p = argparse.ArgumentParser(description="关系图数据生成器")
    p.add_argument("--yaml-dir", type=Path, default=ROOT / "data", help="yaml 目录")
    p.add_argument("--output", type=Path, default=ROOT / "dist" / "graph.json",
                   help="输出 JSON 路径")
    p.add_argument("--filter-system", type=str, default=None,
                   help="只输出某体系（如 realm / elixir / artifact）")
    p.add_argument("--stats", action="store_true", help="只打印统计")
    args = p.parse_args(argv)

    graph = build_graph(args.yaml_dir, args.filter_system)

    if args.stats:
        meta = graph["metadata"]
        print(f"📊 关系图统计:")
        print(f"   节点数: {meta['total_nodes']}")
        print(f"   边数: {meta['total_edges']}")
        print(f"   按类型: {meta['type_counts']}")
        print(f"   按体系: {meta['system_counts']}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"💾 已生成: {args.output}")
    print(f"   节点: {graph['metadata']['total_nodes']}")
    print(f"   边: {graph['metadata']['total_edges']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())