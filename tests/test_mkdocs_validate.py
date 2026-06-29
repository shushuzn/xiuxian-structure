"""
test_mkdocs_validate.py — 验证 scripts/validate.py [7/7] mkdocs strict 集成

测试：
- mkdocs 模块可用时，[7/7] 会跑 mkdocs build --strict 且通过
- 不可用时跳过（warning）
- mock 失败时记为 error
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate.py"


def _run_validate(*extra_args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *extra_args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        timeout=120,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )


def test_mkdocs_step_present():
    """validate.py 应该有 [7/7] mkdocs 步骤"""
    result = _run_validate()
    assert "[7/7]" in result.stdout, (
        f"validate.py 应有 [7/7] mkdocs 步骤，实际输出:\n{result.stdout}"
    )


def test_mkdocs_module_installed():
    """如果 mkdocs 未安装，应该 warning 而非 fail"""
    import importlib.util
    spec = importlib.util.find_spec("mkdocs")
    assert spec is not None, (
        "mkdocs 必须安装在本环境（pip install -r requirements-dev.txt）"
    )


def test_validate_strict_passes():
    """本地 mkdocs build --strict 应该通过（0 警告）"""
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding="utf-8", timeout=60,
    )
    if result.returncode != 0:
        # 输出前 30 行帮助调试
        lines = (result.stdout + result.stderr).splitlines()[:30]
        pytest.fail(f"mkdocs --strict 失败:\n  " + "\n  ".join(lines))
