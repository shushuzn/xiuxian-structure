# 安全策略

## 支持的版本

| 版本 | 支持状态 |
|---|---|
| main | ✅ 积极维护 |

旧版本不再接受安全更新。

## 报告漏洞

如果你发现本仓库存在安全问题（例如 GitHub Actions 中的密钥泄漏、workflow 注入等），请通过以下方式私下报告：

- 📧 邮件：你的 GitHub 账户邮箱（如公开）
- 🔒 或通过 GitHub 的 [私有漏洞报告](../../security/advisories/new) 功能

请**不要**在公开 Issue 中披露安全问题。

## 响应时效

- 确认收到：48 小时内
- 评估与修复：7 天内
- 公开披露：修复发布后 90 天，或与报告者协商后

## 范围

本仓库是**纯文档/数据仓库**（Markdown + YAML + Python 校验脚本），风险面包括：

- `.github/workflows/*.yml` — CI 配置
- `scripts/*.py` — 校验脚本
- 任何可能引入第三方依赖的 PR

典型风险：

| 风险 | 缓解 |
|---|---|
| Workflow 注入 | 限制 `pull_request_target` 使用，避免未信任输入 |
| 第三方依赖投毒 | 校验脚本只用 stdlib + pyyaml，pin 版本 |
| Markdown XSS | GitHub 渲染时沙箱化，无需特别处理 |

## 历史事件

暂无。