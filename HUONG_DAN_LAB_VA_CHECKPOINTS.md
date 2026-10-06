# Giải thích bài lab Self-Evolving Agentic và checklist checkpoint

Tài liệu này tổng hợp `README.md`, `GUIDE.md`, `RUBRIC.md`, các pseudo-code, mã nguồn, test và checker trong dự án. Mục tiêu là giúp thực hiện bài lab theo đúng thứ tự, biết mỗi checkpoint cần tạo ra gì và biết bằng chứng nào phải giữ lại để báo cáo/chấm điểm.

> Cảnh báo về tính hợp lệ: các task `*-eval` là tập đánh giá giữ riêng. Trước khi viết giả thuyết và tạo tag `freeze`, không dùng nội dung checker, đáp án hoặc quy ước riêng của tập đánh giá để sửa prompt, subagent hay skill. Không chép chi tiết của task đánh giá vào `skills/auto/` hoặc báo cáo.

## 1. Bài lab yêu cầu làm gì?

Bài lab xây dựng một **agent harness** bằng Deep Agents rồi so sánh ba điều kiện thí nghiệm:

| Điều kiện | Cấu hình | Câu hỏi cần trả lời |
|---|---|---|
| `baseline` | Agent mặc định, không có skill | Agent gốc làm tốt đến đâu? |
| `subagents` | Agent chính cộng các subagent tự định nghĩa | Chia việc cho nhiều agent có tăng điểm và có đáng chi phí token không? |
| `skills-auto` | Agent đơn nạp skill do curator tự sinh | Agent có học được quy trình tổng quát từ lỗi của tập học không? |

Điểm cốt lõi không chỉ là làm agent chạy được. Bài lab còn yêu cầu một thí nghiệm có thể tái lập:

1. Mỗi lần chạy dùng một sandbox tạm, không sửa dữ liệu gốc.
2. Mỗi task được chấm bằng các check tự động và có điểm từng phần.
3. Mỗi lần chạy lưu điểm, token, thời gian, tool call, trace và hash của skill.
4. Curator chỉ học từ lỗi của task `learn`.
5. Skill phải được đóng băng trước khi chạy task `eval`.
6. Kết luận phải dựa trên số liệu và trace, kể cả khi cải tiến không có tác dụng.

## 2. Luồng hoạt động của toàn hệ thống

```text
task instruction + workspace
          |
          v
prepare_sandbox() sao chép dữ liệu vào thư mục tạm
          |
          v
build_agent() tạo Deep Agent + backend + prompt
          |
          v
agent đọc/ghi file, chạy shell, có thể gọi subagent hoặc đọc skill
          |
          v
grade() chạy tasks/<id>/check.py trên workspace đã sửa
          |
          +--> results/<condition>/<task>/run.json
          +--> results/<condition>/<task>/trace.md

baseline learn results
          |
          v
curate_skills() lấy failed checks + cuối trace của task học
          |
          v
validate_skill() lọc skill sai định dạng/rò rỉ
          |
          v
skills/auto/<skill>/SKILL.md
          |
          v
viết giả thuyết -> commit -> tag freeze -> chạy eval -> so sánh
```

### Các thành phần chính

- `src/lab/agent.py`: tạo backend an toàn và dựng agent ở mode `single`/`subagents`.
- `src/lab/subagents.py`: định nghĩa ít nhất hai subagent có vai trò khác nhau.
- `src/lab/runner.py`: chạy task, đo lường, chấm điểm và ghi kết quả.
- `src/lab/curator.py`: đọc thất bại của task học và nhờ LLM sinh skill.
- `src/lab/model.py`: tạo model từ biến môi trường.
- `src/lab/tasks.py`: tìm task, chuẩn bị sandbox, hash skill.
- `src/lab/grading.py`: chạy checker và chỉ giữ `detail` của check thất bại trên task học.
- `src/lab/compare.py`: tạo bảng so sánh ba điều kiện.
- `scripts/verify_freeze.py`: kiểm tra giao thức giả thuyết/đóng băng.
- `scripts/check_breakdown.py`: tách check kỹ thuật và check quy ước tổ chức.

## 3. Những file được phép và không được phép sửa

### Phải cài đặt

Chỉ hoàn thiện các phần đánh dấu TODO trong:

1. `src/lab/subagents.py`: `get_subagents`.
2. `src/lab/agent.py`: import cần thiết, `make_backend`, `build_agent`.
3. `src/lab/runner.py`: `run_task`.
4. `src/lab/curator.py`: `curate_skills`.

### Được tạo bởi quy trình lab

- `skills/auto/`: chỉ do curator sinh; được xóa skill kém nhưng không sửa tay nội dung.
- `results/`: kết quả chạy thực nghiệm.
- `report/REPORT.md`: báo cáo theo mẫu.
- `report/table.md`: bảng do `lab.compare` sinh.

### Không sửa

- `tests/`, `tasks/`, `scripts/`.
- `src/lab/model.py`, `tasks.py`, `grading.py`, `testing.py`, `compare.py`.
- Các hằng prompt trong `agent.py`.
- `render_trace`, `main` trong `runner.py`.
- `validate_skill`, `parse_skill_blocks` trong `curator.py`.

Sửa các phần có sẵn có thể bị trừ 10 điểm; khi chấm, giảng viên có thể thay chúng bằng bản gốc.

## 4. Sáu task và cách tính điểm

Mỗi task có `instruction.md`, `workspace/` và `check.py`. Điểm task bằng `passed / total`; chỉ khi mọi check đạt thì task mới được xem là thành công hoàn toàn.

| Họ task | Task học | Task đánh giá | Nội dung chính | Số check học/eval |
|---|---|---|---|---:|
| Code | `code-learn` | `code-eval` | Sửa package Python; phải đọc cả test và docstring, sửa nguyên nhân gốc, không sửa test | 10 / 11 |
| Data | `data-learn` | `data-eval` | Làm sạch dữ liệu, khử trùng, chuẩn hóa thời gian/múi giờ, tiền tệ và ghi JSON/CSV | 8 / 9 |
| Logs | `logs-learn` | `logs-eval` | Parse log nhiều dòng, chuẩn hóa mức log/thời gian, xử lý dòng lặp và tổng hợp lỗi | 9 / 10 |

Mỗi task học có các check kỹ thuật cùng các check `rule_*` mô phỏng quy ước nội bộ của Acme. Task đánh giá cùng họ dùng dữ liệu khác và thêm một quy ước mới để đo khả năng tổng quát hóa. Tổng cộng mỗi điều kiện chính thức có 6 lần chạy; cả ba điều kiện tạo 18 `run.json` và 18 `trace.md`.

Các bẫy kỹ thuật chung của ba họ task:

- Code: test nhìn thấy không bao phủ toàn bộ đặc tả; docstring mới là specification đầy đủ; lỗi trong hàm dùng chung ảnh hưởng nhiều caller.
- Data: phải khử trùng theo ID, xử lý sentinel thiếu dữ liệu, chuẩn hóa chữ hoa/thường, parse nhiều định dạng và đổi thời gian sang UTC trước khi lọc theo kỳ.
- Logs: một entry có thể gồm nhiều dòng; dòng lặp thuộc entry ngay trước; từ `ERROR` trong message không biến một dòng `INFO` thành lỗi; level không luôn viết hoa.

## 5. Trạng thái dự án tại thời điểm rà soát

Ngày rà soát: 2026-10-06.

| Hạng mục | Trạng thái hiện tại |
|---|---|
| Git | Sạch, nhánh `main`, HEAD `d982034` |
| TODO harness | Chưa cài đặt 5 hàm chính nêu ở mục 3 |
| `skills/auto/` | Chỉ có README, chưa có skill |
| `results/` | Chưa có kết quả |
| `report/` | Chưa được tạo |
| Tag `freeze` | Chưa có |
| Python trong PowerShell hiện tại | Không tìm thấy `python`, `python3` hoặc `py`; chưa thể chạy pytest tại shell hiện tại |

Vì backend của agent dùng `/bin/sh`, dự án yêu cầu macOS/Linux; trên Windows nên làm trong **WSL hoặc Docker**. Đây là việc cần xử lý đầu tiên trước khi đánh giá bất kỳ test nào.

## 6. Checkpoint 0 — Cài đặt và làm quen

### Việc cần làm

Trong WSL/Linux hoặc container:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
mkdir -p report
cp REPORT_TEMPLATE.md report/REPORT.md
pytest tests/test_01_provided.py
```

Điền `.env` bằng một trong hai cấu hình:

- Azure/OpenAI-compatible: đủ `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT_MODEL`.
- Provider LangChain khác: `LAB_MODEL` và biến API key tương ứng.

Không commit `.env`, không đưa API key vào trace hoặc báo cáo.

Kiểm tra model và xem công cụ mặc định:

```bash
python -c "from lab.model import make_model; print(make_model().invoke('Reply with OK').content)"
python scripts/tour.py
```

### Điều kiện đạt checkpoint

- [ ] Python từ 3.11 trở lên chạy được trong WSL/Linux/Docker.
- [ ] `pip install -e .` thành công.
- [ ] `pytest tests/test_01_provided.py` trả về `12 passed`.
- [ ] Model trả lời được `OK`.
- [ ] `report/REPORT.md` đã được tạo.
- [ ] Mục 3 của báo cáo trả lời đủ ba câu hỏi từ `scripts/tour.py`.

Checkpoint này chưa yêu cầu các test `test_02` đến `test_04` đạt, vì mã TODO chưa được cài đặt.

## 7. Checkpoint 1 — Hoàn thiện harness

Làm đúng thứ tự sau vì `build_agent` phụ thuộc `get_subagents`.

### 1.1. `get_subagents`

Định nghĩa ít nhất hai subagent, tên không trùng. Mỗi dict phải có:

- `name`: tên ngắn, ổn định.
- `description`: chỉ rõ **khi nào nên gọi**.
- `system_prompt`: phạm vi trách nhiệm và hành vi cần làm.

Thiết kế khuyến nghị: `explorer` đọc đặc tả/dữ liệu và báo cáo, `implementer` sửa/chạy test, `reviewer` kiểm tra độc lập. Subagent chỉ thấy prompt được giao, vì vậy agent chính phải truyền đầy đủ quy tắc và đường dẫn.

```bash
pytest tests/test_02_agent.py -k subagents
```

Đạt khi subagent đủ trường, tên duy nhất và mode `subagents` đưa chúng vào mô tả tool `task`.

### 1.2. `make_backend` và `build_agent`

`make_backend` phải dùng `LocalShellBackend` với các yêu cầu quan trọng:

- `root_dir=sandbox`, `virtual_mode=True`.
- `inherit_env=False` để API key không lọt vào shell của agent.
- Tự đặt `PATH`, bắt đầu bằng thư mục chứa executable Python hiện tại, sau đó là các đường dẫn hệ thống cần thiết.
- `HOME` trỏ vào sandbox; đặt `PYTHONDONTWRITEBYTECODE=1`.
- Timeout mỗi lệnh là 120 giây.

`build_agent` phải:

- Chỉ nhận mode `single` hoặc `subagents`, mode khác ném `ValueError`.
- Luôn dùng nguyên `BASE_PROMPT`.
- Ở mode `subagents`, nối `PATHS_NOTE` vào prompt của từng subagent và nối `SUBAGENTS_NOTE` vào prompt chính.
- Khi `use_skills=True`, truyền `skills=["/skills/"]` và thêm `SKILLS_NOTE`.
- Dùng model được truyền vào; nếu không có thì gọi `make_model()`.

Không dùng `permissions=` với shell backend. Công cụ file chấp nhận đường dẫn ảo, nhưng shell chỉ dùng an toàn dạng tương đối `workspace/...`; tuyệt đối không hướng agent dùng `/workspace/...` trong lệnh shell.

```bash
pytest tests/test_02_agent.py
```

Đạt khi cả 9 test của file này xanh: Python được tìm thấy, secrets bị ẩn, file tool/shell dùng chung đường dẫn, prompt/mode/skill/subagent hoạt động đúng.

### 1.3. `run_task`

`run_task` phải thực hiện trọn vòng đời:

1. Lấy task và cấu hình condition.
2. Tạo output folder và sandbox tạm **ngoài repository**.
3. Sao chép workspace/skill vào sandbox.
4. Hash skill trước khi chạy và ghi timestamp UTC.
5. Dựng agent, gắn `UsageMetadataCallbackHandler`, gọi agent với `recursion_limit`.
6. Nếu agent lỗi, ghi `error` thay vì làm chương trình dừng.
7. Đếm tool call, call `task`, số skill khác nhau đã đọc.
8. So hash sau chạy để tạo `skills_modified`.
9. Chấm workspace, ghi trace và luôn xóa sandbox.
10. Ghi `run.json` UTF-8, JSON dễ đọc.

`run.json` bắt buộc có:

```text
task, condition, role, score, passed, total, checks,
tokens {input, output, total}, tool_calls, subagent_calls,
skills_read, skills_modified, skills_sha256, timestamp,
seconds, final_message, error
```

```bash
pytest tests/test_03_runner.py
```

Đạt khi cả 6 test xanh, workspace gốc không bị đổi, lỗi API được ghi lại và các bộ đếm/hash/timestamp đúng.

### 1.4. Chạy end-to-end lần đầu

```bash
python -m lab.runner --condition baseline --tasks data-learn
```

Đạt khi:

- [ ] Có `results/baseline/data-learn/run.json` và `trace.md`.
- [ ] `tokens.total > 0`.
- [ ] `checks` có danh sách check; check thất bại có `detail`.
- [ ] `tasks/data-learn/workspace/` vẫn nguyên vẹn.
- [ ] `error` là `null`, hoặc lỗi hạ tầng được ghi rõ để xử lý/chạy lại.

Lần chạy này chính là baseline chính thức của `data-learn`; không cần chạy lại ở checkpoint 2.

## 8. Checkpoint 2 — Chạy task học và phân tích lỗi

### Chạy hai điều kiện

```bash
python -m lab.runner --condition baseline --tasks code-learn logs-learn
python -m lab.runner --condition subagents --tasks learn
```

Sau bước này phải có 3 task học cho `baseline` và 3 task học cho `subagents`.

### Phân loại mọi check thất bại của baseline

Đọc `run.json` và `trace.md`, rồi đưa từng lỗi vào một nhóm:

| Nhóm | Ý nghĩa |
|---|---|
| A | Bỏ qua README, docstring hoặc đặc tả định dạng |
| B | Không chạy test/không kiểm chứng kết quả trước khi kết thúc |
| C | Vá chỗ biểu hiện thay vì sửa nguyên nhân gốc |
| D | Bỏ sót dữ liệu bẩn, trùng, sentinel, định dạng hoặc múi giờ |
| E | Vi phạm quy ước Acme; thường là check `rule_*` với `detail` bắt đầu `RULE:` |
| F | Final message nói đã tạo/sửa file nhưng thực tế không có |
| G | Lỗi khác, phải mô tả cụ thể |

Mỗi dòng trong mục 4 của báo cáo phải có task, tên check và bằng chứng ngắn từ `detail` hoặc trace. Lỗi hạ tầng như 401/429/timeout không được dùng làm bằng chứng lỗi của agent.

Chạy công cụ hỗ trợ:

```bash
python scripts/check_breakdown.py
```

Trước tag `freeze`, công cụ cố ý ẩn hàng eval. Nếu phần lớn lỗi là nhóm E, phải nêu thêm bằng chứng phủ định cho A-D, ví dụ số check kỹ thuật đạt trên tổng số check kỹ thuật.

### Phân tích subagent

Với từng task học, ghi:

- `subagent_calls` bằng bao nhiêu và subagent nào được gọi.
- Prompt giao việc có đủ quy tắc/đường dẫn không.
- Agent chính có kiểm tra lại báo cáo của subagent không.
- Token/thời gian so với baseline.
- Nếu không gọi subagent, giải thích hợp lý; đây vẫn là kết quả hợp lệ.

### Điều kiện đạt checkpoint

- [ ] `results/baseline/` đủ 3 task học.
- [ ] `results/subagents/` đủ 3 task học.
- [ ] Mỗi run có cả `run.json` và `trace.md` hợp lệ.
- [ ] Mục 4 báo cáo có bảng phân loại và bằng chứng.
- [ ] Mục 5 báo cáo phân tích `subagent_calls`, trace, token và thời gian.

## 9. Checkpoint 3 — Curator và skill tự sinh

### 3.1. Cài `curate_skills`

Curator chỉ được đọc `results/<source_condition>/*/run.json` có `role == "learn"`. Với mỗi run, lấy:

- Tên và `detail` của check thất bại.
- Khoảng 6000 ký tự cuối của `trace.md`.

Nếu không có check thất bại, in cảnh báo, trả `[]` và **không gọi model**. Nếu có, gọi model một lần, parse các khối skill, validate từng khối, chỉ ghi tối đa `max_skills` skill hợp lệ vào `<out_dir>/<name>/SKILL.md`.

Các bảo vệ bắt buộc:

- Không đưa bất kỳ run `eval` nào vào prompt.
- Tên skill phải an toàn, không cho path traversal như `../evil`.
- Không ghi skill chứa marker của tập đánh giá.
- Không bỏ qua `validate_skill`.

```bash
pytest tests/test_04_curator.py
```

Đạt khi 2 test xanh.

### 3.2. Sinh và đánh giá skill

```bash
python -m lab.curator
```

Với từng skill, kiểm tra:

1. Có tổng quát cho task mới cùng loại hay chỉ ghi nhớ chi tiết task học?
2. Chỉ dẫn có đúng với feedback/đặc tả không?
3. Có ngắn, có checklist hành động và điều kiện hoàn thành không?
4. `description` có nói rõ khi nào dùng để agent chủ động đọc không?
5. Có dấu hiệu rò rỉ dữ liệu đánh giá không?

Có thể xóa skill kém chất lượng và chạy lại curator tối đa hai lần; phải ghi lý do. Không được sửa tay nội dung skill.

### 3.3. Kiểm tra skill trên task học

```bash
python -m lab.runner --condition skills-auto --tasks learn
```

Đọc `skills_read` và trace. `skills_read > 0` chỉ chứng minh agent đã mở skill; vẫn phải kiểm tra agent có làm theo các quy tắc hay không.

Trước checkpoint 4, sao lưu kết quả dev vì lần chạy chính thức sẽ ghi đè:

```bash
mv results/skills-auto results/skills-auto-dev
```

### Điều kiện đạt checkpoint

- [ ] `pytest tests/test_04_curator.py` đạt 2/2.
- [ ] `skills/auto/` có ít nhất một skill hợp lệ do curator sinh.
- [ ] Mục 6 báo cáo đánh giá từng skill và ghi số lần chạy lại/xóa.
- [ ] Có kết quả `skills-auto` cho 3 task học và đã sao lưu để đo nhiễu.

## 10. Checkpoint 4 — Giả thuyết, freeze và đánh giá chính thức

Thứ tự ở phần này là bắt buộc.

### 4.0. Viết giả thuyết trước khi xem điểm eval

Điền đủ H1-H3 ở mục 2 của `report/REPORT.md`:

- H1: dự đoán `subagents` so với `baseline`.
- H2: dự đoán `skills-auto` so với `baseline`.
- H3: dự đoán kết quả task học so với task đánh giá.

Mỗi giả thuyết phải có lý do dựa trên phân loại lỗi và tài liệu, sau đó commit:

```bash
git add -A
git commit -m "hypotheses"
```

### 4.1. Đóng băng skill

Từ thời điểm này không sửa `skills/auto/`.

```bash
git add -A
git commit --allow-empty -m "freeze skills"
git tag freeze
```

### 4.2. Chạy chính thức

```bash
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python scripts/verify_freeze.py
```

`verify_freeze.py` phải báo `OK`. Nó kiểm tra:

- Có commit `hypotheses` với H1-H3 đã điền trước tag.
- `skills/` hiện tại không khác tag `freeze`.
- Mọi run `skills-auto` dùng đúng hash skill đã freeze.
- Run bắt đầu sau freeze và `skills_modified == false`.

Nếu run lỗi hạ tầng, chạy lại đúng task và ghi sự cố trong báo cáo. Không dùng run lỗi làm bằng chứng về chất lượng agent.

### Điều kiện đạt checkpoint

- [ ] Có commit `hypotheses` trước tag `freeze`.
- [ ] Có tag `freeze` và skill không đổi sau tag.
- [ ] `baseline`, `subagents`, `skills-auto` đều có đủ 6 task.
- [ ] Tất cả run `skills-auto` có `skills_modified=false` và hash đúng.
- [ ] `python scripts/verify_freeze.py` báo `OK`.

## 11. Checkpoint 5 — So sánh và hoàn thiện báo cáo

Tạo bảng và số liệu phân rã:

```bash
python -m lab.compare > report/table.md
python scripts/check_breakdown.py
```

`report/table.md` phải có:

- 3 cột `baseline`, `subagents`, `skills-auto`.
- 6 hàng task.
- Điểm trung bình task học và task đánh giá.
- Token trung bình mỗi run.
- Số run đã đọc skill.

Trong mục 8 báo cáo, phải phân tích:

1. Điểm task học và eval riêng, không gộp để che dấu quá khớp.
2. Check kỹ thuật và check `rule_*` riêng.
3. Cơ chế thành công/thất bại dựa trên trace và `skills_read`.
4. Chi phí token; có thể tính hiệu quả gần đúng bằng tổng/điểm trung bình trên token trung bình, nhưng phải nêu rõ cách tính.
5. Dấu hiệu quá khớp hoặc rò rỉ và cách phòng tránh.
6. Nhiễu: so điểm task học của cùng bộ skill ở run dev và run sau freeze.
7. Ít nhất ba hạn chế, kèm ảnh hưởng của từng hạn chế lên kết luận.

Kết quả âm hoặc không khác biệt vẫn có thể đạt điểm tối đa nếu số liệu đúng và phân tích trung thực.

### Điều kiện đạt checkpoint

- [ ] `report/table.md` được sinh từ `lab.compare`, không nhập số tay.
- [ ] Số trong báo cáo khớp toàn bộ `run.json`.
- [ ] Mục 1-10 của mẫu báo cáo đã hoàn thiện.
- [ ] Kết luận tối đa 5 câu và không khẳng định vượt quá dữ liệu.
- [ ] Phụ lục ghi lệnh theo đúng thứ tự và mọi lần chạy lỗi/chạy lại.

## 12. Checklist theo thang điểm 100

| Hạng mục | Điểm | Checklist ngắn |
|---|---:|---|
| Harness | 30 | `test_02` 9/9, `test_03` 6/6, `test_04` 2/2; `test_01` 12/12 phải đạt nhưng không tính điểm |
| Baseline và phân loại lỗi | 14 | Baseline đủ 6 task; ít nhất 4 check thất bại được phân loại với bằng chứng, hoặc có bằng chứng phủ định nếu lỗi ít/cùng nhóm |
| Multi-agent | 10 | Ít nhất 2 vai trò rõ; subagents đủ 6 task; phân tích call/trace/token |
| Self-evolving | 16 | Có skill hợp lệ do curator sinh; đánh giá chất lượng; skills-auto đủ 6 task; giải thích việc đọc/làm theo skill |
| So sánh và freeze | 10 | Bảng đủ và khớp; `verify_freeze.py` báo OK |
| Báo cáo | 20 | Giả thuyết trước freeze; phân tích số liệu/cơ chế/chi phí; ít nhất 3 hạn chế; đủ thông tin tái lập |

Điểm thưởng tối đa +5 chỉ nên làm sau khi toàn bộ phần chính hoàn tất. Một lựa chọn an toàn và có giá trị khoa học là lặp lại eval thêm ít nhất hai lần trong thư mục kết quả riêng để ước lượng nhiễu.

## 13. Các lỗi dễ làm mất điểm

1. Chạy trực tiếp trong PowerShell Windows dù backend cần `/bin/sh`.
2. Bật `inherit_env=True`, làm lộ API key cho shell của agent.
3. Dùng `/workspace/...` trong shell thay vì `workspace/...`.
4. Sửa test/task/checker hoặc các hàm được cung cấp sẵn.
5. Chạy eval trước khi commit giả thuyết và freeze.
6. Sửa tay skill hoặc để agent sửa skill trong lần chạy chính thức.
7. Quên sao lưu `results/skills-auto` ở checkpoint 3 nên mất số liệu đo nhiễu.
8. Chỉ nhìn `skills_read` mà không kiểm tra trace xem skill có được làm theo.
9. Xem lỗi API/timeout là lỗi năng lực của agent.
10. Nhập số liệu báo cáo bằng tay khiến lệch với `run.json`.
11. Để final message nói đã tạo file dù file thực tế không tồn tại.
12. Kết luận “subagent/skill tốt hơn” từ một chênh lệch nhỏ trong đúng một lần chạy.

## 14. Trình tự lệnh đề xuất từ đầu đến cuối

```bash
# Cài đặt
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
mkdir -p report
cp REPORT_TEMPLATE.md report/REPORT.md

# Checkpoint 0-1
pytest tests/test_01_provided.py
python scripts/tour.py
pytest tests/test_02_agent.py
pytest tests/test_03_runner.py
python -m lab.runner --condition baseline --tasks data-learn

# Checkpoint 2
python -m lab.runner --condition baseline --tasks code-learn logs-learn
python -m lab.runner --condition subagents --tasks learn
python scripts/check_breakdown.py

# Checkpoint 3
pytest tests/test_04_curator.py
python -m lab.curator
python -m lab.runner --condition skills-auto --tasks learn
mv results/skills-auto results/skills-auto-dev

# Điền H1-H3 trước khi chạy eval
git add -A
git commit -m "hypotheses"
git add -A
git commit --allow-empty -m "freeze skills"
git tag freeze

# Checkpoint 4-5
python -m lab.runner --condition baseline --tasks eval
python -m lab.runner --condition subagents --tasks eval
python -m lab.runner --condition skills-auto --tasks all
python scripts/verify_freeze.py
python -m lab.compare > report/table.md
python scripts/check_breakdown.py
pytest
```

## 15. Checklist trước khi nộp

- [ ] Không có API key trong git, trace hoặc report.
- [ ] Chỉ các TODO cho phép đã được sửa.
- [ ] `pytest` đạt toàn bộ 29 test của dự án.
- [ ] Ba condition đều có đủ 6 task, mỗi task có `run.json` và `trace.md`.
- [ ] Không có run chính thức còn `error`; nếu từng có, báo cáo đã ghi cách xử lý.
- [ ] Mọi run `skills-auto` có `skills_modified=false`.
- [ ] `verify_freeze.py` báo OK.
- [ ] `report/table.md` khớp với kết quả sinh lại từ `lab.compare`.
- [ ] `report/REPORT.md` đủ 10 mục, có số liệu và bằng chứng trace.
- [ ] Git có commit giả thuyết trước tag `freeze`.
- [ ] `skills/auto/`, `results/`, `report/REPORT.md`, `report/table.md` đều được commit.

Sản phẩm nộp cuối cùng gồm mã cài đặt trong bốn file TODO, skill tự sinh, toàn bộ kết quả được dùng trong báo cáo và hai file báo cáo. Giá trị lớn nhất của bài lab nằm ở việc chứng minh được điều gì đã cải thiện, điều gì không, chi phí bao nhiêu và kết luận đáng tin đến mức nào.
