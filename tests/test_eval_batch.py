"""
test_eval_batch.py — v2.2 LLM 工业化脚本的单测

测试：
- eval_prompts.yaml 格式正确
- eval_llm.py 的 dry-run 模式
- batch_generate.py 的 dry-run 模式
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


# ─── eval_prompts.yaml 格式校验 ───


def test_eval_prompts_yaml_exists():
    assert (ROOT / "tests" / "eval_prompts.yaml").exists()


def test_eval_prompts_yaml_loadable():
    """评测集 YAML 应能正确解析"""
    with open(ROOT / "tests" / "eval_prompts.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "prompts" in data
    assert "defaults" in data
    assert len(data["prompts"]) >= 5


def test_eval_prompts_have_required_fields():
    """每个 prompt 必含字段：id, story, requirement, expected_refs"""
    with open(ROOT / "tests" / "eval_prompts.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for p in data["prompts"]:
        assert "id" in p, f"missing id: {p}"
        assert "story" in p, f"missing story: {p['id']}"
        assert "requirement" in p, f"missing requirement: {p['id']}"
        assert "expected_refs" in p, f"missing expected_refs: {p['id']}"
        assert len(p["requirement"]) >= 10
        assert len(p["expected_refs"]) >= 1


def test_eval_prompts_stories_exist():
    """每个 prompt 引用的 story 应在 stories/ 存在"""
    with open(ROOT / "tests" / "eval_prompts.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for p in data["prompts"]:
        story_path = ROOT / "stories" / f"{p['story']}.md"
        assert story_path.exists(), f"{p['id']}: 故事不存在 {story_path}"


def test_eval_prompts_unique_ids():
    """prompt id 应唯一"""
    with open(ROOT / "tests" / "eval_prompts.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    ids = [p["id"] for p in data["prompts"]]
    assert len(ids) == len(set(ids)), f"重复 id: {ids}"


def test_eval_prompts_v1_v2_coverage():
    """评测集应覆盖 v1.5-v2.1 新体系"""
    with open(ROOT / "tests" / "eval_prompts.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    tags = set()
    for p in data["prompts"]:
        for tag in p.get("tags", []):
            tags.add(tag)
    # 必须包含 v1.5 - v2.1 的至少一个 tag
    required = {"v1.5", "v1.6", "v1.7", "v2.0", "v2.1"}
    missing = required - tags
    assert not missing, f"缺少版本覆盖: {missing}"


# ─── eval_llm.py dry-run ───


def test_eval_llm_dry_run():
    """dry-run 模式不需 API key，输出汇总报告"""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "eval_llm.py"),
         "--prompts", str(ROOT / "tests" / "eval_prompts.yaml"),
         "--models", "gpt-4o-mini,deepseek-chat",
         "--dry-run"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # 报告应包含 10 prompts × 2 models = 20 results
    assert "10 个 prompt" in result.stdout or "10" in result.stdout
    assert "deepseek-chat" in result.stdout
    assert "gpt-4o-mini" in result.stdout


def test_eval_llm_missing_key():
    """缺少 API key 时（无 dry-run）应返回错误"""
    import os
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("LLM_API_KEY", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "eval_llm.py"),
         "--prompts", str(ROOT / "tests" / "eval_prompts.yaml"),
         "--models", "gpt-4o-mini"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", timeout=30, env=env,
    )
    assert result.returncode != 0
    assert "API key" in result.stdout or "API key" in result.stderr


# ─── batch_generate.py dry-run ───


def test_batch_generate_dry_run():
    """dry-run 模式不需 API key"""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "batch_generate.py"),
         "--prompts", str(ROOT / "tests" / "eval_prompts.yaml"),
         "--dry-run",
         "--output", "/tmp/batch_test/"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "批量生成" in result.stdout
    assert "dry-run" in result.stdout


# ─── 评测集导入 ───


def test_eval_prompts_importable():
    """评测集可被 eval_llm.py 正确加载"""
    from eval_llm import load_prompts
    data = load_prompts(ROOT / "tests" / "eval_prompts.yaml")
    assert "prompts" in data
    assert isinstance(data["prompts"], list)


def test_eval_one_returns_dict():
    """evaluate_one 应返回 dict（不调 API 时 mock）"""
    from eval_llm import evaluate_one
    from interactive import World

    world = World.from_yaml_dir(ROOT / "data")
    cfg = {
        "id": "test",
        "story": "demo_measuring_spirit",
        "requirement": "测试",
        "expected_refs": ["丹药体系/辟谷丹.md"],
        "temperature": 0.3,
        "max_retries": 3,
    }
    # 无 API key → 直接失败但仍返回结构化结果
    result = evaluate_one(cfg, "test-model", "https://api.test/v1", "", world, {})
    assert "prompt_id" in result
    assert "model" in result
    assert "pass" in result
    assert "retries" in result
    assert "errors" in result
    assert "elapsed_sec" in result
    assert "node_md" in result