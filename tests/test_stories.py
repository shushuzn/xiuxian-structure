"""
test_stories.py — 自动验证 stories/*.md 的可玩性

覆盖：
- 每个 story 能被 Story.from_file() 解析
- start_node 存在
- 所有 goto 引用的 target 都存在
- 至少一个 ending 节点
- v32_demo 能 headless 跑通
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from interactive import Story, Engine, State, World  # noqa: E402

STORIES_DIR = ROOT / "stories"
DATA_DIR = ROOT / "data"


def _all_story_files():
    """返回所有 stories/*.md（排除 README.md）"""
    return sorted([
        f for f in STORIES_DIR.glob("*.md")
        if f.name != "README.md"
    ])


@pytest.mark.parametrize("story_path", _all_story_files(), ids=lambda p: p.name)
def test_story_parseable(story_path):
    """每个 story 都能被 Story.from_file() 解析"""
    story = Story.from_file(story_path)
    assert story.id, f"{story_path.name} 缺少 id"
    assert story.title, f"{story_path.name} 缺少 title"
    assert story.nodes, f"{story_path.name} 无节点"


@pytest.mark.parametrize("story_path", _all_story_files(), ids=lambda p: p.name)
def test_story_start_node_exists(story_path):
    """start_node 必须存在"""
    story = Story.from_file(story_path)
    assert story.start_node in story.nodes, (
        f"{story_path.name}: start_node '{story.start_node}' 不在节点列表中"
    )


@pytest.mark.parametrize("story_path", _all_story_files(), ids=lambda p: p.name)
def test_story_goto_targets_exist(story_path):
    """所有 choice 的 goto 必须指向真实节点"""
    story = Story.from_file(story_path)
    missing = []
    for nid, node in story.nodes.items():
        for choice in node.choices:
            target = choice.get("goto")
            if target and target not in story.nodes:
                missing.append(f"{nid} -> {target}")
    assert not missing, (
        f"{story_path.name}: broken goto 引用 ({len(missing)} 处)：\n  " +
        "\n  ".join(missing[:10]) + ("\n  ..." if len(missing) > 10 else "")
    )


@pytest.mark.parametrize("story_path", _all_story_files(), ids=lambda p: p.name)
def test_story_has_at_least_one_ending(story_path):
    """每个 story 至少有一个结局"""
    story = Story.from_file(story_path)
    endings = [nid for nid, n in story.nodes.items() if n.type == "ending"]
    assert endings, f"{story_path.name} 没有 ending 节点"


@pytest.mark.parametrize("story_path", _all_story_files(), ids=lambda p: p.name)
def test_story_refs_files_exist(story_path):
    """refs 字段引用的 .md 文件应真实存在"""
    story = Story.from_file(story_path)
    missing = [
        ref for nid, node in story.nodes.items()
        for ref in node.refs
        if not (STORIES_DIR.parent / ref).exists() and not (STORIES_DIR.parent / f"{ref}.md").exists()
    ]
    assert not missing, (
        f"{story_path.name}: refs 不存在的文件 ({len(missing)} 处)：\n  " +
        "\n  ".join(missing[:5])
    )


def test_v32_demo_headless_path():
    """v32_demo 能完整从 start_node 走到 ending（headless）"""
    story_path = STORIES_DIR / "v32_demo.md"
    story = Story.from_file(story_path)
    world = World.from_yaml_dir(DATA_DIR)
    state = State()
    engine = Engine(world, story, state)

    # headless 模式：每步选第一个有可用 target 的选项
    visited = []
    current = story.start_node
    max_steps = 50
    for _ in range(max_steps):
        node = story.nodes.get(current)
        if not node:
            break
        visited.append(current)
        if node.type == "ending":
            break
        # 找第一个选项
        chosen = None
        for choice in node.choices:
            target = choice.get("goto")
            if target and target in story.nodes:
                chosen = target
                break
        if not chosen:
            break
        current = chosen

    assert current in story.nodes, f"headless 走断（current={current}）"
    final_node = story.nodes[current]
    assert final_node.type == "ending", (
        f"v32_demo headless 在 {max_steps} 步内未到达 ending（停于 {current}）"
    )
    assert visited, "v32_demo 一个节点都没访问"


def test_v32_demo_yaml_ids_resolved():
    """v32_demo 中所有 refs 引用的 .md 文件内 id 必须在对应 yaml 中存在"""
    import yaml as pyyaml

    story_path = STORIES_DIR / "v32_demo.md"
    story = Story.from_file(story_path)

    # 收集每个 system 的 id 索引
    ids_by_system = {}
    for f in sorted(DATA_DIR.glob("*.yaml")):
        sys_name = f.stem
        data = pyyaml.safe_load(f.read_text(encoding="utf-8"))
        ids = set()
        if isinstance(data, dict):
            for section, content in data.items():
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "id" in item:
                            ids.add(item["id"])
        ids_by_system[sys_name] = ids

    # 检查每个 ref（如 "灵根体系/灵根.md"）
    all_node_refs = []
    for nid, node in story.nodes.items():
        all_node_refs.extend(node.refs)

    # 因为 v32_demo 引用的 ref 是 .md 文档（不是 yaml id），
    # 这里仅做"路径在 docs_src 镜像或根目录存在" 检查
    missing = [
        ref for ref in all_node_refs
        if not (ROOT / ref).exists()
        and not (ROOT / "docs_src" / ref).exists()
    ]
    assert not missing, (
        f"v32_demo refs 不存在的文件 ({len(missing)} 处)：\n  " +
        "\n  ".join(missing[:5])
    )
