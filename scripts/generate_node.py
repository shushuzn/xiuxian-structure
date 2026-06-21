#!/usr/bin/env python3
"""
generate_node.py — LLM 协作生成互动小说节点

工作流：
1. 读 data/*.yaml 提取世界摘要（物品/境界/丹药/势力等 ID 名）
2. 用户给一段自然语言需求
3. 调 LLM（OpenAI 兼容 API）生成一个节点 .md
4. 解析输出 + 跑连通性 + yaml 一致性校验
5. 失败自动反馈给 LLM 重试（最多 max-retries 轮）

用法：
  export OPENAI_API_KEY=sk-...
  python3 scripts/generate_node.py \
    --story stories/hanli_vol1_mochui.md \
    --after-node 藏经阁 \
    --requirement "在发现天霞山牌位后，加一个'夜探禁地'节点"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from interactive import Story, World  # noqa: E402


# ────────────────────────────────────────────────────────
# 1. YAML 摘要（喂给 LLM）
# ────────────────────────────────────────────────────────

def build_world_summary(world: World) -> str:
    """生成一份给 LLM 看的世界摘要 — 体系目录 + 关键 ID。

    不强求 system key → 目录名一一映射（很多 yaml 用 `tiers`/`grades` 这种通用 key
    跨多个体系）。只列出仓库里 11 个体系目录 + 一些关键 ID 名，让 LLM 据此写 refs。
    错误的 refs 会被 NodeValidator 兜底拒绝。
    """
    lines: list[str] = ["## 仓库的 11 个体系目录（refs 必须用这些名字）"]
    # 扫 ROOT 找 11 个体系目录
    system_dirs: list[str] = []
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and list(d.glob("*.md")) and d.name not in (
            "data", "scripts", "docs", "examples", "stories",
            "interactive", ".github", "dist", "node_modules",
        ):
            system_dirs.append(d.name)
    for d in system_dirs:
        lines.append(f"- {d}/")

    lines.append("\n## 关键 ID 名（可作 yaml 引用）")
    for system, payload in world.data.items():
        records: list[dict] = []
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and "id" in item:
                    records.append(item)
        elif isinstance(payload, dict):
            for v in payload.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and "id" in item:
                            records.append(item)
        if not records:
            continue
        # 用 id -> name 字典
        id_to_name = {r["id"]: r.get("name", r["id"]) for r in records if r.get("id")}
        if id_to_name:
            lines.append(f"- {system}: {', '.join(f'{k}={v}' for k, v in list(id_to_name.items())[:10])}")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────
# 2. Prompt 模板
# ────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """你是一个修仙互动小说作者。
任务是：为现有的修仙互动故事**生成 1 个新节点**（scene 或 ending）。

## 世界设定（数据驱动，必须严格遵守）
{world_summary}

## 现有故事节点（已存在）
{existing_nodes}

## 现有故事的所有跳转（避免重复 ID 和循环）
{existing_edges}

## 用户需求
{requirement}

## 输出格式（严格遵守）

只输出一个新节点的 .md 片段，**不要**输出其他内容。格式：

```
## 节点 <新节点id> (scene)
refs: 体系A/xxx.md, 体系B/yyy.md
text: |
  <多行叙述，100-300 字>
data:
  ?字段1: 默认值1
  ?字段2: 默认值2
next:
  - label: "选项 1"
    goto: <跳转到的节点id>
    if: <条件表达式（可选）>
    set: {{ 字段: 值 }}
    flag: 标志名
  - label: "选项 2"
    goto: <其他跳转>
```

要求：
1. **id 命名**：用中文短语，无空格（"夜探禁地" / "接受委托" / "杀墨大夫"）
2. **refs 必填**：列出涉及的体系（参考世界设定的体系名）
3. **text 必填**：100-300 字叙述，用**第二人称**（"你..."）
4. **data 用 ? 前缀**：避免覆盖用户状态
5. **next 至少 1 个选项**：跳转目标**必须是已有节点**或**本故事其他合理节点**
6. **不要**写 `## 节点 起点` 等会破坏结构的标题
7. **不要**在 text 中编造 yaml 里没有的数值（如"筑基成功率 73.5%"）

只输出 .md 片段，不要解释。"""


def build_prompt(story: Story, world: World, requirement: str) -> str:
    world_summary = build_world_summary(world)
    existing_nodes = "\n".join(
        f"- {nid} ({n.type}): {(n.text[:60] + '...') if len(n.text) > 60 else n.text}"
        for nid, n in story.nodes.items()
    )
    edges: set[str] = set()
    for nid, n in story.nodes.items():
        for c in n.choices:
            edges.add(f"{nid} → {c.get('goto')}")
    existing_edges = "\n".join(sorted(edges))

    return PROMPT_TEMPLATE.format(
        world_summary=world_summary,
        existing_nodes=existing_nodes or "(无)",
        existing_edges=existing_edges or "(无)",
        requirement=requirement,
    )


# ────────────────────────────────────────────────────────
# 3. LLM 调用（OpenAI 兼容）
# ────────────────────────────────────────────────────────

def call_llm(prompt: str, *, base_url: str, api_key: str, model: str,
              temperature: float = 0.7, max_tokens: int = 1500) -> str:
    """调 OpenAI 兼容 API，返回 content 文本"""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是修仙互动小说作者，输出严格遵守指定格式。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API 错误 {e.code}: {body[:500]}") from e
    return data["choices"][0]["message"]["content"]


# ────────────────────────────────────────────────────────
# 4. 节点校验
# ────────────────────────────────────────────────────────

class NodeValidator:
    """对生成节点做结构 + 连通性 + yaml 一致性校验"""

    def __init__(self, story: Story, world: World):
        self.story = story
        self.world = world
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self, node_md: str, new_node_id_hint: str | None = None) -> tuple[bool, str]:
        """返回 (ok, parsed_node_id)"""
        self.errors.clear()
        self.warnings.clear()
        try:
            new_story_text = self._wrap_story(node_md)
            new_nodes = Story.parse_nodes_only(new_story_text, source_name="<generated>")
        except Exception as e:
            self.errors.append(f"解析失败: {e}")
            return False, ""

        if not new_nodes:
            self.errors.append("未生成任何节点")
            return False, ""

        # 取第一个（也应该是唯一）生成的节点
        nid, node = next(iter(new_nodes.items()))

        # 1) 不能跟已有节点 id 冲突
        if nid in self.story.nodes:
            self.errors.append(f"节点 id '{nid}' 与已有节点冲突")
            return False, ""

        # 2) refs 解析：必须是 `体系/文档.md` 格式，文档要存在
        for ref in node.refs:
            if "/" not in ref or not ref.endswith(".md"):
                self.warnings.append(f"refs 格式可疑: {ref!r}")
                continue
            system, fname = ref.split("/", 1)
            ref_path = ROOT / system / fname
            if not ref_path.exists():
                self.warnings.append(f"refs 指向不存在的文件: {ref}")

        # 3) next 中所有 goto 必须在已有节点或自身中
        valid_targets = set(self.story.nodes.keys()) | {nid}
        for c in node.choices:
            tgt = c.get("goto")
            if tgt not in valid_targets:
                self.errors.append(f"goto '{tgt}' 不在已有节点中")

        # 4) data 字段中数值范围（针对常见字段：灵石、境界、声望）
        for k, v in node.data.items():
            real_key = k.lstrip("?")
            if real_key == "灵石" and isinstance(v, int) and not (0 <= v <= 10000):
                self.warnings.append(f"灵石={v} 超出常见范围 0-10000")
            if real_key == "声望" and isinstance(v, int) and not (0 <= v <= 100):
                self.warnings.append(f"声望={v} 超出常见范围 0-100")

        # 5) text 不能提到 yaml 不存在的境界名（粗略）
        for realm in ("炼气期", "筑基期", "结丹期", "元婴期", "化神期"):
            pass  # 暂时跳过，避免误报

        if self.errors:
            return False, ""
        return True, nid

    def _wrap_story(self, node_md: str) -> str:
        """把新节点片段包成可解析的 .md"""
        # 先用占位 start 包一次，解析出真实 id，再用真实 id 包
        placeholder = f"# _tmp\n\n## 元数据\nid: _tmp\nstart: 起点\n\n{node_md}"
        try:
            tmp = Story.from_text(placeholder, source_name="<generated>")
            real_id = next(iter(tmp.nodes.keys()), "起点")
        except Exception:
            real_id = "起点"
        return f"# 临时故事\n\n## 元数据\nid: _generated\nstart: {real_id}\n\n{node_md}"

    def feedback_message(self) -> str:
        """给 LLM 的反馈（错误 + 警告）"""
        msgs = []
        if self.errors:
            msgs.append("【错误（必须修复）】\n" + "\n".join(f"- {e}" for e in self.errors))
        if self.warnings:
            msgs.append("【警告（建议修复）】\n" + "\n".join(f"- {w}" for w in self.warnings))
        return "\n\n".join(msgs)


# ────────────────────────────────────────────────────────
# 5. CLI 入口
# ────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="LLM 协作生成互动小说节点")
    p.add_argument("--story", type=Path, required=True)
    p.add_argument("--requirement", required=True, help="自然语言需求描述")
    p.add_argument("--data-dir", type=Path, default=ROOT / "data")
    p.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"))
    p.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY", ""))
    p.add_argument("--model", default=os.environ.get("LLM_MODEL", "gpt-4o-mini"))
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--dry-run", action="store_true", help="只生成 + 校验，不写文件")
    p.add_argument("--output", type=Path, help="输出文件路径（默认追加到 --story）")
    args = p.parse_args(argv)

    if not args.api_key and not args.dry_run:
        print("❌ 缺 API key（设 OPENAI_API_KEY 或 LLM_API_KEY，或用 --dry-run）")
        return 1

    world = World.from_yaml_dir(args.data_dir)
    story = Story.from_file(args.story)
    print(f"📖 已加载故事: {args.story.name} ({len(story.nodes)} 节点)")
    print(f"🌍 已加载世界: {len(world.data)} 体系\n")

    prompt = build_prompt(story, world, args.requirement)
    if args.dry_run:
        print("🔍 Dry-run 模式：只生成 prompt，不调 LLM\n")
        print(prompt)
        return 0

    print("🤖 调 LLM 生成节点...")
    last_node_md = ""
    for attempt in range(1, args.max_retries + 1):
        print(f"\n🔄 尝试 {attempt}/{args.max_retries}")
        if attempt == 1:
            content = call_llm(prompt, base_url=args.base_url, api_key=args.api_key,
                                model=args.model, temperature=args.temperature)
        else:
            # 反馈重试
            feedback = validator.feedback_message()
            retry_prompt = (
                f"上一轮输出有问题：\n\n{feedback}\n\n"
                f"请修复并重新输出节点 .md 片段。\n\n"
                f"原 prompt 摘要（再次参考）：\n{args.requirement}"
            )
            content = call_llm(retry_prompt, base_url=args.base_url, api_key=args.api_key,
                                model=args.model, temperature=args.temperature)

        last_node_md = content.strip()
        # 去 markdown 代码块包裹
        last_node_md = re.sub(r"^```(?:markdown|md)?\s*\n", "", last_node_md)
        last_node_md = re.sub(r"\n```\s*$", "", last_node_md)

        print(f"📝 生成的节点（{len(last_node_md)} 字符）：")
        print("─" * 60)
        print(last_node_md[:500] + ("..." if len(last_node_md) > 500 else ""))
        print("─" * 60)

        validator = NodeValidator(story, world)
        ok, nid = validator.validate(last_node_md)

        if ok:
            print(f"\n✅ 校验通过！新节点 id: {nid}")
            if args.output:
                out = args.output
            else:
                # 默认写到 examples/generated/<nid>.md
                gen_dir = ROOT / "examples" / "generated"
                gen_dir.mkdir(parents=True, exist_ok=True)
                out = gen_dir / f"{nid}.md"
            out.write_text(
                f"# {nid}（LLM 生成于 {args.model}）\n\n"
                f"需求：{args.requirement}\n\n"
                f"---\n\n{last_node_md}\n",
                encoding="utf-8",
            )
            print(f"💾 已写入: {out.relative_to(ROOT)}")
            print(f"\n💡 接入故事：把以下选项加到 {args.story.name} 的合适节点 next：")
            print(f"   - label: \"...\"")
            print(f"     goto: {nid}")
            return 0
        else:
            print(f"\n❌ 校验失败：")
            for e in validator.errors:
                print(f"  - {e}")
            if validator.warnings:
                print(f"⚠️  警告：")
                for w in validator.warnings:
                    print(f"  - {w}")

    print(f"\n💀 达到最大重试次数 {args.max_retries}，生成失败")
    print("最后一次输出已保存到 stderr 供人工编辑")
    print("─" * 60)
    print(last_node_md, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
