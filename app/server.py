"""Local web UI for the Day 7 agentic RAG agent (Python stdlib only, no extra dependencies).

Run:  python app/server.py [--port 8000]   then open http://127.0.0.1:8000  (see README "Test UI").

Reuses src/agent.py: every question goes through A.run_query with a GeminiClient, the same code path as
scripts/run_agent.py; there is no retrieval logic here. Sample questions come from benchmark/questions.json
(id/question; gold is never read) or, for your own PDFs, from the "examples" in their collection.json. The API key is never sent to the browser or
logged. Chunk text and model output are untrusted: the page renders them with textContent only.
Each interaction trace is saved to results/ui/<timestamp>.json (git-ignored).
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import agent as A  # noqa: E402
from src import day6_store as d6  # noqa: E402
from src import local_docs as LD  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
CONFIG_DIR = ROOT / "configs"
QUESTIONS = ROOT / "benchmark" / "questions.json"
UI_OUT = ROOT / "results" / "ui"
MAX_BODY = 16_384
MAX_QUESTION = 2000
CONFIG_FIELDS = ("model", "method", "top_k", "context_budget_chars", "max_tool_calls", "collection",
                 "reranker", "prompt_version", "neighbors", "allow_chapter_filter")
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                 ".js": "text/javascript; charset=utf-8", ".svg": "image/svg+xml"}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


# --- configs, samples, trace helpers ---------------------------------------------------------------
# Default mode: one search over every document (scripts/build_library.py). Not a file in configs/: nothing here says which
# document to look in; the hybrid cosine + BM25 search over the whole library decides. No chapter filter (chapters are
# per document), hybrid without reranker (the available cross-encoder is English-only).
LIBRARY_SETTINGS = {
    "collection": LD.LIBRARY, "method": "hybrid", "top_k": 5, "depth": 20, "fuse_depth": 20, "rrf_k": 60,
    "demote_backmatter": False, "max_tool_calls": 3, "context_budget_chars": 10000, "neighbors": True,
    "allow_chapter_filter": False, "thinking_budget": 2048, "lenient_citation_format": True,
}


def library_available() -> bool:
    return LD.is_library(LD.LIBRARY)


def list_configs() -> list[str]:
    """'library' first (when built), then the benchmark configs in configs/ (each searches one fixed collection)."""
    files = sorted(p.stem for p in CONFIG_DIR.glob("*.json") if p.stem != LD.LIBRARY)
    return ([LD.LIBRARY] if library_available() else []) + files


def load_config(name: str) -> dict:
    """Merged run config: the built-in library mode, or configs/<name>.json. Unknown names are rejected."""
    if name not in list_configs():
        raise KeyError(f"unknown config: {name!r}")
    if name == LD.LIBRARY:
        return {**A.DEFAULT_CONFIG, **LIBRARY_SETTINGS, "name": name}
    raw = json.loads((CONFIG_DIR / f"{name}.json").read_text(encoding="utf-8"))
    cfg = dict(raw.get("config", raw))
    cfg["name"] = name
    return {**A.DEFAULT_CONFIG, **cfg}


TEXTBOOK = {"title": "Introduction to Sociology 3e", "subtitle": "ch. 5–7", "samples_source": "benchmark/questions.json"}


def load_samples() -> list[dict]:
    """id/question only, from benchmark/questions.json (no gold)."""
    try:
        rows = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [{"id": r["id"], "question": r["question"]} for r in rows]


def document_info(cfg: dict) -> dict:
    """What the config answers from, for the page: title, subtitle, where its sample questions come from."""
    m = LD.manifest(cfg.get("collection"))
    if m is None:
        return {**TEXTBOOK, "key": "benchmark"}
    if m.get("kind") == "library":  # shown to you, never to the model
        docs = m.get("documents", [])
        return {"key": f"doc:{m['name']}", "title": "All documents", "library": True,
                "subtitle": f"{len(docs)} documents, {m.get('chunks', 0)} chunks in one index",
                "documents": [{"title": d["title"], "chunks": d["chunks"]} for d in docs],
                "samples_source": "benchmark + document examples"}
    return {"key": f"doc:{m['name']}", "title": m["title"], "subtitle": m.get("description", ""),
            "samples_source": f"data/local_docs/{m['name']}/collection.json (examples)", "language": m.get("language")}


def all_samples(configs: dict) -> dict[str, list[dict]]:
    out = {"benchmark": load_samples()}
    for c in configs.values():
        key = c["document"]["key"]
        if key.startswith("doc:") and key not in out:
            m = LD.manifest(key[4:]) or {}
            out[key] = [{"id": e.get("id") or f"ex{i + 1}", "question": e["question"]}
                        for i, e in enumerate(m.get("examples", [])) if isinstance(e, dict) and e.get("question")]
            if m.get("kind") == "library" and m.get("include_textbook", True):
                out[key] += out["benchmark"]
    return out


def classify_error(trace: dict) -> str | None:
    """Friendly message for an error trace, or None."""
    if trace.get("status") != "error":
        return None
    text = " ".join(trace.get("errors") or []) + " " + str(trace.get("reason"))
    low = text.lower()
    if "429" in low or "quota" in low or "resource_exhausted" in low:
        return "Gemini quota / rate limit hit (429). No answer was produced; wait and retry. Details: " + text[:400]
    if "gemini_api_key" in low:
        return "GEMINI_API_KEY is missing. Add GEMINI_API_KEY=... to .env in the repo root and restart the server."
    if trace.get("reason") == "resources":
        return "Could not load retrieval resources. If the vector store is missing or stale, run " \
               "`python scripts/build_index.py`. Details: " + text[:400]
    return "The agent failed: " + text[:400]


def citation_rows(trace: dict) -> list[dict]:
    """Each cited id with its context chunk (chunk None -> invalid, not in the final context)."""
    ctx = {c["id"]: c for c in trace.get("final_context", [])}
    return [{"id": cid, "valid": cid in ctx, "chunk": ctx.get(cid)} for cid in trace.get("citations", [])]


def save_trace(trace: dict) -> Path:
    UI_OUT.mkdir(parents=True, exist_ok=True)
    p = UI_OUT / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".json")
    p.write_text(json.dumps(trace, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return p


def error_trace(qid: str, question: str, cfg: dict, reason: str, error: str) -> dict:
    """Trace with the same shape as A.run_query's, for failures before the agent runs."""
    return {"query_id": qid, "question": question, "status": "error", "reason": reason, "answer": "",
            "citations": [], "events": [], "errors": [error], "tool_calls": 0, "llm_calls": 0,
            "tokens": {"prompt": 0, "output": 0, "thoughts": 0, "total": 0}, "latency_s": 0.0,
            "context_ids": [], "context_chars": 0, "final_context": [], "config_name": cfg["name"], "model": cfg["model"]}


# --- resources (embedding model, Chroma, BM25, cross-encoder) --------------------------------------
_warm: dict[str, dict] = {}
_load_lock = threading.Lock()   # serializes model loading
_ask_lock = threading.Lock()    # one agent run at a time (free-tier pacing is per client anyway)
_clients: dict[str, A.GeminiClient] = {}


def warm_key(cfg: dict) -> str:
    return f"{cfg['collection']}|{cfg['reranker'] if 'rerank' in cfg['method'] else ''}"


def warm_state(cfg: dict) -> dict:
    return _warm.get(warm_key(cfg), {"state": "cold", "error": None})


def warm_resources(cfg: dict) -> dict:
    """Load and keep (in the modules' own caches) everything retrieval needs for cfg. Blocking, thread-safe."""
    key = warm_key(cfg)
    with _load_lock:
        if _warm.get(key, {}).get("state") == "ready":
            return _warm[key]
        _warm[key] = {"state": "loading", "error": None}
        try:
            from src import retrievers as R
            d6.get_collection(cfg["collection"])
            d6.embed_query("warm up", cfg["collection"])
            R._bm25(cfg["collection"])
            reranker = key.split("|", 1)[1]
            if reranker and reranker not in R._rerankers:
                from sentence_transformers import CrossEncoder
                R._rerankers[reranker] = CrossEncoder(reranker, device="cpu")
            _warm[key] = {"state": "ready", "error": None}
        except Exception as e:  # reported to the page; a later call retries
            _warm[key] = {"state": "error", "error": f"{type(e).__name__}: {str(e)[:300]}"}
        return _warm[key]


def warm_in_background(cfg: dict) -> None:
    if warm_state(cfg)["state"] in ("cold", "error"):
        _warm[warm_key(cfg)] = {"state": "loading", "error": None}
        threading.Thread(target=warm_resources, args=(cfg,), daemon=True).start()


def get_client(cfg: dict) -> A.GeminiClient:
    key = json.dumps(cfg, sort_keys=True, default=str)
    if key not in _clients:
        _clients[key] = A.GeminiClient(cfg)
    return _clients[key]


def store_info() -> tuple[str | None, str | None]:
    try:
        return str(d6.store_path()), None
    except Exception as e:
        return None, str(e)


def ask(question: str, cfg_name: str) -> dict:
    """Run one question; never raises. Returns the trace plus a `ui` block for the page."""
    cfg = load_config(cfg_name)
    qid = "ui-" + datetime.now().strftime("%H%M%S")
    warm = warm_resources(cfg)
    if warm["state"] != "ready":
        trace = error_trace(qid, question, cfg, "resources", warm["error"] or "resources not loaded")
    else:
        with _ask_lock:
            try:
                client = get_client(cfg)
            except Exception as e:  # e.g. missing key; the message carries no secret
                trace = error_trace(qid, question, cfg, "client_init", f"{type(e).__name__}: {str(e)[:300]}")
            else:
                trace = A.run_query(qid, question, cfg, client)
    trace["ui_config"] = cfg_name
    trace["vectorstore"] = store_info()[0]
    trace["timestamp"] = datetime.now().isoformat(timespec="seconds")
    try:
        trace["_saved"] = str(save_trace(trace).relative_to(ROOT))
    except Exception as e:
        trace["_save_error"] = f"{type(e).__name__}: {e}"
    trace["ui"] = {"error_message": classify_error(trace), "citations": citation_rows(trace)}
    return trace


def status() -> dict:
    names = list_configs()
    store, store_err = store_info()
    try:
        A.load_api_key()
        key_ok = True
    except Exception:
        key_ok = False
    configs = {}
    for n in names:
        try:
            cfg = load_config(n)
        except Exception:
            continue
        configs[n] = {**{k: cfg.get(k) for k in CONFIG_FIELDS}, "warm": warm_state(cfg), "document": document_info(cfg)}
    try:
        store_display = Path(store).relative_to(ROOT).as_posix() + "/" if store else None
    except ValueError:
        store_display = store
    default = next((n for n in (LD.LIBRARY, "final") if n in configs), next(iter(configs), None))
    return {"configs": configs, "default": default,
            "store": store, "store_display": store_display, "store_error": store_err, "api_key": key_ok, "busy": _ask_lock.locked(),
            "samples": all_samples(configs)}


# --- HTTP ------------------------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "RAGTester/1.0"
    allowed_hosts: frozenset[str] = frozenset({"127.0.0.1", "localhost", "[::1]"})

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8")

    def _host_ok(self) -> bool:
        """Reject foreign Host headers (DNS rebinding) since the server holds an API key."""
        if "*" in self.allowed_hosts:
            return True
        host = self.headers.get("Host") or ""
        name = host.split("]")[0] + "]" if host.startswith("[") else host.split(":")[0]
        return name in self.allowed_hosts

    def _static(self, rel: str) -> None:
        base = STATIC.resolve()
        p = (base / rel).resolve()
        ctype = CONTENT_TYPES.get(p.suffix)
        if base not in p.parents or not p.is_file() or ctype is None:
            return self._json(404, {"error": "not found"})
        self._send(200, p.read_bytes(), ctype)

    def _body(self) -> dict | None:
        if (self.headers.get("Content-Type") or "").split(";")[0].strip() != "application/json":
            self._json(415, {"error": "Content-Type must be application/json"})
            return None
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n <= 0 or n > MAX_BODY:
            self._json(413 if n > MAX_BODY else 400, {"error": "bad request body size"})
            return None
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"error": "invalid JSON"})
            return None
        if not isinstance(body, dict):
            self._json(400, {"error": "JSON object expected"})
            return None
        return body

    def do_GET(self):  # noqa: N802
        if not self._host_ok():
            return self._json(403, {"error": "forbidden host"})
        path = urlsplit(self.path).path
        if path == "/api/status":
            return self._json(200, status())
        if path in ("/", "/index.html"):
            return self._static("index.html")
        if path.startswith("/static/"):
            return self._static(path[len("/static/"):])
        self._json(404, {"error": "not found"})

    def do_POST(self):  # noqa: N802
        if not self._host_ok():
            return self._json(403, {"error": "forbidden host"})
        path = urlsplit(self.path).path
        if path not in ("/api/ask", "/api/warm"):
            return self._json(404, {"error": "not found"})
        body = self._body()
        if body is None:
            return
        name = body.get("config")
        if not isinstance(name, str) or name not in list_configs():
            return self._json(400, {"error": "unknown config"})
        if path == "/api/warm":
            warm_in_background(load_config(name))
            return self._json(202, {"warm": warm_state(load_config(name))})
        question = body.get("question")
        question = question.strip() if isinstance(question, str) else ""
        if not question or len(question) > MAX_QUESTION:
            return self._json(400, {"error": f"question must be 1-{MAX_QUESTION} characters"})
        self._json(200, ask(question, name))

    def log_message(self, fmt, *args):  # quieter than the default; never logs bodies
        if "/api/status" not in (args[0] if args else ""):
            sys.stderr.write(f"[ui] {self.address_string()} {fmt % args}\n")


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    extra = {"*"} if host in ("0.0.0.0", "::") else {host, f"[{host}]"}  # wildcard bind: explicit opt-in to exposure
    handler = type("BoundHandler", (Handler,), {"allowed_hosts": Handler.allowed_hosts | extra})
    srv = ThreadingHTTPServer((host, port), handler)
    srv.daemon_threads = True
    return srv


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Local web UI for the Day 7 RAG agent")
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default: loopback only)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-warm", action="store_true", help="do not preload models at startup")
    args = ap.parse_args(argv)
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"WARNING: binding to {args.host} exposes an agent that spends your Gemini quota.", file=sys.stderr)
    srv = make_server(args.host, args.port)
    st = status()
    if st["default"] and not args.no_warm and st["store"]:
        warm_in_background(load_config(st["default"]))
    print(f"RAG Agent Tester on http://{'localhost' if args.host == '127.0.0.1' else args.host}:{srv.server_address[1]}"
          "  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
