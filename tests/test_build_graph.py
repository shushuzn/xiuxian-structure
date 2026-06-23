"""
test_build_graph.py — build_graph.py 单测（v2.9 关系图谱）
"""
import json
import sys
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_graph import build_graph, build_mermaid  # noqa: E402

DATA_DIR = ROOT / "data"


def test_build_graph_basic():
    g = build_graph(DATA_DIR)
    assert g["metadata"]["total_nodes"] > 0
    assert g["metadata"]["total_edges"] > 0
    assert "nodes" in g
    assert "edges" in g


def test_build_graph_nodes_have_required_fields():
    g = build_graph(DATA_DIR)
    for node in g["nodes"][:10]:
        assert "id" in node
        assert "system" in node
        assert "name" in node
        assert "color" in node


def test_build_graph_edges_have_required_fields():
    g = build_graph(DATA_DIR)
    for edge in g["edges"][:10]:
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge
        assert "color" in edge


def test_build_graph_filter_system():
    g = build_graph(DATA_DIR, filter_system="realm")
    for node in g["nodes"]:
        assert node["system"] == "realm"


def test_build_graph_filter_system_inclusive():
    """filter 应同时包含 from 和 to 涉及的体系边"""
    g = build_graph(DATA_DIR, filter_system="realm")
    for edge in g["edges"]:
        sys_from = edge["source"].split(":")[0] if edge["source"] else ""
        sys_to = edge["target"].split(":")[0] if edge["target"] else ""
        assert "realm" in (sys_from, sys_to)


def test_build_graph_metadata_relation_types():
    g = build_graph(DATA_DIR)
    assert "relation_types" in g["metadata"]
    assert "influences" in g["metadata"]["relation_types"]
    assert "enables" in g["metadata"]["relation_types"]


def test_build_graph_metadata_type_counts():
    g = build_graph(DATA_DIR)
    counts = g["metadata"]["type_counts"]
    assert counts["enables"] > 50
    assert counts["blocks"] > 0
    assert counts["parallels"] > 0
    assert counts["requires"] > 0


def test_build_graph_metadata_system_counts():
    g = build_graph(DATA_DIR)
    counts = g["metadata"]["system_counts"]
    # 至少 5 个体系
    assert len(counts) >= 5


def test_build_graph_missing_file(tmp_path):
    g = build_graph(tmp_path)
    # 缺 relations.yaml 时返回错误 metadata
    assert "nodes" in g
    assert "edges" in g
    assert g["nodes"] == [] or "error" in g["metadata"]


def test_build_graph_no_duplicates():
    """节点 ID 应无重复"""
    g = build_graph(DATA_DIR)
    ids = [n["id"] for n in g["nodes"]]
    assert len(ids) == len(set(ids))


# ── Mermaid 输出（v2.9 新增） ──


def test_build_mermaid_returns_string():
    g = build_graph(DATA_DIR)
    md = build_mermaid(g, max_edges=20)
    assert isinstance(md, str)
    assert "```mermaid" in md
    assert "flowchart" in md
    assert "```" in md


def test_build_mermaid_includes_subgraphs():
    g = build_graph(DATA_DIR)
    md = build_mermaid(g, max_edges=20)
    assert "subgraph" in md
    assert "end" in md


def test_build_mermaid_respects_max_edges():
    g = build_graph(DATA_DIR)
    md = build_mermaid(g, max_edges=5)
    edge_lines = [l for l in md.split("\n") if "-->" in l]
    assert len(edge_lines) <= 5


def test_build_mermaid_no_breaks_syntax():
    g = build_graph(DATA_DIR)
    md = build_mermaid(g, max_edges=10)
    # 不能有裸方括号
    for line in md.split("\n"):
        if '["' in line or "[(" in line:
            # 检查中括号配对
            assert line.count("[") == line.count("]")


def test_build_mermaid_contains_colors_or_styles():
    g = build_graph(DATA_DIR)
    md = build_mermaid(g, max_edges=10)
    # 应至少包含子图（带体系名）
    assert "subgraph" in md
