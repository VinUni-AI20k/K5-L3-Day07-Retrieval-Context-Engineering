# Pseudocode

```text
chunks, questions = adapt_day6()
validate_unique_ids_sources_and_evidence(chunks, questions)
freeze_split_and_test()
index = build_indices(same_chunks, tokenizer, model_versions)
configs = [tfidf, bm25, rrf(tfidf, bm25)]
for config in configs:
    dev_trace[config] = evaluate(dev, config, top_k=3, budget=800)
inspect_errors(dev_trace)
candidate = controlled_change(one_baseline)
dev_trace[candidate] = evaluate(dev, candidate, top_k=3, budget=800)
selected = choose_using_dev_only(dev_trace, predeclared_rule)
freeze(selected)
for config in unique(configs + [selected]):
    test_trace[config] = evaluate(test, config, top_k=3, budget=800)
manual_audit_same_five_test_queries(test_trace)
report_with_limits_and_reproducibility()

function evaluate(queries, config, top_k, budget):
    for q in queries:
        ranks = retrieve(q.question, q.explicit_filter, config)
        results = unique_id_sorted(ranks)[:top_k]
        context = pack_whole_chunks_with_sources(results, budget)
        record_query_results_scores_gold_context_and_time()
    return numerator_denominator_hit1_hit3_context_hit()
```
