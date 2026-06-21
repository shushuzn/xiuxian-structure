// app.js — 修仙互动小说 SPA（零依赖）

const API = '';  // 同源
let currentStory = null;
let currentSid = null;

// ──────────── 路由 ────────────

function showPage(id) {
  for (const p of document.querySelectorAll('.page')) p.classList.add('hidden');
  document.getElementById(id).classList.remove('hidden');
}

function goHome() {
  currentStory = null;
  currentSid = null;
  showPage('story-list');
  loadStoryList();
}

function goGame() {
  showPage('game');
}

// ──────────── API 调用 ────────────

async function api(path, options = {}) {
  const r = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${body}`);
  }
  return r.json();
}

// ──────────── 故事列表 ────────────

async function loadStoryList() {
  const cards = document.getElementById('story-cards');
  cards.innerHTML = '<div class="loading-pulse">⏳ 加载中…</div>';
  try {
    const stories = await api('/');
    if (stories.length === 0) {
      cards.innerHTML = '<p class="muted">暂无故事</p>';
      return;
    }
    cards.innerHTML = stories.map(s => `
      <div class="card" onclick="startStory('${s.id}')">
        <div class="card-title">${escapeHtml(s.title)}</div>
        <div class="card-desc">${escapeHtml(s.description || '无简介')}</div>
        <div class="card-stats">
          <span>📖 ${s.node_count} 节点</span>
          <span>🏁 ${s.ending_count} 结局</span>
        </div>
      </div>
    `).join('');
  } catch (e) {
    cards.innerHTML = `<p class="muted">❌ 加载失败：${escapeHtml(e.message)}</p>`;
  }
}

// ──────────── 开始 / 重启 ────────────

async function startStory(storyId, initialState = {}) {
  try {
    const data = await api(`/story/${storyId}/session`, {
      method: 'POST',
      body: JSON.stringify({ initial_state: initialState }),
    });
    currentStory = { id: storyId };
    currentSid = data.sid;
    // 拉元数据
    const meta = await api(`/story/${storyId}`);
    document.getElementById('story-title').textContent = meta.title;
    document.getElementById('story-description').textContent = meta.description || '';
    goGame();
    renderNode(data);
  } catch (e) {
    alert('开始故事失败：' + e.message);
  }
}

async function restart() {
  if (!currentSid) return;
  try {
    const data = await api(`/session/${currentSid}/restart`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
    renderNode(data);
  } catch (e) {
    alert('重启失败：' + e.message);
  }
}

// ──────────── 选选项 ────────────

async function makeChoice(index) {
  if (!currentSid) return;
  // 视觉反馈：禁用所有按钮
  for (const b of document.querySelectorAll('.choice')) {
    b.disabled = true;
    b.style.opacity = '0.5';
  }
  try {
    const data = await api(`/session/${currentSid}/choice`, {
      method: 'POST',
      body: JSON.stringify({ choice_index: index }),
    });
    // 小延迟，让用户看到点击效果
    setTimeout(() => renderNode(data), 100);
  } catch (e) {
    alert('选择失败：' + e.message);
    for (const b of document.querySelectorAll('.choice')) {
      b.disabled = false;
      b.style.opacity = '1';
    }
  }
}

// ──────────── 渲染 ────────────

function renderNode(data) {
  const cur = data.current;
  // 节点 id
  document.getElementById('node-id').textContent = `【${cur.id}】`;

  // 正文
  document.getElementById('story-text').textContent = cur.text;

  // refs
  const refsEl = document.getElementById('refs');
  if (cur.refs && cur.refs.length > 0) {
    refsEl.innerHTML = `
      <span class="refs-label">📚 引用：</span>
      ${cur.refs.map(r => `<a class="ref" href="https://github.com/shushuzn/xiuxian-structure/blob/main/${encodeURI(r)}" target="_blank" rel="noopener">${escapeHtml(r)}</a>`).join('')}
    `;
    refsEl.classList.remove('hidden');
  } else {
    refsEl.innerHTML = '';
    refsEl.classList.add('hidden');
  }

  // 选项
  const choicesEl = document.getElementById('choices');
  if (cur.choices && cur.choices.length > 0) {
    choicesEl.innerHTML = cur.choices.map((c, i) => `
      <button class="choice" onclick="makeChoice(${i})">
        ${escapeHtml(c.label)}
        ${c.if_clause ? `<span class="if-clause">条件: ${escapeHtml(c.if_clause)}</span>` : ''}
      </button>
    `).join('');
    choicesEl.classList.remove('hidden');
  } else {
    choicesEl.innerHTML = '';
    choicesEl.classList.add('hidden');
  }

  // 结局 banner
  const endingBanner = document.getElementById('ending-banner');
  if (cur.type === 'ending' || !cur.choices || cur.choices.length === 0) {
    endingBanner.classList.remove('hidden');
  } else {
    endingBanner.classList.add('hidden');
  }

  // 状态面板
  renderState(data);

  // history
  renderHistory(data.history || [], cur.id);

  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderState(data) {
  const state = data.state || {};
  const attrs = state.attrs || {};
  const flags = state.flags || [];
  const el = document.getElementById('state-view');

  const rows = [];
  for (const [k, v] of Object.entries(attrs)) {
    let display;
    if (typeof v === 'object' && v !== null) {
      display = JSON.stringify(v);
    } else {
      display = String(v);
    }
    rows.push(`<div class="state-row"><span class="state-key">${escapeHtml(k)}</span><span class="state-val">${escapeHtml(display)}</span></div>`);
  }
  if (flags.length > 0) {
    rows.push(`<div class="state-row"><span class="state-key">flags</span><span class="state-val">${flags.map(escapeHtml).join(', ')}</span></div>`);
  }
  if (rows.length === 0) {
    el.innerHTML = '<p class="muted">（无状态）</p>';
  } else {
    el.innerHTML = rows.join('');
  }
}

function renderHistory(history, currentId) {
  const el = document.getElementById('history-view');
  el.innerHTML = history.map(nid => {
    const cls = nid === currentId ? 'current' : '';
    return `<li class="${cls}">${escapeHtml(nid)}</li>`;
  }).join('');
}

// ──────────── 工具 ────────────

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ──────────── 启动 ────────────

loadStoryList();
