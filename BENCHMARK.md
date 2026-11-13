# Benchmark Day 7

Đánh giá riêng **retrieval/context** và **câu trả lời của agent**. Retrieval tốt không đảm bảo câu trả lời đúng.

## 1. Bộ câu hỏi

| Loại câu | Dev | Test |
|---|---:|---:|
| Có đáp án trong tài liệu | Ít nhất 15 | Ít nhất 5 |
| Không đủ bằng chứng | Ít nhất 2 | Ít nhất 2 |
| **Tối thiểu** | **17** | **7** |

Với câu có đáp án, ghi ID, câu hỏi, đáp án, nguồn, trang và evidence nguyên văn. Evidence phải nằm trong nguồn và trọn trong một chunk. Nếu có nhiều evidence thay thế hợp lệ, ghi tất cả; tìm được một là đủ.

Với câu thiếu bằng chứng, ghi cách kiểm tra trong bộ tài liệu. Không tính chúng vào mẫu số của retrieval metrics.

Dùng **dev** để tìm lỗi và chọn cấu hình; vai trò này tương tự validation. Dùng **test** sau khi chốt, không dùng để chỉnh. Nếu test Day 6 đã dùng để chỉnh, tạo test mới. Không đưa gold hoặc evidence chuẩn vào agent.

## 2. Retrieval và context

Chạy dense retrieval, BM25 và hybrid RRF với **cùng query gốc**, chunk, filter đầu vào, top-3 và context budget 800 ký tự. Nếu agent tự viết lại query, báo riêng.

Một chunk là **hit** khi đúng nguồn, đúng trang và chứa đủ evidence; evidence tương đương cần được đọc và ghi lý do.

| Metric | Cách tính trên câu có đáp án |
|---|---|
| Hit@1 | Số câu có hit ở kết quả đầu / tổng số câu |
| Evidence Hit@3 | Số câu có hit trong top-3 / tổng số câu |
| Context Evidence Hit@3 | Số câu còn hit trong context gửi cho model / tổng số câu |

Báo `n/N` và tỷ lệ cho từng strategy, riêng dev và test. Ví dụ `12/15 = 80%`. Context Hit không thể lớn hơn Hit@3. Lưu query, kết quả, score, nguồn, trang, nhãn, context, thời gian và chi phí.

Đọc cùng 5 câu test cho baseline và cấu hình cải thiện. Chấm context: **0** không có evidence; **1** có nhưng thiếu điều kiện hoặc nguồn; **2** đủ evidence và nguồn. Ghi lý do và số câu mỗi mức.

## 3. Agent và câu trả lời

Chạy agent thật với strategy đã chọn trên dev. Lưu model, tool call và tham số, kết quả, context, câu trả lời, citation, thời gian và lỗi. Tối đa 2 lần search mỗi câu. Đọc thủ công ít nhất **5 câu test có đáp án và 2 câu thiếu evidence**.

| Nội dung | Cách đánh giá |
|---|---|
| Tool use | Số câu có gọi retrieval tool / số câu chạy thành công; kiểm tra thêm tham số và số lần gọi. |
| Grounded answer | Với câu có đáp án: 0 = sai hoặc không có evidence; 1 = đúng một phần; 2 = đúng và đủ. Báo số câu mỗi mức và trung bình /2. Từ chối câu có đáp án chấm 0. |
| Citation hợp lệ | Số citation có trong context **và** hỗ trợ câu trả lời / tổng citation. Nếu không có, báo `0/0 (không áp dụng)`; báo thêm số câu trả lời có citation / số câu trả lời. |
| Abstention | Số câu thiếu evidence được từ chối / tổng câu thiếu evidence; báo thêm số câu có đáp án bị từ chối / tổng câu có đáp án. |

Báo riêng dev và test, ghi nhãn từng câu và từng citation. Lỗi model hoặc vector store phải đếm riêng, không tính là từ chối đúng. Người chấm phải đọc xem citation có hỗ trợ câu trả lời không; ID hợp lệ là chưa đủ.

[Script tổng hợp](starter/README.md#4-tổng-hợp-đánh-giá-agent) dùng nhãn do bạn tự chấm, không tự chạy hoặc chấm agent. Ghi ít nhất hai lỗi, giả thuyết, kết quả trước/sau và giới hạn trong [báo cáo](report/individual/MSSV_HoTen.md).
