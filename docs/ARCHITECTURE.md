# 架构决策记录

本文档记录本仓库的关键设计决策及理由。

## ADR-001：使用 Markdown + YAML 双轨制

**日期**：2025-06-21

**状态**：✅ 已采纳

**背景**：纯 Markdown 知识库无法被程序读取，无法做自动化校验、可视化、查询。

**决策**：
- `*.md` — 人类可读的描述（带 ## 关联、mermaid 图）
- `data/*.yaml` — 程序可读的结构化数据

**理由**：
- YAML 是修真体系的"权威数据源"，所有跨文件引用都基于 yaml 的 id
- Markdown 是"展示层"，描述 + 关联 + 图谱，方便人阅读
- CI 校验两者一致性

**后果**：
- ✅ 可校验、可视化、可扩展
- ⚠️ 维护成本加倍（改 md 时还要改 yaml）

---

## ADR-002：六体系目录结构 + data/*.yaml 平铺

**日期**：2025-06-21

**状态**：✅ 已采纳

**决策**：
- 体系描述按"体系名/" 目录组织（人类友好的层次）
- 数据按"体系类型" 平铺在 `data/`（程序友好的扁平命名空间）

**理由**：
- 中文目录名对人类直观，对程序无意义
- YAML 用 `realms/elixirs/techniques/...` 英文命名，对程序友好
- 链接走相对路径，跨平台无问题

---

## ADR-003：mermaid 而非外部图工具

**日期**：2025-06-21

**状态**：✅ 已采纳

**决策**：所有关系图用 mermaid 写在 `docs/图谱.md`

**理由**：
- GitHub 原生支持，无需第三方工具
- 版本控制友好（diff 即图变更）
- 单一文件 `docs/图谱.md` 包含所有图，避免散落

---

## ADR-004：Conventional Commits + 5 个固定 scope

**日期**：2025-06-21

**状态**：✅ 已采纳

**决策**：commit message 遵循 Conventional Commits，scope 限定为：
- `境界 | 灵根 | 灵气 | 功法 | 丹药 | 法器`
- `data | ci | docs`

**理由**：
- 便于自动生成 CHANGELOG
- scope 与体系对应，git log 可读性高

---

## ADR-005：CI 校验脚本只用 stdlib + pyyaml

**日期**：2025-06-21

**状态**：✅ 已采纳

**决策**：`scripts/validate.py` 依赖最小化（stdlib + pyyaml）

**理由**：
- 安全：避免第三方依赖投毒
- 速度：CI 启动快
- 可移植：任何 Python 3.8+ 环境都能跑

---

## ADR-006：单分支 main + PR 工作流

**日期**：2025-06-21

**状态**：✅ 已采纳

**决策**：使用 GitHub Flow，单 main 分支，所有改动走 PR。

**理由**：
- 个人/小团队项目无需 git-flow 复杂分支
- CI 自动跑校验，保证 main 始终可发布

---

## ADR-007：compress 17 个占位 commit 为 1 个

**日期**：2025-06-21

**状态**：✅ 已采纳

**背景**：仓库有 17 个 `feat: 你好` 占位 commit，无任何历史价值。

**决策**：rebase root，将前 17 个 commit squash 成 1 个 `chore: 初始提交`。

**理由**：
- 保护未来读者不被噪音 commit 困扰
- 历史信息已通过 commit message 完整保留

**风险与缓解**：
- 风险：force push 会改写共享历史
- 缓解：仓库早期阶段、只有 1 个贡献者、本地有 backup 分支

---

## ADR-008：data/schema.json — 30 个 yaml 的机器校验层

**日期**：2026-06-29

**状态**：✅ 已采纳

**背景**：data/*.yaml 的结构此前只在 ADR-002 文字描述 + 测试枚举中约定。任何 PR 都可以把 `elixirs.yaml` 改成 `elixirs:{elixir: [...]}` 而 CI 不报。

**决策**：在 `data/schema.json` 提供 30 个 yaml 的 JSON Schema（Draft-07），`scripts/validate.py` 第 [4/6] 步 `check_yaml_schema()` 在每次 CI 自动校验：
- 顶层 key 必须在白名单（如 `realms.yaml` 顶层只能是 `realms`、`references`）
- `list-of-dicts` 项必须有 `id` 字段
- `relations.yaml` 的 from/to 必须含 `:`，且引用 id 必须真实存在（由 `[6/6] audit_relations()` 负责）

**理由**：
- 防止 schema drift（yaml 结构变形不会被发现）
- 提供 LLM 工作流的 ground truth：喂给 LLM 的 yaml 知道"它的合法结构"
- 让 contribute PR 在 review 前自动校验

**后果**：
- ✅ 增删 section 时必须同步 schema.json（可机械化）
- ⚠️ schema.json 维护成本（25 个体系 × 5-15 section = ~150 行）
- 历史效果：v3.0 → v3.0.1 修复了 0 yaml 结构错误（基线已正确），但 `relations.yaml` 端点 193 条无效全部修正（`#6/6` 端点审计）

---

## ADR-009：scripts/build_docs_src.py — 跨平台 mkdocs 源同步

**日期**：2026-06-29

**状态**：✅ 已采纳

**背景**：原始设计 `docs_src/` 用 Git symbolic link 指向根目录 .md。在 Windows 上，symbolic link 需要开发者模式权限；mock clone 在 Windows 上会回退为"只包含路径文本"的占位文件，mkdocs build 全部失败。

**决策**：写 `scripts/build_docs_src.py` 直接 `shutil.copy2` 把根目录的 .md 复制到 `docs_src/` 镜像。每次 CI 在 `mkdocs build` 前自动 sync。

**理由**：
- 跨平台一致：Windows / macOS / Linux 都跑同一份 Python
- 不依赖 git clone 用户环境（开发者无需打开 dev mode）
- 可控：ignore 规则清晰（README / LICENSE / CHANGELOG 等元文件不复制）

**后果**：
- ✅ mkdocs build 在 Windows 本地 + Linux CI 都 0 警告（strict mode）
- ⚠️ 复制时间开销 ~0.5s（260 个 .md）
- ⚠️ `docs_src/` 不入仓（.gitignore 排除），本地同步状态作为生成产物

---

## ADR-010：tests/test_*.py 显式 encoding='utf-8' + PYTHONIOENCODING=utf-8

**日期**：2026-06-29

**状态**：✅ 已采纳

**背景**：在 Windows 控制台默认 GBK 编码下，`open(path)` 不带参数会以 GBK 解码 UTF-8 中文 yaml/.md 文件，失败；`subprocess.run()` 的 stdout/stderr 若子进程输出 emoji（如 `🔍`、`✅`）也会失败。原本的 33 个测试失败都是这个原因。

**决策**：
- 所有 `open(path)` 调用显式加 `encoding='utf-8'`
- `subprocess.run()` 的 `stdout=PIPE / stderr=PIPE` 加 `encoding='utf-8'`（替代 `universal_newlines=True`）
- `subprocess.run()` 调用 validate.py 时设 `env={**os.environ, "PYTHONIOENCODING": "utf-8"}`，确保子进程内部 print 也不走 GBK

**理由**：
- 代码可读性：显式 encoding > 默认编码（PEP 263）
- 跨平台一致：Windows / Linux / macOS 都用 UTF-8
- 不增加依赖（不引 tox 或 pytest-env）

**后果**：
- ✅ 本地 Windows：245/245 passed
- ✅ CI Linux（ubuntu-latest）：245/245 passed
- ⚠️ Python 3.14 升级到 pytest 9.x 后，部分 capture 行为变了（已修复）

---

## 如何新增 ADR

复制本节，命名为 `ADR-NNN：标题`，填入日期、状态、背景、决策、理由、后果。

新增时在 `README.md` 的"决策记录"链接补上。