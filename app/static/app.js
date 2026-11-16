"use strict";
/* RAG Agent Tester client. Model output and chunk text are untrusted: they are only ever set via textContent
   (the el() helper never uses innerHTML); the only innerHTML is the constant SVG icon markup below. */

const SVGNS = "http://www.w3.org/2000/svg";
const ICONS = {
  layers: '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  menu: '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
  panel: '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M15 3v18"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
  check: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
  warn: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  abstain: '<circle cx="12" cy="12" r="10"/><path d="M8 12h8"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  tool: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
  hash: '<path d="M4 9h16"/><path d="M4 15h16"/><path d="M10 3 8 21"/><path d="m16 3-2 18"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  doc: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  retry: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
};
const STATUS = {
  answered: { label: "Answered", icon: "check" },
  abstain: { label: "Abstained", icon: "abstain" },
  error: { label: "Error", icon: "alert" },
  pending: { label: "Running", icon: "clock" },
};
const TABS = ["sources", "timeline", "context", "tokens", "raw"];
const NARROW_INSPECTOR = window.matchMedia("(max-width: 959px)");
const NARROW_SIDEBAR = window.matchMedia("(max-width: 1279px)");

const S = { status: null, config: null, turns: [], selected: null, tab: "sources", pending: false, poll: null, seq: 0 };
const $ = (id) => document.getElementById(id);

/* ---------- DOM helpers ---------- */
function icon(name) {
  const s = document.createElementNS(SVGNS, "svg");
  s.setAttribute("viewBox", "0 0 24 24");
  s.setAttribute("class", "i");
  s.setAttribute("aria-hidden", "true");
  s.innerHTML = ICONS[name] || "";
  return s;
}

function el(tag, props, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = String(v);
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : String(v));
  }
  append(n, kids);
  return n;
}

function append(n, kids) {
  for (const k of kids.flat(Infinity)) {
    if (k == null || k === false) continue;
    n.append(k instanceof Node ? k : document.createTextNode(String(k)));
  }
  return n;
}

const fmt = {
  n: (x) => (x == null ? "—" : Number(x).toLocaleString("en-US")),
  s: (x) => (x == null ? "—" : `${Number(x).toFixed(Number(x) < 10 ? 2 : 1)} s`),
  score: (x) => (x == null ? "—" : Number(x).toFixed(3)),
  time: (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
};

function shortId(id) {
  const m = /p0*(\d+)-0*(\d+)$/.exec(id);
  return m ? `p.${m[1]} · ${m[2]}` : id;
}

function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch (_) { /* storage unavailable: per-viewer convenience only */ }
  return null;
}

/* ---------- server ---------- */
async function api(path, body) {
  const opts = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, opts);
  let data = null;
  try { data = await res.json(); } catch (_) { /* non-JSON */ }
  if (!res.ok) throw Object.assign(new Error((data && data.error) || `HTTP ${res.status}`), { status: res.status });
  return data;
}

async function loadStatus() {
  clearTimeout(S.poll);
  try {
    S.status = await api("/api/status");
  } catch (e) {
    S.status = null;
    showBanner([icon("alert"), el("div", {}, "Cannot reach the UI server. Is ", el("code", { text: "python app/server.py" }), " still running?")]);
    renderTopbar();
    updateSend();
    S.poll = setTimeout(loadStatus, 4000);
    return;
  }
  const names = Object.keys(S.status.configs);
  if (!S.config || !names.includes(S.config)) {
    const remembered = store("rag-tester-mode");
    S.config = names.includes(remembered) ? remembered : S.status.default;
    renderConfigOptions(names);
  }
  renderConfigDetails();
  renderHealth();
  renderBanner();
  renderTopbar();
  renderDocument();
  if (!$("samples").childElementCount) renderSamples();
  updateSend();
  const warm = currentConfig()?.warm?.state;
  if (warm === "cold" && S.status.store) api("/api/warm", { config: S.config }).then(loadStatus).catch(() => {});
  else if (warm === "loading") S.poll = setTimeout(loadStatus, 1500);
}

const currentConfig = () => S.status?.configs?.[S.config];

/* ---------- sidebar ---------- */
const isLibrary = (name) => !!S.status?.configs?.[name]?.document?.library;
const modeLabel = (name) => (isLibrary(name) ? "All documents" : name);

function renderConfigOptions(names) {
  const sel = $("config");
  const lib = names.filter(isLibrary);
  const bench = names.filter((n) => !isLibrary(n));
  sel.replaceChildren(
    ...lib.map((n) => el("option", { value: n, text: "All documents" })),
    bench.length && el("optgroup", { label: "Benchmark configs: one fixed collection" },
      bench.map((n) => el("option", { value: n, text: n === "final" ? `${n} (frozen)` : n }))),
  );
  sel.value = S.config;
}

function renderConfigDetails() {
  const c = currentConfig();
  const dl = $("config-details");
  if (!c) return dl.replaceChildren();
  const rows = [
    ["model", c.model], ["retrieval", c.method], ["top_k", c.top_k], ["context budget", `${fmt.n(c.context_budget_chars)} chars`],
    ["max tool calls", c.max_tool_calls], ["collection", c.collection], ["prompt", c.prompt_version],
  ];
  if (String(c.method).includes("rerank")) rows.push(["reranker", String(c.reranker).split("/").pop()]);
  if (c.neighbors) rows.push(["neighbors tool", "on"]);
  for (const d of c.document?.documents || []) rows.push(["document", `${d.title} (${d.chunks})`]);
  dl.replaceChildren(...rows.flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v ?? "—" })]));
}

function healthItem(kind, title, detail) {
  const ico = { ok: "check", warn: "warn", bad: "alert" }[kind];
  return el("li", {}, el("span", { class: kind }, icon(ico)), el("div", {}, el("span", { class: "h-title", text: title }), detail && el("span", { class: "h-detail", text: detail })));
}

function renderHealth() {
  const st = S.status;
  const w = currentConfig()?.warm || { state: "cold" };
  const items = [
    st.store ? healthItem("ok", "Vector store found", st.store_display || st.store) : healthItem("bad", "Vector store missing", "run python scripts/build_index.py"),
    st.api_key ? healthItem("ok", "Gemini API key loaded", "from environment or .env") : healthItem("bad", "GEMINI_API_KEY missing", "add it to .env and restart"),
    w.state === "ready" ? healthItem("ok", "Retrieval models ready", "embedder, BM25 and reranker in memory")
      : w.state === "error" ? healthItem("bad", "Retrieval models failed", w.error)
      : healthItem("warn", w.state === "loading" ? "Loading retrieval models…" : "Retrieval models not loaded", "first load takes a while"),
  ];
  $("health").replaceChildren(...items);
}

function renderBanner() {
  const st = S.status;
  if (!st.store) {
    return showBanner([icon("alert"), el("div", {}, "Vector store not found. Run ", el("code", { text: "python scripts/build_index.py" }), ", then reload this page.", st.store_error ? el("div", { class: "saved", text: st.store_error }) : null)]);
  }
  if (!st.api_key) {
    return showBanner([icon("alert"), el("div", {}, "GEMINI_API_KEY not found. Add ", el("code", { text: "GEMINI_API_KEY=..." }), " to ", el("code", { text: ".env" }), " in the repo root and restart the server.")]);
  }
  showBanner(null);
}

function showBanner(kids) {
  const b = $("banner");
  b.hidden = !kids;
  b.replaceChildren(...(kids || []));
}

/** Title, sample-question source and placeholder follow the selected config's document. */
function renderDocument() {
  const doc = currentConfig()?.document;
  const label = doc ? [doc.title, doc.subtitle].filter(Boolean).join(" · ") : "—";
  $("brand-sub").textContent = label;
  $("brand-sub").title = label;
  $("empty-doc").textContent = doc?.title || "—";
  $("samples-source").textContent = doc?.samples_source || "";
  $("question").placeholder = doc && !doc.library ? `Ask about ${doc.title}…` : "Ask anything: the agent searches every document…";
}

function currentSamples() {
  const key = currentConfig()?.document?.key || "benchmark";
  return S.status?.samples?.[key] || [];
}

function renderSamples() {
  const q = $("sample-filter").value.trim().toLowerCase();
  const all = currentSamples();
  const rows = all.filter((s) => !q || s.id.toLowerCase().includes(q) || s.question.toLowerCase().includes(q));
  const list = $("samples");
  if (!rows.length) return list.replaceChildren(el("li", { class: "sample-empty", text: all.length ? "No sample matches the filter." : "No sample questions for this document." }));
  list.replaceChildren(...rows.map((s) => el("li", {}, el("button", {
    type: "button", title: "Ask this question",
    onclick: () => { $("question").value = s.question; autosize(); if (NARROW_SIDEBAR.matches) closeDrawer("sidebar"); canSend() ? submit() : $("question").focus(); },
  }, el("span", { class: "sid", text: s.id }), el("span", { text: s.question })))));
}

function renderTopbar() {
  const c = currentConfig();
  $("topbar-config").textContent = S.config ? modeLabel(S.config) : "—";
  $("topbar-sub").textContent = c ? `${c.model} · ${c.method} · top_k ${c.top_k}` : "server unavailable";
  const pill = $("topbar-state");
  const w = c?.warm?.state;
  let kind = "bad", text = "Not ready", busy = false;
  if (S.pending) [kind, text, busy] = ["warn", "Agent running", true];
  else if (!S.status) text = "Offline";
  else if (!S.status.store || !S.status.api_key) text = "Setup needed";
  else if (w === "ready") [kind, text] = ["ok", "Ready"];
  else if (w === "loading" || w === "cold") [kind, text, busy] = ["warn", "Loading models", true];
  else text = "Models failed";
  pill.className = `pill ${kind}${busy ? " busy" : ""}`;
  pill.replaceChildren(el("span", { class: "dot", "aria-hidden": "true" }), text);
}

/* ---------- composer ---------- */
function canSend() {
  return !S.pending && !!S.status?.store && !!S.status?.api_key && $("question").value.trim().length > 0;
}

function updateSend() {
  $("send").disabled = !canSend();
  $("clear").disabled = S.pending;
  const n = $("question").value.length;
  const counter = $("counter");
  counter.textContent = `${n} / 2000`;
  counter.classList.toggle("near", n > 1800);
}

function autosize() {
  const t = $("question");
  t.style.height = "auto";
  t.style.height = `${Math.min(t.scrollHeight, 200)}px`;
  updateSend();
}

async function submit(question) {
  question = (question ?? $("question").value).trim();
  if (!question || S.pending) return;
  const turn = { id: ++S.seq, question, config: S.config, started: new Date(), trace: null, node: null };
  S.turns.push(turn);
  S.pending = true;
  $("question").value = "";
  autosize();
  $("empty").hidden = true;
  drawTurn(turn);
  renderTopbar();
  const timer = setInterval(() => {
    const e = turn.node?.querySelector("[data-elapsed]");
    if (e) e.textContent = `${Math.round((Date.now() - turn.started) / 1000)} s`;
  }, 1000);
  try {
    turn.trace = await api("/api/ask", { question, config: turn.config });
  } catch (e) {
    const msg = e.status ? `Server rejected the request: ${e.message}` : "Lost connection to the UI server. Is python app/server.py still running?";
    turn.trace = { status: "error", reason: e.status ? `http_${e.status}` : "network", answer: "", citations: [], events: [], errors: [e.message],
      tool_calls: 0, llm_calls: 0, tokens: { total: 0 }, latency_s: (Date.now() - turn.started) / 1000, final_context: [], context_ids: [],
      ui: { error_message: msg, citations: [] } };
  } finally {
    clearInterval(timer);
    S.pending = false;
  }
  drawTurn(turn);
  select(turn, { tab: turn.trace.status === "answered" ? "sources" : "timeline", open: false });
  turn.node.scrollIntoView({ block: "nearest" });
  loadStatus();
  $("question").focus();
}

/* ---------- thread ---------- */
function statusBadge(status) {
  const s = STATUS[status] || STATUS.error;
  return el("span", { class: `status ${STATUS[status] ? status : "error"}` }, icon(s.icon), s.label);
}

function metric(ico, value, label) {
  return el("span", { title: label }, icon(ico), el("b", { text: value }), el("span", { class: "sr-only", text: ` ${label}` }));
}

function drawTurn(turn) {
  const node = el("article", { class: "turn", "aria-label": `Question ${turn.id}` },
    el("div", { class: "q", text: turn.question }),
    el("div", { class: "q-meta", text: `${turn.config} · ${fmt.time(turn.started)}` }),
    turn.trace ? answerCard(turn) : pendingCard());
  if (turn.node) turn.node.replaceWith(node);
  else $("thread").append(node);
  turn.node = node;
  if (S.selected === turn) node.querySelector(".a")?.classList.add("selected");
  node.scrollIntoView({ block: "end" });
}

function pendingCard() {
  return el("div", { class: "a" },
    el("div", { class: "a-head" }, statusBadge("pending"), el("span", { class: "reason", text: "searching · reading · answering" }),
      el("div", { class: "metrics" }, el("span", {}, icon("clock"), el("b", { "data-elapsed": true, text: "0 s" })))),
    el("div", { class: "a-body" },
      el("div", { class: "pending-body" }, el("span", { class: "spinner", "aria-hidden": "true" }), "The agent is calling tools. Free-tier calls are paced, so this can take 10–40 s."),
      el("div", { class: "skeleton", "aria-hidden": "true" }, el("span"), el("span"), el("span"))));
}

function answerCard(turn) {
  const t = turn.trace;
  const invalid = (t.ui?.citations || []).filter((c) => !c.valid);
  const finish = [...(t.events || [])].reverse().find((e) => e.event === "finish_call");
  const card = el("div", { class: "a", onclick: (ev) => { if (!ev.target.closest("button")) select(turn); } },
    el("div", { class: "a-head" },
      statusBadge(t.status),
      t.reason && el("span", { class: "reason", text: t.reason }),
      el("div", { class: "metrics" },
        metric("tool", fmt.n(t.tool_calls), "tool calls"),
        metric("chat", fmt.n(t.llm_calls), "LLM calls"),
        metric("clock", fmt.s(t.latency_s), "latency"),
        metric("hash", fmt.n(t.tokens?.total), "tokens"))),
    el("div", { class: "a-body" },
      t.ui?.error_message && el("div", { class: "alert bad" }, icon("alert"), el("span", { text: t.ui.error_message })),
      t.answer && el("div", { class: `answer${t.status === "answered" ? "" : " dim"}` }, answerNodes(t, turn)),
      t.status === "answered" && finish?.evidence_quote && el("div", { class: "quote" }, el("span", { class: "quote-label", text: "Evidence quote" }), String(finish.evidence_quote)),
      invalid.length > 0 && el("div", { class: "alert bad" }, icon("warn"), el("span", { text: `Invalid citations (not in final context): ${invalid.map((c) => c.id).join(", ")}` }))),
    el("div", { class: "a-foot" },
      el("button", { class: "btn ghost small", type: "button", onclick: () => select(turn, { open: true }) }, icon("doc"), "Inspect trace"),
      t.status === "error" && el("button", { class: "btn ghost small", type: "button", disabled: S.pending || null, onclick: () => submit(turn.question) }, icon("retry"), "Retry"),
      t._saved && el("span", { class: "saved", text: `saved ${t._saved}` }),
      t._save_error && el("span", { class: "saved", text: `trace not saved: ${t._save_error}` })));
  return card;
}

/** Answer text with [id] groups turned into citation chips; unknown bracket text stays literal. */
function answerNodes(t, turn) {
  const ctx = new Set(t.context_ids || []);
  const cited = new Set(t.citations || []);
  const out = [];
  let last = 0;
  for (const m of t.answer.matchAll(/\[([^[\]]+)\]/g)) {
    out.push(t.answer.slice(last, m.index));
    last = m.index + m[0].length;
    const tokens = m[1].split(/[,;\s]+/).filter(Boolean);
    if (!tokens.some((x) => ctx.has(x) || cited.has(x))) { out.push(m[0]); continue; }
    tokens.forEach((x) => {
      if (!(ctx.has(x) || cited.has(x))) return out.push(` ${x} `);
      const valid = ctx.has(x);
      out.push(el("button", {
        type: "button", class: `cite${valid ? "" : " invalid"}`, title: valid ? `${x}: open source` : `${x}: not in the final context`,
        "aria-label": `Citation ${x}${valid ? "" : ", invalid"}`,
        onclick: () => select(turn, { tab: valid ? "sources" : "context", focus: x, open: true }),
      }, shortId(x)));
    });
  }
  out.push(t.answer.slice(last));
  return out;
}

/* ---------- inspector ---------- */
function select(turn, { tab, focus, open } = {}) {
  S.selected = turn;
  if (tab) S.tab = tab;
  document.querySelectorAll(".a.selected").forEach((n) => n.classList.remove("selected"));
  turn.node?.querySelector(".a")?.classList.add("selected");
  renderInspector();
  if (open && NARROW_INSPECTOR.matches) openDrawer("inspector");
  if (focus) {
    const target = [...$("tabpanel").querySelectorAll("[data-chunk]")].find((n) => n.dataset.chunk === focus);
    if (target) {
      if (target.tagName === "DETAILS") target.open = true;
      target.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      target.classList.remove("flash");
      void target.offsetWidth;
      target.classList.add("flash");
    }
  }
}

function renderInspector() {
  const turn = S.selected;
  const t = turn?.trace;
  const counts = t ? {
    sources: (t.ui?.citations || []).length,
    timeline: (t.events || []).filter((e) => e.event === "search" || e.event === "tool_error").length,
    context: (t.final_context || []).length,
    tokens: t.llm_calls || 0,
  } : {};
  for (const btn of $("tabs").querySelectorAll("[role=tab]")) {
    const name = btn.dataset.tab;
    const on = name === S.tab;
    btn.setAttribute("aria-selected", String(on));
    btn.tabIndex = on ? 0 : -1;
    const label = { sources: "Sources", timeline: "Timeline", context: "Context", tokens: "Tokens", raw: "Raw" }[name];
    btn.replaceChildren(...[label, counts[name] != null && el("span", { class: "count", text: counts[name] })].filter(Boolean));
  }
  $("tabpanel").setAttribute("aria-labelledby", `tab-${S.tab}`);
  $("inspector-q").textContent = turn ? turn.question : "Select an answer to inspect it.";
  const panel = $("tabpanel");
  panel.scrollTop = 0;
  if (!t) return panel.replaceChildren(el("p", { class: "placeholder", text: turn ? "Waiting for the agent…" : "Answers you ask appear here with their sources, tool calls, context and token usage." }));
  panel.replaceChildren(...{ sources: sourcesTab, timeline: timelineTab, context: contextTab, tokens: tokensTab, raw: rawTab }[S.tab](t, turn));
}

function chunkTags(c, extra) {
  return [
    c.document && el("span", { class: "tag doc", title: "document", text: c.document }),
    c.page != null && el("span", { class: "tag", text: `p.${c.page}` }),
    c.chapter != null && el("span", { class: "tag", text: `ch ${c.chapter}` }),
    c.score != null && el("span", { class: "tag", title: "retrieval score", text: fmt.score(c.score) }),
    c.origin && el("span", { class: "tag", text: c.origin }),
    extra,
  ];
}

function sourcesTab(t) {
  const rows = t.ui?.citations || [];
  const finish = [...(t.events || [])].reverse().find((e) => e.event === "finish_call");
  const out = [];
  if (finish?.evidence_quote && t.status === "answered") out.push(el("div", { class: "quote" }, el("span", { class: "quote-label", text: "Evidence quote given by the model" }), String(finish.evidence_quote)));
  if (!rows.length) {
    out.push(el("p", { class: "placeholder", text: t.status === "abstain" ? "No citations: the agent abstained. See Timeline and Context for what it read." : "No citations in this answer." }));
    return out;
  }
  for (const r of rows) {
    if (!r.valid) {
      out.push(el("div", { class: "src invalid", "data-chunk": r.id }, el("div", { class: "src-head" }, el("span", { class: "src-id", text: r.id }), el("span", { class: "tag bad", text: "not in final context" }))));
      continue;
    }
    const c = r.chunk;
    out.push(el("div", { class: "src", "data-chunk": c.id },
      el("div", { class: "src-head" }, el("span", { class: "src-id", text: c.id }), chunkTags(c)),
      c.section && el("div", { class: "src-section", text: c.section }),
      el("pre", { class: "src-text", text: c.text || "" })));
  }
  return out;
}

function step(dotKind, dotText, title, ...body) {
  return el("div", { class: "step" }, el("span", { class: `step-dot ${dotKind}`, "aria-hidden": "true", text: dotText }), el("div", { class: "step-title" }, title), body);
}

function timelineTab(t) {
  const out = [];
  const docOf = Object.fromEntries((t.final_context || []).filter((c) => c.document).map((c) => [c.id, c.document]));
  if (t.errors?.length) out.push(el("div", { class: "alert bad" }, icon("alert"), el("ul", { class: "errors" }, t.errors.map((e) => el("li", { text: e })))));
  for (const ev of t.events || []) {
    if (ev.event === "model_call") {
      out.push(step("", ev.n, [el("b", { text: `LLM call ${ev.n}` }), el("span", { class: "step-meta", text: `${fmt.s(ev.latency_s)} · ${fmt.n(ev.usage?.total)} tok${ev.retries ? ` · ${ev.retries} retries` : ""}` })],
        el("div", { class: "step-note", text: ev.function_calls?.length ? `calls: ${ev.function_calls.join(", ")}` : "no function call" }),
        ev.text && el("div", { class: "step-query", text: ev.text })));
    } else if (ev.event === "search") {
      const added = new Set(ev.context_added || []), dup = new Set(ev.duplicates || []), dropped = new Set(ev.budget_dropped || []);
      const filter = ev.filter?.chapter ? `chapter ${ev.filter.chapter}` : null;
      out.push(step(ev.ok ? "ok" : "bad", ev.ok ? "✓" : "!", [el("b", { text: ev.tool }), el("span", { class: "step-meta", text: [ev.method, ev.top_k && `k=${ev.top_k}`, fmt.s(ev.latency_s)].filter(Boolean).join(" · ") })],
        el("div", { class: "step-query", text: ev.query }),
        filter && el("div", { class: "step-note" }, el("span", { class: "tag", text: filter }), " ", ev.filter_reason || ""),
        ev.error && el("div", { class: "alert bad" }, icon("alert"), el("span", { text: ev.error })),
        (ev.results || []).length > 0 && el("ul", { class: "hits" }, ev.results.map((h) => el("li", { title: docOf[h.id] ? `${h.id} — ${docOf[h.id]}` : h.id },
          el("span", { class: "rank", text: `#${h.rank}` }), el("span", { class: "hid", text: h.id }),
          el("span", { class: "score", text: fmt.score(h.score) }),
          added.has(h.id) ? el("span", { class: "tag ok", text: "added" }) : dup.has(h.id) ? el("span", { class: "tag", text: "seen" })
            : dropped.has(h.id) ? el("span", { class: "tag warn", text: "over budget" }) : el("span"))))));
    } else if (ev.event === "citation_check_failed") {
      out.push(step("warn", "!", el("b", { text: "Citation check failed" }), el("div", { class: "step-note", text: ev.problem })));
    } else if (ev.event === "finish_call") {
      out.push(step(ev.abstain ? "warn" : "ok", "■", [el("b", { text: "finish" }), el("span", { class: "step-meta", text: ev.abstain ? "abstain=true" : `${(ev.citations || []).length} citations` })],
        ev.answer && el("div", { class: "step-query", text: ev.answer })));
    } else if (ev.event === "tool_error") {
      out.push(step("bad", "!", el("b", { text: `tool error: ${ev.tool}` }), el("div", { class: "step-note", text: ev.error })));
    }
  }
  if (!out.length) out.push(el("p", { class: "placeholder", text: "No events were recorded." }));
  return out;
}

function contextTab(t, turn) {
  const budget = S.status?.configs?.[turn.config]?.context_budget_chars;
  const cited = new Set(t.citations || []);
  const pct = budget ? Math.min(100, Math.round((100 * (t.context_chars || 0)) / budget)) : 0;
  const fill = el("span");
  fill.style.width = `${pct}%`;  // CSSOM, not a style attribute: the page CSP has no 'unsafe-inline'
  const out = [el("div", { class: "meter" },
    el("div", { class: "meter-row" }, el("span", { text: "Context used" }), el("b", { text: `${fmt.n(t.context_chars)} / ${fmt.n(budget)} chars` })),
    el("div", { class: "bar", role: "progressbar", "aria-label": "Context budget used", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": pct }, fill))];
  const chunks = t.final_context || [];
  if (!chunks.length) out.push(el("p", { class: "placeholder", text: "No chunks were admitted into the context." }));
  for (const c of chunks) {
    out.push(el("details", { class: "src", "data-chunk": c.id },
      el("summary", {}, el("div", { class: "src-head" }, el("span", { class: "src-id", text: c.id }), chunkTags(c, cited.has(c.id) && el("span", { class: "tag ok", text: "cited" })), el("span", { class: "chev" }, icon("chevron")))),
      c.section && el("div", { class: "src-section", text: c.section }),
      el("pre", { class: "src-text", text: c.text || "" })));
  }
  return out;
}

function tokensTab(t) {
  const tok = t.tokens || {};
  const stat = (k, v) => el("div", { class: "stat" }, el("div", { class: "k", text: k }), el("div", { class: "v", text: v }));
  const calls = (t.events || []).filter((e) => e.event === "model_call");
  return [
    el("div", { class: "stats" }, stat("Total tokens", fmt.n(tok.total)), stat("Latency", fmt.s(t.latency_s)), stat("Prompt", fmt.n(tok.prompt)),
      stat("Output", fmt.n(tok.output)), stat("Thinking", fmt.n(tok.thoughts)), stat("LLM / tool calls", `${fmt.n(t.llm_calls)} / ${fmt.n(t.tool_calls)}`)),
    calls.length ? el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, ["#", "latency", "retries", "prompt", "output", "thoughts", "total", "calls"].map((h) => el("th", { scope: "col", text: h })))),
      el("tbody", {}, calls.map((e) => el("tr", {}, [e.n, fmt.s(e.latency_s), e.retries, fmt.n(e.usage?.prompt), fmt.n(e.usage?.output), fmt.n(e.usage?.thoughts), fmt.n(e.usage?.total), (e.function_calls || []).join(", ") || "—"].map((v) => el("td", { text: v })))))))
      : el("p", { class: "placeholder", text: "No model calls were made." }),
  ];
}

function rawTab(t) {
  const { ui, ...trace } = t;
  const json = JSON.stringify(trace, null, 1);
  const btn = el("button", { class: "btn ghost small", type: "button", onclick: async () => {
    try { await navigator.clipboard.writeText(json); btn.lastChild.textContent = "Copied"; } catch (_) { btn.lastChild.textContent = "Copy failed"; }
    setTimeout(() => { btn.lastChild.textContent = "Copy JSON"; }, 1500);
  } }, icon("copy"), el("span", { text: "Copy JSON" }));
  return [el("div", { class: "raw-tools" }, btn, t._saved && el("span", { class: "saved", text: t._saved })), el("pre", { class: "raw", text: json })];
}

/* ---------- drawers ---------- */
let lastFocus = null;
function openDrawer(id) {
  lastFocus = document.activeElement;
  $(id).classList.add("open");
  $("scrim").hidden = false;
  $(id === "sidebar" ? "open-sidebar" : "open-inspector").setAttribute("aria-expanded", "true");
  $(id).querySelector(".drawer-close")?.focus();
}
function closeDrawer(id) {
  const d = $(id);
  if (!d.classList.contains("open")) return;
  d.classList.remove("open");
  $(id === "sidebar" ? "open-sidebar" : "open-inspector").setAttribute("aria-expanded", "false");
  if (!document.querySelector(".drawer.open")) $("scrim").hidden = true;
  if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
}

/* ---------- wiring ---------- */
function init() {
  document.querySelectorAll("[data-icon]").forEach((n) => n.prepend(icon(n.dataset.icon)));
  const q = $("question");
  q.addEventListener("input", autosize);
  q.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); if (canSend()) submit(); }
  });
  $("composer").addEventListener("submit", (e) => { e.preventDefault(); if (canSend()) submit(); });
  $("config").addEventListener("change", (e) => {
    S.config = e.target.value;
    store("rag-tester-mode", S.config);
    renderConfigDetails(); renderHealth(); renderTopbar(); renderDocument(); renderSamples();
    api("/api/warm", { config: S.config }).then(loadStatus).catch(loadStatus);
  });
  $("sample-filter").addEventListener("input", renderSamples);
  $("clear").addEventListener("click", () => {
    if (S.pending) return;
    S.turns = []; S.selected = null;
    $("thread").replaceChildren($("empty"));
    $("empty").hidden = false;
    renderInspector();
  });
  $("tabs").addEventListener("click", (e) => {
    const b = e.target.closest("[role=tab]");
    if (b) { S.tab = b.dataset.tab; renderInspector(); }
  });
  $("tabs").addEventListener("keydown", (e) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
    e.preventDefault();
    const i = TABS.indexOf(S.tab);
    S.tab = TABS[e.key === "Home" ? 0 : e.key === "End" ? TABS.length - 1 : (i + (e.key === "ArrowRight" ? 1 : TABS.length - 1)) % TABS.length];
    renderInspector();
    $(`tab-${S.tab}`).focus();
  });
  $("open-sidebar").addEventListener("click", () => openDrawer("sidebar"));
  $("open-inspector").addEventListener("click", () => openDrawer("inspector"));
  document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => closeDrawer(b.dataset.close)));
  $("scrim").addEventListener("click", () => { closeDrawer("sidebar"); closeDrawer("inspector"); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeDrawer("sidebar"); closeDrawer("inspector"); } });
  NARROW_INSPECTOR.addEventListener("change", () => closeDrawer("inspector"));
  NARROW_SIDEBAR.addEventListener("change", () => closeDrawer("sidebar"));
  renderInspector();
  autosize();
  loadStatus();
}

document.addEventListener("DOMContentLoaded", init);
