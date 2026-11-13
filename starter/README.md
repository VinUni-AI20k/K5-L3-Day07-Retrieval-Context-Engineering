# Bộ khởi đầu Day 7

| File | Công dụng |
|---|---|
| `agentic.py` | Khung agent giới hạn 2 lần tìm và kiểm tra ID nguồn |
| `baseline.py` | Ví dụ tìm theo từ khóa TF-IDF, chạy không cần mạng |
| `convert_day6.py` | Chuyển một số trường JSON từ Day 6 |
| `agent_metrics.py` | Tổng hợp nhãn đánh giá do bạn tự chấm |

Bộ này **chưa phải lời giải hoàn chỉnh**. Bạn phải nối mô hình và kho vector thật, bổ sung tìm bằng vector, BM25 và RRF. Dữ liệu giả lập chỉ dùng để kiểm thử mã.

## 1. Kết nối agent

Trong `agentic.py`, hiện thực:

- `Controller.decide`: gọi mô hình thật và trả về `{action: "search", query: "..."}` hoặc `{action: "answer", answer: "... [chunk-id]", citations: ["chunk-id"]}`.
- `Retriever.search`: tạo vector câu hỏi tương thích Day 6, truy vấn kho thật và trả các đoạn theo [định dạng dữ liệu](../data/README.md).

Tự viết chương trình nối hai phần với `run_agent`. Xem `tests/test_agentic.py` để hiểu cách gọi; các kết nối trong đó là giả lập. Khung mã kiểm tra ID nguồn có trong nội dung đưa vào mô hình, nhưng bạn phải tự đọc xem nguồn có hỗ trợ câu trả lời. Báo lỗi kết nối, không thay bằng kết quả giả.

## 2. Chạy ví dụ tìm kiếm

Chạy từ thư mục gốc, với Python 3.11 trở lên:

```bash
python3 -m unittest discover -s tests -v
python3 starter/baseline.py --chunks data/example_chunks.json --questions data/example_questions.json --split dev --output starter/results/example-dev
```

Kết quả có `summary.json` và `traces.json`. Dữ liệu mẫu chỉ có một câu, không đủ để nộp bài. TF-IDF là tìm theo từ khóa, không dùng bộ lọc và không thay thế tìm bằng vector.

## 3. Dùng dữ liệu Day 6

Xuất đoạn tài liệu và câu hỏi thành hai danh sách JSON. Bộ khởi đầu Day 6 không quy định tên bảng hay cách xuất; bạn cần tự thực hiện. Nếu dùng các trường `chunk_id`, `document_id`, `source`, `page`, `text`, `metadata` và câu hỏi có `gold_source_id`, `gold_page`, `evidence_quote`, chạy:

```bash
python3 starter/convert_day6.py --chunks <day6_chunks.json> --questions <day6_questions.json> --output starter/data/converted
python3 starter/baseline.py --chunks starter/data/converted/chunks.json --questions starter/data/converted/questions.json --split dev --output starter/results/dev-tfidf
```

Thay phần trong `< >` bằng đường dẫn thật. Chương trình chỉ đổi tên trường, không tự truy cập cơ sở dữ liệu hay đoán bằng chứng. Nếu cấu trúc khác, tự viết phần chuyển đổi. Đối chiếu lại nguồn, trang và bằng chứng.

`--split dev` chỉ chấm tập phát triển. Sau khi chốt cấu hình, dùng `--split test` và chọn thư mục kết quả khác. Việc khớp nguyên văn trong mã không thay thế đọc và chấm thủ công.

## 4. Tổng hợp đánh giá agent

Sau khi chạy agent thật và tự chấm, chuẩn bị ba danh sách JSON:

- `cases.json`: mỗi câu có `id`, `split`, `answerable` (`true` nếu có đủ bằng chứng).
- `traces.json`: mỗi kết quả có `query_id`, `status` (`answered`, `abstain`, `error`), `events`, `citations`. Thêm `query_id` vào kết quả `run_agent`; lỗi kết nối ghi riêng với `status: "error"`.
- `reviews.json`: mỗi nhãn có `query_id`, `citation_support` là danh sách đúng/sai ứng với từng nguồn. Câu có đáp án cần thêm `answer_grade` 0–2 theo [BENCHMARK.md](../BENCHMARK.md); nếu bị từ chối, chấm 0. Lần chạy lỗi không cần nhãn.

```bash
python3 starter/agent_metrics.py --cases <cases.json> --traces <traces.json> --reviews <reviews.json> --split test --output starter/results/agent-test/summary.json
```

Chương trình tổng hợp nhãn bạn đã chấm, không tự đánh giá nội dung. Mẫu số bằng 0 nghĩa là không áp dụng. Lỗi kết nối được báo riêng, không tính vào chất lượng; giữ kết quả và nhãn để đối chiếu.

## Lưu ý

TF-IDF dùng cách tách từ đơn giản. Giới hạn nội dung là 800 ký tự, gồm cả nguồn; đoạn không vừa bị bỏ. File kết quả cùng tên sẽ bị ghi đè. `starter/data/` và `starter/results/` không được Git theo dõi mặc định; nếu được phép chia sẻ, dùng `git add -f <đường-dẫn>`, hoặc ghi cách tái tạo. Không nộp dữ liệu mật và khóa bí mật.
