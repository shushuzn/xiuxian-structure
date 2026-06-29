"""
test_performance.py — 性能基准测试（D.6）

测量关键操作的耗时，作为性能 baseline。
CI 中可通过 `--benchmark-only` 运行。
"""
import time
import pytest
from pathlib import Path
import yaml
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from interactive import World, State, Engine, Story  # noqa: E402

DATA_DIR = ROOT / "data"


# ── 性能阈值（秒）──
# D.6 性能优化目标值，超过则失败
# 25 yaml 文件 + World 缓存的合理目标
THRESHOLDS = {
    "yaml_load_all": 2.0,        # 加载所有 yaml < 2s (25 文件)
    "world_init": 2.0,           # World 初始化 < 2s (含 yaml 加载)
    "build_graph": 5.0,          # build_graph.py < 5s (子进程开销)
    "story_parse": 1.0,          # 解析单个 story < 1s
    "engine_init": 0.5,          # Engine 初始化 < 0.5s
}


def _time_func(func, *args, **kwargs):
    """测量函数执行时间"""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return result, elapsed


def test_yaml_load_all_performance():
    """所有 yaml 加载性能"""
    def load_all():
        for f in sorted(DATA_DIR.glob("*.yaml")):
            with open(f, encoding="utf-8") as fh:
                yaml.safe_load(fh)
    _, elapsed = _time_func(load_all)
    assert elapsed < THRESHOLDS["yaml_load_all"], \
        f"yaml loading 耗时 {elapsed:.3f}s > {THRESHOLDS['yaml_load_all']}s"


def test_world_init_performance():
    """World 初始化性能"""
    _, elapsed = _time_func(World.from_yaml_dir, DATA_DIR)
    assert elapsed < THRESHOLDS["world_init"], \
        f"World 初始化耗时 {elapsed:.3f}s > {THRESHOLDS['world_init']}s"


def test_build_graph_performance():
    """build_graph 性能"""
    import subprocess
    start = time.time()
    r = subprocess.run(
        ["python3", "scripts/build_graph.py", "--stats"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
    )
    elapsed = time.time() - start
    assert r.returncode == 0, f"build_graph failed: {r.stderr.decode()}"
    assert elapsed < THRESHOLDS["build_graph"], \
        f"build_graph 耗时 {elapsed:.3f}s > {THRESHOLDS['build_graph']}s"


def test_story_parse_performance():
    """单 story 解析性能"""
    story_path = ROOT / "stories" / "v31_demo.md"
    if not story_path.exists():
        pytest.skip("v31_demo.md 不存在")
    def parse():
        Story.from_file(story_path)
    _, elapsed = _time_func(parse)
    assert elapsed < THRESHOLDS["story_parse"], \
        f"story 解析耗时 {elapsed:.3f}s > {THRESHOLDS['story_parse']}s"


def test_engine_init_performance():
    """Engine 初始化性能"""
    world = World.from_yaml_dir(DATA_DIR)
    story_text = """# test
## 元数据
id: perf
start: s
## 节点 s (ending)
text: end
"""
    story = Story.from_text(story_text)
    def init_engine():
        Engine(world, story, State())
    _, elapsed = _time_func(init_engine)
    assert elapsed < THRESHOLDS["engine_init"], \
        f"Engine 初始化耗时 {elapsed:.3f}s > {THRESHOLDS['engine_init']}s"


def test_world_cache_benefit():
    """验证 World 缓存可受益（多次调用 vs 单次）"""
    # 第一次加载
    start = time.time()
    World.from_yaml_dir(DATA_DIR)
    first = time.time() - start
    # 第二次加载（应该快得多因为缓存）
    start = time.time()
    World.from_yaml_dir(DATA_DIR)
    second = time.time() - start
    # 缓存版本（用 _world）更快
    start = time.time()
    for _ in range(5):
        World.from_yaml_dir(DATA_DIR)
    five = time.time() - start
    # 缓存函数测试
    sys.path.insert(0, str(ROOT / "tests"))
    from test_interactive import _world
    start = time.time()
    for _ in range(5):
        _world()
    five_cached = time.time() - start
    # 缓存版本应该明显快于未缓存版本
    assert five_cached < five, \
        f"缓存版本 {five_cached:.4f}s 不应慢于未缓存 {five:.4f}s"


def test_performance_summary(capsys):
    """性能 summary (D.6 性能报告)"""
    measurements = {}

    # 测 World
    start = time.time()
    world = World.from_yaml_dir(DATA_DIR)
    measurements["world_init"] = time.time() - start

    # 测 yaml 全部
    start = time.time()
    for f in sorted(DATA_DIR.glob("*.yaml")):
        with open(f, encoding="utf-8") as fh:
            yaml.safe_load(fh)
    measurements["yaml_all"] = time.time() - start

    # 测 Engine
    story = Story.from_text("""# test
## 元数据
id: p
start: s
## 节点 s (ending)
text: end
""")
    start = time.time()
    Engine(world, story, State())
    measurements["engine_init"] = time.time() - start

    # 打印结果
    print("\n📊 D.6 性能报告:")
    for k, v in sorted(measurements.items()):
        status = "✅" if v < THRESHOLDS.get(k, 999) else "❌"
        print(f"  {status} {k}: {v*1000:.1f}ms (阈值: {THRESHOLDS.get(k, 999)*1000:.0f}ms)")
