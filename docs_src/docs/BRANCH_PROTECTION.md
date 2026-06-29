# 分支保护配置

本仓库使用 GitHub 默认 main 分支 + CI 校验的工作流。
**强烈建议** 在 GitHub 仓库设置中启用以下分支保护规则。

## 设置路径

`Settings` → `Branches` → `Branch protection rules` → `Add rule`

## 推荐规则（针对 `main` 分支）

| 规则 | 值 | 理由 |
|---|---|---|
| `Require a pull request before merging` | ✅ | 禁止直推，所有改动走 PR |
| `Require approvals` | 1（启用多人协作时） | 至少 1 人 review |
| `Dismiss stale pull request approvals when new commits are pushed` | ✅ | 新提交需重新 review |
| `Require status checks to pass before merging` | ✅ | CI 必须绿 |
| `Required checks` | `validate` | 跑 `Validate Knowledge Base` workflow |
| `Require linear history` | ✅ | 强制 rebase/merge，禁 merge commit |
| `Include administrators` | ✅ | 管理员也不能绕过 |

## Issue 标签体系

仓库建议使用以下标签（在 `Settings` → `Labels）创建：

```
bug          #d73a4a  错误报告
content      #0075ca  内容提议/讨论
data         #7057ff  数据问题
docs         #0e8a16  仅文档改动
infra        #fbca04  工程/脚本/CI
enhancement  #a2eeef  改进提议
question     #d876e3  提问
wontfix      #ffffff  决定不处理
duplicate    #cfd3d7  重复
help wanted  #008672  欢迎贡献
good first issue  #7057ff  适合新人
```

## GitHub Discussions

仓库可启用 `Discussions` 功能，分类建议：
- 📣 Announcements
- 💡 Ideas（提议新体系/新设定）
- 🙏 Q&A（提问）
- 📖 Show and tell（分享用法）

## 设置后效果

- 直推 main 被拒绝
- 未通过 CI 的 PR 无法 merge
- 所有改动有可追溯的 PR 历史

## 关于 force push

即使在分支保护下，admin 角色仍可 force push。
本仓库在 2025-06-21 的 `chore(release): 压缩 commit 历史` 操作中使用了
`git push --force-with-lease`，事后已恢复线性历史。

未来如需 force push，请：
1. 在 Issue 中说明理由
2. 确认无其他贡献者未推送的 commit
3. 用 `--force-with-lease` 而非 `--force`