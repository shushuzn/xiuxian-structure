# v3.1 综合演示 - 跨体系大冒险

## 元数据
id: v31_demo
title: v3.1 综合演示 · 跨体系大冒险
description: |
  展示 v2.10-v2.17 所有新系统的综合应用：
  - 秘境体系 (秘药岛/雷师之墓)
  - 天材地宝体系 (灵草/灵石)
  - 宗门体系 (落云宗/天星城商会)
  - 因果体系 (功德/业力)
  - 时空体系 (空间秘境)
  - 跨境界试炼副本
  - 世界书/成就/AI 叙事

  主角: 散修韩立后期（元婴化神过渡期）
  4 大路径, 5 种结局
start: 开局

## 节点 开局 (scene)
text: |
  【第 47 章 · 乱星海域风云再起】

  {{last_narrative}}

  你（韩立）已化神期 30 余年，立于下界之巅。
  但天道无常，一日，**灵界飞升令**忽至。
  持此令者，必是**大因果**之人。

  你将如何抉择？
data:
  ?境界: 化神期
  ?灵根: 天灵根
  ?灵石: 50000
  ?功德: 1000
  ?声望: 80
  ?因果: 善缘
next:
  - label: 探索【空间秘境】
    goto: kongjian_miji
  - label: 拜访【落云宗】求取飞升之法
    goto: luoyun_zong
  - label: 接受【灵药岛】邀请
    goto: lingyaodao
  - label: 独自【渡飞升之劫】
    goto: shendan_guodu
  - label: 查看世界书「飞升」
    goto: worldbook_feisheng
    worldbook: feisheng_guide

refs:
  - 飞升体系/飞升.md
  - 时空体系/时空总览.md
  - 秘境体系/空间秘境.md

## 节点 kongjian_miji (scene)
text: |
  【空间秘境 · 蓬莱仙岛】

  你踏入了传说中的蓬莱仙岛。
  此岛漂浮于虚空之间，时间流速不同。

  岛上有**万年灵草**、**极品灵石**、传说中还有**时光之沙**。
  但岛上守卫凶险——有**化形期海妖**与**上古阵法**。

  你的选择将决定你的收获。
next:
  - label: 直取时光之沙（高风险）
    goto: shi_guang_sha
    set:
      风险: 高
    narrate: 你感到时间在扭曲，仿佛踏入了一场无尽的轮回
  - label: 稳妥采集灵草（中等风险）
    goto: ling_cao_qu
    random_event:
      type: encounter
      seed: 42
  - label: 退出秘境（保守）
    goto: shendan_guodu

## 节点 shi_guang_sha (scene)
text: |
  【时光之沙】

  你在蓬莱深处找到了传说中的**时光之沙**！
  这可是助悟时间法则的至高宝物。

  但守护此沙的是**时空之灵**——强大的概念级存在。
  你必须做出抉择。
next:
  - label: 以战力强行夺取
    goto: combat_temporal
    combat:
      enemy: shi_kong_zhi_ling
  - label: 以功德化解（消耗 500 功德）
    goto: shendan_guodu
    set:
      功德: 500
  - label: 以因果律说服
    goto: karma_persuade
    narrate: 你以因果律与时空之灵论道

## 节点 combat_temporal (ending)
text: |
  【战斗结果】
  {{last_combat.narrative}}

  你的灵石：{灵石}，功德：{功德}

  🏁 时空法则领悟成功！
  你获得 **时光之沙**。

refs:
  - 时空体系/时间法则.md
  - 时空体系/时空宝物.md
refs:
  - 时空体系/时间法则.md

## 节点 karma_persuade (scene)
text: |
  你以**因果律**与时空之灵论道三日三夜。
  最终，时空之灵被你的因果领悟所动，主动让出时光之沙。

  {{last_narrative}}

  你获得 **时光之沙** + 因果感悟 +500。
data:
  因果感悟: 500
next:
  - label: 返回
    goto: shendan_guodu

## 节点 ling_cao_qu (scene)
text: |
  【灵草区】

  {{last_event.narrative}}

  随机事件已发生。
  你获得了一些 **千年灵草**。

  但你也消耗了一些灵石。
next:
  - label: 返回
    goto: shendan_guodu

## 节点 luoyun_zong (scene)
text: |
  【落云宗 · 仙山之巅】

  你拜访了乱星海域的顶级宗门【落云宗】。
  宗主【落云真人】亲自接见。

  落云真人告诉你，飞升有 3 大难关：
  1. **飞升之劫**（九九天劫 + 3 道特殊）
  2. **界面壁障**（需大法力穿越）
  3. **飞升者分类**（普通/天才/传说/仙帝）

  你将如何应对？
next:
  - label: 求取**飞升丹**与**渡劫阵**
    goto: request_pills
  - label: 观看【跨境界试炼】
    goto: trial_dungeon
    trial: yuanying_hell
  - label: 婉拒，独行
    goto: shendan_guodu
    narrate: 你选择独自面对飞升之劫

## 节点 request_pills (scene)
text: |
  落云真人赐你：
  - 飞升丹 ×3
  - 渡劫阵图 ×1
  - **因果祝福**（因果+200）

  你的准备更充分了。
data:
  飞升丹: 3
  渡劫阵图: 1
  因果: 200
next:
  - label: 返回
    goto: shendan_guodu

## 节点 lingyaodao (scene)
text: |
  【灵药岛 · 浮岛秘境】

  你接受了**灵药岛**的邀请。
  岛主是化形妖修【寒蟾真君】。

  寒蟾真君说：你曾对妖族有恩（救过 5 只小妖），故邀请你。
  岛上**九幽还魂草**对化神期有奇效。

  你将如何应对？
next:
  - label: 接受邀请，登岛采药
    goto: island_pick
  - label: 婉拒，担心陷阱
    goto: shendan_guodu

## 节点 island_pick (scene)
text: |
  你登上灵药岛。
  寒蟾真君信守承诺，让你采摘了**九幽还魂草 ×3**。

  因果循环：当年救妖，今日得药。
  你的【因果】值大幅上升。

  {{last_narrative}}
data:
  因果: 500
  九幽还魂草: 3
next:
  - label: 返回
    goto: shendan_guodu

## 节点 trial_dungeon (scene)
text: |
  【跨境界试炼 · 元婴期·地狱】

  {{last_trial.narrative}}

  你观摩了一场试炼。获得启发。
next:
  - label: 返回
    goto: shendan_guodu

## 节点 shendan_guodu (ending)
text: |
  【飞升之劫】

  多年后，你已准备充分。
  你站在飞升台前，回望这一生。

  {{last_narrative}}
  {{last_breakthrough.message}}

  你的境界：{境界}，因果：{因果}，功德：{功德}
  灵石：{灵石}

  你的成就：
  - 第一个成就：first_herb

  📊 结局：飞升仙界 · 仙帝之资
  耗时：3 节点
