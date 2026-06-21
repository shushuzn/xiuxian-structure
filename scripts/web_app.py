#!/usr/bin/env python3
"""
web_app.py — 互动小说 Web API（FastAPI）

把 scripts/interactive.py 的状态机引擎包装成 REST API，让前端 / 第三方
可以无状态地调用。

API：
  GET  /                       列出所有 stories
  GET  /story/{story_id}       故事元数据
  POST /story/{story_id}/session  创建会话 → 返回 sid + 起点节点
  GET  /session/{sid}          读状态：state + history + 当前节点
  POST /session/{sid}/choice   选选项：传 choice_index → 下一节点 + 新 state
  POST /session/{sid}/restart  重启：清 state
  GET  /health                 健康检查

状态：内存 dict（重启丢失，简单）

启动：
  pip install fastapi uvicorn
  uvicorn scripts.web_app:app --reload --port 8000
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from interactive import World, Story, Engine, State  # noqa: E402

STORIES_DIR = ROOT / "stories"
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "interactive" / "web"

# ────────────────────────────────────────────────────────
# 1. 应用初始化
# ────────────────────────────────────────────────────────

app = FastAPI(
    title="xiuxian-structure · 互动小说 API",
    description="基于修仙知识库的互动叙事引擎 Web 接口",
    version="1.4.0",
)

# 启动时加载所有 stories（cache）
_stories: dict[str, Story] = {}
_world: World = World.from_yaml_dir(DATA_DIR)
_sessions: dict[str, Engine] = {}


def _load_stories() -> None:
    """扫描 stories/*.md 并加载"""
    _stories.clear()
    if not STORIES_DIR.exists():
        return
    for md in sorted(STORIES_DIR.glob("*.md")):
        try:
            story = Story.from_file(md)
            _stories[story.id] = story
        except Exception as e:
            print(f"⚠️ 加载 {md.name} 失败: {e}", file=sys.stderr)


# Eager-load: 让 TestClient / 单测也能拿到数据
_load_stories()


@app.on_event("startup")
def _on_startup() -> None:
    _load_stories()
    print(f"🌍 已加载 {len(_world.data)} 个世界体系")
    print(f"📖 已加载 {len(_stories)} 个故事：{list(_stories.keys())}")


# ────────────────────────────────────────────────────────
# 2. 数据模型
# ────────────────────────────────────────────────────────

class NodeView(BaseModel):
    id: str
    type: str
    text: str
    choices: list[dict]  # [{label, index, goto, if_clause}]
    refs: list[str] = []


class StoryView(BaseModel):
    id: str
    title: str
    description: str
    start_node: str
    node_count: int
    ending_count: int


class SessionCreate(BaseModel):
    initial_state: dict[str, Any] = {}  # 可选初始 state


class SessionView(BaseModel):
    sid: str
    story_id: str
    state: dict
    history: list[str]
    current: NodeView


class ChoiceRequest(BaseModel):
    choice_index: int


# ────────────────────────────────────────────────────────
# 3. API 端点
# ────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "stories": len(_stories), "world_systems": len(_world.data)}


@app.get("/")
def list_stories() -> list[StoryView]:
    out: list[StoryView] = []
    for sid, story in _stories.items():
        endings = [n for n in story.nodes.values() if n.type == "ending"]
        out.append(StoryView(
            id=sid,
            title=story.title,
            description=story.description,
            start_node=story.start_node,
            node_count=len(story.nodes),
            ending_count=len(endings),
        ))
    return out


@app.get("/story/{story_id}")
def get_story(story_id: str) -> StoryView:
    story = _stories.get(story_id)
    if not story:
        raise HTTPException(404, f"故事 '{story_id}' 不存在")
    endings = [n for n in story.nodes.values() if n.type == "ending"]
    return StoryView(
        id=story.id,
        title=story.title,
        description=story.description,
        start_node=story.start_node,
        node_count=len(story.nodes),
        ending_count=len(endings),
    )


def _render_node(engine: Engine) -> NodeView:
    """把 engine 当前节点的视图返回（不修改 state）"""
    if not engine.history:
        node_id = engine.story.start_node
    else:
        node_id = engine.history[-1]
    node = engine.story.get(node_id)
    assert node
    # 应用 data 块（生成 view 用，不持久）
    saved_attrs = dict(engine.state.attrs)
    engine._apply_state(node)
    text = engine.world.render_template(node.text)
    valid: list[dict] = []
    for i, c in enumerate(node.choices):
        if engine.state.check(c.get("if", "")):
            valid.append({
                "label": c["label"],
                "index": i,
                "goto": c["goto"],
                "if_clause": c.get("if", ""),
            })
    # 恢复 state（保持持久层不变）
    engine.state.attrs = saved_attrs
    return NodeView(
        id=node.id,
        type=node.type,
        text=text,
        choices=valid,
        refs=node.refs,
    )


@app.post("/story/{story_id}/session")
def create_session(story_id: str, body: SessionCreate | None = None) -> SessionView:
    story = _stories.get(story_id)
    if not story:
        raise HTTPException(404, f"故事 '{story_id}' 不存在")
    initial = body.initial_state if body else {}
    engine = Engine(_world, story, State(initial))
    sid = uuid.uuid4().hex
    _sessions[sid] = engine
    # 走到第一个节点
    start_node = story.get(story.start_node)
    engine._apply_state(start_node)
    engine.history.append(story.start_node)
    return SessionView(
        sid=sid,
        story_id=story_id,
        state=engine.state.to_dict(),
        history=list(engine.history),
        current=_render_node(engine),
    )


@app.get("/session/{sid}")
def get_session(sid: str) -> SessionView:
    engine = _sessions.get(sid)
    if not engine:
        raise HTTPException(404, f"会话 '{sid}' 不存在或已过期")
    return SessionView(
        sid=sid,
        story_id=engine.story.id,
        state=engine.state.to_dict(),
        history=list(engine.history),
        current=_render_node(engine),
    )


@app.post("/session/{sid}/choice")
def make_choice(sid: str, body: ChoiceRequest) -> SessionView:
    engine = _sessions.get(sid)
    if not engine:
        raise HTTPException(404, f"会话 '{sid}' 不存在")
    if not engine.history:
        raise HTTPException(400, "会话还没开始")

    # 找到当前节点的 valid choices
    cur_id = engine.history[-1]
    node = engine.story.get(cur_id)
    if not node:
        raise HTTPException(500, f"当前节点 '{cur_id}' 不存在")

    # 应用 data 块（确保 if 求值看到完整 state）
    saved_attrs = dict(engine.state.attrs)
    engine._apply_state(node)
    valid = [(i, c) for i, c in enumerate(node.choices) if engine.state.check(c.get("if", ""))]
    engine.state.attrs = saved_attrs  # 恢复

    if not valid:
        raise HTTPException(400, "当前节点没有可用选项（已到结局）")
    if not (0 <= body.choice_index < len(valid)):
        raise HTTPException(400, f"choice_index 必须在 0-{len(valid) - 1} 之间")

    _, chosen = valid[body.choice_index]
    # 应用副作用
    if "set" in chosen:
        engine.state.attrs.update(chosen["set"])
    if "flag" in chosen:
        engine.state.set_flag(chosen["flag"])

    next_id = chosen["goto"]
    next_node = engine.story.get(next_id)
    if not next_node:
        raise HTTPException(500, f"goto 目标 '{next_id}' 不存在")
    engine._apply_state(next_node)
    engine.history.append(next_id)

    return SessionView(
        sid=sid,
        story_id=engine.story.id,
        state=engine.state.to_dict(),
        history=list(engine.history),
        current=_render_node(engine),
    )


@app.post("/session/{sid}/restart")
def restart(sid: str, body: SessionCreate | None = None) -> SessionView:
    engine = _sessions.get(sid)
    if not engine:
        raise HTTPException(404, f"会话 '{sid}' 不存在")
    initial = body.initial_state if body else {}
    engine.state = State(initial)
    engine.history = []
    start_node = engine.story.get(engine.story.start_node)
    engine._apply_state(start_node)
    engine.history.append(engine.story.start_node)
    return SessionView(
        sid=sid,
        story_id=engine.story.id,
        state=engine.state.to_dict(),
        history=list(engine.history),
        current=_render_node(engine),
    )


# ────────────────────────────────────────────────────────
# 4. 静态文件（前端 SPA — v1.4 PR2 接入）
# ────────────────────────────────────────────────────────

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/play/{story_id}")
    def play_page(story_id: str):
        """SPA 入口 — 单页应用加载所有 JS/CSS"""
        return FileResponse(str(WEB_DIR / "index.html"))

    @app.get("/play")
    def play_index():
        return FileResponse(str(WEB_DIR / "index.html"))


# ────────────────────────────────────────────────────────
# 5. CLI 启动
# ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n🎮 启动互动小说 Web API…")
    print("📖 API 文档: http://localhost:8000/docs")
    print("🎨 前端入口: http://localhost:8000/play")
    print("⏹️  Ctrl-C 停止\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
