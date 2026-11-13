# Checkpoints — Day 7

Các mốc tính từ lúc bắt đầu lớp; xem [GUIDE](GUIDE.md) và [BENCHMARK](BENCHMARK.md).

| Mốc | Cần hoàn thành | Bằng chứng |
|---|---|---|
| 0:00–1:00 | Kết nối model embedding/vector store Day 6; kiểm tra corpus, benchmark và split | Index/model/version, nguồn/page, 15 dev / 5 test có evidence và thêm 2 dev / 2 test thiếu evidence |
| 1:00–1:55 | Triển khai dense, BM25 và hybrid RRF trên cùng chunks | Kết quả top-3, ID/score/source/page và cấu hình |
| 1:55–2:35 | Xây agent model thật có tool search, context và citation | Trace tool/args/results, context tối đa 800 ký tự, câu trả lời hoặc abstain |
| 2:35–3:30 | Đo retrieval và agent, thử cải tiến trên dev rồi chốt trước khi chạy test | Trace, bảng `n/N`, nhãn thủ công, lỗi và lựa chọn |
| 3:30–4:00 | Demo, hoàn thiện báo cáo và nộp | Lệnh chạy, chi phí, model/index, bài nộp theo [SUBMISSION](SUBMISSION.md) |
