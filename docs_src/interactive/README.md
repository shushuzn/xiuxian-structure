# interactive/ — 互动小说引擎

> **状态机驱动的修仙互动叙事**，由 `data/*.yaml` 喂数据，`stories/*.md` 写剧本。

## 是什么

传统的「知识库」是被读的资料。`interactive.py` 把知识库升级为**运行时世界数据库** —— 互动小说引擎通过查询 `data/*.yaml` 来确保剧情符合设定。

## 快速试玩

```bash
# 交互模式（手动选）
python3 scripts/interactive.py --story stories/demo_measuring_spirit.md

# Headless 模式（自动选第一有效选项，用于 CI）
python3 scripts/interactive.py --story stories/demo_measuring_spirit.md --headless
```

## 写一个新故事

每个故事是一个 `.md` 文件，结构：

```markdown
# 故事标题

## 元数据
id: 唯一id
description: 一句话简介
start: 起点节点id

## 节点 起点 (scene)

type: scene            # scene | ending（可省略，标题里 (scene/ending) 标识）
refs: 灵根体系/灵根.md, 符箓体系/火球符.md   # 知识引用，自动渲染为链接
text: |
  多行叙述文本...
  支持 {realms.炼气期.lifespan} 这种 yaml 占位符。
data:
  ?主角: 韩立      # ? 前缀：仅当未设置时初始化（不覆盖用户存档）
  ?灵石: 5
  ?境界: 凡人
next:
  - label: "选项文字"
    goto: 下一节点id
    if: 灵石 >= 3           # 条件表达式（可选）
    set: { 灵石: 2 }        # 选中后修改状态（可选）
    flag: 拜师               # 选中后设置标志（可选）

## 节点 结局 (ending)

type: ending
text: |
  🏁 结局描述...
```

### 状态机制

- **data 块**：节点进入时设置状态
  - 普通 key（`灵石: 5`）：总是覆盖
  - `?` 前缀 key（`?灵石: 5`）：仅当未设置时初始化（**推荐用于初始化字段**）
- **choice 副作用**：
  - `set: { 灵石: 2 }` — 合并到 attrs
  - `flag: 拜师` — 加入 flags
- **条件表达式**：节点的 `if:` 字段
  - 支持：`>=`, `<=`, `==`, `!=`, `>`, `<`, `and`, `or`, `not`
  - 特殊：`flag.标志名` 检查标志

### 模板占位符

文本中 `{体系.记录.字段}` 会被替换为 yaml 实际值：

```
你的寿元是 {realms.炼气期.lifespan} 年。
# → 你的寿元是 120 年。
```

## 程序化 API

```python
from interactive import World, Story, Engine, State

world = World.from_yaml_dir("data")
story = Story.from_file("stories/demo_measuring_spirit.md")

# 方式 1：完全手动状态
state = State({"灵石": 10, "灵根": "伪灵根"})
engine = Engine(world, story, state)
# engine.play()  # 交互
# engine.step(0)  # 单步

# 方式 2：存档/读档
import json
save = engine.save()
# ... 玩家退出
engine2 = Engine.load(world, story, save)
```

## 架构

```
data/*.yaml (世界数据)
    ↓ World.from_yaml_dir()
World (内存 dict，World.lookup / World.find_by_id)
    ↓
Story.from_file(stories/xxx.md)  # 自创 DSL
    ↓
Engine.play() / Engine.step()  # 状态机 + 条件求值
    ↓
终端 / CI / 未来的 Web UI
```

## 下一步

- 写 `examples/feed-to-llm.md` 引导 LLM 据 yaml 自动生成故事节点
- 写 `examples/consume-interactive.py` 程序化驱动 demo
- 写 v1.2.0 完整故事「韩立的修行路」（10+ 节点、4 结局）
- 集成 FastAPI 做 Web UI
