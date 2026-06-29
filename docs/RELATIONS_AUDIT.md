# data/relations.yaml 审计报告

> 最后更新于 2026-06-29
> **当前状态**：✅ **全部 336 条关系（672 个端点）通过 validate.py [6/6] 端点校验**
> 关系总数：336 | 来源体系分布：29 个 | 失效端点：**0**

## 修复历程

| 阶段 | 提交 | 端点状态 |
|---|---|---|
| 起点 | `c37ae8` (reset 后) | 313/672 失效（93.2%） |
| P1.2 (单/复数 + 误复数 + 少 s) | `73bc767` | 减少 ~210 处 |
| P1.2 (audit + 容错) | `e467eab` | 1 warning / 引入自动审计 |
| **P1.3 (上下文系统映射)** | **`6edf1c8`** | 193 → **0** ✅ |
| P1.4 (结构化分组) | 本次 | 0（+头部注释，按 from-system 分组） |

## 错误模式分类（已 100% 修复）

- **A. 单/复数不一致**（13 个 system 映射，~200 处）：`realm` → `realms`、`elixir` → `elixirs`、`technique` → `techniques`、`artifact` → `artifacts`、`talisman` → `talismans`、`spirit_root` → `spirit_roots`、`contract` → `contracts`、`formation` → `formations`、`heart_demon` → `heart_demons`、`tribulation` → `tribulations`、`divine_power` → `divine_powers`、`spirit_stone` → `spirit_stones`、`org` → `factions`
- **B. 拼写误复数**（3 个）：`secret_realms` → `secret_realm`、`immortal_realms` → `immortal_realm`、`ascension_tribulations` → `ascension_tribulation`
- **C. 单复数少 s**（1 个）：`spirit_weapon` → `spirit_weapons`
- **D. section 误用 system**（~80 处）：`divine_grades:xxx` → `divine_realm:xxx`、`underworld_titles:xxx` → `underworld_realm:xxx`、`demon_*:xxx` → `demon_realm:xxx`、`examples:xxx` → `{factions,monsters,formations,combat}:xxx` 等
- **E. 上下文歧义端点**（~140 处）：按 description 手动映射（如 `realms:xian_jie` 在 6 个 yaml 中都出现，需要按 description 上下文判断是 `ascension` / `combat` / `divine_sense` 等）

## 自动审计

`scripts/validate.py` 第 6 步 `audit_relations()` 会在每次 CI 跑时自动校验：

```bash
$ python3 scripts/validate.py
  ...
  [6/6] relations.yaml 端点校验...
  ✓ data/relations.yaml：336 条关系均有效
```

如未来新增关系端点不符合规范，CI 会出现警告/错误阻止合入。

## 文件结构（v3.0.1 + P1.4）

`data/relations.yaml` 按 from-system 名字典排序，每组前加注释头（共 29 个 group），便于人读与审查：

```yaml
# ── aether (9 条) ──
- from: aether:xi_bao
  to: realms:lianqi
  type: enables
  description: 稀薄灵气下炼气期尚可
...
# ── zi_ling_gen (1 条) ──
...
```
