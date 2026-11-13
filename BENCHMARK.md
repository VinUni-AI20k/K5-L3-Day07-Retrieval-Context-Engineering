# Đánh giá Day 7

Đánh giá riêng **tìm bằng chứng** và **agent trả lời**. Tìm đúng tài liệu không đảm bảo câu trả lời đúng.

## Bộ câu hỏi

| Loại câu | Tập phát triển | Tập kiểm thử |
|---|---:|---:|
| Có đáp án trong tài liệu | Ít nhất 15 | Ít nhất 5 |
| Không đủ bằng chứng | Ít nhất 2 | Ít nhất 2 |

Với câu có đáp án, ghi ID, câu hỏi, đáp án, nguồn, trang và đoạn bằng chứng nguyên văn. Kiểm tra bằng chứng nằm trong nguồn và trong một đoạn đã lưu. Nếu có nhiều bằng chứng thay thế hợp lệ, ghi tất cả; tìm được một là đủ.

Với câu thiếu bằng chứng, ghi cách kiểm tra trong bộ tài liệu. Không tính các câu này vào chỉ số tìm kiếm. Chia tập trước khi thử: dùng tập phát triển để chọn cấu hình, sau đó mới chạy tập kiểm thử. Không đưa đáp án chuẩn vào agent.

## Tìm kiếm và thông tin đưa vào mô hình

So sánh vector, BM25 và RRF trên cùng câu hỏi gốc, dữ liệu, bộ lọc đầu vào, 3 kết quả cuối và giới hạn 800 ký tự. Báo riêng nếu agent tự viết lại câu hỏi. Một đoạn đúng khi có **đúng nguồn, đúng trang và đủ bằng chứng**; bằng chứng tương đương cần được đọc và ghi lý do.

| Chỉ số | Cách tính trên câu có đáp án |
|---|---|
| Hit@1 | Số câu có bằng chứng đúng ở kết quả đầu / tổng số câu |
| Evidence Hit@3 | Số câu có bằng chứng đúng trong 3 kết quả đầu / tổng số câu |
| Context Evidence Hit@3 | Số câu còn bằng chứng đúng trong thông tin đưa vào mô hình / tổng số câu |

Báo số câu và tỷ lệ cho từng cách, riêng từng tập. Ví dụ: `12/15 = 80%`. Chỉ số cuối không thể lớn hơn Hit@3. Lưu câu hỏi, kết quả, điểm, nguồn, trang, nhãn, nội dung đưa vào mô hình, thời gian và chi phí.

Đọc cùng 5 câu kiểm thử cho cách ban đầu và cách cải thiện. Chấm nội dung đưa vào mô hình: **0** không có bằng chứng; **1** có nhưng thiếu điều kiện hoặc nguồn; **2** đủ bằng chứng và nguồn. Ghi lý do và số câu mỗi mức.

## Agent và câu trả lời

Chạy agent thật với cách tìm đã chọn. Ghi mô hình, từng lần gọi công cụ và tham số, kết quả, nội dung đưa vào mô hình, câu trả lời, nguồn, thời gian và lỗi. Tối đa 2 lần tìm mỗi câu. Đọc thủ công ít nhất 5 câu kiểm thử có đáp án và 2 câu thiếu bằng chứng.

| Nội dung | Cách đánh giá |
|---|---|
| Gọi công cụ | Số câu có gọi tìm kiếm / số câu chạy thành công; kiểm tra thêm tham số và số lần gọi. |
| Độ đúng câu trả lời | Với câu có đáp án: 0 = sai hoặc không có bằng chứng; 1 = đúng một phần; 2 = đúng và đủ. Báo số câu mỗi mức và trung bình /2. Từ chối câu có đáp án được chấm 0. |
| Nguồn hợp lệ | Số trích dẫn có trong nội dung gửi cho mô hình **và** hỗ trợ câu trả lời / tổng trích dẫn. Nếu không có trích dẫn, báo `0/0 (không áp dụng)`; báo thêm số câu trả lời có nguồn / số câu trả lời. |
| Từ chối | Số câu thiếu bằng chứng được từ chối / tổng câu thiếu bằng chứng; báo thêm số câu có đáp án bị từ chối / tổng câu có đáp án. |

Báo kết quả riêng từng tập và nhãn từng câu, từng nguồn. Lỗi mô hình hoặc kho dữ liệu phải được đếm riêng, không tính là từ chối đúng. Kiểm tra ID nguồn thôi chưa đủ: người chấm phải đọc xem nguồn có hỗ trợ câu trả lời không.

[Chương trình tổng hợp](starter/README.md#4-tổng-hợp-đánh-giá-agent) dùng nhãn do bạn tự chấm; không tự chạy hay chấm agent. Ghi ít nhất hai lỗi, giả thuyết, kết quả trước/sau và giới hạn trong [báo cáo](report/individual/MSSV_HoTen.md).
