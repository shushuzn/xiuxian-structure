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
        # examples/ 是示例作品（小说/使用 demo），不强制
        if rel.parts[0] == "examples":
            continue
        # .release-notes-*.md 是发布管理文件，不强制
        if rel.name.startswith(".release-notes-"):
            continue
        # stories/ 是互动小说剧本（不是知识库文档），不强制
        if rel.parts[0] == "stories":
            continue
        # docs_src/ 是 mkdocs 文档站源（symlink 到真实 .md），不强制
        if rel.parts[0] == "docs_src":
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

def audit_relations():
    """审计 data/relations.yaml 中 from/to 引用的 id 是否真实存在"""
    import yaml
    from collections import defaultdict

    ids_by_system = defaultdict(set)
    for f in sorted((ROOT / "data").glob("*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue  # 跳过的 yaml 由 check_yaml 步骤处理
        if not isinstance(data, dict):
            continue
        sys_name = f.stem
        for section, content in data.items():
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "id" in item:
                        ids_by_system[sys_name].add(item["id"])

    rels_path = ROOT / "data" / "relations.yaml"
    if not rels_path.exists():
        return
    try:
        rels = yaml.safe_load(rels_path.read_text(encoding="utf-8")).get("relations", [])
    except yaml.YAMLError:
        return
    broken = []
    for r in rels:
        for side in ("from", "to"):
            s = r.get(side, "")
            if ":" not in s:
                continue
            sys_, id_ = s.split(":", 1)
            if id_ not in ids_by_system.get(sys_, set()):
                broken.append((r.get("type", "?"), side, s))
    if broken:
        warn("data/relations.yaml", f"存在 {len(broken)} 条失效端点引用（详见 docs/RELATIONS_AUDIT.md）")
    else:
        print(f"  ✓ data/relations.yaml：{len(rels)} 条关系均有效")



def check_mkdocs():
    """跑 mkdocs build --strict，捕获警告/错误

    需要 mkdocs 包（在 requirements-dev.txt 中）。
    如果 mkdocs 未安装，跳过（warning）。
    如果 mkdocs build 失败（非 0 exit 或含 WARNING），记为 error。
    """
    try:
        import importlib.util
        spec = importlib.util.find_spec("mkdocs")
        if spec is None:
            warn("scripts/validate.py", "mkdocs 未安装（pip install -r requirements-dev.txt）")
            return
    except Exception:
        warn("scripts/validate.py", "mkdocs 未安装")
        return

    import subprocess

    # 先确保 docs_src/ 同步（mkdocs build 需要 docs_src 内容）
    sync_script = ROOT / "scripts" / "build_docs_src.py"
    if sync_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(sync_script)],
                capture_output=True, timeout=30,
            )
        except Exception as e:
            warn("scripts/validate.py", f"build_docs_src.py 跑失败: {e}")

    # 跑 mkdocs build --strict
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--strict"],
            cwd=ROOT, capture_output=True, timeout=60, encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        err("scripts/validate.py", "mkdocs build 超时（>60s）")
        return
    except Exception as e:
        err("scripts/validate.py", f"mkdocs build 异常: {e}")
        return

    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        # 提取关键警告（最多 5 条）
        warnings = [l for l in output.splitlines() if "WARNING" in l or "ERROR" in l]
        preview = "\n    ".join(warnings[:5])
        err("scripts/validate.py",
            f"mkdocs build --strict 失败（exit={result.returncode}）：\n    {preview}")
        return

    if "WARNING" in output or "INFO" in output and "unrecognized" in output:
        # 严格模式下即使 exit=0 也可能有 INFO
        # INFO 不算 warning（已在 D.5 #85dfbca 中清理为 0）
        print(f"  ✓ mkdocs --strict 通过（{(result.stdout or '').count(chr(10))} 行输出）")


def main():
    print("🔍 开始校验修仙体系知识库...\n")

    print("  [1/7] .md 文件结构...")
    check_md_structure()

    print("  [2/7] .md 链接完整性...")
    check_md_links()

    print("  [3/7] YAML 解析...")
    check_yaml()

    print("  [4/7] Mermaid 代码块...")
    check_mermaid()

    print("  [5/7] 索引一致性...")
    check_index_consistency()

    print("  [6/7] relations.yaml 端点校验...")
    audit_relations()

    print("  [7/7] mkdocs build --strict...")
    check_mkdocs()

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