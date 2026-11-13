# Thử thách nâng cao — tối đa 15 điểm

**Không bắt buộc.** Hoàn thành phần này và đạt ít nhất **90% benchmark test** để nhận 15 điểm bonus. Điểm tối đa toàn bài là **100**: 85 điểm cơ bản + 15 điểm nâng cao. Xem [rubric](RUBRIC.md).

## 1. Tài liệu và index

Chọn **một tài liệu thực tế ít nhất 100 trang** có text, bảng, ảnh và biểu đồ chứa thông tin hữu ích. Ví dụ: báo cáo thường niên, báo cáo nghiên cứu hoặc báo cáo thống kê. Ghi nguồn, phiên bản, số trang và quyền sử dụng; người chấm cần truy cập được bản gốc hoặc có cách tái tạo hợp lệ.

Index toàn bộ nội dung hữu ích của tài liệu, không chỉ những trang xuất hiện trong benchmark. Ghi những trang hoặc phần không xử lý được, lý do và ảnh hưởng. Giữ liên kết từ mỗi phần được index về tài liệu và số trang gốc; với bảng, ảnh, biểu đồ, lưu thêm vùng trang, ảnh crop hoặc thông tin đủ để tìm và kiểm chứng hình gốc.

Thiết kế pipeline để agent tìm được evidence từ cả text và nội dung trực quan. Bạn tự chọn và giải thích cách xử lý: OCR, phân tích layout, trích bảng, mô tả ảnh, vision model, multimodal embedding, kết hợp text và image retrieval hoặc cách khác. Không bắt buộc dùng model hay framework cụ thể. Kiểm tra nội dung trích xuất với bản gốc: text OCR hoặc mô tả do model tạo không tự bảo đảm đúng.

## 2. Benchmark

Tạo benchmark riêng cho tài liệu này và chia dev/test trước khi thử nghiệm. Bộ test có **ít nhất 30 câu**, gồm ít nhất **24 câu có đáp án** và **6 câu thiếu bằng chứng**. Các câu có đáp án phải bao phủ:

| Nhóm chính | Tối thiểu | Ví dụ yêu cầu |
|---|---:|---|
| Bảng | 6 | Tra đúng hàng, cột, đơn vị; so sánh hoặc tính từ các ô. |
| Ảnh, sơ đồ | 5 | Nhận diện hoặc giải thích thông tin thể hiện trong ảnh/sơ đồ. |
| Biểu đồ | 5 | Đọc trục, chú giải, đơn vị; so sánh xu hướng hoặc giá trị có thể kiểm chứng. |
| Multi-hop | 4 | Kết hợp evidence từ ít nhất hai trang, bảng hoặc hình. |
| Text | 4 | Tìm và tổng hợp thông tin có điều kiện từ văn bản. |

Mỗi câu chỉ tính vào **một nhóm chính** trong bảng, dù có thể gắn thêm tag phụ. Không dùng các hình chỉ để trang trí làm câu ảnh/biểu đồ. Dùng thêm câu hỏi gần chủ đề nhưng không đủ evidence trong tài liệu để kiểm tra abstention.

Bộ dev có ít nhất **15 câu có đáp án và 3 câu thiếu bằng chứng**; nên bao phủ đủ các nhóm. Câu dev và test không trùng hoặc chỉ đổi cách diễn đạt cùng một câu trả lời. Có thể dùng cùng tài liệu, nhưng không chọn cấu hình bằng test. Nếu đã dùng test để chỉnh, tạo test mới trước khi báo điểm. Không đưa câu trả lời chuẩn, bảng gold hoặc vùng evidence chuẩn vào pipeline khi chạy.

Mỗi câu có ID, nhóm chính, câu hỏi, đáp án hoặc hành vi từ chối mong đợi, nguồn và lý do. Câu có đáp án cần ghi evidence đủ kiểm chứng: trang và đoạn text, ô/hàng/cột bảng hoặc vùng ảnh/biểu đồ; ghi đơn vị, điều kiện và phép tính nếu có. Câu thiếu bằng chứng cần ghi cách kiểm tra trong tài liệu. Chấm bằng cách đối chiếu bản gốc, không chỉ dựa vào nội dung model trích xuất.

## 3. Chạy và chấm

Thử các cấu hình trên dev, lưu kết quả và chốt pipeline. Chạy pipeline đã chốt trên **toàn bộ test**, lưu trace retrieval, context, tool call, câu trả lời, citation, thời gian, chi phí và lỗi cho từng câu. Benchmark test chấm mỗi câu **đạt hoặc không đạt**:

- **Câu có đáp án:** đạt khi trả lời đúng và đủ, đúng đơn vị/điều kiện/phép tính nếu có; citation xác định được trang và vùng evidence cần thiết; evidence thực sự hỗ trợ toàn bộ câu trả lời. Đúng một phần, sai citation hoặc từ chối đều không đạt.
- **Câu thiếu bằng chứng:** đạt khi từ chối hoặc nêu rõ không đủ bằng chứng, không thêm khẳng định thiếu căn cứ. Câu trả lời suy đoán không đạt.
- **Lỗi hệ thống, timeout hoặc không có kết quả:** tính không đạt và báo riêng; không loại khỏi mẫu số.

**Tỷ lệ đạt = số câu đạt / tổng số câu test × 100%.** Phải đạt từ 90% trở lên, không làm tròn để qua ngưỡng; ví dụ test 30 câu cần ít nhất **27/30**. Nếu có nhiều hơn 30 câu, tính trên toàn bộ test đã công bố, không chọn câu để chấm. Báo `n/N` toàn bộ và theo từng nhóm, gồm cả câu thiếu evidence; đồng thời báo số lỗi, thời gian và chi phí.

Đọc và ghi nhãn **từng câu test**, kèm lý do và đối chiếu evidence từ bản gốc. LLM judge có thể hỗ trợ nhưng không thay thế việc kiểm tra này; cần để giảng viên/người chấm có thể kiểm tra lại. Để nhận bonus phải hoàn thành yêu cầu tài liệu, index, benchmark và nộp đủ bằng chứng tái lập, ngoài việc đạt ngưỡng. Không cộng một phần của 15 điểm nếu chưa đạt các điều kiện.

## 4. Nộp

Nộp code và cách chạy; nguồn tài liệu, thống kê và cấu hình index; benchmark dev/test, đáp án và evidence; kết quả từng câu, trace, nhãn, metrics theo nhóm; phân tích lỗi, chi phí và giới hạn. Không nộp tài liệu hoặc dữ liệu khi chưa có quyền chia sẻ; thay bằng nguồn và cách truy cập hợp lệ.
