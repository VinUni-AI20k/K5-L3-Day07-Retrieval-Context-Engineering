r"""Export the real Day 6 chunks (soc3e_B) and the Day 7 benchmark to data/ in the starter JSON format.

  python scripts/export_data.py                 # system python is enough (reads Day 6 JSONL)
  <Day6>.venvScripts\python.exe scripts/export_data.py --verify-chroma   # also compare text with Chroma

Writes data/chunks.json, data/questions.json (EVALUATOR ONLY: contains gold), data/agent_cases.json.
Agents/retrieval must read only benchmark/questions.json (id, split, question; no gold).
Answerable questions -> data/questions.json (starter requires non-empty gold). Unanswerable -> agent_cases only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import day6_store  # noqa: E402


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="soc3e_B")
    ap.add_argument("--out", type=Path, default=ROOT / "data")
    ap.add_argument("--verify-chroma", action="store_true")
    a = ap.parse_args()

    chunks = day6_store.load_chunks(a.collection)
    if a.verify_chroma:
        got = day6_store.get_collection(a.collection).get(include=["documents"])
        db = dict(zip(got["ids"], got["documents"]))
        assert set(db) == {c["id"] for c in chunks}, "chunk id sets differ from Chroma"
        bad = [c["id"] for c in chunks if db[c["id"]] != c["text"]]
        assert not bad, f"text differs from Chroma: {bad[:5]}"
        print(f"chroma verified: {len(db)} chunks identical")

    by_id = {c["id"]: c for c in chunks}
    pub = {q["id"]: q for q in json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8"))}
    gold = json.loads((ROOT / "benchmark" / "gold" / "gold.json").read_text(encoding="utf-8"))
    assert set(pub) == {g["id"] for g in gold}

    questions, cases = [], []
    for g in gold:
        q = pub[g["id"]]
        assert q["question"] == g["question"] and q["split"] == g["split"]
        if g["answerable"]:
            entries = []
            for ev, gd in zip(g["evidence"], g["gold"]):
                c = by_id[ev["chunk_id"]]
                assert gd["evidence"] in c["text"] and gd["page"] == c["page"] and gd["source_id"] == c["source_id"]
                entries.append({"source_id": gd["source_id"], "page": gd["page"], "evidence": gd["evidence"],
                                "chunk_id": ev["chunk_id"]})
            questions.append({"id": g["id"], "split": g["split"], "question": g["question"], "gold": entries,
                              "expected_answer": g["expected_answer"], "filter": {},
                              "type": g["type"], "evidence_mode": g["evidence_mode"]})
            cases.append({"id": g["id"], "split": g["split"], "question": g["question"], "answerable": True,
                          "expected_behavior": "search_and_answer"})
        else:
            cases.append({"id": g["id"], "split": g["split"], "question": g["question"], "answerable": False,
                          "expected_behavior": g["expected_behavior"], "absence_reason": g["absence_reason"]})

    a.out.mkdir(parents=True, exist_ok=True)
    dump(a.out / "chunks.json", chunks)
    dump(a.out / "questions.json", questions)
    dump(a.out / "agent_cases.json", cases)
    print(f"chunks={len(chunks)} questions(answerable)={len(questions)} agent_cases={len(cases)}")


if __name__ == "__main__":
    main()
