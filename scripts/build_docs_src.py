#!/usr/bin/env python3
"""
build_docs_src.py — 同步 mkdocs 文档站源

背景：
- 项目根目录使用中文体系目录（如 境界体系/）存放真实 Markdown。
- mkdocs 需要一个统一的 docs_dir，因此使用 docs_src/ 作为镜像。
- docs_src/ 原本使用符号链接指向根目录文件，但在 Windows 上符号链接需要管理员权限，
  导致仓库被检出为只包含路径文本的“伪符号链接”，mkdocs 构建失败。

本脚本把根目录的 Markdown 文件和必要元文件复制到 docs_src/，保持相对路径结构，
使 mkdocs 在 Windows / macOS / Linux 上都能正常构建。

用法：
  python scripts/build_docs_src.py

CI 应在 mkdocs build 前运行此脚本。
"""
import shutil
import sys
from pathlib import Path

# Windows 控制台默认 GBK，无法输出 emoji
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DOCS_SRC = ROOT / "docs_src"

# 需要同步的目录：根目录相对路径 -> docs_src 相对路径
SYNC_DIRS = {
    "境界体系": "境界体系",
    "灵根体系": "灵根体系",
    "天地灵气": "天地灵气",
    "妖兽体系": "妖兽体系",
    "妖修体系": "妖修体系",
    "势力体系": "势力体系",
    "灵石体系": "灵石体系",
    "阵法体系": "阵法体系",
    "符箓体系": "符箓体系",
    "功法体系": "功法体系",
    "丹药体系": "丹药体系",
    "法器体系": "法器体系",
    "秘境体系": "秘境体系",
    "天材地宝体系": "天材地宝体系",
    "宗门体系": "宗门体系",
    "战斗体系": "战斗体系",
    "心魔体系": "心魔体系",
    "雷劫体系": "雷劫体系",
    "神识体系": "神识体系",
    "器灵体系": "器灵体系",
    "契约体系": "契约体系",
    "飞升体系": "飞升体系",
    "神界体系": "神界体系",
    "魔界体系": "魔界体系",
    "冥界体系": "冥界体系",
    "因果体系": "因果体系",
    "时空体系": "时空体系",
    "docs": "docs",
    "examples": "examples",
    "interactive": "interactive",
    "stories": "stories",
}

# 顶层元文件：根目录文件名 -> docs_src 文件名
SYNC_TOP_FILES = {
    "README.md": "index.md",
    "索引.md": "索引.md",
    "CHANGELOG.md": "CHANGELOG.md",
    "CONTRIBUTING.md": "CONTRIBUTING.md",
    "LICENSE": "LICENSE",
    "SECURITY.md": "SECURITY.md",
}


def clean_docs_src():
    """清空 docs_src 下所有内容（保留空目录本身）。"""
    if not DOCS_SRC.exists():
        DOCS_SRC.mkdir(parents=True)
        return
    for item in DOCS_SRC.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_tree(src: Path, dst: Path):
    """递归复制目录，只复制文件，保持目录结构。"""
    if not src.exists():
        print(f"⚠️  源目录不存在，跳过: {src.relative_to(ROOT)}", file=sys.stderr)
        return
    if not dst.exists():
        dst.mkdir(parents=True)
    for item in sorted(src.iterdir()):
        relative = item.relative_to(src)
        target = dst / relative
        if item.is_dir():
            copy_tree(item, target)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def copy_file(src: Path, dst: Path):
    """复制单个文件。"""
    if not src.exists():
        print(f"⚠️  源文件不存在，跳过: {src.relative_to(ROOT)}", file=sys.stderr)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main():
    print("🏗️  同步 docs_src/ 文档站源...")
    clean_docs_src()

    for src_name, dst_name in SYNC_TOP_FILES.items():
        copy_file(ROOT / src_name, DOCS_SRC / dst_name)

    for src_name, dst_name in SYNC_DIRS.items():
        copy_tree(ROOT / src_name, DOCS_SRC / dst_name)

    # .github/CODE_OF_CONDUCT.md 在 mkdocs nav 中被引用
    if (ROOT / ".github" / "CODE_OF_CONDUCT.md").exists():
        (DOCS_SRC / ".github").mkdir(parents=True, exist_ok=True)
        copy_file(
            ROOT / ".github" / "CODE_OF_CONDUCT.md",
            DOCS_SRC / ".github" / "CODE_OF_CONDUCT.md",
        )

    # 统计
    md_count = sum(1 for _ in DOCS_SRC.rglob("*.md"))
    print(f"✅ docs_src/ 同步完成：{md_count} 个 .md 文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
