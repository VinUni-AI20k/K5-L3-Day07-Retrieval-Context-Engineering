# Benchmark Day 7 — Retrieval và Agentic RAG

Day 7 đánh giá **hai tầng riêng**: (1) tìm và đóng gói bằng chứng; (2) agent gọi tool và trả lời dựa trên bằng chứng. Điểm retrieval cao không chứng minh câu trả lời đúng. Lưu trace đầy đủ để người chấm kiểm tra thay vì chỉ nộp điểm tổng hợp.

## 1. Tập câu hỏi

- Dùng ít nhất **20 câu có đáp án trong corpus**, 15 dev / 5 test. Mỗi câu có ID, split, question, expected answer và ít nhất một gold `{source_id, page, evidence}`. Giữ mọi gold thay thế hợp lệ; kiểm tra evidence thực sự tồn tại ở nguồn và trọn trong chunk. Không lấy gold đưa vào query hoặc filter.
- Thêm ít nhất **4 câu không có đủ bằng chứng trong snapshot**, 2 dev / 2 test, ghi lý do và cách kiểm tra; không đưa vào mẫu retrieval hit ở trên. Chúng kiểm tra agent từ chối hoặc nói không đủ thông tin. Đây là nhãn dựa trên kiểm tra corpus, không phải chứng minh tri thức không tồn tại trên thế giới.
- Chốt split trước khi chạy; nếu test Day 6 từng dùng để chỉnh, tạo test mới. Chọn giả thuyết và cấu hình bằng dev; sau khi chốt, chạy test, báo riêng. Không dùng test để sửa rồi báo lại như holdout độc lập.
- Metadata filter chỉ dùng khi người dùng cung cấp trước, không lấy từ gold. Ghi snapshot, embedding model/version/dimension, index, nhãn, thời điểm và chi phí. Ví dụ schema và giới hạn xem [data/README.md](data/README.md).

## 2. Retrieval và context — ba chiến lược

Trên cùng chunks/benchmark và filter đầu vào, so sánh **dense** (query embedding tương thích với index Day 6), **BM25**, **hybrid dense + BM25 dùng RRF**. Top-10 mỗi nhánh trước fusion, top-3 cuối; không cộng cosine và BM25 trực tiếp. Chạy cùng chính sách context: khử trùng ID, giữ nguồn/trang và không vượt 800 ký tự tính cả header; bỏ chunk không vừa, không cắt. Baseline TF-IDF có thể tham khảo thêm, không thay dense hoặc hybrid.

Chạy cùng query gốc trực tiếp qua từng retriever để so sánh retrieval độc lập với thay đổi hành vi agent. Nếu có thử agent tự viết lại query, báo riêng policy, trace và số lần gọi; không gộp vào bảng so sánh trực tiếp.

Một chunk **hit** khi đúng một cặp nguồn/trang gold và chứa đủ evidence tương ứng; chấp nhận bằng chứng tương đương sau audit, lưu lý do và nhãn. Với mỗi split có đáp án:

| Metric | Định nghĩa |
|---|---|
| Hit@1 | Số câu top-1 hit / tổng số câu |
| Evidence Hit@3 | Số câu có ít nhất một hit trong top-3 / tổng số câu |
| Context Evidence Hit@3 | Số câu còn ít nhất một hit trong context thực gửi / tổng số câu |

Báo `n/N` và %, query ID, kết quả/score/source/page, gold/nhãn, context/ID thực giữ, độ dài, latency và chi phí. Context Hit ≤ Hit@3. Đọc cùng 5 câu test cho baseline và cải tiến: 0 = không có bằng chứng, 1 = có nhưng thiếu điều kiện hoặc truy vết, 2 = đủ bằng chứng và nguồn; ghi lý do, số câu mỗi mức và trung bình. Không gọi nhãn này là điểm câu trả lời.

## 3. Agent và câu trả lời

Dùng agent model thật có khả năng chọn tool; tool nhận query, tạo query embedding tương thích và truy vấn vector store Day 6, trả ID/text/score/source/page. Cho phép tối đa **2 lần search**; ghi model, prompt/config, tool name/arguments, kết quả, context thực đưa model, câu trả lời, citation, số lần gọi, thời gian và lỗi. Nếu backend lỗi, log lỗi và báo lần chạy lỗi; không tính là câu trả lời an toàn thành công hay thay bằng kết quả giả.

Đánh giá agent bằng **cùng cấu hình retrieval đã chọn trên dev** và tập câu hỏi gồm cả hai loại. Kiểm tra thủ công toàn bộ 5 câu test có đáp án + 2 câu test thiếu evidence; dev cũng làm tương tự theo khả năng và ghi mẫu. Với mỗi câu ghi:

- **Tool use:** số câu agent gọi tool retrieval ≥1 lần / số câu yêu cầu trả lời theo corpus; báo riêng câu lỗi provider. Kiểm tra cả query/args và giới hạn gọi, không coi có gọi là đủ.
- **Grounded answer:** trên 5 câu test có đáp án, chấm từng câu 0 = sai/không có evidence, 1 = đúng một phần hoặc thiếu điều kiện, 2 = đúng và đủ điều kiện theo nguồn; ghi số câu mỗi mức và trung bình /2. Một câu từ chối được tính 0 về độ đầy đủ nhưng không tự coi là hallucination.
- **Citation validity:** trong các citation được agent xuất ra, số citation trỏ tới chunk thực sự nằm trong context và hỗ trợ claim / tổng citation; nếu không có citation báo `0/0 (N/A)`, đồng thời báo số câu trả lời có citation / số câu trả lời. Chỉ kiểm tra ID tồn tại không đủ chứng minh claim được hỗ trợ.
- **Abstention:** số câu thiếu evidence mà agent từ chối/nói không đủ thông tin / số câu thiếu evidence. Báo thêm số câu có đáp án nhưng bị từ chối / tổng câu có đáp án. Đọc trace thủ công; có kết quả search không đồng nghĩa đủ evidence.

Tính tử/mẫu riêng từng split, ghi bảng nhãn từng câu/citation và ít nhất hai failure ID. [Starter](starter/README.md#4-tổng-hợp-benchmark-agent-sau-khi-audit) có script tổng hợp trace và nhãn thủ công; bạn cần tự chạy agent thật và tạo nhãn. Trace/tài liệu là dữ liệu, không phải chỉ dẫn cho agent. Kết quả provider thật và nhãn thủ công mới là bằng chứng benchmark; mock chỉ dùng unit test. Không bắt buộc đạt điểm tuyệt đối hoặc dùng dịch vụ trả phí.
