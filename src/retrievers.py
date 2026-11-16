"""Retrieval methods over the Day 6 corpus with one interface.

    search(query, top_k=5, method="dense"|"bm25"|"hybrid"|"hybrid_rerank"|"dense_rerank", **opts)
        -> list of {id, text, score, rank, source, page, metadata, method}

opts: collection (soc3e_A/soc3e_B, or a local document collection from scripts/ingest_pdf.py), chapter (int or None), infer_chapter (bool; filter derived
from the query text only), depth (candidates per retriever before fusion/rerank, default 20),
rrf_k (60), demote_backmatter (push key_terms/summary/review_questions chunks below body chunks), fuse_depth (candidates sent to the reranker, default 20), reranker (cross-encoder name).
Errors raise RetrievalError (empty query, store failure); there is no fake fallback.
safe_search() wraps this and returns an error record instead of raising.
Never reads gold files.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import day6_store as d6  # noqa: E402

RERANKER_DEFAULT = "cross-encoder/ms-marco-MiniLM-L-6-v2"
STOP = set("""a an the of in on at to for from by with and or but is are was were be been being it its this that these
those as what which who whom whose how when where why do does did done can could should would may might will shall
than then so such not no nor into about according textbook between during their there they them he she his her you
your we our i me my also have has had having if any each other some more most many much""".split())


BACKMATTER = {"key_terms", "review_questions", "summary"}  # Day 6 document_type values for end-of-section material


class RetrievalError(RuntimeError):
    pass


def stem(w: str) -> str:
    """Tiny suffix stripper (nltk is not installed)."""
    for suf, rep in (("ization", "ize"), ("ies", "y"), ("ing", ""), ("ed", ""), ("ly", ""), ("es", ""), ("s", "")):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not (suf == "s" and w.endswith("ss")):
            return w[: len(w) - len(suf)] + rep
    return w


def tokenize(text: str, lang: str = "en") -> list[str]:
    if lang == "vi":
        return tokenize_vi(text)
    if lang == "multi":
        return tokenize_multi(text)
    return [stem(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


def tokenize_multi(text: str) -> list[str]:
    """Mixed English + Vietnamese (the library collection): Unicode words; plain-ASCII words get the English stemmer,
    words with Vietnamese letters are kept as is; plus adjacent-word pairs. Used for both chunks and queries."""
    words = re.findall(r"\w+", unicodedata.normalize("NFC", text).lower())
    stop = STOP | VI_STOP
    return [stem(w) if w.isascii() else w for w in words if w not in stop] + \
        [f"{a}_{b}" for a, b in zip(words, words[1:]) if a not in stop and b not in stop]


# Vietnamese (local document collections with language "vi"): words are written as space-separated syllables,
# so index each syllable plus each adjacent syllable pair ("ma trận" -> "ma", "trận", "ma_trận"). No stemming.
# "không" is deliberately not a stopword: it is part of terms such as "không gian" (space).
VI_STOP = set("""và của là các có được cho trong với một những thì ta này đó khi nếu để từ theo cũng như đã sẽ ra
vào lại rằng hay hoặc mà nào gì sao thế bằng hãy""".split())


def tokenize_vi(text: str) -> list[str]:
    syl = re.findall(r"\w+", unicodedata.normalize("NFC", text).lower())
    return [t for t in syl if t not in VI_STOP] + \
        [f"{a}_{b}" for a, b in zip(syl, syl[1:]) if a not in VI_STOP and b not in VI_STOP]


# --- query-only chapter inference -------------------------------------------------------------
# Chapter 5 = Socialization, 6 = Social Groups and Organization, 7 = Deviance, Crime and Social Control
# (chapter titles from the textbook table of contents / chunk metadata). Keyword rules are applied to the
# QUERY text only; a chapter is returned only if it has strictly the most keyword hits, otherwise None
# (= no filter). Gold labels are never consulted.
CHAPTER_KEYWORDS = {
    5: ["socializ", "looking glass", "cooley", "mead", "kohlberg", "piaget", "play stage", "preparatory",
        "moral development", "gender role", "peer group", "anticipatory", "resocializ", "total institution",
        "rite of passage", "hidden curriculum", "egalia", "self development", "self-development", "child"],
    6: ["group", "leader", "conformity", "asch", "milgram", "bureaucra", "weber", "etzioni", "organization",
        "in-group", "network", "mcdonaldization", "coerc", "utilitarian", "normative", "dyad", "triad",
        "instrumental", "expressive"],
    7: ["deviance", "deviant", "crime", "criminal", "merton", "strain", "lemert", "labeling", "differential association",
        "social control", "sanction", "recidivism", "conformist", "innovation", "ritualism", "retreatism",
        "rebellion", "white-collar", "punishment", "stigma", "broken windows"],
}


def infer_chapter(query: str) -> int | None:
    q = query.lower()
    scores = {c: sum(1 for k in kws if k in q) for c, kws in CHAPTER_KEYWORDS.items()}
    top = max(scores.values())
    if top == 0:
        return None
    winners = [c for c, s in scores.items() if s == top]
    return winners[0] if len(winners) == 1 else None


# --- indexes / helpers ------------------------------------------------------------------------
_bm25_cache: dict = {}


def _bm25(collection):
    key = d6.collection_name(collection)
    ver = d6.LD.version(key) if d6.LD.manifest(key) else None  # local collections: rebuilt when re-ingested
    if key not in _bm25_cache or _bm25_cache[key][0] != ver:
        from rank_bm25 import BM25Okapi
        chunks = d6.load_chunks(key)
        lang = collection_lang(key)
        _bm25_cache[key] = (ver, BM25Okapi([tokenize(c["text"], lang) for c in chunks]), chunks)
    return _bm25_cache[key][1:]


def collection_lang(collection) -> str:
    """Tokenizer language: a local document collection's manifest language, else English (textbook)."""
    m = d6.LD.manifest(d6.collection_name(collection))
    return (m or {}).get("language", "en")


def _fmt(c: dict, score: float, rank: int, method: str) -> dict:
    return {"id": c["id"], "text": c["text"], "score": float(score), "rank": rank, "source": c["source"],
            "source_id": c.get("source_id"), "page": c["page"], "metadata": c["metadata"], "method": method}


def _where(chapter):
    return {"chapter": int(chapter)} if chapter is not None else None


def _dense(query, n, collection, chapter):
    try:
        hits = d6.dense_search(query, top_k=n, where=_where(chapter), collection=collection)
    except Exception as e:  # store connection / embedding failure
        raise RetrievalError(f"dense search failed: {type(e).__name__}: {e}") from e
    return [_fmt(h, h["score"], i + 1, "dense") for i, h in enumerate(hits)]


def _bm25_search(query, n, collection, chapter):
    try:
        bm, chunks = _bm25(collection)
    except Exception as e:
        raise RetrievalError(f"bm25 index failed: {type(e).__name__}: {e}") from e
    toks = tokenize(query, collection_lang(collection))
    if not toks:
        raise RetrievalError("query has no content tokens after stopword removal")
    scores = bm.get_scores(toks)
    order = sorted(range(len(chunks)), key=lambda i: (-scores[i], chunks[i]["id"]))
    out = []
    for i in order:
        if chapter is not None and chunks[i]["metadata"].get("chapter") != int(chapter):
            continue
        if scores[i] <= 0:
            break
        out.append(_fmt(chunks[i], scores[i], len(out) + 1, "bm25"))
        if len(out) >= n:
            break
    return out


def rrf(lists: list[list[dict]], k: int = 60) -> list[dict]:
    fused: dict[str, dict] = {}
    for lst in lists:
        for h in lst:
            e = fused.setdefault(h["id"], {**h, "score": 0.0})
            e["score"] += 1.0 / (k + h["rank"])
    return sorted(fused.values(), key=lambda h: (-h["score"], h["id"]))


_rerankers: dict = {}


def _rerank(query, cands, model_name):
    try:
        if model_name not in _rerankers:
            from sentence_transformers import CrossEncoder
            _rerankers[model_name] = CrossEncoder(model_name, device="cpu")
        sc = _rerankers[model_name].predict([(query, c["text"]) for c in cands], show_progress_bar=False)
    except Exception as e:
        raise RetrievalError(f"rerank failed ({model_name}): {type(e).__name__}: {e}") from e
    return sorted(({**c, "score": float(s)} for c, s in zip(cands, sc)), key=lambda h: (-h["score"], h["id"]))


def search(query: str, top_k: int = 5, method: str = "dense", **opts) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise RetrievalError("empty query")
    if top_k < 1:
        raise RetrievalError("top_k must be >= 1")
    collection = opts.get("collection")
    chapter = opts.get("chapter")
    if chapter is None and opts.get("infer_chapter"):
        chapter = infer_chapter(query)
    demote = bool(opts.get("demote_backmatter"))
    n = max(int(opts.get("depth", 20)), top_k)
    pool = n if demote else top_k  # need a deeper list to re-partition
    if method == "dense":
        res = _dense(query, pool, collection, chapter)
    elif method == "bm25":
        res = _bm25_search(query, pool, collection, chapter)
    elif method in ("hybrid", "hybrid_rerank", "dense_rerank"):
        if method == "dense_rerank":
            cands = _dense(query, n, collection, chapter)
        else:
            cands = rrf([_dense(query, n, collection, chapter), _bm25_search(query, n, collection, chapter)],
                        int(opts.get("rrf_k", 60)))
        if method == "hybrid":
            res = cands
        else:
            cands = cands[: max(int(opts.get("fuse_depth", 20)), top_k)]
            res = _rerank(query, cands, opts.get("reranker", RERANKER_DEFAULT))
    else:
        raise RetrievalError(f"unknown method {method!r}")
    if demote:  # stable partition: body chunks first, glossary/summary/quiz chunks after (document_type metadata only)
        res = [h for h in res if h["metadata"].get("document_type") not in BACKMATTER] +               [h for h in res if h["metadata"].get("document_type") in BACKMATTER]
    res = res[:top_k]
    return [{**h, "rank": i + 1, "method": method} for i, h in enumerate(res)]


def safe_search(query, top_k=5, method="dense", **opts) -> dict:
    """Never raises: {"ok": True, "results": [...]} or {"ok": False, "error": "...", "results": []}."""
    try:
        return {"ok": True, "results": search(query, top_k, method, **opts)}
    except RetrievalError as e:
        return {"ok": False, "error": str(e), "results": []}
