# Day 7 Part 2/4 - Retrieval methods and dev evaluation

## 0. Pre-registered hypotheses and selection criteria (written BEFORE the first dev run)

Selection criteria (fixed now, applied to dev only): (1) retrieval quality first: Recall@5 and full-recall (all required evidence, relevant to the multi-hop question d13), (2) then MRR, (3) then median latency; a config must also have 0 errors. Ties within one question (1/16 = 0.0625) are treated as ties and broken by the next criterion. With n=16 answerable dev questions differences of one question are noise.

| id | config | hypothesis (predicted before running) |
|---|---|---|
| H1 | `imp1_hybrid_depth10/50_k5` (RRF candidate depth 10 / 50 vs default 20) | Corpus is only 241 chunks and questions mostly have 1 gold chunk; depth barely matters. Expect identical or +-1 question; depth 10 may drop multi-hop d13 second chunk. |
| H2 | `imp2_*_chapterfilter_k5` (chapter filter inferred from query keywords only) | Narrowing to one chapter removes cross-chapter distractors, so MRR should rise slightly; risk: a wrong inference (keyword rule picks wrong chapter) excludes the gold chunk and lowers recall. Expect small MRR gain, possible 1 recall loss. |
| H3 | `imp3_*_collA_k5` (collection A: 468 fixed 500-char chunks, vs B 241 section-aware chunks) | Smaller chunks are more focused for dense retrieval (higher Hit@1) but multi-hop needs two chunks and answers may straddle chunk borders; expect Hit@1 similar or higher, full-recall on d13 equal or lower. Day 6 chose B, so I expect B >= A overall. |
| H4 | `hybrid_rerank_*` and `imp4_*` (cross-encoder ms-marco-MiniLM-L-6-v2 on top of fused candidates; pool 20 vs 30; dense-only rerank) | Cross-encoder reads query and passage jointly, so Hit@1/MRR should improve over hybrid and dense; Recall@5 limited by the candidate pool. Cost: ~+0.1-0.5 s per query on CPU. Pool 30 ~ pool 20. |
| H5 | `imp5_hybrid_rerank_collA_k5` | Rerank may rescue collection A's smaller chunks; still B >= A. |
| H0 | baselines | Dense (bge-small) is strong for natural-language questions with named concepts; BM25 is competitive on named entities (Asch, Etzioni); hybrid >= max(dense, bm25) in Recall@5. |

### Added after reading the first dev results (error analysis stage; hypotheses written before re-running)

First run showed hybrid/dense/bm25 all fail d09 and hybrid_rerank (pool 20) too, while a pool of 30 fixes it; d07 gets a glossary chunk at rank 1 (gold is the body chunk).

| id | config | hypothesis |
|---|---|---|
| H6 | `imp4_hybrid_rerank_pool30_k3/k10` | Pool 30 fixes d09 at k=3 and 10 too (gold lands at rank 1 after rerank). |
| H7 | `imp6_*_demote_k5` (key_terms / summary / review_questions chunks ranked after body chunks, using chunk metadata `document_type` only) | Glossary chunks restate body definitions and rank above them (d07); demoting them should turn d07 rank 2 -> 1 (MRR +1/32) without losing others; risk: a question answerable only from a glossary/summary chunk would lose. |

## 1. Methods (`src/retrievers.py`)

Common interface `search(query, top_k, method, **opts) -> [{id, text, score, rank, source, page, metadata, method}]`; `safe_search` returns `{ok, error, results}`. Empty query, bad `top_k`, unknown method, Chroma/embedding failure or reranker failure raise `RetrievalError` (never fake results). Run with the Day 7 `.venv` (`pip install -r requirements.txt`). Retrieval code never reads gold; only `scripts/eval_retrieval.py` does.

| method | description |
|---|---|
| `dense` | Day 6 Chroma (`day6_store.dense_search`), bge-small-en-v1.5 cosine, optional `chapter` filter. |
| `bm25` | `rank_bm25.BM25Okapi` (k1=1.5, b=0.75) over the same chunks; tokenization = lowercase, `[a-z0-9]+`, English stopword list, tiny suffix stemmer (no nltk). |
| `hybrid` | dense top-`depth` + bm25 top-`depth` fused by RRF, `score = sum 1/(60+rank)`; `depth` (candidates per retriever) default 20. |
| `hybrid_rerank` | RRF candidates (`fuse_depth`, default 20) re-scored by a local cross-encoder, `cross-encoder/ms-marco-MiniLM-L-6-v2` (HF revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`, 88 MB download, about 40 s for first download + load + first query on this machine, cost 0 USD). Scores are logits. `dense_rerank` = same on dense candidates only. |
| `demote_backmatter` (option) | stable re-partition so chunks whose Day 6 `document_type` is key_terms / summary / review_questions rank after body chunks. Uses chunk metadata only. |
| `infer_chapter` (option) | chapter filter inferred from the **query text only**: keyword lists per chapter (5 socialization, 6 groups/organizations, 7 deviance/crime) in `CHAPTER_KEYWORDS`; applied only when one chapter has strictly the most keyword hits, otherwise no filter. Gold is never consulted. |

## 2. Evaluation setup (`scripts/eval_retrieval.py`)

Dev split only (test is refused without `--allow-test`; not run). 16 answerable (15 direct + multi-hop d13, which needs both chunks) + 3 unanswerable (excluded from metrics; their top-1 scores are in `results/retrieval/dev/comparison.md`). Hit@k = any gold chunk in top-k; Recall@k = fraction of required evidence found; FullRecall = all required evidence (multi-hop). Collection A gold = `also_in_chunks_A`. Per-query traces and summary per config in `results/retrieval/dev/<config>/`; the full table (26 configs, p95 latency, unanswerable score distribution) is `results/retrieval/dev/comparison.md`. Latency = CPU, warm models, one run; it is noisy (e.g. `hybrid_rerank_k3` 1282 ms vs `imp5` 326 ms for the same model; machine load varied), so only the order of magnitude matters: dense/hybrid tens of ms, bm25 about 1 ms, rerank 0.3-1.3 s.

## 3. Results (dev, n=16 answerable)

| config | Hit@1 | Hit@3 | Recall@5 / full | MRR | median ms |
|---|---|---|---|---|---|
| dense_k5 | 0.812 | 0.938 | 0.938 | 0.865 | 46 |
| bm25_k5 | 0.875 | 0.938 | 0.938 | 0.906 | 1 |
| hybrid_k5 (RRF, depth 20) | 0.938 | 0.938 | 0.938 | 0.938 | 52 |
| hybrid_rerank_k5 (pool 20) | 0.875 | 0.938 | 0.938 | 0.906 | 812 |
| imp1 hybrid depth 10 / 50 | 0.938 | 0.938 | 0.938 | 0.938 | 26 / 27 |
| imp2 hybrid + chapter filter | 0.938 | 0.938 | 0.938 | 0.938 | 26 |
| imp2 dense + chapter filter | 0.812 | 0.938 | 0.938 | 0.865 | 22 |
| imp3 dense, collection A | 0.750 | 0.812 | 0.781 / 0.750 | 0.781 | 24 |
| imp3 hybrid, collection A | 0.750 | 0.875 | 0.844 / 0.812 | 0.812 | 25 |
| imp4 hybrid_rerank pool 30 (k3/k5/k10) | 0.938 | 1.000 | 1.000 | 0.969 | about 1040 |
| imp4 dense_rerank (pool 20) | 0.938 | 1.000 | 1.000 | 0.969 | 689 |
| imp5 hybrid_rerank, collection A | 0.750 | 0.875 | 0.844 / 0.812 | 0.802 | 326 |
| imp6 hybrid + demote_backmatter | 0.938 | 0.938 | 0.938 | 0.938 | 25 |
| **imp6 hybrid_rerank pool 30 + demote_backmatter (k5)** | **1.000** | 1.000 | **1.000** | **1.000** | 1033 |

k = 3, 5, 10 give identical numbers for every baseline method (gold is in the top 3 or not in the top 10); see `comparison.md`. No config had errors. Multi-hop d13 (both chunks needed) is fully recalled by every collection-B config; both collection-A configs miss it.

## 4. Hypotheses vs outcomes

- H0 partly wrong: dense (MRR 0.865) is worse than bm25 (0.906) on this textbook because questions reuse textbook terms; hybrid (0.938) beats both. Recall@5 is equal for all three (all miss only d09).
- H1 confirmed: depth 10/20/50 identical (tiny corpus).
- H2 no effect: the inferred chapter filter changed no metric for hybrid or dense (harmless, not useful; keyword inference is brittle, so not recommended).
- H3 confirmed (B >= A): collection A is worse (Recall@5 0.84 hybrid / 0.78 dense), loses multi-hop d13, and d07/d08.
- H4 contradicted at pool 20 (MRR 0.906 < hybrid 0.938: the reranker put d07's glossary chunk first and d09's gold was outside the pool); confirmed at pool 30 (Recall 1.0, MRR 0.969) at about 20x the latency.
- H5 confirmed: rerank does not fix collection A (0.844).
- H6 confirmed (k=3 and 10 same as k=5).
- H7 confirmed with rerank (d07 rank 2 -> 1, MRR 1.000); without rerank, demote changed nothing.

Caveat: n=16, one question = 0.0625; the gains rest on two questions (d09, d07) that I found by reading dev failures, and pool 30 / demote were tuned on dev, so expect lower numbers on test.

## 5. Error analysis

1. **d09** "minimum number of people needed to form a group" (failed by dense, bm25, hybrid and hybrid_rerank pool 20; gold `B-soc3e-p0161-001`, 6.1 Types of Groups: "any collection of at least two people who interact..."). Root cause: vocabulary mismatch. The gold says "at least two people", the question says "minimum number ... needed"; retrievers rank 6.2 "Group Size and Structure" chunks (dyads/triads, Asch) due to group/size/people overlap. The gold is dense rank 12, bm25 rank 24, and just outside the reranker pool of 20 after fusion. Change: reranker pool 20 -> 30 (`imp4`). Re-measured: the cross-encoder ranks the gold chunk first; Recall 0.938 -> 1.000.
2. **d07** "What is anticipatory socialization?" (gold `B-soc3e-p0147-003` at rank 2 under rerank pool 20). Rank 1 was `B-soc3e-p0150-000`, the "Key Terms" glossary chunk. Root cause: the glossary is a compact definition of the same term, the cross-encoder prefers it, and it duplicates the body evidence without section context. Change: demote key_terms/summary/review_questions chunks by metadata (`imp6`). Re-measured: Hit@1 0.938 -> 1.000, MRR 0.969 -> 1.000, nothing lost on dev. Risk: a glossary-only fact is pushed down (still retrievable, since it is a re-partition not a filter).
3. (extra) **d08 with collection A**: 500-char fixed chunking cuts the answer ("must leave behind their old identity through ... a degradation ceremony") into a chunk starting mid-word ("nstitution"), and end-of-chapter review questions rank higher. This is why B stays.

## 6. Selection (criteria pre-declared in section 0, dev only)

Quality first (Recall@5 / full recall, then MRR, then latency, with 0 errors). At Recall@5 = 1.000: `imp6 hybrid_rerank pool30 + demote` (MRR 1.000), `imp4 hybrid_rerank pool30` and `imp4 dense_rerank` (MRR 0.969). Best without rerank: `hybrid_k5` (MRR 0.938, 52 ms).

**Recommended config for the agent (dev-only evidence): `method="hybrid_rerank", top_k=5, collection="soc3e_B", depth=30, fuse_depth=30, rrf_k=60, demote_backmatter=True, reranker="cross-encoder/ms-marco-MiniLM-L-6-v2"`** (about 1 s per query on CPU). Fallback when latency matters: `hybrid`, k=5, depth 20 (about 50 ms, MRR 0.938; misses d09).

Abstention note: cross-encoder top-1 logits on the 3 unanswerable dev questions (mean -3.06, max -1.39) overlap the low end of answerable top-1 scores (mean 6.8, min -7.2; d09's gold scored -6.9), and dense cosine top-1 also overlaps (unanswerable max 0.70, answerable min 0.65). A single score threshold is therefore unreliable; the agent should judge sufficiency from the retrieved text. The test split was not run; the config is not frozen until the owner decides.
