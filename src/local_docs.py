"""Registry of user-supplied document collections (PDFs ingested with scripts/ingest_pdf.py).

Each collection lives in data/local_docs/<name>/ (git-ignored: it holds the extracted text of your documents):
  collection.json  manifest: title, description, language, embedding model + prefixes, chapters, examples
  chunks.json      chunks in the Day 7 format: id, text, source_id, source, page, metadata
The vectors are in the same Chroma store as the Day 6 collections (src/day6_store.store_path()), under <name>.
The textbook collections (soc3e_A / soc3e_B) are NOT handled here and behave exactly as before.

The special collection "library" (scripts/build_library.py) holds every document at once: the textbook chunks and all
ingested PDFs, re-embedded with one multilingual model so a single cosine search + BM25 ranks them all together.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "data" / "local_docs"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_]{1,40}$")
RESERVED = {"soc3e_a", "soc3e_b"}
LIBRARY = "library"  # all documents in one collection; built by scripts/build_library.py, never by ingest_pdf.py

# Caches are keyed by file modification time, so a running server picks up a re-ingested document or rebuilt library.
_manifests: dict[str, tuple[int | None, dict | None]] = {}
_chunks: dict[str, tuple[int | None, list[dict]]] = {}


def _mtime(p: Path) -> int | None:
    try:
        return p.stat().st_mtime_ns
    except OSError:
        return None


def version(name: str) -> int | None:
    """Changes whenever the collection's chunks.json is rewritten (used to refresh derived indexes such as BM25)."""
    return _mtime(DOCS_DIR / name / "chunks.json") if valid_name(name) else None


def valid_name(name: str) -> bool:
    return bool(isinstance(name, str) and NAME_RE.match(name)) and name.lower() not in RESERVED


def names() -> list[str]:
    if not DOCS_DIR.is_dir():
        return []
    return sorted(p.name for p in DOCS_DIR.iterdir() if valid_name(p.name) and (p / "collection.json").is_file())


def document_names() -> list[str]:
    """Ingested PDF collections (everything except the library itself)."""
    return [n for n in names() if n != LIBRARY]


def is_library(name: str | None) -> bool:
    m = manifest(name)
    return bool(m and m.get("kind") == "library")


def manifest(name: str | None) -> dict | None:
    """The collection's manifest, or None if `name` is not a local document collection (e.g. soc3e_B)."""
    if not name or not valid_name(name):
        return None
    p = DOCS_DIR / name / "collection.json"
    mt = _mtime(p)
    if name not in _manifests or _manifests[name][0] != mt:
        _manifests[name] = (mt, json.loads(p.read_text(encoding="utf-8")) if mt is not None else None)
    return _manifests[name][1]


def load_chunks(name: str) -> list[dict]:
    if manifest(name) is None:
        raise ValueError(f"unknown local document collection {name!r}")
    mt = version(name)
    if name not in _chunks or _chunks[name][0] != mt:
        _chunks[name] = (mt, json.loads((DOCS_DIR / name / "chunks.json").read_text(encoding="utf-8")))
    return _chunks[name][1]


def clear_cache() -> None:
    _manifests.clear()
    _chunks.clear()
