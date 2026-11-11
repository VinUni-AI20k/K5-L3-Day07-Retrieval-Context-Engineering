# Day 7 — Retrieval & Context Engineering: Từ câu hỏi đến bằng chứng

**Cá nhân · 4 giờ · Python 3.11+ · tiếp nối Day 6**

Bạn nhận đầu ra ingestion: chunks, metadata và benchmark. Hãy xây, so sánh ít nhất **ba chiến lược retrieval**, đóng gói kết quả thành context có thể truy nguồn, dùng dev để cải thiện một cấu hình và đánh giá trên test.

> **Gợi ý thêm — tùy chọn:** Muốn dùng Codex, Claude Code hoặc Antigravity để hỗ trợ lập trình? Xem [best practices về context cho coding agent](AGENT_SETUP.md): instruction, skill, MCP và plugin. Phần này không bắt buộc, không tính điểm và không yêu cầu cài đặt.

Đọc [RULES](RULES.md), [CHECKPOINTS](CHECKPOINTS.md), [GUIDE](GUIDE.md), [RUBRIC](RUBRIC.md), [SUBMISSION](SUBMISSION.md) và [PSEUDOCODE](PSEUDOCODE.md). Báo cáo theo [mẫu cá nhân](report/individual/MSSV_HoTen.md). Có thể làm offline không API key; không cần chatbot hoặc LLM sinh câu trả lời.

## Pipeline: từ Day 6 đến context

![Sơ đồ pipeline từ dữ liệu Day 6, các chiến lược retrieval đến context có nguồn](assets/retrieval-pipeline.svg)

Từ cùng một bộ chunks, chạy TF-IDF + cosine và BM25 độc lập; dùng RRF để gộp hai bảng xếp hạng thành chiến lược thứ ba. Mỗi chiến lược trả top-3 để đóng gói context và đo retrieval. Có thể thay TF-IDF bằng dense embedding thật; RRF kết hợp TF-IDF và BM25 là kết hợp hai phương pháp lexical.

## Vòng lặp thực nghiệm

![Vòng lặp đánh giá trên dev và kiểm thử sau khi chốt cấu hình](assets/experiment-loop.svg)

Đọc trace, thử cải tiến trên dev, chọn cấu hình rồi đánh giá test đã giữ kín.

## Đầu ra bắt buộc

- Chuyển dữ liệu Day 6 sang contract trong `data/README.md`; giữ nguyên văn evidence và định danh nguồn/trang. Nếu không có Day 6, tự chuẩn bị corpus và benchmark theo GUIDE.
- Ba chiến lược có tên: BM25, TF-IDF + cosine, và RRF kết hợp hai bảng xếp hạng; hoặc dense embedding thật thay TF-IDF. Không gọi TF-IDF là semantic embedding. Giữ cùng corpus/chunks và so sánh công bằng.
- Context có nguồn, loại trùng, tuân thủ budget cố định; trace đủ để tính và kiểm tra metrics.
- Chốt baseline → phân tích dev → đề xuất và thử cải tiến có kiểm soát → chọn cấu hình theo dev → chạy test một lần. Cải thiện không bắt buộc có điểm cao hơn.
- Nộp code, dữ liệu được phép chia sẻ hoặc cách tái tạo, benchmark/gold, config, trace, nhãn và báo cáo.

## Bắt đầu

1. Fork hoặc clone repository đề bài và tạo repo cá nhân theo [SUBMISSION](SUBMISSION.md); mở thư mục này trong môi trường làm việc của bạn.
2. Tạo môi trường Python và cài các thư viện bạn chọn; ghi phiên bản và lệnh trong README bài nộp. Dùng `data/example_*.json` chỉ để kiểm tra schema, không phải benchmark nộp bài.
3. Làm theo [GUIDE](GUIDE.md). Chạy `python -m unittest discover -s tests -v` để kiểm tra fixture và contract mẫu.
