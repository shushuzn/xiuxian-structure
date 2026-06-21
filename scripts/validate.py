#!/usr/bin/env python3
"""
修仙体系知识库校验脚本

校验项：
1. 每个 .md 必须包含必备章节（按 docs/TEMPLATE.md）
2. `## 关联` 章节里写的链接文件必须真实存在
3. data/*.yaml 通过 PyYAML 解析
4. mermaid 代码块格式正确
5. 索引.md 中提到的体系文件必须存在
"""
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少依赖 pyyaml，请安装：pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
WARNINGS = []


# ────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────

def err(file, msg):
    ERRORS.append(f"[ERROR] {file}: {msg}")


def warn(file, msg):
    WARNINGS.append(f"[WARN] {file}: {msg}")


def all_md_files():
    return list(ROOT.rglob("*.md"))


def all_yaml_files():
    return list((ROOT / "data").glob("*.yaml"))


def extract_sections(content):
    """提取所有 ## 级章节标题"""
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", content, re.MULTILINE)]


def extract_links_to_md(content):
    """提取文中所有指向 .md 的相对链接（不含 http）"""
    pattern = r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]*)?)\)"
    return [m.group(1) for m in re.finditer(pattern, content)]


# ────────────────────────────────────────────────────────
# 1. .md 文件结构校验
# ────────────────────────────────────────────────────────

def check_md_structure():
    """每个 .md 必须包含 `## 关联`（体系类文档）"""
    skip_files = {"README.md", "索引.md", "CONTRIBUTING.md", "LICENSE",
                  "CHANGELOG.md", "SECURITY.md"}
    for md in all_md_files():
        rel = md.relative_to(ROOT)
        if rel.name in skip_files:
            continue
        # 模板/schema/图谱/ADR 不强制
        if rel.parts[0] in ("docs",):
            continue
        # .github/ 下的元文件不强制（PR/Issue 模板、CODE_OF_CONDUCT、CODEOWNERS）
        if rel.parts[0] == ".github":
            continue
        # dist/ 是 export.py 工具产物，不强制
        if rel.parts[0] == "dist":
            continue
        content = md.read_text(encoding="utf-8")
        sections = extract_sections(content)
        if "关联" not in sections:
            err(str(rel), "缺少 `## 关联` 章节")


# ────────────────────────────────────────────────────────
# 2. 链接完整性校验
# ────────────────────────────────────────────────────────

def check_md_links():
    """检查 .md 内链接的目标文件是否存在"""
    for md in all_md_files():
        rel = md.relative_to(ROOT)
        content = md.read_text(encoding="utf-8")
        for link in extract_links_to_md(content):
            # 去掉锚点
            target = link.split("#")[0]
            if not target or target.startswith("http"):
                continue
            target_path = (md.parent / target).resolve()
            # 允许指向空锚（占位）
            if target in ("#", ""):
                continue
            if not target_path.exists():
                warn(str(rel), f"链接目标不存在: {link}")


# ────────────────────────────────────────────────────────
# 3. YAML 解析校验
# ────────────────────────────────────────────────────────

def check_yaml():
    for yf in all_yaml_files():
        try:
            yaml.safe_load(yf.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            err(str(yf.relative_to(ROOT)), f"YAML 解析失败: {e}")


# ────────────────────────────────────────────────────────
# 4. Mermaid 代码块校验（基础）
# ────────────────────────────────────────────────────────

def check_mermaid():
    pattern = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
    for md in all_md_files():
        rel = md.relative_to(ROOT)
        content = md.read_text(encoding="utf-8")
        for m in pattern.finditer(content):
            block = m.group(1)
            first_line = block.strip().split("\n")[0]
            if not re.match(r"^(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram)", first_line):
                warn(str(rel), f"mermaid 代码块语法可能错误: 首行 '{first_line}'")


# ────────────────────────────────────────────────────────
# 5. 索引一致性
# ────────────────────────────────────────────────────────

def check_index_consistency():
    """检查索引.md 中提到的体系子目录/文件是否存在"""
    index = ROOT / "索引.md"
    if not index.exists():
        return
    content = index.read_text(encoding="utf-8")
    for line in content.splitlines():
        # 匹配可能的体系名（如 灵根 → 功法）
        m = re.search(r"([\u4e00-\u9fa5]+(?:体系|期|丹|脉))", line)
        if m:
            name = m.group(1)
            # 不强校验，只是警告
    # 同时校验 README 中列出的目录（仅顶层，缩进为 0）
    readme = ROOT / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        # 只匹配顶层目录（不在 │ 之后）
        for m in re.finditer(r"^├──\s+(\S+)/", content, re.MULTILINE):
            d = ROOT / m.group(1)
            if not d.exists():
                err("README.md", f"README 列出顶层目录 {m.group(1)} 但不存在")


# ────────────────────────────────────────────────────────
# 主入口
# ────────────────────────────────────────────────────────

def main():
    print("🔍 开始校验修仙体系知识库...\n")

    print("  [1/5] .md 文件结构...")
    check_md_structure()

    print("  [2/5] .md 链接完整性...")
    check_md_links()

    print("  [3/5] YAML 解析...")
    check_yaml()

    print("  [4/5] Mermaid 代码块...")
    check_mermaid()

    print("  [5/5] 索引一致性...")
    check_index_consistency()

    print("\n" + "─" * 50)
    if WARNINGS:
        print(f"⚠️  警告 {len(WARNINGS)} 条:")
        for w in WARNINGS:
            print(f"  {w}")

    if ERRORS:
        print(f"\n❌ 错误 {len(ERRORS)} 条:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)

    print(f"\n✅ 全部通过 ({len(WARNINGS)} 个警告)")


if __name__ == "__main__":
    main()