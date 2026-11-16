"""Parity check: Day 7 vectorstore vs Day 6 vectorstore (collection soc3e_B).

Day 6 store is copied to a temp dir first so it is never opened in place (no lock/write on it).
Compares ids, documents, metadata, stored embeddings, and top-10 dense results for every question in
benchmark/questions.json (questions only, no gold).  Writes results/index_parity.json.
Run: python scripts/verify_index.py [--day6 DIR] [--day7 DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DAY6 = ROOT.parent / "K5-L3B-Day06-TranThanhVinh-2A202603821-DataIngestion"
QI = "Represent this sentence for searching relevant passages: "


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day6", default=os.environ.get("DAY6_DIR", str(DEFAULT_DAY6)))
    ap.add_argument("--day7", default=str(ROOT / "vectorstore"))
    ap.add_argument("--out", default=str(ROOT / "results" / "index_parity.json"))
    a = ap.parse_args()
    import chromadb
    from build_index import COLLECTION, MODEL_NAME, MODEL_REVISION, load_model

    tmp = Path(tempfile.mkdtemp(prefix="day6_copy_"))
    shutil.copytree(Path(a.day6) / "vectorstore", tmp / "vs")
    try:
        c6 = chromadb.PersistentClient(path=str(tmp / "vs")).get_collection(COLLECTION)
        c7 = chromadb.PersistentClient(path=a.day7).get_collection(COLLECTION)
        g6 = c6.get(include=["documents", "metadatas", "embeddings"])
        g7 = c7.get(include=["documents", "metadatas", "embeddings"])
        d6 = {i: (d, m, e) for i, d, m, e in zip(g6["ids"], g6["documents"], g6["metadatas"], g6["embeddings"])}
        d7 = {i: (d, m, e) for i, d, m, e in zip(g7["ids"], g7["documents"], g7["metadatas"], g7["embeddings"])}
        common = sorted(set(d6) & set(d7))
        rep = {"model": MODEL_NAME, "revision": MODEL_REVISION, "collection": COLLECTION,
               "count_day6": c6.count(), "count_day7": c7.count(), "ids_equal": set(d6) == set(d7),
               "collection_metadata_day6": c6.metadata, "collection_metadata_day7": c7.metadata,
               "documents_equal": all(d6[i][0] == d7[i][0] for i in common),
               "metadata_equal": all(d6[i][1] == d7[i][1] for i in common)}
        e6 = np.array([d6[i][2] for i in common], dtype=np.float64)
        e7 = np.array([d7[i][2] for i in common], dtype=np.float64)
        cos = (e6 * e7).sum(1) / (np.linalg.norm(e6, axis=1) * np.linalg.norm(e7, axis=1))
        rep["embedding_max_abs_diff"] = float(np.abs(e6 - e7).max())
        rep["embedding_min_cosine"] = float(cos.min())

        qs = json.loads((ROOT / "benchmark" / "questions.json").read_text(encoding="utf-8"))
        qs = qs["questions"] if isinstance(qs, dict) else qs
        model = load_model()
        qv = model.encode([QI + q["question"] for q in qs], normalize_embeddings=True, convert_to_numpy=True,
                          show_progress_bar=False).tolist()
        r6 = c6.query(query_embeddings=qv, n_results=10, include=["distances"])
        r7 = c7.query(query_embeddings=qv, n_results=10, include=["distances"])
        same_ids = same_set = 0
        maxd = 0.0
        diffs = []
        for q, i6, i7, s6, s7 in zip(qs, r6["ids"], r7["ids"], r6["distances"], r7["distances"]):
            same_ids += i6 == i7
            same_set += set(i6) == set(i7)
            if i6 == i7:
                maxd = max(maxd, max(abs(x - y) for x, y in zip(s6, s7)))
            else:
                diffs.append({"id": q["id"], "day6": i6, "day7": i7})
        rep["queries"] = {"n": len(qs), "top10_identical_order": same_ids, "top10_same_set": same_set,
                          "max_abs_score_diff_when_identical": maxd, "differences": diffs}
        rep["passed"] = bool(rep["ids_equal"] and rep["count_day6"] == rep["count_day7"]
                             and rep["documents_equal"] and rep["metadata_equal"]
                             and rep["embedding_min_cosine"] > 0.9999 and same_set == len(qs))
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print(json.dumps(rep, indent=2)[:3000])
        return 0 if rep["passed"] else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    raise SystemExit(main())
