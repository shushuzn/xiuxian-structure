<!--
PR 标题请遵循 Conventional Commits：
  <type>(<scope>): <subject>

type: feat | fix | docs | refactor | data | chore
scope: 境界 | 灵根 | 灵气 | 功法 | 丹药 | 法器 | data | ci | docs

示例：
  feat(境界): 新增结丹期文档
  fix(丹药): 修正筑基丹引用链接
-->

## 改动说明

<!-- 简述这个 PR 做了什么、为什么改 -->

## 改动类型

请勾选（删除不适用的）：

- [ ] 新增内容（境界/丹药/法器等具体条目）
- [ ] 修改现有内容
- [ ] 添加数据（data/*.yaml）
- [ ] 修改文档/图谱
- [ ] 修改 CI/脚本
- [ ] 重构（不改语义）

## 涉及的文件

<!-- 列出本次修改的所有 .md / .yaml 文件 -->

## 校验

- [ ] 本地运行 `python3 scripts/validate.py` 通过
- [ ] 新增的 .md 包含 `## 关联` 章节
- [ ] 新增/修改的 yaml 已同步到 relations.yaml（如涉及跨体系关联）
- [ ] mermaid 图谱已更新（如涉及新增体系或境界）

## 关联 Issue

<!-- 如有关联 Issue，填 `closes #123` 或 `fixes #456` -->

## Checklist

- [ ] 我已阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)
- [ ] 我已阅读 [docs/TEMPLATE.md](../docs/TEMPLATE.md)（如修改了 .md）
- [ ] 我已阅读 [docs/SCHEMA.md](../docs/SCHEMA.md)（如修改了 yaml）