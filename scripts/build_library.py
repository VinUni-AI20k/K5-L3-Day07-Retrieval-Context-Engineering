"""Build the "library" collection: every document in ONE index, so a question is answered by searching all of them.

Usage (Day 7 .venv):  python scripts/build_library.py [--no-textbook] [--model intfloat/multilingual-e5-small]
(scripts/ingest_pdf.py runs this automatically after each ingest.)

Contents: the Day 7 textbook chunks (soc3e_B, unless --no-textbook) + every collection ingested with
scripts/ingest_pdf.py. All chunks are embedded with the same multilingual model (vectors from earlier builds or from a
document's own collection are reused when the model, prefix and text are identical), stored in the Chroma collection
"library" (cosine), and their text is written to data/local_docs/library/chunks.json for BM25. Each chunk keeps its
original id and metadata plus `document` (collection) and `doc_title`.
The textbook collection soc3e_B, its index and the benchmark are not modified.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import day6_store as d6  # noqa: E402
from src import local_docs as LD  # noqa: E402

TEXTBOOK = ("soc3e_B", "Introduction to Sociology 3e (chapters 5–7)", "en")
DEFAULT_MODEL = "intfloat/multilingual-e5-small"


def _scalar_meta(meta: dict) -> dict:
    return {k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))}


def collect(include_textbook: bool = True) -> tuple[list[dict], list[dict]]:
    """(library chunks, per-document summary) from the textbook and every ingested PDF collection."""
    sources = []
    if include_textbook:
        sources.append((TEXTBOOK[0], TEXTBOOK[1], TEXTBOOK[2], d6.load_chunks(TEXTBOOK[0])))
    for name in LD.document_names():
        m = LD.manifest(name)
        sources.append((name, m["title"], m.get("language", "en"), LD.load_chunks(name)))
    chunks, docs, seen = [], [], set()
    for coll, title, lang, cs in sources:
        for c in cs:
            if c["id"] in seen:
                raise SystemExit(f"duplicate chunk id {c['id']} in {coll}; re-ingest it with a different --id-prefix")
            seen.add(c["id"])
            chunks.append({**c, "metadata": {**_scalar_meta(c["metadata"]), "document": coll, "doc_title": title}})
        docs.append({"collection": coll, "title": title, "language": lang, "chunks": len(cs)})
    return chunks, docs


def build_library(model: str = DEFAULT_MODEL, include_textbook: bool = True, verbose: bool = True) -> dict:
    import chromadb
    t0 = time.perf_counter()
    qp, pp = ("query: ", "passage: ") if "e5" in model.lower() else ("", "")
    chunks, docs = collect(include_textbook)
    if not chunks:
        raise SystemExit("nothing to put in the library")
    try:
        store = d6.store_path()
    except FileNotFoundError:
        store = d6.LOCAL_STORE
    client = chromadb.PersistentClient(path=str(store))

    # reuse identical (model, prefix, text) vectors from the previous library and from same-model document collections
    reuse: dict[str, tuple[str, list[float]]] = {}
    candidates = [(LD.LIBRARY, pp)] + [(n, (LD.manifest(n) or {}).get("passage_prefix")) for n in LD.document_names()
                                       if (LD.manifest(n) or {}).get("embed_model") == model]
    for name, prefix in candidates:
        try:
            col = client.get_collection(name)
        except Exception:
            continue
        if name == LD.LIBRARY and (col.metadata or {}).get("embed_model") != model:
            continue
        if prefix != pp:
            continue
        got = col.get(include=["documents", "embeddings"])
        for cid, doc, emb in zip(got["ids"], got["documents"], got["embeddings"]):
            reuse.setdefault(cid, (doc, list(map(float, emb))))
    todo = [c for c in chunks if reuse.get(c["id"], ("",))[0] != c["text"]]
    if todo:
        from sentence_transformers import SentenceTransformer
        st = SentenceTransformer(model, device="cpu")
        vecs = st.encode([pp + c["text"] for c in todo], batch_size=16, normalize_embeddings=True,
                         convert_to_numpy=True, show_progress_bar=False)
        for c, v in zip(todo, vecs):
            reuse[c["id"]] = (c["text"], v.tolist())
    dim = len(reuse[chunks[0]["id"]][1])

    try:
        client.delete_collection(LD.LIBRARY)
    except Exception:
        pass
    col = client.create_collection(LD.LIBRARY, metadata={"hnsw:space": "cosine", "embed_model": model, "kind": "library"})
    for i in range(0, len(chunks), 256):
        b = chunks[i:i + 256]
        col.upsert(ids=[c["id"] for c in b], documents=[c["text"] for c in b], metadatas=[c["metadata"] for c in b],
                   embeddings=[reuse[c["id"]][1] for c in b])

    out = LD.DOCS_DIR / LD.LIBRARY
    out.mkdir(parents=True, exist_ok=True)
    (out / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    examples = []
    for d in docs:
        if d["collection"] != TEXTBOOK[0]:
            examples += [{**e, "id": e.get("id", "")} for e in (LD.manifest(d["collection"]) or {}).get("examples", [])]
    manifest = {
        "name": LD.LIBRARY, "kind": "library", "title": "All documents", "language": "multi",
        "languages": sorted({d["language"] for d in docs}),
        "math": any((LD.manifest(d["collection"]) or {}).get("math") for d in docs),
        "embed_model": model, "query_prefix": qp, "passage_prefix": pp, "dim": dim, "chunks": len(chunks),
        "documents": docs, "chapters": {}, "example_id": chunks[0]["id"], "built": date.today().isoformat(),
        "examples": examples, "include_textbook": include_textbook,
    }
    (out / "collection.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if verbose:
        print(f"library: {len(chunks)} chunks from {len(docs)} documents "
              f"({', '.join(f'{d["collection"]}={d["chunks"]}' for d in docs)}); embedded {len(todo)}, reused "
              f"{len(chunks) - len(todo)}; model={model} dim={dim} count={col.count()} ({time.perf_counter() - t0:.1f}s)")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--no-textbook", action="store_true", help="leave the sociology textbook out of the library")
    a = ap.parse_args(argv)
    build_library(a.model, include_textbook=not a.no_textbook)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
