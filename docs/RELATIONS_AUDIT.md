# data/relations.yaml 审计报告

> 自动生成于 2026-06-29
> 关系总数：336 | 失效端点：193 / 672 (28.7%)

## 已修复的错误模式

- 单/复数不一致（第一轮 ~134 处）：`realm` → `realms`、`elixir` → `elixirs`、`technique` → `techniques`、`artifact` → `artifacts`、`talisman` → `talismans`、`spirit_root` → `spirit_roots`、`contract` → `contracts`、`formation` → `formations`、`heart_demon` → `heart_demons`、`tribulation` → `tribulations`、`divine_power` → `divine_powers`、`spirit_stone` → `spirit_stones`、`org` → `factions`
- 拼写误复数（第二轮 ~20 处）：`secret_realms` → `secret_realm`、`immortal_realms` → `immortal_realm`、`ascension_tribulations` → `ascension_tribulation`
- 单复数少 s（第三轮 ~7 处）：`spirit_weapon` → `spirit_weapons`

## 剩余的失效端点（按 system 分组）

> 这些不是简单错位：大部分是把"section 名"误用为"system 名"，需要根据 description 上下文判断正确的 (system, section, id) 组合。

| system | 失效端点数 | 说明 |
|---|---|---|
| `examples` | 30 | 应该是实际案例的 yaml section（divine_powers/formations/factions/monsters/secret_realm/zong_men 都有 examples 段，但 system name 不能用 section name） |
| `six_realms` | 12 | 在 karma.yaml / underworld_realm.yaml 中是 section |
| `titles` | 10 | 在 immortal_realm.yaml / divine_realm.yaml 中是 section |
| `tribulations` | 10 | 需要按 description 人工确认 (system, section, id) |
| `divine_grades` | 9 | 在 divine_realm.yaml 中是 section（前缀应为 divine_realm:divine_grades:） |
| `underworld_domains` | 8 | 需要按 description 人工确认 (system, section, id) |
| `realms` | 6 | 需要按 description 人工确认 (system, section, id) |
| `types` | 6 | 需要按 description 人工确认 (system, section, id) |
| `shen_tong` | 5 | 需要按 description 人工确认 (system, section, id) |
| `divine_powers` | 5 | 需要按 description 人工确认 (system, section, id) |
| `factions` | 4 | 需要按 description 人工确认 (system, section, id) |
| `techniques` | 4 | 需要按 description 人工确认 (system, section, id) |
| `concentrations` | 4 | 应在 aether.yaml 中 section 名为 concentrations |
| `counter_elixirs` | 4 | 需要按 description 人工确认 (system, section, id) |
| `merit_levels` | 4 | 需要按 description 人工确认 (system, section, id) |
| `law_levels` | 4 | 需要按 description 人工确认 (system, section, id) |
| `veins` | 4 | 需要按 description 人工确认 (system, section, id) |
| `attributes` | 3 | 需要按 description 人工确认 (system, section, id) |
| `immortal_tribulations` | 3 | 需要按 description 人工确认 (system, section, id) |
| `aether` | 3 | 需要按 description 人工确认 (system, section, id) |
| `ascension_types` | 3 | 需要按 description 人工确认 (system, section, id) |
| `solutions` | 3 | 需要按 description 人工确认 (system, section, id) |
| `masters` | 3 | 需要按 description 人工确认 (system, section, id) |
| `spirit_beast` | 2 | 应为 spirit_roots:spirit_beast_tiers 或 monsters 中的 spirit_beast_tiers |
| `spirit_stones` | 2 | 需要按 description 人工确认 (system, section, id) |
| `domains` | 2 | 需要按 description 人工确认 (system, section, id) |
| `demon_aether` | 2 | 需要按 description 人工确认 (system, section, id) |
| `demon_titles` | 2 | 需要按 description 人工确认 (system, section, id) |
| `underworld_titles` | 2 | 需要按 description 人工确认 (system, section, id) |
| `underworld_races` | 2 | 需要按 description 人工确认 (system, section, id) |
| `dun_shu` | 2 | 需要按 description 人工确认 (system, section, id) |
| `dun_fa` | 2 | 需要按 description 人工确认 (system, section, id) |
| `fa_xiang` | 2 | 需要按 description 人工确认 (system, section, id) |
| `ascension_tribulation` | 2 | 需要按 description 人工确认 (system, section, id) |
| `paths` | 2 | 需要按 description 人工确认 (system, section, id) |
| `karmic_obsructions` | 2 | 需要按 description 人工确认 (system, section, id) |
| `karma_levels` | 2 | 需要按 description 人工确认 (system, section, id) |
| `time_powers` | 2 | 需要按 description 人工确认 (system, section, id) |
| `space_powers` | 2 | 需要按 description 人工确认 (system, section, id) |
| `forms` | 2 | 需要按 description 人工确认 (system, section, id) |
| `recognition_methods` | 1 | 需要按 description 人工确认 (system, section, id) |
| `barrier_types` | 1 | 需要按 description 人工确认 (system, section, id) |
| `demon_races` | 1 | 需要按 description 人工确认 (system, section, id) |
| `demon_ascension` | 1 | 需要按 description 人工确认 (system, section, id) |
| `demon_grades` | 1 | 需要按 description 人工确认 (system, section, id) |
| `underworld_tribulations` | 1 | 需要按 description 人工确认 (system, section, id) |
| `demon_tribulations` | 1 | 需要按 description 人工确认 (system, section, id) |
| `underworld_aether` | 1 | 需要按 description 人工确认 (system, section, id) |
| `ling_yu` | 1 | 需要按 description 人工确认 (system, section, id) |
| `space_artifacts` | 1 | 需要按 description 人工确认 (system, section, id) |
| `time_artifacts` | 1 | 需要按 description 人工确认 (system, section, id) |
| `stages` | 1 | 需要按 description 人工确认 (system, section, id) |

## 修复建议

由于本审计涉及 193 处端点（占 28.7%），全部修复需要逐条分析 description 上下文。建议分批按 system 处理：

1. **下一轮 (P1.3)**：批量修正 `divine_grades`、`titles`、`tribulations`、`six_realms` 等"section 误作 system"型（~80 处）
2. **P1.4**：人工修复 `examples:*`、`paths:*`、`barrier_types:*` 等需要语义判断的（~70 处）
3. **P1.5**：扩展 `data/*.yaml`，补齐缺失 id（如 `artifacts:fa_bao` 这种 tier 名而非具体物品）

## 自动审计脚本

`scripts/validate.py` 第 6 步会在每次 CI 跑时报告失效端点数。
