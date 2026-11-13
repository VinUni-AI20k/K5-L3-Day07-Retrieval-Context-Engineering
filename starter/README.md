# Bộ khởi đầu Day 7

Bộ này giúp bạn bắt đầu bài thực hành. Nó gồm:

| Thành phần | Đã làm gì? | Bạn cần làm tiếp |
|---|---|---|
| `agentic.py` | Khung agent giới hạn 2 lần tìm kiếm và kiểm tra ID nguồn trích dẫn | Kết nối mô hình thật và kho dữ liệu Day 6 |
| `baseline.py` | Một cách tìm kiếm theo từ khóa bằng TF-IDF, chạy được không cần mạng | Bổ sung tìm bằng vector, BM25 và kết hợp RRF |
| `convert_day6.py` | Đổi tên một số trường dữ liệu Day 6 sang định dạng Day 7 | Xuất dữ liệu từ hệ thống của bạn và kiểm tra kết quả chuyển đổi |
| `agent_metrics.py` | Tổng hợp các nhãn đánh giá đã được con người chấm | Chạy agent thật và tự chấm câu trả lời, nguồn trích dẫn |

**Lưu ý:** Đây chưa phải hệ thống Agentic RAG hoàn chỉnh. Các kết nối giả lập trong bài kiểm thử chỉ để kiểm tra mã, không dùng để báo cáo chất lượng agent. Tìm kiếm TF-IDF không phải tìm kiếm bằng vector ngữ nghĩa và không thay thế ba cách tìm bắt buộc.

## 1. Kết nối agent

Trong `agentic.py`, bạn cần hiện thực hai phần:

- **`Controller.decide`** gọi mô hình thật có khả năng chọn công cụ. Chuyển yêu cầu tìm kiếm của mô hình thành `{action: "search", query: "..."}`; chuyển câu trả lời cuối thành `{action: "answer", answer: "... [chunk-id]", citations: ["chunk-id"]}`.
- **`Retriever.search`** tạo vector cho câu hỏi bằng mô hình tương thích với Day 6, truy vấn kho vector thật và trả về các đoạn theo [định dạng dữ liệu](../data/README.md).

Sau đó tự viết chương trình kết nối hai phần này với `run_agent`. Xem `tests/test_agentic.py` để hiểu cách gọi; dữ liệu giả trong file kiểm thử không phải kết nối thật.

Khung vòng lặp ghi lại các lần tìm, giới hạn nội dung tích lũy và từ chối câu trả lời không có ID nguồn hợp lệ. Bạn vẫn cần tự kiểm tra **nội dung nguồn có hỗ trợ câu trả lời hay không**. Khi mô hình hoặc kho dữ liệu lỗi, ghi lỗi riêng; không tự thay bằng dữ liệu giả.

## 2. Chạy ví dụ TF-IDF

Chạy từ thư mục gốc của repo, với Python 3.11 trở lên:

```bash
python3 -m unittest discover -s tests -v
python3 starter/baseline.py --chunks data/example_chunks.json --questions data/example_questions.json --split dev --output starter/results/example-dev
```

Chương trình ghi `summary.json` và `traces.json`: tổng số câu, số câu tìm đúng, nội dung và nguồn tìm được, phần thông tin được giữ lại và thời gian chạy. Muốn tính tỷ lệ, lấy số câu tìm đúng chia tổng số câu.

Hai file trong `data/example_*.json` chỉ có một ví dụ để kiểm tra định dạng, **không đủ điều kiện làm bộ câu hỏi nộp bài**. Cách tìm TF-IDF không sử dụng bộ lọc trong dữ liệu; hãy ghi rõ nếu bạn dùng nó để đối chiếu.

## 3. Dùng dữ liệu Day 6

Trước hết, xuất một bộ đoạn tài liệu và bộ câu hỏi từ hệ thống Day 6 thành hai file JSON. Mỗi file là một danh sách. Bộ khởi đầu Day 6 không quy định tên bảng hay cách xuất dữ liệu từ cơ sở dữ liệu, vì vậy bạn phải tự hoàn thành bước xuất này.

Nếu dữ liệu dùng các trường `chunk_id`, `document_id`, `source`, `page`, `text`, `metadata` và câu hỏi dùng `gold_source_id`, `gold_page`, `evidence_quote`, chạy:

```bash
python3 starter/convert_day6.py --chunks <day6_chunks.json> --questions <day6_questions.json> --output starter/data/converted
python3 starter/baseline.py --chunks starter/data/converted/chunks.json --questions starter/data/converted/questions.json --split dev --output starter/results/dev-tfidf
```

Thay nội dung trong `< >` bằng đường dẫn thật và bỏ dấu `< >`. Chương trình chuyển đổi chỉ đổi tên các trường nêu trên; không tự truy cập PostgreSQL hoặc đoán nguồn, trang và bằng chứng. Nếu dữ liệu của bạn có cấu trúc khác, tự viết phần chuyển đổi. Kiểm tra lại từng nguồn, trang và đoạn bằng chứng theo [quy định dữ liệu](../data/README.md).

Lệnh trên chỉ đánh giá **tập phát triển** (`dev`). Sau khi đã chốt cấu hình, dùng `--split test` để đánh giá tập kiểm thử và chọn thư mục kết quả khác. Nếu tập kiểm thử Day 6 từng được dùng để chỉnh hệ thống, tạo tập kiểm thử mới theo [GUIDE.md](../GUIDE.md).

Chương trình kiểm tra xem bằng chứng có nằm nguyên văn trong một đoạn đúng nguồn và trang hay không. Việc này không chứng minh đoạn đó đã đủ ngữ cảnh; bạn vẫn cần đọc và đánh giá thủ công.

## 4. Tổng hợp kết quả đánh giá agent

Sau khi chạy agent thật và tự chấm, chuẩn bị ba file JSON:

- `cases.json`: danh sách câu hỏi, mỗi câu có `id`, `split` và `answerable` (`true` nếu có đủ bằng chứng, `false` nếu không). Giữ đáp án chuẩn riêng, không gửi cho agent.
- `traces.json`: mỗi kết quả có `query_id`, `status` (`answered`, `abstain` hoặc `error`), `events` và `citations`. Có thể thêm `query_id` vào kết quả của `run_agent`. Nếu kết nối lỗi, ghi `status: "error"` cùng thông tin lỗi đã loại bỏ dữ liệu nhạy cảm.
- `reviews.json`: mỗi nhãn có `query_id` và `citation_support`, là danh sách giá trị đúng/sai cho từng trích dẫn theo đúng thứ tự. Với câu có đáp án, thêm `answer_grade` là 0, 1 hoặc 2 theo [BENCHMARK.md](../BENCHMARK.md). Câu có đáp án nhưng bị từ chối được chấm 0. Không cần chấm nội dung cho lần chạy bị lỗi kết nối.

```bash
python3 starter/agent_metrics.py --cases <cases.json> --traces <traces.json> --reviews <reviews.json> --split test --output starter/results/agent-test/summary.json
```

Thay đường dẫn trong `< >` như trên. Chương trình báo số câu đạt và tổng số câu; mẫu số bằng 0 là **không áp dụng**, không phải 100%. Lỗi kết nối được đếm riêng và loại khỏi mẫu đánh giá chất lượng, nên cần báo cả số lỗi và tổng số câu. Giữ lại kết quả và nhãn để người chấm đối chiếu.

## Giới hạn cần biết

- TF-IDF dùng cách tách từ đơn giản, chưa tối ưu cho tiếng Việt. Điểm dương được sắp giảm dần; nếu điểm bằng nhau, sắp theo ID.
- Phần thông tin đưa vào mô hình có giới hạn 800 ký tự, bao gồm tên nguồn và dấu phân cách. Đoạn không vừa sẽ bị bỏ, không bị cắt; kết quả có thể rỗng.
- Thời gian dựng chỉ mục và thời gian tìm kiếm được đo riêng. Không so sánh thời gian giữa các máy như phép đo hiệu năng sản xuất.
- File cùng tên trong thư mục kết quả sẽ bị ghi đè. `starter/data/` và `starter/results/` không được Git theo dõi mặc định để tránh vô tình tải dữ liệu lên. Nếu được phép chia sẻ, chọn file cần nộp và dùng `git add -f <đường-dẫn>`; nếu không, ghi cách tái tạo hoặc cấp quyền trong README. Không nộp khóa bí mật hoặc dữ liệu mật.
