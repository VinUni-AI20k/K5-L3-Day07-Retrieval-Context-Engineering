# Checkpoints — Day 7

Các mốc dưới đây tính từ lúc bắt đầu lớp (4 giờ); thời gian thực tế theo coach. Xem chi tiết và tiêu chí trong [GUIDE.md](GUIDE.md).

## CP1 — Setup agent và handoff (0:00–1:00)

- **Mục tiêu:** có workspace, agent và dữ liệu đầu vào đáng tin.
- **Cần làm:** đọc instruction; thử skill/MCP hoặc ghi fallback; chuyển chunks và benchmark Day 6, kiểm chứng evidence và split.
- **Sản phẩm:** manifest, chunks, benchmark, setup log đã biên tập.
- **Cần hiểu:** instruction, skill, MCP, plugin; test đã dùng để chỉnh không còn là holdout.
- **Tự kiểm tra:** mỗi evidence có ít nhất một chunk hợp lệ, source/page và ID truy vết được; test mới nếu test cũ đã dùng để chọn.

## CP2 — Ba baseline (1:00–1:55)

- **Mục tiêu:** so sánh TF-IDF, BM25, RRF hoặc thay TF-IDF bằng dense embedding thật.
- **Cần làm:** dùng cùng chunks, build index, lưu tên strategy, score và thứ tự.
- **Sản phẩm:** code/config và trace dev có top-3.
- **Cần hiểu:** TF-IDF là lexical; RRF fuse theo rank, không cộng trực tiếp các score.
- **Tự kiểm tra:** không lặp ID, không vượt k, score sort ổn định và output rỗng được xử lý.

## CP3 — Context (1:55–2:20)

- **Mục tiêu:** đóng gói kết quả thành context có thể truy vết.
- **Cần làm:** loại trùng, giữ thứ tự/source/page, budget 800 ký tự gồm header và phân cách.
- **Sản phẩm:** context và danh sách ID được giữ trong trace.
- **Cần hiểu:** chunk đúng nằm trong top-3 chưa chắc nằm trong context cuối.
- **Tự kiểm tra:** context không vượt budget, không cắt chunk, có nhánh rỗng.

## CP4 — Đánh giá và cải thiện (2:20–3:30)

- **Mục tiêu:** đo, tìm lỗi và chọn cải tiến dựa trên dev.
- **Cần làm:** tính Hit@1, Evidence Hit@3 và Context Evidence Hit@3; nêu hai lỗi dev và thử một giả thuyết thay một yếu tố; chốt cấu hình rồi chạy test.
- **Sản phẩm:** trace, bảng tử/mẫu, cấu hình chọn và audit 5 test cùng mẫu.
- **Cần hiểu:** test không được dùng chọn cấu hình; kết quả giảm vẫn có giá trị nếu báo trung thực.
- **Tự kiểm tra:** context hit không vượt hit@3; từng nhãn audit có lý do và nguồn.

## CP5 — Demo và nộp (3:30–4:00)

- **Mục tiêu:** người khác tái lập, đọc hiểu và chấm được.
- **Cần làm:** demo một query thành công, một lỗi/context rỗng; viết báo cáo, ghi cách kiểm chứng agent, push bài cá nhân.
- **Sản phẩm:** repo và báo cáo theo [SUBMISSION.md](SUBMISSION.md).
- **Tự kiểm tra:** lệnh chạy, file trace, benchmark, nguồn hợp lệ và quyền đọc repo; không commit secret.
