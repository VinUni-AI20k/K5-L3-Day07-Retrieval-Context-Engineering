# Cách đánh giá Day 7

Đánh giá hai phần riêng: **khả năng tìm bằng chứng** và **hành vi của agent khi trả lời**. Tìm được tài liệu liên quan chưa đủ để kết luận câu trả lời đúng.

## 1. Chuẩn bị câu hỏi

Tạo ít nhất 24 câu và chia trước khi thử nghiệm:

| Loại câu | Tập phát triển | Tập kiểm thử | Dùng để làm gì? |
|---|---:|---:|---|
| Có đáp án trong tài liệu | Ít nhất 15 | Ít nhất 5 | Đánh giá tìm kiếm và câu trả lời |
| Không có đủ bằng chứng | Ít nhất 2 | Ít nhất 2 | Kiểm tra agent có nói không đủ thông tin |

Với mỗi câu có đáp án, ghi ID câu hỏi, câu hỏi, đáp án mong đợi, ID nguồn, trang và đoạn bằng chứng nguyên văn. Nếu có nhiều đoạn bằng chứng thay thế hợp lệ, ghi tất cả; tìm được một trong số đó là đủ. Kiểm tra từng đoạn thực sự nằm trong nguồn và nằm trọn trong một đoạn dữ liệu đã lưu.

Với câu thiếu bằng chứng, ghi lý do và cách kiểm tra trong bộ tài liệu hiện có. Không đưa các câu này vào mẫu số của các chỉ số tìm kiếm ở mục 2.

**Tập phát triển** dùng để tìm lỗi, thử và chọn cấu hình. **Tập kiểm thử** chỉ dùng sau khi đã chốt. Nếu tập kiểm thử Day 6 từng được dùng để chỉnh hệ thống, hãy tạo tập mới. Không đưa đáp án chuẩn vào câu hỏi, bộ lọc hay thông tin gửi cho mô hình.

## 2. Đánh giá tìm kiếm và thông tin đưa cho mô hình

Chạy ba cách tìm kiếm bằng **cùng câu hỏi gốc**: tìm bằng vector, BM25 và kết hợp bằng RRF. Dùng cùng dữ liệu, bộ lọc được cung cấp từ trước, 3 kết quả cuối và giới hạn 800 ký tự. Nếu thử cho agent tự viết lại câu hỏi, báo cáo kết quả đó riêng.

Một đoạn được tính là **tìm đúng bằng chứng** khi nó thuộc nguồn và trang chuẩn, đồng thời chứa đầy đủ đoạn bằng chứng. Có thể công nhận bằng chứng tương đương sau khi đọc và ghi lý do.

| Chỉ số | Cách tính trên các câu có đáp án |
|---|---|
| Hit@1 | Số câu có bằng chứng đúng ở kết quả đầu tiên / tổng số câu |
| Evidence Hit@3 | Số câu có ít nhất một bằng chứng đúng trong 3 kết quả đầu / tổng số câu |
| Context Evidence Hit@3 | Số câu còn bằng chứng đúng trong phần thông tin thực sự đưa cho mô hình / tổng số câu |

Ví dụ: nếu 12 trong 15 câu có bằng chứng đúng ở 3 kết quả đầu, Evidence Hit@3 là **12/15 = 80%**. Báo cả số câu và tỷ lệ cho từng cách tìm, riêng tập phát triển và kiểm thử. Chỉ số thứ ba không thể lớn hơn chỉ số thứ hai.

Lưu câu hỏi, kết quả, điểm, ID, nguồn, trang, bằng chứng chuẩn, nhãn đúng/sai, phần thông tin cuối cùng, độ dài, thời gian và chi phí. Đọc thủ công cùng 5 câu kiểm thử cho cách ban đầu và cách cải thiện; chấm thông tin đưa vào mô hình: **0** không có bằng chứng; **1** có nhưng thiếu điều kiện hoặc nguồn; **2** đủ bằng chứng và truy được nguồn. Ghi lý do và số câu ở mỗi mức.

## 3. Đánh giá agent và câu trả lời

Sau khi chọn cách tìm kiếm bằng tập phát triển, chạy agent trên cả hai loại câu hỏi. Lưu tên mô hình, cấu hình, từng lần gọi công cụ và tham số, kết quả trả về, thông tin thực sự đưa cho mô hình, câu trả lời, nguồn trích dẫn, thời gian và lỗi. Mỗi câu được gọi công cụ tìm kiếm tối đa 2 lần.

Đọc thủ công toàn bộ **5 câu kiểm thử có đáp án và ít nhất 2 câu thiếu bằng chứng**. Báo riêng các lần lỗi mô hình hoặc kho dữ liệu; không tính chúng là từ chối đúng.

| Nội dung đánh giá | Cách tính hoặc chấm |
|---|---|
| **Gọi công cụ** | Số câu agent gọi tìm kiếm ít nhất một lần / số câu đã chạy thành công. Đọc thêm tham số và số lần gọi. |
| **Độ đúng của câu trả lời** | Với câu có đáp án: 0 = sai hoặc không có bằng chứng; 1 = đúng một phần hoặc thiếu điều kiện; 2 = đúng và đủ theo nguồn. Báo số câu mỗi mức và điểm trung bình trên 2. Câu bị từ chối được chấm 0 ở mục này. |
| **Nguồn trích dẫn hợp lệ** | Số trích dẫn vừa có trong thông tin gửi cho mô hình, vừa hỗ trợ nội dung được dẫn / tổng số trích dẫn. Nếu không có trích dẫn, báo `0/0 (không áp dụng)`; báo thêm số câu trả lời có trích dẫn / số câu trả lời. |
| **Từ chối đúng** | Số câu thiếu bằng chứng mà agent nói không đủ thông tin / tổng số câu thiếu bằng chứng. Báo thêm số câu có đáp án nhưng bị từ chối / tổng số câu có đáp án. |

Ghi nhãn và lý do cho từng câu và từng nguồn trích dẫn. ID nguồn xuất hiện trong phần thông tin gửi cho mô hình **không tự chứng minh** nguồn đó hỗ trợ câu trả lời.

[starter/agent_metrics.py](starter/README.md#4-tổng-hợp-kết-quả-đánh-giá-agent) giúp tổng hợp các nhãn đã được con người kiểm tra. Chương trình không tự chạy agent thật hoặc tự chấm độ đúng của câu trả lời. Kết quả từ kết nối giả lập chỉ dùng để kiểm thử mã, không dùng để báo cáo chất lượng agent.

## 4. Phân tích và báo cáo

Nêu ít nhất hai câu bị lỗi trên tập phát triển, giả thuyết về nguyên nhân và thay đổi bạn đã thử. Ghi cấu hình đã chọn, kết quả trước/sau, thời gian, chi phí và giới hạn của bộ câu hỏi. Tham khảo [mẫu báo cáo](report/individual/MSSV_HoTen.md) và [thang điểm](RUBRIC.md).
