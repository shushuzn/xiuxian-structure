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

## 💡 最佳实践

1. **从 demo 故事开始试**（`stories/demo_measuring_spirit.md` 节点少，LLM 容易出对）
2. **需求写得越具体越好**（"夜探禁地" + "用到火球符和微型灵脉" + "至少 1 个失败结局"）
3. **接受 WARNING**：refs 不存在可能是 LLM 写了一个合理但仓库还没建的体系 — 你后续加文档就行
4. **失败的 LLM 输出写到 stderr**：重试用尽后，脚本会把最后一次输出 dump 到 stderr，可以人工编辑后再跑
5. **审完手动接**：脚本不会自动把新节点挂到 story（避免 LLM 乱连），需要你决定接到哪个节点

## 🚧 限制

- **不调多个 LLM**：当前只支持单 LLM 调用（未来可加 ensemble）
- **不存 LLM 偏好**：每次跑都是新对话，不存会话历史
- **不跨故事**：每次只针对一个 `stories/*.md`
- **不接 dist/**：dist/ 里的 JSON 是 export 工具产物，不是 source of truth
