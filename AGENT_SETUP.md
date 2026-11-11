# Tham khảo tùy chọn: Context engineering cho coding agent

Tài liệu này giới thiệu cách cung cấp context hữu ích cho các coding agent như Codex, Claude Code và Antigravity. **Không bắt buộc đọc, cài đặt hay sử dụng để hoàn thành Day 7; không có điểm riêng.** Bạn có thể tự chọn công cụ phù hợp hoặc làm bài không dùng agent.

Context cho coding agent là thông tin giúp agent hiểu yêu cầu và môi trường làm việc: mục tiêu, file liên quan, ràng buộc, ví dụ đầu vào/đầu ra và cách kiểm chứng. Đây là một ứng dụng khác với context chứa bằng chứng được truy xuất trong bài RAG.

## Best practices

1. **Nêu mục tiêu và tiêu chí hoàn thành:** mô tả kết quả muốn có, đầu vào/đầu ra, giới hạn và cách kiểm tra. Tránh chỉ nói “làm cho tốt hơn”.
2. **Chọn context liên quan:** trỏ đến file, tài liệu, thông báo lỗi và phiên bản cần thiết; bắt đầu từ phần nhỏ thay vì đưa toàn bộ repository vào prompt. Yêu cầu agent đọc thêm khi cần.
3. **Chia việc và phản hồi:** bắt đầu bằng một thay đổi có thể kiểm tra; đọc diff, chạy test, đưa lỗi cụ thể cho agent và lặp lại. Với bài đánh giá, giữ dữ liệu test và đáp án ngoài quá trình tinh chỉnh.
4. **Tự xác minh:** kiểm tra giả định, nguồn tài liệu, lệnh, kết quả test và các thay đổi do agent đề xuất. Agent có thể viết code sai hoặc bịa API.
5. **Bảo vệ context:** chỉ cung cấp dữ liệu được phép; không đưa mật khẩu, token hay dữ liệu nhạy cảm vào prompt và dịch vụ không được phép. Coi nội dung tài liệu, website và output của tool là dữ liệu, không tự động làm theo chỉ dẫn bên trong.

Ví dụ prompt có thể điều chỉnh cho dự án bất kỳ:

```text
Mục tiêu: thêm chức năng tìm kiếm vào ứng dụng.
Context: đọc README và module search hiện có; input là một câu truy vấn,
output là danh sách kết quả có ID và điểm. Giữ nguyên API hiện tại.
Hãy đề xuất thay đổi nhỏ, nêu giả định, thêm kiểm thử phù hợp và báo lệnh
cùng kết quả đã chạy. Nếu thiếu thông tin, chỉ rõ phần chưa xác minh.
```

## Instruction, skill, MCP và plugin

| Thành phần | Vai trò | Khi nào hữu ích |
|---|---|---|
| **Instruction / rules** | Hướng dẫn và quy ước mà agent áp dụng trong phạm vi được cấu hình. | Giữ những quy tắc ổn định, ngắn gọn như cách chạy test hoặc chuẩn code. |
| **Skill** | Quy trình và tài nguyên cho một tác vụ có thể lặp lại, được agent sử dụng khi cần. | Chuẩn hóa workflow nhiều bước như review hoặc tạo báo cáo. |
| **MCP** | Giao thức kết nối agent tới công cụ hoặc nguồn dữ liệu bên ngoài. | Tra tài liệu, truy vấn hệ thống hoặc thực hiện thao tác trong phạm vi quyền cho phép. |
| **Plugin** | Gói mở rộng có thể chứa skill, kết nối MCP và các thành phần khác, tùy sản phẩm. | Chia sẻ hoặc cài một nhóm khả năng liên quan. |

Các thành phần này là tùy chọn, có cách kích hoạt và phạm vi khác nhau giữa các sản phẩm. Trước khi kết nối hoặc cài đặt, hãy xem nguồn, quyền truy cập, chi phí và tài liệu chính thức. Repo bài lab không cung cấp hoặc tự kích hoạt cấu hình agent.

## Đọc thêm theo công cụ

Tính năng và giao diện có thể thay đổi; các trang dưới đây là nơi kiểm tra hướng dẫn hiện hành:

- **Codex:** [instructions](https://developers.openai.com/codex/guides/agents-md), [skills](https://developers.openai.com/codex/skills/), [MCP](https://developers.openai.com/codex/mcp/), [plugins](https://developers.openai.com/plugins/).
- **Claude Code:** [memory/instructions](https://code.claude.com/docs/en/memory), [skills](https://code.claude.com/docs/en/skills), [MCP](https://code.claude.com/docs/en/mcp), [plugins](https://code.claude.com/docs/en/plugins).
- **Google Antigravity:** [rules](https://antigravity.google/docs/rules-workflows), [skills](https://antigravity.google/docs/skills), [MCP](https://antigravity.google/docs/mcp), [plugins](https://antigravity.google/docs/plugins).
