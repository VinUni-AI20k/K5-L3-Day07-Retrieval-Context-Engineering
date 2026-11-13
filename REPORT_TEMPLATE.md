# Báo cáo Day 7

## Dữ liệu và benchmark

- Nguồn, quyền sử dụng, số trang và số chunk:
- Vector store, cách kết nối; embedding model, phiên bản và số chiều:
- Agent model, phiên bản, cách chạy:
- Cách chia dev/test và kiểm tra câu có/thiếu evidence:

Báo số câu / tổng số câu và tỷ lệ cho các metric.

## Retrieval và cải thiện

- Cấu hình dense, BM25, RRF; top-k và context budget:
- Hai lỗi dev, giả thuyết, thay đổi và lý do chọn cấu hình:

| Strategy | Split | Hit@1 | Evidence Hit@3 | Context Evidence Hit@3 | Thời gian | Chi phí |
|---|---|---|---|---|---|---|

## Agent và đánh giá

- Retrieval tool, filter, giới hạn số lần gọi và xử lý lỗi:

| Split | Tool use | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|

- Đường dẫn trace, nhãn, lệnh chạy và chi phí:
- Kết quả trước/sau, ví dụ lỗi, đánh đổi và giới hạn:
