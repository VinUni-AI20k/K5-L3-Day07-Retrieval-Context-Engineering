# Rubric Day 7 — tối đa 100 điểm

## Phần cơ bản — 85 điểm

| Hạng mục | Điểm | Bằng chứng |
|---|---:|---|
| Dữ liệu và benchmark | 13 | Kết nối Day 6, embedding và nguồn (6); câu hỏi, evidence và split (7) |
| Retrieval | 17 | Ít nhất 3 phương pháp khác nhau, gồm dense trên vector store Day 6 (10); cấu hình, nguồn, score/rank và xử lý lỗi (7) |
| Agent và context | 17 | Agent dùng model thật để truy xuất, trace tool và điều kiện dừng (9); chọn context, citation và xử lý thiếu evidence (8) |
| Đánh giá | 17 | Retrieval/context metrics và so sánh có thể kiểm chứng (9); đánh giá câu trả lời, citation, abstention và tool use (8) |
| Thử nghiệm và cải thiện | 13 | Ít nhất 2 cấu hình thử cải thiện, giả thuyết và phân tích lỗi (5); chọn trên dev, đánh giá test sau khi chốt (5); đánh đổi chất lượng, thời gian và chi phí (3) |
| Tái lập và báo cáo | 8 | Code, cách chạy, model và dữ liệu (5); kết luận, nguồn và giới hạn (3) |
| **Tổng cơ bản** | **85** | |

Không chấm theo một thuật toán, framework, số tool hay số lượt gọi cố định. Phần cơ bản không yêu cầu metric tuyệt đối; kết quả thấp vẫn được ghi nhận nếu thí nghiệm đúng và phân tích trung thực.

## Thử thách nâng cao — 15 điểm bonus

Index một tài liệu thực tế từ 100 trang có bảng, ảnh và biểu đồ; xây benchmark đa dạng theo [thử thách nâng cao](ADVANCED.md). **Được cộng 15 điểm** khi hoàn thành toàn bộ yêu cầu và đạt **ít nhất 90% số câu test** theo cách chấm trong thử thách. Không cộng một phần nếu chưa đạt điều kiện; tổng điểm toàn bài tối đa 100.

Không dùng kết quả mock hoặc test đã dùng để chỉnh làm đánh giá độc lập. Có thể dùng model trên máy hoặc API; không bắt buộc trả phí.
