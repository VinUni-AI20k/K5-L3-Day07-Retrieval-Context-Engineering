# Pseudocode

```text
store, embedder, chunks, benchmark = adapt_day6()
assert same_embedding_model_and_dimension_for_documents_and_query
validate_sources_evidence_and_freeze_dev_test(benchmark)
retrievers = [dense(store, embedder), bm25(chunks), hybrid_rrf(dense, bm25)]
for retriever in retrievers:
    dev_trace[retriever] = evaluate_retrieval(dev_answerable, retriever, k=3, budget=800)
inspect_dev_errors_and_try_controlled_change()
selected = choose_on_dev_only_and_freeze()
for retriever in unique(retrievers + [selected]):
    test_trace[retriever] = evaluate_retrieval(test_answerable, retriever, k=3, budget=800)

# Chạy riêng agent với cấu hình đã chọn, trên câu trả lời được và thiếu evidence.
function agent(question, supplied_filter):
    context, trace = empty, []
    for step in 1..2:
        decision = model.choose_search_or_answer(question, context)
        if decision requests search:
            results = selected.search(decision.query, supplied_filter)
            context = pack_dedup_with_source(results, total_budget=800)
            trace.append(tool_args_results_context)
        else:
            break
    return model_answer_with_citations_or_abstain(context), trace

audit_grounded_answer_citation_and_abstention()
report_numerators_denominators_limits_and_reproducibility()
```

Pseudocode mô tả mục tiêu; giữ trace của mọi lần search và áp dụng budget cho context tích lũy. Kiểm tra citation ID bằng code chỉ là bước đầu, không thay audit claim so với nguồn.
