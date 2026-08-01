# gc-327 Interface Contract — BudgetSync (MARBLE coding task_id=12)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=12, at commit
`8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-327/solution.py`.

## class BudgetSync()

- `register(user, password) -> None` — duplicate user raises `ValueError`.
- `login(user, password) -> bool` — `False` for unknown user or wrong password.
- `create_budget(owner, name) -> int` — ids start at 1. Unknown owner raises
  `KeyError`. The owner is a member with role `"owner"`.
- `invite(inviter, budget_id, invitee, role) -> None`
  - Only the budget owner may invite, otherwise `PermissionError`.
  - Unknown budget or unknown invitee raises `KeyError`; role must be `"viewer"` or
    `"editor"` else `ValueError`; inviting an existing member raises `ValueError`.
  - Every member that was already in the budget (including the owner) receives the
    notification `"member_added:<invitee>:<budget_id>"`. The invitee gets none.
- `add_income(user, budget_id, amount, category) -> None` and
  `add_expense(user, budget_id, amount, category) -> None`
  - `amount <= 0` raises `ValueError`. Non-members and viewers raise
    `PermissionError`. Owner and editors are allowed. Unknown budget raises `KeyError`.
- `dashboard(user, budget_id) -> dict` — any member (viewers included); non-members
  raise `PermissionError`. Keys: `"total_income"`, `"total_expense"`, `"net"`
  (income - expense), `"by_category"` (dict of expense sums per category).
- `set_limit(user, budget_id, category, limit) -> None` — owner or editor only,
  otherwise `PermissionError`; `limit <= 0` raises `ValueError`.
- After any `add_expense` that lifts a category's expense total strictly above its
  limit, every member of that budget receives `"limit_exceeded:<category>:<budget_id>"`
  (once per such expense event).
- `suggestions(budget_id) -> dict` — `{category: overshoot}` for every category whose
  expense total exceeds its limit, overshoot = total - limit. Empty dict if none.
- `notifications(user) -> list[str]` — delivery order. Unknown user raises `KeyError`.

Budgets are fully isolated: amounts, limits, categories, and membership never leak
across budget ids.
