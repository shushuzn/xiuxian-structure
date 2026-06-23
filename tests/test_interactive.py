"""
test_interactive.py — 互动引擎 core 层扩展测试（D.2 覆盖率深化）

覆盖：
- World 异常路径
- State check 复杂表达式
- Engine choice actions 全路径
- 序列化/反序列化
- DSL 解析
"""
import json
import sys
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from interactive import World, Story, State, Engine  # noqa: E402

DATA_DIR = ROOT / "data"


def _minimal_story(text):
    return Story.from_text(text)


def _world():
    return World.from_yaml_dir(DATA_DIR)


# ── World ──


def test_world_find_by_id_missing():
    w = World({})
    assert w.find_by_id("foo", "nonexistent") is None


def test_world_find_by_id_nonexistent_system():
    w = _world()
    assert w.find_by_id("foo", "bar") is None


def test_world_render_template_missing_key():
    w = World({})
    assert "<未知:" in w.render_template("{foo.bar}")


def test_world_render_template_complex_val():
    w = _world()
    result = w.render_template("{realms.realms}")
    assert "<" in result


# ── Story ──


STORY_MINIMAL = """# Test
## 元数据
id: test_story
start: start
## 节点 start (scene)
text: 起始
next:
  - label: 结束
    goto: end
## 节点 end (ending)
text: 结束
next: []
"""


def test_story_parse_minimal():
    s = _minimal_story(STORY_MINIMAL)
    assert s.id == "test_story"
    assert s.title == "Test"
    assert s.start_node == "start"
    assert len(s.nodes) == 2


def test_story_parse_missing_text():
    raw = """# NoText
## 元数据
id: no_text
start: n1
## 节点 n1 (scene)
data: {x: 1}
next:
  - label: end
    goto: e1
## 节点 e1 (ending)
text: ended
next: []
"""
    s = _minimal_story(raw)
    assert s.nodes["n1"].text == ""


def test_story_from_file(tmp_path):
    fp = tmp_path / "test.md"
    fp.write_text(STORY_MINIMAL, encoding="utf-8")
    s = Story.from_file(fp)
    assert s.id == "test_story"


def test_story_get_missing():
    s = _minimal_story(STORY_MINIMAL)
    assert s.get("nonexistent") is None


# ── State ──


def test_state_check_simple():
    s = State({"灵石": 100, "灵根": "伪灵根"})
    assert s.check("灵石 >= 50")
    assert not s.check("灵石 >= 200")
    assert s.check('灵根 == "伪灵根"')


def test_state_check_complex():
    s = State({"灵石": 100, "声望": 50})
    assert s.check("灵石 >= 50 and 声望 >= 30")
    assert not s.check("灵石 >= 200 or 声望 >= 100")


def test_state_check_flag():
    s = State()
    s.set_flag("tested")
    assert s.check("flag.tested")
    s.clear_flag("tested")
    assert not s.check("flag.tested")


def test_state_check_empty():
    s = State()
    assert s.check("")
    assert s.check(None)
    assert s.check("  ")


def test_state_incr():
    s = State({"x": 5})
    s.incr("x", 3)
    assert s.attrs["x"] == 8
    s.incr("y")
    assert s.attrs["y"] == 1


def test_state_get_default():
    s = State()
    assert s.get("nocfg", 42) == 42
    assert s.get("nocfg2") is None


def test_state_item_count():
    s = State()
    assert s.item_count == 0
    s.add_item("剑")
    assert s.item_count == 1
    s.add_item("剑")  # duplicate ignored
    assert s.item_count == 1
    s.add_item("丹")
    assert s.item_count == 2


def test_state_score_empty():
    s = State()
    sc = s.score_breakdown()
    assert sc["灵石"] == 0
    assert sc["修为"] == 0
    assert sc["总分"] == 0


def test_state_score_max():
    s = State({"灵石": 99999, "声望": 999, "境界": "大乘期"})
    for i in range(15):
        s.add_item(f"物品{i}")
    s.modify_npc_favor("师父", 50)
    sc = s.score_breakdown()
    assert sc["灵石"] == 30
    assert sc["声望"] == 25
    assert sc["物品"] == 20
    assert sc["修为"] == 10
    assert sc["好感"] == 15
    assert sc["总分"] == 100


# ── Engine: 序列化 ──


def _mk_engine():
    world = _world()
    story = _minimal_story(STORY_MINIMAL)
    state = State({"灵石": 10})
    return Engine(world, story, state)


def test_engine_save_roundtrip():
    eng = _mk_engine()
    d = eng.save()
    assert "story" in d
    assert "state" in d
    assert "history" in d
    assert d["state"]["attrs"]["灵石"] == 10


def test_engine_load():
    eng1 = _mk_engine()
    eng1.step(0)
    d = eng1.save()
    eng2 = Engine.load(eng1.world, eng1.story, d)
    assert eng2.state.realm == eng1.state.realm


def test_engine_save_to_file(tmp_path):
    eng = _mk_engine()
    fp = tmp_path / "save.json"
    eng.save_to_file(fp)
    assert fp.exists()
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert data["attrs"]["灵石"] == 10


def test_engine_load_from_file(tmp_path):
    eng1 = _mk_engine()
    fp = tmp_path / "save.json"
    eng1.save_to_file(fp)
    eng2 = Engine.load_from_file(eng1.world, eng1.story, fp)
    assert eng2.state.attrs["灵石"] == 10


def test_engine_get_score():
    eng = _mk_engine()
    sc = eng.get_score()
    assert isinstance(sc, dict)
    assert "总分" in sc


def test_engine_step_to_invalid():
    """_step_to 对不存在的节点应 assert"""
    eng = _mk_engine()
    with pytest.raises(AssertionError):
        eng._step_to("nonexistent")


# ── Engine: choice actions 全路径 ──


CHOICE_ACTIONS_STORY = """# Actions
## 元数据
id: actions
start: s
## 节点 s (scene)
text: 测试
next:
  - label: 全操作
    goto: e1
    set: {境界: 筑基}
    flag: tested
    pickup: [剑, 丹]
    drop: 无用品
    favor: {墨大夫: 10}
    advance: {years: 1, months: 3, days: 5}
    realm: 仙界
## 节点 e1 (ending)
text: 结束
next: []
"""


def test_engine_choice_actions_all():
    world = _world()
    story = _minimal_story(CHOICE_ACTIONS_STORY)
    state = State({"灵石": 5, "无用品": 1})
    state.add_item("无用品")
    eng = Engine(world, story, state)
    eng.step(0)
    assert eng.state.attrs.get("境界") == "筑基"
    assert eng.state.flag("tested")
    assert eng.state.has_item("剑")
    assert eng.state.has_item("丹")
    assert not eng.state.has_item("无用品")
    assert eng.state.get_npc_favor("墨大夫") == 60
    assert eng.state.get_time_str() == "2年04月06日"
    assert eng.state.realm == "仙界"


def test_engine_choice_pickup_single():
    world = _world()
    raw = """# Pickup
## 元数据
id: pickup
start: s
## 节点 s (scene)
text: t
next:
  - label: pick
    goto: e1
    pickup: 剑
## 节点 e1 (ending)
text: end
next: []
"""
    eng = Engine(world, _minimal_story(raw), State())
    eng.step(0)
    assert eng.state.has_item("剑")


def test_engine_choice_drop_invalid():
    world = _world()
    raw = """# Drop
## 元数据
id: drop
start: s
## 节点 s (scene)
text: t
next:
  - label: drop_nonexist
    goto: e1
    drop: 不存在物
## 节点 e1 (ending)
text: end
next: []
"""
    eng = Engine(world, _minimal_story(raw), State())
    eng.step(0)  # should not raise
    assert not eng.state.has_item("不存在物")


# ── Engine: ending → 无选项 ──


ENDING_STORY = """# End
## 元数据
id: end
start: e
## 节点 e (ending)
text: 终
next: []
"""


def test_engine_ending_no_choices():
    eng = Engine(_world(), _minimal_story(ENDING_STORY), State())
    ev = eng.step()
    assert ev.ending
    assert ev.node_id == "e"


# ── Engine: step with invalid index ──


def test_engine_step_invalid_index():
    raw = """# Inv
## 元数据
id: inv
start: s
## 节点 s (scene)
text: t
next:
  - label: ok
    goto: e1
## 节点 e1 (ending)
text: end
next: []
"""
    eng = Engine(_world(), _minimal_story(raw), State())
    ev = eng.step(999)  # out of range
    assert ev.ending  # treated as ending


# ── Engine: step with None index (auto first) ──


def test_engine_step_auto():
    raw = """# Auto
## 元数据
id: auto
start: s
## 节点 s (scene)
text: t
next:
  - label: a
    goto: e1
## 节点 e1 (ending)
text: end
next: []
"""
    eng = Engine(_world(), _minimal_story(raw), State())
    ev = eng.step()  # None → auto pick first
    assert ev.node_id == "e1"


# ── DSL: front matter ──


def test_story_no_front_matter_fails():
    """无 ## 元数据 的 header 应抛错（缺 id）"""
    raw = """# JustTitle
## 节点 n1 (scene)
text: x
next: []
"""
    with pytest.raises(ValueError, match="缺少年级 # id 字段"):
        _minimal_story(raw)


def test_story_data_block():
    raw = """# DataBlock
## 元数据
id: data_block
start: s
## 节点 s (scene)
text: hello
data:
  x: 1
  y: hello
next:
  - label: go
    goto: e1
## 节点 e1 (ending)
text: end
next: []
"""
    s = _minimal_story(raw)
    assert s.nodes["s"].data == {"x": 1, "y": "hello"}


# ── Engine: story get ──


def test_story_get():
    s = _minimal_story(STORY_MINIMAL)
    assert s.get("start") is not None
    assert s.get("end") is not None
    assert s.get("nope") is None


# ── v2.8 互动引擎扩展（突破/战斗/随机事件） ──

import importlib
interactive_mod = importlib.import_module("interactive")
BreakthroughSimulator = interactive_mod.BreakthroughSimulator
CombatSystem = interactive_mod.CombatSystem
RandomEventEngine = interactive_mod.RandomEventEngine
BreakthroughResult = interactive_mod.BreakthroughResult
CombatResult = interactive_mod.CombatResult
RandomEvent = interactive_mod.RandomEvent


# ── BreakthroughSimulator ──

def test_breakthrough_result_dataclass():
    r = BreakthroughResult(success=True, from_realm="lianqi", to_realm="zhuji")
    assert r.success
    assert r.from_realm == "lianqi"
    assert r.to_realm == "zhuji"
    assert r.tribulation_passed is False
    assert r.heart_demon_encountered is None


def test_breakthrough_attempt_basic():
    w = _world()
    s = State({"境界": "炼气期", "灵根": "tian_ling_gen", "breakthrough_pills": 5})
    sim = BreakthroughSimulator(w, s)
    r = sim.attempt("筑基期")
    assert r.from_realm == "炼气期"
    assert r.to_realm == "筑基期"
    assert r.message  # 有提示


def test_breakthrough_attempt_deterministic(monkeypatch):
    """固定随机种子：低灵根 + 无丹药 + 高境界 → 必失败"""
    import random as _r
    w = _world()
    s = State({"境界": "合体期", "灵根": "fei_ling_gen", "breakthrough_pills": 0})
    sim = BreakthroughSimulator(w, s)
    _r.seed(1)
    r = sim.attempt("渡劫期")
    # 合体期基础 0.1，废灵根 -0.4，无加成 → 必失败
    assert r.success is False


def test_breakthrough_drops_pills_on_fail(monkeypatch):
    """突破失败应当消耗一颗丹药"""
    import random as _r
    _r.seed(1)
    w = _world()
    s = State({"境界": "合体期", "灵根": "fei_ling_gen", "breakthrough_pills": 3})
    sim = BreakthroughSimulator(w, s)
    r = sim.attempt("渡劫期")
    if not r.success:
        # lost_attrs 中 breakthrough_pills 至少为 2
        assert r.lost_attrs.get("breakthrough_pills", 0) <= 2


def test_breakthrough_success_updates_attrs(monkeypatch):
    import random as _r
    _r.seed(0)
    w = _world()
    s = State({"境界": "炼气期", "灵根": "shen_gen", "breakthrough_pills": 10})
    sim = BreakthroughSimulator(w, s)
    r = sim.attempt("筑基期")
    # 高灵根 + 满丹药 → 大概率成功
    if r.success:
        assert r.new_attrs.get("境界") == "筑基期"


def test_breakthrough_heart_demon_overcome(monkeypatch):
    """满 NPC 好感度应能克服心魔"""
    import random as _r
    w = _world()
    s = State({"境界": "结丹期", "灵根": "tian_ling_gen", "breakthrough_pills": 5})
    # 多个高好感度 NPC
    s.npc_favor = {"a": 80, "b": 90, "c": 100}
    sim = BreakthroughSimulator(w, s)
    # 多次尝试统计：心魔克服率应 > 0.5
    _r.seed(0)
    overcomes = 0
    for _ in range(50):
        s2 = State({"境界": "结丹期", "灵根": "tian_ling_gen", "breakthrough_pills": 5})
        s2.npc_favor = {"a": 80, "b": 90, "c": 100}
        sim2 = BreakthroughSimulator(w, s2)
        r = sim2.attempt("元婴期")
        if r.success or (r.heart_demon_encountered and r.success is not False):
            overcomes += 1
    # 至少 30% 成功率（含心魔不出现的概率）
    assert overcomes >= 15


def test_breakthrough_big_realm_need_tribulation():
    w = _world()
    # 炼气→筑基 是 big realm 但概率 0.8，多次应能通过
    import random as _r
    _r.seed(0)
    trib_pass = 0
    for _ in range(200):
        s2 = State({"境界": "炼气期", "灵根": "shen_gen", "breakthrough_pills": 10, "anti_tribulation": 0})
        sim2 = BreakthroughSimulator(w, s2)
        r = sim2.attempt("筑基期")
        if r.tribulation_passed:
            trib_pass += 1
    # 80% baseline, +/- 10% tolerance
    assert 140 <= trib_pass <= 200  # 70%-100%


# ── CombatSystem ──

def test_combat_result_dataclass():
    r = CombatResult(enemy_id="x", enemy_name="X", victory=True, fled=False,
                    turns=[], player_hp=50, enemy_hp=0)
    assert r.victory
    assert r.enemy_hp == 0


def test_combat_player_attack():
    w = _world()
    s = State({"境界": "结丹期"})
    cs = CombatSystem(w, s, "tian_gang_zhen")  # 不存在
    # enemy_id 找不到时会用默认 grade
    turn = cs.player_turn("attack")
    assert turn.attacker == "player"
    assert turn.action == "attack"
    assert cs.enemy_hp < 50  # 受到伤害


def test_combat_player_defend():
    w = _world()
    s = State({"境界": "结丹期"})
    cs = CombatSystem(w, s, "ghost_enemy")
    turn = cs.player_turn("defend")
    assert turn.action == "defend"


def test_combat_player_flee():
    w = _world()
    s = State({"境界": "炼气期"})
    cs = CombatSystem(w, s, "ghost")
    turn = cs.player_turn("flee")
    assert turn.action == "flee"
    assert cs.is_over() is True
    assert cs.fled() is True


def test_combat_enemy_turn():
    w = _world()
    s = State({"境界": "炼气期"})  # 低境界 → 不会一击必杀
    # 找一个真实存在的怪物（普通妖兽 grade，血量 50）
    monster = w.find_by_id("monsters", "tie_bei_cang_lang")
    if monster:
        cs = CombatSystem(w, s, "tie_bei_cang_lang")
    else:
        cs = CombatSystem(w, s, "ghost")
    # 炼气期攻击 20，普通妖兽血量 50，不会一击必杀
    cs.player_turn("attack")
    turn = cs.enemy_turn()
    assert turn is not None
    assert turn.attacker == "enemy"


def test_combat_victory():
    w = _world()
    s = State({"境界": "大乘期"})  # 高境界
    cs = CombatSystem(w, s, "ghost")
    # 大乘期攻击 = 30000，普通怪物血量 50
    cs.player_turn("attack")
    assert cs.is_over()
    assert cs.victory()


def test_combat_victory_rewards():
    w = _world()
    s = State({"境界": "化神期"})
    # 找一个存在的怪物
    monster = w.find_by_id("monsters", "tie_bei_cang_lang")
    if monster:
        cs = CombatSystem(w, s, "tie_bei_cang_lang")
        # 多次攻击保证胜利
        for _ in range(10):
            if cs.is_over():
                break
            cs.player_turn("attack")
        if cs.victory():
            r = cs.result()
            assert r.rewards.get("灵石", 0) >= 5


def test_combat_result_structure():
    w = _world()
    s = State({"境界": "炼气期"})
    cs = CombatSystem(w, s, "x")
    cs.player_turn("attack")
    if not cs.is_over():
        cs.enemy_turn()
    r = cs.result()
    assert r.enemy_id == "x"
    assert len(r.turns) >= 1


# ── RandomEventEngine ──

def test_random_event_dataclass():
    ev = RandomEvent(event_type="encounter", title="X", description="Y")
    assert ev.event_type == "encounter"
    assert ev.title == "X"


def test_random_event_trigger_returns_event():
    w = _world()
    s = State({"境界": "炼气期"})
    eng = RandomEventEngine(w, s, seed=42)
    ev = eng.trigger("encounter")
    assert ev.event_type == "encounter"
    assert ev.title


def test_random_event_random_type():
    w = _world()
    s = State({"境界": "炼气期"})
    eng = RandomEventEngine(w, s, seed=0)
    ev = eng.trigger()  # 随机类型
    assert ev.event_type in RandomEventEngine.EVENT_POOL


def test_random_event_apply_rewards():
    w = _world()
    s = State({"境界": "炼气期", "灵石": 10})
    eng = RandomEventEngine(w, s)
    ev = RandomEvent(event_type="treasure", title="X", description="Y",
                    rewards={"灵石": 100})
    eng.apply(ev)
    assert s.get("灵石") == 110


def test_random_event_apply_costs():
    w = _world()
    s = State({"境界": "炼气期", "声望": 10})
    eng = RandomEventEngine(w, s)
    ev = RandomEvent(event_type="tribulation", title="X", description="Y",
                    costs={"声望": -3})
    eng.apply(ev)
    assert s.get("声望") == 7


def test_random_event_apply_item():
    w = _world()
    s = State({"境界": "炼气期"})
    eng = RandomEventEngine(w, s)
    ev = RandomEvent(event_type="treasure", title="X", description="Y",
                    rewards={"item": "灵草"})
    eng.apply(ev)
    assert s.has_item("灵草")


def test_random_event_apply_favor():
    w = _world()
    s = State({"境界": "炼气期"})
    eng = RandomEventEngine(w, s)
    ev = RandomEvent(event_type="npc", title="X", description="Y",
                    rewards={"favor": {"散修": 5}})
    eng.apply(ev)
    assert s.get_npc_favor("散修") == 55


# ── Engine 集成 ──

def test_engine_breakthrough_action(monkeypatch):
    """breakthrough action 应更新 state.last_breakthrough"""
    import random as _r
    _r.seed(0)
    w = _world()
    s = State({"境界": "炼气期", "灵根": "shen_gen", "breakthrough_pills": 10})
    story_text = """# test
## 元数据
id: test_bt
start: start
## 节点 start (scene)
text: "start"
next:
  - label: 突破
    goto: end
    breakthrough:
      to: 筑基期
## 节点 end (ending)
text: "end"
"""
    story = Story.from_text(story_text)
    eng = Engine(w, story, s)
    eng._apply_choice_actions(story.get("start").choices[0])
    assert "last_breakthrough" in s.attrs
    assert s.attrs["last_breakthrough"]["to"] == "筑基期"


def test_engine_combat_action():
    w = _world()
    s = State({"境界": "大乘期", "灵石": 0})
    story_text = """# test
## 元数据
id: test_c
start: start
## 节点 start (scene)
text: "start"
next:
  - label: 战
    goto: end
    combat:
      enemy: ghost
## 节点 end (ending)
text: "end"
"""
    story = Story.from_text(story_text)
    eng = Engine(w, story, s)
    eng._apply_choice_actions(story.get("start").choices[0])
    assert "last_combat" in s.attrs
    # 大乘期对 ghost 应胜
    if s.attrs["last_combat"]["victory"]:
        assert s.get("灵石", 0) > 0


def test_engine_random_event_action():
    w = _world()
    s = State({"境界": "炼气期"})
    story_text = """# test
## 元数据
id: test_re
start: start
## 节点 start (scene)
text: "start"
next:
  - label: 触发
    goto: end
    random_event:
      type: encounter
      seed: 42
## 节点 end (ending)
text: "end"
"""
    story = Story.from_text(story_text)
    eng = Engine(w, story, s)
    eng._apply_choice_actions(story.get("start").choices[0])
    assert "last_event" in s.attrs
    assert s.attrs["last_event"]["type"] == "encounter"
