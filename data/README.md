# Định dạng dữ liệu

Các file `example_*.json` chỉ minh họa định dạng, không đủ để nộp bài. Dữ liệu thật là JSON array UTF-8; nếu dùng định dạng khác, ghi cách chuyển trong README.

- **Chunk:** `id`, `text`, `source_id`, `source`, `page`, `metadata`. ID phải duy nhất; giữ phiên bản hoặc ngày nếu có.
- **Câu có đáp án:** `id`, `split` (`dev` hoặc `test`), `question`, `expected_answer`, `gold`: danh sách `{source_id, page, evidence}`. Với schema mẫu, mỗi evidence phải nằm trọn trong một chunk đúng nguồn và trang; các phần tử `gold` là evidence thay thế. Với câu multi-hop cần nhiều đoạn, bạn có thể mở rộng schema, ghi rõ nhóm evidence bắt buộc và cách chấm. Có thể thêm `filter` do người dùng cung cấp trước.
- **Câu thiếu evidence:** `id`, `split`, `question`, `answerable: false`, `expected_behavior: "search_and_abstain"`, `absence_reason`. Xem `agent_cases_example.json`.

Không đưa `gold` hoặc nhãn đáp án vào model và retrieval tool. Ghi nguồn dữ liệu và quyền sử dụng. Cách chuyển một số định dạng Day 6: [starter/README.md](../starter/README.md).

## Dữ liệu thật (Day 6 -> Day 7)

Tạo lại bằng `python scripts/export_data.py` (thêm `--verify-chroma` với Python của `.venv` (Day 7) để so text với Chroma):

- `chunks.json`: 241 chunk collection `soc3e_B`, ID Day 6 thật (`B-soc3e-p0171-003`), `page` = trang PDF, chapter/section/... nằm trong `metadata`.
- `questions.json`: 24 câu có đáp án (`gold` có thêm `chunk_id`, `type`, `evidence_mode`; multi-hop liệt kê đủ evidence, `evidence_mode: "all"` nghĩa là cần tất cả, còn `baseline.py` chấm như thay thế). `filter` = `{}` vì benchmark không có filter do người dùng cung cấp. 6 câu thiếu evidence không nằm ở đây (baseline yêu cầu `gold` không rỗng).
- `agent_cases.json`: 30 câu (24 có đáp án, 6 `answerable: false` kèm `absence_reason`).

**`data/questions.json` chứa gold, chỉ dành cho evaluator.** Agent/retrieval chỉ được đọc `benchmark/questions.json` (không có gold).

Nguồn: OpenStax *Introduction to Sociology 3e*, CC BY 4.0 (https://openstax.org), trích đoạn chương 5-7; cần giữ ghi nguồn khi chia sẻ.
