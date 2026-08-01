# gc-329 Interface Contract — MultiAgentBudgetOptimizer (MARBLE coding task_id=50)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=50, at
commit `8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-329/solution.py`.

## class BudgetOptimizer()

- `add_user(name) -> None` — duplicate raises `ValueError`.
- `set_limit(category, amount) -> None` — `amount <= 0` raises `ValueError`.
  Re-setting replaces the limit.
- `add_expense(user, category, amount) -> None`
  - Unknown user raises `KeyError`. A category with no limit set raises `KeyError`
    (limits must be planned before spending).
  - `amount` must be an int or float with `amount > 0`, else `ValueError`
    (bool counts as invalid).
- `summary() -> dict` with keys:
  - `"total_budget"`: sum of category limits;
  - `"total_expenses"`: sum of all expenses;
  - `"remaining"`: total_budget - total_expenses;
  - `"contributions"`: dict mapping every registered user (including ones with no
    expenses) to their expense sum.
- `category_status(category) -> dict` — `{"limit", "spent", "remaining", "over"}`
  where `over` is `spent > limit`. Unknown category raises `KeyError`.
- `reallocate(from_cat, to_cat, amount) -> None` — moves limit between categories.
  Unknown category raises `KeyError`; `amount <= 0` raises `ValueError`; if
  `from_cat`'s unspent headroom (`limit - spent`) is less than `amount`, raises
  `ValueError` and changes nothing.
- `optimize() -> list` — one `[category, reduce_by]` entry per category with
  `spent > limit`, `reduce_by = spent - limit`, sorted by `reduce_by` descending then
  category name ascending. Empty list when nothing is over.
- `savings_gap(target) -> float` — `max(0, target - sum of all overshoots)`.
