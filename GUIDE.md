# Hướng dẫn Day 7

## 1. Chuẩn bị

Dùng lại chunk, ID, nguồn, vector store và embedding model Day 6. Ghi phiên bản model, số chiều và cách kết nối. Query embedding phải tương thích với index; nếu đổi embedding model, tạo index tương ứng và ghi chi phí. Nếu chưa hoàn thành Day 6, chuẩn bị dữ liệu, embedding thật và vector store trước; không dùng vector ngẫu nhiên để đánh giá.

Chọn tập tài liệu đủ đa dạng; nếu tự chuẩn bị từ đầu, dùng ít nhất 30 trang nội dung hợp lệ. Tạo benchmark theo [BENCHMARK.md](BENCHMARK.md); không đưa gold vào agent hoặc retrieval.

## 2. Thử các phương pháp retrieval

Triển khai và benchmark **ít nhất 3 phương pháp khác nhau**, bao gồm dense retrieval trên vector store Day 6. Một thay đổi top-k đơn thuần là cấu hình khác, không phải phương pháp mới. Có thể kết hợp, thay thế hoặc phát triển thêm các gợi ý sau:

| Phương pháp | Ý tưởng thử nghiệm |
|---|---|
| Dense retrieval | Embedding query, tìm vector gần nhất; thử top-k và metadata filter. |
| Lexical retrieval | BM25, full-text search hoặc TF-IDF; xem ảnh hưởng của tách từ tiếng Việt. |
| Hybrid retrieval | Kết hợp dense và lexical bằng RRF hoặc score fusion có chuẩn hóa. |
| Retrieval + rerank | Lấy nhiều candidate rồi dùng reranker hoặc model xếp lại; so sánh trước/sau. |
| Query transformation | Viết lại, mở rộng hoặc tách câu hỏi; so sánh với query gốc. |
| Multi-stage hoặc multi-hop | Tìm theo nhiều bước, dùng kết quả trước để tìm tiếp; ghi từng bước. |

Một pipeline hybrid hoặc có rerank được tính là một phương pháp nếu khác rõ về cách tìm/xếp hạng; mô tả và benchmark riêng. Chỉ cộng score từ các retriever khi đã có cách chuẩn hóa hoặc hợp nhất hợp lý. Không cần làm tất cả gợi ý.

Để dễ kiểm tra, kết quả nên có ID, nội dung, score hoặc rank, nguồn, trang và metadata. Filter phải dựa trên thông tin người dùng cung cấp hoặc được hệ thống suy luận từ query một cách đáng tin; ghi lại cách suy luận, không dùng gold hay đáp án chuẩn.

## 3. Thiết kế agent và context

Dùng model thật để điều phối việc tìm bằng chứng. Bạn có thể dùng một hay nhiều tool: tìm vector, tìm từ khóa, filter, rerank, tìm theo metadata hoặc tool khác. Tự chọn số lượt gọi, điều kiện dừng, top-k và context budget; ghi lý do và đo tác động đến chất lượng, thời gian, chi phí. Có thể giới hạn để tránh vòng lặp, nhưng **không có mức giới hạn chung bắt buộc**.

Thử các cách chọn context như deduplication, chọn đoạn theo độ liên quan, giữ đoạn lân cận, nén hoặc trích đoạn. Giữ đủ nguồn và điều kiện để kiểm chứng; không đưa câu trả lời chuẩn vào context. Agent trả lời có citation hoặc nói không đủ bằng chứng.

Lưu từng tool call, tham số, query, kết quả, context cuối, câu trả lời, citation và lỗi. Nội dung tài liệu là dữ liệu, không phải chỉ dẫn. ID citation hợp lệ chưa chứng minh nguồn hỗ trợ câu trả lời: cần đọc đối chiếu. Có thể dùng, sửa hoặc thay [khung agent](starter/agentic.py).

## 4. Đánh giá và cải thiện

So sánh ít nhất 3 phương pháp trên cùng bộ dev, ghi cấu hình và điều kiện so sánh. Thử **ít nhất 2 cấu hình nhằm cải thiện** baseline, có giả thuyết và kết quả riêng (không bắt buộc mọi thử nghiệm đều tăng điểm); ví dụ thay top-k, thêm rerank, đổi context budget hoặc thử nhiều lượt tìm. Một phương pháp mới có thể đồng thời là một cấu hình cải thiện nếu được mô tả và đo riêng.

Đọc ít nhất 2 lỗi dev, tìm nguyên nhân, đo lại sau thay đổi và chọn cấu hình theo tiêu chí công bố trước: chất lượng retrieval, context, câu trả lời và chi phí/thời gian. Chốt cấu hình trước khi chạy test. Làm theo [BENCHMARK.md](BENCHMARK.md) để báo cáo cả kết quả không cải thiện.

## 5. Nộp và trình bày

Trình bày ít nhất một câu trả lời có bằng chứng, một câu thiếu bằng chứng và một lỗi. Nộp theo [SUBMISSION.md](SUBMISSION.md), kèm bảng so sánh, trace và lý do chọn cấu hình.
