# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Vũ Văn Diện | 2A202602418 | Cài đặt harness, chạy thí nghiệm, phân tích và viết báo cáo |

- Mô hình: `anthropic:claude-haiku-4-5-20251001` qua cổng Anthropic-compatible; `LAB_TEMPERATURE=0`; `recursion_limit=60`.
- Deep Agents `0.7.21`; Python 3.12 trong `python:3.12-slim`; chạy bằng Docker trên máy chủ Windows.
- Ngân sách được đo bằng `UsageMetadataCallbackHandler`; mỗi cấu hình chạy một lần chính thức cho mỗi task. Các lần rerun do lỗi hạ tầng được ghi ở Phụ lục.
- Commit của tag `freeze`: cập nhật sau khi tạo tag.

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
- Ở lượt học hợp lệ đầu tiên, `subagent_calls`: code-learn = 1 (`explorer`), data-learn = 1 (giao triển khai/phân tích), logs-learn = 0. Không gọi subagent ở logs-learn là hợp lệ: agent chính đánh giá có thể tự xử lý luồng phân tích log.
- Lời giao việc code-learn liệt kê rõ file và bốn nhóm yêu cầu docstring; báo cáo được agent chính đối chiếu bằng test. Lời giao data-learn truyền chi tiết quy tắc kỹ thuật nhưng chỉ nói chung “Acme reporting conventions”, nên subagent không có thông tin để suy ra ba quy ước ẩn.
- Trên ba task học, lượt hợp lệ đầu tiên của subagents dùng trung bình khoảng 234.982 token và 54,1 giây, so với baseline khoảng 154.880 token và 34,6 giây: xấp xỉ 1,52 lần token và 1,56 lần thời gian mà chưa tăng điểm.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Curator chạy một lần, tạo ba skill; không skill nào bị xóa và không nội dung nào được sửa tay. Cả ba qua `validate_skill`, không chứa marker eval.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `validate-output-schema` | Tổng quát cho JSON/CSV/file có schema; ví dụ là kiểu dữ liệu và format, không chứa đáp án task | Đúng: yêu cầu liệt kê schema, viết kiểm tra, sửa nguyên nhân và kiểm tra lại | 13 dòng; description kích hoạt sau khi tạo structured output; được đọc ở data-learn và logs-learn |
| `protect-original-files` | Tổng quát cho task cấm sửa file gốc | Đúng: lập allow-list, kiểm tra diff/checksum và khôi phục file bảo vệ nếu cần | 12 dòng; description nêu đúng điều kiện “task forbids modifying”; được đọc ở code-learn |
| `audit-required-artifacts` | Tổng quát cho task có tài liệu/test/artifact bắt buộc; các tên quy ước Acme được GUIDE cho phép | Đúng: kiểm kê sự tồn tại, vị trí, format, số lượng và chạy validation | 12 dòng; description kích hoạt sau implementation; được đọc ở code-learn và logs-learn |

Trong lượt development đã sao lưu tại `results/skills-auto-dev/`, `skills_read` lần lượt là code = 2, data = 1, logs = 2; `skills_modified=false` cho cả ba và cùng hash `130309bce4cb...`. Dù agent đọc skill, điểm vẫn bằng baseline trước khi chuẩn hóa CRLF, cho thấy đọc skill chưa đồng nghĩa thực thi đủ mọi checklist.

## 7. Kết quả so sánh (Phần 4.3, 4.4)

Chưa chạy tập eval tại thời điểm viết giả thuyết. Bảng này sẽ được thay bằng đầu ra chính thức của `python -m lab.compare` sau tag `freeze`.

## 8. Phân tích

Sẽ hoàn thiện sau khi có kết quả chính thức của sáu task ở cả ba điều kiện. Quan sát trước eval: subagents và skills-auto chưa cải thiện điểm learn; cả hai làm tăng ngữ cảnh/token, và mọi lỗi baseline còn lại là quy ước tổ chức chứ không phải lỗi kỹ thuật.

## 9. Hạn chế và tính hợp lệ

1. Chỉ có ba họ task và một task cho mỗi vai trò trong mỗi họ; một ngoại lệ có thể làm thay đổi mạnh trung bình, nên không thể khái quát sang mọi agent workflow.
2. Mỗi cấu hình chỉ chạy một lần chính thức trong khi LLM và việc chọn tool có nhiễu; chênh lệch nhỏ có thể do ngẫu nhiên thay vì do subagent/skill.
3. Chỉ dùng một model (`claude-haiku-4-5-20251001`) và một gateway; kết luận về chi phí, tool calling và khả năng tuân thủ không đại diện cho model khác.
4. Feedback học chủ yếu tiết lộ quy ước do bộ task thiết kế; curator có thể quá khớp các quy ước này và không chuyển giao sang quy ước mới ở eval.
5. Token callback cộng toàn bộ message/model calls theo metadata của provider nhưng không đo chi phí tiền thực tế của gateway; so sánh token là tương đối.

## 10. Kết luận

Kết luận cuối sẽ được viết sau các lượt chạy eval đã đóng băng. Dữ liệu học hiện tại chỉ hỗ trợ nhận định rằng subagents tăng chi phí mà chưa tăng điểm, còn skill được đọc nhưng chưa chứng minh cải thiện.

## Phụ lục

- Lệnh chính đã chạy: `pytest`; `python scripts/tour.py`; `python -m lab.runner --condition baseline --tasks learn`; `python -m lab.runner --condition subagents --tasks learn`; `python -m lab.curator`; `python -m lab.runner --condition skills-auto --tasks learn`.
- Lượt `code-learn` đầu tiên bị check `tests_not_modified` sai do checkout CRLF trên Windows trong khi checker dùng hash LF. Hai test file được chuẩn hóa byte LF mà không đổi nội dung Git; baseline code-learn được chạy lại và check này đã đạt.
- Một lượt rerun `subagents/code-learn` gặp `API_KEY_QUOTA_EXHAUSTED`; không dùng lượt có `error` làm kết quả chính thức.
- Thử thách mở rộng: không thực hiện.
