"""Connection to the Day 6 corpus: chunks (JSONL) + Chroma vector store + embedding model.

Nothing is copied from Day 6; it is referenced by path. Configure with env vars:
  DAY6_DIR         path of the Day 6 repo (default: sibling folder, see DEFAULT_DAY6_DIR)
  DAY6_COLLECTION  soc3e_B (default; 241 chunks) or soc3e_A (468 chunks)
  VECTORSTORE_DIR  explicit Chroma store directory (highest priority)
Store resolution: VECTORSTORE_DIR -> <Day7>/vectorstore (built by scripts/build_index.py, parity-verified
with Day 6) -> <DAY6_DIR>/vectorstore. Use store_path() to see which one is active.
Requires chromadb 1.5.x and sentence-transformers (install via requirements.txt in the Day 7 .venv).
Query embedding = same model as the index (BAAI/bge-small-en-v1.5, 384-d, normalised, BGE query
instruction). Failures raise; there is no random/mock fallback. This module never reads gold files.
"""
from __future__ import annotations

import json
import os
import unicodedata
from pathlib import Path

from src import local_docs as LD  # user PDFs ingested by scripts/ingest_pdf.py (own embedding model per collection)

DEFAULT_DAY6_DIR = Path(__file__).resolve().parents[2] / "K5-L3B-Day06-TranThanhVinh-2A202603821-DataIngestion"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
EXPECTED_DIM = 384
COLLECTIONS = {"soc3e_A": "chunks_A.jsonl", "soc3e_B": "chunks_B.jsonl"}

_model = None
_doc_models: dict[str, object] = {}  # embedding models of local document collections, by model name
_clients: dict[str, object] = {}


DAY7_ROOT = Path(__file__).resolve().parents[1]
LOCAL_STORE = DAY7_ROOT / "vectorstore"
LOCAL_CHUNKS = DAY7_ROOT / "data" / "chunks.json"


def store_path() -> Path:
    """Active Chroma directory: env VECTORSTORE_DIR, else local Day 7 vectorstore, else Day 6's."""
    env = os.environ.get("VECTORSTORE_DIR")
    if env:
        p = Path(env)
        if not (p / "chroma.sqlite3").exists():
            raise FileNotFoundError(f"VECTORSTORE_DIR={p} has no chroma.sqlite3; run `python scripts/build_index.py`")
        return p
    if (LOCAL_STORE / "chroma.sqlite3").exists():
        return LOCAL_STORE
    p = Path(os.environ.get("DAY6_DIR", DEFAULT_DAY6_DIR)) / "vectorstore"
    if (p / "chroma.sqlite3").exists():
        return p
    raise FileNotFoundError("No vector store found (checked VECTORSTORE_DIR, ./vectorstore, Day 6). "
                            "Run `python scripts/build_index.py`")


def day6_dir() -> Path:
    p = Path(os.environ.get("DAY6_DIR", DEFAULT_DAY6_DIR))
    if not (p / "vectorstore" / "chroma.sqlite3").exists():
        raise FileNotFoundError(f"Day 6 vector store not found under {p}; set DAY6_DIR")
    return p


def collection_name(name: str | None = None) -> str:
    name = name or os.environ.get("DAY6_COLLECTION", "soc3e_B")
    if name not in COLLECTIONS and LD.manifest(name) is None:
        raise ValueError(f"unknown collection {name!r}; choose {list(COLLECTIONS) + LD.names()}")
    return name


def _to_chunk(row: dict) -> dict:
    m = row["metadata"]
    return {"id": row["id"], "text": row["text"], "source_id": m["document_id"], "source": m["source"],
            "page": m["page"], "metadata": m}


def load_chunks(name: str | None = None) -> list[dict]:
    """All chunks of a collection in Day 7 format: id, text, source_id, source, page, metadata."""
    name = collection_name(name)
    if name not in COLLECTIONS:
        return LD.load_chunks(name)
    d6 = Path(os.environ.get("DAY6_DIR", DEFAULT_DAY6_DIR)) / "results" / COLLECTIONS[name]
    if name == "soc3e_B" and LOCAL_CHUNKS.exists() and not d6.exists():
        return json.loads(LOCAL_CHUNKS.read_text(encoding="utf-8"))  # already in Day 7 format
    with open(d6, encoding="utf-8") as f:
        return [_to_chunk(json.loads(line)) for line in f if line.strip()]


def get_collection(name: str | None = None):
    import chromadb
    root = str(store_path())
    if root not in _clients:
        _clients[root] = chromadb.PersistentClient(path=root)
    return _clients[root].get_collection(collection_name(name))


def doc_model(model_name: str):
    """Embedding model of a local document collection (loaded once, CPU)."""
    if model_name not in _doc_models:
        from sentence_transformers import SentenceTransformer
        _doc_models[model_name] = SentenceTransformer(model_name, device="cpu")
    return _doc_models[model_name]


def embed_query(query: str, collection: str | None = None) -> list[float]:
    """Query vector for `collection`. Textbook collections (and None) use the Day 6 BGE model unchanged;
    local document collections use the model and query prefix recorded in their manifest."""
    m = LD.manifest(collection)
    if m is not None:
        q = unicodedata.normalize("NFC", m.get("query_prefix", "") + query)
        v = doc_model(m["embed_model"]).encode([q], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        if v.shape != (1, m["dim"]):
            raise RuntimeError(f"query embedding shape {v.shape} != (1, {m['dim']}) for collection {collection}")
        return v[0].tolist()
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
    r = get_collection(collection).query(query_embeddings=[embed_query(query, collection)], n_results=top_k, where=where,
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
    print(f"store={store_path()}")
    print(f"collection={col.name} count={col.count()} chunks_loaded={len(load_chunks())}")
    for h in dense_search(q, 3):
        print(f"{h['rank']} {h['id']} score={h['score']:.4f} p{h['page']} [{h['metadata']['section']}] {h['text'][:80]!r}")
