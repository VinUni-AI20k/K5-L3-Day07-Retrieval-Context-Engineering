# Nộp bài Day 7

## Tạo repo cá nhân

Đặt tên theo lớp, ví dụ `K5-L3A-DAY07-MSSV-HoTen-RetrievalContext` hoặc `K5-L3B-DAY07-MSSV-HoTen-RetrievalContext`. Tên không dấu, không khoảng trắng. Fork repo đề bài hoặc clone rồi đổi địa chỉ repo:

```bash
git clone https://github.com/VinUni-AI20k/K5-L3-Day07-Retrieval-Context-Engineering.git <TEN_REPO>
cd <TEN_REPO>
git remote rename origin upstream
git remote add origin <URL_REPO_CA_NHAN>
git push -u origin main
```

Thay các phần trong `< >` bằng tên và địa chỉ thật. Nộp link theo hướng dẫn giảng viên; không push bài vào repo đề bài.

## Danh sách bài nộp

- [ ] Mã agent, công cụ tìm kiếm, ba cách tìm, kiểm thử và hướng dẫn chạy.
- [ ] Thông tin mô hình tạo vector, kho vector, cách kết nối và dữ liệu được phép chia sẻ hoặc cách cấp quyền/tái tạo.
- [ ] Ít nhất 20 câu có bằng chứng và 4 câu thiếu bằng chứng, đã chia tập.
- [ ] Kết quả từng lần tìm và gọi công cụ; nội dung đưa vào mô hình, câu trả lời, nguồn, lỗi, thời gian và chi phí.
- [ ] Bảng đánh giá, nhãn thủ công, phân tích lỗi và cải thiện theo [BENCHMARK.md](BENCHMARK.md).
- [ ] Sao chép và điền [mẫu báo cáo](report/individual/MSSV_HoTen.md), đổi tên theo MSSV và họ tên.
- [ ] Người chấm có quyền xem repo; không nộp dữ liệu mật, `.env`, API key hoặc token.
