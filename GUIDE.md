# Hướng dẫn Day 7

## 1. Chuẩn bị

Dùng lại một phiên bản dữ liệu Day 6: đoạn tài liệu, ID, nguồn, trang, kho vector và mô hình tạo vector. Ghi phiên bản, số chiều và cách kết nối. Vector câu hỏi phải dùng mô hình tương thích; nếu đổi mô hình, hãy tạo lại kho vector.

Nếu chưa hoàn thành Day 6, tự tạo dữ liệu, vector thật và kho lưu trữ trước. Nếu chưa có tài liệu, chuẩn bị ít nhất 30 trang nội dung hợp lệ. Không dùng vector ngẫu nhiên để đánh giá.

Chuẩn bị câu hỏi và chia tập theo [BENCHMARK.md](BENCHMARK.md). Nếu đã dùng tập kiểm thử Day 6 để chỉnh hệ thống, tạo tập kiểm thử mới. Không đưa đáp án hay nguồn chuẩn vào câu hỏi hoặc mô hình.

## 2. Tìm tài liệu

Viết công cụ `search(query, filters, top_k)` trả về ID, nội dung, điểm, nguồn, trang và thông tin mô tả. Chỉ dùng bộ lọc do người dùng cung cấp từ trước.

So sánh trên cùng dữ liệu và câu hỏi:

1. **Vector:** tạo vector câu hỏi và tìm trong kho Day 6.
2. **BM25:** tìm theo từ khóa trên cùng các đoạn; ghi cách tách từ tiếng Việt.
3. **Kết hợp RRF:** lấy tối đa 10 kết quả mỗi cách, gộp theo thứ hạng và chọn 3 kết quả đầu. Điểm RRF là tổng `1 / (60 + thứ_hạng)`, tính từ 1.

Không cộng trực tiếp điểm vector và BM25. TF-IDF chỉ là đối chứng theo từ khóa, không thay tìm kiếm bằng vector thật.

## 3. Xây agent

Dùng mô hình thật quyết định gọi công cụ tìm kiếm, tối đa **2 lần mỗi câu**. Sau khi nhận tài liệu, agent trả lời kèm `[chunk-id]` hoặc nói không đủ bằng chứng.

Thông tin đưa vào mô hình tối đa **800 ký tự**, gồm cả nguồn và dấu phân cách. Loại đoạn trùng ID; bỏ đoạn không vừa thay vì cắt; giữ nguồn và trang. Lưu từng lần gọi, kết quả, nội dung đưa vào mô hình, câu trả lời và nguồn trích dẫn.

Nội dung tìm được là dữ liệu, không phải chỉ dẫn cho agent. Báo lỗi mô hình hoặc kho dữ liệu riêng; không thay bằng kết quả giả. ID nguồn hợp lệ chưa chứng minh nguồn đó hỗ trợ câu trả lời.

[Khung agent](starter/agentic.py) chưa nối mô hình hay kho thật. Xem [bộ khởi đầu](starter/README.md) để hoàn thiện.

## 4. Đánh giá và cải thiện

Chạy câu hỏi gốc qua ba cách tìm; lưu kết quả và tính các chỉ số trong [BENCHMARK.md](BENCHMARK.md). Đọc ít nhất hai lỗi trên tập phát triển, đặt giả thuyết, thay một yếu tố và đo lại. Chọn cấu hình có Context Evidence Hit@3 cao hơn trên tập phát triển; nếu bằng nhau, chọn cách đơn giản hơn. Sau đó mới chạy tập kiểm thử.

Chạy agent với cả câu có và thiếu bằng chứng. Đọc thủ công ít nhất 5 câu kiểm thử có đáp án và 2 câu thiếu bằng chứng; chấm việc gọi công cụ, câu trả lời, nguồn và cách từ chối. Ghi nhãn, lý do, thời gian và chi phí.

## 5. Trình bày và nộp

Trình bày một câu có bằng chứng, một câu thiếu bằng chứng và một trường hợp lỗi. Nộp mã, cách chạy, dữ liệu hoặc cách truy cập, cấu hình, câu hỏi, kết quả, nhãn và báo cáo theo [SUBMISSION.md](SUBMISSION.md).
