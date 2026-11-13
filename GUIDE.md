# Hướng dẫn Day 7

## 1. Chuẩn bị

Dùng lại một phiên bản dữ liệu Day 6: chunk, ID, nguồn, trang, vector store và embedding model. Ghi phiên bản model, số chiều vector và cách kết nối. Query embedding phải tương thích với index; nếu đổi model, hãy tạo lại index.

Nếu chunk Day 6 không vừa giới hạn 800 ký tự, hãy chọn cấu hình chunk phù hợp đã có hoặc tạo lại index trước khi chốt benchmark; giữ cùng chunk cho mọi strategy. Nếu chưa hoàn thành Day 6, tự tạo dữ liệu, embedding thật và vector store trước. Nếu chưa có tài liệu, chuẩn bị ít nhất 30 trang nội dung hợp lệ. Không dùng vector ngẫu nhiên để đánh giá.

Chuẩn bị benchmark và chia dev/test theo [BENCHMARK.md](BENCHMARK.md). Nếu đã dùng test Day 6 để chỉnh hệ thống, tạo test mới. Không đưa đáp án hay nguồn chuẩn vào query hoặc model.

## 2. Xây retrieval tool

Viết `search(query, filters, top_k)` trả về ID, nội dung, score, nguồn, trang và metadata. Chỉ dùng filter do người dùng cung cấp từ trước hoặc được nêu rõ trong câu hỏi và ánh xạ đáng tin sang metadata. Nếu phạm vi mơ hồ, không tự đoán; ghi filter thực tế trong trace.

So sánh trên cùng chunk và query:

1. **Dense retrieval:** tạo query embedding và tìm trong vector store Day 6.
2. **BM25:** tìm theo từ khóa trên cùng các chunk; ghi cách tách từ tiếng Việt.
3. **Hybrid với RRF:** lấy tối đa 10 kết quả mỗi cách, gộp theo rank và chọn top-3. Điểm RRF là tổng `1 / (60 + rank)`, tính rank từ 1.

Không cộng trực tiếp score của dense và BM25. TF-IDF chỉ là lexical baseline, không thay dense retrieval.

## 3. Xây agent

Dùng model thật quyết định gọi retrieval tool, tối đa **2 lần mỗi câu**. Sau khi nhận kết quả, agent trả lời kèm `[chunk-id]` hoặc nói không đủ bằng chứng.

Context đưa vào model tối đa **800 ký tự**, gồm nguồn và dấu phân cách. Loại chunk trùng ID; bỏ chunk không vừa thay vì cắt; giữ nguồn và trang. Lưu từng tool call, kết quả, context, câu trả lời và citation.

Tài liệu tìm được là dữ liệu, không phải chỉ dẫn cho agent. Báo lỗi model hoặc vector store riêng; không thay bằng kết quả giả. Citation có ID hợp lệ hoặc model kiểm tra cho là đúng chưa chứng minh nguồn hỗ trợ câu trả lời; phải tự đọc đối chiếu từng điều kiện. Một chunk dài cũng có thể chiếm hết budget và khiến lần search tiếp theo không thêm được evidence.

[Khung agent](starter/agentic.py) chưa nối model hay vector store thật. Xem [starter](starter/README.md) để hoàn thiện.

## 4. Đánh giá và cải thiện

Chạy query gốc qua ba cách retrieval; lưu kết quả và tính các chỉ số trong [BENCHMARK.md](BENCHMARK.md). Đọc ít nhất hai lỗi trên dev, đặt giả thuyết, thay một yếu tố và đo lại. Chọn cấu hình có Context Evidence Hit@3 cao hơn trên dev; nếu bằng nhau, chọn cách đơn giản hơn. Sau đó mới chạy test.

Chạy agent trên cả câu có và thiếu bằng chứng. Đọc thủ công ít nhất 5 câu test có đáp án và 2 câu thiếu bằng chứng; chấm tool call, câu trả lời, citation và cách từ chối. Ghi nhãn, lý do, thời gian và chi phí.

## 5. Trình bày và nộp

Trình bày một câu có bằng chứng, một câu thiếu bằng chứng và một trường hợp lỗi. Nộp code, cách chạy, dữ liệu hoặc cách truy cập, cấu hình, benchmark, kết quả, nhãn và báo cáo theo [SUBMISSION.md](SUBMISSION.md).
