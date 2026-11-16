"""Connection to the Day 6 corpus: chunks (JSONL) + Chroma vector store + embedding model.

Nothing is copied from Day 6; it is referenced by path. Configure with env vars:
  DAY6_DIR         path of the Day 6 repo (default: sibling folder, see DEFAULT_DAY6_DIR)
  DAY6_COLLECTION  soc3e_B (default; 241 chunks) or soc3e_A (468 chunks)
Requires chromadb 1.5.x and sentence-transformers (the Day 6 .venv has both).
Query embedding = same model as the index (BAAI/bge-small-en-v1.5, 384-d, normalised, BGE query
instruction). Failures raise; there is no random/mock fallback. This module never reads gold files.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_DAY6_DIR = Path(__file__).resolve().parents[2] / "K5-L3B-Day06-TranThanhVinh-2A202603821-DataIngestion"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
EXPECTED_DIM = 384
COLLECTIONS = {"soc3e_A": "chunks_A.jsonl", "soc3e_B": "chunks_B.jsonl"}

_model = None
_clients: dict[str, object] = {}


def day6_dir() -> Path:
    p = Path(os.environ.get("DAY6_DIR", DEFAULT_DAY6_DIR))
    if not (p / "vectorstore" / "chroma.sqlite3").exists():
        raise FileNotFoundError(f"Day 6 vector store not found under {p}; set DAY6_DIR")
    return p


def collection_name(name: str | None = None) -> str:
    name = name or os.environ.get("DAY6_COLLECTION", "soc3e_B")
    if name not in COLLECTIONS:
        raise ValueError(f"unknown collection {name!r}; choose {list(COLLECTIONS)}")
    return name


def _to_chunk(row: dict) -> dict:
    m = row["metadata"]
    return {"id": row["id"], "text": row["text"], "source_id": m["document_id"], "source": m["source"],
            "page": m["page"], "metadata": m}


def load_chunks(name: str | None = None) -> list[dict]:
    """All chunks of a collection in Day 7 format: id, text, source_id, source, page, metadata."""
    path = day6_dir() / "results" / COLLECTIONS[collection_name(name)]
    with open(path, encoding="utf-8") as f:
        return [_to_chunk(json.loads(line)) for line in f if line.strip()]


def get_collection(name: str | None = None):
    import chromadb
    root = str(day6_dir() / "vectorstore")
    if root not in _clients:
        _clients[root] = chromadb.PersistentClient(path=root)
    return _clients[root].get_collection(collection_name(name))


def embed_query(query: str) -> list[float]:
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME, device="cpu")
    v = _model.encode([QUERY_INSTRUCTION + query], normalize_embeddings=True, convert_to_numpy=True,
                      show_progress_bar=False)
    if v.shape != (1, EXPECTED_DIM):
        raise RuntimeError(f"query embedding shape {v.shape} != (1, {EXPECTED_DIM})")
    return v[0].tolist()


def dense_search(query: str, top_k: int = 3, where: dict | None = None, collection: str | None = None) -> list[dict]:
    """Dense (cosine) nearest-neighbour search. `where` is a Chroma metadata filter, e.g. {"chapter": 7}.
    Returns top_k dicts: id, text, score (=1-cosine distance), rank (1-based), source_id, source, page, metadata."""
    r = get_collection(collection).query(query_embeddings=[embed_query(query)], n_results=top_k, where=where,
                                         include=["documents", "metadatas", "distances"])
    out = []
    for i, (cid, doc, m, d) in enumerate(zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])):
        out.append({"id": cid, "text": doc, "score": 1.0 - d, "rank": i + 1, "source_id": m["document_id"],
                    "source": m["source"], "page": m["page"], "metadata": m})
    return out


def export_chunks(out_dir: str | Path, name: str | None = None) -> Path:
    """Write chunks.json (Day 7 data contract) for starter/baseline.py; default starter/data/converted."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / "chunks.json"
    p.write_text(json.dumps(load_chunks(name), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is a total institution?"
    col = get_collection()
    print(f"collection={col.name} count={col.count()} chunks_loaded={len(load_chunks())}")
    for h in dense_search(q, 3):
        print(f"{h['rank']} {h['id']} score={h['score']:.4f} p{h['page']} [{h['metadata']['section']}] {h['text'][:80]!r}")
