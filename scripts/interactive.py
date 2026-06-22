#!/usr/bin/env python3
"""
interactive.py — 互动小说引擎

把 data/*.yaml 当作运行时世界数据库，把 stories/*.md 当作剧本，驱动一个
基于状态机的互动叙事。

节点类型：
- scene   场景（叙述 + 数据修改 + 跳转选项）
- ending  结局（终止节点）

核心 API：
- World.from_yaml_dir(ROOT/data)  构建世界
- Story.from_file(stories/xxx.md)  解析剧本
- Engine(world, story).play()      启动交互循环
- Engine.play(seed) / play(input)  用于程序化驱动（CI 测试）

状态操作：
- 玩家属性：set/get/incr/dec
- 标志位：flag/set/clear
- 检查：check(expr)  例如 "灵石 >= 10 and 灵根 == '伪灵根'"

知识引用：
- 节点里 refs: [境界/炼气期, 符箓/火球符]  引擎自动加跳转链接
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parent.parent


# ────────────────────────────────────────────────────────
# 1. 世界（World）
# ────────────────────────────────────────────────────────

class World:
    """运行时世界数据库：11 个 yaml → 内存 dict"""

    def __init__(self, data: dict[str, Any]):
        self.data = data  # {"realms": {"realms": [...], ...}, ...}

    @classmethod
    def from_yaml_dir(cls, yaml_dir: Path) -> "World":
        yaml_dir = Path(yaml_dir)
        data = {}
        for yf in sorted(yaml_dir.glob("*.yaml")):
            with yf.open(encoding="utf-8") as f:
                payload = yaml.safe_load(f)
            # yaml 顶层 key 就是体系名（如 realms, elixirs, ...）
            if isinstance(payload, dict):
                for system_name, system_data in payload.items():
                    data[system_name] = system_data
        return cls(data)

    def lookup(self, system: str, *path: str) -> Any:
        """按路径取值，例如 lookup('realms', 'by_id', 'lianqi', 'lifespan')"""
        node: Any = self.data.get(system)
        for p in path:
            if isinstance(node, dict):
                node = node.get(p)
            elif isinstance(node, list):
                # 尝试当作 id 索引
                node = next((x for x in node if isinstance(x, dict) and x.get("id") == p), None)
            else:
                return None
            if node is None:
                return None
        return node

    def find_by_id(self, system: str, target_id: str) -> dict | None:
        """按 id 找记录：find_by_id('realms', 'lianqi') → {...}"""
        for v in self.data.get(system, {}).values():
            if isinstance(v, list):
                hit = next((x for x in v if isinstance(x, dict) and x.get("id") == target_id), None)
                if hit:
                    return hit
        return None

    def render_template(self, text: str) -> str:
        """把 {体系.记录.字段} 这种占位符替换为实际值"""
        def repl(m: re.Match) -> str:
            path = m.group(1).split(".")
            # 第一个 token 是体系名
            system = path[0]
            val = self.lookup(system, *path[1:])
            if val is None:
                return f"<未知:{m.group(1)}>"
            if isinstance(val, (dict, list)):
                return f"<{m.group(1)}>"  # 复杂对象不内联
            return str(val)
        return re.sub(r"\{([^{}]+)\}", repl, text)


# ────────────────────────────────────────────────────────
# 2. 剧本（Story）
# ────────────────────────────────────────────────────────

@dataclass
class Node:
    id: str
    type: str  # "scene" | "ending"
    text: str
    data: dict = field(default_factory=dict)   # 进入时设置/修改的状态
    refs: list[str] = field(default_factory=list)  # 知识引用
    choices: list[dict] = field(default_factory=list)  # [{label, goto, if, set, flag}]


@dataclass
class Story:
    id: str
    title: str
    description: str = ""
    start_node: str = "start"
    nodes: dict[str, Node] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> "Story":
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        return cls.from_text(text, source_name=str(path))

    @classmethod
    def from_text(cls, text: str, source_name: str = "<text>") -> "Story":
        # 1) front matter（# 标题 + 元数据段）
        meta, body = _split_front_matter(text)
        if not meta.get("id"):
            raise ValueError(f"{source_name}: 缺少年级 # id 字段")
        story = cls(
            id=meta["id"],
            title=meta.get("title") or meta["id"],
            description=meta.get("description", ""),
            start_node=meta.get("start", "start"),
        )

        # 2) 节点
        nodes_raw = _split_nodes(body)
        for nid, (type_hint, raw) in nodes_raw.items():
            node = _parse_node(nid, type_hint, raw)
            story.nodes[nid] = node

        if story.start_node not in story.nodes:
            raise ValueError(f"{source_name}: 起点节点 '{story.start_node}' 不存在")
        return story

    @classmethod
    def parse_nodes_only(cls, text: str, source_name: str = "<text>") -> dict[str, "Node"]:
        """只解析节点（不校验 start），给 generate_node.py 这种场景用"""
        _meta, body = _split_front_matter(text)
        nodes_raw = _split_nodes(body)
        result: dict[str, "Node"] = {}
        for nid, (type_hint, raw) in nodes_raw.items():
            result[nid] = _parse_node(nid, type_hint, raw)
        return result

    def get(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)


# ────────────────────────────────────────────────────────
# 3. 状态（State）
# ────────────────────────────────────────────────────────

class State:
    """玩家状态：属性 + 物品 + 标志位"""

    def __init__(self, initial: dict | None = None):
        self.attrs: dict[str, Any] = dict(initial or {})
        self.flags: set[str] = set()
        self.items: list[str] = []              # 背包（物品列表）
        self.npc_favor: dict[str, int] = {}     # NPC 好感度（0-100）
        self.time: dict[str, int] = {"年": 1, "月": 1, "日": 1}  # 游戏内时间

    def get(self, key: str, default: Any = None) -> Any:
        return self.attrs.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.attrs[key] = value

    def incr(self, key: str, delta: Any = 1) -> None:
        self.attrs[key] = self.attrs.get(key, 0) + delta

    def flag(self, name: str) -> bool:
        return name in self.flags

    def set_flag(self, name: str) -> None:
        self.flags.add(name)

    def clear_flag(self, name: str) -> None:
        self.flags.discard(name)

    def to_dict(self) -> dict:
        return {
            "attrs": dict(self.attrs),
            "flags": sorted(self.flags),
            "items": list(self.items),
            "npc_favor": dict(self.npc_favor),
            "time": dict(self.time),
            "score": self.score_breakdown(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "State":
        s = cls(d.get("attrs", {}))
        s.flags = set(d.get("flags", []))
        s.items = list(d.get("items", []))
        s.npc_favor = dict(d.get("npc_favor", {}))
        s.time = dict(d.get("time", {"年": 1, "月": 1, "日": 1}))
        return s

    def save(self, path) -> None:
        """存档到 JSON 文件"""
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path) -> "State":
        """从 JSON 文件读档"""
        from pathlib import Path
        with open(Path(path), encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    # ── 背包 ──
    def add_item(self, item: str) -> None:
        if item and item not in self.items:
            self.items.append(item)

    def remove_item(self, item: str) -> bool:
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def has_item(self, item: str) -> bool:
        return item in self.items

    @property
    def item_count(self) -> int:
        return len(self.items)

    # ── NPC 好感度 ──
    def modify_npc_favor(self, npc: str, delta: int) -> int:
        """调整 NPC 好感度，返回调整后的值"""
        cur = self.npc_favor.get(npc, 50)  # 默认 50（中性）
        cur = max(0, min(100, cur + delta))
        self.npc_favor[npc] = cur
        return cur

    def get_npc_favor(self, npc: str) -> int:
        return self.npc_favor.get(npc, 50)

    # ── 时间推进 ──
    def advance_time(self, years: int = 0, months: int = 0, days: int = 0) -> dict:
        """推进时间（年/月/日），自动处理进位"""
        y = self.time.get("年", 1) + years
        m = self.time.get("月", 1) + months
        d = self.time.get("日", 1) + days
        # 处理日进位
        while d > 30:
            d -= 30
            m += 1
        # 处理月进位
        while m > 12:
            m -= 12
            y += 1
        self.time = {"年": y, "月": m, "日": d}
        return dict(self.time)

    def get_time_str(self) -> str:
        t = self.time
        return f"{t.get('年', 1)}年{t.get('月', 1):02d}月{t.get('日', 1):02d}日"

    # ── 结局评分 ──
    def score_breakdown(self) -> dict:
        """计算结局评分（0-100）"""
        breakdown = {}
        # 灵石评分（最多 30 分）
        lingshi = self.attrs.get("灵石", 0)
        breakdown["灵石"] = min(30, lingshi // 100)
        # 声望评分（最多 25 分）
        shengwang = self.attrs.get("声望", 0)
        breakdown["声望"] = min(25, shengwang // 4)
        # 物品评分（最多 20 分，每件 2 分）
        items = self.item_count
        breakdown["物品"] = min(20, items * 2)
        # NPC 好感评分（最多 15 分）
        avg_favor = sum(self.npc_favor.values()) / max(len(self.npc_favor), 1) if self.npc_favor else 50
        breakdown["好感"] = min(15, int((avg_favor - 50) / 50 * 15))
        # 修为评分（最多 10 分）
        realm = self.attrs.get("境界", "")
        realm_score = {"炼气期": 1, "筑基期": 3, "结丹期": 5, "元婴期": 7,
                      "化神期": 8, "炼虚期": 9, "合体期": 10, "渡劫期": 10, "大乘期": 10}
        breakdown["修为"] = realm_score.get(realm, 0)
        breakdown["总分"] = sum(breakdown.values())
        return breakdown

    def check(self, expr: str) -> bool:
        """求值一个简单表达式：'灵石 >= 10' / '灵根 == "伪灵根"' / 'flag.遇见妖兽'"""
        if not expr or not expr.strip():
            return True
        # flag 检查
        m = re.match(r"flag\.(\w+)$", expr.strip())
        if m:
            return self.flag(m.group(1))
        # 替换变量名为字面量
        # 支持：>=, <=, ==, !=, >, <, and, or, not, 字面字符串/数字
        safe = self._substitute(expr)
        try:
            return bool(eval(safe, {"__builtins__": {}}, {}))
        except Exception:
            return False

    def _substitute(self, expr: str) -> str:
        # 把 attr 名替换为其字符串表示（"伪灵根" / 10 / True）
        def repl(m: re.Match) -> str:
            name = m.group(1)
            v = self.attrs.get(name)
            if isinstance(v, str):
                return repr(v)
            return str(v)
        # 长名优先
        names = sorted(self.attrs.keys(), key=len, reverse=True)
        out = expr
        for n in names:
            out = re.sub(rf"\b{re.escape(n)}\b", repl(n) if False else f"<<{n}>>", out)
        # 再二次替换为字面量
        for n in names:
            v = self.attrs.get(n)
            out = out.replace(f"<<{n}>>", repr(v) if isinstance(v, str) else str(v))
        return out


# ────────────────────────────────────────────────────────
# 4. 引擎（Engine）
# ────────────────────────────────────────────────────────

@dataclass
class EngineEvent:
    """每一步的输出（用于程序化 / CI 测试）"""
    node_id: str
    text: str
    choices: list[dict]  # [{label, goto}]
    ending: bool = False
    refs: list[str] = field(default_factory=list)


class Engine:
    def __init__(self, world: World, story: Story, state: State | None = None):
        self.world = world
        self.story = story
        self.state = state or State()
        self.history: list[str] = []
        self.log: list[str] = []

    def play(self) -> None:
        """交互式（CLI）"""
        print(f"\n🎮 {self.story.title}\n{self.story.description}\n{'='*60}")
        node_id = self.story.start_node
        while True:
            node = self.story.get(node_id)
            if not node:
                print(f"❌ 节点 '{node_id}' 不存在")
                return
            self._apply_state(node)
            text = self.world.render_template(node.text)
            print(f"\n【{node.id}】\n{text}\n")

            if node.type == "ending":
                print("🏁 结局。")
                return

            if not node.choices:
                print("（无后续）")
                return

            valid = [c for c in node.choices if self.state.check(c.get("if", ""))]
            if not valid:
                print("❌ 所有选项都不可用（条件不满足）")
                return

            for i, c in enumerate(valid, 1):
                print(f"  [{i}] {c['label']}")
            print(f"  [s] 查看状态  [q] 退出")

            while True:
                try:
                    raw = input("> ").strip()
                except EOFError:
                    return
                if raw == "q":
                    return
                if raw == "s":
                    print(f"  状态: {self.state.attrs}  标志: {sorted(self.state.flags)}")
                    continue
                if raw.isdigit() and 1 <= int(raw) <= len(valid):
                    chosen = valid[int(raw) - 1]
                    self._apply_choice_actions(chosen)
                    node_id = chosen["goto"]
                    self.history.append(node_id)
                    self.log.append(f"→ {chosen['label']} → {node_id}")
                    break
                print("  无效输入")

    def step(self, choice_index: int | None = None) -> EngineEvent:
        """单步（程序化）。choice_index=None 时自动选第一个有效选项。
        返回事件并推进到下一节点。"""
        if not self.history:
            node_id = self.story.start_node
        else:
            # 重放：删掉上次推进的节点，从 history 末梢继续
            # 为简单起见，要求 step() 顺序调用
            raise RuntimeError("step() 应从头顺序调用；如要重置请新建 Engine")

        node = self.story.get(node_id)
        assert node, f"start node {node_id} missing"
        self._apply_state(node)
        self.history.append(node_id)

        text = self.world.render_template(node.text)
        valid = [c for c in node.choices if self.state.check(c.get("if", ""))]

        if node.type == "ending":
            return EngineEvent(node_id, text, [], ending=True, refs=node.refs)

        if choice_index is None:
            choice_index = 0
        if not (0 <= choice_index < len(valid)):
            return EngineEvent(node_id, text, [], ending=True, refs=node.refs)

        chosen = valid[choice_index]
        self._apply_choice_actions(chosen)

        next_id = chosen["goto"]
        # 立即前进一步：迭代而非递归，避免深度爆栈
        return self._step_to(next_id)

    def _step_to(self, node_id: str) -> EngineEvent:
        node = self.story.get(node_id)
        assert node
        self._apply_state(node)
        self.history.append(node_id)
        text = self.world.render_template(node.text)
        valid = [c for c in node.choices if self.state.check(c.get("if", ""))]
        return EngineEvent(
            node.id, text,
            [{"label": c["label"], "goto": c["goto"]} for c in valid],
            ending=(node.type == "ending"),
            refs=node.refs,
        )

    def _apply_state(self, node: Node) -> None:
        """应用节点 data 字段的初始化状态。
        默认行为：data 块覆盖现有状态。
        如果 key 以 ? 开头（如 ?灵石），则仅在未设置时初始化。
        """
        for k, v in node.data.items():
            if k.startswith("?"):
                real_key = k[1:]
                if real_key not in self.state.attrs:
                    self.state.attrs[real_key] = v
            else:
                self.state.attrs[k] = v

    def _apply_choice_actions(self, chosen: dict) -> None:
        """应用选项的副作用（set / flag / pickup / drop / favor / advance）。"""
        if "set" in chosen:
            self.state.attrs.update(chosen["set"])
        if "flag" in chosen:
            self.state.set_flag(chosen["flag"])
        if "pickup" in chosen:
            item = chosen["pickup"]
            if isinstance(item, list):
                for it in item:
                    self.state.add_item(it)
            else:
                self.state.add_item(item)
        if "drop" in chosen:
            item = chosen["drop"]
            if isinstance(item, list):
                for it in item:
                    self.state.remove_item(it)
            else:
                self.state.remove_item(item)
        if "favor" in chosen:
            for npc, delta in chosen["favor"].items():
                self.state.modify_npc_favor(npc, delta)
        if "advance" in chosen:
            adv = chosen["advance"]
            self.state.advance_time(
                years=adv.get("years", 0),
                months=adv.get("months", 0),
                days=adv.get("days", 0),
            )

    def save(self) -> dict:
        """返回可序列化的存档"""
        return {
            "story": self.story.id,
            "state": self.state.to_dict(),
            "history": list(self.history),
        }

    def save_to_file(self, path) -> None:
        """存档到 JSON 文件"""
        self.state.save(path)

    @classmethod
    def load(cls, world: World, story: Story, save: dict) -> "Engine":
        e = cls(world, story, State.from_dict(save["state"]))
        e.history = list(save.get("history", []))
        return e

    @classmethod
    def load_from_file(cls, world: World, story: Story, path) -> "Engine":
        """从 JSON 文件读档"""
        return cls.load(world, story, {"story": story.id, "state": State.load(path).to_dict()})

    def get_score(self) -> dict:
        """获取结局评分（在 ending 节点调用）"""
        return self.state.score_breakdown()


# ────────────────────────────────────────────────────────
# 5. 剧本解析（DSL）
# ────────────────────────────────────────────────────────

NODE_HEADER = re.compile(r"^##\s+节点\s+(\S+)(?:\s+\((\S+)\))?\s*$", re.MULTILINE)
SECTION_HEADER = re.compile(r"^(type|text|data|next|refs|choices):\s*(.*)$")


def _split_front_matter(text: str) -> tuple[dict, str]:
    """简单 front matter：第一个 ## 节点 之前的所有 # / ## 元数据 段"""
    lines = text.split("\n")
    meta: dict = {}
    body_start = 0
    in_meta_section = False
    for i, ln in enumerate(lines):
        if ln.startswith("# ") and not in_meta_section:
            # 标题
            if not meta.get("title"):
                meta["title"] = ln[2:].strip()
            body_start = i + 1
        elif ln.startswith("## 元数据"):
            in_meta_section = True
            body_start = i + 1
        elif in_meta_section and re.match(r"^[a-zA-Z_][\w-]*:", ln):
            k, _, v = ln.partition(":")
            meta[k.strip()] = v.strip()
        elif ln.startswith("## 节点"):
            body_start = i
            break
    body = "\n".join(lines[body_start:])
    return meta, body


def _split_nodes(body: str) -> dict[str, str]:
    """按 `## 节点 <id> [(type)]` 切分"""
    parts: dict[str, str] = {}
    matches = list(NODE_HEADER.finditer(body))
    for i, m in enumerate(matches):
        nid = m.group(1)
        # 节点标题里 (ending) / (scene) 标识，可被节点内 type: 字段覆盖
        type_hint = m.group(2)  # None / "scene" / "ending"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        parts[nid] = (type_hint, body[start:end].strip("\n"))
    return parts


def _parse_node(nid: str, type_hint: str | None, raw: str) -> Node:
    # 简单 YAML 风格解析（type/text/data/next/refs）
    lines = raw.split("\n")
    node = Node(id=nid, type=type_hint or "scene", text="")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            i += 1
            continue
        m = SECTION_HEADER.match(ln)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if key in ("type", "text", "refs"):
            if key == "type":
                # 显式 type 字段覆盖 type_hint
                node.type = val or node.type
            elif key == "text":
                # 多行：用 | 起首，下一空行/段标题结束
                buf = []
                if val == "|":
                    i += 1
                    while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t") or not lines[i].strip()):
                        if not lines[i].strip():
                            buf.append("")
                        else:
                            buf.append(lines[i].lstrip())
                        i += 1
                    node.text = "\n".join(buf).rstrip()
                    continue
                else:
                    node.text = val
            elif key == "refs":
                node.refs = [x.strip() for x in val.split(",") if x.strip()]
            i += 1
        elif key == "data":
            # YAML 多行缩进块
            block, i = _collect_indented(lines, i + 1)
            try:
                node.data = yaml.safe_load(block) or {}
            except yaml.YAMLError:
                node.data = {}
        elif key == "next":
            # 选项列表
            block, i = _collect_indented(lines, i + 1)
            try:
                parsed = yaml.safe_load(block) or []
                if isinstance(parsed, list):
                    node.choices = parsed
            except yaml.YAMLError:
                node.choices = []
        else:
            i += 1
    return node


def _collect_indented(lines: list[str], start: int) -> tuple[str, int]:
    """从 start 开始收集缩进行（>= 2 空格），遇到非缩进/EOF 停止"""
    buf: list[str] = []
    i = start
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("  ") or ln.startswith("\t"):
            buf.append(ln)
            i += 1
        else:
            break
    return "\n".join(buf), i


# ────────────────────────────────────────────────────────
# 6. CLI 入口
# ────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="互动小说引擎")
    p.add_argument("--story", type=Path, required=True, help="剧本 .md 路径")
    p.add_argument("--data-dir", type=Path, default=ROOT / "data", help="yaml 目录")
    p.add_argument("--headless", action="store_true", help="不进入交互，直接选第一选项走到结尾（CI 用）")
    p.add_argument("--save", type=Path, help="保存到 JSON 存档（结束时）")
    p.add_argument("--load", type=Path, help="从 JSON 存档继续游戏")
    p.add_argument("--score", action="store_true", help="结束时打印结局评分")
    args = p.parse_args(argv)

    world = World.from_yaml_dir(args.data_dir)
    story = Story.from_file(args.story)

    # 读档优先：用存档中的 state 初始化
    if args.load:
        engine = Engine.load_from_file(world, story, args.load)
        print(f"📂 已从存档加载: {args.load}")
    else:
        engine = Engine(world, story)

    if args.headless:
        # 自动路径：始终选第一个有效选项
        steps = 0
        node_id = story.start_node
        while True:
            node = story.get(node_id)
            if not node:
                break
            engine._apply_state(node)  # 应用 data 块的状态
            valid = [c for c in node.choices if engine.state.check(c.get("if", ""))]
            if node.type == "ending" or not valid:
                print(f"🏁 节点: {node.id} | 结局: {node.type == 'ending'} | 历史: {engine.history}")
                break
            chosen = valid[0]
            print(f"  {node.id} → {chosen['label']} → {chosen['goto']}")
            engine._apply_choice_actions(chosen)
            node_id = chosen["goto"]
            engine.history.append(node_id)
            steps += 1
            if steps > 100:
                print("❌ 步数过多，可能循环")
                return 1
        if args.save:
            engine.save_to_file(args.save)
            print(f"💾 已存档: {args.save}")
        if args.score:
            score = engine.get_score()
            print(f"\n📊 结局评分:")
            for k, v in score.items():
                print(f"   {k}: {v}")
        return 0
    else:
        engine.play()
        return 0


if __name__ == "__main__":
    sys.exit(main())
