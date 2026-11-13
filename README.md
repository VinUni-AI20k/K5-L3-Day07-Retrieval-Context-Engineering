# Day 7 — Agentic RAG: Agent tìm và sử dụng tài liệu

**Bài cá nhân · 4 giờ · Tiếp nối Day 6 · Python 3.11 trở lên**

Ở Day 6, bạn đã chia tài liệu thành các đoạn, tạo vector biểu diễn và lưu chúng vào kho dữ liệu. Ở Day 7, bạn sẽ xây dựng một **agent biết gọi công cụ tìm kiếm** trong kho đó để trả lời câu hỏi có dẫn nguồn. Nếu tài liệu không đủ thông tin, agent cần nói rõ thay vì tự suy đoán.

> **Gợi ý thêm, không bắt buộc:** Bạn có thể dùng công cụ hỗ trợ lập trình như Codex, Claude Code hoặc Antigravity. Xem [gợi ý cung cấp thông tin cho công cụ lập trình](AGENT_SETUP.md). Phần này không tính điểm.

## Bài lab gồm những gì?

![Sơ đồ agent tìm tài liệu trong kho Day 6 và trả lời có dẫn nguồn](assets/retrieval-pipeline.svg)

1. **Kết nối kho dữ liệu Day 6.** Dùng lại các đoạn tài liệu, vector, mô hình tạo vector và thông tin nguồn.
2. **Xây agent.** Cho mô hình quyền gọi công cụ tìm kiếm; giới hạn số lần gọi, lưu lại các bước và yêu cầu câu trả lời có dẫn nguồn.
3. **So sánh ba cách tìm kiếm.** Thử tìm bằng vector, tìm theo từ khóa BM25 và kết hợp hai cách bằng RRF.
4. **Đánh giá và cải thiện.** Kiểm tra tài liệu tìm được, câu trả lời, nguồn trích dẫn và cách agent xử lý câu hỏi không có đủ thông tin.

## Đánh giá như thế nào?

Chuẩn bị ít nhất **20 câu có đáp án trong tài liệu**: 15 câu để phát triển và 5 câu để kiểm thử. Thêm ít nhất **4 câu không có đủ bằng chứng**: 2 câu cho mỗi tập.

Dùng tập phát triển để tìm lỗi và chọn cách cải thiện. Sau khi chốt cấu hình, chạy tập kiểm thử. Đề bài không yêu cầu điểm tìm kiếm tuyệt đối; bạn cần báo cáo trung thực và giải thích kết quả.

Chi tiết về câu hỏi, cách tính chỉ số và bảng chấm thủ công có trong [BENCHMARK.md](BENCHMARK.md).

![Các bước chạy thử, phân tích lỗi, cải thiện và kiểm thử](assets/experiment-loop.svg)

## Bắt đầu

1. Tạo kho bài làm cá nhân theo [hướng dẫn nộp bài](SUBMISSION.md). Chuẩn bị đầu ra Day 6 và một mô hình có khả năng gọi công cụ; có thể dùng mô hình chạy trên máy hoặc qua API.
2. Đọc [hướng dẫn thực hành](GUIDE.md), [cách đánh giá](BENCHMARK.md) và [các mốc thực hiện](CHECKPOINTS.md).
3. Tham khảo [bộ khởi đầu](starter/README.md). Bộ này có khung vòng lặp agent và ví dụ tìm kiếm TF-IDF; bạn cần tự kết nối mô hình và kho dữ liệu thật, sau đó bổ sung các cách tìm kiếm theo đề.
4. Chạy `python -m unittest discover -s tests -v` để kiểm tra bộ khởi đầu. Các phép thử dùng dữ liệu và kết nối giả lập chỉ kiểm tra mã; **không phải kết quả đánh giá agent thật**.

## Tài liệu và bài nộp

Nộp mã nguồn, cách chạy và kết nối kho dữ liệu, bộ câu hỏi, kết quả từng lần chạy, bảng đánh giá và [báo cáo cá nhân](report/individual/MSSV_HoTen.md). Xem danh sách đầy đủ trong [SUBMISSION.md](SUBMISSION.md).

| Tài liệu | Nội dung |
|---|---|
| [GUIDE.md](GUIDE.md) | Hướng dẫn từng bước |
| [BENCHMARK.md](BENCHMARK.md) | Cách chuẩn bị câu hỏi và đánh giá |
| [RUBRIC.md](RUBRIC.md) | Thang điểm |
| [CHECKPOINTS.md](CHECKPOINTS.md) | Các mốc trong 4 giờ |
| [starter/README.md](starter/README.md) | Bộ khởi đầu và giới hạn của nó |
| [data/README.md](data/README.md) | Định dạng dữ liệu |
| [RULES.md](RULES.md) · [SUBMISSION.md](SUBMISSION.md) | Quy tắc và cách nộp bài |
