"""Helper for MANUAL grading: prints question, gold, each config's answer + cited chunk texts (evaluator-side; reads gold)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
split, configs, ids = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(",")
gold = {g["id"]: g for g in json.loads((ROOT / "benchmark/gold/gold.json").read_text(encoding="utf-8"))}
tr = {c: {t["query_id"]: t for t in json.loads((ROOT / f"results/agent/{split}/{c}/traces.json").read_text(encoding="utf-8"))} for c in configs}
seen = set()
for i in ids:
    g = gold[i]
    print("=" * 100)
    print(i, g["type"], "answerable" if g["answerable"] else "UNANSWERABLE", "|", g["question"])
    if g["answerable"]:
        print("EXPECTED:", g["expected_answer"], "| mode", g["evidence_mode"])
        for e in g["evidence"]:
            print("  GOLD", e["chunk_id"], "|", e["evidence"])
    else:
        print("ABSENCE:", g.get("absence_reason"))
    for c in configs:
        t = tr[c].get(i)
        if not t:
            print(f"--[{c}] (no trace)"); continue
        print(f"--[{c}] {t['status']} reason={t['reason']} tools={t['tool_calls']} cites={t['citations']} ctx={len(t['context_ids'])} err={t['errors'][:1]}")
        print("   ANSWER:", t["answer"])
        for cid in t["citations"]:
            if (i, cid) in seen: continue
            seen.add((i, cid))
            ch = next((x for x in t["final_context"] if x["id"] == cid), None)
            goldids = [e["chunk_id"] for e in g.get("evidence", [])]
            print(f"   CITED {cid} (gold={cid in goldids}) p{ch['page'] if ch else '?'}: {ch['text'] if ch else 'NOT IN CONTEXT'}")
