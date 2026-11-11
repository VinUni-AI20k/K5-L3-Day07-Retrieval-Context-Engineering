# Hướng dẫn thực hành

## 0. Thiết lập và kế hoạch (0:00–0:30)

Chọn một agent và thực hiện [AGENT_SETUP](AGENT_SETUP.md). Đọc `AGENTS.md`/`CLAUDE.md`, chạy thử skill và ghi lại bằng chứng. Yêu cầu agent tóm tắt contract và lập kế hoạch; tự đối chiếu với đề, chia việc thành các bước nhỏ. Không đưa dữ liệu mật, key hoặc test bị giữ kín lên dịch vụ không được phép.

## 1. Handoff từ Day 6 (0:30–1:00)

Xuất **một** cấu hình chunk đã chọn ở Day 6 vào contract `data/README.md`, giữ nội dung, source/page và ID ổn định. Không tạo chunk theo từng strategy. Ghi phiên bản nguồn, phương pháp chunk và cách ánh xạ ID. Dùng benchmark Day 6 (≥20 câu: 15 dev/5 test), chuẩn hóa schema; kiểm tra từng `evidence` có trong nguồn và ít nhất một chunk. Nếu bằng chứng bị cắt, báo và sửa adapter/chunk **trước** thí nghiệm; không thay gold để lấy điểm. Nhiều bằng chứng hợp lệ: liệt kê tất cả; một bằng chứng đầy đủ là đủ để hit. Không đưa gold vào query, filter hoặc context selection.

Nếu đã dùng test Day 6 để chỉnh hệ thống, không gọi đó là holdout mới: tạo ít nhất 5 câu test mới có evidence, ưu tiên chủ đề/trang khác; ghi nguồn và cách chia trước khi chạy. Nếu không có Day 6, chuẩn bị corpus ít nhất 20 trang hợp lệ theo quy tắc Day 6, benchmark ≥20 câu với 15 dev/5 test. Tất cả câu trong metric chính phải trả lời được, bao gồm diễn đạt khác và điều kiện/ngoại lệ. Dữ liệu dùng được/quyền chia sẻ và snapshot phải được ghi rõ. Có thể thêm câu không trả lời được để phân tích, nhưng báo riêng, không tính vào mẫu metric chính.

## 2. Baseline retrieval (1:00–1:55)

Trên cùng chunks, triển khai **TF-IDF cosine**, **BM25**, **RRF** (top-10 mỗi nhánh → top-3; RRF `sum(1/(60+rank))`, rank từ 1) hoặc thay TF-IDF bằng dense embeddings thật. TF-IDF là lexical; RRF giữa hai lexical baseline **không phải dense–sparse hybrid**. Nêu tokenizer tiếng Việt và xử lý Unicode; ghi model/version nếu dùng dense; index document và query cùng model. Điểm BM25, cosine và RRF không cùng thang đo: không cộng trực tiếp hoặc dùng cùng threshold. Khử ID trùng trong từng danh sách và fuse đúng một lần. Kết quả ít hơn k/không có kết quả phải xử lý an toàn; không tự gán chunk khi tất cả score không có tín hiệu.

Mỗi kết quả: `id`, `text`, `score`, `source_id`, `source`, `page`, `strategy`, và metadata cần thiết. Thứ tự score giảm dần, hòa điểm ổn định theo ID. Lọc metadata chỉ dùng nếu filter là input hợp lệ sẵn có, không lấy từ gold; index và query phải dùng cùng phạm vi. Ghi rõ thời điểm tạo index, tham số và chi phí. Provider lỗi phải báo lỗi, không âm thầm dùng mock.

## 3. Đóng gói context (1:55–2:20)

Chọn top-3; khử trùng theo ID, giữ thứ tự, gắn ID/source/page, phân cách rõ và budget **800 ký tự Unicode** tính cả header và dấu phân cách. Chunk không vừa thì bỏ qua, không cắt evidence; context rỗng là kết quả hợp lệ. Cùng chính sách, budget và k trên mọi strategy. In context và danh sách ID được đưa vào; không gọi context là câu trả lời đã được xác thực. Nếu dùng token thay ký tự phải báo tokenizer và giữ cùng budget giữa các cấu hình; mẫu 800 ký tự dùng để kiểm tra thống nhất.

## 4. Đánh giá và cải thiện (2:20–3:30)

Chốt thí nghiệm và tiêu chí chọn trước khi xem test. Trên dev, chạy ba baseline, đọc trace, xác định ít nhất hai lỗi với ID câu và đưa ra **một giả thuyết có thể kiểm tra**. Thử một cải tiến, ví dụ metadata filter chỉ khi được cung cấp, tokenizer, query expansion hoặc reranker; thay một yếu tố so với baseline tương ứng. Ghi các cấu hình đã thử và chọn theo Context Evidence Hit@3 trên dev, hòa thì chọn cấu hình đơn giản hơn. Giữ test nguyên vẹn; sau khi chốt cấu hình, chạy 3 baseline và cấu hình cải tiến được chọn trên test một lần, báo riêng split. Nếu cấu hình không được chọn, không cần chạy test nó. Không sửa test sau khi xem kết quả.

Cho mỗi câu answerable, `hit(chunk)` đúng khi chunk thuộc một nguồn/trang gold và chứa **đầy đủ** đoạn evidence tương ứng, hoặc bằng chứng tương đương được người chấm xác nhận trước khi tính. `Hit@1` = số câu top-1 hit / số câu; `Evidence Hit@3` = số câu có ít nhất một hit top-3 / số câu; `Context Evidence Hit@3` = số câu còn ít nhất một hit trong context cuối / số câu. Đưa numerator/denominator và %; context hit không thể vượt retrieval hit. Không dùng precision/recall nếu chưa có nhãn đầy đủ cho các chunk liên quan.

Ghi trace từng câu: query/split, cấu hình, k, ranked chunks gồm ID/text/score/source/page, gold và nhãn hit, context/ID thực giữ, chiều dài và thời gian retrieval+packing. Báo median latency trên mỗi split và môi trường; tách thời gian xây index, ghi cost thực tế; không so latency giữa các máy như benchmark sản xuất.

Chấm thủ công cùng 5 câu test cho baseline và cấu hình chọn: context có đúng nguồn/trang và đủ bằng chứng/điều kiện không? Nhãn 0 = không có, 1 = có nhưng thiếu điều kiện hoặc truy vết, 2 = đủ và truy nguồn; nêu lý do, số từng mức và trung bình. Thêm hai ví dụ lỗi và một đánh đổi (context budget, thời gian, chất lượng, metadata). Nhãn tác giả có thể thiên lệch. Không coi nhãn này là chất lượng câu trả lời LLM.

## 5. Demo và nộp (3:30–4:00)

Demo một query thành công, một lỗi hoặc context rỗng, và so sánh trước/sau. Nộp README setup/run, mã, manifest, corpus hoặc cách lấy hợp lệ, benchmark/split, config, script và output, traces, bảng nhãn, report, log agent đã biên tập (prompt chính, thay đổi, lệnh và kết quả kiểm chứng). Bỏ secret, dữ liệu riêng tư và toàn bộ lịch sử không cần thiết. Đảm bảo người khác chạy được mà không dựa vào `solution/`.
