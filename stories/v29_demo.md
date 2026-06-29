# v2.9 互动引擎演示（世界书 + 成就 + AI 叙事）

## 元数据
id: v29_demo
title: v2.9 互动引擎演示
description: |
  展示 v2.9 新增的 3 大模块：
  - **世界书**（worldbook action）：关键词触发的补充设定
  - **成就**（achievement action）：里程碑解锁
  - **AI 叙事**（narrate action）：自动生成自然语言描述
start: start

## 节点 start (scene)
text: |
  {{last_narrative}}

  你的灵根：{灵根}，境界：{境界}

  接下来你打算？
data:
  ?境界: 炼气期
  ?灵根: 天灵根
  ?灵石: 50
next:
  - label: 探索山林（触发 AI 叙事）
    goto: explore
    narrate: 你走入山林，发现古木参天、灵气浓郁。
  - label: 查看世界书
    goto: worldbook
  - label: 直接挑战妖兽
    goto: combat
    combat:
      enemy: tie_bei_cang_lang
  - label: 尝试突破
    goto: breakthrough
    breakthrough:
      to: 筑基期

## 节点 explore (scene)
text: |
  {{last_narrative}}

  山林中似乎有异动。
  你达到了**灵气浓郁**之地。

  接下来你打算？
next:
  - label: 采集灵草（触发成就）
    goto: pick_herb
    achievement: first_herb
  - label: 返回山门
    goto: start

## 节点 pick_herb (scene)
text: |
  你成功采集了一株百年灵草！

  你的成就「first_herb」已解锁！
  获得 100 贡献点。
data:
  贡献: 100
next:
  - label: 继续采集
    goto: explore
  - label: 返回山门
    goto: start

## 节点 worldbook (scene)
text: |
  【世界书：灵草】你记得师父曾说过：百年灵草需在清晨露水未干时采集，药性最足。

  灵草属于天材地宝体系的【灵草类】。
  参见 [天材地宝体系/灵草类](../天材地宝体系/灵草类.md)
next:
  - label: 返回
    goto: start

## 节点 combat (scene)
text: |
  {{last_combat}}
next:
  - label: 返回山门
    goto: start

## 节点 breakthrough (ending)
text: |
  {{last_breakthrough.message}}

  你现在是：{境界}
