# Các bước triển khai

```text
kết_nối_vector_store_và_embedding_model_Day6()
kiểm_tra_evidence_và_chia_dev_test()

với mỗi strategy: dense, BM25, RRF
    chạy_các_câu_dev()
    lưu_kết_quả_và_đo_metrics()

đọc_lỗi_thử_cải_thiện_và_chốt_cấu_hình_trên_dev()
chạy_các_câu_test()

với mỗi câu hỏi cho agent
    model_chọn_search_hoặc_dừng()
    nếu search: gọi_tool_và_lưu_kết_quả()  # tối đa 2 lần
    giữ_chunk_có_nguồn_trong_context_800_ký_tự()
    trả_lời_có_citation_hoặc_nói_không_đủ_thông_tin()

chấm_thủ_công_và_ghi_báo_cáo()
```

Giữ kết quả từng lần search. Kiểm tra citation ID không thay thế việc đọc xem nguồn có hỗ trợ câu trả lời hay không.
