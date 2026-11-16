"""Retrieval evaluator (the ONLY retrieval-side code that reads benchmark/gold/gold.json).

Usage (Day 7 .venv):  python scripts/eval_retrieval.py [--configs name1,name2] [--split dev]
Writes results/retrieval/<split>/<config>/{traces.json,summary.json} and comparison.md.
The test split is refused unless --allow-test is passed (reserved until the config is frozen).

Metrics (answerable questions only):
  Hit@k   : any gold evidence chunk in top-k (k<=top_k of the config; "-" if k>top_k)
  Recall@top_k : fraction of required evidence items retrieved ("any" mode: 1 if any alternative retrieved)
  FullRecall@top_k : all required evidence items retrieved (differs from Hit only for multi-hop, evidence_mode=all)
  MRR     : 1/rank of first gold chunk within top_k (0 if absent)
Unanswerable: distribution of top-1 score (and top-k scores) for a later abstention threshold.
Collection A gold ids come from each evidence item's `also_in_chunks_A`.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import retrievers as R  # noqa: E402

# name -> (method, top_k, opts)
CONFIGS: dict[str, tuple[str, int, dict]] = {}
for _m in ("dense", "bm25", "hybrid", "hybrid_rerank"):
    for _k in (3, 5, 10):
        CONFIGS[f"{_m}_k{_k}"] = (_m, _k, {})
# improvement configs (hypotheses in docs/retrieval.md, written before running)
CONFIGS["imp1_hybrid_depth10_k5"] = ("hybrid", 5, {"depth": 10})
CONFIGS["imp1_hybrid_depth50_k5"] = ("hybrid", 5, {"depth": 50})
CONFIGS["imp2_hybrid_chapterfilter_k5"] = ("hybrid", 5, {"infer_chapter": True})
CONFIGS["imp2_dense_chapterfilter_k5"] = ("dense", 5, {"infer_chapter": True})
CONFIGS["imp3_hybrid_collA_k5"] = ("hybrid", 5, {"collection": "soc3e_A"})
CONFIGS["imp3_dense_collA_k5"] = ("dense", 5, {"collection": "soc3e_A"})
CONFIGS["imp4_hybrid_rerank_pool30_k5"] = ("hybrid_rerank", 5, {"depth": 30, "fuse_depth": 30})
CONFIGS["imp4_dense_rerank_k5"] = ("dense_rerank", 5, {})
CONFIGS["imp5_hybrid_rerank_collA_k5"] = ("hybrid_rerank", 5, {"collection": "soc3e_A"})
CONFIGS["imp6_hybrid_rerank_pool30_demote_k5"] = ("hybrid_rerank", 5, {"depth": 30, "fuse_depth": 30, "demote_backmatter": True})
CONFIGS["imp6_hybrid_demote_k5"] = ("hybrid", 5, {"demote_backmatter": True})
CONFIGS["imp4_hybrid_rerank_pool30_k3"] = ("hybrid_rerank", 3, {"depth": 30, "fuse_depth": 30})
CONFIGS["imp4_hybrid_rerank_pool30_k10"] = ("hybrid_rerank", 10, {"depth": 30, "fuse_depth": 30})


def load(split: str):
    qs = [q for q in json.loads((ROOT / "benchmark/questions.json").read_text(encoding="utf-8")) if q["split"] == split]
    gold = {g["id"]: g for g in json.loads((ROOT / "benchmark/gold/gold.json").read_text(encoding="utf-8"))}
    return qs, gold


def gold_items(g: dict, collection: str) -> list[set[str]]:
    """One set of acceptable chunk ids per required/alternative evidence item."""
    items = []
    for e in g.get("evidence", []):
        ids = {e["chunk_id"]} if collection == "soc3e_B" else set(e.get("also_in_chunks_A", []))
        items.append(ids)
    return items


def score_query(g: dict, ids: list[str], collection: str) -> dict:
    items = gold_items(g, collection)
    got = [bool(it & set(ids)) for it in items]
    mode = g.get("evidence_mode", "any")
    need = len(items) if mode == "all" else 1
    rank = next((i + 1 for i, cid in enumerate(ids) if any(cid in it for it in items)), None)
    hits_at = {k: any(any(cid in it for it in items) for cid in ids[:k]) for k in (1, 3, 5, 10)}
    n_got = sum(got)
    return {"hit_at": hits_at, "first_gold_rank": rank, "mrr": 1.0 / rank if rank else 0.0,
            "recall": (min(n_got, need) / need), "full_recall": n_got >= need, "items_found": n_got,
            "items_required": need, "gold_ids": sorted(set().union(*items)) if items else []}


def run_config(name, method, top_k, opts, qs, gold, split):
    collection = opts.get("collection") or "soc3e_B"
    # warm-up (model load / index build) excluded from latency
    R.safe_search("What is a reference group?", top_k, method, **opts)
    traces, errors = [], 0
    for q in qs:
        t0 = time.perf_counter()
        out = R.safe_search(q["question"], top_k, method, **opts)
        ms = (time.perf_counter() - t0) * 1000
        res = out["results"]
        if not out["ok"]:
            errors += 1
        ids = [h["id"] for h in res]
        g = gold[q["id"]]
        tr = {"query_id": q["id"], "split": split, "question": q["question"], "method": method, "top_k": top_k,
              "params": opts, "collection": collection, "ok": out["ok"], "error": out.get("error"),
              "inferred_chapter": R.infer_chapter(q["question"]) if opts.get("infer_chapter") else None,
              "retrieved": [{"id": h["id"], "score": h["score"], "rank": h["rank"], "page": h["page"],
                             "section": h["metadata"].get("section")} for h in res],
              "latency_ms": ms, "answerable": g.get("answerable", True), "type": g["type"]}
        if tr["answerable"]:
            tr["eval"] = score_query(g, ids, collection)
        traces.append(tr)
    summ = summarize(name, method, top_k, opts, collection, traces, errors, split)
    return traces, summ


def mean(xs):
    return statistics.mean(xs) if xs else None


def summarize(name, method, top_k, opts, collection, traces, errors, split):
    ans = [t for t in traces if t["answerable"]]
    direct = [t for t in ans if t["type"] != "multi-hop" and t["eval"]["items_required"] == 1]
    multi = [t for t in ans if t["eval"]["items_required"] > 1]
    unans = [t for t in traces if not t["answerable"]]
    hit = {k: (sum(t["eval"]["hit_at"][k] for t in ans) / len(ans) if k <= top_k else None) for k in (1, 3, 5)}
    lat = sorted(t["latency_ms"] for t in traces)
    top1 = [t["retrieved"][0]["score"] for t in unans if t["retrieved"]]
    top1_ans = [t["retrieved"][0]["score"] for t in ans if t["retrieved"]]
    return {
        "config": name, "method": method, "top_k": top_k, "params": opts, "collection": collection, "split": split,
        "n_answerable": len(ans), "n_direct": len(direct), "n_multihop": len(multi), "n_unanswerable": len(unans),
        "errors": errors,
        "hit@1": hit[1], "hit@3": hit[3], "hit@5": hit[5],
        "recall@k": mean([t["eval"]["recall"] for t in ans]),
        "full_recall@k": mean([float(t["eval"]["full_recall"]) for t in ans]),
        "multihop_full_recall": mean([float(t["eval"]["full_recall"]) for t in multi]),
        "multihop_recall": mean([t["eval"]["recall"] for t in multi]),
        "mrr": mean([t["eval"]["mrr"] for t in ans]),
        "failed_queries": [t["query_id"] for t in ans if not t["eval"]["full_recall"]],
        "latency_ms_mean": mean(lat), "latency_ms_median": statistics.median(lat),
        "latency_ms_p95": lat[min(len(lat) - 1, int(round(0.95 * (len(lat) - 1))))],
        "unanswerable_top1_scores": {t["query_id"]: t["retrieved"][0]["score"] for t in unans if t["retrieved"]},
        "unanswerable_top1_mean": mean(top1), "unanswerable_top1_max": max(top1) if top1 else None,
        "answerable_top1_mean": mean(top1_ans), "answerable_top1_min": min(top1_ans) if top1_ans else None,
        "score_scale_note": "dense=cosine, bm25=raw BM25, hybrid=RRF sum, *_rerank=cross-encoder logit; not comparable across methods",
    }


def f(x, d=3):
    return "-" if x is None else f"{x:.{d}f}"


def write_comparison(summs, split, path):
    lines = [f"# Retrieval comparison ({split} split)", "",
             f"Answerable n={summs[0]['n_answerable']} (multi-hop {summs[0]['n_multihop']}), unanswerable n={summs[0]['n_unanswerable']}. "
             "Hit@k = any gold chunk in top-k; Recall@k = fraction of required evidence; FullRecall = all required evidence. "
             "Latency = per-query wall time on CPU, warm models (ms).", "",
             "| config | method | k | coll | Hit@1 | Hit@3 | Hit@5 | Recall@k | FullRecall@k | multi-hop full | MRR | lat med ms | lat p95 ms | errors | failed |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summs:
        lines.append(f"| {s['config']} | {s['method']} | {s['top_k']} | {s['collection'][-1]} | {f(s['hit@1'])} | {f(s['hit@3'])} | "
                     f"{f(s['hit@5'])} | {f(s['recall@k'])} | {f(s['full_recall@k'])} | {f(s['multihop_full_recall'], 1)} | {f(s['mrr'])} | "
                     f"{s['latency_ms_median']:.0f} | {s['latency_ms_p95']:.0f} | {s['errors']} | {','.join(s['failed_queries'])} |")
    lines += ["", "## Unanswerable top-1 score vs answerable top-1 score (abstention signal)", "",
              "| config | unans top1 mean | unans top1 max | ans top1 mean | ans top1 min |", "|---|---|---|---|---|"]
    for s in summs:
        lines.append(f"| {s['config']} | {f(s['unanswerable_top1_mean'], 4)} | {f(s['unanswerable_top1_max'], 4)} | "
                     f"{f(s['answerable_top1_mean'], 4)} | {f(s['answerable_top1_min'], 4)} |")
    lines += ["", "Scores are not comparable across methods (cosine / BM25 / RRF / cross-encoder logit)."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=("dev", "test"))
    ap.add_argument("--allow-test", action="store_true", help="only after the config is frozen")
    ap.add_argument("--configs", default="all")
    a = ap.parse_args()
    if a.split == "test" and not a.allow_test:
        sys.exit("refusing to run the test split without --allow-test (reserved until the config is frozen)")
    qs, gold = load(a.split)
    names = list(CONFIGS) if a.configs == "all" else a.configs.split(",")
    out_root = ROOT / "results" / "retrieval" / a.split
    summs = []
    for n in names:
        method, k, opts = CONFIGS[n]
        traces, s = run_config(n, method, k, opts, qs, gold, a.split)
        d = out_root / n
        d.mkdir(parents=True, exist_ok=True)
        (d / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (d / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        summs.append(s)
        print(f"{n}: hit1={f(s['hit@1'])} hit3={f(s['hit@3'])} R={f(s['recall@k'])} full={f(s['full_recall@k'])} mrr={f(s['mrr'])} "
              f"med={s['latency_ms_median']:.0f}ms err={s['errors']} failed={s['failed_queries']}", flush=True)
    if a.configs == "all":
        write_comparison(summs, a.split, out_root / "comparison.md")
    else:  # merge with any previously saved summaries for the comparison table
        allsum = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out_root.glob("*/summary.json"))]
        order = {n: i for i, n in enumerate(CONFIGS)}
        allsum.sort(key=lambda s: order.get(s["config"], 999))
        write_comparison(allsum, a.split, out_root / "comparison.md")


if __name__ == "__main__":
    main()
