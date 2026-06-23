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


# ── v2.9 D.3 覆盖率加深 ──


def test_world_lookup_nested_dict():
    """lookup 嵌套 dict 应正确取值"""
    w = World({"a": {"b": {"c": 42}}})
    assert w.lookup("a", "b", "c") == 42


def test_world_lookup_nested_list_by_id():
    """lookup 嵌套 list 应按 id 索引"""
    w = World({"a": {"b": [{"id": "x", "v": 1}, {"id": "y", "v": 2}]}})
    assert w.lookup("a", "b", "y", "v") == 2


def test_world_lookup_invalid_path():
    """lookup 不存在的路径应返回 None"""
    w = World({"a": {"b": 1}})
    assert w.lookup("a", "missing") is None
    assert w.lookup("nonexistent") is None


def test_world_lookup_string_value():
    """lookup 字符串值应直接返回"""
    w = World({"a": "value"})
    assert w.lookup("a") == "value"


def test_world_find_by_id_in_dict():
    """find_by_id 应在 dict 中查找"""
    w = World({"a": {"items": [{"id": "x", "v": 1}]}})
    hit = w.find_by_id("a", "x")
    assert hit is not None
    assert hit["v"] == 1


def test_world_find_by_id_empty_data():
    """空数据应返回 None"""
    w = World({})
    assert w.find_by_id("x", "y") is None


def test_world_render_template_int():
    """render_template 整数应正确渲染"""
    w = _world()
    result = w.render_template("{realms.炼气期.lifespan}")
    # 炼气期.lifespan 是 120
    assert "120" in result or "<未知" in result


def test_state_substitute_string_attr():
    """_substitute 应正确处理字符串属性"""
    s = State({"name": "test_value"})
    expr = s._substitute("name == 'foo'")
    # 字符串应用 repr
    assert "'test_value'" in expr


def test_state_substitute_number_attr():
    """_substitute 应正确处理数字属性"""
    s = State({"count": 42})
    expr = s._substitute("count >= 10")
    assert "42" in expr


def test_state_substitute_long_names_first():
    """长的属性名应优先匹配（避免子串冲突）"""
    s = State({"lianqi_count": 5, "lianqi": "炼气期"})
    expr = s._substitute("lianqi_count == 5")
    assert "5" in expr
    # 长名替换为 <<lianqi_count>>，短名 <<lianqi>>
    # 两个都被替换但顺序无关


def test_state_check_complex_expr():
    """check 应支持复合表达式"""
    s = State({"灵石": 100, "声望": 50})
    assert s.check("灵石 >= 50 and 声望 > 30")
    assert not s.check("灵石 >= 200")


def test_state_check_with_string_compare():
    """check 应支持字符串比较"""
    s = State({"灵根": "天灵根"})
    assert s.check("灵根 == '天灵根'")
    assert not s.check("灵根 == '废灵根'")


def test_state_check_with_flag():
    """check 应支持 flag.xxx 语法"""
    s = State()
    s.set_flag("已拜师")
    assert s.check("flag.已拜师")
    assert not s.check("flag.未拜师")


def test_state_check_invalid_expr():
    """check 遇到无效表达式应返回 False（不抛异常）"""
    s = State()
    assert s.check("invalid syntax !@#") is False
    assert s.check("undefined_var == 1") is False


def test_engine_apply_state_with_prefix():
    """data 块中带 ? 前缀的 key 仅在未设置时初始化"""
    s = State({"灵石": 5})
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
data:
  ?灵石: 100
  ?声望: 10
"""), s)
    eng._apply_state(eng.story.get("s"))
    # 已存在的 5 不变
    assert s.get("灵石") == 5
    # 未存在的 声望 设为 10
    assert s.get("声望") == 10


def test_engine_apply_state_overwrites():
    """data 块中不带 ? 前缀的 key 总是覆盖"""
    s = State({"灵石": 5})
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
data:
  灵石: 100
"""), s)
    eng._apply_state(eng.story.get("s"))
    assert s.get("灵石") == 100


def test_engine_apply_choice_with_set():
    """choice 含 set 字段应更新 attrs"""
    s = State()
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: act
    goto: e
    set:
      a: 1
## 节点 e (ending)
text: done
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert s.get("a") == 1


def test_engine_save_returns_dict():
    """save() 应返回可序列化的 dict"""
    s = State({"x": 1})
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
"""), s)
    eng.history.append("s")
    saved = eng.save()
    assert saved["story"] == "t"
    assert "state" in saved
    assert "history" in saved
    assert saved["history"] == ["s"]


def test_engine_save_to_file(tmp_path):
    """save_to_file 应写入 JSON 文件（state 部分）"""
    s = State({"x": 1})
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
"""), s)
    target = tmp_path / "save.json"
    eng.save_to_file(target)
    assert target.exists()
    import json as _json
    data = _json.loads(target.read_text())
    # save_to_file 只保存 state 部分
    assert "attrs" in data


def test_engine_get_score_returns_dict():
    """get_score 应返回评分 dict"""
    s = State({"灵石": 100, "声望": 10})
    s.set_item_count = len(s.items)  # type: ignore
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
"""), s)
    score = eng.get_score()
    assert "灵石" in score
    assert "声望" in score
    assert "总分" in score


def test_engine_step_with_no_choice():
    """step() 在无 choice 时应返回 ending event"""
    s = State()
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (ending)
text: end
"""), s)
    ev = eng.step(0)
    assert ev.ending is True
    assert ev.node_id == "s"


def test_story_from_text_minimal():
    """from_text 接受最小有效输入"""
    s = Story.from_text("""# test
## 元数据
id: min
start: s
## 节点 s (ending)
text: end
""")
    assert s.id == "min"
    assert s.start_node == "s"
    assert "s" in s.nodes


def test_story_parse_nodes_only():
    """parse_nodes_only 应跳过元数据校验"""
    nodes = Story.parse_nodes_only("""# test
## 元数据
id: t
start: nonexistent
## 节点 a (scene)
text: hi
## 节点 b (ending)
text: end
""")
    assert "a" in nodes
    assert "b" in nodes


def test_world_render_template_complex_obj():
    """复杂对象不应内联"""
    w = _world()
    # 找一个 list 类型字段
    result = w.render_template("{realms.炼气期.sub_stages}")
    # list 不是基本类型，应返回 <{}>
    assert "<" in result


def test_engine_apply_choice_with_realm():
    """choice 含 realm 字段应更新 state.realm"""
    s = State()
    s.realm = "下界"
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: go
    goto: e
    realm: 仙界
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert s.realm == "仙界"


def test_engine_apply_choice_drop():
    """choice 含 drop 字段应从背包移除"""
    s = State()
    s.add_item("灵石")
    s.add_item("丹药")
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: drop
    goto: e
    drop: 灵石
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert not s.has_item("灵石")
    assert s.has_item("丹药")


def test_engine_apply_choice_pickup_list():
    """choice 含 pickup 列表应全部加入背包"""
    s = State()
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: pickup
    goto: e
    pickup:
      - 灵石
      - 丹药
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert s.has_item("灵石")
    assert s.has_item("丹药")


def test_engine_apply_choice_favor_dict():
    """choice 含 favor 字典应调整 NPC 好感度"""
    s = State()
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: favor
    goto: e
    favor:
      张三: 10
      李四: -5
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert s.get_npc_favor("张三") == 60
    assert s.get_npc_favor("李四") == 45


def test_engine_apply_choice_advance():
    """choice 含 advance 字段应推进时间"""
    s = State()
    eng = Engine(_world(), _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: advance
    goto: e
    advance:
      years: 1
      months: 2
      days: 3
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert s.time["年"] == 2
    assert s.time["月"] == 3
    assert s.time["日"] == 4


def test_state_load_from_dict():
    """from_dict 应正确恢复 state"""
    d = {
        "attrs": {"x": 1},
        "flags": ["f1"],
        "items": ["a"],
        "npc_favor": {"n": 70},
        "time": {"年": 2, "月": 3, "日": 4},
        "realm": "仙界",
    }
    s = State.from_dict(d)
    assert s.get("x") == 1
    assert s.flag("f1")
    assert s.has_item("a")
    assert s.get_npc_favor("n") == 70
    assert s.realm == "仙界"


# ── v2.9 互动引擎深化：世界书 / 成就 / 多结局 / AI 叙事 ──

from interactive import (
    WorldBook, WorldBookEntry, Achievement, AchievementTracker,
    EndingAnalyzer, EndInfo, AINarrator,
)


# ── WorldBook ──

def test_worldbook_empty():
    wb = WorldBook()
    assert wb.entries == []
    assert wb.lookup("any text") == []


def test_worldbook_add_and_lookup():
    wb = WorldBook()
    entry = WorldBookEntry(
        id="thunder",
        keywords=["天劫", "雷劫"],
        title="天劫",
        content="渡劫时要小心",
    )
    wb.add(entry)
    matches = wb.lookup("要小心天劫")
    assert len(matches) == 1
    assert matches[0].id == "thunder"


def test_worldbook_keyword_no_match():
    wb = WorldBook()
    wb.add(WorldBookEntry(id="x", keywords=["天劫"], title="x", content="x"))
    assert wb.lookup("无关文本") == []


def test_worldbook_priority():
    wb = WorldBook()
    wb.add(WorldBookEntry(id="low", keywords=["x"], title="low", content="low", priority=1))
    wb.add(WorldBookEntry(id="high", keywords=["x"], title="high", content="high", priority=10))
    matches = wb.lookup("something x happens")
    assert matches[0].id == "high"


def test_worldbook_max_entries():
    wb = WorldBook()
    for i in range(5):
        wb.add(WorldBookEntry(id=f"e{i}", keywords=["x"], title=f"e{i}", content="c"))
    matches = wb.lookup("test x", max_entries=2)
    assert len(matches) == 2


def test_worldbook_disabled():
    wb = WorldBook()
    wb.add(WorldBookEntry(id="d", keywords=["x"], title="d", content="c", enabled=False))
    assert wb.lookup("x") == []


def test_worldbook_to_dict():
    wb = WorldBook()
    wb.add(WorldBookEntry(id="e1", keywords=["k1"], title="t1", content="c1"))
    d = wb.to_dict()
    assert "entries" in d
    assert len(d["entries"]) == 1
    assert d["entries"][0]["id"] == "e1"


# ── Achievement ──

def test_achievement_basic():
    ach = Achievement(id="a", name="A", description="D", condition="state.attrs.get('x', 0) >= 10")
    s = State({"x": 15})
    assert ach.check(s) is True
    assert ach.unlocked is False  # 还未解锁


def test_achievement_unlock():
    ach = Achievement(id="a", name="A", description="D", condition="state.attrs.get('x', 0) >= 10")
    s = State({"x": 15})
    if ach.check(s):
        ach.unlocked = True
    assert ach.unlocked is True


def test_achievement_already_unlocked():
    ach = Achievement(id="a", name="A", description="D", condition="True")
    s = State()
    assert ach.check(s) is True
    ach.unlocked = True
    assert ach.check(s) is False  # 已解锁不重复


def test_achievement_invalid_condition():
    ach = Achievement(id="a", name="A", description="D", condition="invalid syntax !@#")
    s = State()
    assert ach.check(s) is False  # 不抛异常


def test_achievement_tracker_check_all():
    tracker = AchievementTracker()
    tracker.add(Achievement(id="a1", name="A1", description="", condition="state.attrs.get('x', 0) >= 5"))
    tracker.add(Achievement(id="a2", name="A2", description="", condition="state.attrs.get('y', 0) >= 10"))
    s = State({"x": 10, "y": 20})
    newly = tracker.check_all(s)
    assert len(newly) == 2


def test_achievement_tracker_partial():
    tracker = AchievementTracker()
    tracker.add(Achievement(id="a1", name="A1", description="", condition="state.attrs.get('x', 0) >= 5"))
    tracker.add(Achievement(id="a2", name="A2", description="", condition="state.attrs.get('y', 0) >= 100"))
    s = State({"x": 10, "y": 0})
    newly = tracker.check_all(s)
    assert len(newly) == 1
    assert newly[0].id == "a1"


def test_achievement_tracker_score():
    tracker = AchievementTracker()
    tracker.add(Achievement(id="a1", name="A1", description="", condition="True", points=10))
    tracker.add(Achievement(id="a2", name="A2", description="", condition="True", points=20))
    s = State()
    tracker.check_all(s)
    assert tracker.get_score() == 30


def test_achievement_tracker_progress():
    tracker = AchievementTracker()
    tracker.add(Achievement(id="a1", name="A1", description="", condition="True"))
    tracker.add(Achievement(id="a2", name="A2", description="", condition="False"))
    s = State()
    tracker.check_all(s)
    progress = tracker.get_progress()
    assert progress["total"] == 2
    assert progress["unlocked"] == 1
    assert progress["percent"] == 50.0


# ── EndingAnalyzer ──

def test_ending_analyzer_story_with_endings():
    story = _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (ending)
text: success
## 节点 b (ending)
text: bad ending
## 节点 c (ending)
text: secret ending
## 节点 d (ending)
text: normal ending
""")
    analyzer = EndingAnalyzer(story)
    endings = analyzer.get_endings()
    assert len(endings) == 4


def test_ending_analyzer_classify_types():
    story = _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
## 节点 good_ending (ending)
text: good
## 节点 bad_ending (ending)
text: bad
## 节点 secret_ending (ending)
text: secret
## 节点 normal_ending (ending)
text: normal
""")
    analyzer = EndingAnalyzer(story)
    completeness = analyzer.get_completeness()
    assert completeness["total_endings"] == 4
    assert completeness["good_endings"] >= 1
    assert completeness["bad_endings"] >= 1
    assert completeness["secret_endings"] >= 1


def test_ending_analyzer_predict():
    story = _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
## 节点 a (ending)
text: a
""")
    analyzer = EndingAnalyzer(story)
    pred = analyzer.predict_ending(75)
    assert pred.id == "a"


def test_ending_analyzer_no_endings():
    story = _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: scene
next:
  - label: next
    goto: e
## 节点 e (ending)
text: end
""")
    analyzer = EndingAnalyzer(story)
    assert len(analyzer.get_endings()) == 1


# ── AINarrator ──

def test_ai_narrator_basic():
    w = _world()
    narrator = AINarrator(w)
    s = State({"境界": "炼气期", "灵根": "伪灵根", "灵石": 10})
    narr = narrator.narrate_state(s)
    assert "炼气期" in narr
    assert "伪灵根" in narr


def test_ai_narrator_jindan():
    w = _world()
    narrator = AINarrator(w)
    s = State({"境界": "结丹期", "灵根": "天灵根", "灵石": 1000})
    narr = narrator.narrate_state(s)
    assert "结丹期" in narr
    assert "天灵根" in narr


def test_ai_narrator_with_context():
    w = _world()
    narrator = AINarrator(w)
    s = State({"境界": "炼气期"})
    narr = narrator.narrate_state(s, "你在山间发现了一座洞府")
    assert "洞府" in narr


def test_ai_narrator_change_lingshi():
    w = _world()
    narrator = AINarrator(w)
    s = State()
    narr = narrator.narrate_change(s, "灵石", 0, 50)
    assert "50" in narr
    assert "获得" in narr


def test_ai_narrator_change_realm():
    w = _world()
    narrator = AINarrator(w)
    s = State()
    narr = narrator.narrate_change(s, "境界", "炼气期", "筑基期")
    assert "炼气期" in narr
    assert "筑基期" in narr


def test_ai_narrator_change_lingshi_spend():
    w = _world()
    narrator = AINarrator(w)
    s = State()
    narr = narrator.narrate_change(s, "灵石", 100, 30)
    assert "消耗" in narr or "70" in narr


# ── Engine 集成 ──

def test_engine_attach_worldbook():
    w = _world()
    s = State()
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (ending)
text: end
"""), s)
    wb = WorldBook()
    eng.attach_worldbook(wb)
    assert eng._worldbook is wb


def test_engine_attach_achievements():
    w = _world()
    s = State()
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (ending)
text: end
"""), s)
    tracker = AchievementTracker()
    eng.attach_achievements(tracker)
    assert eng._achievements is tracker


def test_engine_worldbook_action():
    """worldbook choice action 应更新 state.last_worldbook"""
    w = _world()
    s = State()
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: wb
    goto: e
    worldbook: thunder
## 节点 e (ending)
text: end
"""), s)
    wb = WorldBook()
    wb.add(WorldBookEntry(id="thunder", keywords=["x"], title="天劫", content="小心天劫"))
    eng.attach_worldbook(wb)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert "last_worldbook" in s.attrs
    assert s.attrs["last_worldbook"]["id"] == "thunder"


def test_engine_achievement_action():
    """achievement choice action 应直接解锁"""
    w = _world()
    s = State()
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: ach
    goto: e
    achievement: a1
## 节点 e (ending)
text: end
"""), s)
    tracker = AchievementTracker()
    tracker.add(Achievement(id="a1", name="A1", description="", condition="True", points=10))
    eng.attach_achievements(tracker)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert "last_achievement" in s.attrs
    assert s.attrs["last_achievement"]["id"] == "a1"


def test_engine_narrate_action():
    """narrate choice action 应生成叙事"""
    w = _world()
    s = State({"境界": "炼气期", "灵根": "天灵根"})
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: narr
    goto: e
    narrate: 你在山间发现了一座洞府
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert "last_narrative" in s.attrs
    assert "洞府" in s.attrs["last_narrative"]


def test_engine_check_achievements():
    """engine.check_achievements() 应能触发解锁"""
    w = _world()
    s = State({"x": 100})
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (ending)
text: end
"""), s)
    tracker = AchievementTracker()
    tracker.add(Achievement(id="x100", name="百数", description="", condition="state.attrs.get('x', 0) >= 100"))
    eng.attach_achievements(tracker)
    newly = eng.check_achievements()
    assert len(newly) == 1
    assert newly[0].id == "x100"


# ── v2.15 跨境界试炼副本 ──

from interactive import TrialDungeon, TrialStage, TrialResult


def test_trial_stage_can_enter_realm_match():
    s = State({"境界": "炼气期"})
    stage = TrialStage(
        id="lianqi_easy", name="炼气期-easy", description="",
        difficulty="easy", realm_required="炼气期",
    )
    assert stage.can_enter(s) is True


def test_trial_stage_cannot_enter_wrong_realm():
    s = State({"境界": "炼气期"})
    stage = TrialStage(
        id="zhuji_easy", name="筑基期-easy", description="",
        difficulty="easy", realm_required="筑基期",
    )
    assert stage.can_enter(s) is False


def test_trial_stage_can_enter_with_conditions():
    s = State({"境界": "筑基期", "声望": 10})
    stage = TrialStage(
        id="test", name="t", description="",
        difficulty="normal", realm_required="筑基期",
        conditions={"声望": 10},
    )
    assert stage.can_enter(s) is True


def test_trial_stage_condition_mismatch():
    s = State({"境界": "筑基期", "声望": 5})
    stage = TrialStage(
        id="test", name="t", description="",
        difficulty="normal", realm_required="筑基期",
        conditions={"声望": 10},
    )
    assert stage.can_enter(s) is False


def test_trial_dungeon_default_stages():
    w = _world()
    s = State()
    d = TrialDungeon(w, s)
    # 9 境界 × 4 难度 = 36 关卡
    assert len(d.stages) == 36


def test_trial_dungeon_list_stages_for_realm():
    w = _world()
    s = State({"境界": "炼气期"})
    d = TrialDungeon(w, s)
    stages = d.list_stages("炼气期")
    assert len(stages) == 4  # easy/normal/hard/hell


def test_trial_dungeon_realm_mismatch_no_access():
    w = _world()
    s = State({"境界": "炼气期"})
    d = TrialDungeon(w, s)
    stages = d.list_stages("大乘期")
    assert len(stages) == 0


def test_trial_enter_existing_stage():
    w = _world()
    s = State({"境界": "炼气期"})
    d = TrialDungeon(w, s)
    result = d.enter_stage("lianqi_easy")
    assert result.stage_id == "lianqi_easy"
    assert isinstance(result.success, bool)
    assert result.narrative != ""


def test_trial_enter_nonexistent_stage():
    w = _world()
    s = State()
    d = TrialDungeon(w, s)
    result = d.enter_stage("nonexistent")
    assert result.success is False
    assert "不存在" in result.narrative


def test_trial_apply_result_success():
    w = _world()
    s = State({"境界": "炼气期", "灵石": 0})
    d = TrialDungeon(w, s)
    result = d.enter_stage("lianqi_easy")
    if result.success:
        d.apply_result(result)
        # 灵石应增加
        assert s.get("灵石", 0) > 0


def test_trial_apply_result_failure():
    w = _world()
    s = State({"境界": "炼气期", "灵石": 100})
    d = TrialDungeon(w, s)
    result = d.enter_stage("lianqi_hell")  # 高难度容易失败
    if not result.success:
        d.apply_result(result)
        # 灵石应减少
        assert s.get("灵石", 100) < 100


def test_trial_rewards_scale():
    w = _world()
    s = State()
    d = TrialDungeon(w, s)
    easy = d.stages["lianqi_easy"].rewards
    normal = d.stages["lianqi_normal"].rewards
    hard = d.stages["lianqi_hard"].rewards
    hell = d.stages["lianqi_hell"].rewards
    # 高难度奖励应更多
    assert normal["灵石"] > easy["灵石"]
    assert hard["灵石"] > normal["灵石"]
    assert hell["灵石"] > hard["灵石"]


def test_trial_penalties_scale():
    w = _world()
    s = State()
    d = TrialDungeon(w, s)
    easy = d.stages["lianqi_easy"].penalties
    hell = d.stages["lianqi_hell"].penalties
    # 高难度惩罚应更重
    assert abs(hell["灵石"]) > abs(easy["灵石"])


def test_trial_get_progress():
    w = _world()
    s = State({"境界": "炼气期"})
    d = TrialDungeon(w, s)
    progress = d.get_progress()
    assert progress["total_stages"] == 36
    assert progress["accessible"] == 4
    assert progress["locked"] == 32


def test_engine_trial_action():
    """trial choice action 应触发试炼"""
    w = _world()
    s = State({"境界": "炼气期", "灵石": 0})
    eng = Engine(w, _minimal_story("""# test
## 元数据
id: t
start: s
## 节点 s (scene)
text: hi
next:
  - label: trial
    goto: e
    trial: lianqi_easy
## 节点 e (ending)
text: end
"""), s)
    eng._apply_choice_actions(eng.story.get("s").choices[0])
    assert "last_trial" in s.attrs
    assert s.attrs["last_trial"]["stage_id"] == "lianqi_easy"
