# Các bước triển khai

```text
kết_nối_vector_store_và_embedding_model_Day6()
chuẩn_bị_evidence_và_chia_dev_test()

với ít nhất 3 phương pháp retrieval do bạn chọn
    chạy_dev_và_lưu_trace_metrics()

phân_tích_lỗi_và_đặt_giả_thuyết()
thử_ít_nhất_2_cấu_hình_cải_thiện_trên_dev()
chọn_và_chốt_cấu_hình_theo_chất_lượng_thời_gian_chi_phí()

với baseline và cấu hình đã chọn, chạy agent trên test
    agent_chọn_tool_và_số_lượt_truy_xuất()
    chọn_context_có_nguồn()
    trả_lời_có_citation_hoặc_nói_không_đủ_thông_tin()
    lưu_trace_và_chấm_câu_trả_lời()

ghi_kết_quả_giới_hạn_và_báo_cáo()
```

Đây là một hướng triển khai, không bắt buộc kiến trúc cụ thể. Kiểm tra citation ID không thay thế việc đọc xem nguồn có hỗ trợ câu trả lời hay không.
