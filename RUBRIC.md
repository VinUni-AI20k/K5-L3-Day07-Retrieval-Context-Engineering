# Rubric Day 7 — 100 điểm

Chấm theo bằng chứng và thiết kế thí nghiệm, không dựa vào điểm retrieval tuyệt đối hoặc agent được chọn.

| Hạng mục | Điểm | Bằng chứng |
|---|---:|---|
| Handoff và benchmark | 15 | Chunks/metadata truy vết (6); ≥20 câu, evidence kiểm chứng, split và giữ test (9) |
| Retrieval | 20 | Ba baseline chạy và so sánh cùng input (12); scores, ID, k, xử lý lỗi đúng (8) |
| Context engineering | 15 | Budget, loại trùng, thứ tự và nguồn (10); xử lý không có/không vừa bằng chứng (5) |
| Evaluation | 20 | Hit@1, Evidence Hit@3, Context Hit và trace đúng theo split (12); nhãn thủ công, latency/chi phí và phân tích (8) |
| Cải thiện có kiểm soát | 15 | Lỗi và giả thuyết (4); thay đổi, dev selection, test (7); phân tích trade-off trung thực (4) |
| Coding agent và tái lập | 15 | Setup instruction/skill và kiểm tra MCP hoặc fallback có lý do, tìm hiểu plugin (6); bằng chứng prompt và tự kiểm chứng (4); README, artifacts, chạy lại (5) |
| **Tổng** | **100** | |

Không có dữ liệu/evidence/split hợp lệ hoặc không có trace chỉ chấm phần chứng minh được. Không chấm thấp vì cải tiến không tăng điểm; không coi test đã dùng chỉnh là holdout. Không yêu cầu trả phí, đăng nhập dịch vụ thứ ba, dùng dense model hoặc cài plugin để đạt điểm tối đa.
