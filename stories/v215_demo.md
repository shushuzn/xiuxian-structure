# v2.15 跨境界试炼副本演示

id: v215_demo
title: v2.15 试炼副本演示
description: |
  展示 v2.15 新增的 TrialDungeon 模块：
  - 9 境界 × 4 难度 = 36 个试炼关卡
  - 自动通过率计算
  - 通关奖励 / 失败惩罚
  - 进度跟踪

  你将在不同境界挑战不同难度的试炼副本。
start: start

## 节点 start (scene)
text: |
  {{last_narrative}}

  你的境界：{境界}，灵石：{灵石}
data:
  ?境界: 炼气期
  ?灵根: 天灵根
  ?灵石: 100
next:
  - label: 挑战炼气期·简单
    goto: lianqi_easy
    trial: lianqi_easy
  - label: 挑战炼气期·困难
    goto: lianqi_hard
    trial: lianqi_hard
  - label: 查看可挑战的关卡
    goto: list_stages
  - label: 突破到筑基期
    goto: zhuji
    breakthrough:
      to: 筑基期

## 节点 lianqi_easy (scene)
text: |
  【试炼结果】
  {{last_trial.narrative}}

  你的灵石：{灵石}，声望：{声望}
next:
  - label: 继续挑战
    goto: start
  - label: 查看进度
    goto: list_stages

## 节点 lianqi_hard (scene)
text: |
  【试炼结果】
  {{last_trial.narrative}}

  你的灵石：{灵石}，声望：{声望}
next:
  - label: 继续挑战
    goto: start

## 节点 list_stages (scene)
text: |
  当前境界：{境界}
  可挑战的关卡需先匹配境界。

  境界匹配：炼气期可挑战 4 关
  其他境界需突破后才可挑战。
next:
  - label: 返回
    goto: start

## 节点 zhuji (ending)
text: |
  突破结果：{last_breakthrough.message}

  恭喜！你的境界是：{境界}

  🏆 v2.15 演示完成
