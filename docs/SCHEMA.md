# 数据 Schema（YAML）

本仓库 `data/*.yaml` 是程序可读的权威数据源。GitHub Actions 会校验所有 yaml 符合 schema。

校验脚本：`scripts/validate.py`
schema 文件：`data/schema.json`

---

## 通用规则

- 编码：UTF-8
- 缩进：2 空格
- 中文字符串用双引号包，避免特殊字符歧义
- 列表项用 `-` 短横线
- 必填字段缺失时 CI 报错

---

## 境界体系 — `data/realms.yaml`

每个境界一个 entry，按从低到高排序。

```yaml
realms:
  - id: lianqi          # 英文 id，用于跨文件引用
    name: 炼气期          # 中文名
    order: 1              # 序号
    lifespan: 120          # 寿命上限（年）
    sub_stages:            # 子境界
      - chuqi
      - zhongqi
      - houqi
      - fengfeng
    abilities:             # 核心能力
      divine_sense_range: "数丈"      # 神识范围
      can_fly: false                  # 能否御空
      can_wield_high_tier: false      # 能否驱动高阶法器
    breakthrough:          # 突破到下一境界
      realm: zhuji
      requires:
        - zhuji_dan       # 必需丹药（引用丹药 id）
      risk: "经脉受损"     # 失败后果
      recommended_env: lingmai  # 推荐环境（引用灵气 id）
    restrictions:          # 做不到的事
      - 不能御空飞行
      - 神识无法离体
    references:            # 引用的体系文件
      - ../境界体系/炼气期.md
```

## 丹药体系 — `data/elixirs.yaml`

```yaml
elixirs:
  - id: zhuji_dan
    name: 筑基丹
    tier: ling_pin         # 品级：fan_pin/ling_pin/bao_pin/xian_pin
    used_in_realm: lianqi  # 适用境界（id）
    purpose: tuopo         # 用途：tuopo/zengyi/huifu/pigu
    ingredients:           # 主药（引用灵物 id，未来扩展）
      - tier_3_herb
    recipe_difficulty: high
    references:
      - ../丹药体系/丹药.md
```

## 功法体系 — `data/techniques.yaml`

```yaml
techniques:
  - id: chang_sheng_jue
    name: 长生诀
    tier: tian             # 品级：huang/xuan/di/tian
    attribute: wu          # 属性：wu/jin/mu/shui/huo/tu/variant
    max_realm: huashen     # 能修到的最高境界（id）
    style: jinggong        # 风格：jinggong/donggong/kuxiu
    references:
      - ../功法体系/功法.md
```

## 法器体系 — `data/artifacts.yaml`

```yaml
artifacts:
  - id: qing_feng_jian
    name: 青锋剑
    tier: zhong_jie        # 品级：di_jie/zhong_jie/gao_jie/fa_bao/ling_bao
    attribute: jin
    required_realm: zhuji  # 驱动所需境界（id）
    recognition: jingxue   # 认主方式：fali/jingxue/shenshi
    references:
      - ../法器体系/法器.md
```

## 灵根体系 — `data/spirit_roots.yaml`

```yaml
spirit_roots:
  - id: tian_ling_gen
    name: 天灵根
    grade: 4               # 1=废, 2=伪, 3=真, 4=天, 5=变异
    attribute_count: 1     # 属性数量
    speed_modifier: 5.0    # 相对伪灵根的修炼速度倍率
    breakthrough_modifier: 3.0
    references:
      - ../灵根体系/灵根.md
```

## 灵气体系 — `data/aether.yaml`

```yaml
aether:
  concentrations:
    - id: xi_bao
      name: 稀薄
      supports_realm: lianqi      # 能支撑的最高境界（id）
  veins:
    - id: wei_xing_lingmai
      name: 微型灵脉
      coverage_km: 5
      supports_realm: lianqi
      suitable_org_size: san_xiu  # 适合势力规模
  realms:                         # 界面（人界/灵界/仙界）
    - id: ren_jie
      name: 人界
      default_concentration: xi_bao
```

## 体系关联 — `data/relations.yaml`

跨体系的关系定义，供 mermaid 图生成。

```yaml
relations:
  - from: spirit_root:tian_ling_gen
    to: realm:lianqi
    type: influences     # influences/enables/requires/blocks
    description: "天灵根突破瓶颈天生占优"
  - from: elixir:zhuji_dan
    to: realm:zhuji
    type: enables
    description: "辅助突破炼气→筑基"
```

---

## 妖兽体系 — `data/monsters.yaml`

```yaml
grades:                       # 妖兽品级（对应修士境界）
  - id: yao_wang
    name: 妖王
    realm_equivalent: yuanying

attributes:                   # 妖兽属性
  - id: wu_xing
    name: 五行属性

spirit_beasts:                # 灵兽品级
  - id: ling_pin
    name: 灵品灵兽
    owner_realm: zhuji
```

## 势力体系 — `data/factions.yaml`

```yaml
scales:                       # 势力规模
  - id: top_sect
    name: 顶级宗门
    member_count: "50000+"
    max_realm: huashen
    lingmai_required: chao_ji_lingmai

forms:                        # 势力形态
  - id: zong_men
    name: 宗门
```

## 灵石体系 — `data/spirit_stones.yaml`

```yaml
tiers:                        # 灵石品级
  - id: xia_pin
    name: 下品灵石
    energy_unit: 1
    exchange_ratio: 1
    used_in_realm: lianqi

attributes:                   # 灵石属性
  - id: wu_shuxing
    name: 无属性
```

---

## ID 命名约定

- 全小写英文 + 下划线
- 数字不放在开头
- 体系内部唯一，跨体系可重名（引用时用 `{体系}:{id}` 前缀消歧）

---

## 扩展约定

新增体系时：
1. 在本 SCHEMA.md 补充章节
2. 在 `data/schema.json` 补充 JSON Schema 片段
3. 在 `scripts/validate.py` 加校验逻辑
4. 在 README.md 体系清单添加链接