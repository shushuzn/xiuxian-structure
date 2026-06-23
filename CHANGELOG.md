# 变更日志

本仓库所有重要变更会记录在此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### D.4 文档站 CI 增强
- 📝 **mkdocs.yml 增强**：
  - 新增 6 个体系到 nav (天材地宝/宗门/战斗/因果/时空)
  - 新增"互动故事" section (5 演示)
  - 站点元数据 (description/keywords/site_url)
- 🔧 **docs.yml CI 重构**：
  - 拆分为 `validate` (校验) + `deploy` (部署) 两个 job
  - validate 跑 `mkdocs build` 校验构建产物
  - deploy 依赖 validate + 仅 main 分支部署
  - 产物统计 (HTML 页数/总大小)
- 📊 **构建产物**：243 HTML 页面 / 21MB (本地验证)
- ✅ 22 个预存 warning 已记录 (后续 D.5 计划逐步修复)

### v2.15 跨境界试炼副本
- 🆕 **TrialDungeon** 类：跨境界试炼系统
  - **9 境界 × 4 难度 = 36 关卡**
  - 难度：easy (70%) / normal (50%) / hard (30%) / hell (10%)
- 🆕 **TrialStage** 类：试炼关卡定义
  - `can_enter(state)` 进入条件检查 (境界 + 条件)
  - `rewards` / `penalties` 奖励惩罚
  - `boss` boss 描述
- 🆕 **TrialResult** 类：试炼结果
  - `success` / `rounds` / `narrative` / `score`
- 🎮 **`trial` 选项动作**：触发指定关卡
- 🆕 `dungeon.enter_stage(stage_id)` + `dungeon.apply_result(result)` API
- 📊 `dungeon.get_progress()` 进度跟踪
- 📖 **stories/v215_demo.md** — 5 节点演示
- 🧪 **+15 单测**：试炼关卡 / 通关 / 失败 / 难度缩放 / 引擎集成
- ✅ **223 → 238 tests** (+15)

### v2.9 互动引擎深化
- 🆕 **WorldBook** 类：关键词触发的补充设定
  - `WorldBookEntry` (id/keywords/title/content/priority)
  - `lookup(text, max_entries=3)` 按关键词匹配
  - 按 priority 自动排序
- 🆕 **AchievementTracker** 类：成就系统
  - `Achievement` (id/name/description/condition/points)
  - `check_all(state)` 批量检查解锁
  - `get_score()` / `get_progress()` 统计
- 🆕 **EndingAnalyzer** 类：多结局分析
  - 自动从 Story 提取所有 ending 节点
  - 按名字智能分类 (good/bad/secret/normal)
  - `predict_ending(score)` 预测最可能结局
  - `get_completeness()` 故事完整度
- 🆕 **AINarrator** 类：AI 叙事
  - `narrate_state(state, context)` 状态叙事
  - `narrate_change(state, attr, old, new)` 变化叙事
  - 9 境界模板 (炼气→大乘)
- 🎮 **3 个新选项动作**：`worldbook` / `achievement` / `narrate`
- 🆕 **Engine 扩展**：`attach_worldbook()` / `attach_achievements()` / `check_achievements()`
- 📖 **stories/v29_demo.md** — v2.9 演示故事
- 🧪 **+31 单测**：WorldBook (7) / Achievement (8) / EndingAnalyzer (4) / AINarrator (6) / Engine 集成 (6)
- ✅ **192 → 223 tests** (+31)
- ✅ **coverage 81.45% → 83.69%**

### D.3 CI 强化
- 📈 **覆盖率阈值**：70% → **80%**（`pyproject.toml` `[tool.coverage.report].fail_under`）
- 🆕 **mypy 类型检查**：新增 `[tool.mypy]` 配置 + `requirements-dev.txt` 加 `mypy>=0.991` + CI 新增 `Mypy type check` 步骤
- 🧪 **+29 个新单测**：`tests/test_interactive.py` 加 29 个边界测试（World/State/Engine 全面）
- ✅ **129 → 158 tests** (129 → 158, +29)

### v2.9 关系图谱
- 🔗 **+53 条 relations**：灵根↔妖兽/心魔↔契约/灵根↔雷劫/灵石↔灵脉/势力↔灵脉/神通↔境界/...
- 🧜 **`build_mermaid()`** 新函数：自动从 `data/relations.yaml` 生成 Mermaid flowchart
- 📖 **docs/图谱.md** 末尾新增自动生成的全图（161 节点 / 221 边 / 50 边）
- 🧪 **+13 单测**：`tests/test_build_graph.py`
- ✅ **126 → 129 tests** (+13)

### v2.8 互动引擎完善
- 🆕 **BreakthroughSimulator** — 境界突破模拟器
  - 灵根加成 / 丹药加成 / 心境加成 / 天劫判定 / 心魔遭遇
  - 支持中英文境界名（炼气期/lianqi）
- 🆕 **CombatSystem** — 回合制战斗系统
  - 玩家 vs 怪物（来自 monsters.yaml）
  - attack / defend / skill / flee 四种动作
  - 暴击系统 + 战利品奖励
- 🆕 **RandomEventEngine** — 随机事件生成器
  - 5 类事件：encounter / treasure / tribulation / npc / weather
  - 奖励/消耗/好感度变动
- 🎮 **3 个新选项动作**：`breakthrough` / `combat` / `random_event`
- 📖 **stories/v28_demo.md** — v2.8 演示故事
- 🧪 **25 个新单测**：覆盖三个模块 + Engine 集成
- ✅ **126 tests** passing (101 → 126, +25)

### v2.7 数据深化（v2-v4 合并）
- 数据深化 v2 (PR #58): 阵法/符箓/功法/神通 +20
- 数据深化 v3 (PR #59): 灵气/灵根/心魔/雷劫/灵石/妖修/势力/契约/神识 +20
- 数据深化 v4 (PR #60): 飞升/境界/仙界/器灵/神界 +20

### v2.6 战斗体系
- 📚 **10 篇新 .md**：战斗体系（武器/招式/阵法/策略/...）
- 🗂️ **data/combat.yaml**（93 条记录 / 8 字段）
- 🔗 **16 条 relations**

### v2.5 互动引擎扩四大界面
- **State.realm** 字段 + `realm:` 选项动作 — 引擎现在感知角色所在界面
- 📖 **`stories/demo_sijie.md`** — 四大界面跨界史诗 demo（14 节点 / 4 条路径）
- 🔧 Py3.6 兼容修复：移除 2 处 `re.Match` → `def repl(m)`
- ✅ 交互式 CLI 已验证

### D.2 工程化深化
- 📊 **覆盖率阈值**：`pyproject.toml` 新增 `[tool.coverage]`，`fail_under = 70`，CI 强制执行
- 🧪 **32 个新单测**：覆盖 engine 异常路径 / 序列化 / DSL 解析
- 🔧 **CI 矩阵**：Python 3.9 + 3.12 双版本

### v2.4 魔界 + 冥界体系
- 📚 **24 篇新 .md**：魔界体系 12 篇 + 冥界体系 12 篇
- 🗂️ **data/demon_realm.yaml + data/underworld_realm.yaml**
- 🔗 **data/relations.yaml +15 条**跨体系关系 + 六道轮回全条目
- **四大界面全部覆盖**（22 体系）

### v2.3 神界体系
- 📚 **12 篇新 .md**：神界 / 神格 / 神职 / 神气 / 神石 / 神劫 / 神域 / 神兽 / 神器 / 神族 / 下界飞神者 / 神界纪元
- 🗂️ **data/divine_realm.yaml**
- 🔗 **data/relations.yaml +12 条**神界相关关系

### 新增（之前）
- 🆕 **13 个体系目录 / 25 篇新体系 .md**（覆盖 vol2/aoyue 引用的所有体系）
  - **新增目录**：`妖修体系/`（2 篇）+ `秘境体系/`（3 篇）
  - **势力体系（+7）**：墨府 / 落云宗 / 寒焰宗 / 潮汐宫 / 天星城商会 / 黑岩海盗 / 妖修海域
  - **妖兽体系（+4）**：海妖 / 九幽寒蟒 / 化形妖修 / 妖丹
  - **法器体系（+4）**：养魂木 / 雷师印 / 易容符 / 灵兽袋
  - **阵法体系（+5）**：护山大阵 / 雾阵 / 寒泉阵 / 召唤阵 / 渡劫阵
  - **丹药体系（+4）**：疗伤丹 / 九幽还魂草 / 渡劫丹 / 千年灵药
  - **功法体系（+2）**：长春功 / 雷法
- 🐛 **bug fix**：3 处故事 refs 笔误修复
  - `灵兽体系/灵兽.md` → `妖兽体系/灵兽.md`（×2 in hanli_vol1）
  - `妖兽体系/妖修.md` → `妖修体系/妖修.md`（in hanli_vol2）
  - `妖兽体系/灵兽袋.md` → `法器体系/灵兽袋.md`（in aoyue_npc_fanpai）
- 🐛 **bug fix**：8 处跨目录链接路径修复（`阵法体系/` 和 `法器体系/` 中的链接未加 `../势力体系/` 前缀）

### 统计
- **体系数**：11 → **13**（+妖修体系、+秘境体系）
- **体系 .md 总数**：57 → **82**（+25 篇）
- **README 中 .md 总数**：61 → **122**
- **跨剧本 refs 完整性**：49/49 引用 100% 对应真实文件（之前 19/50）

### 新增（之前）
- 📖 **`stories/hanli_vol2_yuanzou.md`**（韩立第二卷 · 30 节点 / 5 结局 / 662 路径 / 9 体系）
  - 承接 vol1「借药筑基」结局，韩立已筑基远走
  - 主题：护送南陇侯残魂回落云宗 + 墨府追杀 + 妖修海域 + 雷师传承
- 📖 **`stories/aoyue_npc_fanpai.md`**（敖越 · 多主角 / NPC 反派视角 · 22 节点 / 4 结局 / 316 路径 / 9 体系）
  - 敖越是墨大夫的表妹，结丹后期，反出墨府自立寒焰宗
  - 与 vol1/vol2 共享同一世界观（墨大夫、潮汐宫、天星城商会）
  - 主题：三方博弈（元婴/化形/商会）+ 元婴渡劫 + 反派崛起
- 📚 **`stories/README.md`** 介绍现有剧本 + 写作约定 + 跨卷关联
- 🔧 **CI 新 step** `Verify vol2 + aoyue stories`（跨剧本路径覆盖 + 共享引用统计）
- 🧰 **Consumer API `examples/consume-interactive.py`**（~330 行 · 零依赖）
  - 4 个高层 API：`analyze_story` / `walk_all_paths` / `find_shortest_path` / `export_to_json`
  - CLI 4 子命令：`analyze` / `walk` / `path` / `export`
  - Python 模块调用友好（`sys.path.insert(0, "examples")`）
  - 死循环防护（单路径 > 50 步 → `loop_or_invalid`）
  - 孤儿节点检测（`is_well_formed` + exit_code 1）
- 📖 **`examples/README.md`** 重写为 Consumer API 教程（用法 + Python 调用 + 输出示例 + CI 集成）
- 🔧 **CI step** `Verify consume-interactive API`（4 个 CLI 全跑 + 临时 JSON 导出）

### 计划
- 暂无。等待社区反馈或新需求。

## [1.4.0] - 2025-06-21

### 新增
- 🌐 **Web API `scripts/web_app.py`**（~310 行 · FastAPI）
  - 8 个 REST 端点（health / list / get / session CRUD）
  - Pydantic 模型：NodeView / StoryView / SessionView / ChoiceRequest
  - 内存 sessions（`dict[sid, Engine]`，重启丢失）
  - 静态文件挂载（`/static` + `/play` SPA）
- 🎨 **Web UI `interactive/web/`**（3 文件 · 零依赖）
  - `index.html` — SPA 骨架（3 块布局）
  - `style.css` — 暗色修仙主题（衬线字体 + 暖金/冷蓝调色板）
  - `app.js` — vanilla JS（6 个 API 函数）
- 📦 **`requirements.txt`**：pyyaml + fastapi + uvicorn

### 设计亮点
- **API-only**：server 持 state，client 只持 sid
- **零依赖前端**：单 HTML + 单 CSS + 单 JS（gzip 后 ~5KB）
- **响应式**：< 900px 折叠为单列
- **严格 CI**：8 REST + 4 UI + 1 HTML 挂载点

### 变更
- `.github/workflows/validate.yml`：新增 `Verify Web API endpoints`（CI 加 12 个端点检查）
- `README.md`：新增「Web API」章节 + 架构图加 `web_app.py` + `interactive/web/`
- `scripts/interactive.py`：无改动（v1.2 引擎直接被 web_app 复用）

## [1.3.0] - 2025-06-21

### 新增
- 🤖 **LLM 协作 `scripts/generate_node.py`**（~340 行）
  - `build_world_summary` 从 `data/*.yaml` 自动生成 11 体系 + 关键 ID 摘要
  - `build_prompt` 严格 prompt 模板（7 条硬性规则）
  - `call_llm` OpenAI 兼容 API 调用
  - `NodeValidator` 5 项校验（id 冲突 / 解析 / goto 存在 / refs 文件 / 数值范围）
  - 失败自动反馈重试：3 轮内把错误传给 LLM 修复
  - 成功节点写 `examples/generated/<id>.md`
- 📖 **LLM 协作指南 `examples/feed-to-llm.md`**
  - 3 阶段工作流（提取需求 / LLM 生成 / 验证入库）
  - 快速开始（dry-run / 正式跑 / 改 LLM）
  - 7 条最佳实践
- 🆕 **mock LLM 输出 `examples/generated/夜探禁地.md`**
  - 2 个节点（夜探禁地 + 杀火鳞蜥 ending）
  - NodeValidator 校验通过示例

### 设计亮点
- **数据驱动（防幻觉）**：自动从 yaml 生成体系 + ID 摘要，LLM 写 refs 时知道文件存在
- **严格 prompt（结构化输出）**：7 条硬性规则保证输出格式一致
- **失败自动反馈**：3 轮内把 ERROR 传给 LLM 修复，重试用尽后 dump 到 stderr

### 变更
- `scripts/interactive.py`：新增 `Story.parse_nodes_only()` API（绕过 start_node 校验）
- `.github/workflows/validate.yml`：CI 新增 `Verify LLM-generated examples are parseable` 步骤
- `README.md`：新增「LLM 协作」章节 + 架构图更新
- `索引.md`：知识库 → 创作示例 新增「LLM 节点」条目

## [1.2.0] - 2025-06-21

### 新增
- 🎮 **互动小说引擎 `scripts/interactive.py`**（547 行）
  - `World` 从 `data/*.yaml` 构建内存世界（`lookup` / `find_by_id` / `render_template`）
  - `Story` 解析 `stories/*.md`（自创轻量 DSL：`## 节点 <id> [(type)]` + YAML 字段块）
  - `Engine` 状态机 + 条件求值 + data 初始化
  - `State` 玩家属性 + 标志位 + `check(expr)` 条件表达式求值
  - CLI：交互模式 / headless 模式（CI 用）
  - 程序化 API：`Engine.play()` / `Engine.step()` / `Engine.save()` / `Engine.load()`
- 📖 **2 个互动故事**
  - `stories/demo_measuring_spirit.md` — 4 节点 / 2 结局（入李家 / 自立于坊市）
  - `stories/hanli_vol1_mochui.md` — 10 节点 / 5 结局（远走 / 流落 / 杀墨 / 灵兽 / 借药筑基）
- 📚 **互动小说文档**：`interactive/README.md`（DSL 文档 + API 指南）

### 设计亮点
- **数据驱动**：剧情里写 `{realms.炼气期.lifespan}` 自动从 yaml 拉值 — 剧情永远跟数据一致
- **状态机分支**：`if: 灵石 >= 3` / `flag.拜师` / `set: { 境界: 筑基初期 }`
- **`?` 前缀机制**：`?灵石: 5` 仅在未设置时初始化（保护玩家存档不被覆盖）
- **条件求值**：支持 `>=` / `<=` / `==` / `!=` / `>` / `<` / `and` / `or` / `not`

### 变更
- `scripts/validate.py`：`stories/` 加白名单（剧本非知识库）
- `.github/workflows/validate.yml`：CI 增加 2 个新步骤
  - `Run interactive engine (smoke test)` — 跑 headless 模式
  - `Verify all stories are well-formed` — 连通性 + 完整性 + 至少 1 ending + 无孤儿节点
- `.gitignore`：`interactive/saves/`（存档不入仓）
- `README.md`：新增「互动小说」章节 + 架构图新增 `stories/` / `interactive/` / `scripts/interactive.py`
- `索引.md`：知识库 → 创作示例 新增「互动」条目

## [1.1.0] - 2025-06-21

### 新增
- 📖 **示例作品集 `examples/`**
  - `第一章_散修韩立.md` — ~2000 字小说片段，串联 8 体系（灵根/境界/灵气/符箓/丹药/灵石/势力/妖兽）
  - `README.md` — 写作指南（导出→喂 LLM→写片段）+ 串联体系密度建议
- 🎨 **韩立式主角设计**：伪灵根散修，符合知识库的"伪灵根"设定（4 属性混杂、速度 × 1.0、突破 × 0.3）
- 🔥 **火鳞蜥**：示例妖兽（炼气后期，鳞甲刀剑难伤）

### 变更
- `validate.py`：`examples/` 目录跳过 `## 关联` 校验
- `README.md`：新增「示例作品」章节
- `索引.md`：新增「知识库 → 创作示例」关联

## [1.0.0] - 2025-06-21

### 新增
- 📦 **导出工具 `scripts/export.py`**
  - JSON：整本知识库（44K，含 12 体系元信息 + 数据）
  - CSV：每段数据一张表（共 42 个 CSV）
  - Markdown：单文件手册 `HANDBOOK.md`（1053 行）
  - 支持 `--format {all,json,csv,md}` 和 `--output DIR` 参数
- 🔧 **CI smoke test**（`.github/workflows/validate.yml`）
  - PR/CI 自动跑 export.py 验证工具可执行
  - 显示产物统计
- 🚫 **`.gitignore`**：排除 dist/、__pycache__、IDE 文件

### 变更
- `validate.py`：`dist/` 目录跳过 `## 关联` 强制检查
- `README.md`：新增「导出与消费」章节，列 3 种产物用法
- 架构图：scripts/ 下新增 `export.py`

## [0.9.0] - 2025-06-21

### 新增
- 🏛️ **势力体系实例**（3 篇 .md）
  - 散修联盟（炼气期松散组织）
  - 修仙家族（血缘纽带 + 小型灵脉）
  - 天霞山（中型宗门示例，结丹期坐镇，含完整组织/资源/晋升）
- 💰 **灵石体系实例**（3 篇 .md）
  - 下品灵石（炼气期日常，1 单位灵气）
  - 中品灵石（筑基期常用，10 单位灵气）
  - 极品灵石（元婴期以上，1000 单位灵气）
- ⚔️ **阵法体系实例**（3 篇 .md）
  - 攻击型阵法（九霄雷阵等）
  - 防御型阵法（金光护山阵等，含护山大阵分级）
  - 聚灵型阵法（聚灵阵，加速修炼）
- 📜 **符箓体系实例**（4 篇 .md）
  - 火球符（凡符，最基础攻击）
  - 金刚符（灵符，筑基期防御标配）
  - 遁符（瞬间移动逃命）
  - 传讯符（远距离传信）
- 4 体系由 1/1 全部扩展到 4+/4+

### 变更
- 4 体系主 .md 各加「实例」导航章节
- 索引.md：新增 3 条关联（散修→功法、阵法→势力经济、符箓→修士等级差弥补）
- README.md：架构图 4 体系展开为 13 个子条目

## [0.8.0] - 2025-06-21

### 新增
- 🌫️ **灵气浓度实例**（4 篇 .md）
  - 稀薄灵气（人界主流）/ 普通灵气（小型宗门）/ 浓郁灵气（中型灵脉）/ 化液灵气（仙界）
  - 每篇含：浓度特征、分布区域、修炼表现、适用场景、典型地点
- 🏔️ **灵脉等级实例**（5 篇 .md）
  - 微型 / 小型 / 中型 / 大型 / 超级
  - 每篇含：灵脉参数、覆盖范围、灵气浓度、灵石产出、经营成本、战略价值
- 天地灵气体系由 1/1 扩展到 10/10

### 变更
- 灵气.md：新增「浓度实例」导航章节 + 修复重复标题
- 索引.md：新增 2 条关联（灵气浓度→境界、灵脉→势力规模）
- README.md：架构图天地灵气展开为 9 个子条目

## [0.7.0] - 2025-06-21

### 新增
- 🌿 **灵根属性实例**（8 篇 .md）
  - 五行基础天灵根：金属性、木属性、水属性、火属性、土属性
  - 变异灵根：雷灵根（自金）、冰灵根（自水）、风灵根（自木）
  - 每篇含：定位、特征、修炼速度、适配功法/法器、副业加成、代表修士类型
- 灵根体系由 1/1 扩展到 9/9

### 变更
- 灵根.md：新增「属性实例」章节（5 天灵根 + 3 变异）
- 索引.md：新增 2 条关联（灵根→副业、灵根→法器契合）
- README.md：架构图灵根体系展开为 8 个子条目

## [0.6.0] - 2025-06-21

### 新增
- 🔮 **阵法体系**（阵法.md + data/formations.yaml）
  - 6 类阵法（攻击/防御/困敌/聚灵/幻术/辅助）
  - 4 级阵法（凡阵→仙阵）
  - 3 种布阵方式（临时/永久/随身）
  - 示例：净海神灯阵（护山大阵）、九霄雷阵、迷天幻阵
- 📜 **符箓体系**（符箓.md + data/talismans.yaml）
  - 4 个品级（凡符→仙符）
  - 6 类符箓（攻击/防御/辅助/遁/封印/传讯）
  - 3 种制作方式（手工/批量/一次成型）
  - 示例：火球符、金刚符、闪电符

### 变更
- 索引.md：新增 2 条关联（阵法→势力防御、符箓→修为补足）
- docs/图谱.md：体系全景图扩展到 11 个体系
- docs/SCHEMA.md：新增 2 个体系 schema 章节
- README.md：架构图新增 2 个目录 + data 章节新增 2 个 yaml

## [0.5.0] - 2025-06-21

### 新增
- 🐉 **妖兽体系**（妖兽.md + 灵兽.md + data/monsters.yaml）
  - 妖兽品级（凡兽→妖帝，对应修士境界）
  - 灵兽契约（灵魂/平等/主从）
  - 4 类灵兽品级
  - 示例：云渡剑鹤、九霄火鸾
- 🏛️ **势力体系**（势力.md + data/factions.yaml）
  - 5 级规模（散修→顶级宗门）
  - 5 种形态（宗门/家族/散修联盟/王朝/妖修）
  - 4 级弟子等级（外门→真传）
  - 示例：青虚宫、天霞山、万妖林
- 💎 **灵石体系**（灵石.md + data/spirit_stones.yaml）
  - 5 个品级（下品→仙品，含兑换比例）
  - 3 类属性
  - 4 种用途、3 类来源

### 变更
- 索引.md：新增 5 条跨体系关联（灵脉→灵石、灵石→势力、妖兽→势力、妖兽→资源）
- docs/图谱.md：体系全景图扩展到 9 个体系
- docs/SCHEMA.md：新增 3 个体系 schema 章节
- README.md：架构图新增 3 个体系目录

## [0.4.0] - 2025-06-21

### 新增
- 📖 功法体系示例（2 部）：
  - 长生诀.md — 天级无属性功法
  - 金剑诀.md — 地级金属性功法
- 📖 法器体系示例（2 件）：
  - 青锋剑.md — 中阶金属性飞剑
  - 雷鼎珠.md — 高阶雷属性法宝
- 📖 丹药体系实例（6 种，覆盖全部 4 个用途）：
  - 突破类：筑基丹、结丹丹、培婴丹
  - 增益类：黄龙丹
  - 恢复类：小还丹
  - 辟谷类：辟谷丹

### 变更
- 功法.md / 法器.md / 丹药.md 加入子条目链接
- README.md 架构图扩展

## [0.3.0] - 2025-06-21

### 新增
- 📖 补齐境界体系文档：
  - 结丹期.md（500 年，金丹质变）
  - 元婴期.md（1000 年，元婴具象）
  - 化神期.md（2000 年，神魂化形）
  - 炼虚期.md（5000 年，法则融合）
  - 合体期.md（10000 年，神肉合一）
  - 渡劫期.md（近乎无限，承受天劫）
  - 大乘期.md（近乎无限，凡界终点）

### 变更
- data/realms.yaml：补全化神/炼虚/合体/渡劫/大乘的 `breakthrough` 和 `restrictions` 字段
- data/realms.yaml：高阶境界的 sub_stages 从 `early/mid/late/peak` 统一为拼音 `chuqi/zhongqi/houqi/fengfeng`
- 境界.md：子条目列表扩展到 9 个境界
- README.md：架构图加入新境界文档

## [0.2.0] - 2025-06-21

### 新增
- 🏗️ 工程化基础：
  - `docs/TEMPLATE.md` — 统一 .md 模板
  - `docs/SCHEMA.md` — YAML 数据 schema
  - `docs/图谱.md` — 6 个 mermaid 关系图
  - `scripts/validate.py` — 5 项校验脚本
  - `.github/workflows/validate.yml` — GitHub Actions CI
- 📊 结构化数据（`data/*.yaml`）：
  - realms.yaml — 9 个境界
  - elixirs.yaml — 6 种丹药 + 4 个品级
  - spirit_roots.yaml — 5 类灵根 + 8 种属性
  - aether.yaml — 4 浓度 + 5 灵脉 + 3 界面
  - techniques.yaml — 4 品级 + 3 修炼方式 + 示例功法
  - artifacts.yaml — 5 品级 + 3 认主方式 + 示例法器
  - relations.yaml — 17 条跨体系关联
- 🔗 为所有体系 .md 添加 `## 关联` 章节
- 📝 完整 README + CONTRIBUTING

### 变更
- 压缩 17 个 `feat: 你好` 占位 commit 为 1 个 `chore: 初始提交`

## [0.1.0] - 2025-06-21（初始）

### 新增
- 六大体系框架
  - 境界体系（境界、炼气期、筑基期）
  - 灵根体系、天地灵气、功法体系、丹药体系、法器体系
- 索引.md
- README.md
- LICENSE

[Unreleased]: https://github.com/shushuzn/xiuxian-structure/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/shushuzn/xiuxian-structure/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/shushuzn/xiuxian-structure/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/shushuzn/xiuxian-structure/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/shushuzn/xiuxian-structure/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/shushuzn/xiuxian-structure/releases/tag/v0.1.0