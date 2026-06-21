# 互动小说剧本（stories/）

> 本目录存放**互动小说剧本**，由 `scripts/interactive.py` 引擎解析并可执行游玩。

## 📚 现有剧本

| 文件 | 规模 | 路线数 | 体系数 | 视角 |
|---|---|---|---|---|
| `demo_measuring_spirit.md` | 5 节点 / 2 结局 / 4 路线 | 测灵殿选择 demo | 5 体系 | 第三人称 |
| `hanli_vol1_mochui.md` | 18 节点 / 5 结局 / 11 路线 | 散修韩立·第一卷：墨大夫的阴谋 | 8 体系 | 韩立 |
| `hanli_vol2_yuanzou.md` | 30 节点 / 5 结局 / 600+ 路线 | 散修韩立·第二卷：远走与南陇侯 | 9 体系 | 韩立（续） |
| `aoyue_npc_fanpai.md` | 22 节点 / 4 结局 / 300+ 路线 | 敖越·寒焰宗崛起（NPC 反派视角） | 9 体系 | 敖越（NPC） |

## 🎮 怎么玩

```bash
# CLI 模式（打印节点 + 选项 + 状态）
python3 scripts/interactive.py --story stories/hanli_vol1_mochui.md

# Headless 模式（CI 用，自动跑完所有 ending）
python3 scripts/interactive.py --story stories/hanli_vol1_mochui.md --headless

# Web UI（v1.4.0+）
python3 scripts/web_app.py
# → 浏览器打开 http://localhost:8000/play
```

## 🔍 怎么分析

```bash
# 故事统计
python3 examples/consume-interactive.py analyze stories/hanli_vol2_yuanzou.md

# 遍历所有路径
python3 examples/consume-interactive.py walk stories/hanli_vol2_yuanzou.md

# 找最短决策链
python3 examples/consume-interactive.py path stories/hanli_vol2_yuanzou.md --from 离府启程 --to 落云宗交差

# 导出 JSON
python3 examples/consume-interactive.py export stories/hanli_vol2_yuanzou.md -o /tmp/vol2.json
```

## 📖 剧本格式

见 [`../interactive/README.md`](../interactive/README.md) 的 **DSL 语法**章节。

剧本必备结构：

```markdown
# 标题

## 元数据
id: story_id
description: 一句话简介
start: 起点节点 id

## 节点 节点 id (scene|ending)

text: |
  节点正文...

data:
  ?字段: 默认值
  字段: 新值
refs: 体系目录/文档名.md
next:
  - label: "选项文字"
    goto: 目标节点 id
    set: { 字段: 值 }
    if: 状态条件
```

## ✍️ 写作约定

- **节点 id 用中文**：剧情化、易读
- **正文使用 `|`**：保留换行（YAML 块字符串）
- **选项 label 写明后果**：避免误导玩家
- **state 字段命名**：`?` 前缀表示"未设置时才初始化"；不带 `?` 表示强制覆盖
- **refs 必须存在**：所有 `refs:` 引用的 .md 必须真实存在（CI 校验）
- **连通性**：所有 `goto` 目标必须存在（CI 校验孤儿节点）

## 🌐 跨卷/跨剧本关联

- **hanli_vol1 → hanli_vol2**：vol2 起点承接 vol1 结局「借药筑基」
- **hanli_vol1 + aoyue_npc_fanpai**：aoyue 是墨大夫的表妹，与 vol1「墨大夫」势力直接相关
- **多视角对比**：同一世界观下，不同主角（韩立/敖越）走出完全不同的路径

## 🛠️ 怎么新增剧本

1. 在 `stories/` 新建 `xxx.md`，遵循上述格式
2. 本地跑 `python3 examples/consume-interactive.py analyze stories/xxx.md`
3. 确保 `✅ is_well_formed`
4. 跑 `python3 scripts/validate.py`（如果改了元数据）
5. 提 PR，CI 自动校验