# Hướng dẫn thực hành Day 7

**Mục tiêu:** xây agent biết tìm tài liệu trong kho dữ liệu Day 6, trả lời có dẫn nguồn và nhận biết khi không đủ thông tin.

## 1. Chuẩn bị dữ liệu và bộ câu hỏi

Dùng lại một phiên bản dữ liệu đã tạo ở Day 6. Lưu lại tên và phiên bản mô hình tạo vector, số chiều vector, cách kết nối kho dữ liệu, ID từng đoạn, nguồn, trang và các thông tin mô tả khác. Vector của câu hỏi phải được tạo bằng mô hình tương thích với vector trong kho. Nếu đổi mô hình, bạn cần tạo lại kho vector tương ứng.

Bộ khởi đầu Day 6 chỉ là khung mã. Nếu chưa hoàn thành Day 6, bạn cần tự tạo dữ liệu, vector thật và kho lưu trữ trước. Nếu chưa có bộ tài liệu, chọn ít nhất **30 trang nội dung** hợp lệ theo yêu cầu Day 6. Không dùng vector ngẫu nhiên để báo cáo chất lượng tìm kiếm.

Chuẩn bị bộ câu hỏi theo [BENCHMARK.md](BENCHMARK.md):

- Ít nhất **15 câu phát triển và 5 câu kiểm thử** có đáp án và đoạn bằng chứng trong tài liệu.
- Ít nhất **2 câu phát triển và 2 câu kiểm thử** không có đủ bằng chứng trong bộ tài liệu; ghi cách bạn kiểm tra.
- Nếu tập kiểm thử Day 6 đã được dùng để chỉnh hệ thống, tạo tập kiểm thử mới cho Day 7. Không đưa đáp án hoặc nguồn chuẩn vào câu hỏi gửi cho agent.

## 2. Xây công cụ tìm kiếm

Viết công cụ `search(query, filters, top_k)` để nhận câu hỏi, tìm tài liệu và trả về ID, nội dung đoạn, điểm, nguồn, trang và thông tin mô tả. Bộ lọc chỉ được dùng khi người dùng cung cấp từ trước; không lấy bộ lọc từ đáp án chuẩn.

So sánh ba cách trên **cùng dữ liệu và cùng câu hỏi**:

1. **Tìm bằng vector:** tạo vector cho câu hỏi bằng mô hình tương thích, sau đó truy vấn kho vector Day 6.
2. **Tìm theo từ khóa BM25:** tìm trên cùng các đoạn tài liệu; ghi rõ cách tách từ, nhất là với tiếng Việt.
3. **Tìm kết hợp:** lấy tối đa 10 kết quả từ mỗi cách trên, dùng RRF để gộp theo thứ hạng, rồi chọn 3 kết quả đầu.

Với RRF, điểm gộp của một đoạn là tổng `1 / (60 + thứ_hạng)` ở các danh sách, tính thứ hạng từ 1. Không cộng trực tiếp điểm vector với điểm BM25 vì chúng khác thang đo. TF-IDF là cách tìm theo từ khóa và có thể dùng làm đối chứng thêm; nó không thay cho cách tìm bằng vector thật.

## 3. Xây agent và chuẩn bị thông tin cho câu trả lời

Cho một mô hình thật khả năng quyết định gọi công cụ tìm kiếm hoặc dừng. Công cụ trả lại các đoạn tìm được; mô hình dùng chúng để trả lời và ghi nguồn theo dạng `[chunk-id]`. Nếu không có đủ bằng chứng, agent phải nói rõ. Giới hạn tối đa **2 lần gọi tìm kiếm** cho mỗi câu hỏi.

Thông tin được đưa cho mô hình không vượt quá **800 ký tự**, kể cả tên nguồn và dấu phân cách. Bỏ đoạn bị trùng ID hoặc không vừa giới hạn; giữ ID, nguồn và trang. Lưu kết quả từng lần gọi, thông tin thực sự đưa cho mô hình, câu trả lời và nguồn trích dẫn.

Không để nội dung tài liệu trở thành chỉ dẫn mới cho agent. Nếu mô hình hoặc kho dữ liệu bị lỗi, ghi lỗi riêng; không thay bằng kết quả giả và không tính lỗi là một lần từ chối đúng. Mã chỉ kiểm tra được ID trích dẫn có xuất hiện; bạn vẫn phải tự kiểm tra nguồn có hỗ trợ nội dung câu trả lời hay không.

[starter/agentic.py](starter/agentic.py) là khung vòng lặp có giới hạn số lần tìm. Bạn cần tự kết nối mô hình và kho Day 6 theo [hướng dẫn bộ khởi đầu](starter/README.md).

## 4. Đánh giá và cải thiện

Trước tiên, chạy cùng câu hỏi gốc qua ba cách tìm kiếm để so sánh công bằng. Đo số câu tìm được bằng chứng ở vị trí đầu, trong 3 kết quả đầu và trong phần thông tin thực sự đưa cho mô hình. Cách tính cụ thể nằm trong [BENCHMARK.md](BENCHMARK.md).

Đọc ít nhất hai lỗi trên tập phát triển. Đặt một giả thuyết, thay đổi một yếu tố và đo lại. Chọn cấu hình dựa trên tập phát triển, sau đó mới chạy tập kiểm thử. Báo cả trường hợp kết quả giảm.

Với cấu hình đã chọn, chạy agent trên cả câu có và không có đủ bằng chứng. Đánh giá việc gọi công cụ, độ đúng của câu trả lời, nguồn trích dẫn và việc từ chối. Đọc thủ công ít nhất 5 câu kiểm thử có đáp án và 2 câu thiếu bằng chứng; ghi nhãn, lý do và đường dẫn đến kết quả từng câu.

## 5. Trình bày và nộp bài

Trình bày một câu có bằng chứng: lần gọi công cụ, tài liệu tìm được và câu trả lời kèm nguồn. Thử thêm một câu thiếu bằng chứng và giải thích một trường hợp lỗi.

Nộp mã nguồn, lệnh chạy, cấu hình mô hình và kho dữ liệu, bộ câu hỏi, kết quả từng lần chạy, bảng đánh giá và báo cáo. Không nộp khóa bí mật hay dữ liệu không được phép chia sẻ. Xem [SUBMISSION.md](SUBMISSION.md).
