# Submission — Day 7

## Loại bài và tên repo

**Cá nhân.** Tạo repo bài làm từ repo đề bài, đặt tên theo lớp, ví dụ `K5-L3A-DAY07-MSSV-HoTen-RetrievalContext` hoặc `K5-L3B-DAY07-MSSV-HoTen-RetrievalContext` (không dấu, không khoảng trắng). Nộp link repo theo hướng dẫn coach/LMS và cấp quyền xem cho người chấm. Deadline theo thông báo của coach.

Fork repository đề bài nếu được phép; hoặc clone rồi tạo repo cá nhân và đổi remote. Hướng dẫn chung:

```bash
git clone https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering.git <TEN_REPO>
cd <TEN_REPO>
git remote rename origin upstream
git remote add origin <URL_REPO_CA_NHAN>
git push -u origin main
```

Thay URL khi repo đề bài do coach cung cấp khác. Không push bài vào repo đề bài.

## Deliverable

- Code agent model thật, retrieval tool/vector-store adapter, test, lệnh setup/run; cấu hình dense/BM25/hybrid và context packing.
- Manifest, corpus/chunks hoặc hướng dẫn lấy và xử lý; model embedding/index/version/dimension và cách kết nối; benchmark ≥20 câu có evidence cùng ≥4 câu thiếu evidence, split và nhãn.
- Trace retrieval và agent: tool call/arguments/results, context, câu trả lời/citation, status, thời gian/chi phí; bảng metric và audit theo BENCHMARK.
- Báo cáo cá nhân `report/individual/MSSV_HoTen.md` đã đổi tên theo MSSV và họ tên; ghi cách kiểm chứng, lỗi, giả thuyết và cải tiến.
- Nếu dữ liệu bị hạn chế, không commit dữ liệu mật; nêu cách người chấm được cấp quyền hoặc tái tạo.

## Checklist

- [ ] Repo có tên đúng, README chỉ cách chạy, người chấm mở được và link đã nộp.
- [ ] Dùng đúng input/split, benchmark evidence được kiểm chứng, không tune bằng test.
- [ ] Dense, BM25, hybrid và cấu hình cải tiến được chọn có kết quả/trace theo GUIDE.
- [ ] Agent model thật gọi tool; context đúng budget, có nguồn; audit trả lời, citation và abstention dựa trên evidence thật.
- [ ] Ghi lệnh/test thực tế và nguồn tham khảo.
- [ ] Không commit secrets, `.env`, `.venv`, dữ liệu riêng tư hoặc kết quả không có quyền chia sẻ.
