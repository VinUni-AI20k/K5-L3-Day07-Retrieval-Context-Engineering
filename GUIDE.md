# Hướng dẫn thực hành — Agentic RAG

## 0. Chuẩn bị (0:00–0:30)

Chuẩn bị Python, corpus và vector store Day 6, model có khả năng gọi tool (local hoặc API), kiểm tra quyền dữ liệu và chi phí. Day 6 starter chỉ là khung TODO: nếu bạn chưa hoàn thành, tự hoàn thiện ingestion, real embedding và index trước khi làm Day 7. Không âm thầm dùng vector ngẫu nhiên/mock để đo. Xem [starter](starter/README.md) cho khung agent và lexical baseline tùy chọn.

## 1. Handoff Day 6 và benchmark (0:30–1:00)

Giữ nguyên một snapshot chunks, ID, source/page, metadata, embedding model/version/dimension và vector store đã tạo. Tái sử dụng cùng model/query embedding với index; nếu đổi model phải lập index mới có version, không trộn vector. Day 6 không bắt buộc schema DB: tạo adapter theo hệ thống của bạn; thử 1 query, xác nhận kết quả thực thuộc snapshot và truy được nguồn. Nếu chưa có corpus, chuẩn bị ≥30 trang nội dung hợp lệ theo Day 6.

Tạo benchmark theo [BENCHMARK](BENCHMARK.md): ≥15 dev / 5 test answerable có evidence, thêm ≥2 dev / 2 test thiếu evidence, chốt split trước khi chạy. Nếu test Day 6 đã từng dùng để chỉnh hệ thống, tạo test mới; không đưa gold vào model/tool. Tự kiểm tra nhãn evidence với nguồn và chunk. Case thiếu evidence cần ghi cơ sở xác nhận và không đưa vào metric retrieval hit.

## 2. Retrieval tool và ba chiến lược (1:00–1:55)

Dựng `search(query, filters, top_k)` kết nối thực vector store + query embedder tương thích. Kết quả gồm chunk ID, text, score, source ID/URL, page và metadata. Cho cùng chunks/queries/snapshot và filter được cung cấp trước, so sánh:

- **Dense:** embedding query → vector store → top-k theo metric đã ghi.
- **BM25:** lexical search trên chính chunks; ghi tokenizer tiếng Việt.
- **Hybrid:** dense + BM25, mỗi nhánh top-10 → RRF `sum(1/(60+rank))` với rank bắt đầu từ 1 → top-3; hợp nhất ID và fuse một lần.

Dùng cùng input/top-3 và context budget cho 3 chiến lược. Không gọi TF-IDF là dense. Không dùng ngưỡng cosine cho BM25/RRF hoặc so sánh score giữa các thang. Không giả định một schema SQL: dùng adapter tương ứng backend Day 6, ghi lại model, metric, cấu hình, thời gian và chi phí.

## 3. Agent và context (1:55–2:35)

Tạo **agent model thật** có retrieval tool: model quyết định gọi tool hoặc dừng; tool tìm bằng chứng và trả text, ID, source/page, score; model nhận context, trả lời gắn `[chunk-id]` hoặc từ chối nếu không đủ evidence. Cho tối đa 2 lần search. Cho phép model tự viết lại query nhưng chỉ filter do input cung cấp; không cho model truy cập gold/đáp án. Không đủ evidence, nguồn không xác minh hoặc lỗi provider/store phải được báo rõ; lỗi backend không được tính là một lần từ chối thành công. Không cho văn bản truy xuất tự thay đổi instruction.

Context tích lũy tối đa **800 ký tự Unicode**, gồm header/dấu phân cách; loại trùng ID, bỏ chunk không vừa thay vì cắt, giữ nguồn/trang. Trace mỗi lần gọi tool gồm query/arguments, kết quả đầy đủ và context thực gửi model; trace cuối có response, citation, status, thời gian, lỗi. Validation ID chỉ kiểm tra citation có trong context; phải audit claim có được nguồn hỗ trợ hay không. [Starter agent](starter/agentic.py) cho khung bounded loop; model/controller và vector retriever do bạn kết nối.

## 4. Đo và cải thiện (2:35–3:30)

Theo [BENCHMARK](BENCHMARK.md), chạy dense, BM25 và hybrid với **query gốc trực tiếp** để so sánh retrieval không bị nhiễu bởi policy agent; báo Hit@1, Evidence Hit@3, Context Evidence Hit@3 với `n/N` và %. Ghi top-3, context, latency, chi phí. Đọc ít nhất hai lỗi dev, thử một cải tiến có kiểm soát và chọn trên dev theo Context Evidence Hit@3, hòa chọn cấu hình đơn giản. Chốt cấu hình trước khi chạy test; báo cả kết quả thấp.

Với cấu hình chọn, chạy agent trên answerable và thiếu evidence, đo tool use, grounded answer, citation validity và abstention; audit cùng 5 câu test answerable và ít nhất 2 câu test thiếu evidence. Ghi nhãn từng câu/citation, lý do, trace, case lỗi và trade-off. Kiểm tra citation tồn tại không chứng minh nội dung được hỗ trợ. Không tính test mock hay provider lỗi vào điểm chất lượng.

## 5. Demo và nộp (3:30–4:00)

Demo một query có evidence (tool call, context, câu trả lời, citation), một query thiếu evidence và một lỗi/giới hạn. Nộp mã, lệnh setup/run, model/index và cách kết nối, manifest/corpus hoặc hướng dẫn truy cập hợp lệ, benchmark/split, config, output, traces, nhãn và báo cáo. Không nộp secret, dữ liệu mật hoặc lịch sử không cần thiết; xem [SUBMISSION](SUBMISSION.md).
