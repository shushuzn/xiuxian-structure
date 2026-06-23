# v2.8 互动引擎扩展示范

## 元数据
id: v28_demo
title: v2.8 互动引擎演示
description: 展示 v2.8 新增的 3 个模块：突破/战斗/随机事件
start: start

## 节点 start (scene)
text: |
  你出生于下界一介散修，灵根为「{灵根}」。

  初入修真界，你将如何起步？

  当前状态：境界={境界} 灵石={灵石} 灵根={灵根}
data:
  ?境界: 炼气期
  灵根: 伪灵根
  灵石: 50
  breakthrough_pills: 0
  anti_tribulation: 0
next:
  - label: 前往山林采药（触发随机事件）
    goto: yunlai_encounter
    random_event:
      type: encounter
      seed: 1
  - label: 闭关修炼（推进时间）
    goto: biguan
    advance:
      years: 1
    set:
      breakthrough_pills: 3
  - label: 尝试突破（用 breakthrough action）
    goto: tu_po

refs:
  - 境界体系/炼气期
  - 灵根体系/灵根

## 节点 yunlai_encounter (scene)
text: |
  【随机事件】{last_event.title}

  {last_event.description}

  事件影响：
  {last_event.changes}

  当前灵石：{灵石}
next:
  - label: 继续
    goto: biguan

## 节点 biguan (scene)
text: |
  闭关 1 年，吞服 3 颗突破丹药。

  当前状态：境界={境界} 灵石={灵石} 丹药={breakthrough_pills}
next:
  - label: 出关战斗
    goto: fight
    combat:
      enemy: tie_bei_cang_lang
  - label: 再次触发随机事件
    goto: random_treasure
    random_event:
      type: treasure
  - label: 尝试突破
    goto: tu_po

refs:
  - 丹药体系/破境丹
  - 灵根体系/伪灵根

## 节点 fight (scene)
text: |
  【战斗】遭遇 {last_combat.enemy_name}

  战斗结果：{last_combat.victory}

  回合记录：
  {last_combat.turns}

  剩余血量：{last_combat.player_hp}
next:
  - label: 查看战利品
    goto: rewards

## 节点 rewards (scene)
text: |
  战斗胜利！获得战利品：

  灵石：{灵石}
  物品数：{item_count}
next:
  - label: 尝试突破
    goto: tu_po

## 节点 random_treasure (scene)
text: |
  【随机事件：宝藏】{last_event.title}

  {last_event.description}

  影响：{last_event.changes}
next:
  - label: 尝试突破
    goto: tu_po

## 节点 tu_po (scene)
text: |
  你已准备就绪，开始尝试突破到筑基期！

  灵气在体内翻涌……雷劫将至……
next:
  - label: 突破
    goto: after_breakthrough
    breakthrough:
      to: 筑基期

refs:
  - 境界体系/筑基期
  - 雷劫体系/三九天劫

## 节点 after_breakthrough (ending)
text: |
  突破结果：{last_breakthrough.message}

  from: {last_breakthrough.from}
  to: {last_breakthrough.to}
  tribulation_passed: {last_breakthrough.tribulation_passed}
  heart_demon: {last_breakthrough.heart_demon}

  当前境界：{境界}

  🏁 v2.8 演示完成
