# Báo cáo cá nhân — Day 7

- Họ tên, MSSV, lớp:
- Repo, nhánh và commit nộp:

## Handoff và setup
- Nguồn, quyền, snapshot, số trang/chunks, chiến lược chunk Day 6, lệnh adapter:
- Benchmark: 15 dev/5 test, cách chia, kiểm tra evidence, test đã từng dùng chưa:
- Agent/phiên bản, instruction, skill, MCP và plugin hoặc lý do fallback:
- Prompt chính, thay đổi do agent đề xuất, lệnh và kết quả kiểm chứng độc lập:

## Cấu hình và thí nghiệm
- Tokenizer; BM25 / TF-IDF hoặc dense / RRF, k, candidate depth, budget, chi phí:
- Hai lỗi dev (query ID, ranked IDs, lý do):
- Giả thuyết, baseline, yếu tố thay đổi, cấu hình đã thử, quy tắc chọn trước khi xem test:

| Strategy | Split | Hit@1 n/N | Evidence Hit@3 n/N | Context Evidence Hit@3 n/N | Context chars trung bình | Median ms | Index s / cost |
|---|---|---|---|---|---|---|---|

## Audit và phân tích
| Query ID | Strategy | Context 0/1/2 | Source/page đúng? | Lý do |
|---|---|---:|---|---|

- Số câu mỗi mức và trung bình; link trace và nhãn:
- Kết quả dev → lựa chọn → kết quả test, ví dụ tốt/xấu, trade-off:
- Giới hạn, nguy cơ leakage/bias, việc sẽ làm tiếp:
