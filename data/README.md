# Data contract

`example_chunks.json` và `example_questions.json` chỉ là fixture một câu, không đủ điều kiện nộp. Các file thật là JSON array UTF-8; tên/format có thể khác nếu README chỉ rõ adapter.

Chunk: `id` duy nhất ổn định, `text` nguyên văn đã chuẩn hóa, `source_id`, `source` (đường dẫn/URL hoặc ID được phép), `page` (số trang hoặc page ID), `metadata` (object). Giữ version/date nếu có. Bằng chứng cần được chứa đầy đủ trong ít nhất một chunk; nhiều evidence có thể nằm ở các chunk khác nhau.

Question: `id`, `split` (`dev`/`test`), `question`, `gold` là danh sách các object `{source_id,page,evidence}` chứa các bằng chứng thay thế đầy đủ, `expected_answer`; `filter` tùy chọn là metadata người dùng cung cấp trước, không phải gold. ID câu duy nhất. Ghi manifest và nguồn gốc mỗi trường; không đoán metadata. Trace cần giữ đủ text/source/page, score và context sau packing.

Với JSON xuất từ dataclass và benchmark mẫu Day 6, xem adapter và các giới hạn tại [starter/README.md](../starter/README.md). Schema lưu trong database do từng bài Day 6 tự thiết kế, nên bạn cần tự xuất dữ liệu trước.

**Case agent thiếu evidence:** thêm ít nhất 2 dev / 2 test riêng, mỗi case có `id`, `split`, `question`, `answerable: false`, `expected_behavior: "search_and_abstain"`, `absence_reason`; xem `agent_cases_example.json` (chỉ fixture). Giữ nhãn/gold ngoài model và tool. Case answerable dùng benchmark chính; agent case không thay thế 20 câu có evidence.
