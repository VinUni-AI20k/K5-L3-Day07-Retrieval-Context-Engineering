# Day 7 Part 1 - Preparation (Day 6 data, embedding, vector store, benchmark)

## 1. What is reused from Day 6 (referenced by path, not copied)

| Item | Value |
|---|---|
| Day 6 repo | `K5-L3B-Day06-TranThanhVinh-2A202603821-DataIngestion` (sibling folder; override with env `DAY6_DIR`) |
| Corpus | OpenStax *Introduction to Sociology 3e* (CC BY 4.0), physical PDF pages 131-212 = chapters 5-7; **69 pages with content** extracted to `data/processed/pages.jsonl` (1 document, `source_id` = `soc3e`). Meets the "at least 30 pages" bar; single-document corpus. |
| Chunks | Collection **B** `soc3e_B`: **241 chunks** (section/paragraph packing, max 1200 chars, section title prefix) - file `results/chunks_B.jsonl`. Collection A `soc3e_A`: 468 chunks (fixed 500 chars, overlap 50) - `results/chunks_A.jsonl`. Day 6 selected B; Day 7 defaults to B (env `DAY6_COLLECTION` switches). |
| Chunk ID format | `B-soc3e-p{page:04d}-{idx:03d}` (A: `A-soc3e-p...`), page = physical PDF page, idx = chunk order within the page. Deterministic. |
| Chunk fields | `id`, `text`, `metadata`. Metadata: `document_id`, `source` (download URL), `page`, `page_end`, `printed_page` (physical - 12), `chapter`, `chapter_title`, `section`, `document_type` (`chapter_intro`/`chapter_body`/...), `char_start`, `char_end`, `content_hash`, `strategy`, `license`. The module maps these to the Day 7 contract: `id, text, source_id, source, page, metadata`. |
| Vector store | **ChromaDB 1.5.9**, `PersistentClient(path=<Day6>/vectorstore)`, collections `soc3e_A` / `soc3e_B`, cosine HNSW (approximate), score = `1 - cosine distance`. Store is gitignored in Day 6; share by pointing `DAY6_DIR` at it or rebuild with Day 6 `src/index.py`. |
| Embedding model | **BAAI/bge-small-en-v1.5**, local `sentence-transformers 6.3.0` / `torch 2.15.0+cpu`, HF revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, **dimension 384**, L2-normalised, max_seq_length 512, CPU. Documents embedded without prefix; **queries prefixed** with `Represent this sentence for searching relevant passages: `. No API key, cost 0 USD. Model was not changed for Day 7, so no re-index cost. |

No random vectors, no mock fallback anywhere; query embedding uses the same model/prefix/normalisation as the index.

## 2. Connection module

`src/day6_store.py` (Day 7 contract; reads only Day 6 data, never the gold file):

- `load_chunks(collection=None)` -> list of `{id, text, source_id, source, page, metadata}`
- `get_collection(collection=None)` -> Chroma collection handle
- `embed_query(text)` -> 384-d list
- `dense_search(query, top_k=3, where=None, collection=None)` -> list of `{id, text, score, rank, source_id, source, page, metadata}`; `where` is a Chroma metadata filter, e.g. `{"chapter": 7}`
- `export_chunks(out_dir)` -> `chunks.json` for `starter/baseline.py` (default target `starter/data/converted/`, gitignored)

Environment: `chromadb==1.5.9` and `sentence-transformers` are needed. Create the Day 7 `.venv` and `pip install -r requirements.txt` (system Python lacks them). Quick check:

```bash
# Windows, from the Day 7 root
.venv\Scripts\python.exe src\day6_store.py "What is a total institution?"
```

Optional install in a Day 7 venv: `pip install torch --index-url https://download.pytorch.org/whl/cpu` then `pip install chromadb==1.5.9 sentence-transformers==6.3.0`. `load_chunks` needs neither package.

## 3. Smoke test (real query embedding + nearest-neighbour search)

Query `What is a total institution?`, collection `soc3e_B`, top-3 (run 2026-11-16 with the Day 6 venv; Day 7 venv should match):

| rank | chunk | score | page / section |
|---|---|---|---|
| 1 | `B-soc3e-p0171-003` | 0.6763 | 171 / 6.3 Formal Organizations |
| 2 | `B-soc3e-p0176-002` | 0.6534 | 176 / Key Terms |
| 3 | `B-soc3e-p0172-000` | 0.6156 | 172 / 6.3 Formal Organizations |

Identical IDs and scores to Day 6 `results/smoke_test.txt`, so the query path is compatible with the index. Collection counts: B=241, A=468; 241 chunks loaded from JSONL match.

## 4. Benchmark (per BENCHMARK.md / SUBMISSION.md)

Files:

- `benchmark/questions.json` - **agent-visible**: `id, split, question` only.
- `benchmark/gold/gold.json` - **evaluator-only** (never read by agent/retrieval code): type, expected answer, evidence (`chunk_id, source_id, page, section, evidence quote, also_in_chunks_A`), `evidence_mode` (`any` = alternatives, `all` = every item required), and for unanswerable questions `absence_reason` + `absence_check`. `gold` field also follows the starter/`data/README.md` schema.
- `scripts/build_benchmark.py` - single source of the questions; regenerates both files and verifies every gold chunk exists and every evidence quote is an exact substring of its chunk. Questions were written from the actual Day 6 chunks (Day 6's own 24-question set was *not* reused, because its test split was used in Day 6 selection).

Counts (all answerable questions are in-corpus; chapters 5, 6 and 7 are all covered):

| Split | Answerable | of which multi-hop | Unanswerable | Total |
|---|---:|---:|---:|---:|
| dev | 16 | 1 (`d13`) | 3 | 19 |
| test | 8 | 1 (`t08`) | 3 | 11 |
| **Total** | **24** | 2 | **6** | **30** |

Minimums: BENCHMARK.md dev 15+2 / test 5+2 and SUBMISSION 20 answerable + 4 unanswerable are all met.

Multi-hop scoring: `d13` and `t08` need **both** evidence chunks (`evidence_mode: all`). Report them separately from the direct questions (or count a hit only when all chunks are retrieved / in context); `starter/baseline.py` treats `gold` as alternatives and would credit one chunk.

Unanswerable questions: near-topic questions whose key facts are absent. Check method: case-insensitive exact-term count of the key terms over all 241 B chunks and all 69 source pages = 0 (recorded in `gold.json`), plus manual reading of the neighbouring pages. This is a lexical check, so absence is stated for this document set only. `t11` is a hard negative (Egalia is described, enrollment is not). Exclude unanswerable questions from retrieval-metric denominators.

Sanity checks run: `python scripts/build_benchmark.py` -> all 26 distinct gold chunk IDs exist in `soc3e_B` (JSONL) and all evidence quotes are exact substrings; additionally 26/26 gold IDs fetched from the live Chroma collection. For information only, plain dense retrieval on collection B scores Hit@1 20/24 and any-evidence Hit@3 22/24 on all answerable questions (not a reported result; dev/test must be evaluated by the proper harness).

## 5. Deviations / notes

- Day 6 was built on one English textbook; corpus is single-source, so metadata filters are limited to `chapter`/`section`/`document_type`. Questions are in English; Day 7 docs are in English.
- Day 6 vector store lives outside this repo and is gitignored there; graders need `DAY6_DIR` or a rebuild with Day 6 code (local model, free).
- Gold lives in `benchmark/gold/`; keep it out of any code path that builds prompts or filters.

## 6. Self-contained index

The Day 7 repo can rebuild the vector store itself from `data/chunks.json`, so Day 6 is no longer required at run time.

```bash
python scripts/build_index.py --rebuild     # writes ./vectorstore (gitignored); idempotent without --rebuild
python scripts/verify_index.py              # parity vs Day 6 store (needs Day 6 repo; writes results/index_parity.json)
```

- Same recipe as Day 6: `BAAI/bge-small-en-v1.5` pinned to revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`, documents without prefix, L2-normalised, CPU, collection `soc3e_B` with `hnsw:space=cosine`, ids/documents/metadata from the chunk file.
- Time: about 29 s on CPU (incl. model load, 241 chunks). Cost: 0 USD (local model).
- Parity with the Day 6 collection (`results/index_parity.json`): 241 = 241 ids, documents and metadata identical, embeddings max abs diff 0.0 (min cosine 1.0), top-10 ids and scores identical for all 30 benchmark questions (30/30, score diff 0.0). Dense k=5 dev metrics on the new store equal the Day 6-store results (only latency differs; output in `results/retrieval/dev/dense_k5_day7index`).
- Store resolution order (`src/day6_store.py`, `store_path()` shows the active one): env `VECTORSTORE_DIR` -> `<Day7>/vectorstore` if present -> `<DAY6_DIR>/vectorstore`. `load_chunks` falls back to `data/chunks.json` when Day 6 is absent.

### How to run from a fresh clone

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/build_index.py
python scripts/eval_retrieval.py --split dev --configs dense_k5
```
