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
import json
import random
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml

ROOT = Path(__file__).resolve().parent.parent


# ────────────────────────────────────────────────────────
# 1. 世界（World）
# ────────────────────────────────────────────────────────

class World:
    """运行时世界数据库：11 个 yaml → 内存 dict"""

    def __init__(self, data: Dict[str, Any]):
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

    def find_by_id(self, system: str, target_id: str):  # → Optional[Dict]
        """按 id 找记录：find_by_id('realms', 'lianqi') → {...}"""
        for v in self.data.get(system, {}).values():
            if isinstance(v, list):
                hit = next((x for x in v if isinstance(x, dict) and x.get("id") == target_id), None)
                if hit:
                    return hit
        return None

    def render_template(self, text: str) -> str:
        """把 {体系.记录.字段} 这种占位符替换为实际值"""
        def repl(m) -> str:
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
    refs: List[str] = field(default_factory=list)  # 知识引用
    choices: List[dict] = field(default_factory=list)  # [{label, goto, if, set, flag}]


@dataclass
class Story:
    id: str
    title: str
    description: str = ""
    start_node: str = "start"
    nodes: Dict[str, Node] = field(default_factory=dict)

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
    def parse_nodes_only(cls, text: str, source_name: str = "<text>") -> Dict[str, "Node"]:
        """只解析节点（不校验 start），给 generate_node.py 这种场景用"""
        _meta, body = _split_front_matter(text)
        nodes_raw = _split_nodes(body)
        result: Dict[str, "Node"] = {}
        for nid, (type_hint, raw) in nodes_raw.items():
            result[nid] = _parse_node(nid, type_hint, raw)
        return result

    def get(self, node_id):  # → Optional["Node"]
        return self.nodes.get(node_id)


# ────────────────────────────────────────────────────────
# 3. 状态（State）
# ────────────────────────────────────────────────────────

class State:
    """玩家状态：属性 + 物品 + 标志位 + 界面"""

    def __init__(self, initial: Optional[Dict] = None):
        self.attrs: Dict[str, Any] = dict(initial or {})
        self.flags: Set[str] = set()
        self.items: List[str] = []              # 背包（物品列表）
        self.npc_favor: Dict[str, int] = {}     # NPC 好感度（0-100）
        self.time: Dict[str, int] = {"年": 1, "月": 1, "日": 1}  # 游戏内时间
        self.realm: str = "下界"                # v2.5 当前界面（下界/仙界/神界/魔界/冥界）

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
            "realm": self.realm,
            "score": self.score_breakdown(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "State":
        s = cls(d.get("attrs", {}))
        s.flags = set(d.get("flags", []))
        s.items = list(d.get("items", []))
        s.npc_favor = dict(d.get("npc_favor", {}))
        s.time = dict(d.get("time", {"年": 1, "月": 1, "日": 1}))
        s.realm = d.get("realm", "下界")
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
        def repl(m) -> str:
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
    choices: List[dict]  # [{label, goto}]
    ending: bool = False
    refs: List[str] = field(default_factory=list)


# ────────────────────────────────────────────────────────
# 4.6 跨境界试炼副本（v2.15 新增）
# ────────────────────────────────────────────────────────

@dataclass
class TrialStage:
    """试炼副本的关卡"""
    id: str
    name: str
    description: str
    difficulty: str  # "easy" / "normal" / "hard" / "hell"
    realm_required: str  # "炼气期" / "筑基期" / etc.
    duration_minutes: int = 60  # 预计耗时
    conditions: Dict[str, Any] = field(default_factory=dict)  # 进入条件 (state 检查)
    rewards: Dict[str, Any] = field(default_factory=dict)  # 通关奖励
    penalties: Dict[str, Any] = field(default_factory=dict)  # 失败惩罚
    boss: str = ""  # boss 怪物/场景
    story: str = ""  # 剧情描述

    def can_enter(self, state: "State") -> bool:
        """检查玩家是否可进入此关卡"""
        # 境界必须匹配
        if state.get("境界") != self.realm_required:
            return False
        # 检查条件
        for k, v in self.conditions.items():
            if state.get(k) != v:
                return False
        return True


@dataclass
class TrialResult:
    """试炼结果"""
    stage_id: str
    success: bool
    rounds: int  # 持续回合数
    rewards_gained: Dict[str, Any] = field(default_factory=dict)
    penalties_applied: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""  # 详细描述
    score: int = 0  # 评分 0-100


class TrialDungeon:
    """跨境界试炼副本

    按境界分层的试炼关卡，每层有不同难度。
    通过试炼获得奖励，失败有惩罚。
    """

    REALM_STAGES = [
        ("lianqi", "炼气期", "lianqi"),
        ("zhuji", "筑基期", "zhuji"),
        ("jiedan", "结丹期", "jiedan"),
        ("yuanying", "元婴期", "yuanying"),
        ("huashen", "化神期", "huashen"),
        ("lianxu", "炼虚期", "lianxu"),
        ("heti", "合体期", "heti"),
        ("dujie", "渡劫期", "dujie"),
        ("dacheng", "大乘期", "dacheng"),
    ]

    DIFFICULTY_MODIFIERS = {
        "easy": 0.7,    # 通过率 70%
        "normal": 0.5,  # 通过率 50%
        "hard": 0.3,    # 通过率 30%
        "hell": 0.1,    # 通过率 10%
    }

    def __init__(self, world: World, state: "State"):
        self.world = world
        self.state = state
        self.stages: Dict[str, TrialStage] = {}
        self._init_default_stages()

    def _init_default_stages(self) -> None:
        """初始化默认试炼关卡"""
        for stage_id, name, realm_id in self.REALM_STAGES:
            realm_name = self._realm_id_to_name(realm_id)
            for difficulty in ("easy", "normal", "hard", "hell"):
                full_id = f"{stage_id}_{difficulty}"
                self.stages[full_id] = TrialStage(
                    id=full_id,
                    name=f"{name}-{difficulty}",
                    description=f"{name}修士的{difficulty}试炼",
                    difficulty=difficulty,
                    realm_required=name,
                    conditions={},
                    rewards=self._make_rewards(realm_id, difficulty),
                    penalties=self._make_penalties(realm_id, difficulty),
                    boss=self._make_boss(realm_id, difficulty),
                )

    def _realm_id_to_name(self, realm_id: str) -> str:
        """id → 中文名"""
        mapping = {
            "lianqi": "炼气期", "zhuji": "筑基期", "jiedan": "结丹期",
            "yuanying": "元婴期", "huashen": "化神期", "lianxu": "炼虚期",
            "heti": "合体期", "dujie": "渡劫期", "dacheng": "大乘期",
        }
        return mapping.get(realm_id, realm_id)

    def _make_rewards(self, realm_id: str, difficulty: str) -> Dict[str, Any]:
        """生成奖励"""
        base = {"灵石": 50, "经验": 100, "声望": 5}
        mult = {"easy": 1, "normal": 2, "hard": 4, "hell": 8}[difficulty]
        realm_mult = list(self.REALM_STAGES).index((realm_id, self._realm_id_to_name(realm_id), realm_id)) + 1
        return {
            "灵石": base["灵石"] * mult * realm_mult,
            "经验": base["经验"] * mult * realm_mult,
            "声望": base["声望"] * mult * realm_mult,
            "items": [f"{self._realm_id_to_name(realm_id)}-{difficulty}-奖励"] if mult >= 2 else [],
        }

    def _make_penalties(self, realm_id: str, difficulty: str) -> Dict[str, Any]:
        """生成失败惩罚"""
        base = {"灵石": 10, "声望": -2}
        mult = {"easy": 1, "normal": 2, "hard": 4, "hell": 8}[difficulty]
        return {
            "灵石": -base["灵石"] * mult,
            "声望": -2 * mult,
        }

    def _make_boss(self, realm_id: str, difficulty: str) -> str:
        """生成 boss 描述"""
        bosses = {
            "lianqi": "山中虎妖",
            "zhuji": "筑基大妖",
            "jiedan": "结丹期魔修",
            "yuanying": "元婴期心魔化身",
            "huashen": "化神期天劫残影",
            "lianxu": "炼虚期空间裂缝",
            "hetong": "合体期时间乱流",
            "dujie": "渡劫期仙界守卫",
            "dacheng": "大乘期道心试炼",
        }
        return bosses.get(realm_id, "神秘试炼者")

    def list_stages(self, realm_name: str = "") -> List[TrialStage]:
        """列出可进入的关卡"""
        results = []
        for stage in self.stages.values():
            if not realm_name or stage.realm_required == realm_name:
                if stage.can_enter(self.state):
                    results.append(stage)
        return results

    def enter_stage(self, stage_id: str) -> TrialResult:
        """进入指定关卡"""
        stage = self.stages.get(stage_id)
        if not stage:
            return TrialResult(
                stage_id=stage_id, success=False, rounds=0,
                narrative=f"❌ 关卡 '{stage_id}' 不存在",
            )
        if not stage.can_enter(self.state):
            return TrialResult(
                stage_id=stage_id, success=False, rounds=0,
                narrative=f"❌ 无法进入 '{stage.name}': 境界不匹配或条件不满足",
            )
        # 根据难度计算通过率
        modifier = self.DIFFICULTY_MODIFIERS.get(stage.difficulty, 0.5)
        # 基础通过率受灵石、声望等影响
        bonus = 0
        if self.state.get("声望", 0) > 50:
            bonus += 0.1
        if self.state.get("灵石", 0) > 1000:
            bonus += 0.1
        final_rate = min(0.95, modifier + bonus)
        # 模拟试炼
        import random as _r
        _r.seed(hash(stage_id) % 2**32)
        success = _r.random() < final_rate
        rounds = _r.randint(3, 12)
        narrative = self._make_narrative(stage, success, rounds)
        result = TrialResult(
            stage_id=stage_id,
            success=success,
            rounds=rounds,
            narrative=narrative,
            score=int(final_rate * 100) if success else int((1 - final_rate) * 50),
        )
        if success:
            result.rewards_gained = dict(stage.rewards)
        else:
            result.penalties_applied = dict(stage.penalties)
        return result

    def _make_narrative(self, stage: TrialStage, success: bool, rounds: int) -> str:
        """生成试炼叙事"""
        outcome = "✅ 通关！" if success else "❌ 失败..."
        return (
            f"【{stage.name}】{outcome}\n"
            f"难度：{stage.difficulty}，持续 {rounds} 回合\n"
            f"Boss：{stage.boss}\n"
            f"{'奖励丰厚' if success else '损失惨重'}"
        )

    def apply_result(self, result: TrialResult) -> None:
        """应用试炼结果到 state"""
        if result.success:
            for k, v in result.rewards_gained.items():
                if k == "items":
                    for item in v:
                        self.state.add_item(item)
                else:
                    self.state.incr(k, v)
        else:
            for k, v in result.penalties_applied.items():
                if k == "声望":
                    self.state.modify_npc_favor("宗门", v)  # 简化
                self.state.incr(k, v)

    def get_progress(self) -> dict:
        """获取试炼进度"""
        total = len(self.stages)
        accessible = len(self.list_stages())
        return {
            "total_stages": total,
            "accessible": accessible,
            "locked": total - accessible,
            "current_realm": self.state.get("境界", "炼气期"),
        }


# ────────────────────────────────────────────────────────
# 4.5 世界书 / 成就 / 多结局 / AI 叙事（v2.9 新增，定义在 Engine 之前）
# ────────────────────────────────────────────────────────

@dataclass
class WorldBookEntry:
    """世界书条目：关键词触发的补充设定"""
    id: str
    keywords: List[str]
    title: str
    content: str
    priority: int = 0
    insert_position: str = "after"
    enabled: bool = True

    def matches(self, text: str) -> bool:
        for kw in self.keywords:
            if kw in text:
                return True
        return False


class WorldBook:
    def __init__(self):
        self.entries: List[WorldBookEntry] = []

    def add(self, entry: WorldBookEntry) -> None:
        self.entries.append(entry)
        self.entries.sort(key=lambda e: -e.priority)

    def lookup(self, text: str, max_entries: int = 3) -> List[WorldBookEntry]:
        matches = []
        for entry in self.entries:
            if entry.enabled and entry.matches(text):
                matches.append(entry)
                if len(matches) >= max_entries:
                    break
        return matches

    def to_dict(self) -> dict:
        return {"entries": [
            {"id": e.id, "keywords": e.keywords, "title": e.title,
             "content": e.content, "priority": e.priority,
             "insert_position": e.insert_position, "enabled": e.enabled}
            for e in self.entries
        ]}


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    condition: str
    points: int = 10
    unlocked: bool = False
    unlock_message: str = ""

    def check(self, state) -> bool:
        if self.unlocked:
            return False
        try:
            return bool(eval(self.condition, {"__builtins__": {}}, {"state": state}))
        except Exception:
            return False


class AchievementTracker:
    def __init__(self):
        self.achievements: List[Achievement] = []
        self.unlocked_history: List[dict] = []

    def add(self, achievement: Achievement) -> None:
        self.achievements.append(achievement)

    def check_all(self, state) -> List[Achievement]:
        newly = []
        for ach in self.achievements:
            if ach.check(state):
                ach.unlocked = True
                newly.append(ach)
                self.unlocked_history.append({
                    "id": ach.id, "name": ach.name,
                    "message": ach.unlock_message or f"成就解锁：{ach.name}",
                    "points": ach.points,
                })
        return newly

    def get_score(self) -> int:
        return sum(a.points for a in self.achievements if a.unlocked)

    def get_progress(self) -> dict:
        total = len(self.achievements)
        unlocked = sum(1 for a in self.achievements if a.unlocked)
        return {
            "total": total, "unlocked": unlocked, "locked": total - unlocked,
            "percent": (unlocked / total * 100) if total > 0 else 0,
        }


@dataclass
class EndInfo:
    id: str
    title: str
    type: str
    rarity: str = "common"
    score_min: int = 0
    score_max: int = 100


class EndingAnalyzer:
    def __init__(self, story):
        self.story = story
        self.endings: List[EndInfo] = []
        for nid, node in story.nodes.items():
            if node.type == "ending":
                etype = "normal"
                rarity = "common"
                if "good" in nid or "正" in nid or "happy" in nid:
                    etype = "good"
                    rarity = "epic"
                elif "bad" in nid or "死" in nid or "fail" in nid or "败" in nid:
                    etype = "bad"
                elif "secret" in nid or "秘" in nid or "hidden" in nid:
                    etype = "secret"
                    rarity = "legendary"
                self.endings.append(EndInfo(
                    id=nid, title=node.text[:30] or nid,
                    type=etype, rarity=rarity,
                ))

    def get_endings(self) -> List[EndInfo]:
        return self.endings

    def predict_ending(self, current_score: int) -> EndInfo:
        for e in self.endings:
            if e.score_min <= current_score <= e.score_max:
                return e
        return self.endings[0] if self.endings else EndInfo(
            id="unknown", title="未知", type="normal"
        )

    def get_completeness(self) -> dict:
        return {
            "total_endings": len(self.endings),
            "good_endings": sum(1 for e in self.endings if e.type == "good"),
            "bad_endings": sum(1 for e in self.endings if e.type == "bad"),
            "secret_endings": sum(1 for e in self.endings if e.type == "secret"),
            "normal_endings": sum(1 for e in self.endings if e.type == "normal"),
            "legendary_endings": sum(1 for e in self.endings if e.rarity == "legendary"),
        }


class AINarrator:
    REALM_TEMPLATES = {
        "炼气期": "你是一名{realm_desc}的炼气期修士，灵根{linggen}，灵石{lingshi}。",
        "筑基期": "你已踏入{realm_desc}的筑基期，{linggen}修士，{lingshi}枚灵石。",
        "结丹期": "金丹已成，你迈入{realm_desc}的结丹期，{linggen}，{lingshi}枚灵石。",
        "元婴期": "元婴初成，你已踏入{realm_desc}的元婴期。",
        "化神期": "神识化形，你已踏入{realm_desc}的化神期。",
        "炼虚期": "虚空中有道，你已踏入{realm_desc}的炼虚期。",
        "合体期": "天人之境，你已踏入{realm_desc}的合体期。",
        "渡劫期": "天劫将至，你已踏入{realm_desc}的渡劫期。",
        "大乘期": "大道将成，你已踏入{realm_desc}的大乘期。",
    }

    def __init__(self, world):
        self.world = world

    def narrate_state(self, state, context: str = "") -> str:
        realm = state.get("境界", "炼气期")
        linggen = state.get("灵根", "伪灵根")
        lingshi = state.get("灵石", 0)
        realm_desc = "下界"
        if realm in ("元婴期", "化神期", "炼虚期", "合体期", "渡劫期", "大乘期"):
            realm_desc = "灵界"
        elif realm in ("人仙期", "地仙期", "天仙期", "玄仙期", "真仙期", "仙君期", "仙王期", "仙帝期"):
            realm_desc = "仙界"
        elif realm in ("神人期", "神王期", "神帝期"):
            realm_desc = "神界"
        template = self.REALM_TEMPLATES.get(realm, "境界 {realm}，{linggen}，{灵石} 灵石。")
        narrative = template.format(realm=realm, realm_desc=realm_desc, linggen=linggen, lingshi=lingshi)
        if context:
            narrative += "\n" + context
        return narrative

    def narrate_change(self, state, attr: str, old_val, new_val) -> str:
        delta = (new_val - old_val) if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)) else 0
        if attr == "灵石":
            if delta > 0:
                return f"你获得了 {delta} 枚灵石（当前：{new_val}）。"
            elif delta < 0:
                return f"你消耗了 {-delta} 枚灵石（剩余：{new_val}）。"
        elif attr == "境界":
            return f"你的境界提升了：{old_val} → {new_val}！"
        elif attr == "声望":
            if delta > 0:
                return f"你的声望提高了 {delta} 点（当前：{new_val}）。"
            elif delta < 0:
                return f"你的声望降低了 {-delta} 点（当前：{new_val}）。"
        return f"{attr} 变化：{old_val} → {new_val}"


class Engine:
    def __init__(self, world: World, story: Story, state: Optional[State] = None):
        self.world = world
        self.story = story
        self.state = state or State()
        self.history: List[str] = []
        self.log: List[str] = []
        # v2.9 新增：世界书、成就、AI 叙事器
        self._worldbook: Optional[WorldBook] = None
        self._achievements: Optional[AchievementTracker] = None
        self._narrator: Optional[AINarrator] = AINarrator(world)

    def attach_worldbook(self, wb: WorldBook) -> None:
        """附加世界书"""
        self._worldbook = wb

    def attach_achievements(self, tracker: AchievementTracker) -> None:
        """附加成就追踪器"""
        self._achievements = tracker

    def check_achievements(self) -> List[Achievement]:
        """检查并解锁新成就"""
        if not self._achievements:
            return []
        return self._achievements.check_all(self.state)

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

    def step(self, choice_index: Optional[int] = None) -> EngineEvent:
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
        if "realm" in chosen:
            self.state.realm = chosen["realm"]
        # ── v2.8 新增：突破 / 战斗 / 随机事件 ──
        if "breakthrough" in chosen:
            to_realm = chosen["breakthrough"].get("to") if isinstance(chosen["breakthrough"], dict) else chosen["breakthrough"]
            sim = BreakthroughSimulator(self.world, self.state)
            result = sim.attempt(to_realm)
            # 把结果存到 state.attrs.last_breakthrough，供下一节点渲染
            self.state.attrs["last_breakthrough"] = {
                "success": result.success,
                "from": result.from_realm,
                "to": result.to_realm,
                "message": result.message,
                "heart_demon": result.heart_demon_encountered,
                "tribulation_passed": result.tribulation_passed,
            }
            # 应用状态变更
            self.state.attrs.update(result.new_attrs)
            for k, v in result.lost_attrs.items():
                if k == "breakthrough_pills":
                    self.state.attrs[k] = v
                else:
                    self.state.attrs[k] = v
        if "combat" in chosen:
            enemy = chosen["combat"].get("enemy") if isinstance(chosen["combat"], dict) else chosen["combat"]
            cs = CombatSystem(self.world, self.state, enemy)
            # 自动战斗（玩家攻击 1 次，敌人反击）
            cs.player_turn("attack")
            if not cs.is_over():
                cs.enemy_turn()
            result = cs.result()
            self.state.attrs["last_combat"] = {
                "enemy_id": result.enemy_id,
                "enemy_name": result.enemy_name,
                "victory": result.victory,
                "fled": result.fled,
                "turns": [{"actor": t.attacker, "action": t.action, "damage": t.damage, "crit": t.crit, "message": t.message} for t in result.turns],
                "player_hp": result.player_hp,
                "enemy_hp": result.enemy_hp,
            }
            # 应用奖励
            for k, v in result.rewards.items():
                if k == "item":
                    self.state.add_item(v)
                else:
                    self.state.incr(k, v)
        if "random_event" in chosen:
            ev_type = chosen["random_event"].get("type") if isinstance(chosen["random_event"], dict) else None
            seed = chosen["random_event"].get("seed") if isinstance(chosen["random_event"], dict) else None
            eng = RandomEventEngine(self.world, self.state, seed=seed)
            ev = eng.trigger(ev_type)
            changes = eng.apply(ev)
            self.state.attrs["last_event"] = {
                "type": ev.event_type,
                "title": ev.title,
                "description": ev.description,
                "changes": changes,
                "choices": ev.choices,
            }
        # ── v2.9 新增：世界书 / 成就 / AI 叙事 ──
        if "worldbook" in chosen:
            wb_id = chosen["worldbook"]
            if hasattr(self, "_worldbook") and self._worldbook:
                for entry in self._worldbook.entries:
                    if entry.id == wb_id:
                        self.state.attrs["last_worldbook"] = {
                            "id": entry.id,
                            "title": entry.title,
                            "content": entry.content,
                        }
                        break
        if "achievement" in chosen:
            ach_id = chosen["achievement"]
            if hasattr(self, "_achievements") and self._achievements:
                for ach in self._achievements.achievements:
                    if ach.id == ach_id:
                        ach.unlocked = True
                        self.state.attrs["last_achievement"] = {
                            "id": ach.id,
                            "name": ach.name,
                            "message": ach.unlock_message or f"成就解锁：{ach.name}",
                            "points": ach.points,
                        }
                        break
        if "narrate" in chosen:
            ctx = chosen["narrate"] if isinstance(chosen["narrate"], str) else ""
            narrator = AINarrator(self.world)
            self.state.attrs["last_narrative"] = narrator.narrate_state(self.state, ctx)
        # ── v2.15 新增：跨境界试炼副本 ──
        if "trial" in chosen:
            stage_id = chosen["trial"]
            dungeon = TrialDungeon(self.world, self.state)
            result = dungeon.enter_stage(stage_id)
            dungeon.apply_result(result)
            self.state.attrs["last_trial"] = {
                "stage_id": result.stage_id,
                "success": result.success,
                "rounds": result.rounds,
                "narrative": result.narrative,
                "rewards": result.rewards_gained,
                "penalties": result.penalties_applied,
                "score": result.score,
            }

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
# 5. 突破模拟（v2.8 新增）
# ────────────────────────────────────────────────────────

@dataclass
class BreakthroughResult:
    """突破结果"""
    success: bool
    from_realm: str
    to_realm: str
    heart_demon_encountered: Optional[str] = None  # 遭遇的心魔
    tribulation_passed: bool = False                # 是否渡过天劫
    new_attrs: Dict[str, Any] = field(default_factory=dict)  # 新增属性
    lost_attrs: Dict[str, Any] = field(default_factory=dict)  # 失去属性
    message: str = ""                                # 提示信息


class BreakthroughSimulator:
    """境界突破模拟器

    根据玩家当前状态 (境界、灵根、丹药、心境) 和目标境界，
    计算突破成功率、心魔遭遇、天劫渡过、最终结果。
    """

    # 灵根 → 突破加成（简化版）
    SPIRIT_ROOT_BONUS = {
        "tian_ling_gen": 0.3,
        "bian_yi_ling_gen": 0.25,
        "jian_gen": 0.2,
        "dao_gen": 0.3,
        "shen_gen": 0.4,
        "xian_gen": 0.4,
        "zhen_ling_gen": 0.1,
        "wei_ling_gen": -0.2,
        "fei_ling_gen": -0.4,
        "天灵根": 0.3,
        "变异灵根": 0.25,
        "剑灵根": 0.2,
        "道灵根": 0.3,
        "神灵根": 0.4,
        "仙灵根": 0.4,
        "真灵根": 0.1,
        "伪灵根": -0.2,
        "废灵根": -0.4,
    }

    # 境界 → 基础成功率（中英双键）
    REALM_BASE_SUCCESS = {
        "lianqi": 0.95, "zhuji": 0.85, "jiedan": 0.7,
        "yuanying": 0.5, "huashen": 0.3, "lianxu": 0.2,
        "heti": 0.1, "dujie": 0.05, "dacheng": 0.01,
        "炼气期": 0.95, "筑基期": 0.85, "结丹期": 0.7,
        "元婴期": 0.5, "化神期": 0.3, "炼虚期": 0.2,
        "合体期": 0.1, "渡劫期": 0.05, "大乘期": 0.01,
    }

    # 境界顺序（中英双键）
    BIG_REALM_ORDER = [
        "lianqi", "zhuji", "jiedan", "yuanying",
        "huashen", "lianxu", "heti", "dujie", "dacheng",
        "炼气期", "筑基期", "结丹期", "元婴期",
        "化神期", "炼虚期", "合体期", "渡劫期", "大乘期",
    ]

    def __init__(self, world: World, state: State):
        self.world = world
        self.state = state

    def attempt(self, to_realm: str) -> BreakthroughResult:
        """尝试突破到 to_realm"""
        from_realm = self.state.get("境界", "炼气期")
        # 基础成功率
        base = self.REALM_BASE_SUCCESS.get(from_realm, 0.5)
        # 灵根加成
        linggen = self.state.get("灵根", "伪灵根")
        bonus = self.SPIRIT_ROOT_BONUS.get(linggen, 0.0)
        # 丹药加成（每颗 +0.05，最多 +0.3）
        pills = self.state.attrs.get("breakthrough_pills", 0)
        pill_bonus = min(0.3, pills * 0.05)
        # 心境加成（基于 npc_favor / items / 修为）
        heart_bonus = self._calc_heart_bonus()
        # 渡劫
        tribulation_passed = self._pass_tribulation(from_realm, to_realm)
        if not tribulation_passed:
            return BreakthroughResult(
                success=False, from_realm=from_realm, to_realm=to_realm,
                tribulation_passed=False,
                lost_attrs={"境界": from_realm, "breakthrough_pills": max(0, pills - 1)},
                message=f"雷劫失败，{from_realm}跌回"
            )
        # 心魔遭遇
        heart_demon = self._encounter_heart_demon(from_realm)
        if heart_demon and not self._overcome_heart_demon(heart_demon):
            return BreakthroughResult(
                success=False, from_realm=from_realm, to_realm=to_realm,
                heart_demon_encountered=heart_demon, tribulation_passed=True,
                lost_attrs={"breakthrough_pills": max(0, pills - 1)},
                message=f"心魔『{heart_demon}』侵袭，突破失败"
            )
        # 成功率
        final = min(0.99, base + bonus + pill_bonus + heart_bonus)
        success = random.random() < final
        if not success:
            return BreakthroughResult(
                success=False, from_realm=from_realm, to_realm=to_realm,
                heart_demon_encountered=heart_demon, tribulation_passed=True,
                lost_attrs={"breakthrough_pills": max(0, pills - 1)},
                message=f"突破失败，气运不济"
            )
        return BreakthroughResult(
            success=True, from_realm=from_realm, to_realm=to_realm,
            heart_demon_encountered=heart_demon, tribulation_passed=True,
            new_attrs={"境界": to_realm, "breakthrough_pills": 0},
            message=f"突破成功：{from_realm} → {to_realm}！"
        )

    def _calc_heart_bonus(self) -> float:
        """心境加成：基于 NPC 好感度（-0.1~+0.1）"""
        if not self.state.npc_favor:
            return 0.0
        avg = sum(self.state.npc_favor.values()) / len(self.state.npc_favor)
        # 50 中性，0-100 映射到 -0.1~+0.1
        return (avg - 50) / 500.0

    def _pass_tribulation(self, from_r: str, to_r: str) -> bool:
        """天劫渡过判定"""
        # 大境界突破才需要渡劫
        if from_r not in self.BIG_REALM_ORDER or to_r not in self.BIG_REALM_ORDER:
            return True
        fi = self.BIG_REALM_ORDER.index(from_r)
        ti = self.BIG_REALM_ORDER.index(to_r)
        if ti - fi != 1:
            return True  # 跨境界直接通过
        # 渡劫概率 80%（可通过 anti_tribulation 道具提升）
        anti = self.state.attrs.get("anti_tribulation", 0)
        return random.random() < (0.8 + min(0.15, anti * 0.05))

    def _encounter_heart_demon(self, from_r: str) -> Optional[str]:
        """按境界遭遇心魔"""
        demons_by_realm = {
            "lianqi": ["qie_mo", "you_zi_mo"],
            "zhuji": ["qie_mo", "you_zi_mo", "pan_ju_mo"],
            "jiedan": ["tan_mo", "zhi_nian_mo", "yu_mo", "ai_mo"],
            "yuanying": ["chen_mo", "tan_mo", "ai_guo_mo"],
            "huashen": ["chi_mo", "wu_mo", "sheng_si_mo"],
            "lianxu": ["chi_mo", "wu_mo"],
            "heti": ["e_mo", "wu_mo"],
            "dujie": ["e_mo"],
        }
        pool = demons_by_realm.get(from_r, [])
        if not pool or random.random() > 0.5:
            return None
        return random.choice(pool)

    def _overcome_heart_demon(self, demon: str) -> bool:
        """心魔对抗（基于状态）"""
        # 简单判定：每 3 个 NPC 好感 ≥70 提升 20% 几率
        good_npcs = sum(1 for f in self.state.npc_favor.values() if f >= 70)
        base = 0.5 + good_npcs * 0.1
        return random.random() < base


# ────────────────────────────────────────────────────────
# 6. 战斗系统（v2.8 新增）
# ────────────────────────────────────────────────────────

@dataclass
class CombatTurn:
    """单回合结果"""
    attacker: str  # "player" / "enemy"
    action: str    # "attack" / "defend" / "skill" / "flee"
    damage: int
    crit: bool
    message: str


@dataclass
class CombatResult:
    """完整战斗结果"""
    enemy_id: str
    enemy_name: str
    victory: bool
    fled: bool
    turns: List[CombatTurn]
    player_hp: int
    enemy_hp: int
    rewards: Dict[str, Any] = field(default_factory=dict)  # {灵石: X, item: "Y"}


class CombatSystem:
    """回合制战斗系统

    玩家 vs 怪物（来自 monsters.yaml），
    基于境界差 + 法器 + 灵根计算伤害。
    """

    # 境界（中→英）→ 基础血量
    REALM_HP = {
        # 中文名
        "炼气期": 100, "筑基期": 200, "结丹期": 500,
        "元婴期": 1000, "化神期": 2000, "炼虚期": 5000,
        "合体期": 10000, "渡劫期": 20000, "大乘期": 50000,
        # 英文 id
        "lianqi": 100, "zhuji": 200, "jiedan": 500,
        "yuanying": 1000, "huashen": 2000, "lianxu": 5000,
        "heti": 10000, "dujie": 20000, "dacheng": 50000,
    }

    # 境界 → 基础攻击
    REALM_ATK = {
        "炼气期": 20, "筑基期": 50, "结丹期": 120,
        "元婴期": 300, "化神期": 800, "炼虚期": 2000,
        "合体期": 5000, "渡劫期": 12000, "大乘期": 30000,
        "lianqi": 20, "zhuji": 50, "jiedan": 120,
        "yuanying": 300, "huashen": 800, "lianxu": 2000,
        "heti": 5000, "dujie": 12000, "dacheng": 30000,
    }

    def __init__(self, world: World, state: State, enemy_id: str):
        self.world = world
        self.state = state
        self.enemy_id = enemy_id
        self.enemy = world.find_by_id("monsters", enemy_id) or {
            "id": enemy_id, "name": enemy_id,
            "grade": "普通妖兽", "attribute": "wu",
        }
        self.player_hp = self.REALM_HP.get(state.get("境界", "lianqi"), 100)
        self.player_atk = self.REALM_ATK.get(state.get("境界", "lianqi"), 20)
        # 怪物血量与攻击（按 grade 推算）
        grade_map = {
            "普通妖兽": (50, 10), "灵兽": (80, 15), "妖王": (300, 60),
            "妖圣": (1000, 200), "圣兽": (2000, 400), "上古凶兽": (5000, 1000),
        }
        ehp, eatk = grade_map.get(self.enemy.get("grade", "普通妖兽"), (50, 10))
        self.enemy_hp = ehp
        self.enemy_atk = eatk
        self.turns: List[CombatTurn] = []
        self.ended = False

    def player_turn(self, action: str) -> CombatTurn:
        """玩家一回合"""
        if self.ended:
            return CombatTurn("player", action, 0, False, "战斗已结束")
        if action == "flee":
            self.ended = True
            turn = CombatTurn("player", "flee", 0, False, "你选择逃跑")
            self.turns.append(turn)
            return turn
        if action == "defend":
            self.enemy_atk = max(1, int(self.enemy_atk * 0.5))  # 下回合减伤
            turn = CombatTurn("player", "defend", 0, False, "你严守防御")
            self.turns.append(turn)
            return turn
        # attack / skill
        crit = random.random() < 0.15
        skill_mult = 1.5 if action == "skill" else 1.0
        dmg = int(self.player_atk * skill_mult * (2 if crit else 1))
        self.enemy_hp = max(0, self.enemy_hp - dmg)
        turn = CombatTurn(
            "player", action, dmg, crit,
            f"你{'施法' if action == 'skill' else '攻击'}造成 {dmg} 伤害{'（暴击）' if crit else ''}"
        )
        self.turns.append(turn)
        if self.enemy_hp == 0:
            self.ended = True
        return turn

    def enemy_turn(self) -> Optional[CombatTurn]:
        """敌人一回合"""
        if self.ended:
            return None
        crit = random.random() < 0.1
        dmg = int(self.enemy_atk * (2 if crit else 1))
        self.player_hp = max(0, self.player_hp - dmg)
        turn = CombatTurn(
            "enemy", "attack", dmg, crit,
            f"{self.enemy['name']}攻击你造成 {dmg} 伤害{'（暴击）' if crit else ''}"
        )
        self.turns.append(turn)
        if self.player_hp == 0:
            self.ended = True
        return turn

    def is_over(self) -> bool:
        return self.ended

    def victory(self) -> bool:
        return self.ended and self.enemy_hp == 0 and self.player_hp > 0

    def fled(self) -> bool:
        return self.ended and self.player_hp > 0 and self.enemy_hp > 0

    def result(self) -> CombatResult:
        rewards = {}
        if self.victory():
            # 按 grade 给奖励
            grade = self.enemy.get("grade", "普通妖兽")
            reward_map = {
                "普通妖兽": {"灵石": 5, "item": "妖丹碎"},
                "灵兽": {"灵石": 15, "item": "灵兽角"},
                "妖王": {"灵石": 50, "item": "妖王内丹"},
                "妖圣": {"灵石": 200, "item": "妖圣精血"},
                "圣兽": {"灵石": 1000, "item": "圣兽羽"},
                "上古凶兽": {"灵石": 5000, "item": "凶兽魂"},
            }
            rewards = reward_map.get(grade, {"灵石": 5})
        return CombatResult(
            enemy_id=self.enemy_id, enemy_name=self.enemy.get("name", self.enemy_id),
            victory=self.victory(), fled=self.fled(), turns=self.turns,
            player_hp=self.player_hp, enemy_hp=self.enemy_hp, rewards=rewards,
        )


# ────────────────────────────────────────────────────────
# 7. 随机事件（v2.8 新增）
# ────────────────────────────────────────────────────────

@dataclass
class RandomEvent:
    """随机事件结果"""
    event_type: str  # "encounter" / "treasure" / "tribulation" / "npc" / "weather"
    title: str
    description: str
    rewards: Dict[str, Any] = field(default_factory=dict)  # 获得
    costs: Dict[str, Any] = field(default_factory=dict)    # 失去
    choices: List[dict] = field(default_factory=list)      # 可选后续


class RandomEventEngine:
    """随机事件生成器

    根据玩家境界、灵根、所在界面生成随机事件。
    """

    EVENT_POOL = {
        "encounter": [
            {"title": "偶遇妖兽", "desc": "前路遇到一只 {grade}{attribute}妖兽", "rewards": {"灵石": 5}, "choices": ["战斗", "绕道", "无视"]},
            {"title": "山间遇险", "desc": "在山间遇到一只饥饿的狼妖", "rewards": {}, "costs": {"声望": -1}, "choices": ["战斗", "逃跑"]},
            {"title": "发现奇兽", "desc": "偶遇一只灵智初开的灵兽", "rewards": {"item": "灵兽蛋"}, "choices": ["收养", "放生", "售卖"]},
        ],
        "treasure": [
            {"title": "发现灵草", "desc": "在山崖下发现一株 {grade}灵草", "rewards": {"item": "灵草"}, "choices": ["采摘", "研究", "离开"]},
            {"title": "古人洞府", "desc": "误入一处古人洞府，发现 {item}", "rewards": {"灵石": 100, "item": "古法宝"}, "choices": ["取走", "不动", "毁掉"]},
            {"title": "天降灵石雨", "desc": "天上突然降下灵石雨", "rewards": {"灵石": 200}, "choices": ["拾取", "观望"]},
        ],
        "tribulation": [
            {"title": "突降雷劫", "desc": "天空骤然黑云密布，雷劫将至", "costs": {"breakthrough_pills": -1}, "choices": ["应劫", "逃避"]},
            {"title": "心魔试炼", "desc": "心魔忽然来袭", "costs": {"声望": -2}, "choices": ["坚定", "动摇"]},
        ],
        "npc": [
            {"title": "偶遇散修", "desc": "路上遇到一位 {npc_kind} 散修", "rewards": {"favor": {"散修": 5}}, "choices": ["结交", "无视"]},
            {"title": "仙人指路", "desc": "山中遇一白胡子老者指点", "rewards": {"声望": 5}, "choices": ["拜谢", "询问"]},
        ],
        "weather": [
            {"title": "天降甘霖", "desc": "天降甘霖，万物滋润", "rewards": {"声望": 1}, "choices": ["享受"]},
            {"title": "风暴来袭", "desc": "突遇灵气风暴", "costs": {"灵石": -10}, "choices": ["躲避", "硬抗"]},
        ],
    }

    def __init__(self, world: World, state: State, seed: Optional[int] = None):
        self.world = world
        self.state = state
        if seed is not None:
            random.seed(seed)

    def trigger(self, event_type: Optional[str] = None) -> RandomEvent:
        """触发一个随机事件。event_type=None 时随机选。"""
        if event_type is None:
            event_type = random.choice(list(self.EVENT_POOL.keys()))
        pool = self.EVENT_POOL.get(event_type, [])
        if not pool:
            return RandomEvent(event_type, "无事件", "无事发生")
        ev = random.choice(pool)
        # 简单模板替换
        realm = self.state.get("境界", "lianqi")
        linggen = self.state.get("灵根", "wei_ling_gen")
        desc = ev["desc"].format(
            grade=random.choice(["百", "千", "万", "十万"]),
            attribute=random.choice(["金", "木", "水", "火", "土", "雷", "冰", "风"]),
            npc_kind=random.choice(["炼气", "筑基", "结丹"]),
            item=random.choice(["古剑", "古镜", "古玉简", "古宝"]),
        )
        return RandomEvent(
            event_type=event_type,
            title=ev["title"],
            description=desc,
            rewards=ev.get("rewards", {}),
            costs=ev.get("costs", {}),
            choices=ev.get("choices", []),
        )

    def apply(self, event: RandomEvent) -> Dict[str, Any]:
        """应用事件到状态，返回状态变更"""
        changes = {"rewards": dict(event.rewards), "costs": dict(event.costs)}
        for k, v in event.rewards.items():
            if k == "item":
                self.state.add_item(v)
            elif k == "favor" and isinstance(v, dict):
                for npc, delta in v.items():
                    self.state.modify_npc_favor(npc, delta)
            else:
                self.state.incr(k, v)
        for k, v in event.costs.items():
            if k == "breakthrough_pills":
                self.state.attrs["breakthrough_pills"] = max(0, self.state.attrs.get("breakthrough_pills", 0) + v)
            elif k == "favor" and isinstance(v, dict):
                for npc, delta in v.items():
                    self.state.modify_npc_favor(npc, delta)
            else:
                self.state.incr(k, v)
        return changes


# ────────────────────────────────────────────────────────
# 8. 剧本解析（DSL）
# ────────────────────────────────────────────────────────

NODE_HEADER = re.compile(r"^##\s+节点\s+(\S+)(?:\s+\((\S+)\))?\s*$", re.MULTILINE)
SECTION_HEADER = re.compile(r"^(type|text|data|next|refs|choices):\s*(.*)$")


def _split_front_matter(text: str) -> Tuple[dict, str]:
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


def _split_nodes(body: str) -> Dict[str, str]:
    """按 `## 节点 <id> [(type)]` 切分"""
    parts: Dict[str, str] = {}
    matches = list(NODE_HEADER.finditer(body))
    for i, m in enumerate(matches):
        nid = m.group(1)
        # 节点标题里 (ending) / (scene) 标识，可被节点内 type: 字段覆盖
        type_hint = m.group(2)  # None / "scene" / "ending"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        parts[nid] = (type_hint, body[start:end].strip("\n"))
    return parts


def _parse_node(nid: str, type_hint: Optional[str], raw: str) -> Node:
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


def _collect_indented(lines: List[str], start: int) -> Tuple[str, int]:
    """从 start 开始收集缩进行（>= 2 空格），遇到非缩进/EOF 停止"""
    buf: List[str] = []
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

def main(argv: Optional[List[str]] = None) -> int:
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
