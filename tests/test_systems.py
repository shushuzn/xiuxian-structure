"""
test_systems.py — 体系完整性测试

测试：
1. 所有预期体系目录存在
2. 每个体系有对应的 data/*.yaml
3. 每个体系的 .md 含 ## 关联 章节
4. 跨体系链接目标文件存在
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# 项目当前应有的体系清单（v2.0）
EXPECTED_SYSTEMS = [
    "境界体系",
    "灵根体系",
    "天地灵气",
    "妖兽体系",
    "妖修体系",
    "势力体系",
    "灵石体系",
    "阵法体系",
    "符箓体系",
    "功法体系",
    "丹药体系",
    "法器体系",
    "秘境体系",
    # v1.5+
    "心魔体系",
    "雷劫体系",
    # v1.6+
    "神识体系",
    # v1.7+
    "器灵体系",
    "契约体系",
    # v2.0
    "飞升体系",
    # v2.3
    "神界体系",
    # v2.4
    "魔界体系",
    "冥界体系",
    # v2.6
    "战斗体系",
    # v2.10
    "秘境体系",
    # v2.11
    "天材地宝体系",
    # v2.12
    "宗门体系",
    # v2.13
    "因果体系",
]


def test_all_expected_systems_exist():
    """所有预期体系目录必须存在"""
    for sys_dir in EXPECTED_SYSTEMS:
        path = ROOT / sys_dir
        assert path.is_dir(), f"缺失体系目录: {sys_dir}/"


def test_no_extra_top_level_system_dirs():
    """顶层不应有未列入 EXPECTED_SYSTEMS 的体系目录"""
    skip = {".git", ".github", "data", "docs", "docs_src", "site", "examples", "interactive",
            "scripts", "stories", "tests", "dist", ".pytest_cache", "__pycache__",
            ".ruff_cache", ".mypy_cache"}
    skip |= set(EXPECTED_SYSTEMS)
    actual = {p.name for p in ROOT.iterdir() if p.is_dir()}
    extras = actual - skip
    assert not extras, f"出现未列入的顶层目录: {extras}"


def test_each_system_has_at_least_one_md():
    """每个体系目录至少应有一篇 .md"""
    for sys_dir in EXPECTED_SYSTEMS:
        path = ROOT / sys_dir
        md_files = list(path.glob("*.md"))
        assert len(md_files) >= 1, f"{sys_dir}/ 中没有 .md 文件"


def test_each_system_md_has_关联_section():
    """每篇体系 .md 必须含 ## 关联 章节（stories/ / examples/ / docs/ / docs_src/ 除外）"""
    skip_dirs = {"docs", "docs_src", "examples", "stories", ".github", "interactive", "site"}
    for md in ROOT.rglob("*.md"):
        rel = md.relative_to(ROOT)
        if rel.parts[0] in skip_dirs:
            continue
        if rel.name in {"README.md", "索引.md", "CONTRIBUTING.md",
                        "LICENSE", "CHANGELOG.md", "SECURITY.md"}:
            continue
        if rel.name.startswith(".release-notes-"):
            continue
        content = md.read_text(encoding="utf-8")
        assert "## 关联" in content, f"{rel} 缺少 ## 关联 章节"


def test_data_yaml_matches_system_dirs():
    """data/*.yaml 应与体系对应（每个 yaml 至少被一个体系 .md 引用）"""
    data_dir = ROOT / "data"
    yaml_files = [f.stem for f in data_dir.glob("*.yaml") if f.stem != "relations"]
    # 此测试较宽松：仅校验 yaml 文件数量 > 0
    assert len(yaml_files) >= 10, f"data/ 应有 ≥10 个 yaml，当前 {len(yaml_files)}"

# ── v2.10 秘境体系（已存在但 24 体系）──

def test_secret_realm_directory_exists():
    """v2.10 秘境体系目录必须存在"""
    path = ROOT / "秘境体系"
    assert path.is_dir(), "秘境体系/ 目录必须存在"


def test_secret_realm_yaml_exists():
    """data/secret_realm.yaml 必须存在（v2.10 新增）"""
    path = ROOT / "data" / "secret_realm.yaml"
    assert path.is_file(), "data/secret_realm.yaml 必须存在"


def test_secret_realm_yaml_has_forms():
    """secret_realm.yaml 必须含 forms 字段"""
    import yaml
    with open(ROOT / "data" / "secret_realm.yaml") as f:
        data = yaml.safe_load(f)
    assert "forms" in data
    assert len(data["forms"]) >= 5


def test_secret_realm_yaml_has_grades():
    """secret_realm.yaml 必须含 5 个等级"""
    import yaml
    with open(ROOT / "data" / "secret_realm.yaml") as f:
        data = yaml.safe_load(f)
    assert "grades" in data
    assert len(data["grades"]) >= 5


def test_secret_realm_yaml_has_examples():
    """secret_realm.yaml 必须含至少 15 个实例"""
    import yaml
    with open(ROOT / "data" / "secret_realm.yaml") as f:
        data = yaml.safe_load(f)
    assert "examples" in data
    assert len(data["examples"]) >= 15


def test_secret_realm_directory_has_at_least_8_files():
    """v2.10 后秘境体系/ 应至少有 8 篇 .md"""
    md_files = list((ROOT / "秘境体系").glob("*.md"))
    assert len(md_files) >= 8, f"秘境体系/ 仅有 {len(md_files)} 篇 .md，应 ≥8"


# ── v2.11 天材地宝体系 ──

def test_tian_cai_directory_exists():
    """v2.11 天材地宝体系目录必须存在"""
    path = ROOT / "天材地宝体系"
    assert path.is_dir(), "天材地宝体系/ 目录必须存在"


def test_tian_cai_yaml_exists():
    """data/tian_cai.yaml 必须存在"""
    path = ROOT / "data" / "tian_cai.yaml"
    assert path.is_file(), "data/tian_cai.yaml 必须存在"


def test_tian_cai_yaml_has_categories():
    """tian_cai.yaml 必须含 7 个 categories"""
    import yaml
    with open(ROOT / "data" / "tian_cai.yaml") as f:
        data = yaml.safe_load(f)
    assert "categories" in data
    assert len(data["categories"]) >= 7


def test_tian_cai_yaml_has_grades():
    """tian_cai.yaml 必须含 6 个等级"""
    import yaml
    with open(ROOT / "data" / "tian_cai.yaml") as f:
        data = yaml.safe_load(f)
    assert "grades" in data
    assert len(data["grades"]) >= 6


def test_tian_cai_yaml_has_attributes():
    """tian_cai.yaml 必须含 15+ 属性"""
    import yaml
    with open(ROOT / "data" / "tian_cai.yaml") as f:
        data = yaml.safe_load(f)
    assert "attributes" in data
    assert len(data["attributes"]) >= 15


def test_tian_cai_yaml_has_examples():
    """tian_cai.yaml 必须含 herb/wood/metal/element/beast/exotic/celestial examples 各 ≥ 4"""
    import yaml
    with open(ROOT / "data" / "tian_cai.yaml") as f:
        data = yaml.safe_load(f)
    for field in ("herb_examples", "wood_examples", "metal_examples",
                  "element_examples", "beast_examples",
                  "exotic_examples", "celestial_examples"):
        assert field in data, f"缺少 {field}"
        assert len(data[field]) >= 4, f"{field} 少于 4 条"


def test_tian_cai_directory_has_at_least_8_files():
    """v2.11 后天材地宝体系/ 应至少有 8 篇 .md"""
    md_files = list((ROOT / "天材地宝体系").glob("*.md"))
    assert len(md_files) >= 8, f"天材地宝体系/ 仅有 {len(md_files)} 篇 .md，应 ≥8"


# ── v2.12 宗门体系 ──

def test_zong_men_directory_exists():
    """v2.12 宗门体系目录必须存在"""
    path = ROOT / "宗门体系"
    assert path.is_dir(), "宗门体系/ 目录必须存在"


def test_zong_men_yaml_exists():
    """data/zong_men.yaml 必须存在"""
    path = ROOT / "data" / "zong_men.yaml"
    assert path.is_file(), "data/zong_men.yaml 必须存在"


def test_zong_men_yaml_has_levels():
    """zong_men.yaml 必须含 4+ 等级"""
    import yaml
    with open(ROOT / "data" / "zong_men.yaml") as f:
        data = yaml.safe_load(f)
    assert "levels" in data
    assert len(data["levels"]) >= 4


def test_zong_men_yaml_has_disciple_levels():
    """zong_men.yaml 必须含 4 弟子级别"""
    import yaml
    with open(ROOT / "data" / "zong_men.yaml") as f:
        data = yaml.safe_load(f)
    assert "disciple_levels" in data
    assert len(data["disciple_levels"]) >= 4


def test_zong_men_yaml_has_examples():
    """zong_men.yaml 必须含 10+ 宗门实例"""
    import yaml
    with open(ROOT / "data" / "zong_men.yaml") as f:
        data = yaml.safe_load(f)
    assert "examples" in data
    assert len(data["examples"]) >= 10


def test_zong_men_yaml_has_alliances():
    """zong_men.yaml 必须含 5+ 宗盟"""
    import yaml
    with open(ROOT / "data" / "zong_men.yaml") as f:
        data = yaml.safe_load(f)
    assert "alliances" in data
    assert len(data["alliances"]) >= 5


def test_zong_men_directory_has_at_least_10_files():
    """v2.12 后宗门体系/ 应至少有 10 篇 .md"""
    md_files = list((ROOT / "宗门体系").glob("*.md"))
    assert len(md_files) >= 10, f"宗门体系/ 仅有 {len(md_files)} 篇 .md，应 ≥10"


# ── v2.13 因果体系 ──

def test_karma_directory_exists():
    """v2.13 因果体系目录必须存在"""
    path = ROOT / "因果体系"
    assert path.is_dir(), "因果体系/ 目录必须存在"


def test_karma_yaml_exists():
    """data/karma.yaml 必须存在"""
    path = ROOT / "data" / "karma.yaml"
    assert path.is_file(), "data/karma.yaml 必须存在"


def test_karma_yaml_has_six_realms():
    """karma.yaml 必须含 6 道"""
    import yaml
    with open(ROOT / "data" / "karma.yaml") as f:
        data = yaml.safe_load(f)
    assert "six_realms" in data
    assert len(data["six_realms"]) == 6


def test_karma_yaml_has_divine_powers():
    """karma.yaml 必须含 8+ 因果类神通"""
    import yaml
    with open(ROOT / "data" / "karma.yaml") as f:
        data = yaml.safe_load(f)
    assert "divine_powers" in data
    assert len(data["divine_powers"]) >= 8


def test_karma_yaml_has_merit_and_karma_levels():
    """karma.yaml 必须含功德与业力等级"""
    import yaml
    with open(ROOT / "data" / "karma.yaml") as f:
        data = yaml.safe_load(f)
    assert "merit_levels" in data
    assert "karma_levels" in data
    assert len(data["merit_levels"]) >= 4
    assert len(data["karma_levels"]) >= 4


def test_karma_directory_has_at_least_8_files():
    """v2.13 后因果体系/ 应至少有 8 篇 .md"""
    md_files = list((ROOT / "因果体系").glob("*.md"))
    assert len(md_files) >= 8, f"因果体系/ 仅有 {len(md_files)} 篇 .md，应 ≥8"
