#!/usr/bin/env python3
"""
eval_llm.py — LLM 评测脚本（v2.2 新增）

用途：
  把 tests/eval_prompts.yaml 中的多个需求批量交给 LLM，
  统计每个 prompt 在多个模型上的 NodeValidator 通过率与重试次数。
  用于：
    - 对比不同 LLM 的生成质量
    - 跟踪回归（同一 prompt 在升级 prompt 模板后的表现变化）

用法：
  export OPENAI_API_KEY=sk-...
  python3 scripts/eval_llm.py \
    --prompts tests/eval_prompts.yaml \
    --models gpt-4o-mini,deepseek-chat \
    --report dist/eval_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from interactive import Story, World  # noqa: E402
from generate_node import (  # noqa: E402
    NodeValidator,
    build_prompt,
    call_llm,
)


def load_prompts(path: Path) -> dict:
    """加载评测集 YAML"""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_one(prompt_cfg: dict, model: str, base_url: str, api_key: str,
                 world: World, defaults: dict, max_steps: int = 5) -> dict:
    """评测一个 prompt 在一个模型上的表现。

    返回：
      {
        "prompt_id": ..., "model": ..., "pass": bool,
        "retries": int, "errors": [...], "elapsed_sec": float,
        "node_md": str (truncated),
      }
    """
    story_path = ROOT / "stories" / f"{prompt_cfg['story']}.md"
    if not story_path.exists():
        return {
            "prompt_id": prompt_cfg["id"],
            "model": model,
            "pass": False,
            "retries": 0,
            "errors": [f"故事不存在: {story_path}"],
            "elapsed_sec": 0.0,
            "node_md": "",
        }
    story = Story.from_file(story_path)

    temperature = prompt_cfg.get("temperature", defaults.get("temperature", 0.3))
    max_retries = prompt_cfg.get("max_retries", defaults.get("max_retries", 3))

    # 构造完整 prompt
    full_prompt = build_prompt(story, world, prompt_cfg["requirement"])
    if prompt_cfg.get("expected_refs"):
        full_prompt += "\n\n期望引用的体系文件：\n" + "\n".join(
            f"- {r}" for r in prompt_cfg["expected_refs"]
        )

    validator = NodeValidator(story, world)
    errors: list[str] = []
    last_md = ""
    retries = 0
    start = time.time()

    for attempt in range(1, max_retries + 1):
        retries = attempt
        try:
            content = call_llm(
                full_prompt,
                base_url=base_url,
                api_key=api_key,
                model=model,
                temperature=temperature,
            )
        except Exception as e:
            errors.append(f"API 调用失败（attempt {attempt}）: {e}")
            continue

        last_md = content.strip()
        # 去 markdown 代码块包裹
        last_md = re.sub(r"^```(?:markdown|md)?\s*\n", "", last_md)
        last_md = re.sub(r"\n```\s*$", "", last_md)

        ok, _nid = validator.validate(last_md)
        if ok:
            return {
                "prompt_id": prompt_cfg["id"],
                "model": model,
                "pass": True,
                "retries": retries,
                "errors": [],
                "elapsed_sec": round(time.time() - start, 2),
                "node_md": last_md[:200],
            }
        else:
            errors.extend([f"attempt {attempt}: {e}" for e in validator.errors])
            # 反馈重试
            feedback = validator.feedback_message()
            full_prompt = full_prompt + "\n\n" + (
                f"上一轮输出有问题：\n{feedback}\n\n请修复并重新输出节点 .md 片段。"
            )

    return {
        "prompt_id": prompt_cfg["id"],
        "model": model,
        "pass": False,
        "retries": retries,
        "errors": errors,
        "elapsed_sec": round(time.time() - start, 2),
        "node_md": last_md[:200],
    }


def print_summary(results: list[dict]) -> None:
    """打印汇总报告"""
    if not results:
        print("⚠️  无评测结果")
        return

    print("\n" + "=" * 80)
    print("📊 LLM 评测报告")
    print("=" * 80)

    # 按模型聚合
    by_model: dict[str, list[dict]] = {}
    for r in results:
        by_model.setdefault(r["model"], []).append(r)

    for model, items in by_model.items():
        total = len(items)
        passed = sum(1 for r in items if r["pass"])
        rate = passed / total * 100 if total else 0
        avg_retries = sum(r["retries"] for r in items) / total if total else 0
        avg_time = sum(r["elapsed_sec"] for r in items) / total if total else 0

        print(f"\n📦 {model}")
        print(f"   通过率: {passed}/{total} ({rate:.1f}%)")
        print(f"   平均重试: {avg_retries:.2f}")
        print(f"   平均耗时: {avg_time:.2f}s")

        print(f"\n   {'Prompt':<30} {'结果':<6} {'重试':<6} {'耗时':<8}")
        print("   " + "-" * 60)
        for r in items:
            status = "✅" if r["pass"] else "❌"
            print(f"   {r['prompt_id']:<30} {status:<6} {r['retries']:<6} {r['elapsed_sec']:.2f}s")

    print("\n" + "=" * 80)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LLM 评测脚本")
    p.add_argument("--prompts", type=Path, default=ROOT / "tests" / "eval_prompts.yaml",
                   help="评测集 YAML 路径")
    p.add_argument("--models", type=str, default=os.environ.get("EVAL_MODELS", "gpt-4o-mini"),
                   help="逗号分隔的模型列表")
    p.add_argument("--base-url", type=str, default=None,
                   help="API base URL（默认用 prompts 中的 default.base_url）")
    p.add_argument("--api-key", type=str, default=None,
                   help="API key（默认从 OPENAI_API_KEY 环境变量）")
    p.add_argument("--report", type=Path, default=None,
                   help="保存 JSON 报告路径")
    p.add_argument("--dry-run", action="store_true",
                   help="只看 prompt，不调 LLM（不需要 key）")
    args = p.parse_args(argv)

    prompts_data = load_prompts(args.prompts)
    prompts = prompts_data.get("prompts", [])
    defaults = prompts_data.get("defaults", {})

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY", "")
    base_url = args.base_url or defaults.get("base_url", "https://api.openai.com/v1")
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    # 加载世界
    world = World.from_yaml_dir(ROOT / "data")

    results: list[dict] = []

    if args.dry_run:
        print(f"🔍 Dry-run: {len(prompts)} 个 prompt × {len(models)} 个模型")
        for p in prompts:
            for m in models:
                results.append({
                    "prompt_id": p["id"],
                    "model": m,
                    "pass": None,
                    "retries": 0,
                    "errors": ["dry-run"],
                    "elapsed_sec": 0.0,
                    "node_md": "",
                })
    else:
        if not api_key:
            print("❌ 缺少 API key。请设置 OPENAI_API_KEY 或使用 --dry-run")
            return 1

        total = len(prompts) * len(models)
        print(f"🚀 评测 {len(prompts)} 个 prompt × {len(models)} 个模型 = {total} 次调用")

        for i, prompt_cfg in enumerate(prompts, 1):
            for model in models:
                idx = (i - 1) * len(models) + models.index(model) + 1
                print(f"\n[{idx}/{total}] {prompt_cfg['id']} × {model}")
                result = evaluate_one(prompt_cfg, model, base_url, api_key, world, defaults)
                results.append(result)
                status = "✅" if result["pass"] else "❌"
                print(f"   {status} 重试 {result['retries']} 次 · {result['elapsed_sec']}s")
                if not result["pass"]:
                    for err in result["errors"][:3]:
                        print(f"     - {err}")

    print_summary(results)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump({
                "config": {
                    "prompts_path": str(args.prompts),
                    "models": models,
                    "base_url": base_url,
                },
                "results": results,
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for r in results if r["pass"]),
                },
            }, f, ensure_ascii=False, indent=2)
        print(f"\n💾 报告已保存: {args.report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())