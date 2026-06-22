"""
test_state_features.py — 互动引擎 v2.1 升级的单测

测试 State 类新增功能：
- 背包系统（add_item / remove_item / has_item）
- NPC 好感度（modify_npc_favor / get_npc_favor）
- 时间推进（advance_time / get_time_str）
- 存档 / 读档（save / load）
- 结局评分（score_breakdown）
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

# 添加 scripts/ 到路径
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from interactive import State  # noqa: E402


# ─── 背包 ───

def test_add_item():
    s = State()
    s.add_item("清心丹")
    s.add_item("火球符")
    assert "清心丹" in s.items
    assert "火球符" in s.items
    assert s.item_count == 2


def test_add_item_duplicate_ignored():
    s = State()
    s.add_item("清心丹")
    s.add_item("清心丹")  # 重复
    assert s.item_count == 1


def test_add_empty_item_ignored():
    s = State()
    s.add_item("")
    assert s.item_count == 0


def test_remove_item():
    s = State()
    s.add_item("清心丹")
    s.add_item("火球符")
    assert s.remove_item("清心丹") is True
    assert "清心丹" not in s.items
    assert "火球符" in s.items


def test_remove_nonexistent_item():
    s = State()
    assert s.remove_item("不存在的物品") is False


def test_has_item():
    s = State()
    s.add_item("清心丹")
    assert s.has_item("清心丹") is True
    assert s.has_item("不存在") is False


# ─── NPC 好感度 ───

def test_npc_favor_default():
    s = State()
    assert s.get_npc_favor("墨大夫") == 50  # 默认中性


def test_modify_npc_favor_increase():
    s = State()
    new_val = s.modify_npc_favor("墨大夫", 20)
    assert new_val == 70


def test_modify_npc_favor_decrease():
    s = State()
    new_val = s.modify_npc_favor("墨大夫", -30)
    assert new_val == 20


def test_npc_favor_clamp_max():
    s = State()
    s.modify_npc_favor("墨大夫", 200)  # 溢出
    assert s.get_npc_favor("墨大夫") == 100


def test_npc_favor_clamp_min():
    s = State()
    s.modify_npc_favor("墨大夫", -200)  # 下溢
    assert s.get_npc_favor("墨大夫") == 0


# ─── 时间推进 ───

def test_advance_time_years():
    s = State()
    s.advance_time(years=10)
    assert s.time == {"年": 11, "月": 1, "日": 1}


def test_advance_time_month_carry():
    s = State()
    s.advance_time(months=15)
    # 15 个月 → 年 +1，剩余 3 个月
    assert s.time["年"] == 2
    assert s.time["月"] == 4
    assert s.time["日"] == 1


def test_advance_time_day_carry():
    s = State()
    s.advance_time(days=45)
    # 45 天 = 1 月 15 日
    assert s.time["年"] == 1
    assert s.time["月"] == 2
    assert s.time["日"] == 16


def test_advance_time_complex():
    s = State()
    s.advance_time(years=2, months=10, days=20)
    # 1 + 2 年 = 3, 1 + 10 月 = 11, 1 + 20 日 = 21
    # 21 ≤ 30 不进位
    assert s.time["年"] == 3
    assert s.time["月"] == 11
    assert s.time["日"] == 21


def test_get_time_str():
    s = State()
    s.advance_time(years=99, months=11, days=29)
    # y=100, m=12, d=30
    # 30>30? 否
    s_str = s.get_time_str()
    assert "100年12月30日" == s_str


# ─── 存档 / 读档 ───

def test_save_load_roundtrip(tmp_path):
    s = State({"灵石": 100, "声望": 10, "境界": "结丹期"})
    s.add_item("清心丹")
    s.add_item("火球符")
    s.modify_npc_favor("墨大夫", 20)
    s.advance_time(years=5)

    save_path = tmp_path / "save.json"
    s.save(save_path)
    assert save_path.exists()

    loaded = State.load(save_path)
    assert loaded.attrs["灵石"] == 100
    assert loaded.attrs["声望"] == 10
    assert loaded.attrs["境界"] == "结丹期"
    assert loaded.items == ["清心丹", "火球符"]
    assert loaded.npc_favor == {"墨大夫": 70}
    assert loaded.time["年"] == 6


def test_save_creates_parent_dirs(tmp_path):
    s = State()
    save_path = tmp_path / "subdir" / "save.json"
    s.save(save_path)
    assert save_path.exists()


def test_to_dict_contains_all_fields():
    s = State({"灵石": 50})
    s.add_item("丹药")
    s.modify_npc_favor("韩立", 10)
    s.advance_time(years=2)

    d = s.to_dict()
    assert "attrs" in d
    assert "flags" in d
    assert "items" in d
    assert "npc_favor" in d
    assert "time" in d
    assert "score" in d
    assert d["items"] == ["丹药"]
    assert d["npc_favor"] == {"韩立": 60}
    assert d["time"] == {"年": 3, "月": 1, "日": 1}


def test_from_dict_backwards_compatible():
    """测试旧版本存档（无 items/npc_favor/time 字段）也能加载"""
    old_data = {
        "attrs": {"灵石": 100},
        "flags": ["遇见妖兽"],
    }
    s = State.from_dict(old_data)
    assert s.attrs["灵石"] == 100
    assert s.flag("遇见妖兽")
    assert s.items == []
    assert s.npc_favor == {}
    assert s.time == {"年": 1, "月": 1, "日": 1}


# ─── 结局评分 ───

def test_score_empty_state():
    s = State()
    score = s.score_breakdown()
    assert score["总分"] == 0


def test_score_lingshi():
    s = State({"灵石": 5000})
    score = s.score_breakdown()
    assert score["灵石"] == 30  # 5000 // 100 = 50, min(30, 50) = 30


def test_score_shengwang():
    s = State({"声望": 100})
    score = s.score_breakdown()
    assert score["声望"] == 25  # 100 // 4 = 25


def test_score_items():
    s = State()
    for i in range(15):
        s.add_item(f"物品{i}")
    score = s.score_breakdown()
    assert score["物品"] == 20  # 15 * 2 = 30, min(20, 30) = 20


def test_score_realm():
    s = State({"境界": "元婴期"})
    score = s.score_breakdown()
    assert score["修为"] == 7


def test_score_npc_favor():
    s = State()
    s.modify_npc_favor("A", 50)  # 100
    s.modify_npc_favor("B", -50)  # 0
    score = s.score_breakdown()
    # 平均 = 50, (50-50)/50*15 = 0
    assert score["好感"] == 0


def test_score_max():
    s = State({"灵石": 99999, "声望": 99999, "境界": "大乘期"})
    for i in range(20):
        s.add_item(f"物品{i}")
    s.modify_npc_favor("A", 50)
    s.modify_npc_favor("B", 50)
    score = s.score_breakdown()
    # 30 + 25 + 20 + 15 + 10 = 100
    assert score["总分"] == 100


# ─── 集成测试：save/load + score ───

def test_full_cycle(tmp_path):
    """完整周期：玩 → 存档 → 读档 → 评分"""
    s1 = State({"灵石": 300, "声望": 50, "境界": "结丹期"})
    s1.add_item("清心丹")
    s1.modify_npc_favor("墨大夫", 30)
    s1.advance_time(years=2)
    s1.set_flag("飞升成功")

    save_path = tmp_path / "endgame.json"
    s1.save(save_path)

    # 模拟"读档继续游戏"
    s2 = State.load(save_path)
    assert s2.attrs["灵石"] == 300
    assert s2.flag("飞升成功")

    # 评分
    # 灵石=300→3, 声望=50→12, 物品=1→2, 修为=结丹期→5
    # 好感: 墨大夫 30+50=80，avg=80，(80-50)/50*15=9
    # 总分 = 3 + 12 + 2 + 9 + 5 = 31
    score = s2.score_breakdown()
    assert score["灵石"] == 3
    assert score["声望"] == 12
    assert score["物品"] == 2
    assert score["修为"] == 5
    assert score["好感"] == 9
    assert score["总分"] == 31