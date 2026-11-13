# Baseline Day 7 — TF-IDF + context

Baseline **tùy chọn** chạy offline với Python 3.11+, không cần database, thư viện ngoài hay API key. Pipeline đọc chunks → TF-IDF cosine → top-3 → đóng gói context → lưu trace và metrics. Đây là một **lexical baseline**, không phải dense embedding hay lời giải hoàn chỉnh.

Phần bạn vẫn phải làm: bổ sung **BM25 và RRF** (hoặc thay TF-IDF bằng dense embedding thật theo GUIDE), so sánh ba chiến lược, cải thiện một yếu tố trên dev, đánh giá test sau khi chốt và audit thủ công. TF-IDF baseline không sử dụng filter; filter trong dữ liệu được giữ nhưng **không áp dụng**. Ghi điều này khi so sánh.

## 1. Chạy smoke test với fixture

Chạy các lệnh sau từ **root repo**, không phải thư mục `starter/`:

```bash
python3 -m unittest discover -s tests -v
python3 starter/baseline.py --chunks data/example_chunks.json --questions data/example_questions.json --split dev --output starter/results/example-dev
```

Output gồm `summary.json` và `traces.json`. Summary báo số câu đúng (`hit1`, `hit3`, `context_hit`) và tổng `n`; lấy tử số chia `n` để ra tỷ lệ. Trace ghi câu hỏi, gold, top-3 ID/text/score/source/page, nhãn exact match, context/ID đã giữ và thời gian. Fixture chỉ có một câu, **không phải benchmark nộp bài**.

## 2. Dùng dữ liệu Day 6

Xuất một cấu hình chunk đã chọn và benchmark Day 6 thành hai JSON arrays UTF-8. Starter Day 6 là khung TODO, không quy định tên bảng hay lệnh export database: bạn tự hoàn thiện và xuất từ hệ thống của mình. Với schema dataclass Day 6 (`chunk_id`, `document_id`, `source`, `page`, `text`, `metadata`) và câu hỏi Day 6 (`gold_source_id`, `gold_page`, `evidence_quote`):

```bash
python3 starter/convert_day6.py --chunks <day6_chunks.json> --questions <day6_questions.json> --output starter/data/converted
python3 starter/baseline.py --chunks starter/data/converted/chunks.json --questions starter/data/converted/questions.json --split dev --output starter/results/dev-tfidf
```

Thay các placeholder bằng **đường dẫn thật**, bỏ dấu `< >`. Adapter chỉ đổi tên các trường đã nêu; không truy cập PostgreSQL hay tự suy ra nguồn/trang, metadata, filter hoặc evidence. Nếu schema khác, tự viết adapter và ghi lại cách ánh xạ. Kiểm tra output đối chiếu nguồn gốc, quyền dữ liệu và từng evidence. Nếu có nhiều gold thay thế dùng schema `gold` trong [data contract](../data/README.md). Với dữ liệu đã đúng schema Day 7 có thể chạy `baseline.py` trực tiếp, không cần chuyển đổi.

Kiểm tra evidence thực sự đủ trả lời và nằm trong nguồn gốc; kiểm tra bằng code chỉ xác nhận exact substring trong chunk đúng nguồn/trang, không chứng minh đủ ngữ cảnh. Validation từ chối gold thiếu hoặc không xuất hiện trọn trong một chunk. Giữ nguyên split/ID và không đưa gold vào truy vấn. Khi chạy **dev**, code chỉ kiểm tra/chấm câu dev; sau khi cố định chiến lược và quy tắc chọn, chạy test với `--split test` vào **thư mục output khác**. Nếu test Day 6 đã dùng để chỉnh pipeline, tạo test mới theo GUIDE.

## 3. Hiểu giới hạn và mở rộng

- Tokenizer dùng Unicode NFC, casefold và `\w+`; không có bộ tách từ tiếng Việt chuyên dụng. TF-IDF fit trên cùng tập chunks, cosine trả kết quả có score dương, hòa điểm theo ID. Không dùng gold hoặc filter khi search.
- Budget là 800 ký tự Python, tính cả header và dấu phân cách. Chunk không vừa được bỏ qua thay vì cắt; có thể trả context rỗng. Hit@1 / Hit@3 cần đủ evidence đúng nguồn/trang; context hit chỉ tính chunk thực sự được giữ. Dùng cùng k/budget cho tất cả chiến lược.
- Baseline chỉ chấm khớp chuỗi, không đánh giá evidence tương đương hoặc chất lượng grounding thủ công. Audit các trường hợp tương đương và báo phương pháp/nhãn riêng theo GUIDE.
- `elapsed_ms` đo search + packing cho từng query; `index_seconds` đo dựng index trong bộ nhớ; chi phí dịch vụ bằng 0. Không so sánh latency giữa các máy như benchmark sản xuất.
- Không âm thầm dùng dữ liệu giả cho thí nghiệm; các file cùng tên trong `--output` bị ghi đè. `starter/data/` và `starter/results/` được ignore để tránh vô tình commit corpus hoặc output; nếu được phép chia sẻ, chọn các artifacts cần nộp và dùng `git add -f <đường-dẫn-được-phép>` nếu cần, hoặc ghi cách tái tạo trong README. Không commit dữ liệu mật hay secret.
