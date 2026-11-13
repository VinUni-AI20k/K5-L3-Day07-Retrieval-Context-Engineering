# Rubric Day 7 — 100 điểm

Chấm theo bằng chứng và khả năng tái lập, không dựa vào điểm tuyệt đối. Coding agent để hỗ trợ lập trình là tùy chọn; agentic RAG là sản phẩm bắt buộc.

| Hạng mục | Điểm | Bằng chứng |
|---|---:|---|
| Handoff và benchmark | 15 | Vector store/model/metadata Day 6 và truy vết (7); benchmark, evidence, split và câu thiếu evidence (8) |
| Retrieval | 20 | Dense, BM25, hybrid RRF trên cùng corpus/queries (12); ID, score, k, tương thích embedding, xử lý lỗi (8) |
| Agent và context | 20 | Model chọn/gọi tool thật, số lần giới hạn, trace và xử lý thiếu evidence (10); context budget, nguồn và citation (10) |
| Evaluation | 20 | Ba metric retrieval/context, trace, so sánh công bằng (10); agent tool use, grounded answer, citation, abstention và nhãn thủ công (10) |
| Cải thiện có kiểm soát | 15 | Phân tích lỗi/giả thuyết (4); dev selection và test (7); trade-off, giới hạn (4) |
| Tái lập và báo cáo | 10 | Setup, code, model/index, artifacts hoặc quyền truy cập (6); kết luận, nguồn, chi phí và trình bày (4) |
| **Tổng** | **100** | |

Không chấm thấp chỉ vì điểm retrieval thấp hoặc cải tiến không tăng. Không tính mock, vector giả, chạy lỗi hoặc test đã dùng để chỉnh như kết quả thực. Model có thể local hoặc API; không yêu cầu trả phí. Không bắt buộc cài coding agent hay plugin.
