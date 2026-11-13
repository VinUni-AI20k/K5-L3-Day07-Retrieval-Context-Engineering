# Thang điểm Day 7 — 100 điểm

Điểm dựa trên bằng chứng, cách thực hiện và khả năng chạy lại; không yêu cầu hệ thống đạt điểm tìm kiếm tuyệt đối. Agent tìm tài liệu là phần bắt buộc. Công cụ AI hỗ trợ viết mã là tùy chọn.

| Hạng mục | Điểm | Người chấm xem gì? |
|---|---:|---|
| Dữ liệu và bộ câu hỏi | 15 | Kết nối được kho vector Day 6, mô hình và nguồn tài liệu (7); câu hỏi, bằng chứng và cách chia tập hợp lệ (8) |
| Ba cách tìm kiếm | 20 | Tìm bằng vector, BM25 và kết hợp RRF trên cùng dữ liệu (12); ID, điểm, số kết quả, tính tương thích vector và xử lý lỗi (8) |
| Agent và thông tin trả lời | 20 | Mô hình thật chọn và gọi công cụ, có giới hạn và ghi lại các bước (10); giới hạn nội dung, nguồn trích dẫn và cách xử lý khi thiếu thông tin (10) |
| Đánh giá | 20 | Chỉ số tìm kiếm, thông tin đưa vào mô hình và cách so sánh công bằng (10); đánh giá gọi công cụ, câu trả lời, trích dẫn và từ chối, kèm nhãn thủ công (10) |
| Cải thiện có kiểm soát | 15 | Phân tích lỗi và giả thuyết (4); thử, chọn bằng tập phát triển và kiểm thử sau khi chốt (7); đánh đổi và giới hạn (4) |
| Chạy lại và báo cáo | 10 | Hướng dẫn, mã, cấu hình mô hình/kho và dữ liệu hoặc cách truy cập (6); kết luận, nguồn, chi phí và cách trình bày (4) |
| **Tổng** | **100** | |

Kết quả thấp hoặc một cải tiến không tăng điểm vẫn được ghi nhận nếu làm đúng và phân tích trung thực. Không dùng mô hình, vector hoặc kết quả giả lập để báo chất lượng; không báo tập đã dùng để chỉnh như tập kiểm thử độc lập. Có thể dùng mô hình chạy trên máy hoặc API, không bắt buộc dịch vụ trả phí.
