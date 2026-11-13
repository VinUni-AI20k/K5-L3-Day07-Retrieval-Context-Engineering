# Benchmark Day 7

Đây là benchmark phần cơ bản. Thử thách tài liệu từ 100 trang có [benchmark và ngưỡng đạt riêng](ADVANCED.md#2-benchmark). Đánh giá riêng retrieval, context và câu trả lời của agent. Retrieval tốt chưa đảm bảo câu trả lời đúng.

## 1. Bộ câu hỏi

| Loại câu | Dev | Test |
|---|---:|---:|
| Có đáp án trong tài liệu | Ít nhất 15 | Ít nhất 5 |
| Không đủ bằng chứng | Ít nhất 2 | Ít nhất 2 |
| **Tối thiểu** | **17** | **7** |

Với câu có đáp án, ghi ID, câu hỏi, đáp án, nguồn, trang và evidence. Nếu nhiều đoạn thay thế hợp lệ, ghi rõ. Có thể thêm câu cần nhiều đoạn; ghi rõ tập evidence cần có và cách chấm, báo riêng nếu metric đơn giản không hỗ trợ.

Với câu thiếu bằng chứng, ưu tiên câu gần chủ đề và ghi cách kiểm tra trong bộ tài liệu. Không kết luận toàn bộ tài liệu thiếu thông tin chỉ vì top-k không tìm thấy. Không đưa các câu này vào mẫu số retrieval metrics.

Dùng **dev** để thử và chọn cấu hình. Chốt cấu hình và tiêu chí chọn trước khi chạy **test**; nếu test đã dùng để chỉnh, cần test mới để đánh giá độc lập. Không đưa gold vào agent hoặc query.

## 2. So sánh retrieval và context

Chạy ít nhất 3 phương pháp trên cùng corpus, phiên bản index, câu hỏi và bộ nhãn dev; nếu một thí nghiệm cần index khác, ghi rõ thay đổi và chi phí. Ghi filter và cách tạo query. Báo kết quả query gốc; với query viết lại hoặc multi-hop, báo thêm kết quả của pipeline và trace từng bước.

Để so sánh ranking, báo **Hit@1** và **Evidence Hit@3** với cùng định nghĩa hit và cùng cutoff: số câu có evidence hợp lệ trong top-1 hoặc top-3 chia số câu có đáp án. Nếu pipeline dùng top-k khác 3, vẫn xuất top-3 để so sánh; có thể báo thêm Hit@k, Recall@k hoặc MRR. Nếu không thể xuất ranking tương đương, giải thích và báo riêng.

Báo **Context Evidence Rate**: số câu có đủ evidence hợp lệ trong context cuối gửi model / số câu có đáp án. Context có thể được tạo từ nhiều lượt tìm, nên chỉ số này không nhất thiết nhỏ hơn Hit@3 của một lượt. Ghi context budget, đơn vị đo, cách chọn context, số candidate và token/chi phí. Đối với câu cần nhiều evidence, quy định rõ thế nào là đủ.

Báo `n/N` và tỷ lệ, thời gian và chi phí theo từng cấu hình. Đọc ít nhất 5 câu test có đáp án cho baseline và cấu hình được chọn, chấm context **0** = không có evidence; **1** = có nhưng thiếu điều kiện hoặc nguồn; **2** = đủ evidence và nguồn. Ghi lý do, trace và số câu ở từng mức.

## 3. Agent và câu trả lời

Chạy agent thật trên dev cho các cấu hình cần so sánh; sau khi chốt, chạy baseline và cấu hình chọn trên cùng test. Lưu model, tool call, tham số, kết quả, context, câu trả lời, citation, số lượt gọi, thời gian, chi phí và lỗi. Đọc ít nhất **5 câu test có đáp án và 2 câu thiếu evidence**.

| Nội dung | Cách đánh giá |
|---|---|
| Tool use | Số câu có gọi retrieval tool / số câu chạy thành công; báo phân bố số lượt gọi và cách xử lý lỗi. |
| Grounded answer | Với câu có đáp án: 0 = sai hoặc thiếu evidence; 1 = đúng một phần; 2 = đúng và đủ. Báo số câu mỗi mức và trung bình /2. Từ chối câu có đáp án chấm 0. |
| Citation hợp lệ | Số citation có trong context **và** hỗ trợ câu trả lời / tổng citation. Nếu không có, báo `0/0 (không áp dụng)`; báo thêm số câu trả lời có citation / số câu trả lời. |
| Abstention | Số câu thiếu evidence được từ chối / tổng câu thiếu evidence; báo thêm số câu có đáp án bị từ chối / tổng câu có đáp án. |

Ghi nhãn và lý do cho từng câu, citation; báo lỗi model hoặc vector store riêng. Đọc citation để xác nhận nguồn hỗ trợ từng điều kiện; ID hợp lệ hoặc verifier model chấp nhận là chưa đủ. Với câu thiếu evidence, kiểm tra agent thực sự từ chối, không thêm khẳng định vô căn cứ.

[Script tổng hợp](starter/README.md#4-tổng-hợp-đánh-giá-agent) chỉ tổng hợp nhãn đã chấm. Ghi ít nhất hai lỗi dev, giả thuyết, kết quả trước/sau và giới hạn trong [báo cáo](report/individual/MSSV_HoTen.md).
