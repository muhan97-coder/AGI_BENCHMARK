# gc-325 Interface Contract — TaskChain (MARBLE coding task_id=46)

Source task: MARBLE repo `multiagentbench/coding/coding_main.jsonl`, task_id=46, at commit
`8892e9cfb69282db568e6b018f2b1cd8eec31ba6`.

Implement `workspace/gc-325/solution.py` exposing exactly this API. Times and deadlines
are plain ints.

## class TaskChain()

- `add_task(name: str, deadline: int | None = None) -> None` — duplicate name raises
  `ValueError`. Initial status `"not_started"`.
- `add_dependency(before, after) -> None` — `before` must complete before `after` may
  start. Unknown task raises `KeyError`. If the edge would create a cycle (including
  `before == after`) raise `ValueError` and do not add it.
- `start(name, time: int) -> None` — raises `RuntimeError` unless the task is
  `"not_started"` and all its dependencies are `"completed"`. Records the start time.
- `complete(name, time: int) -> None` — raises `RuntimeError` unless the task is
  `"in_progress"`. Raises `ValueError` if `time` < start time. Then, appends
  `"completed:<name>"` to the event feed and, for every task (in sorted name order)
  that became ready exactly because of this completion, appends `"ready:<task>"`.
- `status(name) -> str` — `"not_started" | "in_progress" | "completed"`; unknown task
  raises `KeyError`.
- `ready_tasks() -> list[str]` — sorted names of `"not_started"` tasks whose
  dependencies are all `"completed"`.
- `topological_order() -> list[str]` — all task names in an order where every
  dependency precedes its dependents.
- `comment(name, author, text) -> None` / `comments(name) -> list` of `(author, text)`
  pairs in order. Unknown task raises `KeyError`.
- `events() -> list[str]` — the event feed in append order.
- `report(now: int) -> dict` with keys `"completed"`, `"in_progress"`, `"not_started"`
  (each a sorted name list) and `"delayed"`: sorted names of tasks that are not
  `"completed"` and have a deadline with `now > deadline`.
