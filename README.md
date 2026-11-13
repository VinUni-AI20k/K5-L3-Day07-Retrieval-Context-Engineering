# Day 7 — Agentic RAG & Context Engineering

### Từ vector store đến agent trả lời có bằng chứng

**Bài cá nhân · 4 giờ · Python 3.11+ · tiếp nối Day 6**

Day 6 tạo chunks, embeddings và vector store. Day 7 xây một **agent dùng model thật** để quyết định gọi tool truy xuất, lấy bằng chứng từ kho đó và trả lời có nguồn hoặc nói không đủ thông tin.

> **Gợi ý tùy chọn:** Muốn dùng coding agent hỗ trợ lập trình? Xem [best practices về instruction, skill, MCP và plugin](AGENT_SETUP.md). Phần này không bắt buộc và không tính điểm.

## Bạn sẽ làm gì?

![Agent gọi tool truy xuất dữ liệu Day 6 và trả lời dựa trên context](assets/retrieval-pipeline.svg)

1. **Kết nối Day 6:** tái sử dụng chunks, metadata, embedding model và vector store; query embedding phải tương thích với index.
2. **Xây agentic RAG:** model quyết định gọi retrieval tool, nhận context có nguồn rồi trả lời có citation hoặc từ chối khi thiếu bằng chứng. Lưu trace và giới hạn số lần gọi tool.
3. **So sánh retrieval:** chạy dense, BM25 và hybrid dense + BM25 (RRF) trên cùng dữ liệu, câu hỏi và budget. TF-IDF là đối chứng lexical tùy chọn.
4. **Đánh giá và cải thiện:** benchmark retrieval, context và hành vi agent; phân tích lỗi, thử cải tiến trên dev, chốt rồi đánh giá test.

## Benchmark

[Benchmark Day 7](BENCHMARK.md) có hai tầng: **Hit@1, Evidence Hit@3, Context Evidence Hit@3** cho retrieval/context; **tool use, grounded answer, citation validity, abstention** cho agent. Dùng tối thiểu 15 dev / 5 test có evidence và thêm 2 dev / 2 test thiếu evidence; báo tử số/mẫu số, trace và nhãn thủ công. Giữ test độc lập trong lúc chọn và chỉnh cấu hình.

![Vòng lặp baseline, phân tích lỗi, cải tiến trên dev và đánh giá test](assets/experiment-loop.svg)

## Bắt đầu

1. Fork hoặc clone repo, tạo repo cá nhân theo [SUBMISSION](SUBMISSION.md). Chuẩn bị output Day 6 và model hỗ trợ tool calling; có thể dùng model local hoặc API.
2. Đọc [GUIDE](GUIDE.md), [BENCHMARK](BENCHMARK.md) và [CHECKPOINTS](CHECKPOINTS.md). [Starter](starter/README.md) có khung vòng lặp agent, adapter JSON và TF-IDF lexical baseline; bạn cần nối model/vector store thật và bổ sung dense, BM25, RRF.
3. Chạy `python -m unittest discover -s tests -v` để kiểm tra contract và vòng lặp với fixture. Test dùng fake adapter **không phải benchmark thật**.

## Nộp bài và tài liệu

Nộp code, cấu hình/model, hướng dẫn kết nối dữ liệu và vector store Day 6, benchmark/gold, trace, kết quả dev/test, nhãn audit và [báo cáo cá nhân](report/individual/MSSV_HoTen.md). Xem [SUBMISSION](SUBMISSION.md) để biết checklist.

| Tài liệu | Nội dung |
|---|---|
| [GUIDE](GUIDE.md) · [CHECKPOINTS](CHECKPOINTS.md) | Các bước làm lab |
| [BENCHMARK](BENCHMARK.md) · [RUBRIC](RUBRIC.md) | Cách đo hai tầng và cách chấm |
| [Starter](starter/README.md) · [Data contract](data/README.md) | Khung agent, baseline và dữ liệu |
| [RULES](RULES.md) · [Pseudocode](PSEUDOCODE.md) | Quy tắc và khung triển khai |
