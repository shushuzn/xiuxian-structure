# xiuxian-structure

基于《凡人修仙传》参考的修仙世界观架构。从底层开始，逐层搭建。

[![Version](https://img.shields.io/github/v/release/shushuzn/xiuxian-structure?include_prereleases)](https://github.com/shushuzn/xiuxian-structure/releases)
[![CI](https://github.com/shushuzn/xiuxian-structure/actions/workflows/validate.yml/badge.svg)](https://github.com/shushuzn/xiuxian-structure/actions/workflows/validate.yml)
[![codecov](https://codecov.io/gh/shushuzn/xiuxian-structure/branch/main/graph/badge.svg)](https://codecov.io/gh/shushuzn/xiuxian-structure)
[![License](https://img.shields.io/github/license/shushuzn/xiuxian-structure)](LICENSE)
[![PRs](https://img.shields.io/github/issues-pr-closed/shushuzn/xiuxian-structure)](https://github.com/shushuzn/xiuxian-structure/pulls?q=is%3Apr+is%3Aclosed)

**v2.13.0** · **26 体系** · 28 yaml · [📖 阅读更新日志](docs/CHANGELOG.md)

> 🆕 v2.13 新增体系 — **因果体系**（8 篇 .md + karma.yaml）— 功德/业力/因果律/因果业报/天道轮回/因果神通/因果业障/因果修炼
>
> 🆕 v2.12 新增体系 — **宗门体系**（11 篇 .md + zong_men.yaml）— 等级/架构/弟子/长老/掌门/任务/经济/外交/联盟/散修
>
> 🆕 v2.11 新增体系 — **天材地宝体系**（9 篇 .md + tian_cai.yaml）— 灵草/灵木/灵金属/灵水灵火/灵兽灵虫/天外奇珍/仙材神材
>
> 🆕 v2.10 新增体系 — **秘境体系**（10 篇 .md + secret_realm.yaml）— 浮岛/空间/传承/灵药/矿脉/凶险/仙府
>
> 🆕 v2.9 关系图谱 — 跨体系 relations +53 条 / 240 总关系 / Mermaid 自动渲染
>
> 🆕 v2.8 互动引擎完善 — **境界突破模拟** / **回合制战斗** / **随机事件** 三大模块
>
> 🆕 v2.7 数据深化 — 4 轮扩展（阵法/符箓/功法/神通/灵气/灵根/心魔/雷劫/灵石/妖修/势力/契约/神识/飞升/境界/仙界/器灵/神界 9 大体系 +280 条）
>
> 🆕 v2.6 战斗体系 — 跨 6 界面的通用战斗规则（10 篇 .md + combat.yaml 93 条）
>
> v2.4 魔界 + 冥界体系（24 篇）— 仙界背面 / 仙陨之后
>
> v2.3 神界体系（12 篇）— 仙帝之上
>
> v2.0 飞升体系（10 篇）— 大乘之上 → 仙界
>
> v1.5/v1.6/v1.7：心魔 + 雷劫 + 神识 + 器灵 + 契约（27 篇）

English readers: see [README_EN.md](README_EN.md).

📖 **文档站**：<https://shushuzn.github.io/xiuxian-structure/>（mkdocs 自动部署）

## 架构

```
xiuxian-structure/
├── README.md                   # 本文件
├── CONTRIBUTING.md             # 贡献指南
├── LICENSE
├── 索引.md                     # 各体系关联关系（人类可读）
│
├── 境界体系/                   # 修炼阶段
│   ├── 境界.md                 # 框架定义
│   ├── 炼气期.md
│   ├── 筑基期.md
│   ├── 结丹期.md
│   ├── 元婴期.md
│   ├── 化神期.md
│   ├── 炼虚期.md
│   ├── 合体期.md
│   ├── 渡劫期.md
│   └── 大乘期.md
├── 灵根体系/                   # 先天资质
│   ├── 灵根.md
│   ├── 金属性天灵根.md
│   ├── 木属性天灵根.md
│   ├── 水属性天灵根.md
│   ├── 火属性天灵根.md
│   ├── 土属性天灵根.md
│   ├── 雷灵根.md               # 变异
│   ├── 冰灵根.md               # 变异
│   └── 风灵根.md               # 变异
├── 天地灵气/                   # 世界资源
│   ├── 灵气.md
│   ├── 稀薄灵气.md
│   ├── 普通灵气.md
│   ├── 浓郁灵气.md
│   ├── 化液灵气.md
│   ├── 微型灵脉.md
│   ├── 小型灵脉.md
│   ├── 中型灵脉.md
│   ├── 大型灵脉.md
│   └── 超级灵脉.md
├── 妖兽体系/                   # 妖族
│   ├── 妖兽.md
│   ├── 灵兽.md
│   ├── 海妖.md                  # 🆕 乱星海域水族
│   ├── 九幽寒蟒.md              # 🆕 aoyue 本命灵兽
│   ├── 化形妖修.md              # 🆕 化形后身份
│   └── 妖丹.md                  # 🆕 妖兽核心资源
├── 妖修体系/                   # 🆕 妖修身份与境界
│   ├── 妖修.md
│   └── 化形期.md
├── 势力体系/                   # 宗门、家族、散修、王朝、妖修
│   ├── 势力.md
│   ├── 散修联盟.md
│   ├── 修仙家族.md
│   ├── 天霞山.md
│   ├── 墨府.md                  # 🆕 vol1/vol2 墨大夫
│   ├── 落云宗.md                # 🆕 元婴期大型宗门
│   ├── 寒焰宗.md                # 🆕 aoyue 自创
│   ├── 潮汐宫.md                # 🆕 化形妖修宗门
│   ├── 天星城商会.md            # 🆕 中立商会
│   ├── 黑岩海盗.md              # 🆕 乱星海域海盗
│   └── 妖修海域.md              # 🆕 妖修聚集地
├── 灵石体系/                   # 通用货币
│   ├── 灵石.md
│   ├── 下品灵石.md
│   ├── 中品灵石.md
│   └── 极品灵石.md
├── 阵法体系/                   # 阵法（攻防、聚灵）
│   ├── 阵法.md
│   ├── 攻击型阵法.md
│   ├── 防御型阵法.md
│   ├── 聚灵型阵法.md
│   ├── 护山大阵.md              # 🆕 宗门必备
│   ├── 雾阵.md                  # 🆕 乱星海域海雾
│   ├── 寒泉阵.md                # 🆕 灵药岛寒泉
│   ├── 召唤阵.md                # 🆕 灵兽召唤
│   └── 渡劫阵.md                # 🆕 突破辅助
├── 符箓体系/                   # 符箓（一次性法术载体）
│   ├── 符箓.md
│   ├── 火球符.md
│   ├── 金刚符.md
│   ├── 遁符.md
│   └── 传讯符.md
├── 功法体系/                   # 修炼方法
│   ├── 功法.md
│   ├── 长生诀.md               # 天级无属性示例
│   ├── 金剑诀.md               # 地级金属性示例
│   ├── 长春功.md               # 🆕 雷师一脉传承
│   └── 雷法.md                 # 🆕 雷师亲创
├── 丹药体系/                   # 辅助外物
│   ├── 丹药.md
│   ├── 筑基丹.md               # 突破类
│   ├── 结丹丹.md               # 突破类
│   ├── 培婴丹.md               # 突破类
│   ├── 黄龙丹.md               # 增益类
│   ├── 小还丹.md               # 恢复类
│   ├── 辟谷丹.md               # 辟谷类
│   ├── 疗伤丹.md               # 🆕 基础疗伤
│   ├── 九幽还魂草.md           # 🆕 千年灵药
│   ├── 渡劫丹.md               # 🆕 突破元婴辅助
│   └── 千年灵药.md             # 🆕 灵药品级
├── 法器体系/                   # 战斗器物
│   ├── 法器.md
│   ├── 青锋剑.md               # 中阶金属性剑
│   ├── 雷鼎珠.md               # 高阶雷属性法宝
│   ├── 养魂木.md               # 🆕 温养残魂
│   ├── 雷师印.md               # 🆕 雷师传承法器
│   ├── 易容符.md               # 🆕 幻形符（跨体系）
│   └── 灵兽袋.md               # 🆕 灵兽收纳
├── 秘境体系/                   # 🆕 独立小世界
│   ├── 秘境.md
│   ├── 灵药岛.md
│   └── 雷师之墓.md
├── 心魔体系/                   # 🆕 v1.5 突破心障
│   ├── 心魔.md
│   ├── 贪魔.md
│   ├── 嗔魔.md
│   ├── 痴魔.md
│   └── 执念魔.md
├── 雷劫体系/                   # 🆕 v1.5 天劫考验
│   ├── 雷劫.md
│   ├── 三九天劫.md
│   ├── 六九天劫.md
│   ├── 九九天劫.md
│   ├── 雷劫淬体.md
│   └── 散功.md
├── 神识体系/                   # 🆕 v1.6 精神力外延
│   ├── 神识.md
│   ├── 炼气神识.md
│   ├── 筑基神识.md
│   ├── 结丹神识.md
│   ├── 元婴神识.md
│   └── 神识攻击.md
├── 器灵体系/                   # 🆕 v1.7 法器灵魂
│   ├── 器灵.md
│   ├── 器灵认主.md
│   ├── 器灵反噬.md
│   ├── 器灵沟通.md
│   └── 器灵成长.md
├── 契约体系/                   # 🆕 v1.7 灵魂绑定关系
│   ├── 契约.md
│   ├── 灵魂契约.md
│   ├── 平等契约.md
│   ├── 主从契约.md
│   └── 魂契.md
├── 飞升体系/                   # 🆕 v2.0 大版本
│   ├── 飞升.md
│   ├── 飞升之劫.md
│   ├── 界面壁障.md
│   ├── 仙界.md
│   ├── 仙灵石.md
│   ├── 仙职.md
│   ├── 仙劫.md
│   ├── 仙界势力.md
│   ├── 仙界功法.md
│   └── 下界飞升者.md
├── 神界体系/                   # 🆕 v2.3 大版本（仙帝之上 → 神界）
├── 魔界体系/                   # 🆕 v2.4 大版本（仙界反面 → 魔界）
├── 冥界体系/                   # 🆕 v2.4 大版本（死后世界 → 冥界）
├── 战斗体系/                   # 🆕 v2.6 大版本（神通/法相/领域/遁术/遁法/阵法战）
│
├── data/                       # 结构化数据（程序可读）
│   ├── realms.yaml             # 境界
│   ├── elixirs.yaml            # 丹药
│   ├── spirit_roots.yaml       # 灵根
│   ├── aether.yaml             # 灵气
│   ├── techniques.yaml         # 功法
│   ├── artifacts.yaml          # 法器
│   ├── monsters.yaml           # 妖兽/灵兽
│   ├── factions.yaml           # 势力
│   ├── spirit_stones.yaml      # 灵石
│   ├── formations.yaml         # 阵法
│   ├── talismans.yaml          # 符箓
│   └── relations.yaml          # 跨体系关联
│
├── docs/                       # 元文档
│   ├── TEMPLATE.md             # .md 模板规范
│   ├── SCHEMA.md               # YAML schema 规范
│   ├── ARCHITECTURE.md         # 架构决策记录（ADR）
│   ├── BRANCH_PROTECTION.md    # 分支保护配置建议
│   └── 图谱.md                  # mermaid 关系图
│
├── examples/                   # 示例作品（小说/使用 demo）
│   ├── README.md
│   ├── 第一章_散修韩立.md      # ~2000 字小说片段，串联 8 体系
│   ├── feed-to-llm.md          # 🆕 LLM 协作工作流指南
│   └── generated/              # 🆕 LLM 生成的节点（mock 示例）
├── stories/                    # 互动小说剧本（v1.2.0+）
│   ├── README.md
│   ├── demo_measuring_spirit.md # 5 节点 demo
│   ├── hanli_vol1_mochui.md     # 18 节点 / 韩立第一卷
│   ├── hanli_vol2_yuanzou.md    # 🆕 30 节点 / 韩立第二卷
│   └── aoyue_npc_fanpai.md      # 🆕 22 节点 / 敖越 NPC 视角
├── interactive/                # 互动小说引擎文档（v1.2.0+）
│   ├── README.md
│   └── web/                    # 🆕 Web UI（v1.4.0+）
│       ├── index.html          # SPA 入口
│       ├── style.css           # 暗色主题
│       └── app.js              # vanilla JS（零依赖）
├── scripts/
│   ├── validate.py             # 校验脚本
│   ├── export.py               # 导出工具（JSON / CSV / Markdown 手册）
│   ├── interactive.py          # 互动小说引擎（v1.2.0+）
│   ├── generate_node.py        # LLM 协作生成节点（v1.3.0+）
│   └── web_app.py              # 🆕 FastAPI Web API（v1.4.0+）
│
├── .github/
│   ├── workflows/validate.yml  # GitHub Actions CI
│   ├── pull_request_template.md
│   ├── ISSUE_TEMPLATE/         # Issue 模板（4 种）
│   ├── CODEOWNERS
│   └── CODE_OF_CONDUCT.md      # 贡献者公约
│
├── CHANGELOG.md                # 变更日志
├── CONTRIBUTING.md             # 贡献指南
└── SECURITY.md                 # 安全策略
```

## 快速上手

```bash
# 校验知识库完整性
python3 scripts/validate.py

# 应该输出：✅ 全部通过
```

## 互动小说（v1.2.0+）

把 23 体系 yaml 当作运行时世界数据库，状态机驱动修仙互动叙事：

```bash
# 试玩 demo 故事
python3 scripts/interactive.py --story stories/demo_measuring_spirit.md

# 引擎 headless 模式（自动选第一有效选项，CI 用）
python3 scripts/interactive.py --story stories/demo_measuring_spirit.md --headless
```

- **数据驱动**：`data/*.yaml` 是唯一真相，剧情节点用 `{realms.炼气期.lifespan}` 占位符从 yaml 拉取
- **条件分支**：`if: 灵石 >= 3` / `flag.拜师` — 状态机过滤可用选项
- **DSL 简洁**：自创轻量剧本格式（`stories/*.md`），见 [interactive/README.md](interactive/README.md)
- **可程序化**：`World` / `Story` / `Engine` / `State` 全 Python API，可嵌入 Web / CI / LLM 工作流

## LLM 协作（v1.3.0+）

让大语言模型半自动扩展互动故事节点：

```bash
# Dry-run：只看 prompt（不需要 key）
python3 scripts/generate_node.py \
  --story stories/hanli_vol1_mochui.md \
  --requirement "在发现天霞山牌位后，加一个'夜探禁地'节点" \
  --dry-run

# 正式跑（设 OPENAI_API_KEY 或 LLM_API_KEY）
python3 scripts/generate_node.py \
  --story stories/hanli_vol1_mochui.md \
  --requirement "..."
```

- **自动喂 yaml**：脚本读 `data/*.yaml` 生成世界摘要（23 体系 + 关键 ID）
- **NodeValidator 5 项校验**：id 冲突 / 解析 / goto 存在 / refs 文件 / 数值范围
- **失败自动反馈重试**：3 轮内把错误传给 LLM 修复
- **示例**：`examples/feed-to-llm.md`（工作流）+ `examples/generated/夜探禁地.md`（mock 输出）
- **CI 自动校验**：`examples/generated/*.md` 必须过 NodeValidator

## Web API（v1.4.0+）

FastAPI 把互动小说引擎包装成 REST API：

```bash
# 安装 + 启动
pip install -r requirements.txt
python3 scripts/web_app.py
# → http://localhost:8000
# → API 文档：/docs
# → 前端入口：/play
```

8 个端点：
- `GET /health` — 健康检查
- `GET /` — 列出所有 stories
- `GET /story/{id}` — 故事元数据
- `POST /story/{id}/session` — 创建会话（可选 `initial_state`）
- `GET /session/{sid}` — 读当前状态
- `POST /session/{sid}/choice` — 选选项（传 `choice_index`）
- `POST /session/{sid}/restart` — 重启

```bash
# 快速体验（curl）
curl -X POST http://localhost:8000/story/demo_measuring_spirit/session \
  -H "Content-Type: application/json" -d '{"initial_state": {"灵石": 1}}'
# → 返回 sid + 起点节点（"求长老推荐" 选项被条件过滤掉）
```

## 程序化消费（v1.4.0+）

`examples/consume-interactive.py` 提供 4 个高层 API，让前端 / LLM 工具 / CI 校验
不用创建 Engine 也能分析故事结构：

```bash
# 1. 统计 — 节点数/分支/可达性/结局
python3 examples/consume-interactive.py analyze stories/hanli_vol1_mochui.md

# 2. 遍历所有路径（11 条完整剧情线）
python3 examples/consume-interactive.py walk stories/hanli_vol1_mochui.md

# 3. BFS 找最短决策链
python3 examples/consume-interactive.py path stories/hanli_vol1_mochui.md \
  --from 托付 --to 杀墨

# 4. 导出 JSON（供前端 / LLM 用）
python3 examples/consume-interactive.py export stories/hanli_vol1_mochui.md \
  -o /tmp/hanli.json
```

或作为 Python 模块调用：

```python
from consume_interactive import analyze_story, walk_all_paths, find_shortest_path
stats = analyze_story("stories/hanli_vol1_mochui.md")
# {"node_count": 18, "ending_count": 5, "is_well_formed": True, ...}
```

详见 [`examples/README.md`](examples/README.md)。

## 导出与消费

把 23 个 yaml 转换为可分发的产物：

```bash
# 导出全部格式到 dist/
python3 scripts/export.py

# 只导出 JSON / CSV / MD 中的一种
python3 scripts/export.py --format json
python3 scripts/export.py --format csv
python3 scripts/export.py --format md

# 指定输出目录
python3 scripts/export.py --output /tmp/xiuxian
```

导出产物（每次运行生成于 `dist/`）：

| 文件 | 用途 |
|---|---|
| `dist/xiuxian.json` | 整本知识库（喂给 LLM / 导入工具）|
| `dist/*__*.csv` | 每段数据一张表（Excel / Pandas 分析）|
| `dist/HANDBOOK.md` | 单文件 Markdown 手册（阅读 / 分享）|

`dist/` 在 `.gitignore` 中（工具产物，不入仓）。需要时本地运行 `export.py` 即得。

## 贡献

参见 [CONTRIBUTING.md](CONTRIBUTING.md)。核心规则：

1. 所有 .md 必须包含 `## 关联` 章节
2. 所有体系必须在 `data/*.yaml` 有对应数据
3. 跨体系关系维护在 `data/relations.yaml`
4. 提交前必须跑 `scripts/validate.py`

## 体系关联（速览）

```
灵根 ──决定──→ 功法 ──决定──→ 境界
 │                            ↑
 └──影响──→ 修炼速度     丹药 ──┘（突破）
                              ↑
灵气 ──决定──→ 灵脉 ──决定──→ 势力
 └─────────────┴──影响──→ 灵药（丹药原料）
```

完整图谱见 [docs/图谱.md](docs/图谱.md)。

## 许可

见 [LICENSE](LICENSE)。

## 决策与治理

- 📐 [ARCHITECTURE.md](docs/ARCHITECTURE.md) — 7 个架构决策的来龙去脉
- 🔒 [SECURITY.md](SECURITY.md) — 安全漏洞报告流程
- 🤝 [.github/CODE_OF_CONDUCT.md](.github/CODE_OF_CONDUCT.md) — 社区公约
- 🛡️ [BRANCH_PROTECTION.md](docs/BRANCH_PROTECTION.md) — 分支保护建议

## 示例作品

知识库的实际应用展示：

- 📖 [examples/第一章_散修韩立.md](examples/第一章_散修韩立.md) — 散修韩立的修仙故事，串联 8 体系（灵根/境界/灵气/符箓/丹药/灵石/势力/妖兽）
- 📝 [examples/README.md](examples/README.md) — 写作指南 + 串联体系密度建议