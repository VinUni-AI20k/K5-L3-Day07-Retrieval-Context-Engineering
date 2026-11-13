# Nộp bài Day 7

## Tạo repo cá nhân

Đặt tên theo lớp, ví dụ `K5-L3A-DAY07-MSSV-HoTen-RetrievalContext` hoặc `K5-L3B-DAY07-MSSV-HoTen-RetrievalContext`. Tên không dấu, không khoảng trắng. Fork repo đề bài hoặc clone rồi đổi remote:

```bash
git clone https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering.git <TEN_REPO>
cd <TEN_REPO>
git remote rename origin upstream
git remote add origin <URL_REPO_CA_NHAN>
git push -u origin main
```

Thay phần trong `< >` bằng tên và địa chỉ thật. Nộp link theo hướng dẫn giảng viên; không push bài vào repo đề bài.

## Danh sách bài nộp

- [ ] Code agent, ít nhất 3 phương pháp retrieval (gồm dense), test và hướng dẫn chạy.
- [ ] Embedding model, vector store, cách kết nối và dữ liệu được phép chia sẻ hoặc cách cấp quyền/tái tạo.
- [ ] Benchmark gồm ít nhất 20 câu có evidence và 4 câu thiếu evidence, đã chia dev/test.
- [ ] Kết quả từng query và tool call; context, câu trả lời, citation, lỗi, thời gian và chi phí.
- [ ] Ít nhất 2 cấu hình cải thiện; bảng benchmark, nhãn, phân tích lỗi và lý do chọn theo [BENCHMARK.md](BENCHMARK.md).
- [ ] Sao chép và điền [mẫu báo cáo](report/individual/MSSV_HoTen.md), đổi tên theo MSSV và họ tên.
- [ ] Người chấm có quyền xem repo; không nộp dữ liệu mật, `.env`, API key hoặc token.

## Nếu làm thử thách nâng cao

- [ ] Nguồn và quyền truy cập tài liệu từ 100 trang; thống kê, cấu hình index và phần chưa xử lý.
- [ ] Benchmark dev/test, đáp án và evidence theo từng trang/vùng, gồm bảng, ảnh và biểu đồ.
- [ ] Trace, nhãn và lý do cho toàn bộ test; tỷ lệ đạt chung và theo nhóm, lỗi, thời gian và chi phí.
- [ ] Cách chạy tái lập và bằng chứng đạt ít nhất 90% theo [ADVANCED.md](ADVANCED.md).
