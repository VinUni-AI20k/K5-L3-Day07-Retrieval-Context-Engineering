# Retrieval comparison (dev split)

Answerable n=16 (multi-hop 1), unanswerable n=3. Hit@k = any gold chunk in top-k; Recall@k = fraction of required evidence; FullRecall = all required evidence. Latency = per-query wall time on CPU, warm models (ms).

| config | method | k | coll | Hit@1 | Hit@3 | Hit@5 | Recall@k | FullRecall@k | multi-hop full | MRR | lat med ms | lat p95 ms | errors | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dense_k3 | dense | 3 | B | 0.812 | 0.938 | - | 0.938 | 0.938 | 1.0 | 0.865 | 44 | 90 | 0 | d09 |
| dense_k5 | dense | 5 | B | 0.812 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.865 | 46 | 84 | 0 | d09 |
| dense_k10 | dense | 10 | B | 0.812 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.865 | 44 | 108 | 0 | d09 |
| bm25_k3 | bm25 | 3 | B | 0.875 | 0.938 | - | 0.938 | 0.938 | 1.0 | 0.906 | 1 | 1 | 0 | d09 |
| bm25_k5 | bm25 | 5 | B | 0.875 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.906 | 1 | 2 | 0 | d09 |
| bm25_k10 | bm25 | 10 | B | 0.875 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.906 | 1 | 2 | 0 | d09 |
| hybrid_k3 | hybrid | 3 | B | 0.938 | 0.938 | - | 0.938 | 0.938 | 1.0 | 0.938 | 45 | 83 | 0 | d09 |
| hybrid_k5 | hybrid | 5 | B | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.938 | 52 | 67 | 0 | d09 |
| hybrid_k10 | hybrid | 10 | B | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.938 | 50 | 90 | 0 | d09 |
| hybrid_rerank_k3 | hybrid_rerank | 3 | B | 0.875 | 0.938 | - | 0.938 | 0.938 | 1.0 | 0.906 | 1282 | 1720 | 0 | d09 |
| hybrid_rerank_k5 | hybrid_rerank | 5 | B | 0.875 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.906 | 812 | 1114 | 0 | d09 |
| hybrid_rerank_k10 | hybrid_rerank | 10 | B | 0.875 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.906 | 720 | 842 | 0 | d09 |
| imp1_hybrid_depth10_k5 | hybrid | 5 | B | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.938 | 26 | 32 | 0 | d09 |
| imp1_hybrid_depth50_k5 | hybrid | 5 | B | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.938 | 27 | 31 | 0 | d09 |
| imp2_hybrid_chapterfilter_k5 | hybrid | 5 | B | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.938 | 26 | 34 | 0 | d09 |
| imp2_dense_chapterfilter_k5 | dense | 5 | B | 0.812 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.865 | 22 | 24 | 0 | d09 |
| imp3_hybrid_collA_k5 | hybrid | 5 | A | 0.750 | 0.875 | 0.875 | 0.844 | 0.812 | 0.0 | 0.812 | 25 | 27 | 0 | d08,d09,d13 |
| imp3_dense_collA_k5 | dense | 5 | A | 0.750 | 0.812 | 0.812 | 0.781 | 0.750 | 0.0 | 0.781 | 24 | 32 | 0 | d07,d08,d09,d13 |
| imp4_hybrid_rerank_pool30_k5 | hybrid_rerank | 5 | B | 0.938 | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 0.969 | 1090 | 1494 | 0 |  |
| imp4_dense_rerank_k5 | dense_rerank | 5 | B | 0.938 | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 0.969 | 689 | 765 | 0 |  |
| imp5_hybrid_rerank_collA_k5 | hybrid_rerank | 5 | A | 0.750 | 0.875 | 0.875 | 0.844 | 0.812 | 0.0 | 0.802 | 326 | 375 | 0 | d08,d09,d13 |
| imp6_hybrid_rerank_pool30_demote_k5 | hybrid_rerank | 5 | B | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 1.000 | 1033 | 1148 | 0 |  |
| imp6_hybrid_demote_k5 | hybrid | 5 | B | 0.938 | 0.938 | 0.938 | 0.938 | 0.938 | 1.0 | 0.938 | 25 | 28 | 0 | d09 |
| imp4_hybrid_rerank_pool30_k3 | hybrid_rerank | 3 | B | 0.938 | 1.000 | - | 1.000 | 1.000 | 1.0 | 0.969 | 1038 | 1109 | 0 |  |
| imp4_hybrid_rerank_pool30_k10 | hybrid_rerank | 10 | B | 0.938 | 1.000 | 1.000 | 1.000 | 1.000 | 1.0 | 0.969 | 1056 | 1126 | 0 |  |

## Unanswerable top-1 score vs answerable top-1 score (abstention signal)

| config | unans top1 mean | unans top1 max | ans top1 mean | ans top1 min |
|---|---|---|---|---|
| dense_k3 | 0.6594 | 0.7017 | 0.7519 | 0.6488 |
| dense_k5 | 0.6594 | 0.7017 | 0.7519 | 0.6488 |
| dense_k10 | 0.6594 | 0.7017 | 0.7519 | 0.6488 |
| bm25_k3 | 9.7087 | 11.3441 | 23.3713 | 7.2369 |
| bm25_k5 | 9.7087 | 11.3441 | 23.3713 | 7.2369 |
| bm25_k10 | 9.7087 | 11.3441 | 23.3713 | 7.2369 |
| hybrid_k3 | 0.0326 | 0.0328 | 0.0326 | 0.0304 |
| hybrid_k5 | 0.0326 | 0.0328 | 0.0326 | 0.0304 |
| hybrid_k10 | 0.0326 | 0.0328 | 0.0326 | 0.0304 |
| hybrid_rerank_k3 | -3.0579 | -1.3948 | 6.8953 | -7.1660 |
| hybrid_rerank_k5 | -3.0579 | -1.3948 | 6.8953 | -7.1660 |
| hybrid_rerank_k10 | -3.0579 | -1.3948 | 6.8953 | -7.1660 |
| imp1_hybrid_depth10_k5 | 0.0326 | 0.0328 | 0.0326 | 0.0304 |
| imp1_hybrid_depth50_k5 | 0.0326 | 0.0328 | 0.0326 | 0.0304 |
| imp2_hybrid_chapterfilter_k5 | 0.0326 | 0.0328 | 0.0326 | 0.0308 |
| imp2_dense_chapterfilter_k5 | 0.6594 | 0.7017 | 0.7519 | 0.6488 |
| imp3_hybrid_collA_k5 | 0.0323 | 0.0325 | 0.0327 | 0.0320 |
| imp3_dense_collA_k5 | 0.6516 | 0.6745 | 0.7599 | 0.6674 |
| imp4_hybrid_rerank_pool30_k5 | -3.0579 | -1.3948 | 6.9131 | -6.8813 |
| imp4_dense_rerank_k5 | -3.0579 | -1.3948 | 6.9131 | -6.8813 |
| imp5_hybrid_rerank_collA_k5 | -2.9407 | -1.0870 | 6.5243 | -7.2776 |
| imp6_hybrid_rerank_pool30_demote_k5 | -3.0579 | -1.3948 | 6.7943 | -6.8813 |
| imp6_hybrid_demote_k5 | 0.0326 | 0.0328 | 0.0326 | 0.0304 |
| imp4_hybrid_rerank_pool30_k3 | -3.0579 | -1.3948 | 6.9131 | -6.8813 |
| imp4_hybrid_rerank_pool30_k10 | -3.0579 | -1.3948 | 6.9131 | -6.8813 |

Scores are not comparable across methods (cosine / BM25 / RRF / cross-encoder logit).
