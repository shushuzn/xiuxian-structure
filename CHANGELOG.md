# 变更日志

本仓库所有重要变更会记录在此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 计划中
- 灵气浓度 / 灵脉具体实例
- 工具化（scripts/export.py）

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

[Unreleased]: https://github.com/shushuzn/xiuxian-structure/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/shushuzn/xiuxian-structure/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/shushuzn/xiuxian-structure/releases/tag/v0.1.0