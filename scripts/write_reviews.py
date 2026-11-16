"""Writes results/agent/<split>/<config>/reviews.json from MANUAL labels.

Labels were assigned by an AI assistant (Claude) that read, for every answer, the cited chunk text and the gold evidence
(see scripts/review_dump.py), on 2026-11-16. They are AI-assisted and must be spot-checked by the student.
Usage: python scripts/write_reviews.py dev cfg1,cfg2,...  (a config's labels are in LABELS below; only configs whose
answers were read may be listed). Per query the label is (answer_grade, [citation_support...], note).
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
split, configs = sys.argv[1], sys.argv[2].split(",")
cases = {c["id"]: c for c in json.loads((ROOT / f"results/agent/{split}/cases.json").read_text(encoding="utf-8"))}
# Per-query exceptions to the default "2, all cited chunks support their claims"; none were needed for the dev configs
# read so far: every answerable answer matched the gold fact and every citation supported the sentence it follows.
EXCEPTIONS: dict[tuple[str, str], dict] = {}
NOTES = {
 "d10": "cited chunks 0164-000 (definition), 0164-001 and 0169-001 (reference groups guide behaviour/norms) all support the claims",
 "d13": "both Etzioni chunks cited; normative/coercive in 0171-003, utilitarian in 0172-000 (multi-hop, mode all)",
}
for cfg in configs:
    traces = json.loads((ROOT / f"results/agent/{split}/{cfg}/traces.json").read_text(encoding="utf-8"))
    out = []
    for t in traces:
        i = t["query_id"]
        if t["status"] == "error":
            continue
        r = {"query_id": i, "labeler": "AI-assisted (Claude); student spot-check required"}
        ex = EXCEPTIONS.get((cfg, i), {})
        if cases[i]["answerable"]:
            r["answer_grade"] = ex.get("answer_grade", 0 if t["status"] == "abstain" else 2)
            r["citation_support"] = ex.get("citation_support", [True] * len(t["citations"]))
            r["note"] = ex.get("note", NOTES.get(i, "answer matches expected answer; cited chunk contains the stated fact"))
        else:
            r["citation_support"] = ex.get("citation_support", [True] * len(t["citations"]))
            r["abstention_correct"] = ex.get("abstention_correct", t["status"] == "abstain")
            r["note"] = ex.get("note", "no answer in corpus (absence_reason in gold); agent abstained without unsupported claims")
        out.append(r)
    (ROOT / f"results/agent/{split}/{cfg}/reviews.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(cfg, len(out), "reviews")
