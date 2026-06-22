#!/usr/bin/env python3
"""
batch_generate.py — 批量扩写脚本（v2.2 新增）

用法：
  export OPENAI_API_KEY=sk-...
  python3 scripts/batch_generate.py \
    --prompts tests/eval_prompts.yaml \
    --output examples/generated_batch/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from interactive import Story, World  # noqa: E402
from generate_node import NodeValidator, build_prompt, call_llm  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="批量扩写节点")
    p.add_argument("--prompts", type=Path, required=True, help="批量 prompt YAML")
    p.add_argument("--output", type=Path, default=ROOT / "examples" / "generated_batch",
                   help="输出目录")
    p.add_argument("--model", type=str, default="gpt-4o-mini")
    p.add_argument("--temperature", type=float, default=0.3)
    p.add_argument("--base-url", type=str, default="https://api.openai.com/v1")
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--dry-run", action="store_true", help="只看配置不调 LLM")
    args = p.parse_args(argv)

    import os
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY", "")

    with open(args.prompts, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    prompts = data.get("prompts", [])

    world = World.from_yaml_dir(ROOT / "data")
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"📦 批量生成 {len(prompts)} 个节点 → {args.output}")

    for i, cfg in enumerate(prompts, 1):
        story_path = ROOT / "stories" / f"{cfg['story']}.md"
        if not story_path.exists():
            print(f"  [{i}] ❌ 故事不存在: {story_path}")
            continue
        story = Story.from_file(story_path)
        prompt = build_prompt(story, world, cfg["requirement"])
        validator = NodeValidator(story, world)

        if args.dry_run:
            print(f"  [{i}] 🔍 (dry-run) {cfg['id']}")
            continue

        try:
            content = call_llm(
                prompt,
                base_url=args.base_url,
                api_key=api_key,
                model=args.model,
                temperature=args.temperature,
            )
        except Exception as e:
            print(f"  [{i}] ❌ API 失败: {e}")
            continue

        # 去 markdown 包裹
        import re
        content = re.sub(r"^```(?:markdown|md)?\s*\n", "", content.strip())
        content = re.sub(r"\n```\s*$", "", content)

        ok, nid = validator.validate(content)
        out_path = args.output / f"{nid or cfg['id']}.md"
        header = (
            f"# {nid or cfg['id']}（批量生成于 {args.model}）\n\n"
            f"需求：{cfg['requirement']}\n\n"
            f"状态：{'✅ 通过 NodeValidator' if ok else '❌ 验证失败'}\n\n"
            f"---\n\n"
        )
        out_path.write_text(header + content + "\n", encoding="utf-8")

        status = "✅" if ok else "❌"
        print(f"  [{i}] {status} {cfg['id']} → {out_path.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())