# xiuxian-structure

[![Version](https://img.shields.io/github/v/release/shushuzn/xiuxian-structure?include_prereleases)](https://github.com/shushuzn/xiuxian-structure/releases)
[![CI](https://github.com/shushuzn/xiuxian-structure/actions/workflows/validate.yml/badge.svg)](https://github.com/shushuzn/xiuxian-structure/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/shushuzn/xiuxian-structure)](LICENSE)
[![PRs](https://img.shields.io/github/issues-pr-closed/shushuzn/xiuxian-structure)](https://github.com/shushuzn/xiuxian-structure/pulls?q=is%3Apr+is%3Aclosed)

A worldbuilding knowledge base for the **cultivation (xiuxian) genre**, inspired by *A Record of a Mortal's Journey to Immortality* (凡人修仙传).

Built bottom-up, layer by layer: realm tiers → spirit roots → world resources → artifacts → factions → interactive fiction engine → web UI.

## At a Glance

- **18 systems** · **111+ knowledge .md** · **14 YAML data files** · **25+ merged PRs**
- Layered architecture: knowledge base → state-machine interactive fiction → REST API + Web UI
- Data-driven: YAML is the single source of truth; .md references and validations are automated
- Bilingual-ready (Chinese primary, English partial)

## Quick Start

```bash
# Validate the knowledge base
pip install -r requirements.txt
python scripts/validate.py
# → ✅ 全部通过 (0 个警告)

# Run the interactive fiction engine
python scripts/interactive.py --story stories/demo_measuring_spirit.md --headless

# Launch the web API + UI
pip install -r requirements.txt
python scripts/web_app.py
# → http://localhost:8000  (API docs at /docs, UI at /play)
```

## Architecture

```
xiuxian-structure/
├── README.md                       # This file
├── CONTRIBUTING.md                 # Contribution guide
├── LICENSE
├── 索引.md                          # Cross-system index (human-readable)
│
├── 境界体系/ (Realm System)         # 9 cultivation tiers
├── 灵根体系/ (Spirit Root System)   # 5 elements + 3 variants
├── 天地灵气/ (World Aether System)  # 5 concentrations + 5 vein tiers
├── 妖兽体系/ (Monster System)       # Spirit beasts, sea monsters, demon cultivators
├── 妖修体系/ (Demon Cultivator)     # Transformation, demon cores
├── 势力体系/ (Faction System)       # Sects, families, alliances, pirate crews
├── 灵石体系/ (Spirit Stone System)  # Currency tiers
├── 阵法体系/ (Formation System)     # Attack/defense/spirit-gathering arrays
├── 符箓体系/ (Talisman System)      # Disposable spell carriers
├── 功法体系/ (Cultivation Method)   # Technique tiers
├── 丹药体系/ (Elixir System)        # Breakthrough / buff / recovery pills
├── 法器体系/ (Artifact System)      # Combat tools
├── 秘境体系/ (Secret Realm System)  # Independent small worlds
│
├── 心魔体系/ (Heart Demon System)   # v1.5 — Inner-demon mechanics (4 types)
├── 雷劫体系/ (Tribulation System)   # v1.5 — Heavenly tribulation (3-9-9 / 6-9 / 9-9-9)
├── 神识体系/ (Divine Sense System)  # v1.6 — Spiritual perception & soul combat
├── 器灵体系/ (Spirit Weapon System) # v1.7 — Weapon spirits (5 grades)
├── 契约体系/ (Contract System)      # v1.7 — Soul-binding contracts (4 types)
│
├── data/                           # Structured data (program-readable)
├── docs/                           # Meta-docs (template / schema / architecture / diagrams)
├── examples/                       # Example works (novels, usage demos)
├── stories/                        # Interactive fiction scripts (state-machine DSL)
├── interactive/                    # Interactive fiction engine + Web UI
├── scripts/                        # validate / export / interactive / generate_node / web_app
├── tests/                          # pytest unit tests (v1.7+ D. 工程化补强)
│
├── .github/workflows/validate.yml  # GitHub Actions CI
├── mkdocs.yml                      # Documentation site config
├── requirements.txt                # Runtime deps
├── requirements-dev.txt            # Dev/test/docs deps
└── CHANGELOG.md
```

## Core Relationships

```
灵根 ──决定──→ 功法 ──决定──→ 境界
 │                            ↑
 └──影响──→ 修炼速度     丹药 ──┘（突破）
                              ↑
灵气 ──决定──→ 灵脉 ──决定──→ 势力
 └─────────────┴──影响──→ 灵药（丹药原料）

神识 ──串联──→ 阵法/符箓/丹药/法器
心魔 ──叠加──→ 雷劫 ──突破──→ 境界（散功/淬体）
器灵 ──嵌入──→ 法器（法宝/灵宝）
契约 ──绑定──→ 灵兽/妖修/人/势力
```

Full diagram: see [图谱.md](docs/图谱.md).

## Interactive Fiction Engine (v1.2+)

State-machine driven interactive narrative using `data/*.yaml` as runtime world DB and `stories/*.md` as scripts.

```bash
# Try the demo
python scripts/interactive.py --story stories/demo_measuring_spirit.md

# Engine in headless mode (auto-pick first valid option, CI-friendly)
python scripts/interactive.py --story stories/demo_measuring_spirit.md --headless
```

- **Data-driven**: YAML is the single source of truth; scripts use `{realms.炼气期.lifespan}` placeholders
- **Conditional branching**: `if: 灵石 >= 3` / `flag.拜师`
- **DSL**: lightweight markdown-based script format, see [interactive/README.md](interactive/README.md)

## LLM Collaboration (v1.3+)

Semi-automated story-node generation by LLMs:

```bash
python scripts/generate_node.py \
  --story stories/hanli_vol1_mochui.md \
  --requirement "在发现天霞山牌位后，加一个'夜探禁地'节点" \
  --dry-run
```

- Auto-feeds yaml world summary (11 systems + key IDs) to LLM
- NodeValidator runs 5 checks (id conflicts / parsing / goto existence / refs / value ranges)
- 3-round auto-retry with feedback on failure

## Web API (v1.4+)

FastAPI wraps the interactive fiction engine into REST endpoints + a vanilla-JS Web UI:

```bash
pip install -r requirements.txt
python scripts/web_app.py
# → http://localhost:8000  ·  API docs: /docs  ·  Frontend: /play
```

8 endpoints: `/health`, `/`, `/story/{id}`, `POST /story/{id}/session`, `/session/{sid}`, `POST /session/{sid}/choice`, `POST /session/{sid}/restart`, ...

## Engineering (v1.7+)

- **Unit tests**: `tests/` with pytest — YAML schema, system completeness, validate.py logic
- **Documentation site**: `mkdocs.yml` with Material theme (deploy with `mkdocs gh-deploy`)
- **CI**: GitHub Actions runs `validate.py` + smoke tests + pytest on every PR
- **Dev deps**: see `requirements-dev.txt`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Core rules:

1. All .md files must contain a `## 关联` section
2. Each system must have a corresponding `data/*.yaml`
3. Cross-system relations are maintained in `data/relations.yaml`
4. Run `scripts/validate.py` and `pytest` before committing

## License

See [LICENSE](LICENSE).

---

For Chinese readers: see [README.md](README.md) for the full Chinese version.

## 关联

- 中文主文档：[README.md](README.md)
- 总索引：[索引.md](索引.md)
- 更新日志：[CHANGELOG.md](CHANGELOG.md)
- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全策略：[SECURITY.md](SECURITY.md)