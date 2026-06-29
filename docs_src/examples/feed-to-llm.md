# LLM 协作：自动生成互动小说节点

> 让大语言模型半自动扩展 `stories/*.md`，把"知识库 → 创作"的链路提速 10×。

## 🎯 适用场景

- 现有故事剧情太单薄，需要补一个"夜探禁地"分支
- 想让 LLM 帮写"试药失败"的多重后果
- 测试不同 LLM 对同一需求的输出差异

## ⚙️ 工作流

```
[1. 你写需求]              1 段自然语言（10-50 字）
   "在发现天霞山牌位后，加一个'夜探禁地'节点"
        ↓
[2. scripts/generate_node.py 自动]
   a. 读 data/*.yaml → 生成世界摘要（18 体系 + 关键 ID）
   b. 读 stories/*.md → 提取现有节点和跳转
   c. 喂给 LLM 一个严格 prompt（见下文）
   d. 解析 LLM 输出 → NodeValidator 5 项校验
   e. 失败 → 把错误反馈给 LLM 重试（最多 3 轮）
   f. 通过 → 写到 examples/generated/<id>.md
        ↓
[3. 你审核 + 接入]
   - 检查 examples/generated/ 里的节点
   - 手动把 `goto: <新节点>` 加到合适节点
   - 跑 python3 scripts/validate.py 确认
```

## 🚀 快速开始

### 前置

- Python 3.12 + pyyaml
- 一个 OpenAI 兼容 LLM 的 API key
  - OpenAI: `export OPENAI_API_KEY=sk-...`
  - 其他: `export LLM_BASE_URL=https://...` + `LLM_API_KEY=...`

### 命令

```bash
# Dry-run：只看 prompt，不调 LLM（不需要 key）
python3 scripts/generate_node.py \
  --story stories/hanli_vol1_mochui.md \
  --requirement "在发现天霞山牌位后，加一个'夜探禁地'节点" \
  --dry-run

# 正式跑（需要 key）
python3 scripts/generate_node.py \
  --story stories/hanli_vol1_mochui.md \
  --requirement "在发现天霞山牌位后，加一个'夜探禁地'节点"

# 改 LLM（默认 gpt-4o-mini）
python3 scripts/generate_node.py \
  --model deepseek-chat \
  --base-url https://api.deepseek.com/v1 \
  --story stories/hanli_vol1_mochui.md \
  --requirement "..."

# 调温度（高 = 更有创造性，低 = 更保守）
python3 scripts/generate_node.py --temperature 0.3 ...   # 几乎按数据写
python3 scripts/generate_node.py --temperature 1.0 ...   # 大胆想象
```

### 输出

成功后会写：
- `examples/generated/<新节点id>.md` — 节点片段 + 需求原文
- 在终端打印**接入建议**（在哪个节点的 next 加新跳转）

## 🔍 Validator 5 项校验

| # | 校验 | 严重度 |
|---|---|---|
| 1 | 节点 id 不与已有冲突 | ERROR |
| 2 | 解析成功（`## 节点 <id>` + 字段块） | ERROR |
| 3 | 所有 `goto` 目标都在已有节点中 | ERROR |
| 4 | `refs` 指向的文件存在 | WARNING |
| 5 | 数值字段范围（灵石 0-10000, 声望 0-100） | WARNING |

ERROR 会触发重试；WARNING 只给反馈不阻塞。

## 📝 Prompt 模板

完整 prompt 见 `scripts/generate_node.py` 的 `PROMPT_TEMPLATE`。核心约束：

1. **只输出 1 个新节点**（不要解释、不要其它格式）
2. **id 命名用中文短语**（"夜探禁地" / "杀墨大夫"）
3. **refs 用仓库的 18 个体系目录名**（`境界体系/炼气期.md` / `心魔体系/嗔魔.md` / `神识体系/神识攻击.md` 等）
4. **text 用第二人称**（"你..."）
5. **data 用 `?` 前缀**（保护玩家存档）
6. **goto 必须是已有节点**（否则校验失败）
7. **不要编造 yaml 里没有的数值**

## 🧪 验证 generate_node.py 不需要 LLM

`NodeValidator` 是纯 Python，可以直接测：

```python
import sys
sys.path.insert(0, 'scripts')
from interactive import World, Story
from generate_node import NodeValidator

world = World.from_yaml_dir('data')
story = Story.from_file('stories/hanli_vol1_mochui.md')

mock_node = '''## 节点 夜探禁地 (scene)
refs: 符箓体系/火球符.md
text: |
  你在夜里。
next:
  - label: 离开
    goto: 质问
'''

v = NodeValidator(story, world)
ok, nid = v.validate(mock_node)
print(f'ok={ok}, nid={nid}')
# ok=True, nid='夜探禁地'
```

## 📂 examples/generated/

LLM 生成的节点默认写到这里。**不会被 validate 当作知识库**（白名单 `examples/` 跳过关联检查），但会被 `interactive.py` 当作 story 加载（如果你想直接用作 story，需要手动移到 `stories/`）。

## 🌐 v1.5-v1.7 新体系的 LLM 生成示例

自 v1.5 起，知识库新增 5 个体系（心魔 / 雷劫 / 神识 / 器灵 / 契约），可作为新需求的目标：

```bash
# 演示心魔爆发（v1.5）
python3 scripts/generate_node.py \
  --story stories/hanli_vol1_mochui.md \
  --requirement "在借药筑基前，加一个'心魔爆发'节点，需清心丹≥1才可渡过"

# 演示器灵反噬（v1.7）
python3 scripts/generate_node.py \
  --story stories/aoyue_npc_fanpai.md \
  --requirement "在元婴渡劫前，加一个'器灵反噬'节点，选择强迫认主触发嗔魔+反噬"

# 演示契约选择（v1.7）
python3 scripts/generate_node.py \
  --story stories/aoyue_npc_fanpai.md \
  --requirement "在寒焰宗建宗后，加一个'幼狼抉择'节点，演示灵魂/平等/主从契约"
```

每个示例生成的节点都应通过 `NodeValidator`，并可在 `examples/generated/` 找到 mock 输出参考。

## 🤝 与其他工具的协作

- **export.py**：先把 `data/*.yaml` 导出成 `dist/xiuxian.json`，喂 LLM 时用 JSON 替代 YAML 摘要（如果你想）
- **interactive.py**：生成节点后，CI 的 `Verify all stories are well-formed` 步骤会自动校验连通性
- **validate.py**：节点最终接入 story 后，跑一次确认整个仓库仍合规
- **eval_llm.py**（v2.2）：批量评测多个 prompt 在多个 LLM 上的 NodeValidator 通过率
- **batch_generate.py**（v2.2）：批量生成节点并自动保存到指定目录

## 🧪 v2.2 评测集（tests/eval_prompts.yaml）

`tests/eval_prompts.yaml` 收录 10 个评测 prompt，覆盖：

- **v1.5 心魔 / 雷劫**（heart_demon_choice, tribulation_breakthrough, heart_demon_zhi_nian）
- **v1.6 神识**（divine_sense_attack）
- **v1.7 器灵 / 契约**（spirit_weapon_recognition, contract_lingbei_choice）
- **v2.0 飞升**（ascension_attempt）
- **v2.1 互动引擎**（inventory_interaction）

用法：

```bash
# 批量评测（不调 LLM，只看配置）
python3 scripts/eval_llm.py --prompts tests/eval_prompts.yaml --dry-run

# 多模型对比（需 API key）
export OPENAI_API_KEY=sk-...
python3 scripts/eval_llm.py \
  --prompts tests/eval_prompts.yaml \
  --models gpt-4o-mini,deepseek-chat \
  --report dist/eval_report.json

# 批量生成节点到指定目录
python3 scripts/batch_generate.py \
  --prompts tests/eval_prompts.yaml \
  --output examples/generated_batch/
```

## v3.0.1 增强：machine-verifiable LLM workflow

v3.0.1 新增了 `data/schema.json` 与完整可校验的 `data/relations.yaml`，让 LLM 生成节点既能保证自身结构合规，又能保证跨章节一致性。

### 在 prompt 中注入 schema（推荐）

修改 `scripts/generate_node.py` 的 `PROMPT_TEMPLATE`（或在自定义调用时拼装）：

```
## 数据结构约束（v3.0.1）

以下是从 data/schema.json 自动生成，你必须严格遵守：

```yaml
# 你的节点 text 字段可以使用这些 yaml 中的 id 来保证可信度：
- realms.yaml: {list of realms}
- elixirs.yaml: {list of elixirs}
- techniques.yaml: {list of techniques}
- relations.yaml: 跨体系关系的 336 条已经 validate.py 校验通过
```

切勿编造 schema.json 不存在的 id。
```

### 校验流程（CI 自动）

```yaml
# GitHub Actions 在 PR 上：
1. scripts/validate.py [4/7] check_yaml_schema() — 校验新增 yaml 结构
2. scripts/validate.py [6/7] audit_relations() — 校验 relations 端点
3. tests/test_stories.py — 校验生成节点可解析
4. mkdocs build --strict — 0 警告
```

如果 LLM 输出任何 `data:` 字段引用了不存在的 id，validate.py [6/7] 会立刻报警。

### 完整 machine-verifiable workflow

```bash
# 1. 让 LLM 生成节点（所有 yamls 作上下文）
python3 scripts/generate_node.py \
  --story stories/v31_demo.md \
  --requirement "在时空大殿前，加一个'选传送阵'分支" \
  --dry-run  # 先看 prompt 包含 schema 注入

# 2. 人工接入 + 跑全套校验
python3 scripts/validate.py          # 7 步结构 + schema + relations
PYTHONIOENCODING=utf-8 python3 -m pytest tests/ -q  # 300 测试
python3 -m mkdocs build --strict    # 0 警告

# 3. (可选) 导出喂给 LLM 的 JSON 一站式数据
python3 scripts/export.py            # → dist/xiuxian.json
```

### v3.0 vs v3.0.1 对比

| 项目 | v3.0 | v3.0.1 |
|---|---|---|
| yaml 结构校验 | 仅 check_yaml 解析 | + schema.json 30 体系白名单 |
| relations 端点 | 193 处失效不报 | validate.py [6/7] 实时报警 |
| docs 站 strict | 80 警告 | **EXIT=0** |
| 知识库体系数 | 23 | **27**（v3.0 之前的 v1.x 早已 27，README 漂移） |

## 💡 最佳实践

1. **从 demo 故事开始试**（`stories/demo_measuring_spirit.md` 节点少，LLM 容易出对）
2. **需求写得越具体越好**（"夜探禁地" + "用到火球符和微型灵脉" + "至少 1 个失败结局"）
3. **接受 WARNING**：refs 不存在可能是 LLM 写了一个合理但仓库还没建的体系 — 你后续加文档就行
4. **失败的 LLM 输出写到 stderr**：重试用尽后，脚本会把最后一次输出 dump 到 stderr，可以人工编辑后再跑
5. **审完手动接**：脚本不会自动把新节点挂到 story（避免 LLM 乱连），需要你决定接到哪个节点
6. **善用 schema 注入**：让 LLM 知道合法 id 列表，从源头减少 broken 引用
7. **跑 E2E 三件套**（validate + pytest + mkdocs）后再 commit

## 🚧 限制

- **不存 LLM 偏好**：每次跑都是新对话，不存会话历史
- **不跨故事**：每次只针对一个 `stories/*.md`
- **不接 dist/**：dist/ 里的 JSON 是 export 工具产物，不是 source of truth
- **v2.2+ 已支持多模型对比**：见 `scripts/eval_llm.py`
- **不在数据 yaml 中编造 id**：v3.0.1 schema.json 会立刻失败
