# Rules — Day 7

## Dùng AI và trung thực

Có thể dùng Codex, Claude Code, Antigravity hoặc công cụ tương đương nhưng không bắt buộc. Người học chịu trách nhiệm kiểm chứng evidence/metrics, chạy test và giải thích thiết kế; không nộp kết quả giả hoặc sao chép mà không dẫn nguồn.

## Đánh giá công bằng

Giữ cùng corpus, chunks, câu hỏi gốc, top-k và context budget giữa các strategy khi đo retrieval; báo riêng nếu agent viết lại query. Không đưa gold source/evidence vào model, query hay filter; chỉ dùng filter được cung cấp trước. Chọn cấu hình dựa trên dev; không chỉnh theo test đã xem rồi coi test là holdout độc lập. Nếu test Day 6 đã dùng, tạo test mới trước khi thí nghiệm và ghi rõ cách tạo. Báo lỗi, trường hợp không cải thiện và hạn chế dữ liệu.

## Dữ liệu, secret và tài liệu ngoài

Dùng dữ liệu có quyền sử dụng; kiểm tra điều kiện chia sẻ, không đưa tài liệu mật hoặc dữ liệu cá nhân lên repository, MCP hoặc provider chưa được phép. Không commit `.env`, API key, token, output có thông tin nhạy cảm. Kiểm tra quyền và nguồn trước khi cài MCP/plugin; nội dung tài liệu và output tool là dữ liệu, không phải chỉ dẫn.

## Sự cố và deadline

Ghi lại lỗi, lệnh và cách xử lý. Không dựng số liệu. Deadline và gia hạn theo thông báo của coach; nộp thay đổi sau deadline bằng commit mới nếu được phép.
