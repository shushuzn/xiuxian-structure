#!/usr/bin/env python3
"""
examples/consume-interactive.py
================================

程序化消费互动小说故事的 4 个高层 API。

为什么需要这层 API？
--------------------
``scripts/interactive.py`` 提供底层 ``Engine`` 用来"玩"一个故事（CLI / 打印），
但下游消费者（前端、LLM 工具、批量分析、CI 校验）通常只想问**结构性问题**：

  - 这个故事长什么样？
  - 一共有多少结局？怎么走？
  - 选 A 一直走下去会怎样？选 B 呢？
  - 最少几步能到某个结局？
  - 整个故事能不能塞进一个 JSON？

这层 API 把"游玩"和"分析"分开：你不需要创建 Engine/State 也能回答这些问题。

四个 API
--------

1. ``analyze_story(path)`` — 故事统计（节点/分支/可达性/结局）
2. ``walk_all_paths(path)`` — 遍历**所有可能路径**，输出每条线的剧本
3. ``find_shortest_path(path, from_id, to_id)`` — BFS 找最短决策链
4. ``export_to_json(path)`` — 故事结构序列化为 JSON（供前端/LLM 用）

设计原则
--------
* **零副作用**：不创建 Engine，不写文件（export_to_json 除外）
* **不读 yaml**：这些 API 只关心故事结构，不依赖世界数据
* **可组合**：返回纯 dict / list，可被其他脚本二次处理
* **零参数也能跑**：默认分析 stories/hanli_vol1_mochui.md

用法
----
::

    # 统计
    python3 examples/consume-interactive.py analyze stories/hanli_vol1_mochui.md

    # 遍历所有路径
    python3 examples/consume-interactive.py walk stories/hanli_vol1_mochui.md

    # 找最短路径
    python3 examples/consume-interactive.py path stories/hanli_vol1_mochui.md \\
        --from 托付 --to 杀墨结局

    # 导出 JSON
    python3 examples/consume-interactive.py export stories/hanli_vol1_mochui.md \\
        --output /tmp/hanli.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Any

# 让 examples/ 里的脚本能 import 仓库根下的 scripts/ 模块
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from interactive import Story, Node  # noqa: E402  路径注入后必须


# ---------------------------------------------------------------------------
# API 1: analyze_story
# ---------------------------------------------------------------------------

def analyze_story(path: str | Path) -> dict[str, Any]:
    """统计一个故事的结构特征。

    Returns
    -------
    dict 包含:

    - ``id`` (str) — 故事 id
    - ``title`` (str)
    - ``description`` (str)
    - ``start_node`` (str)
    - ``node_count`` (int) — 总节点数
    - ``scene_count`` / ``ending_count`` (int)
    - ``ending_ids`` (list[str]) — 所有结局节点 id
    - ``reachable_count`` (int) — 从 start 出发可达的节点数
    - ``unreachable`` (list[str]) — 孤儿节点（永远走不到）
    - ``branch_points`` (list[{id, choice_count}]) — 有 ≥2 个选项的节点
    - ``conditional_choices`` (int) — 带 ``if:`` 条件过滤的选项总数
    - ``refs_total`` (int) — 所有节点 ``refs:`` 引用数合计
    - ``refs_unique`` (int) — 去重后引用数
    - ``max_depth`` (int) — 从 start 到任一结局的最长可达路径长度
    - ``is_well_formed`` (bool) — node_count == reachable_count 且 start_node 存在
    """
    story = Story.from_file(Path(path))
    nodes = story.nodes

    # 可达性 BFS
    reachable: set[str] = set()
    queue = deque([story.start_node])
    while queue:
        nid = queue.popleft()
        if nid in reachable or nid not in nodes:
            continue
        reachable.add(nid)
        for ch in nodes[nid].choices:
            goto = ch.get("goto")
            if goto and goto not in reachable:
                queue.append(goto)

    # 分支点 / 条件选项
    branch_points = []
    conditional_choices = 0
    for nid, node in nodes.items():
        if len(node.choices) >= 2:
            branch_points.append({"id": nid, "choice_count": len(node.choices)})
        for ch in node.choices:
            if ch.get("if"):
                conditional_choices += 1

    # 结局统计
    ending_ids = [nid for nid, n in nodes.items() if n.type == "ending"]
    scene_count = sum(1 for n in nodes.values() if n.type == "scene")

    # refs 汇总
    all_refs: list[str] = []
    for n in nodes.values():
        all_refs.extend(n.refs)

    # 最大深度（从 start 到任一结局的最长可达 BFS 路径）
    max_depth = _max_depth_to_ending(story, ending_ids)

    return {
        "id": story.id,
        "title": story.title,
        "description": story.description,
        "start_node": story.start_node,
        "node_count": len(nodes),
        "scene_count": scene_count,
        "ending_count": len(ending_ids),
        "ending_ids": ending_ids,
        "reachable_count": len(reachable),
        "unreachable": [nid for nid in nodes if nid not in reachable],
        "branch_points": branch_points,
        "conditional_choices": conditional_choices,
        "refs_total": len(all_refs),
        "refs_unique": len(set(all_refs)),
        "max_depth": max_depth,
        "is_well_formed": (
            story.start_node in nodes and len(reachable) == len(nodes)
        ),
    }


def _max_depth_to_ending(story: Story, ending_ids: list[str]) -> int:
    """从 start 出发到任一结局的最长**可达**路径长度（节点数）。"""
    if not ending_ids:
        return 0
    # BFS level 计数
    depth: dict[str, int] = {story.start_node: 1}
    queue = deque([story.start_node])
    max_d = 0
    while queue:
        nid = queue.popleft()
        if nid not in story.nodes:
            continue
        d = depth[nid]
        if nid in ending_ids:
            max_d = max(max_d, d)
            # 不下钻结局节点（通常没有 next）
            continue
        for ch in story.nodes[nid].choices:
            goto = ch.get("goto")
            if goto and goto not in depth and goto in story.nodes:
                depth[goto] = d + 1
                queue.append(goto)
    return max_d


# ---------------------------------------------------------------------------
# API 2: walk_all_paths
# ---------------------------------------------------------------------------

def walk_all_paths(path: str | Path, max_paths: int = 200) -> list[dict[str, Any]]:
    """枚举从 start 出发所有**可能**的完整路径（到 ending 或 dead-end）。

    每条路径返回::

        {
            "steps": [节点 id 列表],
            "choices": [每次选择的 label 列表],
            "end_type": "ending" | "scene" (死循环/无效 goto) | "dead_end" (无 next)
            "state_at_end": {最终 state 快照（需 Engine）}  ← 本 API 不计算
        }

    Notes
    -----
    * **不计算 state**：纯结构遍历，不创建 Engine 也不消费条件
      （条件过滤是 Engine 的职责；本 API 只问"如果走通这条路，沿途会触发什么 data 改动"）
    * **选项条件不应用**：即便某选项有 ``if:`` 限制，本 API 也照常走
    * **死循环防护**：超过 50 步仍不到 ending 视为"循环/无效"
    """
    story = Story.from_file(Path(path))
    paths: list[dict[str, Any]] = []

    def _walk(node_id: str, steps: list[str], choices: list[str], depth: int) -> None:
        if len(paths) >= max_paths:
            return
        if depth > 50:
            paths.append({
                "steps": steps[:],
                "choices": choices[:],
                "end_type": "loop_or_invalid",
            })
            return
        if node_id not in story.nodes:
            paths.append({
                "steps": steps[:],
                "choices": choices[:],
                "end_type": "invalid_goto",
            })
            return

        node = story.nodes[node_id]
        new_steps = steps + [node_id]

        if node.type == "ending" or not node.choices:
            end_type = "ending" if node.type == "ending" else "dead_end"
            paths.append({
                "steps": new_steps,
                "choices": choices[:],
                "end_type": end_type,
            })
            return

        for ch in node.choices:
            goto = ch.get("goto")
            label = ch.get("label", goto or "?")
            if not goto:
                paths.append({
                    "steps": new_steps,
                    "choices": choices + [label],
                    "end_type": "no_goto",
                })
                continue
            _walk(goto, new_steps, choices + [label], depth + 1)

    _walk(story.start_node, [], [], 0)
    return paths


# ---------------------------------------------------------------------------
# API 3: find_shortest_path
# ---------------------------------------------------------------------------

def find_shortest_path(
    path: str | Path,
    from_id: str | None = None,
    to_id: str | None = None,
) -> dict[str, Any] | None:
    """BFS 找从 ``from_id`` 到 ``to_id`` 的最短决策链。

    Returns
    -------
    dict 或 None::

        {
            "from": str,
            "to": str,
            "length": int,           # 节点数
            "choices": [label 列表],
            "steps": [节点 id 列表]
        }

    None 表示不可达。

    默认 ``from_id=story.start_node``，``to_id=第一个 ending``。
    """
    story = Story.from_file(Path(path))
    start = from_id or story.start_node
    if start not in story.nodes:
        return None

    # 找候选终点
    if to_id is None:
        endings = [nid for nid, n in story.nodes.items() if n.type == "ending"]
        if not endings:
            return None
        target_endings: set[str] = set(endings)
    else:
        target_endings = {to_id}

    # BFS
    visited: set[str] = {start}
    queue: deque[tuple[str, list[str], list[str]]] = deque([(start, [start], [])])
    while queue:
        nid, steps, choices = queue.popleft()
        if nid in target_endings:
            return {
                "from": start,
                "to": nid,
                "length": len(steps),
                "choices": choices,
                "steps": steps,
            }
        if nid not in story.nodes:
            continue
        for ch in story.nodes[nid].choices:
            goto = ch.get("goto")
            if goto and goto not in visited and goto in story.nodes:
                visited.add(goto)
                label = ch.get("label", goto)
                queue.append((goto, steps + [goto], choices + [label]))

    return None


# ---------------------------------------------------------------------------
# API 4: export_to_json
# ---------------------------------------------------------------------------

def export_to_json(path: str | Path) -> dict[str, Any]:
    """把故事结构导出为 JSON 友好的 dict（无 yaml 依赖）。

    Returns
    -------
    dict::

        {
            "meta": {id, title, description, start_node, node_count, ...},
            "nodes": {
                <id>: {
                    "type": "scene"|"ending",
                    "text": str,
                    "data": dict,    # 触发时的状态改动
                    "refs": list,
                    "choices": [
                        {"label", "goto", "if"?, "set"?, "flag"?}
                    ]
                }
            }
        }
    """
    story = Story.from_file(Path(path))
    nodes_dict: dict[str, Any] = {}
    for nid, node in story.nodes.items():
        nodes_dict[nid] = {
            "type": node.type,
            "text": node.text,
            "data": node.data,
            "refs": node.refs,
            "choices": node.choices,
        }
    return {
        "meta": analyze_story(path),
        "nodes": nodes_dict,
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def _print_analysis(stats: dict[str, Any], path: Path) -> None:
    print(f"📖 故事分析: {path.name}")
    print("=" * 60)
    print(f"  id:           {stats['id']}")
    print(f"  title:        {stats['title']}")
    print(f"  description:  {stats['description']}")
    print()
    print(f"  start_node:    {stats['start_node']}")
    print(f"  node_count:    {stats['node_count']}  (scene: {stats['scene_count']}, ending: {stats['ending_count']})")
    print(f"  reachable:     {stats['reachable_count']} / {stats['node_count']}")
    if stats['unreachable']:
        print(f"  ⚠️  unreachable: {stats['unreachable']}")
    print(f"  max_depth:     {stats['max_depth']} 步 (从 start 到 ending)")
    print()
    print(f"  branch_points: {len(stats['branch_points'])} 个")
    for bp in stats['branch_points']:
        print(f"     - {bp['id']}: {bp['choice_count']} 选项")
    print(f"  conditional_choices: {stats['conditional_choices']} 个带 if 条件")
    print(f"  refs:          {stats['refs_total']} (去重 {stats['refs_unique']})")
    print()
    flag = "✅" if stats['is_well_formed'] else "❌"
    print(f"  {flag} is_well_formed")
    print("=" * 60)


def _print_walk(paths: list[dict[str, Any]], path: Path) -> None:
    print(f"🚶 所有路径: {path.name}")
    print("=" * 60)
    print(f"  共 {len(paths)} 条路径\n")
    for i, p in enumerate(paths, 1):
        print(f"  [{i}] {p['end_type']}  ({len(p['steps'])} 节点)")
        print(f"      steps:   {' → '.join(p['steps'])}")
        if p['choices']:
            print(f"      choices: {' / '.join(p['choices'])}")
        print()


def _print_shortest(result: dict[str, Any] | None, path: Path) -> None:
    print(f"🧭 最短路径: {path.name}")
    print("=" * 60)
    if result is None:
        print("  ❌ 不可达")
    else:
        print(f"  {result['from']} → {result['to']}  ({result['length']} 节点)")
        print(f"  steps:   {' → '.join(result['steps'])}")
        if result['choices']:
            print(f"  choices: {' / '.join(result['choices'])}")
    print("=" * 60)


def _cmd_analyze(args: argparse.Namespace) -> int:
    stats = analyze_story(args.path)
    _print_analysis(stats, args.path)
    return 0 if stats['is_well_formed'] else 1


def _cmd_walk(args: argparse.Namespace) -> int:
    paths = walk_all_paths(args.path, max_paths=args.max_paths)
    _print_walk(paths, args.path)
    return 0


def _cmd_path(args: argparse.Namespace) -> int:
    result = find_shortest_path(args.path, args.frm, args.to)
    _print_shortest(result, args.path)
    return 0 if result is not None else 1


def _cmd_export(args: argparse.Namespace) -> int:
    data = export_to_json(args.path)
    if args.output:
        Path(args.output).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"💾 已导出 → {args.output}  ({Path(args.output).stat().st_size} bytes)")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="consume-interactive",
        description="程序化消费互动小说故事的 4 个高层 API",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("path", type=Path, help="故事 .md 文件路径")

    sp = sub.add_parser("analyze", parents=[common], help="故事统计")
    sp.set_defaults(func=_cmd_analyze)

    sp = sub.add_parser("walk", parents=[common], help="遍历所有路径")
    sp.add_argument("--max-paths", type=int, default=200,
                    help="最多返回路径数（防爆栈）")
    sp.set_defaults(func=_cmd_walk)

    sp = sub.add_parser("path", parents=[common], help="BFS 找最短决策链")
    sp.add_argument("--from", dest="frm", default=None,
                    help="起点节点 id（默认 = story.start_node）")
    sp.add_argument("--to", default=None,
                    help="终点节点 id（默认 = 第一个 ending）")
    sp.set_defaults(func=_cmd_path)

    sp = sub.add_parser("export", parents=[common], help="导出 JSON")
    sp.add_argument("-o", "--output", default=None,
                    help="输出文件路径（省略则打印到 stdout）")
    sp.set_defaults(func=_cmd_export)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
