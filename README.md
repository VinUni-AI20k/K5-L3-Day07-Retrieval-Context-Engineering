# Day 7 — Agentic RAG

**Bài cá nhân · 4 giờ · Python 3.11+ · tiếp nối Day 6**

Dùng lại embedding và vector store từ Day 6 để xây agent biết tìm tài liệu, trả lời có nguồn hoặc nói rõ khi không đủ bằng chứng. Thời lượng 4 giờ tính từ khi dữ liệu, vector store và model đã sẵn sàng.

> **Tùy chọn:** Xem [gợi ý dùng AI để lập trình](AGENT_SETUP.md). Phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối lại chunk, embedding model và vector store Day 6.
2. Xây agent dùng model thật, có retrieval tool và trả lời kèm nguồn.
3. So sánh dense retrieval, BM25 và kết hợp hai cách bằng RRF.
4. Đánh giá, phân tích lỗi, cải thiện trên tập **dev**, rồi chạy tập **test**.

Benchmark gồm ít nhất **24 câu**: 17 câu dev (15 câu có đáp án, 2 câu thiếu bằng chứng) và 7 câu test (5 câu có đáp án, 2 câu thiếu bằng chứng). Xem [cách đánh giá](BENCHMARK.md).

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [các mốc](CHECKPOINTS.md) và [rubric](RUBRIC.md).
2. Tạo repo cá nhân theo [hướng dẫn nộp bài](SUBMISSION.md). Chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Xem [starter](starter/README.md). Bạn cần tự nối model và vector store thật; starter chưa phải solution hoàn chỉnh.
4. Chạy `python -m unittest discover -s tests -v`. Test dùng kết nối giả lập chỉ kiểm tra code, **không phải kết quả benchmark agent thật**.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

## Nộp bài

Nộp code, cách chạy, dữ liệu hoặc cách truy cập, benchmark, kết quả từng câu, nhãn đánh giá và [báo cáo](report/individual/MSSV_HoTen.md). Xem [danh sách nộp bài](SUBMISSION.md) và [quy tắc](RULES.md).
