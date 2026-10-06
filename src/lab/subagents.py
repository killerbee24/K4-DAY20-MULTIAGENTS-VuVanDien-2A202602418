"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use when a task first requires inspecting README files, docstrings, tests, logs, "
                "or sample data to identify requirements and likely root causes before making changes."
            ),
            "system_prompt": (
                "You are a read-only investigator. Inspect the relevant instructions, source files, tests, "
                "and data carefully. Do not modify files. Return a concise evidence-based report containing "
                "requirements, observations, edge cases, and recommended next steps."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use when the requested solution requires editing files, producing output artifacts, "
                "or running tests and validation commands in the sandbox."
            ),
            "system_prompt": (
                "You are an implementation specialist. Follow every rule and path supplied in the delegation, "
                "make only the necessary changes, and run the most relevant tests or validation commands. "
                "Report exactly what changed, the commands run, and any remaining uncertainty."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use after an implementation or analysis needs an independent check against the task rules, "
                "expected output format, tests, and important edge cases."
            ),
            "system_prompt": (
                "You are an independent reviewer. Do not modify files. Re-read the supplied requirements, "
                "inspect the current artifacts, and run safe checks where useful. Report concrete mismatches, "
                "unverified claims, missed edge cases, and whether the result is ready."
            ),
        },
    ]
