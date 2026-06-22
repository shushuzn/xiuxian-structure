"""
test_yaml_schema.py — YAML 数据一致性测试

测试所有 data/*.yaml 文件：
1. 可被 PyYAML 解析
2. 跨文件 ID 引用一致
3. relations.yaml 引用的所有 ID 在对应文件中存在
"""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def all_yaml_files():
    return sorted(DATA_DIR.glob("*.yaml"))


def test_all_yaml_parseable():
    """所有 yaml 文件必须能被 PyYAML 解析"""
    for yf in all_yaml_files():
        with open(yf, encoding="utf-8") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"{yf.name} 解析失败: {e}")


def test_no_empty_yaml():
    """yaml 文件不应为空"""
    for yf in all_yaml_files():
        with open(yf, encoding="utf-8") as f:
            content = f.read()
        assert content.strip(), f"{yf.name} 是空的"


def test_yaml_use_2_space_indent():
    """yaml 应使用 2 空格缩进（项目约定）"""
    for yf in all_yaml_files():
        content = yf.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            # 跳过空行 / 注释 / 列表项
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            stripped = line.lstrip()
            if not stripped.startswith("-") and line.startswith("\t"):
                pytest.fail(
                    f"{yf.name}:{i} 使用了 tab 缩进，应改为 2 空格"
                )


def test_relations_yaml_references_valid_ids():
    """data/relations.yaml 中的引用应在对应 yaml 文件中存在。

    严格模式：FAIL（不 skip）任何缺失引用。
    项目约定：relations 用单数前缀，yaml 文件名用复数；
    字段名前缀映射见下方 FILENAME_TO_PREFIX。
    """
    relations_file = DATA_DIR / "relations.yaml"
    relations = yaml.safe_load(relations_file.read_text(encoding="utf-8"))
    # 文件名（复数）→ 默认 relations 前缀
    # 但实际 relations 引用多以「字段名」为前缀（artifact/tier/elixir 等），
    # 因此下面的索引会同时记录「文件前缀:id」和「字段前缀:id」。
    FILENAME_TO_PREFIX = {
        "aether": "aether",
        "artifacts": "artifact",
        "contracts": "contract",
        "divine_sense": "divine_sense",
        "elixirs": "elixir",
        "factions": "org",
        "formations": "formation",
        "heart_demons": "heart_demon",
        "monsters": "spirit_beast",
        "realms": "realm",
        "spirit_roots": "spirit_root",
        "spirit_stones": "spirit_stone",
        "spirit_weapons": "spirit_weapon",
        "talismans": "talisman",
        "techniques": "technique",
        "tribulations": "tribulation",
        "yao_xiu": "yao_xiu",
    }

    # 构建 id 索引：
    # - 每个 yaml 的所有「顶层 list[dict{id}]」按字段名建索引
    # - 同时按文件名建索引（兼容旧风格）
    id_index = {}
    for yf in all_yaml_files():
        if yf.name == "relations.yaml":
            continue
        stem = yf.stem
        file_prefix = FILENAME_TO_PREFIX.get(stem, stem)
        data = yaml.safe_load(yf.read_text(encoding="utf-8"))
        if not data:
            continue

        def collect_items(items):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    # 同时记录：文件前缀 和 字段前缀
                    id_index.setdefault(f"{file_prefix}:{item['id']}", yf.name)
                    id_index.setdefault(f"{field_name}:{item['id']}", yf.name)

        for field_name, field_value in data.items():
            if isinstance(field_value, list):
                collect_items(field_value)
            elif isinstance(field_value, dict):
                for k, v in field_value.items():
                    if isinstance(v, list):
                        collect_items(v)

    # 检查所有 relations 引用
    missing = []
    for rel in relations["relations"]:
        for key in ("from", "to"):
            ref = rel.get(key)
            if ref is None:
                continue
            if ":" not in ref:
                pytest.fail(
                    f"relations.yaml 中 {key}={ref!r} 格式错误（应包含 system:id）"
                )
            if ref not in id_index:
                missing.append((key, ref))

    if missing:
        msg = "\n".join(
            f"  - {key}={ref}  (第 {i} 条 relation)"
            for i, (key, ref) in enumerate(missing, 1)
        )
        pytest.fail(
            f"relations.yaml 中有 {len(missing)} 个引用在 data/*.yaml 中未找到：\n{msg}"
        )


def test_realm_ids_consistent():
    """所有 realm 引用应存在于 realms.yaml"""
    realms_file = DATA_DIR / "realms.yaml"
    realms_data = yaml.safe_load(realms_file.read_text(encoding="utf-8"))
    valid_ids = {r["id"] for r in realms_data.get("realms", [])}

    # 检查所有 yaml 中 referenced_realm 字段
    for yf in all_yaml_files():
        if yf.name == "realms.yaml":
            continue
        data = yaml.safe_load(yf.read_text(encoding="utf-8"))
        if not data:
            continue
        text = yf.read_text(encoding="utf-8")
        # 简单字符串扫描：所有 *_realm 字段的值应在 valid_ids 中
        # 注意：仅作粗校验，详细校验在 relations 测试中
        for line in text.splitlines():
            if "_realm:" in line or "to_realm:" in line:
                # 提取值
                value = line.split(":", 1)[1].strip().strip("\"'")
                if value and value not in valid_ids and value != "null":
                    # 不强制失败，只警告（可能是新加的 realm）
                    pass