# gc-324 Interface Contract — OfficeTaskScheduler (MARBLE coding task_id=5)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=5, at commit
`8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement a single file at `workspace/gc-324/solution.py` (relative to the benchmark repo
root) exposing exactly this API. The sealed suite `assets/gc-324/test_accept.py` is the
only grader. Dates are ISO strings `"YYYY-MM-DD"`.

## class OfficeTaskScheduler()

- `add_user(name: str) -> None` — duplicate name raises `ValueError`.
- `create_task(creator, title, assignee, deadline, priority, today) -> int`
  - Returns integer task ids starting at 1, incrementing by 1.
  - Unknown `creator` or `assignee` raises `KeyError`.
  - `deadline < today` raises `ValueError`. `priority` outside 1..5 raises `ValueError`.
  - New tasks have status `"pending"`.
  - On success the assignee receives the notification string `"assigned:<task_id>"`.
- `dashboard(user) -> list[dict]` — tasks assigned to `user`, each dict with keys
  `task_id, title, status, deadline, priority`, sorted by deadline asc, then priority
  desc, then task_id asc. Unknown user raises `KeyError`.
- `update_status(user, task_id, status) -> None` — `status` must be one of
  `"pending" | "in_progress" | "completed"` else `ValueError`. Unknown task raises
  `KeyError`. Only the assignee may update, otherwise `PermissionError`.
- `add_comment(user, task_id, text) -> None` — only creator or assignee, otherwise
  `PermissionError`. Unknown task raises `KeyError`.
- `comments(task_id) -> list` — `(user, text)` pairs in insertion order.
- `notifications(user) -> list[str]` — in delivery order. Unknown user raises `KeyError`.
- `due_soon(user, today, days=2) -> list[int]` — sorted task ids assigned to `user`,
  status != `"completed"`, with `0 <= (deadline - today) <= days` in calendar days.
- `report(today) -> dict` with keys:
  - `"completion_rate"`: completed / total as float, `0.0` when there are no tasks;
  - `"overdue"`: sorted task ids with deadline < today and status != `"completed"`;
  - `"per_user"`: dict mapping every registered user to the count of tasks assigned
    to them (0 included).
