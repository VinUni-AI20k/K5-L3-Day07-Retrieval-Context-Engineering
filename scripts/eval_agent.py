"""Agent evaluator (reads benchmark/gold/gold.json; the agent code never does).

Usage: python scripts/eval_agent.py --split dev --configs base,rerank [--out results/agent/dev]
 * writes results/agent/<split>/cases.json (id, split, answerable)
 * context metrics from traces + gold: context evidence rate (final context has the required evidence; 'all' mode for
   multi-hop), retrieved-evidence rate (gold anywhere in search results)
 * if results/agent/<split>/<config>/reviews.json exists: runs starter/agent_metrics.aggregate on it
 * writes results/agent/<split>/<config>/summary.json and results/agent/<split>/comparison.md
Refuses split=test unless --allow-test.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "starter"))
from agent_metrics import aggregate  # noqa: E402


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))] if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--configs", required=True)
    ap.add_argument("--allow-test", action="store_true")
    a = ap.parse_args()
    if a.split == "test" and not a.allow_test:
        sys.exit("test split needs --allow-test")
    base = ROOT / "results" / "agent" / a.split
    gold = {g["id"]: g for g in json.loads((ROOT / "benchmark/gold/gold.json").read_text(encoding="utf-8")) if g["split"] == a.split}
    cases = [{"id": i, "split": a.split, "answerable": g["answerable"], "type": g["type"]} for i, g in gold.items()]
    base.mkdir(parents=True, exist_ok=True)
    (base / "cases.json").write_text(json.dumps(cases, indent=1) + "\n", encoding="utf-8")
    rows = []
    for name in a.configs.split(","):
        d = base / name
        traces = json.loads((d / "traces.json").read_text(encoding="utf-8"))
        tb = {t["query_id"]: t for t in traces}
        ctx_ok, ret_ok, per = 0, 0, {}
        N = 0
        for i, g in gold.items():
            if not g["answerable"] or i not in tb or tb[i]["status"] == "error":
                continue
            need = [e["chunk_id"] for e in g["evidence"]]
            mode = g["evidence_mode"]
            t = tb[i]
            retrieved = {r["id"] for e in t["events"] if e.get("event") == "search" for r in e.get("results", [])}
            f = (all if mode == "all" else any)
            c = f(n in t["context_ids"] for n in need)
            r = f(n in retrieved for n in need)
            N += 1
            ctx_ok += c
            ret_ok += r
            per[i] = {"context": c, "retrieved": r}
        ok = [t for t in traces if t["status"] != "error"]
        lat = [t["latency_s"] for t in ok]  # wall clock incl. client-side pacing sleeps (6.5 s between LLM calls)
        act = [sum(e.get("latency_s", 0) for e in t["events"] if e["event"] in ("model_call", "search")) for t in ok]  # LLM + tool time only
        tools = [t["tool_calls"] for t in ok]
        s = {"config": name, "queries": len(traces), "errors": sum(t["status"] == "error" for t in traces),
             "answered": sum(t["status"] == "answered" for t in traces), "abstain": sum(t["status"] == "abstain" for t in traces),
             "context_evidence": {"n": ctx_ok, "N": N}, "retrieved_evidence": {"n": ret_ok, "N": N}, "per_query": per,
             "tool_calls_mean": round(statistics.mean(tools), 2) if tools else None,
             "tool_calls_dist": {str(k): tools.count(k) for k in sorted(set(tools))},
             "llm_calls_mean": round(statistics.mean(t["llm_calls"] for t in ok), 2) if ok else None,
             "tokens_mean": round(statistics.mean(t["tokens"]["total"] for t in ok)) if ok else None,
             "prompt_tokens_mean": round(statistics.mean(t["tokens"]["prompt"] for t in ok)) if ok else None,
             "active_median_s": round(statistics.median(act), 1) if act else None, "active_p95_s": round(pct(act, 0.95), 1) if act else None,
             "latency_median_s": round(statistics.median(lat), 1) if lat else None, "latency_p95_s": round(pct(lat, 0.95), 1) if lat else None,
             "context_chars_mean": round(statistics.mean(t["context_chars"] for t in ok)) if ok else None}
        rp = d / "reviews.json"
        if rp.exists():
            s["agent_metrics"] = aggregate([c for c in cases if c["id"] in tb], traces, json.loads(rp.read_text(encoding="utf-8")))
        (d / "summary.json").write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        rows.append(s)
    L = ["| config | err | ctx evid | retr evid | ans grade mean | grades 0/1/2 | cite support | answers w/ cite | abstain ok | false abst | tools/q | tokens/q | active med s | active p95 s | wall med s |", "|" + "---|" * 16]
    for s in rows:
        m = s.get("agent_metrics")
        if m:
            g = m["grounded_answer"]; cv = m["citation_validity"]; ac = m["answer_citation_coverage"]
            extra = (f'{g["mean"]:.3f} | {g["0"]}/{g["1"]}/{g["2"]} | {cv["n"]}/{cv["N"]} | {ac["n"]}/{ac["N"]} | {m["abstention"]["n"]}/{m["abstention"]["N"]} | {m["false_abstention"]["n"]}/{m["false_abstention"]["N"]}')
        else:
            extra = "- | - | - | - | - | -"
        L.append(f'| {s["config"]} | {s["errors"]} | {s["context_evidence"]["n"]}/{s["context_evidence"]["N"]} | {s["retrieved_evidence"]["n"]}/{s["retrieved_evidence"]["N"]} | {extra} | {s["tool_calls_mean"]} | {s["tokens_mean"]} | {s["active_median_s"]} | {s["active_p95_s"]} | {s["latency_median_s"]} |')
    (base / "comparison.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
