# Các bước triển khai

```text
kết_nối_kho_vector_và_mô_hình_Day6()
kiểm_tra_nguồn_và_chia_tập_câu_hỏi()

với mỗi cách tìm: vector, BM25, RRF
    chạy_các_câu_phát_triển()
    lưu_đoạn_tìm_được_và_đo_chỉ_số()

đọc_lỗi_thử_cải_thiện_và_chốt_cấu_hình()
chạy_các_câu_kiểm_thử()

với mỗi câu hỏi cho agent
    mô_hình_chọn_tìm_kiếm_hoặc_dừng()
    nếu tìm: gọi_công_cụ_và_lưu_kết_quả()  # tối đa 2 lần
    giữ_đoạn_có_nguồn_trong_giới_hạn_800_ký_tự()
    trả_lời_có_nguồn_hoặc_nói_không_đủ_thông_tin()

chấm_thủ_công_và_ghi_báo_cáo()
```

Giữ kết quả từng lần tìm. Kiểm tra ID nguồn không thay thế việc đọc xem nguồn có hỗ trợ câu trả lời hay không.
