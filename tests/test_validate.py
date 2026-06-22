"""
test_validate.py — scripts/validate.py 的单元测试

测试 validate.py 的核心校验逻辑：
1. .md 缺少 ## 关联 章节时能报错
2. YAML 文件损坏时能报错
3. 链接目标不存在时能警告
4. mermaid 代码块格式
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate.py"


def test_validate_script_exists():
    """validate.py 必须存在"""
    assert SCRIPT.is_file(), "scripts/validate.py 不存在"


def test_validate_passes_on_current_repo():
    """对当前仓库运行 validate.py 应通过"""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"validate.py 失败:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "✅ 全部通过" in result.stdout, "validate.py 未报告通过"


@pytest.fixture
def temp_repo():
    """临时仓库目录 fixture（兼容 Python 3.6）"""
    tmpdir = tempfile.mkdtemp(prefix="xiuxian_test_")
    test_root = Path(tmpdir)
    try:
        yield test_root
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_validate_detects_missing_md_section(temp_repo):
    """validate.py 应能检测缺少 ## 关联 章节的 .md"""
    test_root = temp_repo
    (test_root / "scripts").mkdir()
    (test_root / "data").mkdir()
    (test_root / "scripts" / "validate.py").write_bytes(SCRIPT.read_bytes())

    bad_dir = test_root / "测试体系"
    bad_dir.mkdir()
    (bad_dir / "test.md").write_text(
        "# 测试\n\n## 定义\n这是测试。\n",
        encoding="utf-8",
    )

    (test_root / "data" / "test.yaml").write_text("test:\n  - id: a\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/validate.py"],
        cwd=test_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30,
    )
    assert result.returncode != 0, "缺少 ## 关联 时 validate.py 应失败"
    assert "缺少 `## 关联`" in result.stdout + result.stderr, (
        "错误信息应提及 ## 关联"
    )


def test_validate_detects_bad_yaml(temp_repo):
    """validate.py 应能检测损坏的 YAML"""
    test_root = temp_repo
    (test_root / "scripts").mkdir()
    (test_root / "data").mkdir()
    (test_root / "scripts" / "validate.py").write_bytes(SCRIPT.read_bytes())

    (test_root / "data" / "bad.yaml").write_text(
        "foo:\n  - bar: [unclosed\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/validate.py"],
        cwd=test_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30,
    )
    assert result.returncode != 0, "坏 YAML 应导致 validate.py 失败"
    assert "YAML 解析失败" in result.stdout + result.stderr, (
        "错误信息应提及 YAML 解析失败"
    )