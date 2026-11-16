"""Rebuild the Chroma vector store inside this repo from data/chunks.json (self-contained, cost 0).

Same settings as Day 6: BAAI/bge-small-en-v1.5 (pinned revision), documents embedded without prefix,
L2-normalised, CPU, batch 32; collection soc3e_B with {"hnsw:space": "cosine"}; ids/documents/metadata
taken as-is from the chunk file.   Run: python scripts/build_index.py [--rebuild] [--out vectorstore]
Idempotent: upsert by id; without --rebuild existing identical content is simply overwritten.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "BAAI/bge-small-en-v1.5"
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
COLLECTION = "soc3e_B"
METRIC = {"hnsw:space": "cosine"}
EMBED_BATCH = 32
ADD_BATCH = 100


def load_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME, revision=MODEL_REVISION, device="cpu")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=str(ROOT / "data" / "chunks.json"))
    ap.add_argument("--out", default=str(ROOT / "vectorstore"))
    ap.add_argument("--rebuild", action="store_true", help="drop and recreate the collection")
    a = ap.parse_args()

    import chromadb
    chunks = json.loads(Path(a.chunks).read_text(encoding="utf-8"))
    t0 = time.perf_counter()
    model = load_model()
    dim = int(model.get_sentence_embedding_dimension())
    vecs = model.encode([c["text"] for c in chunks], batch_size=EMBED_BATCH, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=False)
    if vecs.shape != (len(chunks), dim):
        raise RuntimeError(f"unexpected embedding shape {vecs.shape}")
    client = chromadb.PersistentClient(path=a.out)
    if a.rebuild:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
    col = client.get_or_create_collection(COLLECTION, metadata=METRIC)
    for i in range(0, len(chunks), ADD_BATCH):
        b = chunks[i:i + ADD_BATCH]
        col.upsert(ids=[c["id"] for c in b], documents=[c["text"] for c in b],
                   metadatas=[c["metadata"] for c in b], embeddings=vecs[i:i + ADD_BATCH].tolist())
    dt = time.perf_counter() - t0
    print(f"model={MODEL_NAME} revision={MODEL_REVISION} dim={dim} chromadb={chromadb.__version__}")
    print(f"collection={COLLECTION} count={col.count()} (chunks in file: {len(chunks)}) out={a.out} time={dt:.1f}s")
    return 0 if col.count() == len(chunks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
