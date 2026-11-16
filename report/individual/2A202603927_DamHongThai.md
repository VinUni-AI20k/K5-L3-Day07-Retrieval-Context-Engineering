# Báo cáo Day 7 — Retrieval, agent và đánh giá test

## Dữ liệu và benchmark

- **Corpus:** các trích đoạn từ *A Review of Algebra*, Project Gutenberg eBook #38536; 54 đơn vị văn bản, 168 chunk. Snapshot Day 6 strategy C: `data/day06_strategy_c_chunks.json`.
- **Nguồn/quyền:** Project Gutenberg, https://www.gutenberg.org/ebooks/38536; sách public domain tại Hoa Kỳ theo thông tin eBook. Người dùng ngoài Hoa Kỳ cần tự kiểm tra luật địa phương.
- **Embedding/vector store:** OpenRouter `openai/text-embedding-3-small`, 1536 chiều; PostgreSQL 16.16 + pgvector 0.8.7, cosine distance, exact scan. Query embedding cùng model với vector đã index.
- **Agent/model:** OpenRouter `openai/gpt-4o-mini`, đọc `CHAT_MODEL` và `OPENROUTER_API_KEY` từ `.env` Day 6; không ghi key vào code hoặc trace.
- **Benchmark:** `data/day07_questions.json` chứa query; `data/day07_gold.json` chỉ dùng sau khi chạy agent để chấm. Dev có 18 câu answerable + 2 câu thiếu evidence; test DAY07 mới có 5 câu answerable + 2 câu thiếu evidence. Query tiếng Việt trên corpus tiếng Anh; không dịch query. Chỉ dùng section filter được cung cấp trực tiếp trong câu hỏi.
- **Tiêu chí:** Hit@1 / Evidence Hit@3 tính trên câu answerable; Context Evidence Rate là số context cuối có evidence gold / số câu answerable. Grounded answer chấm 0/1/2; citation phải nằm trong context và hỗ trợ câu trả lời; abstention của câu thiếu evidence cần được đối chiếu corpus.

## Retrieval và thử nghiệm trên dev

Ba phương pháp dùng cùng corpus, benchmark, top-3 và budget context 800 ký tự. Dense/hybrid truy vấn Day 6 strategy C; hybrid hợp nhất candidate của hai nhánh bằng RRF constant 60. Median là thời gian mỗi query, không gồm khởi tạo index. USD embedding API chưa lấy được từ billing nên ghi riêng usage.

| Cấu hình | Phương pháp / thay đổi | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Context TB | Median/query | Embedding usage / chi phí |
|---|---|---:|---:|---:|---:|---:|---|
| TF-IDF, top-3, budget 800 | Lexical baseline offline | 4/18 (22.2%) | 11/18 (61.1%) | 6/18 (33.3%) | 449.4 ký tự | 0.159 ms | 0 request; $0 |
| Dense Day 6 C, top-3, budget 800 | Dense baseline trên vector store đã có | 4/18 (22.2%) | 10/18 (55.6%) | 6/18 (33.3%) | 534.2 ký tự | 1158.2 ms | 20 request / 889 token; USD chưa biết |
| Hybrid RRF, candidate-k 10, top-3, budget 800 | Dense + TF-IDF; candidate 10 mỗi nhánh | 5/18 (27.8%) | 11/18 (61.1%) | 6/18 (33.3%) | 599.0 ký tự | 1149.7 ms | 20 request / 889 token; USD chưa biết |
| Hybrid RRF, candidate-k 5, top-3, budget 800 | Thử giảm candidate | 5/18 (27.8%) | 11/18 (61.1%) | 5/18 (27.8%) | 593.7 ký tự | 1195.2 ms | 20 request / 889 token; USD chưa biết |
| Hybrid RRF, candidate-k 10, top-3, budget 1200 | Thử tăng context budget | 5/18 (27.8%) | 11/18 (61.1%) | 5/18 (27.8%) | 817.2 ký tự | 1132.2 ms | 20 request / 889 token; USD chưa biết |

Hai cấu hình cải thiện được đo riêng trên dev. Candidate-k 5 không tăng metric hay giảm thời gian; budget 1200 tăng độ dài context nhưng không tăng context evidence rate. Cấu hình hybrid candidate-k 10 được chốt trước test vì Hit@1 cao nhất, giữ Hit@3 bằng TF-IDF và tăng một câu Hit@1 so với hai baseline. Thời gian khởi tạo index: TF-IDF khoảng 0.000005 s; dense/hybrid khoảng 0.269–0.327 s.

### Hai lỗi dev đã phân tích

1. **D05 — cách giải hệ phương trình:** kết quả hybrid không có evidence trong top-3; các chunk được xếp hạng là bài tập, không có đoạn liệt kê addition/subtraction, substitution và comparison. Query tiếng Việt trên sách tiếng Anh là lỗi retrieval đa ngôn ngữ.
2. **D15 — nghiệm ngoại lai:** exact section filter `RADICALS` loại đoạn evidence “Always check results…” ở `u003`, vì metadata gắn section tổng quát. Đây là lệch granularity/metadata; tăng budget không thể lấy lại chunk đã bị filter.

D02/D03 cũng cho thấy context packing có thể bỏ evidence ở thứ hạng sau khi chunk trước chiếm budget. Hai thử nghiệm budget/candidate không khắc phục được các lỗi này.

## Kết quả retrieval trên test DAY07

Cấu hình test được giữ nguyên theo quyết định dev. Các lệnh chạy lại và trace đầy đủ nằm trong `starter/results/task8-test-tfidf/` và `starter/results/task8-test-hybrid/`.

| Cấu hình | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Context TB | Median/query | Embedding usage / chi phí |
|---|---:|---:|---:|---:|---:|---|
| TF-IDF baseline, top-3, budget 800 | 3/5 (60%) | 5/5 (100%) | 0/5 (0%) | 505.1 ký tự | 0.120 ms | 0 request; $0 |
| Hybrid RRF đã chốt, candidate-k 10, budget 800 | 4/5 (80%) | 5/5 (100%) | 0/5 (0%) | 505.1 ký tự | 1109.1 ms | 7 request / 344 token; USD chưa biết |

Đã đọc cả 5 câu test có đáp án cho mỗi cấu hình. **Context score: mức 0 = 5/5, mức 1 = 0/5, mức 2 = 0/5** ở cả hai cấu hình. Retrieval đưa gold evidence vào top-3 cho 5/5, nhưng packer bỏ chunk đó khỏi context cuối (chunk vượt budget hoặc chunk khác được chọn trước). Vì vậy kết quả retrieval tốt không dẫn tới câu trả lời có căn cứ.

## Agent, câu trả lời và citation

Agent chạy bằng `starter/run_agent_benchmark.py`; mỗi query tối đa 4 lượt search, top-3 và context budget 800 ký tự. Gold không được nạp vào tiến trình agent. Trace lưu model calls, query/tool results, context cuối, answer, citation, thời gian, token và lỗi.

| Cấu hình / split | Tool use | Search calls | Grounded answer 0 / 1 / 2; trung bình /2 | Citation hợp lệ | Câu trả lời có citation | Abstention đúng | Từ chối nhầm | Lỗi |
|---|---:|---:|---|---|---|---|---|---:|
| TF-IDF / test | 6/6 query chạy thành công | 18 ở query thành công; 1 query lỗi sau 1 search | 5 / 0 / 0; **0.00** | 0/0 (không áp dụng) | 0/0 (không áp dụng) | 1/2 quan sát được; 1/1 trong query thành công | 5/5 | 1/7 |
| Hybrid RRF / test | 7/7 | 19 | 5 / 0 / 0; **0.00** | 0/0 (không áp dụng) | 0/0 (không áp dụng) | 2/2 | 5/5 | 0/7 |

Model: `openai/gpt-4o-mini`. TF-IDF chạy 26 lượt model, 19,272 prompt + 695 completion token; usage ghi nhận $0.0033078, một request lỗi không có chi phí trả về. Hybrid chạy 26 lượt model, 19,961 prompt + 832 completion token, chi phí model theo usage là $0.00349335. Hybrid còn dùng 19 request embedding / 376 token trong agent run; chi phí embedding chưa lấy được từ billing. Mọi answerable đều bị abstain do không có evidence trong context, nên điểm answer 0 và không có citation để xác nhận. Đây là false abstention, không phải câu trả lời đúng.

### Nhãn từng câu test

| Query | Loại | TF-IDF: status / search | Hybrid: status / search | Nhãn và lý do |
|---|---|---|---|---|
| DAY7-T01 | Có đáp án | Abstain / 4 | Abstain / 2 | Answer 0; evidence của tổng/tích nghiệm không có trong context cuối. |
| DAY7-T02 | Có đáp án | Abstain / 4 | Abstain / 4 | Answer 0; chunk có công thức S không được pack vào context. |
| DAY7-T03 | Có đáp án | Abstain / 4 | Abstain / 2 | Answer 0; chunk công thức số hạng n không được pack vào context. |
| DAY7-T04 | Có đáp án | Abstain / 1 | Abstain / 4 | Answer 0; chunk công thức tổng cấp số nhân không được pack vào context. |
| DAY7-T05 | Có đáp án | Abstain / 1 | Abstain / 1 | Answer 0; chunk gold được retrieve nhưng context cuối chứa chunk khác. |
| DAY7-T06 | Thiếu evidence | **Error (HTTP 500)** / 1 | Abstain / 2 | Corpus không có quy tắc logarithm của tích. Hybrid từ chối đúng; baseline lỗi provider nên không tính abstention. |
| DAY7-T07 | Thiếu evidence | Abstain / 4 | Abstain / 4 | Corpus không có định thức/Cramer; hai lần chạy từ chối đúng. |

Không có câu trả lời hay citation nào được sinh ra; vì vậy citation validity và coverage là `0/0 (không áp dụng)`, không phải citation pass. Không có lỗi retrieval/vector store trong final run; có 1 lỗi provider chat HTTP 500 ở TF-IDF T06. Một lần chạy trước đó gặp HTTP 400 `context_length_exceeded` ở T07: trace history khi đó lặp lại nguyên văn kết quả tìm kiếm qua nhiều lượt. Đã sửa agent để giữ metadata gọn trong decision history trong khi trace đầy đủ vẫn được lưu; test tự động xác nhận không lặp full chunk text. Final run không còn lỗi vượt context; test set được chạy lại sau sửa lỗi nên kết quả agent này là chẩn đoán trên bộ đã quan sát, không phải đánh giá mù độc lập. Cấu hình retrieval đã chốt trên dev không đổi.

### Lệnh tái lập

Chạy từ thư mục gốc Day 7 trong PowerShell. Thay `<DAY06_STARTER>` bằng thư mục `starter` của repo Day 6 có `.venv` và `.env`. Không đưa `.env` vào repo.

```powershell
python -m unittest discover -s tests -v
python starter\retrieval.py --chunks data\day06_strategy_c_chunks.json --questions data\day07_questions.json --gold data\day07_gold.json --split test --method tfidf --budget 800 --output starter\results\task8-test-tfidf
& <DAY06_STARTER>\.venv\Scripts\python.exe starter\retrieval.py --chunks data\day06_strategy_c_chunks.json --questions data\day07_questions.json --gold data\day07_gold.json --split test --method hybrid --candidate-k 10 --budget 800 --day6-starter <DAY06_STARTER> --dotenv <DAY06_STARTER>\.env --output starter\results\task8-test-hybrid
& <DAY06_STARTER>\.venv\Scripts\python.exe starter\run_agent_benchmark.py --chunks data\day06_strategy_c_chunks.json --questions data\day07_questions.json --split test --method tfidf --top-k 3 --budget 800 --max-searches 4 --dotenv <DAY06_STARTER>\.env --output starter\results\task8-agent-test-tfidf-final
& <DAY06_STARTER>\.venv\Scripts\python.exe starter\run_agent_benchmark.py --chunks data\day06_strategy_c_chunks.json --questions data\day07_questions.json --split test --method hybrid --candidate-k 10 --top-k 3 --budget 800 --max-searches 4 --day6-strategy C --day6-starter <DAY06_STARTER> --dotenv <DAY06_STARTER>\.env --output starter\results\task8-agent-test-hybrid-final
python starter\agent_metrics.py --cases starter\results\task8-test-cases.json --traces starter\results\task8-agent-test-tfidf-final\traces.json --reviews starter\results\task8-test-reviews-tfidf.json --split test --output starter\results\task8-agent-test-tfidf-final\metrics.json
python starter\agent_metrics.py --cases starter\results\task8-test-cases.json --traces starter\results\task8-agent-test-hybrid-final\traces.json --reviews starter\results\task8-test-reviews-hybrid.json --split test --output starter\results\task8-agent-test-hybrid-final\metrics.json
```

Artifacts:

- Retrieval traces/summary: `starter/results/task8-test-tfidf/` and `starter/results/task8-test-hybrid/`.
- Agent traces/usage/metrics: `starter/results/task8-agent-test-tfidf-final/` and `starter/results/task8-agent-test-hybrid-final/`.
- Evaluator labels/reviews: `starter/results/task8-test-cases.json`, `starter/results/task8-test-reviews-tfidf.json`, `starter/results/task8-test-reviews-hybrid.json`.
- Initial diagnostic attempts and provider/context errors: `starter/results/task8-agent-test-tfidf/` and `starter/results/task8-agent-test-hybrid/`.

## Giới hạn và kết luận

Hybrid thắng Hit@1 trên test (4/5 so với 3/5) nhưng không cải thiện Context Evidence Rate (0/5 ở cả hai); agent do đó từ chối nhầm toàn bộ câu answerable. Kết quả hiện tại **không chứng minh chất lượng QA đầu-cuối**. Việc tiếp theo nên làm trên dev: sửa context packing để ưu tiên/trích đoạn evidence vừa budget, tránh search lặp cùng query, sau đó chạy lại agent và audit citation trên một test mới chưa sử dụng. Chi phí embedding cụ thể còn phụ thuộc billing provider.

## Thử thách nâng cao

Không thực hiện; corpus hiện tại không phải tài liệu từ 100 trang có bảng, ảnh và biểu đồ như yêu cầu bonus.
