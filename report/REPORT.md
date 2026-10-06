# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Vũ Văn Diện | 2A202602418 | Cài đặt harness, chạy thí nghiệm, phân tích và viết báo cáo |

- Mô hình: `anthropic:claude-haiku-4-5-20251001` qua cổng Anthropic-compatible; `LAB_TEMPERATURE=0`; `recursion_limit=60` cho các lượt học ban đầu và 40 cho các lượt chính thức còn lại. Riêng `subagents/logs-eval` dùng lại 60 sau khi trần 40 gây `GraphRecursionError`.
- Deep Agents `0.7.21`; Python 3.12 trong `python:3.12-slim`; chạy bằng Docker trên máy chủ Windows.
- Có 18 lượt chính thức, tổng cộng 3.375.281 token theo metadata của provider; thêm 3 lượt development của skills-auto và các rerun hạ tầng được ghi ở Phụ lục. Mỗi cấu hình chỉ có một kết quả chính thức cho mỗi task.
- Commit/tag `freeze`: `4198cb7`; commit giả thuyết đứng trước tag: `b0e16c8`.

## 2. Giả thuyết (viết trước tag `freeze`)

- H1 (subagents so với baseline): dự đoán `subagents` không tăng điểm trung bình eval so với `baseline` và kém hiệu quả token. Trên tập học, cả hai đạt cùng số check ở ba task trong lượt hợp lệ đầu tiên, trong khi subagents dùng trung bình khoảng 235k token so với 155k của baseline (xấp xỉ 1,52 lần); một task còn không gọi subagent. Subagent cô lập ngữ cảnh chỉ hữu ích khi lời giao việc chứa đủ quy tắc, nên chi phí thêm chưa có căn cứ cho thấy sẽ chuyển thành điểm.
- H2 (skills-auto so với baseline): dự đoán `skills-auto` hòa hoặc chỉ cải thiện rất ít so với `baseline` trên eval, nhưng tốn thêm token để đọc skill. Cả ba task học đều đã đọc 1–2 skill mà điểm không tăng. Kết quả này phù hợp với nhận định trong tài liệu lab rằng skill do mô hình tự sinh trung bình có thể không có lợi, dù checklist tổng quát vẫn có khả năng cứu một số check quy ước tương tự.
- H3 (tác vụ học so với tác vụ đánh giá): dự đoán điểm trung bình eval thấp hơn learn ở cả ba điều kiện vì mỗi task eval có dữ liệu mới và thêm một quy ước chưa xuất hiện trong feedback học. Nếu skill chỉ mã hóa các quy ước đã thất bại trên learn, lợi ích khó chuyển sang quy ước mới; đây là nguy cơ transfer gap/quá khớp được nêu trong phần tham khảo SkillEvolBench của lab.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Agent mặc định nhìn thấy các file tool `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; shell tool `execute`; và subagent tool `task`. `execute` là công cụ chạy lệnh.
2. `general-purpose` dùng cho nghiên cứu phức tạp, tìm kiếm file/nội dung và tác vụ nhiều bước. Mỗi lần gọi mặc định là một phiên stateless: nó chỉ thấy prompt được gửi và trả về một báo cáo cuối, nên agent chính phải truyền đầy đủ mục tiêu, quy tắc và đường dẫn.
3. Từ mô tả `task`: “Put full detail in the prompt and state exactly what it should return”. Từ mô tả `execute`: phải tránh dùng `find`/`grep` trong shell và dùng `glob`/`grep` file tool thay thế.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

Sau khi loại bỏ lỗi CRLF của môi trường Windows, baseline đạt toàn bộ **18/18 check kỹ thuật** và thất bại **9/9 check quy ước**. Vì vậy mọi lỗi thật còn lại thuộc nhóm E.

| Tác vụ | Check thất bại | Nhóm lỗi | Bằng chứng từ `detail` |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | “RULE: every public function ... has type annotations ...” |
| code-learn | `rule_regression_tests` | E | “RULE: add tests/test_regressions.py ... at least 3” |
| code-learn | `rule_changelog` | E | “RULE: record each fix in CHANGELOG.md under ... Unreleased” |
| data-learn | `rule_money_in_cents` | E | “RULE: money values in answer.json are integer cents” |
| data-learn | `rule_meta_block` | E | “RULE: answer.json has an object meta ...” |
| data-learn | `rule_clean_csv` | E | “RULE: write workspace/clean.csv ...” |
| logs-learn | `rule_service_names` | E | “RULE: service names ... lower-case with '-' replaced by '_'” |
| logs-learn | `rule_sorted_errors` | E | “RULE: errors is sorted by service, then by timestamp_utc” |
| logs-learn | `rule_schema_header` | E | “RULE: top-level object has schema_version 2 and generated_by ...” |

Nhóm E chiếm 9/9 lỗi thật. Trace cho thấy agent đọc đề, docstring/dữ liệu, sửa nguyên nhân kỹ thuật và kiểm thử lại; bằng chứng phủ định cho nhóm A–D là 18/18 check kỹ thuật đã đạt. Skill có thể phòng ngừa một phần nhóm E bằng checklist bắt buộc đọc quy ước, kiểm kê artifact và xác thực schema, nhưng không thể biết trước một quy ước hoàn toàn mới nếu đề và feedback không nêu nó.

## 5. Điều kiện `subagents` (Phần 2.3)

- Định nghĩa ba vai trò: `explorer` đọc và báo cáo nhưng không sửa; `implementer` sửa file và chạy kiểm tra; `reviewer` kiểm tra độc lập mà không sửa. `description` của mỗi vai trò nêu tình huống kích hoạt để agent chính chọn đúng người.
- Trong kết quả chính thức, `subagent_calls`: code-learn = 0, data-learn = 1, logs-learn = 0, code-eval = 1, data-eval = 0, logs-eval = 1. Việc code-learn thay đổi từ 1 ở lượt development sang 0 ở lượt chính thức cho thấy quyết định ủy quyền có nhiễu ngay cả ở nhiệt độ 0.
- Lời giao data-learn truyền chi tiết quy tắc kỹ thuật nhưng chỉ nói chung “Acme reporting conventions”, nên subagent không thể suy ra quy ước ẩn. Ở code-eval và logs-eval, lời giao cho `implementer` có file, format và bước kiểm tra khá đầy đủ; agent chính tiếp tục kiểm tra output trước khi kết thúc.
- Trên sáu task chính thức, subagents dùng trung bình 215.265 token/run, cao hơn baseline 155.227 token/run khoảng 38,7%. Điểm learn không đổi (0,66); điểm eval tăng từ 0,42 lên 0,57 nhờ check kỹ thuật data/logs, nhưng code-eval giảm một check.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Curator chạy một lần, tạo ba skill; không skill nào bị xóa và không nội dung nào được sửa tay. Cả ba qua `validate_skill`, không chứa marker eval.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `validate-output-schema` | Tổng quát cho JSON/CSV/file có schema; ví dụ là kiểu dữ liệu và format, không chứa đáp án task | Đúng: yêu cầu liệt kê schema, viết kiểm tra, sửa nguyên nhân và kiểm tra lại | 13 dòng; description kích hoạt sau khi tạo structured output; được đọc ở data/logs và cả code-eval |
| `protect-original-files` | Tổng quát cho task cấm sửa file gốc | Đúng: lập allow-list, kiểm tra diff/checksum và khôi phục file bảo vệ nếu cần | 12 dòng; description nêu đúng điều kiện “task forbids modifying”; được đọc ở code-learn |
| `audit-required-artifacts` | Tổng quát cho task có tài liệu/test/artifact bắt buộc; các tên quy ước Acme được GUIDE cho phép | Đúng: kiểm kê sự tồn tại, vị trí, format, số lượng và chạy validation | 12 dòng; description kích hoạt sau implementation; được đọc ở code-learn và logs-learn |

Trong lượt development đã sao lưu tại `results/skills-auto-dev/`, `skills_read` lần lượt là code = 2, data = 1, logs = 2. Ở sáu lượt chính thức, mọi run đều đọc ít nhất một skill, `skills_modified=false`, và cùng hash `130309bce4cb...`. Dù agent đọc skill, cả 21 house rule (9 learn + 12 eval) vẫn thất bại: đọc skill chưa đồng nghĩa agent biết hoặc thực thi được những quy ước không xuất hiện trong đề.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 7/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 6/9 |
| code-eval | 7/11 | 6/11 | 7/11 |
| data-eval | 3/9 | 5/9 | 5/9 |
| logs-eval | 3/10 | 6/10 | 6/10 |
| **Mean score - learning tasks** | 0.66 | 0.66 | 0.66 |
| **Mean score - evaluation tasks** | 0.42 | 0.57 | 0.60 |
| **Mean tokens per run** | 155,227 | 215,265 | 192,054 |
| **Runs that read a skill** | 0/6 | 0/6 | 6/6 |

Kết quả `check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     13/18         0/12         155,574      0/3
baseline      learn    18/18         0/9          154,879      0/3
subagents     eval     17/18         0/12         200,137      0/3
subagents     learn    18/18         0/9          230,393      0/3
skills-auto   eval     18/18         0/12         175,314      3/3
skills-auto   learn    18/18         0/9          208,795      3/3
```

Không có run chính thức nào có `error` hoặc `skills_modified=true`. Một run `subagents/logs-eval` với trần 40 đã bị `GraphRecursionError` và được chạy lại một lần ở trần 60; run lỗi đã bị kết quả hợp lệ ghi đè.

## 8. Phân tích

1. Không điều kiện nào cải thiện learn: cả ba cùng 0,66. Trên eval, subagents tăng từ 0,42 lên 0,57 và skills-auto lên 0,60; H1 và H2 vì vậy bị bác bỏ, còn H3 được ủng hộ vì eval thấp hơn learn ở mọi điều kiện. Không có mẫu “tăng learn nhưng không tăng eval”; ngược lại, chỉ eval tăng, nên không có bằng chứng quá khớp theo tiêu chí điểm học tăng nhưng không chuyển giao.
2. Baseline learn đạt 18/18 kỹ thuật nhưng 0/9 quy ước. Trên eval, baseline đạt 13/18 kỹ thuật; subagents 17/18 và skills-auto 18/18, trong khi cả ba đều 0/12 quy ước. Như vậy chênh lệch eval hoàn toàn đến từ check kỹ thuật. Quy ước mới không được skill giúp vì skill chỉ yêu cầu kiểm tra các requirement đã biết; các convention ẩn như `rule_sorted_keys_format`, `rule_version_bump` và `rule_source_line` không thể suy ra từ mô tả task.
3. Ví dụ có ích: ở logs-eval, agent đọc `validate-output-schema`, viết script xác thực timestamp/level/repeat count và đạt `timestamps_utc`, `levels_uppercase`, `repeat_counts`; baseline trượt cả ba. Đây là liên hệ cơ chế chứ chưa chứng minh nhân quả, vì subagents cũng đạt ba check đó. Ví dụ không giúp: data-eval đọc đúng skill nhưng vẫn dùng tiền dạng số thực và chỉ xác thực “number”, nên trượt `rule_money_in_cents`; skill đã được đọc nhưng agent áp dụng theo đề công khai thay vì ví dụ cents trong checklist.
4. Token trung bình toàn bộ: baseline 155.227, subagents 215.265 (+38,7%), skills-auto 192.054 (+23,7%). Riêng eval, điểm trên một triệu token xấp xỉ 2,72 (baseline), 2,83 (subagents), 3,41 (skills-auto), nên skills-auto hiệu quả nhất trên eval; nếu tính cả learn không đổi thì baseline vẫn rẻ nhất. Multi-agent chỉ đáng chi phí có điều kiện: nó cải thiện data/logs eval nhưng không cải thiện learn, làm code-eval giảm một check, và có một lượt chạm giới hạn đệ quy.
5. Không có marker eval trong skill; `validate_skill` đều đạt, tag/hash chứng minh skill được sinh và đóng băng trước eval, và không run nào sửa skill. Skill có ví dụ từ quy ước học nhưng không có đáp án/định danh eval; việc 0/12 house rule eval cũng là bằng chứng phủ định cho rò rỉ. Nguy cơ quá khớp vẫn tồn tại ở nội dung ví dụ, nhưng không biểu hiện thành tăng điểm learn hay ăn đúng convention eval.
6. Lượt development của skills-auto là 6/10, 5/8, 6/9; lượt chính thức là 7/10, 5/8, 6/9. Chênh code +1 check là do lỗi CRLF đã xác định (`tests_not_modified`), không phải hiệu quả skill; hai task không bị lỗi hạ tầng có chênh lệch 0. Số lần chạy quá ít để ước lượng nhiễu xác suất, nhưng token thay đổi mạnh giữa hai lượt cho thấy trajectory vẫn biến động dù điểm giữ nguyên.

## 9. Hạn chế và tính hợp lệ

1. Chỉ có ba họ task và một task cho mỗi vai trò trong mỗi họ; một ngoại lệ có thể làm thay đổi mạnh trung bình, nên không thể khái quát sang mọi agent workflow.
2. Mỗi cấu hình chỉ chạy một lần chính thức trong khi LLM và việc chọn tool có nhiễu; chênh lệch nhỏ có thể do ngẫu nhiên thay vì do subagent/skill.
3. Chỉ dùng một model (`claude-haiku-4-5-20251001`) và một gateway; kết luận về chi phí, tool calling và khả năng tuân thủ không đại diện cho model khác.
4. Feedback học chủ yếu tiết lộ quy ước do bộ task thiết kế; curator có thể quá khớp các quy ước này và không chuyển giao sang quy ước mới ở eval.
5. Token callback cộng toàn bộ message/model calls theo metadata của provider nhưng không đo chi phí tiền thực tế của gateway; so sánh token là tương đối.

## 10. Kết luận

Trên tập học, subagents và skill không cải thiện điểm so với baseline 0,66. Trên eval, skills-auto đạt cao nhất 0,60, tiếp theo subagents 0,57 và baseline 0,42, nhưng toàn bộ lợi ích đến từ check kỹ thuật chứ không phải house rule. Skills-auto hiệu quả token tốt nhất trên eval, còn baseline rẻ nhất nếu tính cả các task học không đổi. Kết quả không cho thấy rò rỉ dữ liệu, nhưng chỉ một lần chạy và ba họ task chưa đủ để kết luận rộng. Bước tiếp theo nên lặp mỗi cấu hình ít nhất ba lần và cải thiện skill theo hướng buộc đối chiếu từng yêu cầu đầu ra bằng kiểm tra máy thực thi được.

## Phụ lục

- Lệnh chính đã chạy: `pytest`; `python scripts/tour.py`; các lệnh `python -m lab.runner` cho `baseline`, `subagents`, `skills-auto` trên learn/eval; `python -m lab.curator`; `python -m lab.compare`; `python scripts/check_breakdown.py`; `python scripts/verify_freeze.py` (kết quả: `checked 6 runs of skill conditions: OK`).
- Lượt `code-learn` đầu tiên bị check `tests_not_modified` sai do checkout CRLF trên Windows trong khi checker dùng hash LF. Hai test file được chuẩn hóa byte LF mà không đổi nội dung Git; baseline code-learn được chạy lại và check này đã đạt.
- Một lượt rerun `subagents/code-learn` gặp `API_KEY_QUOTA_EXHAUSTED`; một lượt `subagents/logs-eval` gặp `GraphRecursionError` ở trần 40. Cả hai được thay bằng lượt không lỗi; không dùng run có `error` trong bảng.
- Thử thách mở rộng: không thực hiện.
