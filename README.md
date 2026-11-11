# Day 7 — Retrieval & Context Engineering

### Từ câu hỏi đến bằng chứng

**Bài cá nhân · 4 giờ · Python 3.11+ · tiếp nối Day 6**

Sử dụng chunks, metadata và benchmark từ Day 6 để tìm bằng chứng phù hợp cho một câu hỏi. Bạn sẽ so sánh các chiến lược retrieval, tạo context có thể truy nguồn và cải thiện pipeline dựa trên kết quả đánh giá.

> **Gợi ý tùy chọn:** Dùng coding agent để hỗ trợ lập trình? Xem [best practices về instruction, skill, MCP và plugin](AGENT_SETUP.md). Phần này không bắt buộc và không tính điểm.

## Bạn sẽ làm gì?

![Pipeline từ dữ liệu Day 6 qua retrieval đến context có nguồn](assets/retrieval-pipeline.svg)

1. **Chuẩn bị dữ liệu:** chuyển chunks và benchmark Day 6 theo [data contract](data/README.md), giữ ID, nguồn, trang và evidence. Nếu chưa có đầu ra Day 6, làm theo hướng dẫn chuẩn bị dữ liệu trong [GUIDE](GUIDE.md).
2. **So sánh retrieval:** chạy TF-IDF + cosine, BM25 và RRF trên cùng chunks và câu hỏi. Có thể dùng dense embedding thật thay TF-IDF.
3. **Tạo context:** chọn top-3, loại trùng, giữ nguồn/trang và tuân thủ budget 800 ký tự.
4. **Đánh giá và cải thiện:** đo Hit@1, Evidence Hit@3 và Context Evidence Hit@3; phân tích lỗi, thử một cải tiến trên dev rồi đánh giá cấu hình đã chọn trên test.

TF-IDF là phương pháp lexical. RRF kết hợp TF-IDF và BM25 là kết hợp hai phương pháp lexical; xem [GUIDE](GUIDE.md) để biết chi tiết và tiêu chí đánh giá.

## Quy trình thực nghiệm

![Vòng lặp baseline, phân tích lỗi, cải tiến trên dev và đánh giá test](assets/experiment-loop.svg)

Giữ test độc lập trong lúc thử nghiệm và chọn cấu hình. Một cải tiến không tăng điểm vẫn có giá trị nếu bạn phân tích và báo cáo trung thực.

## Bắt đầu

1. Fork hoặc clone repo và tạo repo bài làm cá nhân theo [SUBMISSION](SUBMISSION.md).
2. Chuẩn bị Python 3.11+ và dữ liệu Day 6; xem [GUIDE](GUIDE.md) và [CHECKPOINTS](CHECKPOINTS.md) để làm bài theo từng bước. Có thể làm offline, không cần API key hay chatbot.
3. Kiểm tra fixture mẫu:

   ```bash
   python -m unittest discover -s tests -v
   ```

   Các file `data/example_*.json` chỉ minh họa schema, không phải benchmark đủ điều kiện nộp.

## Nộp bài và tài liệu

Nộp code, cấu hình, dữ liệu được phép chia sẻ hoặc cách tái tạo, benchmark và gold, trace, kết quả dev/test, nhãn đánh giá và [báo cáo cá nhân](report/individual/MSSV_HoTen.md). Xem checklist đầy đủ tại [SUBMISSION](SUBMISSION.md).

| Tài liệu | Nội dung |
|---|---|
| [GUIDE](GUIDE.md) · [CHECKPOINTS](CHECKPOINTS.md) | Hướng dẫn thực hành và các mốc 4 giờ |
| [RUBRIC](RUBRIC.md) · [RULES](RULES.md) | Cách chấm và quy tắc làm bài |
| [Data contract](data/README.md) · [Pseudocode](PSEUDOCODE.md) | Định dạng dữ liệu và khung triển khai |
