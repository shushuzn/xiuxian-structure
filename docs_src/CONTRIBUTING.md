# 贡献指南

欢迎为 `xiuxian-structure` 添砖加瓦！本指南说明如何规范地提交修改。

## 目录约定

- `境界体系/` `灵根体系/` `天地灵气/` `功法体系/` `丹药体系/` `法器体系/` —— 六大核心体系
- `data/*.yaml` —— 程序可读的结构化数据，每个体系对应一个文件
- `docs/` —— 模板、schema、图谱
- `scripts/validate.py` —— 校验脚本
- `.github/workflows/` —— CI 配置

## 提交修改流程

1. **克隆仓库**
   ```bash
   gh repo clone shushuzn/xiuxian-structure
   cd xiuxian-structure
   ```

2. **创建分支**（按改动类型命名）
   ```bash
   git checkout -b feat/境界-结丹期
   git checkout -b fix/丹药-链接错误
   git checkout -b docs/更新图谱
   ```

3. **本地校验**
   ```bash
   python3 scripts/validate.py
   ```

4. **提交 + PR**
   ```bash
   git add .
   git commit -m "feat(境界): 新增结丹期文档"
   git push -u origin HEAD
   gh pr create --fill
   ```

## Commit 规范（Conventional Commits）

格式：`<type>(<scope>): <subject>`

| type | 用途 |
|---|---|
| `feat` | 新增内容（境界、丹药、关系） |
| `fix` | 修复内容错误、链接失效 |
| `docs` | 仅修改文档/注释 |
| `refactor` | 重构（不改语义） |
| `data` | 修改 yaml 数据 |
| `chore` | 杂项（脚本、CI） |

scope 建议（可省略）：
- `境界` `灵根` `灵气` `功法` `丹药` `法器`
- `data` `ci` `docs`

示例：
```
feat(境界): 新增结丹期文档
fix(丹药): 修正筑基丹引用链接
docs: 更新图谱，添加灵脉-势力关系
data(realms): 补全化神期字段
chore(ci): 添加 yaml 校验到 workflow
```

## .md 文档规范

参见 [docs/TEMPLATE.md](docs/TEMPLATE.md)。每个 .md 必须包含：

- 标题 `#` 后跟名称
- `## 定义` 或 `## 定位`
- `## 构成要素`（按维度拆解）
- `## 关联`（与其他文件的关系链接）

## YAML 数据规范

参见 [docs/SCHEMA.md](docs/SCHEMA.md)。

- `id` 全小写英文 + 下划线
- 修改 yaml 后必须跑 `scripts/validate.py`
- 修改跨体系关系时同步更新 `data/relations.yaml`

## 校验脚本

任何 PR 都会触发 CI 跑 `scripts/validate.py`。本地也建议先跑：

```bash
python3 scripts/validate.py
```

应输出 `✅ 全部通过`。当前 **7 步校验**：

| 步 | 检查项 | 失败提示 |
|---|---|---|
| [1/7] | `.md` 必须含 `## 关联` 章节 | 文件名 + 路径 |
| [2/7] | md 链接的目标文件真实存在 | 链接 + 路径 |
| [3/7] | yaml 文件能被 PyYAML 解析 | yaml 错误 |
| [4/7] | mermaid 代码块首行合法（flowchart/graph/...） | 文件名 |
| [5/7] | 索引.md / README.md 不引用丢失目录 | 文件名 |
| [6/7] | `data/relations.yaml` 的 336 条 from/to 引用真实存在 | 端点详情 |
| [7/7] | `mkdocs build --strict` 0 警告 | 前 5 个 WARNING |

CI 与本地跑同一份脚本。`fail-under` 默认 0 错误即通过，**警告不阻塞**但会显示。

### 跑测试

```bash
PYTHONIOENCODING=utf-8 python3 -m pytest tests/ -q
```

应输出 `300 passed`（当前）。新增 story/yaml 时记得同步加测试用例。

### 完整端到端检查

```bash
python3 scripts/validate.py   # 7 步结构性校验
python3 -m pytest tests/ -q   # 300 个单测
python3 -m mkdocs build --strict  # 文档站 0 警告
```

全绿 → 可放心开 PR。任何一个 failed → 立即修。

## Windows 用户常见错误（ADR-010）

在 Windows 控制台默认 GBK 编码下，**所有 python 调用必须显式设 `PYTHONIOENCODING=utf-8`**，否则会触发 `UnicodeDecodeError: 'gbk' codec`。

```bash
# ❌ 在 Windows PowerShell / cmd 默认 GBK 下失败
python3 scripts/validate.py
# UnicodeDecodeError: 'gbk' codec can't decode byte 0xa2

# ✅ 在 shell 中先设编码
set PYTHONIOENCODING=utf-8          # cmd
$env:PYTHONIOENCODING="utf-8"        # PowerShell
export PYTHONIOENCODING=utf-8        # bash/Git Bash

# ✅ 或在 Python 脚本里强制 stdout reconfigure
sys.stdout.reconfigure(encoding="utf-8")
```

CI（Ubuntu）默认 UTF-8，不会有此问题。本地 Windows 用户若未设置，会看到 emoji 字符乱码（如 `🔍` → `?`）。

## 添加新境界/丹药/法器

举例：添加一个新境界 `合体期`

1. 写 `境界体系/合体期.md`，按模板
2. 在 `data/realms.yaml` 加 `heti` 条目
3. 在 `境界体系/境界.md` 子条目列表添加链接
4. 在 `docs/图谱.md` 境界晋升图补上节点
5. 跑校验脚本
6. 提交 PR

## 添加新体系

1. 创建 `新体系/` 目录
2. 在 `data/` 加对应 yaml
3. 在 `docs/SCHEMA.md` 加 schema 章节
4. 更新 `README.md` 体系清单
5. 更新 `scripts/validate.py` 跳过规则（如有）
6. 更新 `docs/图谱.md` 加入体系全景图
7. 在 `索引.md` 补充关联

## 提问 / 讨论

提 Issue 即可，标签建议：
- `content` —— 内容问题
- `data` —— 数据问题
- `infra` —— 工程问题
- `discussion` —— 讨论/提议

## 架构决策参考（ADR）

重大设计决策记录在 `docs/ARCHITECTURE.md`。当前已有 10 个 ADR：

| ADR | 主题 |
|---|---|
| 001 | Markdown + YAML 双轨制 |
| 002 | 中文体系目录 + 英文 YAML namespace |
| 003 | mermaid 关系图（替代外部工具）|
| 004 | Conventional Commits + 5 个固定 scope |
| 005 | CI 校验只用 stdlib + pyyaml |
| 006 | 单分支 main + PR 工作流 |
| 007 | compress 17 个占位 commit 为 1 个 |
| **008** | `data/schema.json` 作为 30 yaml 的机器校验层 |
| **009** | `scripts/build_docs_src.py` 跨平台同步 docs_src |
| **010** | tests 显式 encoding='utf-8' + PYTHONIOENCODING=utf-8 |

新增 ADR 用 `ADR-NNN：标题` 格式复制到 `docs/ARCHITECTURE.md` 末尾。