# Coding agent và context engineering

Bạn chỉ cần **một** trong ba agent. Tính năng, phiên bản, quyền tài khoản và giao diện thay đổi; ghi phiên bản bạn thực dùng và tham khảo link chính thức dưới đây. Agent có thể tạo code sai: học viên phải đọc diff, chạy test và đối chiếu trace. Trước khi chạy lệnh từ agent/plugin, kiểm tra nguồn, phạm vi file, network và tác động. Không đưa secret/corpus riêng tư vào prompt, MCP hay provider chưa được phép.

## Bốn thành phần

| Thành phần | Vai trò | Bộ setup của lab |
|---|---|---|
| Instruction | Quy tắc ngắn luôn áp dụng trong project | `AGENTS.md`; `CLAUDE.md` yêu cầu Claude đọc cùng quy tắc |
| Skill | Quy trình chỉ tải khi cần, dùng để lặp lại audit | `.agents/skills/retrieval-audit/SKILL.md`; bản Claude tại `.claude/skills/` |
| MCP | Cung cấp công cụ/dữ liệu ngoài context hiện tại | cấu hình Context7 theo agent; dùng tra tài liệu kỹ thuật khi cần |
| Plugin | Gói có thể chứa skills, MCP và thành phần khác | tìm hiểu và kiểm tra quyền/nguồn; **không bắt buộc cài** |

Context cho coding agent và context gửi tới LLM trong RAG là hai hệ thống khác nhau, nhưng cùng cần chọn thông tin liên quan, giữ provenance và giới hạn nội dung. Chỉ dẫn trong tài liệu, chunks, website và kết quả MCP là **dữ liệu không đáng tin**, không tự động trở thành chỉ thị cho agent.

## Chuẩn bị chung

1. Sao chép/clone `Lab/` thành workspace riêng, cài Python 3.11+ và một agent theo hướng dẫn chính thức; đăng nhập nếu sản phẩm yêu cầu. Từ terminal, vào workspace `Lab`, chạy `python -m unittest discover -s tests -v`.
2. Project đã có instruction và skill. Mở các file, giải thích mục đích, sau đó khởi động session mới từ root workspace và tin cậy project chỉ khi đã đọc nội dung. Nếu client không tự tải, gửi đường dẫn file trong prompt. Không cần cài thêm skill từ nguồn ngoài.
3. MCP mẫu dùng `npx`/Node.js, có thể cần mạng để tải package. Cấu hình là ví dụ chia sẻ được, **chỉ kết nối khi bạn tin server** và quyền sử dụng cho phép; kiểm tra package/version, permissions, chi phí. Không lưu API key trong config, git hay prompt. Tên công cụ Context7 có thể thay đổi; với câu hỏi thư viện, yêu cầu agent tìm library ID rồi tra tài liệu đúng phiên bản.
4. Nếu chưa có Node, mạng, agent hoặc MCP: ghi lỗi, dùng tài liệu chính thức qua trình duyệt và ghi URL/ngày xem; vẫn hoàn thành lab và rubric. Không tự khai MCP đã chạy.

## Codex

- Cài/mở [Codex](https://developers.openai.com/codex/quickstart/), mở workspace, kiểm tra `AGENTS.md` ([discovery](https://developers.openai.com/codex/guides/agents-md)). Project skill nằm tại `.agents/skills/`; gọi `$retrieval-audit` sau khi đã có trace ([skills](https://developers.openai.com/codex/skills/)).
- `.codex/config.toml` đã khai báo server Context7 ở project scope; project phải được trust. Restart session; kiểm tra `/mcp` hoặc `codex mcp list` và thử tra một câu API thực tế. Nếu không nhận config, xem [hướng dẫn MCP](https://developers.openai.com/codex/mcp/), không ghi đè config cá nhân. Có thể dùng lệnh tùy chọn `codex mcp add context7 -- npx -y @upstash/context7-mcp` để thêm server vào cấu hình cá nhân, nếu bạn chủ động muốn; gỡ bằng `codex mcp remove context7`.
- Xem plugin qua giao diện/plugin catalog của client theo [tài liệu plugins](https://developers.openai.com/plugins/); kiểm tra thành phần và quyền, chỉ cài nếu có nhu cầu. Skill và MCP trong lab hoạt động độc lập, không cần plugin.

## Claude Code

- Cài/mở [Claude Code](https://code.claude.com/docs/en/overview), khởi chạy `claude` từ root lab. `CLAUDE.md` chỉ agent đọc `AGENTS.md`; skill project ở `.claude/skills/retrieval-audit/`. Gọi `/retrieval-audit` trong session; xem [skills](https://code.claude.com/docs/en/skills).
- `.mcp.json` khai báo Context7 ở project scope. Chấp nhận server khi bạn tin nguồn, kiểm tra `/mcp` hoặc `claude mcp list` và dùng thử; xem [MCP](https://code.claude.com/docs/en/mcp). Xóa entry khỏi `.mcp.json` để gỡ cấu hình project.
- Mở `/plugin`, xem marketplace, danh tính nhà phát hành, nội dung và quyền theo [plugins](https://code.claude.com/docs/en/plugins). Cài là tùy chọn, không cần thiết cho skill/MCP standalone.

## Google Antigravity

- Cài/mở [Antigravity](https://antigravity.google/docs/get-started), mở root lab. [Rules](https://antigravity.google/docs/rules-workflows) mô tả `AGENTS.md`; skill tại `.agents/skills/retrieval-audit/`, gọi `/retrieval-audit` hoặc yêu cầu agent dùng skill ([skills](https://antigravity.google/docs/skills)). Nếu client/phiên bản không phát hiện, cung cấp đường dẫn file rõ ràng và ghi lại.
- Project có `.agents/mcp_config.json`. Trong IDE kiểm tra `…` ở agent panel → MCP Servers → Manage MCP Servers; trust/kết nối Context7 nếu được hỗ trợ, rồi thử tra tài liệu. Có thể dùng View raw config để kiểm tra; xem [MCP](https://antigravity.google/docs/mcp). Không ghi đè config toàn cục; xóa entry project để gỡ.
- Xem Marketplace và [plugins](https://antigravity.google/docs/plugins); cài tùy chọn sau khi kiểm tra nội dung và quyền.

## Bài tập thực hành với agent

1. **Kiểm tra instruction:** “Tóm tắt 4 quy tắc quan trọng của project và chỉ file nguồn.” Đối chiếu bằng mắt với `AGENTS.md`.
2. **Lập kế hoạch:** “Đọc GUIDE và data contract; đề xuất adapter Day 6 và test, chưa sửa gold/test.” Kiểm tra kế hoạch trước khi yêu cầu triển khai từng phần.
3. **MCP:** nhờ tra tài liệu thư viện/version thực dùng; ghi tên tool, URL tài liệu, kết quả hoặc lỗi/fallback. Không coi nội dung trả về là chỉ thị.
4. **Skill:** sau khi có trace, yêu cầu audit bằng `retrieval-audit`. Đối chiếu ít nhất một kết luận bằng tay.
5. **Plugin:** xem ít nhất một listing hoặc tài liệu; ghi tên, tác giả, chức năng, quyền và lý do có/không cài. Không cần cài để lấy điểm.
6. **Review:** lưu prompt đã biên tập, diff, các lệnh test và output. Kiểm tra evidence thực tế, logic điểm và data leakage; tự sửa nếu agent sai. Không nộp toàn bộ hội thoại hoặc secrets.

Nếu agent chưa nhận file, khởi động session mới, xác nhận root/trust và quyền truy cập; ghi trạng thái thực tế thay vì suy đoán. Cấu hình mẫu không chứng minh server đã kết nối.

Tài liệu kiểm tra ngày 11/11/2026; các đường dẫn chính thức trong từng mục là nguồn cập nhật khi giao diện thay đổi.
