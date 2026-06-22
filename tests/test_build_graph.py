"""
test_build_graph.py — v2.2 E. 数据可视化脚本的单测

测试 scripts/build_graph.py：
- 基本图构建
- 体系过滤
- 统计输出
- 文件输出
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_graph import build_graph, SYSTEM_COLORS, RELATION_COLORS  # noqa: E402


# ─── 基本图构建 ───


def test_build_graph_returns_dict():
    graph = build_graph(ROOT / "data")
    assert "nodes" in graph
    assert "edges" in graph
    assert "metadata" in graph


def test_build_graph_has_nodes():
    graph = build_graph(ROOT / "data")
    assert len(graph["nodes"]) > 0
    node = graph["nodes"][0]
    assert "id" in node
    assert "system" in node
    assert "name" in node
    assert "color" in node


def test_build_graph_has_edges():
    graph = build_graph(ROOT / "data")
    assert len(graph["edges"]) > 0
    edge = graph["edges"][0]
    assert "source" in edge
    assert "target" in edge
    assert "type" in edge
    assert "color" in edge


def test_build_graph_node_ids_have_colon():
    """所有节点 ID 应为 system:id 格式"""
    graph = build_graph(ROOT / "data")
    for n in graph["nodes"]:
        assert ":" in n["id"], f"节点 {n['id']} 缺少 system:id 格式"


def test_build_graph_metadata_has_stats():
    graph = build_graph(ROOT / "data")
    meta = graph["metadata"]
    assert "total_nodes" in meta
    assert "total_edges" in meta
    assert "type_counts" in meta
    assert "system_counts" in meta
    assert "relation_colors" in meta
    assert "system_colors" in meta
    assert meta["total_nodes"] == len(graph["nodes"])
    assert meta["total_edges"] == len(graph["edges"])


def test_build_graph_all_known_relations():
    """所有边的 type 都在已知关系类型列表中"""
    graph = build_graph(ROOT / "data")
    for e in graph["edges"]:
        assert e["type"] in RELATION_COLORS, f"未知关系类型: {e['type']}"


# ─── 体系过滤 ───


def test_build_graph_filter_system():
    """过滤单个体系时只返回该体系的节点 + 关联"""
    graph = build_graph(ROOT / "data", filter_system="realm")
    assert all(n["system"] == "realm" for n in graph["nodes"])


def test_build_graph_filter_no_match():
    """过滤不存在的体系返回空"""
    graph = build_graph(ROOT / "data", filter_system="nonexistent_system")
    assert len(graph["nodes"]) == 0
    assert len(graph["edges"]) == 0


def test_build_graph_filter_smaller_than_full():
    """过滤后节点数应少于全量"""
    full = build_graph(ROOT / "data")
    filtered = build_graph(ROOT / "data", filter_system="elixir")
    assert len(filtered["nodes"]) < len(full["nodes"])


# ─── CLI ───


def test_cli_stats():
    """--stats 模式打印统计"""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_graph.py"), "--stats"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10,
    )
    # Py3.6 会有 future annotations 报错，跳过
    if "future feature annotations is not defined" in result.stderr:
        pytest.skip("Py3.6 不支持 future annotations")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "节点" in result.stdout
    assert "边" in result.stdout


def test_cli_output_json(tmp_path):
    """--output 模式生成 JSON 文件"""
    out_path = tmp_path / "graph.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_graph.py"),
         "--output", str(out_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10,
    )
    if "future feature annotations is not defined" in result.stderr:
        pytest.skip("Py3.6 不支持 future annotations")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "nodes" in data
    assert "edges" in data
    assert data["metadata"]["total_nodes"] > 0


def test_cli_filter(tmp_path):
    """--filter-system 工作"""
    out_path = tmp_path / "graph_realm.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_graph.py"),
         "--output", str(out_path),
         "--filter-system", "realm"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=10,
    )
    if "future feature annotations is not defined" in result.stderr:
        pytest.skip("Py3.6 不支持 future annotations")
    assert result.returncode == 0
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert all(n["system"] == "realm" for n in data["nodes"])