# Báo cáo Day 7 — Agentic RAG

## Handoff và benchmark
- Nguồn/quyền/snapshot, chunk ID và metadata, số trang/chunks:
- Vector store và lệnh kết nối; embedding model/version/dimension và metric; LLM/controller/version:
- 15 dev / 5 test có evidence, thêm 2 dev / 2 test thiếu evidence; split, kiểm chứng và nguy cơ leakage:

## Retrieval và cải tiến
- Dense / BM25 / hybrid RRF: cấu hình, k, depth, tokenizer, budget:
- Hai lỗi dev, giả thuyết, yếu tố thay đổi, quy tắc chọn trên dev và cấu hình đã chốt:

| Strategy | Split | Hit@1 n/N | Evidence Hit@3 n/N | Context Hit@3 n/N | Median ms | Chi phí |
|---|---|---|---|---|---|---|

## Agent và audit
- Tool, arguments/filter, giới hạn gọi, xử lý không đủ evidence và lỗi:

| Split | Tool use n/N | Grounded 0/1/2 và TB /2 | Citation hợp lệ n/N | Câu trả lời có citation n/N | Abstain đúng n/N | Từ chối nhầm n/N |
|---|---|---|---|---|---|---|

| Query ID | Loại câu | Tool call/args | Kết quả, context ID | Đáp án/citation | Nhãn và lý do |
|---|---|---|---|---|---|

- Trỏ tới trace, nhãn từng câu/citation, latency/chi phí và lệnh tái lập:
- So sánh trước/sau, ví dụ lỗi và trade-off; giới hạn mẫu, nhãn và model:
