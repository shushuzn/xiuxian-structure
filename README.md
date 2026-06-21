# xiuxian-structure

基于《凡人修仙传》参考的修仙世界观架构。从底层开始，逐层搭建。

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
├── 天地灵气/灵气.md            # 世界资源
├── 妖兽体系/                   # 妖族
│   ├── 妖兽.md
│   └── 灵兽.md
├── 势力体系/势力.md            # 宗门、家族、散修、王朝、妖修
├── 灵石体系/灵石.md            # 通用货币
├── 阵法体系/阵法.md            # 阵法（攻防、聚灵）
├── 符箓体系/符箓.md            # 符箓（一次性法术载体）
├── 功法体系/                   # 修炼方法
│   ├── 功法.md
│   ├── 长生诀.md               # 天级无属性示例
│   └── 金剑诀.md               # 地级金属性示例
├── 丹药体系/                   # 辅助外物
│   ├── 丹药.md
│   ├── 筑基丹.md               # 突破类
│   ├── 结丹丹.md               # 突破类
│   ├── 培婴丹.md               # 突破类
│   ├── 黄龙丹.md               # 增益类
│   ├── 小还丹.md               # 恢复类
│   └── 辟谷丹.md               # 辟谷类
├── 法器体系/                   # 战斗器物
│   ├── 法器.md
│   ├── 青锋剑.md               # 中阶金属性剑
│   └── 雷鼎珠.md               # 高阶雷属性法宝
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
├── scripts/
│   └── validate.py             # 校验脚本
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