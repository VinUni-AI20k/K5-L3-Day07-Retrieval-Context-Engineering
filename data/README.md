# Định dạng dữ liệu

Các file `example_*.json` chỉ minh họa định dạng, không đủ để nộp bài. Dữ liệu thật là danh sách JSON UTF-8; nếu dùng định dạng khác, ghi cách chuyển trong README.

- **Đoạn tài liệu:** `id`, `text`, `source_id`, `source`, `page`, `metadata`. ID phải duy nhất; giữ phiên bản hoặc ngày nếu có.
- **Câu có đáp án:** `id`, `split` (`dev` hoặc `test`), `question`, `expected_answer`, `gold`: danh sách `{source_id, page, evidence}`. Mỗi bằng chứng phải nằm trọn trong một đoạn đúng nguồn và trang. Có thể thêm `filter` do người dùng cung cấp trước.
- **Câu thiếu bằng chứng:** `id`, `split`, `question`, `answerable: false`, `expected_behavior: "search_and_abstain"`, `absence_reason`. Xem `agent_cases_example.json`.

Không đưa `gold` hoặc nhãn đáp án vào mô hình và công cụ tìm kiếm. Ghi nguồn dữ liệu và quyền sử dụng. Cách chuyển một số định dạng Day 6: [starter/README.md](../starter/README.md).
