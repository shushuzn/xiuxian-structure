# examples/consume-interactive.py

> 程序化消费互动小说故事的 4 个高层 API。

## 为什么需要这层 API？

`scripts/interactive.py` 提供底层 `Engine` 用来"玩"一个故事（CLI / 打印），
但下游消费者（前端、LLM 工具、批量分析、CI 校验）通常只想问**结构性问题**：

- 这个故事长什么样？
- 一共有多少结局？怎么走？
- 选 A 一直走下去会怎样？选 B 呢？
- 最少几步能到某个结局？
- 整个故事能不能塞进一个 JSON？

这层 API 把"游玩"和"分析"分开：你不需要创建 Engine/State 也能回答这些问题。

## 四个 API

| API | 用途 | 返回 |
|---|---|---|
| `analyze_story(path)` | 故事统计 | dict（节点/分支/可达性/结局） |
| `walk_all_paths(path)` | 遍历所有可能路径 | list[dict]（每条线的 steps + choices） |
| `find_shortest_path(path, from_id, to_id)` | BFS 找最短决策链 | dict 或 None（不可达） |
| `export_to_json(path)` | 故事结构 → JSON | dict（meta + nodes） |

## 设计原则

- **零副作用**：不创建 Engine，不写文件（`export_to_json` 写文件是显式 opt-in）
- **不读 yaml**：这些 API 只关心故事结构，不依赖世界数据
- **可组合**：返回纯 `dict` / `list`，可被其他脚本二次处理
- **零参数也能跑**：默认分析 `stories/hanli_vol1_mochui.md`

## 用法

```bash
# 1. 统计
python3 examples/consume-interactive.py analyze stories/hanli_vol1_mochui.md

# 2. 遍历所有路径
python3 examples/consume-interactive.py walk stories/hanli_vol1_mochui.md

# 3. 找最短路径
python3 examples/consume-interactive.py path stories/hanli_vol1_mochui.md \
    --from 托付 --to 杀墨

# 4. 导出 JSON
python3 examples/consume-interactive.py export stories/hanli_vol1_mochui.md \
    --output /tmp/hanli.json
```

## 在 Python 代码中调用

```python
import sys
sys.path.insert(0, "examples")
from consume_interactive import analyze_story, walk_all_paths, find_shortest_path, export_to_json

stats = analyze_story("stories/hanli_vol1_mochui.md")
print(f"结局数: {stats['ending_count']}, 完整: {stats['is_well_formed']}")

paths = walk_all_paths("stories/hanli_vol1_mochui.md")
print(f"共 {len(paths)} 条路径")

shortest = find_shortest_path("stories/hanli_vol1_mochui.md", "托付", "杀墨")
print(f"最短: {shortest['length']} 步")

import json
data = export_to_json("stories/hanli_vol1_mochui.md")
# data["meta"] — 故事统计
# data["nodes"] — {节点id: {type, text, data, refs, choices}}
```

## 输出示例（analyze）

```
📖 故事分析: hanli_vol1_mochui.md
============================================================
  id:           hanli_vol1
  title:        散修韩立·第一卷：墨大夫的阴谋
  start_node:    托付
  node_count:    18  (scene: 13, ending: 5)
  reachable:     18 / 18
  max_depth:     6 步 (从 start 到 ending)
  branch_points: 7 个
  conditional_choices: 0 个带 if 条件
  refs:          29 (去重 16)
  ✅ is_well_formed
============================================================
```

## CI 集成

`validate.yml` 新增 step `Verify consume-interactive API works`：

```bash
python3 examples/consume-interactive.py analyze stories/hanli_vol1_mochui.md
python3 examples/consume-interactive.py walk stories/demo_measuring_spirit.md
```

任何故事如果 `is_well_formed=False`（孤儿节点 / start 不存在），CI 会 fail。

## 注意事项

- **`walk_all_paths` 不应用条件过滤**：即便某选项有 `if:` 限制，遍历也照常走
  （条件过滤是 Engine 的职责，本 API 只问结构）
- **`walk_all_paths` 防爆栈**：默认 `max_paths=200`，超过会截断
- **死循环防护**：单条路径超过 50 步视为 `loop_or_invalid`
